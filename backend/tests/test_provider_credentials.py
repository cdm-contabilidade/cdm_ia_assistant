from uuid import uuid4

import pytest

from app.core.database import get_session_factory
from app.models import ProviderCredential
from app.services.agno_client import AgnoAnswer
from app.services.provider_credentials import ProviderCredentialError, decrypt_provider_key, resolve_provider_api_key
from app.services.provider_gateway import ProviderGateway
from app.services.openai_client import OpenAIResponsesClient


AUTH = lambda token: {'Authorization': f'Bearer {token}'}


@pytest.mark.asyncio
async def test_provider_key_endpoints_are_admin_only_masked_and_no_store(client, admin_token):
    unauthenticated = await client.get('/api/admin/provider-keys')
    assert unauthenticated.status_code == 401

    response = await client.put(
        '/api/admin/provider-keys/openai',
        headers=AUTH(admin_token),
        json={'apiKey': 'test-openai-secret-value'},
    )
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    body = response.json()
    assert body['configured'] is True
    assert body['source'] == 'database'
    assert body['last4'] == 'alue'
    assert body['maskedLast4'] == '****alue'
    assert 'test-openai-secret-value' not in response.text
    assert 'encrypted' not in response.text.lower()

    listed = await client.get('/api/admin/provider-keys', headers=AUTH(admin_token))
    assert listed.headers['cache-control'] == 'no-store'
    assert 'test-openai-secret-value' not in listed.text
    assert 'encrypted_api_key' not in listed.text

    async with get_session_factory()() as db:
        credential = await db.get(ProviderCredential, 'openai')
        assert credential is not None
        assert credential.encrypted_api_key != 'test-openai-secret-value'
        assert credential.encrypted_api_key is not None
        assert decrypt_provider_key(credential.encrypted_api_key) == 'test-openai-secret-value'


@pytest.mark.asyncio
async def test_database_key_precedes_environment_and_delete_requires_explicit_revert(client, admin_token, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'environment-secret-value')
    await client.put('/api/admin/provider-keys/openai', headers=AUTH(admin_token), json={'apiKey': 'database-secret-value'})
    async with get_session_factory()() as db:
        assert await resolve_provider_api_key(db, 'openai') == 'database-secret-value'

    deleted = await client.delete('/api/admin/provider-keys/openai', headers=AUTH(admin_token))
    assert deleted.status_code == 204
    disabled = await client.get('/api/admin/provider-keys/openai', headers=AUTH(admin_token))
    assert disabled.json()['configured'] is False
    assert disabled.json()['source'] == 'database'
    async with get_session_factory()() as db:
        assert await resolve_provider_api_key(db, 'openai') is None

    reverted = await client.post('/api/admin/provider-keys/openai/revert-to-env', headers=AUTH(admin_token))
    assert reverted.status_code == 200
    assert reverted.json()['configured'] is True
    assert reverted.json()['source'] == 'environment'


@pytest.mark.asyncio
async def test_import_env_encrypts_legacy_key(client, admin_token, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'google_api_key', 'legacy-google-secret')
    imported = await client.post('/api/admin/provider-keys/gemini/import-env', headers=AUTH(admin_token))
    assert imported.status_code == 200
    assert imported.json()['source'] == 'database'
    assert imported.json()['last4'] == 'cret'
    assert 'legacy-google-secret' not in imported.text


@pytest.mark.asyncio
async def test_corrupted_database_ciphertext_fails_closed(client, admin_token, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'openai_api_key', 'environment-must-not-be-used')
    async with get_session_factory()() as db:
        db.add(ProviderCredential(provider='openai', encrypted_api_key='not-fernet-ciphertext', last4='text'))
        await db.commit()
        with pytest.raises(ProviderCredentialError) as raised:
            await resolve_provider_api_key(db, 'openai')
    assert raised.value.code == 'provider_key_unavailable'


@pytest.mark.asyncio
async def test_storage_requires_encryption_master_key(client, admin_token, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), 'provider_keys_encryption_key', None)
    response = await client.put(
        '/api/admin/provider-keys/openai', headers=AUTH(admin_token), json={'apiKey': 'must-not-persist'},
    )
    assert response.status_code == 503
    assert response.json()['error']['code'] == 'provider_key_encryption_unavailable'
    assert 'must-not-persist' not in response.text


@pytest.mark.asyncio
async def test_openai_db_key_is_forwarded_to_runtime(client, admin_token, collaborator_token, grant_collaborator_access, monkeypatch):
    model = await client.post(
        '/api/admin/models', headers=AUTH(admin_token),
        json={'provider': 'openai', 'displayName': 'OpenAI DB key', 'modelId': 'gpt-db-key'},
    )
    await client.put('/api/admin/provider-keys/openai', headers=AUTH(admin_token), json={'apiKey': 'db-openai-key'})
    await grant_collaborator_access(web_search=True)
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='ok', sources=[])

    monkeypatch.setattr(OpenAIResponsesClient, 'query', fake_query)
    response = await client.post(
        '/api/chat/query', headers=AUTH(collaborator_token),
        json={'sessionId': str(uuid4()), 'chatInput': 'Qual a alíquota atual do ICMS?', 'modelId': model.json()['id']},
    )
    assert response.status_code == 200
    assert captured['api_key'] == 'db-openai-key'


@pytest.mark.asyncio
async def test_queries_require_explicit_active_model_and_rag_uses_gemini(client, admin_token, collaborator_token, grant_collaborator_access, monkeypatch):
    missing = await client.post(
        '/api/chat/query', headers=AUTH(collaborator_token),
        json={'sessionId': str(uuid4()), 'chatInput': 'pergunta contábil'},
    )
    assert missing.status_code == 400
    assert missing.json()['error']['code'] == 'model_required'

    inactive = await client.post(
        '/api/admin/models', headers=AUTH(admin_token),
        json={'provider': 'gemini', 'displayName': 'Inactive Gemini', 'modelId': 'gemini-inactive', 'active': False},
    )
    rejected = await client.post(
        '/api/chat/query', headers=AUTH(collaborator_token),
        json={'sessionId': str(uuid4()), 'chatInput': 'pergunta contábil', 'modelId': inactive.json()['id']},
    )
    assert rejected.status_code == 404
    assert rejected.json()['error']['code'] == 'model_not_available'

    model = await client.post(
        '/api/admin/models', headers=AUTH(admin_token),
        json={'provider': 'gemini', 'displayName': 'Active Gemini', 'modelId': 'gemini-active'},
    )
    base = await client.post(
        '/api/admin/knowledge-bases', headers=AUTH(admin_token),
        json={'name': 'RAG model', 'fileSearchStoreId': 'fileSearchStores/model-selection'},
    )
    await grant_collaborator_access([base.json()['id']])
    await client.put('/api/admin/provider-keys/gemini', headers=AUTH(admin_token), json={'apiKey': 'db-gemini-key'})
    captured = {}

    async def fake_gateway(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='ok', sources=[])

    monkeypatch.setattr(ProviderGateway, 'query', fake_gateway)
    response = await client.post(
        '/api/chat/query', headers=AUTH(collaborator_token),
        json={
            'sessionId': str(uuid4()), 'chatInput': 'pergunta contábil',
            'modelId': model.json()['id'], 'knowledgeBaseId': base.json()['id'],
        },
    )
    assert response.status_code == 200
    assert captured['provider'] == 'gemini'
    assert captured['api_key'] == 'db-gemini-key'
