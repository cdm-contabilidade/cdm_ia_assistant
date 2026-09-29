from datetime import datetime, timezone

import jwt
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin, get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import error_body
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token, create_refresh_token, decode_token_claims, hash_password, token_predates_password_change,
    verify_password,
)
from app.core.permissions import can_use_web_search
from app.models import PasswordResetRequest, User
from app.schemas import (
    ChangePasswordRequest, LoginRequest, PasswordResetRequestCreate, PasswordResetResponse, RegisterRequest,
    TokenResponse, UserPublic,
)

router = APIRouter(prefix='/api/auth', tags=['auth'])
COOKIE_NAME = 'cdm_refresh_token'


def set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME, token, max_age=settings.refresh_token_expire_days * 86400,
        httponly=True, secure=settings.cookie_secure, samesite='lax', path='/',
    )


def invalid_refresh(request: Request) -> JSONResponse:
    result = JSONResponse(status_code=401, content=error_body(request, 'invalid_refresh_token', 'Sessão expirada. Faça login novamente.'), headers={'WWW-Authenticate': 'Bearer'})
    result.delete_cookie(COOKIE_NAME, path='/')
    return result


async def public_user(db: AsyncSession, user: User) -> UserPublic:
    result = UserPublic.model_validate(user)
    result.can_web_search = await can_use_web_search(db, user)
    return result


async def issue_tokens(user: User, response: Response, db: AsyncSession) -> TokenResponse:
    set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(access_token=create_access_token(user.id), user=await public_user(db, user))

@router.post('/register', response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    limiter.check(f'register:{request.client.host if request.client else "unknown"}')
    user = User(email=payload.email, name=payload.name, password_hash=hash_password(payload.password), role='collaborator')
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'email_in_use', 'message': 'Não foi possível criar a conta com este email.'})
    return await issue_tokens(user, response, db)


@router.post('/login', response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    limiter.check(f'login:{request.client.host if request.client else "unknown"}')
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={'code': 'invalid_credentials', 'message': 'Email ou senha inválidos.'})
    if not user.is_active or user.is_blacklisted:
        raise HTTPException(status_code=403, detail={'code': 'account_unavailable', 'message': 'A conta não está disponível.'})
    return await issue_tokens(user, response, db)


@router.post('/refresh', response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return invalid_refresh(request)
    try:
        claims = decode_token_claims(token, 'refresh')
        user_id = UUID(str(claims['sub']))
    except (jwt.InvalidTokenError, ValueError):
        return invalid_refresh(request)
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or token_predates_password_change(claims, user.password_changed_at) or not user.is_active or user.is_blacklisted:
        return invalid_refresh(request)
    return await issue_tokens(user, response, db)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path='/')


@router.post('/password', response_model=TokenResponse)
async def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail={'code': 'invalid_current_password', 'message': 'A senha atual está incorreta.'})
    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await db.commit()
    return await issue_tokens(user, response, db)


@router.post('/password-reset-requests', response_model=PasswordResetResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    payload: PasswordResetRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetResponse:
    limiter.check(f'password-reset:{request.client.host if request.client else "unknown"}')
    user = await db.scalar(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    if user is not None:
        pending = await db.scalar(
            select(PasswordResetRequest).where(
                PasswordResetRequest.user_id == user.id,
                PasswordResetRequest.status == 'pending',
            )
        )
        if pending is None:
            db.add(PasswordResetRequest(user_id=user.id))
            await db.commit()
    return PasswordResetResponse(message='Se o email estiver cadastrado, o administrador será notificado.')


@router.get('/me', response_model=UserPublic)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> UserPublic:
    return await public_user(db, user)
