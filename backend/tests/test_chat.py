import base64
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.database import get_session_factory
from app.core.rate_limit import limiter
from app.models import Chat, Message, User
from app.services.agno_client import AgnoAnswer, AgnoError, AgnoGeminiClient, SourceCitation

PNG = 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'\x00' * 32).decode()


def successful_answer(text='Resposta mockada'):
    return AgnoAnswer(text=text, sources=[SourceCitation(title='Manual CDM', uri='https://example.test/manual', page_number=3)])


@pytest.mark.asyncio
async def test_guest_query_sends_history_and_does_not_persist(client, monkeypatch):
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return successful_answer()

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'dúvida guest',
        'history': [{'role': 'user', 'content': 'contexto'}],
    })
    assert response.status_code == 200
    assert response.json()['answer'] == 'Resposta mockada'
    assert response.json()['sources'][0]['pageNumber'] == 3
    assert captured['history'] == [{'role': 'user', 'content': 'contexto'}]
    async with get_session_factory()() as db:
        assert await db.scalar(select(func.count()).select_from(User)) == 0
        assert await db.scalar(select(func.count()).select_from(Chat)) == 0
        assert await db.scalar(select(func.count()).select_from(Message)) == 0


@pytest.mark.asyncio
async def test_authenticated_query_uses_database_history_and_persists_image(client, collaborator_token, monkeypatch):
    calls = []

    async def fake_query(self, **kwargs):
        calls.append(kwargs)
        return successful_answer('Resposta persistida')

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    session_id = str(uuid4())
    headers = {'Authorization': f'Bearer {collaborator_token}'}
    first = await client.post('/api/chat/query', headers=headers, json={'sessionId': session_id, 'chatInput': 'primeira', 'image': PNG})
    assert first.status_code == 200
    second = await client.post('/api/chat/query', headers=headers, json={
        'sessionId': session_id,
        'chatId': session_id,
        'chatInput': 'segunda',
        'history': [{'role': 'user', 'content': 'histórico adulterado'}],
    })
    assert second.status_code == 200
    assert [item['content'] for item in calls[1]['history']] == ['primeira', 'Resposta persistida']
    assert calls[0]['image_bytes'].startswith(b'\x89PNG')
    async with get_session_factory()() as db:
        messages = list(await db.scalars(select(Message).order_by(Message.created_at)))
        assert len(messages) == 4
        assert messages[0].has_image is True
        assert messages[0].image_metadata['mime'] == 'image/png'


@pytest.mark.asyncio
async def test_provider_failure_does_not_persist(client, collaborator_token, monkeypatch):
    async def failed_query(self, **kwargs):
        raise AgnoError(504, 'google_timeout', 'O serviço de resposta demorou além do limite.')

    monkeypatch.setattr(AgnoGeminiClient, 'query', failed_query)
    response = await client.post('/api/chat/query', headers={'Authorization': f"Bearer {collaborator_token}"}, json={'sessionId': str(uuid4()), 'chatInput': 'x'})
    assert response.status_code == 504
    async with get_session_factory()() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 0


@pytest.mark.asyncio
async def test_invalid_image_and_rate_limit(client, monkeypatch):
    async def fake_query(self, **kwargs):
        return successful_answer('ok')

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    invalid = await client.post('/api/chat/query', json={'sessionId': str(uuid4()), 'chatInput': 'x', 'image': 'data:image/png;base64,not-valid'})
    assert invalid.status_code == 422
    from app.core.config import get_settings
    limiter._events.clear()
    get_settings().rate_limit_max_attempts = 1
    first = await client.post('/api/chat/query', json={'sessionId': str(uuid4()), 'chatInput': 'x', 'image': None})
    second = await client.post('/api/chat/query', json={'sessionId': str(uuid4()), 'chatInput': 'x', 'image': None})
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers['X-RateLimit-Remaining'] == '0'
