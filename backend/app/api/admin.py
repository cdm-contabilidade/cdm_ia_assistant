from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models import User
from app.schemas import AdminUserUpdate, RegisterRequest, UserPublic

router = APIRouter(prefix='/api/admin', tags=['admin'])


def missing_user() -> HTTPException:
    return HTTPException(status_code=404, detail={'code': 'collaborator_not_found', 'message': 'Colaborador não encontrado.'})


@router.get('/users', response_model=list[UserPublic])
async def list_collaborators(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    result = await db.scalars(select(User).where(User.role == 'collaborator').order_by(User.name.asc()))
    return list(result)


@router.post('/users', response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_collaborator(
    payload: RegisterRequest,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        role='collaborator',
        is_active=True,
        is_blacklisted=False,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'email_in_use', 'message': 'Não foi possível criar o colaborador com este email.'}) from exc
    return user


@router.patch('/users/{user_id}', response_model=UserPublic)
async def update_collaborator(
    user_id: UUID,
    payload: AdminUserUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.scalar(select(User).where(User.id == user_id, User.role == 'collaborator'))
    if user is None:
        raise missing_user()
    if payload.name is not None:
        user.name = ' '.join(payload.name.split())
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_blacklisted is not None:
        user.is_blacklisted = payload.is_blacklisted
    await db.commit()
    await db.refresh(user)
    return user
