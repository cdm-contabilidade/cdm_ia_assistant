import pytest


@pytest.mark.asyncio
async def test_admin_can_manage_collaborators(client, admin_token):
    forbidden = await client.get('/api/admin/users')
    assert forbidden.status_code == 401

    created = await client.post('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'}, json={
        'email': 'worker@example.com',
        'name': 'Worker',
        'password': 'worker-pass-8',
    })
    assert created.status_code == 201
    user = created.json()
    assert user['role'] == 'collaborator'
    assert user['is_active'] is True
    assert user['is_blacklisted'] is False

    listed = await client.get('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'})
    assert listed.status_code == 200
    assert listed.json()[0]['email'] == 'worker@example.com'

    updated = await client.patch(f"/api/admin/users/{user['id']}", headers={'Authorization': f'Bearer {admin_token}'}, json={
        'is_active': False,
        'is_blacklisted': True,
        'password': 'new-worker-pass-8',
    })
    assert updated.status_code == 200
    assert updated.json()['is_active'] is False
    assert updated.json()['is_blacklisted'] is True
    assert (await client.post('/api/auth/login', json={'email': 'worker@example.com', 'password': 'new-worker-pass-8'})).status_code == 403


@pytest.mark.asyncio
async def test_collaborator_cannot_manage_users(client, collaborator_token):
    response = await client.get('/api/admin/users', headers={'Authorization': f'Bearer {collaborator_token}'})
    assert response.status_code == 403
