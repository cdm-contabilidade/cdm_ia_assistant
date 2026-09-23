from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.permissions import accessible_knowledge_bases
from app.models import AIModel, KnowledgeBase, User
from app.schemas import AIModelCatalogPublic, KnowledgeBaseCatalogPublic

router = APIRouter(prefix='/api/catalog', tags=['catalog'])
compat_router = APIRouter(prefix='/api', tags=['catalog'])


@router.get('/models', response_model=list[AIModelCatalogPublic])
@router.get('/ai-models', response_model=list[AIModelCatalogPublic], include_in_schema=False)
async def active_models(_: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[AIModel]:
    result = await db.scalars(select(AIModel).where(AIModel.active.is_(True)).order_by(AIModel.display_name.asc()))
    return list(result)


@router.get('/knowledge-bases', response_model=list[KnowledgeBaseCatalogPublic])
async def active_knowledge_bases(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[KnowledgeBase]:
    return await accessible_knowledge_bases(db, user)


@compat_router.get('/ai-models', response_model=list[AIModelCatalogPublic])
async def active_models_compat(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[AIModel]:
    return await active_models(user, db)


@compat_router.get('/knowledge-bases', response_model=list[KnowledgeBaseCatalogPublic])
async def active_knowledge_bases_compat(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[KnowledgeBase]:
    return await active_knowledge_bases(user, db)
