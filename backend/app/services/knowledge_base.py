from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeBase


async def set_featured(db: AsyncSession, knowledge_base: KnowledgeBase, featured: bool) -> None:
    """Apply the featured flag while preserving the one-active-featured invariant."""
    if not featured or not knowledge_base.active:
        knowledge_base.featured = False
        return

    now = datetime.now(timezone.utc)
    await db.execute(
        update(KnowledgeBase)
        .where(KnowledgeBase.id != knowledge_base.id, KnowledgeBase.featured.is_(True))
        .values(featured=False, updated_at=now)
    )
    knowledge_base.featured = True
