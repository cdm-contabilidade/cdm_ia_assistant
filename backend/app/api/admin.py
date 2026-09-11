from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models import AIModel, KnowledgeBase, User
from app.schemas import (
    AIModelCreate, AIModelPublic, AIModelUpdate, AdminUserUpdate, KnowledgeBaseCreate,
    KnowledgeBasePublic, KnowledgeBaseUpdate, RegisterRequest, UserPublic,
)
from app.services.knowledge_base import set_featured

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


def missing_model() -> HTTPException:
    return HTTPException(status_code=404, detail={'code': 'model_not_found', 'message': 'Modelo de IA não encontrado.'})


def missing_knowledge_base() -> HTTPException:
    return HTTPException(status_code=404, detail={'code': 'knowledge_base_not_found', 'message': 'Base de conhecimento não encontrada.'})


@router.get('/models', response_model=list[AIModelPublic])
@router.get('/ai-models', response_model=list[AIModelPublic], include_in_schema=False)
async def list_models(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> list[AIModel]:
    result = await db.scalars(select(AIModel).order_by(AIModel.display_name.asc()))
    return list(result)


@router.post('/models', response_model=AIModelPublic, status_code=status.HTTP_201_CREATED)
@router.post('/ai-models', response_model=AIModelPublic, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_model(
    payload: AIModelCreate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AIModel:
    model = AIModel(
        provider=payload.provider,
        display_name=payload.display_name,
        model_id=payload.model_id,
        active=payload.active,
    )
    db.add(model)
    try:
        await db.commit()
        await db.refresh(model)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'model_already_exists', 'message': 'Já existe um modelo com este provedor e identificador.'}) from exc
    return model


@router.get('/models/{model_id}', response_model=AIModelPublic)
@router.get('/ai-models/{model_id}', response_model=AIModelPublic, include_in_schema=False)
async def get_model(model_id: UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> AIModel:
    model = await db.get(AIModel, model_id)
    if model is None:
        raise missing_model()
    return model


@router.patch('/models/{model_id}', response_model=AIModelPublic)
@router.patch('/ai-models/{model_id}', response_model=AIModelPublic, include_in_schema=False)
async def update_model(
    model_id: UUID,
    payload: AIModelUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AIModel:
    model = await db.get(AIModel, model_id)
    if model is None:
        raise missing_model()
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    for key, value in changes.items():
        setattr(model, key, value)
    model.updated_at = datetime.now(timezone.utc)
    try:
        await db.commit()
        await db.refresh(model)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'model_already_exists', 'message': 'Já existe um modelo com este provedor e identificador.'}) from exc
    return model


@router.delete('/models/{model_id}', status_code=status.HTTP_204_NO_CONTENT)
@router.delete('/ai-models/{model_id}', status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def delete_model(model_id: UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> None:
    model = await db.get(AIModel, model_id)
    if model is None:
        raise missing_model()
    await db.delete(model)
    await db.commit()


@router.get('/knowledge-bases', response_model=list[KnowledgeBasePublic])
async def list_knowledge_bases(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> list[KnowledgeBase]:
    result = await db.scalars(select(KnowledgeBase).order_by(KnowledgeBase.featured.desc(), KnowledgeBase.name.asc()))
    return list(result)


@router.post('/knowledge-bases', response_model=KnowledgeBasePublic, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBase:
    knowledge_base = KnowledgeBase(
        name=payload.name,
        provider=payload.provider,
        file_search_store_id=payload.file_search_store_id,
        active=payload.active,
        featured=False,
    )
    db.add(knowledge_base)
    try:
        await set_featured(db, knowledge_base, payload.featured)
        await db.commit()
        await db.refresh(knowledge_base)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'knowledge_base_already_exists', 'message': 'Já existe uma base de conhecimento com este store.'}) from exc
    return knowledge_base


@router.get('/knowledge-bases/{knowledge_base_id}', response_model=KnowledgeBasePublic)
async def get_knowledge_base(knowledge_base_id: UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> KnowledgeBase:
    knowledge_base = await db.get(KnowledgeBase, knowledge_base_id)
    if knowledge_base is None:
        raise missing_knowledge_base()
    return knowledge_base


@router.patch('/knowledge-bases/{knowledge_base_id}', response_model=KnowledgeBasePublic)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    payload: KnowledgeBaseUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBase:
    knowledge_base = await db.get(KnowledgeBase, knowledge_base_id)
    if knowledge_base is None:
        raise missing_knowledge_base()
    changes = payload.model_dump(exclude_unset=True, by_alias=False)
    requested_featured = changes.pop('featured', knowledge_base.featured)
    for key, value in changes.items():
        setattr(knowledge_base, key, value)
    await set_featured(db, knowledge_base, requested_featured)
    knowledge_base.updated_at = datetime.now(timezone.utc)
    try:
        await db.commit()
        await db.refresh(knowledge_base)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'knowledge_base_already_exists', 'message': 'Já existe uma base de conhecimento com este store.'}) from exc
    return knowledge_base


@router.delete('/knowledge-bases/{knowledge_base_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(knowledge_base_id: UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> None:
    knowledge_base = await db.get(KnowledgeBase, knowledge_base_id)
    if knowledge_base is None:
        raise missing_knowledge_base()
    await db.delete(knowledge_base)
    await db.commit()
