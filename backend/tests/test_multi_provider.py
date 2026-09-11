import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.database import get_session_factory
from app.models import Message
from app.services.agno_client import AgnoAnswer, AgnoError, AgnoGeminiClient
from app.services.openai_client import OpenAIResponsesClient
from app.services.provider_gateway import ProviderGateway


def test_openai_sdk_dependency_is_available():
    from openai import AsyncOpenAI

    assert AsyncOpenAI is not None

@pytest.mark.asyncio
async def test_admin_catalog_and_active_collaborator_catalog(client, admin_token, collaborator_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    model = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'openai', 'displayName': 'GPT', 'modelId': 'gpt-test', 'active': True,
    })
    assert model.status_code == 201
    inactive = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'gemini', 'displayName': 'Desativado', 'modelId': 'gemini-off', 'active': False,
    })
    assert inactive.status_code == 201
    knowledge_base = await client.post('/api/admin/knowledge-bases', headers=headers, json={
        'name': 'Documentos', 'fileSearchStoreId': 'fileSearchStores/docs',
    })
    assert knowledge_base.status_code == 201
    assert knowledge_base.json()['fileSearchStoreId'] == 'fileSearchStores/docs'

    catalog_headers = {'Authorization': f'Bearer {collaborator_token}'}
    models = await client.get('/api/catalog/models', headers=catalog_headers)
    assert models.status_code == 200
    assert [item['modelId'] for item in models.json()] == ['gpt-test']
    assert all(item['active'] for item in models.json())
    bases = await client.get('/api/catalog/knowledge-bases', headers=catalog_headers)
    assert bases.status_code == 200
    assert 'fileSearchStoreId' not in bases.json()[0]
    assert 'file_search_store_id' not in bases.json()[0]
    assert 'store_id' not in bases.json()[0]
    guest_models = await client.get('/api/catalog/models')
    assert guest_models.status_code == 200
    assert guest_models.json()[0] == {
        'id': model.json()['id'],
        'name': 'GPT',
        'provider': 'openai',
        'modelId': 'gpt-test',
        'active': True,
    }
    guest_bases = await client.get('/api/catalog/knowledge-bases')
    assert guest_bases.status_code == 200
    assert guest_bases.json() == [{
        'id': knowledge_base.json()['id'],
        'name': 'Documentos',
        'provider': 'gemini',
        'active': True,
        'featured': False,
    }]

    deleted = await client.delete(f"/api/admin/models/{model.json()['id']}", headers=headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_featured_knowledge_base_is_exclusive_switchable_and_sorted(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    inactive = await client.post('/api/admin/knowledge-bases', headers=headers, json={
        'name': 'Z inativa', 'fileSearchStoreId': 'fileSearchStores/inactive', 'active': False, 'featured': True,
    })
    assert inactive.status_code == 201
    assert inactive.json()['featured'] is False

    first = await client.post('/api/admin/knowledge-bases', headers=headers, json={
        'name': 'Z primeiro', 'fileSearchStoreId': 'fileSearchStores/first', 'featured': True,
    })
    second = await client.post('/api/admin/knowledge-bases', headers=headers, json={
        'name': 'A segundo', 'fileSearchStoreId': 'fileSearchStores/second', 'featured': True,
    })
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()['featured'] is True
    assert second.json()['featured'] is True

    listed = await client.get('/api/admin/knowledge-bases', headers=headers)
    assert [item['name'] for item in listed.json()] == ['A segundo', 'Z inativa', 'Z primeiro']
    assert [item['featured'] for item in listed.json()] == [True, False, False]

    catalog_before_deactivation = await client.get('/api/catalog/knowledge-bases')
    assert [item['name'] for item in catalog_before_deactivation.json()] == ['A segundo', 'Z primeiro']
    assert [item['featured'] for item in catalog_before_deactivation.json()] == [True, False]

    deactivated = await client.patch(
        f"/api/admin/knowledge-bases/{second.json()['id']}", headers=headers, json={'active': False}
    )
    assert deactivated.status_code == 200
    assert deactivated.json()['featured'] is False

    catalog = await client.get('/api/catalog/knowledge-bases')
    assert [item['name'] for item in catalog.json()] == ['Z primeiro']
    assert catalog.json()[0]['featured'] is False


@pytest.mark.asyncio
async def test_query_selects_active_records_and_persists_safe_metadata(client, collaborator_token, admin_token, monkeypatch):
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    model = await client.post('/api/admin/models', headers=admin_headers, json={
        'provider': 'gemini', 'displayName': 'Gemini personalizado', 'modelId': 'gemini-custom',
    })
    base = await client.post('/api/admin/knowledge-bases', headers=admin_headers, json={
        'name': 'Base customizada', 'fileSearchStoreId': 'fileSearchStores/custom',
    })
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='ok', sources=[])

    monkeypatch.setattr(ProviderGateway, 'query', fake_query)
    response = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {collaborator_token}'}, json={
        'sessionId': str(uuid4()), 'chatInput': 'pergunta sobre contabilidade',
        'modelId': model.json()['id'], 'knowledgeBaseId': base.json()['id'],
    })
    assert response.status_code == 200
    assert captured['provider'] == 'gemini'
    assert captured['model_id'] == 'gemini-custom'
    assert captured['file_search_store_id'] == 'fileSearchStores/custom'
    metadata = response.json()['messages'][1]['metadata']
    assert metadata['provider'] == 'gemini'
    assert metadata['model_id'] == 'gemini-custom'
    assert 'file_search_store_id' not in metadata
    assert 'api_key' not in str(metadata).lower()
    async with get_session_factory()() as db:
        messages = list(await db.scalars(select(Message).order_by(Message.created_at)))
        assert len(messages) == 2
        assert messages[0].provider_metadata == messages[1].provider_metadata
        metadata = messages[0].provider_metadata
        assert metadata is not None
        assert metadata['knowledge_base_id'] == base.json()['id']


