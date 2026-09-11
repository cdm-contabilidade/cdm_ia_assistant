import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from agno.agent import Agent
from agno.media import Image
from agno.models.google import Gemini

from app.core.config import get_settings
from app.services.image_validation import decode_image, decode_images

logger = logging.getLogger(__name__)
RAG_NOT_FOUND_MESSAGE = 'Não encontrei essa informação na base de conhecimento selecionada.'
RAG_INSTRUCTIONS = (
    'Use exclusivamente o conteúdo recuperado do Store selecionado. Não use conhecimento '
    'geral, memória do modelo, internet ou qualquer outra base. Se o conteúdo recuperado '
    'não responder à pergunta, responda exatamente: '
    f'{RAG_NOT_FOUND_MESSAGE}'
)
MAX_SOURCES = 20


@dataclass(frozen=True)
class SourceCitation:
    title: str
    uri: str | None = None
    text: str | None = None
    page_number: int | None = None


@dataclass(frozen=True)
class AgnoAnswer:
    text: str
    sources: list[SourceCitation]


@dataclass
class AgnoError(Exception):
    status_code: int
    code: str
    message: str


class AgnoGeminiClient:
    def create_model(
        self,
        model_id: str | None = None,
        file_search_store_id: str | None = None,
        use_legacy_knowledge_base: bool = True,
    ) -> Gemini:
        settings = get_settings()
        selected_model_id = model_id or settings.google_gemini_model
        selected_store_id = file_search_store_id
        if selected_store_id is None and use_legacy_knowledge_base:
            selected_store_id = settings.google_file_search_store_name
        common = {
            'id': selected_model_id,
            'api_key': settings.google_api_key,
            'timeout': settings.google_timeout_seconds,
        }
        if selected_store_id is not None:
            common['file_search_store_names'] = [selected_store_id]
        try:
            return Gemini(**common)
        except TypeError:
            fallback: dict[str, Any] = {
                'id': selected_model_id,
                'api_key': settings.google_api_key,
                'client_params': {'http_options': {'timeout': int(settings.google_timeout_seconds * 1000)}},
            }
            if selected_store_id is not None:
                from google.genai.types import FileSearch, Tool

                fallback['generative_model_kwargs'] = {
                    'tools': [Tool(fileSearch=FileSearch(fileSearchStoreNames=[selected_store_id]))]
                }
            return Gemini(**fallback)

    async def query(
        self,
        *,
        prompt: str,
        history: list[dict[str, str]],
        image: str | None = None,
        images: list[str] | None = None,
        image_bytes: bytes | None = None,
        image_format: str | None = None,
        image_bytes_list: list[bytes] | None = None,
        image_formats: list[str] | None = None,
        model_id: str | None = None,
        file_search_store_id: str | None = None,
        use_legacy_knowledge_base: bool = True,
    ) -> AgnoAnswer:
        settings = get_settings()
        if image_bytes_list:
            decoded_images = list(zip(image_bytes_list, image_formats or []))
            if len(decoded_images) != len(image_bytes_list):
                decoded_images = [(content, image_formats[index] if image_formats and index < len(image_formats) else 'png')
                                  for index, content in enumerate(image_bytes_list)]
        elif image_bytes is not None:
            decoded_images = [(image_bytes, image_format or 'png')]
        elif images:
            validated = decode_images(images)
            decoded_images = validated[1] if validated else []
        elif image:
            validated = decode_image(image)
            decoded_images = [(validated[1], validated[2])] if validated else []
        else:
            decoded_images = []
        request = _build_prompt(prompt, history)
        try:
            model = self.create_model(
                model_id=model_id,
                file_search_store_id=file_search_store_id,
                use_legacy_knowledge_base=use_legacy_knowledge_base,
            )
            selected_store_id = file_search_store_id or (
                settings.google_file_search_store_name if use_legacy_knowledge_base else None
            )
            agent = Agent(
                model=model,
                markdown=True,
                instructions=[RAG_INSTRUCTIONS] if selected_store_id else [],
            )
            kwargs: dict[str, Any] = {}
            if decoded_images:
                kwargs['images'] = [Image(content=content, format=image_format) for content, image_format in decoded_images]
            run = await asyncio.wait_for(agent.arun(request, **kwargs), timeout=settings.google_timeout_seconds)
        except AgnoError:
            raise
        except (asyncio.TimeoutError, TimeoutError) as exc:
            logger.warning('Gemini request timed out')
            raise AgnoError(504, 'google_timeout', 'O serviço de resposta demorou além do limite.') from exc
        except Exception as exc:
            error = _provider_error(exc)
            logger.warning('Gemini provider request failed', extra={'code': error.code})
            raise error from exc

        sources = _extract_sources(run)
        if selected_store_id and not sources:
            return AgnoAnswer(text=RAG_NOT_FOUND_MESSAGE, sources=[])
        text = _run_text(run)
        if not text:
            raise AgnoError(502, 'google_provider_error', 'O serviço de resposta não retornou uma resposta válida.')
        return AgnoAnswer(text=text, sources=sources)


def _build_prompt(prompt: str, history: list[dict[str, str]]) -> str:
    lines = ['Histórico recente:']
    for message in history[-20:]:
        lines.append(f"{message['role']}: {message['content']}")
    lines.extend(['', 'Pergunta atual:', prompt])
    return '\n'.join(lines)


def _run_text(run: Any) -> str:
    content = getattr(run, 'content', run)
    if isinstance(content, str):
        return content.strip()
    return str(content).strip() if content is not None else ''


def _provider_error(exc: Exception) -> AgnoError:
    status = getattr(getattr(exc, 'response', None), 'status_code', None) or getattr(exc, 'status_code', None)
    if status == 429 or 'rate' in exc.__class__.__name__.lower() or 'quota' in str(exc).lower():
        return AgnoError(429, 'google_rate_limit', 'O serviço de resposta está temporariamente limitado.')
    if 'timeout' in exc.__class__.__name__.lower():
        return AgnoError(504, 'google_timeout', 'O serviço de resposta demorou além do limite.')
    return AgnoError(502, 'google_provider_error', 'Não foi possível consultar o serviço de resposta.')


def _value(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _extract_sources(run: Any) -> list[SourceCitation]:
    citations = _value(run, 'citations')
    raw = _value(citations, 'raw', {}) or {}
    metadata = _value(raw, 'grounding_metadata', {}) or {}
    chunks = _value(metadata, 'grounding_chunks', []) or []
    sources: list[SourceCitation] = []
    seen: set[tuple[str, str | None]] = set()
    for chunk in chunks:
        context = _value(chunk, 'retrieved_context') or _value(chunk, 'retrievedContext') or chunk
        uri = _value(context, 'uri') or _value(context, 'url')
        title = _value(context, 'title') or _value(context, 'display_name') or uri or 'Fonte consultada'
        text = _value(context, 'text')
        page = _value(context, 'page_number')
        if page is None:
            page = _value(context, 'pageNumber')
        try:
            page = int(page) if page is not None else None
        except (TypeError, ValueError):
            page = None
        key = (str(title), str(uri) if uri else None)
        if key in seen:
            continue
        seen.add(key)
        sources.append(SourceCitation(title=str(title), uri=str(uri) if uri else None, text=str(text) if text else None, page_number=page))
        if len(sources) >= MAX_SOURCES:
            break
    return sources
