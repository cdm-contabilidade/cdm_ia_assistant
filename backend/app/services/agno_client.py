import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from agno.agent import Agent
from agno.media import Image
from agno.models.google import Gemini

from app.core.config import get_settings
from app.services.image_validation import decode_image

logger = logging.getLogger(__name__)
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
    def create_model(self) -> Gemini:
        settings = get_settings()
        common = {
            'id': settings.google_gemini_model,
            'api_key': settings.google_api_key,
            'file_search_store_names': [settings.google_file_search_store_name],
            'timeout': settings.google_timeout_seconds,
        }
        try:
            return Gemini(**common)
        except TypeError:
            from google.genai.types import FileSearch, Tool

            return Gemini(
                id=settings.google_gemini_model,
                api_key=settings.google_api_key,
                generative_model_kwargs={
                    'tools': [Tool(fileSearch=FileSearch(fileSearchStoreNames=[settings.google_file_search_store_name]))]
                },
                client_params={'http_options': {'timeout': int(settings.google_timeout_seconds * 1000)}},
            )

    async def query(
        self,
        *,
        prompt: str,
        history: list[dict[str, str]],
        image: str | None = None,
        image_bytes: bytes | None = None,
        image_format: str | None = None,
    ) -> AgnoAnswer:
        settings = get_settings()
        validated = decode_image(image) if image_bytes is None and image else None
        if validated:
            _, image_bytes, image_format = validated
        request = _build_prompt(prompt, history)
        try:
            model = self.create_model()
            agent = Agent(
                model=model,
                markdown=True,
                instructions=['Responda com precisão usando exclusivamente o contexto recuperado quando ele existir.'],
            )
            kwargs: dict[str, Any] = {}
            if image_bytes:
                kwargs['images'] = [Image(content=image_bytes, format=image_format or 'png')]
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

        text = _run_text(run)
        if not text:
            raise AgnoError(502, 'google_provider_error', 'O serviço de resposta não retornou uma resposta válida.')
        return AgnoAnswer(text=text, sources=_extract_sources(run))


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