@pytest.mark.asyncio
async def test_inactive_and_incompatible_selections_are_rejected(client, collaborator_token, admin_token, monkeypatch):
    headers = {'Authorization': f'Bearer {admin_token}'}
    model = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'openai', 'displayName': 'OpenAI', 'modelId': 'gpt-test',
    })
    base = await client.post('/api/admin/knowledge-bases', headers=headers, json={
        'name': 'Gemini RAG', 'fileSearchStoreId': 'fileSearchStores/gemini',
    })
    called = False

    async def fake_query(self, **kwargs):
        nonlocal called
        called = True
        return AgnoAnswer(text='não deveria chamar', sources=[])

    monkeypatch.setattr(ProviderGateway, 'query', fake_query)
    response = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {collaborator_token}'}, json={
        'sessionId': str(uuid4()), 'chatInput': 'pergunta sobre imposto',
        'modelId': model.json()['id'], 'knowledgeBaseId': base.json()['id'],
    })
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'knowledge_base_provider_mismatch'
    assert called is False

    await client.patch(f"/api/admin/models/{model.json()['id']}", headers=headers, json={'active': False})
    inactive_response = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {collaborator_token}'}, json={
        'sessionId': str(uuid4()), 'chatInput': 'pergunta sobre balanço', 'modelId': model.json()['id'],
    })
    assert inactive_response.status_code == 404
    assert inactive_response.json()['error']['code'] == 'model_not_available'


@pytest.mark.asyncio
async def test_guest_query_can_select_active_model_and_google_rag(client, admin_token, monkeypatch):
    headers = {'Authorization': f'Bearer {admin_token}'}
    model = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'gemini', 'displayName': 'Gemini guest', 'modelId': 'gemini-guest',
    })
    base = await client.post('/api/admin/knowledge-bases', headers=headers, json={
        'name': 'RAG guest', 'fileSearchStoreId': 'fileSearchStores/guest',
    })
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='ok guest', sources=[])

    monkeypatch.setattr(ProviderGateway, 'query', fake_query)
    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()), 'chatInput': 'Qual é o conteúdo principal desta base?',
        'modelId': model.json()['id'], 'knowledgeBaseId': base.json()['id'],
    })

    assert response.status_code == 200
    assert response.json()['answer'] == 'ok guest'
    assert response.json()['modelId'] == model.json()['id']
    assert response.json()['knowledgeBaseId'] == base.json()['id']
    assert response.json()['messages'][0]['metadata'] == response.json()['messages'][1]['metadata']
    assert captured['provider'] == 'gemini'
    assert captured['model_id'] == 'gemini-guest'
    assert captured['file_search_store_id'] == 'fileSearchStores/guest'



@pytest.mark.asyncio
async def test_openai_responses_client_is_mocked_without_fallback(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'test-only-openai-key')
    captured = {}

    class FakeResponses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return type('Response', (), {'output_text': 'resposta OpenAI'})()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured['client'] = kwargs
            self.responses = FakeResponses()

        async def close(self):
            captured['closed'] = True

    monkeypatch.setattr('app.services.openai_client.AsyncOpenAI', FakeOpenAI)
    answer = await OpenAIResponsesClient().query(
        prompt='pergunta', history=[{'role': 'user', 'content': 'histórico'}], model_id='gpt-test'
    )
    assert answer.text == 'resposta OpenAI'
    assert captured['client']['api_key'] == 'test-only-openai-key'
    assert captured['model'] == 'gpt-test'
    assert 'tools' not in captured
    assert 'include' not in captured
    assert captured['closed'] is True


