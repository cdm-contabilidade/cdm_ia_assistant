from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.core.auth import get_optional_user
from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.guardrails import evaluate_guardrail
from app.core.rate_limit import limiter
from app.models import AIModel, Chat, KnowledgeBase, Message, User
from app.schemas import ChatQueryRequest, ChatQueryResponse, MessagePublic, SourceCitation
from app.services.agno_client import AgnoAnswer, AgnoError
from app.services.image_validation import decode_images
from app.services.provider_gateway import ProviderGateway

router = APIRouter(prefix='/api/chat', tags=['chat'])


@dataclass(frozen=True)
class ResolvedProvider:
    provider: str
    model_id: str
    model_display_name: str | None
    knowledge_base_id: UUID | None
    knowledge_base_name: str | None
    file_search_store_id: str | None
    use_legacy_knowledge_base: bool

    @property
    def metadata(self) -> dict[str, str]:
        result = {
            'provider': self.provider,
            'model_id': self.model_id,
        }
        if self.model_display_name:
            result['model_display_name'] = self.model_display_name
        if self.knowledge_base_id:
            result['knowledge_base_id'] = str(self.knowledge_base_id)
        if self.knowledge_base_name:
            result['knowledge_base_name'] = self.knowledge_base_name
        return result


def ephemeral_messages(
    payload: ChatQueryRequest,
    answer: str,
    image_metadata: dict | None,
    provider_metadata: dict[str, str],
) -> list[MessagePublic]:
    now = datetime.now(timezone.utc)
    return [
        MessagePublic(
            id=uuid4(),
            role='user',
            content=payload.chat_input.strip(),
            created_at=now,
            has_image=image_metadata is not None,
            image_metadata=image_metadata,
            metadata=provider_metadata,
        ),
        MessagePublic(id=uuid4(), role='assistant', content=answer, created_at=now, has_image=False, metadata=provider_metadata),
    ]


def chat_title_from_question(question: str) -> str:
    normalized_question = ' '.join(question.split())
    return ' '.join(normalized_question.split()[:8])[:80]


def response_sources(sources) -> list[SourceCitation]:
    return [SourceCitation(title=source.title, uri=source.uri, text=source.text, page_number=source.page_number) for source in sources]


def unavailable_model() -> HTTPException:
    return HTTPException(status_code=404, detail={'code': 'model_not_available', 'message': 'O modelo informado não existe ou está inativo.'})


def unavailable_knowledge_base() -> HTTPException:
    return HTTPException(status_code=404, detail={'code': 'knowledge_base_not_available', 'message': 'A base de conhecimento informada não existe ou está inativa.'})


def knowledge_base_required() -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={
            'code': 'knowledge_base_required',
            'message': 'Selecione uma base de conhecimento para usar um modelo Gemini.',
        },
    )


