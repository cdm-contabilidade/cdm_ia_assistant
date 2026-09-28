from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import Chat, Message, MessageImage, User
from app.schemas import ChatRenameRequest, ChatSummary, MessagePublic
from app.services.image_validation import image_data_url

router = APIRouter(prefix='/api/chats', tags=['chats'])


async def owned_chat(chat_id: UUID, user: User, db: AsyncSession) -> Chat:
    chat = await db.scalar(select(Chat).where(Chat.id == chat_id, Chat.user_id == user.id))
    if chat is None:
        raise HTTPException(status_code=404, detail={'code': 'chat_not_found', 'message': 'Conversa não encontrada.'})
    return chat


@router.get('', response_model=list[ChatSummary])
async def list_chats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[Chat]:
    result = await db.scalars(select(Chat).where(Chat.user_id == user.id).order_by(Chat.updated_at.desc()))
    return list(result)


@router.post('', response_model=ChatSummary, status_code=status.HTTP_201_CREATED)
async def create_chat(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Chat:
    chat = Chat(id=uuid4(), user_id=user.id, title='Nova Consulta')
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


@router.get('/{chat_id}/messages', response_model=list[MessagePublic])
async def list_messages(chat_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[MessagePublic]:
    await owned_chat(chat_id, user, db)
    messages = list(await db.scalars(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())))
    if not messages:
        return []
    images = await db.scalars(
        select(MessageImage).where(MessageImage.message_id.in_([m.id for m in messages])).order_by(MessageImage.position)
    )
    grouped: dict[UUID, list[MessageImage]] = {}
    for image in images:
        grouped.setdefault(image.message_id, []).append(image)
    public_messages: list[MessagePublic] = []
    for message in messages:
        public = MessagePublic.model_validate(message)
        message_images = grouped.get(message.id)
        if message_images:
            public.image_data = [image_data_url(image.mime, image.content) for image in message_images]
        public_messages.append(public)
    return public_messages


@router.patch('/{chat_id}', response_model=ChatSummary)
async def rename_chat(chat_id: UUID, payload: ChatRenameRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Chat:
    chat = await owned_chat(chat_id, user, db)
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail={'code': 'invalid_title', 'message': 'O título não pode ficar vazio.'})
    chat.title = title
    chat.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(chat)
    return chat


@router.delete('/{chat_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: UUID, response: Response, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> None:
    chat = await owned_chat(chat_id, user, db)
    await db.delete(chat)
    await db.commit()
