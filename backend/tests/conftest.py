import os
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import uuid4

# Tests must never touch a real database. These assignments must overwrite, not
# default, because backend/.env sets SSH_ENABLE=true and database_dsn() would
# otherwise redirect the connection through the SSH tunnel to the remote Postgres.
TEST_DB_PATH = (Path(__file__).resolve().parent / 'cdm_test.db').as_posix()
os.environ['DATABASE_URL'] = f'sqlite+aiosqlite:///{TEST_DB_PATH}'
os.environ['SSH_ENABLE'] = 'false'
os.environ['APP_ENV'] = 'testing'
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-with-at-least-32-characters')
os.environ.setdefault('GOOGLE_API_KEY', 'test-google-api-key')
os.environ.setdefault('PROVIDER_KEYS_ENCRYPTION_KEY', 'mF6jtMeIfoXlr1-A6n6AROEYHCM-nJQPL3rpJkMTFdE=')
os.environ.setdefault('GOOGLE_FILE_SEARCH_STORE_NAME', 'fileSearchStores/test-store')
os.environ.setdefault('FRONTEND_ORIGINS', 'http://localhost:5173')
os.environ.setdefault('RATE_LIMIT_MAX_ATTEMPTS', '30')

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import Base, get_db, get_engine, get_session_factory
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.models import Chat, Message, User
from backend.main import app


async def override_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def database() -> AsyncGenerator[None, None]:
    app.dependency_overrides[get_db] = override_db
    get_settings().rate_limit_max_attempts = 30
    limiter._events.clear()
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()
    await get_engine().dispose()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as http:
        yield http

@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    async with get_session_factory()() as db:
        db.add(User(email='admin@test.example', name='admin', password_hash=hash_password('admin-pass-8'), role='admin'))
        await db.commit()
    response = await client.post('/api/auth/login', json={'email': 'admin@test.example', 'password': 'admin-pass-8'})
    assert response.status_code == 200
    return response.json()['access_token']


@pytest_asyncio.fixture
async def collaborator_token(client: AsyncClient, admin_token: str) -> str:
    created = await client.post('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'}, json={
        'email': 'collaborator@test.example',
        'name': 'Collaborator',
        'password': 'collaborator-pass-8',
    })
    assert created.status_code == 201
    logged_in = await client.post('/api/auth/login', json={'email': 'collaborator@test.example', 'password': 'collaborator-pass-8'})
    assert logged_in.status_code == 200
    return logged_in.json()['access_token']


@pytest_asyncio.fixture
async def gemini_model_id(client: AsyncClient, admin_token: str) -> str:
    created = await client.post(
        '/api/admin/models',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'provider': 'gemini', 'displayName': 'Test Gemini', 'modelId': 'gemini-test-active'},
    )
    assert created.status_code == 201
    return created.json()['id']


@pytest_asyncio.fixture
async def grant_collaborator_access(client: AsyncClient, admin_token: str, collaborator_token: str):
    """Return a test-only helper for explicitly granting collaborator access."""
    user = await client.get('/api/auth/me', headers={'Authorization': f'Bearer {collaborator_token}'})
    assert user.status_code == 200

    async def grant(knowledge_base_ids: list[str] | None = None, web_search: bool = False) -> str:
        group = await client.post(
            '/api/admin/groups',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'name': f'Test group {uuid4()}'},
        )
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
            json={'knowledgeBaseIds': knowledge_base_ids or [], 'webSearch': web_search},
        )
        assert grants.status_code == 200
        return group_id

    return grant
