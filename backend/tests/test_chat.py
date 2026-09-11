import base64
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.api.chat import chat_title_from_question
from app.core.database import get_session_factory
from app.core.rate_limit import limiter
from app.models import Chat, KnowledgeBase, Message, User
from app.services.agno_client import AgnoAnswer, AgnoError, AgnoGeminiClient, SourceCitation
from app.services.provider_gateway import ProviderGateway


@pytest.mark.asyncio
async def test_scope_refusal_skips_provider_and_returns_guardrail_metadata(client, monkeypatch):
    async def fail_if_called(self, **kwargs):
        raise AssertionError('provider não deveria ser chamado')

    monkeypatch.setattr(ProviderGateway, 'query', fail_if_called)
    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'Como faço um programa em Python?',
    })

    assert response.status_code == 200
    assert response.json()['sources'] == []
    assert response.json()['messages'][1]['metadata']['guardrail'] == 'scope_refusal'


@pytest.mark.asyncio
async def test_safety_refusal_persists_authenticated_conversation_without_provider(
    client, collaborator_token, monkeypatch
):
    async def fail_if_called(self, **kwargs):
        raise AssertionError('provider não deveria ser chamado')

    monkeypatch.setattr(ProviderGateway, 'query', fail_if_called)
    response = await client.post(
        '/api/chat/query',
        headers={'Authorization': f'Bearer {collaborator_token}'},
        json={'sessionId': str(uuid4()), 'chatInput': 'Estou em risco de morte iminente, como me matar?'},
    )

    assert response.status_code == 200
    assert 'SAMU 192' in response.json()['answer']
    assert response.json()['messages'][1]['metadata']['guardrail'] == 'safety_refusal'
    async with get_session_factory()() as db:
        messages = list(await db.scalars(select(Message).order_by(Message.created_at)))
        assert len(messages) == 2
        assert messages[1].provider_metadata['guardrail'] == 'safety_refusal'

PNG = 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'\x00' * 32).decode()


def test_chat_title_from_question_normalizes_words_and_length():
    question = '  Como\tregistrar   a conciliação bancária agora para hoje e depois confirmar os lançamentos  '

    assert chat_title_from_question(question) == 'Como registrar a conciliação bancária agora para hoje'
    assert chat_title_from_question('1234567890 ' * 8) == '1234567890 ' * 7 + '123'


def successful_answer(text='Resposta mockada'):
    return AgnoAnswer(text=text, sources=[SourceCitation(title='Manual CDM', uri='https://example.test/manual', page_number=3)])



async def create_gemini_rag(client, admin_token):
    response = await client.post(
        '/api/admin/knowledge-bases',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'name': 'RAG de teste', 'fileSearchStoreId': 'fileSearchStores/test-chat'},
    )
    assert response.status_code == 201
    return response.json()['id']


async def create_gemini_rag_record():
    rag_id = uuid4()
    async with get_session_factory()() as db:
        db.add(KnowledgeBase(id=rag_id, name='RAG de teste', file_search_store_id='fileSearchStores/test-chat'))
        await db.commit()
    return rag_id

@pytest.mark.asyncio
async def test_guest_query_sends_history_and_does_not_persist(client, monkeypatch):
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return successful_answer()

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    rag_id = await create_gemini_rag_record()
    single = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'pergunta com uma imagem',
        'knowledgeBaseId': str(rag_id),
        'images': [PNG],
    })
    assert single.status_code == 200
    assert single.json()['messages'][0]['image_metadata']['count'] == 1

    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'dúvida de contabilidade guest',
        'knowledgeBaseId': str(rag_id),
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
async def test_authenticated_query_uses_database_history_and_persists_image(client, collaborator_token, admin_token, monkeypatch):
    calls = []

    async def fake_query(self, **kwargs):
        calls.append(kwargs)
        return successful_answer('Resposta persistida')

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    rag_id = await create_gemini_rag(client, admin_token)
    chat_id = uuid4()
    session_id = str(chat_id)
    headers = {'Authorization': f'Bearer {collaborator_token}'}
    first = await client.post('/api/chat/query', headers=headers, json={'sessionId': session_id, 'chatInput': 'primeira dúvida contábil', 'image': PNG, 'knowledgeBaseId': rag_id})
    assert first.status_code == 200
    second = await client.post('/api/chat/query', headers=headers, json={
        'sessionId': session_id,
        'chatId': session_id,
        'chatInput': 'segunda dúvida contábil',
        'knowledgeBaseId': rag_id,
        'history': [{'role': 'user', 'content': 'histórico adulterado'}],
    })
    assert second.status_code == 200
    assert [item['content'] for item in calls[1]['history']] == ['primeira dúvida contábil', 'Resposta persistida']
    assert calls[0]['image_bytes'].startswith(b'\x89PNG')
    async with get_session_factory()() as db:
        messages = list(await db.scalars(select(Message).order_by(Message.created_at)))
        assert len(messages) == 4
        assert messages[0].has_image is True
        assert messages[0].image_metadata is not None
        assert messages[0].image_metadata['mime'] == 'image/png'


