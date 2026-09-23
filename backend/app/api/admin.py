from datetime import datetime, timezone
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models import (
    AIModel, Group, GroupMembership, GroupResourceGrant, KnowledgeBase, User, UserPermissionOverride,
)
from app.schemas import (
    AIModelCreate, AIModelPublic, AIModelUpdate, AdminUserUpdate, KnowledgeBaseCreate,
    KnowledgeBasePublic, KnowledgeBaseUpdate, RegisterRequest, UserPublic,
    GroupCreate, GroupGrantsReplace, GroupMembersReplace, GroupPublic, GroupUpdate,
    PermissionOverride, PermissionOverridesReplace, PermissionOverridePublic,
    ProviderKeyStatusPublic, ProviderKeyUpdate,
)
from app.services.provider_credentials import (
    ProviderCredentialError, ProviderName, disable_provider_api_key, environment_provider_api_key,
    provider_key_status, revert_provider_to_environment, store_provider_api_key,
)
from app.services.knowledge_base import set_featured

router = APIRouter(prefix='/api/admin', tags=['admin'])
logger = logging.getLogger(__name__)


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


def missing_group() -> HTTPException:
    return HTTPException(status_code=404, detail={'code': 'group_not_found', 'message': 'Grupo não encontrado.'})


async def group_view(db: AsyncSession, group: Group) -> GroupPublic:
    user_ids = list(await db.scalars(select(GroupMembership.user_id).where(GroupMembership.group_id == group.id)))
    grants = list(await db.scalars(select(GroupResourceGrant).where(GroupResourceGrant.group_id == group.id)))
    return GroupPublic(
        id=group.id,
        name=group.name,
        user_ids=user_ids,
        knowledge_base_ids=[
            grant.knowledge_base_id for grant in grants
            if grant.capability == 'knowledge_base' and grant.knowledge_base_id is not None
        ],
        web_search=any(grant.capability == 'web_search' and grant.allowed for grant in grants),
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.get('/groups', response_model=list[GroupPublic])
async def list_groups(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> list[GroupPublic]:
    groups = list(await db.scalars(select(Group).order_by(Group.name.asc())))
    return [await group_view(db, group) for group in groups]


@router.post('/groups', response_model=GroupPublic, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GroupPublic:
    group = Group(name=payload.name)
    db.add(group)
    try:
        await db.commit()
        await db.refresh(group)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'group_already_exists', 'message': 'Já existe um grupo com este nome.'}) from exc
    return await group_view(db, group)


@router.get('/groups/{group_id}', response_model=GroupPublic)
async def get_group(group_id: UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> GroupPublic:
    group = await db.get(Group, group_id)
    if group is None:
        raise missing_group()
    return await group_view(db, group)


@router.patch('/groups/{group_id}', response_model=GroupPublic)
async def update_group(
    group_id: UUID,
    payload: GroupUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GroupPublic:
    group = await db.get(Group, group_id)
    if group is None:
        raise missing_group()
    assert payload.name is not None
    group.name = payload.name
    group.updated_at = datetime.now(timezone.utc)
    try:
        await db.commit()
        await db.refresh(group)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail={'code': 'group_already_exists', 'message': 'Já existe um grupo com este nome.'}) from exc
    return await group_view(db, group)


@router.delete('/groups/{group_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> None:
    group = await db.get(Group, group_id)
    if group is None:
        raise missing_group()
    has_members = await db.scalar(select(GroupMembership.group_id).where(GroupMembership.group_id == group_id).limit(1))
    has_grants = await db.scalar(select(GroupResourceGrant.id).where(GroupResourceGrant.group_id == group_id).limit(1))
    if has_members is not None or has_grants is not None:
        raise HTTPException(status_code=409, detail={'code': 'group_not_empty', 'message': 'Remova membros e permissões antes de excluir o grupo.'})
    await db.delete(group)
    await db.commit()


@router.put('/groups/{group_id}/members', response_model=GroupPublic)
async def replace_group_members(
    group_id: UUID,
    payload: GroupMembersReplace,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GroupPublic:
    group = await db.get(Group, group_id)
    if group is None:
        raise missing_group()
    user_ids = list(dict.fromkeys(payload.user_ids))
    if user_ids:
        found = set(await db.scalars(select(User.id).where(User.id.in_(user_ids))))
        if found != set(user_ids):
            raise missing_user()
    await db.execute(delete(GroupMembership).where(GroupMembership.group_id == group_id))
    db.add_all([GroupMembership(group_id=group_id, user_id=user_id) for user_id in user_ids])
    group.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(group)
    return await group_view(db, group)


@router.put('/groups/{group_id}/grants', response_model=GroupPublic)
async def replace_group_grants(
    group_id: UUID,
    payload: GroupGrantsReplace,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GroupPublic:
    group = await db.get(Group, group_id)
    if group is None:
        raise missing_group()
    knowledge_base_ids = list(dict.fromkeys(payload.knowledge_base_ids))
    if knowledge_base_ids:
        found = set(await db.scalars(select(KnowledgeBase.id).where(KnowledgeBase.id.in_(knowledge_base_ids))))
        if found != set(knowledge_base_ids):
            raise missing_knowledge_base()
    await db.execute(delete(GroupResourceGrant).where(GroupResourceGrant.group_id == group_id))
    db.add_all([
        GroupResourceGrant(group_id=group_id, capability='knowledge_base', knowledge_base_id=knowledge_base_id)
        for knowledge_base_id in knowledge_base_ids
    ])
    if payload.web_search:
        db.add(GroupResourceGrant(group_id=group_id, capability='web_search', knowledge_base_id=None))
    group.updated_at = datetime.now(timezone.utc)
    try:
        await db.commit()
        await db.refresh(group)
    except IntegrityError as exc:
        await db.rollback()
        raise permission_conflict() from exc
    return await group_view(db, group)


def missing_target_user() -> HTTPException:
    return HTTPException(status_code=404, detail={'code': 'user_not_found', 'message': 'Usuário não encontrado.'})


def permission_conflict() -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={'code': 'permission_target_conflict', 'message': 'Já existe uma permissão para este recurso.'},
    )


@router.get('/users/{user_id}/permission-overrides', response_model=list[PermissionOverridePublic])
async def list_permission_overrides(
    user_id: UUID,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserPermissionOverride]:
    if await db.get(User, user_id) is None:
        raise missing_target_user()
    return list(await db.scalars(
        select(UserPermissionOverride)
        .where(UserPermissionOverride.user_id == user_id)
        .order_by(UserPermissionOverride.capability.asc(), UserPermissionOverride.knowledge_base_id.asc())
    ))


@router.put('/users/{user_id}/permission-overrides', response_model=list[PermissionOverridePublic])
async def replace_permission_overrides(
    user_id: UUID,
    payload: PermissionOverridesReplace,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserPermissionOverride]:
    if await db.get(User, user_id) is None:
        raise missing_target_user()
    knowledge_base_ids = [item.knowledge_base_id for item in payload.overrides if item.knowledge_base_id is not None]
    if knowledge_base_ids:
        found = set(await db.scalars(select(KnowledgeBase.id).where(KnowledgeBase.id.in_(knowledge_base_ids))))
        if found != set(knowledge_base_ids):
            raise missing_knowledge_base()
    await db.execute(delete(UserPermissionOverride).where(UserPermissionOverride.user_id == user_id))
    db.add_all([
        UserPermissionOverride(
            user_id=user_id,
            capability=item.capability,
            knowledge_base_id=item.knowledge_base_id,
            allowed=item.allowed,
        )
        for item in payload.overrides
    ])
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise permission_conflict() from exc
    return list(await db.scalars(
        select(UserPermissionOverride)
        .where(UserPermissionOverride.user_id == user_id)
        .order_by(UserPermissionOverride.capability.asc(), UserPermissionOverride.knowledge_base_id.asc())
    ))


def provider_key_error(exc: ProviderCredentialError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={'code': exc.code, 'message': exc.message})


def public_provider_status(status_value) -> ProviderKeyStatusPublic:
    return ProviderKeyStatusPublic(
        provider=status_value.provider,
        configured=status_value.configured,
        source=status_value.source,
        last4=status_value.last4,
        masked_last4=status_value.masked_last4,
        updated_at=status_value.updated_at,
        disabled=status_value.disabled,
    )


def no_store(response: Response) -> None:
    response.headers['Cache-Control'] = 'no-store'


@router.get('/provider-keys', response_model=list[ProviderKeyStatusPublic])
async def list_provider_keys(
    response: Response,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ProviderKeyStatusPublic]:
    no_store(response)
    return [public_provider_status(await provider_key_status(db, provider)) for provider in ('gemini', 'openai')]


@router.get('/provider-keys/{provider}', response_model=ProviderKeyStatusPublic)
async def get_provider_key(
    provider: ProviderName,
    response: Response,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProviderKeyStatusPublic:
    no_store(response)
    return public_provider_status(await provider_key_status(db, provider))


@router.put('/provider-keys/{provider}', response_model=ProviderKeyStatusPublic)
async def put_provider_key(
    provider: ProviderName,
    payload: ProviderKeyUpdate,
    response: Response,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProviderKeyStatusPublic:
    no_store(response)
    try:
        await store_provider_api_key(db, provider, payload.api_key)
        await db.commit()
    except ProviderCredentialError as exc:
        await db.rollback()
        raise provider_key_error(exc) from exc
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail={'code': 'provider_key_write_conflict', 'message': 'A credencial do provedor foi alterada simultaneamente.'},
        ) from exc
    logger.info('provider credential updated', extra={'provider': provider, 'operation': 'update'})
    return public_provider_status(await provider_key_status(db, provider))


@router.delete('/provider-keys/{provider}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider_key(
    provider: ProviderName,
    response: Response,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    no_store(response)
    try:
        await disable_provider_api_key(db, provider)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail={'code': 'provider_key_write_conflict', 'message': 'A credencial do provedor foi alterada simultaneamente.'},
        ) from exc
    logger.info('provider credential disabled', extra={'provider': provider, 'operation': 'delete'})


@router.post('/provider-keys/{provider}/import-env', response_model=ProviderKeyStatusPublic)
async def import_provider_key_from_environment(
    provider: ProviderName,
    response: Response,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProviderKeyStatusPublic:
    no_store(response)
    api_key = environment_provider_api_key(provider)
    if api_key is None:
        raise HTTPException(
            status_code=503,
            detail={'code': 'provider_not_configured', 'message': 'Não existe uma credencial de ambiente para importar.'},
        )
    try:
        await store_provider_api_key(db, provider, api_key)
        await db.commit()
    except ProviderCredentialError as exc:
        await db.rollback()
        raise provider_key_error(exc) from exc
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail={'code': 'provider_key_write_conflict', 'message': 'A credencial do provedor foi alterada simultaneamente.'},
        ) from exc
    logger.info('provider credential imported from environment', extra={'provider': provider, 'operation': 'import-env'})
    return public_provider_status(await provider_key_status(db, provider))


@router.post('/provider-keys/{provider}/revert-to-env', response_model=ProviderKeyStatusPublic)
async def revert_provider_key_to_environment(
    provider: ProviderName,
    response: Response,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProviderKeyStatusPublic:
    no_store(response)
    await revert_provider_to_environment(db, provider)
    await db.commit()
    logger.info('provider credential reverted to environment', extra={'provider': provider, 'operation': 'revert-to-env'})
    return public_provider_status(await provider_key_status(db, provider))


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
