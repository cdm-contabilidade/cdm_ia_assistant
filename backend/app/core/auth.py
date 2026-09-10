from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

from .database import get_db
from .security import decode_token

_bearer = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail={'code': 'unauthorized', 'message': 'Autenticação necessária.'}, headers={'WWW-Authenticate': 'Bearer'})


async def _user_from_credentials(credentials: HTTPAuthorizationCredentials | None, db: AsyncSession) -> User | None:
    if credentials is None:
        return None
    try:
        user_id = decode_token(credentials.credentials, 'access')
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise unauthorized() from exc
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise unauthorized()
    if not user.is_active or user.is_blacklisted:
        raise unavailable()
    return user


def unavailable() -> HTTPException:
    return HTTPException(status_code=403, detail={'code': 'account_unavailable', 'message': 'A conta não está disponível.'})


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    return await _user_from_credentials(credentials, db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _user_from_credentials(credentials, db)
    if user is None:
        raise unauthorized()
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail={'code': 'admin_required', 'message': 'Acesso administrativo necessário.'})
    return user


def request_key(request: Request, user: User | None = None) -> str:
    host = request.client.host if request.client else 'unknown'
    return f'{host}:{user.id}' if user else host