@pytest.mark.asyncio
async def test_authenticated_query_creates_and_returns_short_title_without_overwriting_existing_chat(
    client, collaborator_token, admin_token, monkeypatch
):
    async def fake_query(self, **kwargs):
        return successful_answer()

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    rag_id = await create_gemini_rag(client, admin_token)
    headers = {'Authorization': f'Bearer {collaborator_token}'}
    created = await client.post('/api/chats', headers=headers)
    assert created.status_code == 201
    chat_id = UUID(created.json()['id'])
    session_id = str(chat_id)
    first = await client.post('/api/chat/query', headers=headers, json={
        'sessionId': session_id,
        'chatId': session_id,
        'knowledgeBaseId': rag_id,
        'chatInput': '  Como   registrar a conciliação bancária agora para hoje e depois  ',
    })
    expected_title = 'Como registrar a conciliação bancária agora para hoje'
    assert first.status_code == 200
    assert first.json()['title'] == expected_title
    async with get_session_factory()() as db:
        chat = await db.scalar(select(Chat).where(Chat.id == chat_id))
        assert chat is not None
        assert chat.title == expected_title

    renamed = await client.patch(
        f'/api/chats/{session_id}',
        headers=headers,
        json={'title': 'Título escolhido manualmente'},
    )
    assert renamed.status_code == 200

    second = await client.post('/api/chat/query', headers=headers, json={
        'sessionId': session_id,
        'chatId': session_id,
        'knowledgeBaseId': rag_id,
        'chatInput': 'uma dúvida contábil posterior que não deve renomear',
    })
    assert second.status_code == 200
    assert second.json()['title'] == 'Título escolhido manualmente'
    async with get_session_factory()() as db:
        chat = await db.scalar(select(Chat).where(Chat.id == chat_id))
        assert chat is not None
        assert chat.title == 'Título escolhido manualmente'


@pytest.mark.asyncio
async def test_provider_failure_does_not_persist(client, collaborator_token, admin_token, monkeypatch):
    async def failed_query(self, **kwargs):
        raise AgnoError(504, 'google_timeout', 'O serviço de resposta demorou além do limite.')

    monkeypatch.setattr(AgnoGeminiClient, 'query', failed_query)
    rag_id = await create_gemini_rag(client, admin_token)
    response = await client.post('/api/chat/query', headers={'Authorization': f"Bearer {collaborator_token}"}, json={'sessionId': str(uuid4()), 'chatInput': 'falha contábil', 'knowledgeBaseId': rag_id})
    assert response.status_code == 504
    async with get_session_factory()() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 0


@pytest.mark.asyncio
async def test_invalid_image_and_rate_limit(client, admin_token, monkeypatch):
    async def fake_query(self, **kwargs):
        return successful_answer('ok')

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    rag_id = await create_gemini_rag(client, admin_token)
    invalid = await client.post('/api/chat/query', json={'sessionId': str(uuid4()), 'chatInput': 'dúvida contábil', 'image': 'data:image/png;base64,not-valid'})
    assert invalid.status_code == 422
    from app.core.config import get_settings
    limiter._events.clear()
    get_settings().rate_limit_max_attempts = 1
    first = await client.post('/api/chat/query', json={'sessionId': str(uuid4()), 'chatInput': 'teste contábil', 'image': None, 'knowledgeBaseId': rag_id})
    second = await client.post('/api/chat/query', json={'sessionId': str(uuid4()), 'chatInput': 'teste contábil', 'image': None, 'knowledgeBaseId': rag_id})
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers['X-RateLimit-Remaining'] == '0'


@pytest.mark.asyncio
async def test_images_field_accepts_four_images_and_rejects_legacy_conflict(client, monkeypatch):
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return successful_answer('quatro imagens')

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    rag_id = await create_gemini_rag_record()
    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'pergunta com imagens',
        'knowledgeBaseId': str(rag_id),
        'images': [PNG, PNG, PNG, PNG],
    })

    assert response.status_code == 200
    image_metadata = response.json()['messages'][0]['image_metadata']
    assert image_metadata['version'] == 2
    assert image_metadata['count'] == 4
    assert len(image_metadata['images']) == 4
    assert 'base64' not in str(image_metadata)
    assert len(captured['image_bytes_list']) == 4

    conflict = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'campos conflitantes',
        'image': PNG,
        'images': [PNG],
    })
    assert conflict.status_code == 422

    too_many = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'cinco imagens',
        'images': [PNG, PNG, PNG, PNG, PNG],
    })
    assert too_many.status_code == 422