@pytest.mark.asyncio
async def test_openai_responses_client_adds_one_input_image_per_item(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'test-only-openai-key')
    captured = {}

    class FakeResponses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return type('Response', (), {'output_text': 'ok'})()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

        async def close(self):
            pass

    monkeypatch.setattr('app.services.openai_client.AsyncOpenAI', FakeOpenAI)
    images = ['data:image/png;base64,one', 'data:image/jpeg;base64,two']
    await OpenAIResponsesClient().query(prompt='pergunta', history=[], model_id='gpt-test', images=images)

    content = captured['input'][-1]['content']
    assert [item['type'] for item in content] == ['input_text', 'input_image', 'input_image']
    assert [item['image_url'] for item in content[1:]] == images


@pytest.mark.asyncio
async def test_openai_missing_key_preserves_configuration_error(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', None)

    with pytest.raises(AgnoError) as raised:
        await OpenAIResponsesClient().query(prompt='pergunta', history=[], model_id='gpt-test')

    assert raised.value.code == 'openai_not_configured'


@pytest.mark.asyncio
async def test_openai_timeout_preserves_code_and_closes_client(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'test-only-openai-key')
    captured = {}

    class FakeResponses:
        async def create(self, **kwargs):
            raise asyncio.TimeoutError

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

        async def close(self):
            captured['closed'] = True

    monkeypatch.setattr('app.services.openai_client.AsyncOpenAI', FakeOpenAI)
    with pytest.raises(AgnoError) as raised:
        await OpenAIResponsesClient().query(prompt='pergunta', history=[], model_id='gpt-test')

    assert raised.value.code == 'openai_timeout'
    assert captured['closed'] is True


@pytest.mark.asyncio
async def test_openai_rate_limit_preserves_code(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'test-only-openai-key')

    class RateLimitError(Exception):
        pass

    class FakeResponses:
        async def create(self, **kwargs):
            raise RateLimitError

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

        async def close(self):
            pass

    monkeypatch.setattr('app.services.openai_client.AsyncOpenAI', FakeOpenAI)
    with pytest.raises(AgnoError) as raised:
        await OpenAIResponsesClient().query(prompt='pergunta', history=[], model_id='gpt-test')

    assert raised.value.code == 'openai_rate_limit'
@pytest.mark.asyncio
async def test_openai_web_search_payload_and_dict_citations(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'test-only-openai-key')
    captured = {}
    response = {
        'output_text': 'resposta com fontes',
        'output': [{
            'type': 'message',
            'content': [{
                'type': 'output_text',
                'annotations': [
                    {'type': 'url_citation', 'url': 'https://receita.test/icms', 'title': 'ICMS oficial'},
                    {'type': 'url_citation', 'url': 'ftp://invalid.test', 'title': 'Inválida'},
                    {'type': 'url_citation', 'url': 'https://receita.test/icms', 'title': 'Duplicada'},
                    {'type': 'url_citation', 'url': 'https://gov.test/lei', 'title': ''},
                ],
            }],
        }],
    }

    class FakeResponses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return response

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

        async def close(self):
            captured['closed'] = True

    monkeypatch.setattr('app.services.openai_client.AsyncOpenAI', FakeOpenAI)
    answer = await OpenAIResponsesClient().query(
        prompt='Qual a alíquota atual do ICMS?',
        history=[],
        model_id='gpt-test',
        enable_web_search=True,
    )

    assert captured['instructions'].startswith('Você é um Especialista Contábil')
    assert captured['tools'] == [{'type': 'web_search_preview', 'search_context_size': 'medium'}]
    assert captured['include'] == ['web_search_call.action.sources']
    assert [(source.uri, source.title) for source in answer.sources] == [
        ('https://receita.test/icms', 'ICMS oficial'),
        ('https://gov.test/lei', 'Fonte consultada'),
    ]
    assert captured['closed'] is True


@pytest.mark.asyncio
async def test_openai_object_citations_are_limited_to_twenty(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'test-only-openai-key')
    annotations = [
        SimpleNamespace(url=f'https://gov.test/{index}', title=f'Fonte {index}')
        for index in range(21)
    ]
    response = SimpleNamespace(
        output_text='resposta',
        output=[SimpleNamespace(content=[SimpleNamespace(annotations=annotations)])],
    )

    class FakeResponses:
        async def create(self, **kwargs):
            return response

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

        async def close(self):
            pass

    monkeypatch.setattr('app.services.openai_client.AsyncOpenAI', FakeOpenAI)
    answer = await OpenAIResponsesClient().query(
        prompt='Qual o prazo de uma obrigação acessória?',
        history=[],
        model_id='gpt-test',
        enable_web_search=True,
    )

    assert len(answer.sources) == 20
    assert answer.sources[-1].uri == 'https://gov.test/19'


@pytest.mark.asyncio
async def test_openai_model_without_rag_enables_web_search(client, admin_token, monkeypatch):
    headers = {'Authorization': f'Bearer {admin_token}'}
    model = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'openai', 'displayName': 'OpenAI', 'modelId': 'gpt-test',
    })
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='resposta atual', sources=[])

    monkeypatch.setattr(OpenAIResponsesClient, 'query', fake_query)
    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'Qual o prazo atual do ICMS para uma empresa?',
        'modelId': model.json()['id'],
    })

    assert response.status_code == 200
    assert captured['enable_web_search'] is True
    assert captured['model_id'] == 'gpt-test'

    assert response.json()['sources'] == []


