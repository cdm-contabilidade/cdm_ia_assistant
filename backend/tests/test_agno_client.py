import asyncio
from types import SimpleNamespace

import pytest

from app.services.agno_client import AgnoAnswer, AgnoError, AgnoGeminiClient


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
    )
    assert isinstance(result, AgnoAnswer)
    assert result.text == 'Resposta com fonte'
    assert len(result.sources) == 1
    assert result.sources[0].page_number == 2
    assert 'pergunta anterior' in FakeAgent.prompt
    assert FakeAgent.run_kwargs['images'][0].content.startswith(b'\x89PNG')
    assert FakeGemini.kwargs['file_search_store_names'] == ['fileSearchStores/test-store']


@pytest.mark.asyncio
async def test_query_maps_timeout_and_provider_errors(monkeypatch):
    monkeypatch.setattr('app.services.agno_client.Agent', FakeAgent)
    monkeypatch.setattr('app.services.agno_client.Gemini', FakeGemini)
    FakeAgent.run = asyncio.TimeoutError()
    with pytest.raises(AgnoError) as timeout:
        await AgnoGeminiClient().query(prompt='x', history=[])
    assert (timeout.value.status_code, timeout.value.code) == (504, 'google_timeout')

    class RateLimitError(Exception):
        status_code = 429

    FakeAgent.run = RateLimitError()
    with pytest.raises(AgnoError) as rate:
        await AgnoGeminiClient().query(prompt='x', history=[])
    assert (rate.value.status_code, rate.value.code) == (429, 'google_rate_limit')


@pytest.mark.asyncio
async def test_query_limits_sources(monkeypatch):
    monkeypatch.setattr('app.services.agno_client.Agent', FakeAgent)
    monkeypatch.setattr('app.services.agno_client.Gemini', FakeGemini)
    chunks = [{'retrieved_context': {'title': f'Source {index}', 'uri': f'https://example.test/{index}'}} for index in range(25)]
    FakeAgent.run = SimpleNamespace(content='ok', citations=SimpleNamespace(raw={'grounding_metadata': {'grounding_chunks': chunks}}))
    result = await AgnoGeminiClient().query(prompt='x', history=[])
    assert len(result.sources) == 20