async def resolve_provider(
    model_id: UUID | None,
    knowledge_base_id: UUID | None,
) -> ResolvedProvider:
    settings = get_settings()
    selected_model: AIModel | None = None
    selected_knowledge_base: KnowledgeBase | None = None
    async with get_session_factory()() as db:
        if model_id is not None:
            selected_model = await db.scalar(select(AIModel).where(AIModel.id == model_id, AIModel.active.is_(True)))
            if selected_model is None:
                raise unavailable_model()
        if knowledge_base_id is not None:
            selected_knowledge_base = await db.scalar(
                select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id, KnowledgeBase.active.is_(True))
            )
            if selected_knowledge_base is None:
                raise unavailable_knowledge_base()

    provider = selected_model.provider if selected_model else 'gemini'
    resolved_model_id = selected_model.model_id if selected_model else settings.google_gemini_model
    if selected_knowledge_base is not None and provider != selected_knowledge_base.provider:
        raise HTTPException(
            status_code=400,
            detail={
                'code': 'knowledge_base_provider_mismatch',
                'message': 'Esta base de conhecimento só pode ser usada com um modelo Gemini.',
            },
        )
    if provider == 'gemini' and selected_knowledge_base is None:
        raise knowledge_base_required()
    return ResolvedProvider(
        provider=provider,
        model_id=resolved_model_id,
        model_display_name=selected_model.display_name if selected_model else None,
        knowledge_base_id=selected_knowledge_base.id if selected_knowledge_base else None,
        knowledge_base_name=selected_knowledge_base.name if selected_knowledge_base else None,
        file_search_store_id=selected_knowledge_base.file_search_store_id if selected_knowledge_base else None,
        use_legacy_knowledge_base=False,
    )


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
async def persist_authenticated_response(
    payload: ChatQueryRequest,
    user_id: UUID,
    target_chat_id: UUID,
    cleaned_input: str,
    image_metadata: dict | None,
    answer: AgnoAnswer,
    provider_metadata: dict[str, str],
    resolved_provider: ResolvedProvider | None = None,
) -> ChatQueryResponse:
    async with get_session_factory()() as db:
        chat = await db.scalar(select(Chat).where(Chat.id == target_chat_id, Chat.user_id == user_id))
        now = datetime.now(timezone.utc)
        if chat is None:
            other_chat = await db.scalar(select(Chat.id).where(Chat.id == target_chat_id))
            if other_chat is not None:
                raise HTTPException(status_code=404, detail={'code': 'chat_not_found', 'message': 'Conversa não encontrada.'})
            chat = Chat(id=target_chat_id, user_id=user_id, title=chat_title_from_question(cleaned_input), updated_at=now)
            db.add(chat)
            await db.flush()
        elif chat.title == 'Nova Consulta' and await db.scalar(select(Message.id).where(Message.chat_id == chat.id).limit(1)) is None:
            chat.title = chat_title_from_question(cleaned_input)
        user_message = Message(
            chat_id=chat.id,
            role='user',
            content=cleaned_input,
            created_at=now,
            has_image=image_metadata is not None,
            image_metadata=image_metadata,
            provider_metadata=provider_metadata,
        )
        assistant_message = Message(
            chat_id=chat.id,
            role='assistant',
            content=answer.text,
            created_at=now + timedelta(microseconds=1),
            has_image=False,
            provider_metadata=provider_metadata,
        )
        db.add_all([user_message, assistant_message])
        chat.updated_at = now
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)
        return ChatQueryResponse(
            sessionId=payload.session_id,
            chatId=chat.id,
            title=chat.title,
            answer=answer.text,
            sources=response_sources(answer.sources),
            messages=[MessagePublic.model_validate(user_message), MessagePublic.model_validate(assistant_message)],
            modelId=payload.model_id,
            knowledgeBaseId=resolved_provider.knowledge_base_id if resolved_provider else None,
            model={'name': resolved_provider.model_display_name} if resolved_provider and resolved_provider.model_display_name else None,
            knowledgeBase={'name': resolved_provider.knowledge_base_name} if resolved_provider and resolved_provider.knowledge_base_name else None,
        )




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
        image_values = [payload.image] if payload.image is not None else payload.images
        validated_images = decode_images(image_values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={'code': 'invalid_image', 'message': str(exc)}) from exc
    if validated_images:
        image_metadata, decoded_images = validated_images
        image_bytes_list = [item[0] for item in decoded_images]
        image_formats = [item[1] for item in decoded_images]
    else:
        image_metadata = None
        image_bytes_list = []
        image_formats = []
    image_bytes = image_bytes_list[0] if payload.image is not None and image_bytes_list else None
    image_format = image_formats[0] if payload.image is not None and image_formats else None
    target_chat_id = payload.chat_id or payload.session_id
    decision = evaluate_guardrail(cleaned_input, scope_required=payload.knowledge_base_id is None)
    if not decision.allowed:
        answer = AgnoAnswer(text=decision.message or '', sources=[])
        provider_metadata = {'guardrail': decision.code or 'policy_refusal'}
        if user_id is None:
            return ChatQueryResponse(
                sessionId=payload.session_id,
                chatId=None,
                title=None,
                answer=answer.text,
                sources=[],
                messages=ephemeral_messages(payload, answer.text, image_metadata, provider_metadata),
                modelId=payload.model_id,
                knowledgeBaseId=None,
            )
        return await persist_authenticated_response(
            payload,
            user_id,
            target_chat_id,
            cleaned_input,
            image_metadata,
            answer,
            provider_metadata,
        )
    history = [message.model_dump() for message in payload.history]
    if user_id is not None:
        history = await load_authenticated_history(target_chat_id, user_id)
    resolved_provider = await resolve_provider(payload.model_id, payload.knowledge_base_id)
    try:
        answer = await ProviderGateway().query(
            provider=resolved_provider.provider,
            model_id=resolved_provider.model_id,
            file_search_store_id=resolved_provider.file_search_store_id,
            enable_web_search=resolved_provider.provider == 'openai' and resolved_provider.file_search_store_id is None,
            use_legacy_knowledge_base=resolved_provider.use_legacy_knowledge_base,
            prompt=cleaned_input,
            history=history,
            image=payload.image,
            images=payload.images,
            image_bytes=image_bytes,
            image_format=image_format,
            image_bytes_list=image_bytes_list,
            image_formats=image_formats,
        )
    except AgnoError as exc:
        raise HTTPException(status_code=exc.status_code, detail={'code': exc.code, 'message': exc.message}) from exc
    if user_id is None:
        return ChatQueryResponse(
            sessionId=payload.session_id,
            chatId=None,
            title=None,
            answer=answer.text,
            sources=response_sources(answer.sources),
            messages=ephemeral_messages(payload, answer.text, image_metadata, resolved_provider.metadata),
            modelId=payload.model_id,
            knowledgeBaseId=resolved_provider.knowledge_base_id,
            model={'name': resolved_provider.model_display_name} if resolved_provider.model_display_name else None,
            knowledgeBase={'name': resolved_provider.knowledge_base_name} if resolved_provider.knowledge_base_name else None,
        )
    return await persist_authenticated_response(
        payload,
        user_id,
        target_chat_id,
        cleaned_input,
        image_metadata,
        answer,
        resolved_provider.metadata,
        resolved_provider,
    )