@pytest.mark.asyncio
async def test_gemini_without_rag_is_rejected_before_provider(client, admin_token, monkeypatch):
    model = await client.post('/api/admin/models', headers={'Authorization': f'Bearer {admin_token}'}, json={
        'provider': 'gemini', 'displayName': 'Gemini sem RAG', 'modelId': 'gemini-no-rag',
    })
    called = False

    async def fail_if_called(self, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('provider não deveria ser chamado')

    monkeypatch.setattr(ProviderGateway, 'query', fail_if_called)
    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()),
        'chatInput': 'pergunta contábil sem base',
        'modelId': model.json()['id'],
    })

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'knowledge_base_required'
    assert called is False
@pytest.mark.asyncio
async def test_gemini_gateway_does_not_receive_web_search_option(monkeypatch):
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='gemini', sources=[])

    monkeypatch.setattr(AgnoGeminiClient, 'query', fake_query)
    await ProviderGateway().query(
        provider='gemini',
        model_id='gemini-test',
        file_search_store_id='fileSearchStores/test',
        prompt='Qual a alíquota do ICMS?',
        history=[],
        enable_web_search=True,
    )

    assert 'enable_web_search' not in captured



@pytest.mark.asyncio
async def test_guest_cannot_select_unknown_catalog_records_or_invoke_provider(client, monkeypatch):
    called = False

    async def fail_if_called(self, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('provider não deveria ser chamado')

    monkeypatch.setattr(ProviderGateway, 'query', fail_if_called)
    response = await client.post('/api/chat/query', json={
        'sessionId': str(uuid4()), 'chatInput': 'pergunta sobre tributos', 'modelId': str(uuid4()), 'knowledgeBaseId': str(uuid4()),
    })
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'model_not_available'
    assert called is False


@pytest.mark.asyncio
async def test_catalog_validation_rejects_secrets_and_invalid_store_ids(client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    secret_model = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'openai', 'displayName': 'Não salvar', 'modelId': 'sk-not-a-model',
    })
    assert secret_model.status_code == 422
    empty_model = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'openai', 'displayName': 'Vazio', 'modelId': '   ',
    })
    assert empty_model.status_code == 422
    invalid_store = await client.post('/api/admin/knowledge-bases', headers=headers, json={
        'name': 'Inválida', 'fileSearchStoreId': 'stores/not-gemini-file-search',
    })
    assert invalid_store.status_code == 422
    invalid_provider = await client.post('/api/admin/models', headers=headers, json={
        'provider': 'anthropic', 'displayName': 'Inválido', 'modelId': 'model',
    })
    assert invalid_provider.status_code == 422


@pytest.mark.asyncio
async def test_explicit_null_knowledge_base_disables_legacy_store(client, collaborator_token, admin_token, monkeypatch):
    model = await client.post('/api/admin/models', headers={'Authorization': f'Bearer {admin_token}'}, json={
        'provider': 'openai', 'displayName': 'OpenAI sem RAG', 'modelId': 'gpt-no-rag',
    })
    assert model.status_code == 201
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='sem base', sources=[])

    monkeypatch.setattr(ProviderGateway, 'query', fake_query)
    response = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {collaborator_token}'}, json={
        'sessionId': str(uuid4()), 'chatInput': 'pergunta sobre ICMS',
        'modelId': model.json()['id'], 'knowledgeBaseId': None,
    })
    assert response.status_code == 200
    assert captured['file_search_store_id'] is None
    assert captured['use_legacy_knowledge_base'] is False
    assert captured['enable_web_search'] is True
