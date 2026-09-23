"""Authorization checks for resource and capability access.

The service deliberately does not treat membership in a group as an implicit
grant.  A grant must name the resource (or the explicit ``web_search``
capability), and a user's override is evaluated before all group grants.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GroupMembership, GroupResourceGrant, KnowledgeBase, User, UserPermissionOverride

KNOWLEDGE_BASE = 'knowledge_base'
WEB_SEARCH = 'web_search'


async def has_permission(
    db: AsyncSession,
    user: User,
    capability: str,
    knowledge_base_id: UUID | None = None,
) -> bool:
    """Return whether ``user`` may use a resource or capability."""
    if user.role == 'admin':
        return True

    override_query = select(UserPermissionOverride.allowed).where(
        UserPermissionOverride.user_id == user.id,
        UserPermissionOverride.capability == capability,
    )
    if knowledge_base_id is None:
        override_query = override_query.where(UserPermissionOverride.knowledge_base_id.is_(None))
    else:
        override_query = override_query.where(UserPermissionOverride.knowledge_base_id == knowledge_base_id)
    override = await db.scalar(override_query)
    if override is not None:
        return bool(override)

    group_query = (
        select(GroupResourceGrant.allowed)
        .join(GroupMembership, GroupMembership.group_id == GroupResourceGrant.group_id)
        .where(
            GroupMembership.user_id == user.id,
            GroupResourceGrant.capability == capability,
            GroupResourceGrant.allowed.is_(True),
        )
    )
    if knowledge_base_id is None:
        group_query = group_query.where(GroupResourceGrant.knowledge_base_id.is_(None))
    else:
        group_query = group_query.where(GroupResourceGrant.knowledge_base_id == knowledge_base_id)
    return (await db.scalar(group_query)) is not None


async def can_use_knowledge_base(db: AsyncSession, user: User, knowledge_base_id: UUID) -> bool:
    return await has_permission(db, user, KNOWLEDGE_BASE, knowledge_base_id)


async def can_use_web_search(db: AsyncSession, user: User) -> bool:
    return await has_permission(db, user, WEB_SEARCH)


async def accessible_knowledge_bases(db: AsyncSession, user: User) -> list[KnowledgeBase]:
    result = await db.scalars(
        select(KnowledgeBase)
        .where(KnowledgeBase.active.is_(True))
        .order_by(KnowledgeBase.featured.desc(), KnowledgeBase.name.asc())
    )
    bases = list(result)
    if user.role == 'admin':
        return bases
    accessible: list[KnowledgeBase] = []
    for knowledge_base in bases:
        if await can_use_knowledge_base(db, user, knowledge_base.id):
            accessible.append(knowledge_base)
    return accessible
