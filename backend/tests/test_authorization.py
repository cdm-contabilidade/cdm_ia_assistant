from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect

from app.core.database import get_engine, get_session_factory
from app.models import Group, GroupResourceGrant, UserPermissionOverride
from app.services.agno_client import AgnoAnswer
from app.services.provider_gateway import ProviderGateway


async def authorization_group(client, admin_token, collaborator_token, knowledge_base_id=None, web_search=False):
    user = await client.get('/api/auth/me', headers={'Authorization': f'Bearer {collaborator_token}'})
    group = await client.post('/api/admin/groups', headers={'Authorization': f'Bearer {admin_token}'}, json={'name': f'Group {uuid4()}'})
    assert group.status_code == 201
    group_id = group.json()['id']
    members = await client.put(
        f'/api/admin/groups/{group_id}/members',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'userIds': [user.json()['id']]},
    )
    assert members.status_code == 200
    grants = await client.put(
        f'/api/admin/groups/{group_id}/grants',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'knowledgeBaseIds': [knowledge_base_id] if knowledge_base_id else [], 'webSearch': web_search},
    )
    assert grants.status_code == 200
    return group_id, user.json()['id']


@pytest.mark.asyncio
async def test_catalog_and_query_require_authentication(client):
    assert (await client.get('/api/catalog/models')).status_code == 401
    assert (await client.get('/api/ai-models')).status_code == 401
    assert (await client.get('/api/catalog/knowledge-bases')).status_code == 401
    response = await client.post('/api/chat/query', json={'sessionId': str(uuid4()), 'chatInput': 'pergunta'})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_group_grant_catalog_and_individual_deny(client, admin_token, collaborator_token):
    base = await client.post(
        '/api/admin/knowledge-bases',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'name': 'Permitida', 'fileSearchStoreId': 'fileSearchStores/authorized'},
    )
    _, user_id = await authorization_group(client, admin_token, collaborator_token, base.json()['id'])
    catalog = await client.get('/api/catalog/knowledge-bases', headers={'Authorization': f'Bearer {collaborator_token}'})
    assert [item['id'] for item in catalog.json()] == [base.json()['id']]

    denied = await client.put(
        f'/api/admin/users/{user_id}/permission-overrides',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'overrides': [{'capability': 'knowledge_base', 'knowledgeBaseId': base.json()['id'], 'allowed': False}]},
    )
    assert denied.status_code == 200
    catalog = await client.get('/api/catalog/knowledge-bases', headers={'Authorization': f'Bearer {collaborator_token}'})
    assert catalog.json() == []


@pytest.mark.asyncio
async def test_forged_knowledge_base_id_is_denied_and_admin_bypasses(client, admin_token, collaborator_token, gemini_model_id, monkeypatch):
    base = await client.post(
        '/api/admin/knowledge-bases',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'name': 'Admin only', 'fileSearchStoreId': 'fileSearchStores/admin-only'},
    )
    response = await client.post(
        '/api/chat/query',
        headers={'Authorization': f'Bearer {collaborator_token}'},
        json={'sessionId': str(uuid4()), 'chatInput': 'consulta', 'knowledgeBaseId': base.json()['id'], 'modelId': gemini_model_id},
    )
    assert response.status_code == 404

    async def fake_query(self, **kwargs):
        return AgnoAnswer(text='ok', sources=[])

    monkeypatch.setattr(ProviderGateway, 'query', fake_query)
    response = await client.post(
        '/api/chat/query',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'sessionId': str(uuid4()), 'chatInput': 'consulta', 'knowledgeBaseId': base.json()['id'], 'modelId': gemini_model_id},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_web_search_requires_explicit_grant_and_group_grant_allows(client, admin_token, collaborator_token, monkeypatch):
    model = await client.post(
        '/api/admin/models',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'provider': 'openai', 'displayName': 'OpenAI', 'modelId': 'gpt-authz'},
    )
    payload = {'sessionId': str(uuid4()), 'chatInput': 'Qual a alíquota atual do ICMS?', 'modelId': model.json()['id']}
    denied = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {collaborator_token}'}, json=payload)
    assert denied.status_code == 403
    assert denied.json()['error']['code'] == 'web_search_not_allowed'

    _, user_id = await authorization_group(client, admin_token, collaborator_token, web_search=True)
    override = await client.put(
        f'/api/admin/users/{user_id}/permission-overrides',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'overrides': [{'capability': 'web_search', 'allowed': False}]},
    )
    assert override.status_code == 200
    denied_by_override = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {collaborator_token}'}, json=payload)
    assert denied_by_override.status_code == 403
    await client.put(
        f'/api/admin/users/{user_id}/permission-overrides',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'overrides': []},
    )
    captured = {}

    async def fake_query(self, **kwargs):
        captured.update(kwargs)
        return AgnoAnswer(text='ok', sources=[])

    monkeypatch.setattr(ProviderGateway, 'query', fake_query)
    allowed = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {collaborator_token}'}, json=payload)
    assert allowed.status_code == 200
    assert captured['enable_web_search'] is True


@pytest.mark.asyncio
async def test_authorization_indexes_reject_duplicate_group_and_user_targets(client, admin_token, collaborator_token):
    base = await client.post(
        '/api/admin/knowledge-bases',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'name': 'Unique target', 'fileSearchStoreId': 'fileSearchStores/unique-target'},
    )
    assert base.status_code == 201
    knowledge_base_id = UUID(base.json()['id'])
    user = await client.get('/api/auth/me', headers={'Authorization': f'Bearer {collaborator_token}'})
    user_id = UUID(user.json()['id'])

    async with get_session_factory()() as db:
        group = Group(name='Unique target group')
        db.add(group)
        await db.flush()
        group_id = group.id
        db.add_all([
            GroupResourceGrant(group_id=group_id, capability='knowledge_base', knowledge_base_id=knowledge_base_id),
            GroupResourceGrant(group_id=group_id, capability='web_search'),
        ])
        await db.commit()

        db.add(GroupResourceGrant(group_id=group_id, capability='knowledge_base', knowledge_base_id=knowledge_base_id))
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()

        db.add(GroupResourceGrant(group_id=group_id, capability='web_search'))
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()

        db.add(UserPermissionOverride(user_id=user_id, capability='knowledge_base', knowledge_base_id=knowledge_base_id, allowed=False))
        db.add(UserPermissionOverride(user_id=user_id, capability='web_search', allowed=False))
        await db.commit()

        db.add(UserPermissionOverride(user_id=user_id, capability='knowledge_base', knowledge_base_id=knowledge_base_id, allowed=True))
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()

        db.add(UserPermissionOverride(user_id=user_id, capability='web_search', allowed=True))
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()

    duplicate_payload = await client.put(
        f'/api/admin/users/{user_id}/permission-overrides',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'overrides': [
            {'capability': 'web_search', 'allowed': False},
            {'capability': 'web_search', 'allowed': True},
        ]},
    )
    assert duplicate_payload.status_code == 422

    async with get_engine().connect() as connection:
        index_names = await connection.run_sync(
            lambda sync_connection: {
                index['name']
                for table_name in ('group_resource_grants', 'user_permission_overrides')
                for index in inspect(sync_connection).get_indexes(table_name)
            }
        )
    assert {
        'ix_group_resource_grants_knowledge_base_id',
        'uq_group_resource_grants_knowledge_base_target',
        'uq_group_resource_grants_web_target',
        'ix_user_permission_overrides_knowledge_base_id',
        'uq_user_permission_overrides_knowledge_base_target',
        'uq_user_permission_overrides_web_target',
    } <= index_names
