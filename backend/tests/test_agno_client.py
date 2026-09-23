import asyncio
import base64
from types import SimpleNamespace

import pytest

from app.services.agno_client import AgnoAnswer, AgnoError, AgnoGeminiClient, RAG_NOT_FOUND_MESSAGE, _provider_error


class FakeAgent:
    run = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeAgent.instance = self

    async def arun(self, prompt, **kwargs):
        FakeAgent.prompt = prompt
        FakeAgent.run_kwargs = kwargs
        if isinstance(FakeAgent.run, Exception):
            raise FakeAgent.run
        return FakeAgent.run


class FakeGemini:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeGemini.kwargs = kwargs


def grounding_run():
    return SimpleNamespace(
        content='Resposta com fonte',
        citations=SimpleNamespace(raw={'grounding_metadata': {'grounding_chunks': [
            {'retrieved_context': {'title': 'Guia', 'uri': 'https://example.test/guide', 'text': 'trecho', 'pageNumber': 2}},
            {'retrieved_context': {'title': 'Guia', 'uri': 'https://example.test/guide', 'text': 'duplicada'}},
        ]}}),
    )


@pytest.mark.asyncio
async def test_query_builds_prompt_and_normalizes_sources(monkeypatch):
    monkeypatch.setattr('app.services.agno_client.Agent', FakeAgent)
    monkeypatch.setattr('app.services.agno_client.Gemini', FakeGemini)
    FakeAgent.run = grounding_run()
    image = 'data:image/png;base64,iVBORw0KGgoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='
    result = await AgnoGeminiClient().query(
        prompt='pergunta atual',
        history=[{'role': 'user', 'content': 'pergunta anterior'}],
        image=image,
        model_id='gemini-test',
    )
    assert isinstance(result, AgnoAnswer)
    assert result.text == 'Resposta com fonte'
    assert len(result.sources) == 1
    assert result.sources[0].page_number == 2
    assert 'pergunta anterior' in FakeAgent.prompt
    assert FakeAgent.run_kwargs['images'][0].content.startswith(b'\x89PNG')
    assert FakeGemini.kwargs['file_search_store_names'] == ['fileSearchStores/test-store']


@pytest.mark.asyncio
async def test_query_sends_gemini_images_in_order(monkeypatch):
    monkeypatch.setattr('app.services.agno_client.Agent', FakeAgent)
    monkeypatch.setattr('app.services.agno_client.Gemini', FakeGemini)
    FakeAgent.run = SimpleNamespace(content='ok', citations=SimpleNamespace(raw={}))
    images = [
        'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\nfirst').decode(),
        'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\nsecond').decode(),
    ]

    await AgnoGeminiClient().query(prompt='x', history=[], images=images, model_id='gemini-test')

    assert [item.content for item in FakeAgent.run_kwargs['images']] == [
        b'\x89PNG\r\n\x1a\nfirst',
        b'\x89PNG\r\n\x1a\nsecond',
    ]



@pytest.mark.asyncio
async def test_rag_without_grounding_refuses_to_complete_from_model_memory(monkeypatch):
    monkeypatch.setattr('app.services.agno_client.Agent', FakeAgent)
    monkeypatch.setattr('app.services.agno_client.Gemini', FakeGemini)
    FakeAgent.run = SimpleNamespace(
        content='Resposta inventada pelo modelo',
        citations=SimpleNamespace(raw={'grounding_metadata': {'grounding_chunks': []}}),
    )

    result = await AgnoGeminiClient().query(
        prompt='O que é o Comitê Gestor do IBS?',
        history=[],
        file_search_store_id='fileSearchStores/reforma',
        use_legacy_knowledge_base=False,
        model_id='gemini-test',
    )

    assert result.text == RAG_NOT_FOUND_MESSAGE
    assert result.sources == []
    assert FakeGemini.kwargs['file_search_store_names'] == ['fileSearchStores/reforma']
    assert 'exclusivamente o conteúdo recuperado' in FakeAgent.instance.kwargs['instructions'][0]

@pytest.mark.asyncio
async def test_query_maps_timeout_and_provider_errors(monkeypatch):
    monkeypatch.setattr('app.services.agno_client.Agent', FakeAgent)
    monkeypatch.setattr('app.services.agno_client.Gemini', FakeGemini)
    FakeAgent.run = asyncio.TimeoutError()
    with pytest.raises(AgnoError) as timeout:
        await AgnoGeminiClient().query(prompt='x', history=[], model_id='gemini-test')
    assert (timeout.value.status_code, timeout.value.code) == (504, 'google_timeout')

    class RateLimitError(Exception):
        status_code = 429

    FakeAgent.run = RateLimitError()
    with pytest.raises(AgnoError) as rate:
        await AgnoGeminiClient().query(prompt='x', history=[], model_id='gemini-test')
    assert (rate.value.status_code, rate.value.code) == (429, 'google_rate_limit')
    assert 'Google Gemini' in rate.value.message


@pytest.mark.parametrize(
    ('error', 'status_code', 'code'),
    [
        (Exception('Quota exceeded for this project'), 429, 'google_quota_exceeded'),
        (Exception('Billing account required'), 402, 'google_billing_required'),
        (Exception('API key not valid'), 401, 'google_api_key_invalid'),
        (Exception('Model gemini-invalid does not exist'), 400, 'google_model_not_found'),
        (SimpleNamespace(status_code=403, message='You do not have permission to access the file search store reformatributaria'), 403, 'google_file_search_store_forbidden'),
    ],
)
def test_provider_error_maps_actionable_google_diagnostics(error, status_code, code):
    mapped = _provider_error(error)

    assert (mapped.status_code, mapped.code) == (status_code, code)
    assert mapped.message
    assert 'test-google-api-key' not in mapped.message
    if code == 'google_file_search_store_forbidden':
        assert 'não tem acesso ao File Search Store' in mapped.message

def test_provider_error_maps_rag_store_permission_without_provider_body():
    mapped = _provider_error(SimpleNamespace(status_code=403), file_search_store_id='fileSearchStores/reforma')

    assert (mapped.status_code, mapped.code) == (403, 'google_file_search_store_forbidden')
    assert 'não tem acesso ao File Search Store' in mapped.message


def test_missing_gemini_api_key_is_a_configuration_error(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'google_api_key', '   ')

    with pytest.raises(AgnoError) as raised:
        AgnoGeminiClient().create_model(model_id='gemini-test')

    assert (raised.value.status_code, raised.value.code) == (503, 'google_not_configured')
    assert 'GOOGLE_API_KEY' in raised.value.message


@pytest.mark.asyncio
async def test_query_limits_sources(monkeypatch):
    monkeypatch.setattr('app.services.agno_client.Agent', FakeAgent)
    monkeypatch.setattr('app.services.agno_client.Gemini', FakeGemini)
    chunks = [{'retrieved_context': {'title': f'Source {index}', 'uri': f'https://example.test/{index}'}} for index in range(25)]
    FakeAgent.run = SimpleNamespace(content='ok', citations=SimpleNamespace(raw={'grounding_metadata': {'grounding_chunks': chunks}}))
    result = await AgnoGeminiClient().query(prompt='x', history=[], model_id='gemini-test')
    assert len(result.sources) == 20
