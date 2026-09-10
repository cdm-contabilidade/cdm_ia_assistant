import pytest


@pytest.mark.asyncio
async def test_auth_lifecycle_and_http_only_refresh(client, admin_token):
    public = await client.post('/api/auth/register', json={'email': 'USER@EXAMPLE.COM', 'name': 'Ana Silva', 'password': 'strong-pass-8'})
    assert public.status_code == 401
    created = await client.post('/api/auth/register', headers={'Authorization': f'Bearer {admin_token}'}, json={'email': 'USER@EXAMPLE.COM', 'name': 'Ana Silva', 'password': 'strong-pass-8'})
    assert created.status_code == 201
    assert created.json()['user']['email'] == 'user@example.com'
    assert created.json()['user']['role'] == 'collaborator'
    assert 'password_hash' not in created.text
    access = created.json()['access_token']

    me = await client.get('/api/auth/me', headers={'Authorization': f'Bearer {access}'})
    assert me.status_code == 200
    assert me.json()['name'] == 'Ana Silva'

    invalid = await client.post('/api/auth/login', json={'email': 'USER@EXAMPLE.COM', 'password': 'wrong-pass'})
    assert invalid.status_code == 401

    refreshed = await client.post('/api/auth/refresh')
    assert refreshed.status_code == 200
    assert refreshed.json()['access_token'] != access
    assert (await client.post('/api/auth/logout')).status_code == 204
    client.cookies.set('cdm_refresh_token', 'invalid')
    invalid_refresh = await client.post('/api/auth/refresh')
    assert invalid_refresh.status_code == 401
    assert 'Max-Age=0' in invalid_refresh.headers['set-cookie']

@pytest.mark.asyncio
async def test_expired_access_token_is_rejected(client):
    import jwt
    from app.core.config import get_settings

    token = jwt.encode({'sub': '00000000-0000-0000-0000-000000000000', 'type': 'access', 'exp': 1}, get_settings().jwt_secret_key, algorithm='HS256')
    response = await client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_blacklisted_collaborator_cannot_login_or_use_access_routes(client, admin_token):
    created = await client.post('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'}, json={
        'email': 'blocked@example.com',
        'name': 'Blocked',
        'password': 'blocked-pass-8',
    })
    user_id = created.json()['id']
    active_login = await client.post('/api/auth/login', json={'email': 'blocked@example.com', 'password': 'blocked-pass-8'})
    assert active_login.status_code == 200
    active_token = active_login.json()['access_token']
    updated = await client.patch(f'/api/admin/users/{user_id}', headers={'Authorization': f'Bearer {admin_token}'}, json={'is_blacklisted': True})
    assert updated.status_code == 200
    blocked_login = await client.post('/api/auth/login', json={'email': 'blocked@example.com', 'password': 'blocked-pass-8'})
    assert blocked_login.status_code == 403
    blocked_chat = await client.post('/api/chat/query', headers={'Authorization': f'Bearer {active_token}'}, json={'sessionId': '00000000-0000-0000-0000-000000000000', 'chatInput': 'não deve enviar'})
    assert blocked_chat.status_code == 403
