from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.core.auth import get_optional_user
from app.core.database import get_session_factory
from app.core.rate_limit import limiter
from app.models import Chat, Message, User
from app.schemas import ChatQueryRequest, ChatQueryResponse, MessagePublic, SourceCitation
from app.services.agno_client import AgnoError, AgnoGeminiClient
from app.services.image_validation import decode_image

router = APIRouter(prefix='/api/chat', tags=['chat'])


def ephemeral_messages(payload: ChatQueryRequest, answer: str, image_metadata: dict | None) -> list[MessagePublic]:
    now = datetime.now(timezone.utc)
    return [
        MessagePublic(id=uuid4(), role='user', content=payload.chat_input.strip(), created_at=now, has_image=image_metadata is not None, image_metadata=image_metadata),
        MessagePublic(id=uuid4(), role='assistant', content=answer, created_at=now, has_image=False),
    ]



def response_sources(sources) -> list[SourceCitation]:
    return [SourceCitation(title=source.title, uri=source.uri, text=source.text, page_number=source.page_number) for source in sources]


async def load_authenticated_history(target_chat_id: UUID, user_id: UUID) -> list[dict[str, str]]:
    async with get_session_factory()() as db:
        chat = await db.scalar(select(Chat).where(Chat.id == target_chat_id, Chat.user_id == user_id))
        if chat is None:
            other_chat = await db.scalar(select(Chat.id).where(Chat.id == target_chat_id))
            if other_chat is not None:
                raise HTTPException(status_code=404, detail={'code': 'chat_not_found', 'message': 'Conversa não encontrada.'})
            return []
        result = await db.scalars(
            select(Message).where(Message.chat_id == chat.id).order_by(Message.created_at.desc()).limit(20)
        )
        messages = list(result)
        messages.reverse()
        return [{'role': message.role, 'content': message.content} for message in messages]


@router.post('/query', response_model=ChatQueryResponse)
async def query(
    payload: ChatQueryRequest,
    request: Request,
    user: User | None = Depends(get_optional_user),
) -> ChatQueryResponse:
    user_id = user.id if user else None
    limiter.check(f'chat:{request.client.host if request.client else "unknown"}:{user_id or "guest"}')
    cleaned_input = payload.chat_input.strip()
    if not cleaned_input:
        raise HTTPException(status_code=422, detail={'code': 'empty_chat_input', 'message': 'A mensagem não pode ficar vazia.'})
    try:
        validated_image = decode_image(payload.image)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={'code': 'invalid_image', 'message': str(exc)}) from exc
    image_metadata, image_bytes, image_format = validated_image or (None, None, None)
    target_chat_id = payload.chat_id or payload.session_id
    history = [message.model_dump() for message in payload.history]
    if user_id is not None:
        history = await load_authenticated_history(target_chat_id, user_id)
    try:
        answer = await AgnoGeminiClient().query(
            prompt=cleaned_input,
            history=history,
            image=payload.image,
            image_bytes=image_bytes,
            image_format=image_format,
        )
    except AgnoError as exc:
        raise HTTPException(status_code=exc.status_code, detail={'code': exc.code, 'message': exc.message}) from exc
    if user_id is None:
        return ChatQueryResponse(
            sessionId=payload.session_id,
            chatId=None,
            answer=answer.text,
            sources=response_sources(answer.sources),
            messages=ephemeral_messages(payload, answer.text, image_metadata),
        )
    async with get_session_factory()() as db:
        chat = await db.scalar(select(Chat).where(Chat.id == target_chat_id, Chat.user_id == user_id))
        now = datetime.now(timezone.utc)
        if chat is None:
            chat = Chat(id=target_chat_id, user_id=user_id, title=cleaned_input[:255], updated_at=now)
            db.add(chat)
            await db.flush()
        user_message = Message(chat_id=chat.id, role='user', content=cleaned_input, created_at=now, has_image=image_metadata is not None, image_metadata=image_metadata)
        assistant_message = Message(chat_id=chat.id, role='assistant', content=answer.text, created_at=now + timedelta(microseconds=1), has_image=False)
        db.add_all([user_message, assistant_message])
        chat.updated_at = now
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)
        return ChatQueryResponse(
            sessionId=payload.session_id,
            chatId=chat.id,
            answer=answer.text,
            sources=response_sources(answer.sources),
            messages=[MessagePublic.model_validate(user_message), MessagePublic.model_validate(assistant_message)],
        )
