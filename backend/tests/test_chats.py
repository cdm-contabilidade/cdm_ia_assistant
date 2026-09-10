import pytest


@pytest.mark.asyncio
async def test_history_rename_delete_and_ownership(client, admin_token):
    first = await client.post('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'}, json={'email': 'first@example.com', 'name': 'First', 'password': 'strong-pass-8'})
    first_login = await client.post('/api/auth/login', json={'email': 'first@example.com', 'password': 'strong-pass-8'})
    first_token = first_login.json()['access_token']
    created = await client.post('/api/chats', headers={'Authorization': f'Bearer {first_token}'})
    chat_id = created.json()['id']
    renamed = await client.patch(f'/api/chats/{chat_id}', headers={'Authorization': f'Bearer {first_token}'}, json={'title': 'Consulta renomeada'})
    assert renamed.status_code == 200
    assert renamed.json()['title'] == 'Consulta renomeada'

    await client.post('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'}, json={'email': 'second@example.com', 'name': 'Second', 'password': 'strong-pass-8'})
    second = await client.post('/api/auth/login', json={'email': 'second@example.com', 'password': 'strong-pass-8'})
    second_token = second.json()['access_token']
    forbidden = await client.get(f'/api/chats/{chat_id}/messages', headers={'Authorization': f'Bearer {second_token}'})
    assert forbidden.status_code == 404
    assert (await client.delete(f'/api/chats/{chat_id}', headers={'Authorization': f'Bearer {first_token}'})).status_code == 204
    assert (await client.get('/api/chats', headers={'Authorization': f'Bearer {first_token}'})).json() == []
