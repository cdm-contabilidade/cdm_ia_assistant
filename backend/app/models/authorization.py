import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


PermissionCapability = Literal['knowledge_base', 'web_search']


class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    memberships: Mapped[list['GroupMembership']] = relationship(back_populates='group', cascade='all, delete-orphan')
    grants: Mapped[list['GroupResourceGrant']] = relationship(back_populates='group', cascade='all, delete-orphan')


class GroupMembership(Base):
    __tablename__ = 'group_memberships'
    __table_args__ = (Index('ix_group_memberships_user_id', 'user_id'),)

    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )

    group: Mapped['Group'] = relationship(back_populates='memberships')
    user: Mapped['User'] = relationship(back_populates='group_memberships')


class GroupResourceGrant(Base):
    __tablename__ = 'group_resource_grants'
    __table_args__ = (
        CheckConstraint(
            "(capability = 'web_search' AND knowledge_base_id IS NULL) OR "
            "(capability = 'knowledge_base' AND knowledge_base_id IS NOT NULL)",
            name='ck_group_resource_grants_target',
        ),
        Index('ix_group_resource_grants_lookup', 'group_id', 'capability', 'knowledge_base_id'),
        Index('ix_group_resource_grants_knowledge_base_id', 'knowledge_base_id'),
        Index(
            'uq_group_resource_grants_knowledge_base_target', 'group_id', 'knowledge_base_id',
            unique=True,
            postgresql_where=text("capability = 'knowledge_base'"),
            sqlite_where=text("capability = 'knowledge_base'"),
        ),
        Index(
            'uq_group_resource_grants_web_target', 'group_id',
            unique=True,
            postgresql_where=text("capability = 'web_search'"),
            sqlite_where=text("capability = 'web_search'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('groups.id', ondelete='CASCADE'), nullable=False
    )
    capability: Mapped[str] = mapped_column(String(30), nullable=False)
    knowledge_base_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=True
    )
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default='true')

    group: Mapped['Group'] = relationship(back_populates='grants')


class UserPermissionOverride(Base):
    __tablename__ = 'user_permission_overrides'
    __table_args__ = (
        CheckConstraint(
            "(capability = 'web_search' AND knowledge_base_id IS NULL) OR "
            "(capability = 'knowledge_base' AND knowledge_base_id IS NOT NULL)",
            name='ck_user_permission_overrides_target',
        ),
        Index('ix_user_permission_overrides_lookup', 'user_id', 'capability', 'knowledge_base_id'),
        Index('ix_user_permission_overrides_knowledge_base_id', 'knowledge_base_id'),
        Index(
            'uq_user_permission_overrides_knowledge_base_target', 'user_id', 'knowledge_base_id',
            unique=True,
            postgresql_where=text("capability = 'knowledge_base'"),
            sqlite_where=text("capability = 'knowledge_base'"),
        ),
        Index(
            'uq_user_permission_overrides_web_target', 'user_id',
            unique=True,
            postgresql_where=text("capability = 'web_search'"),
            sqlite_where=text("capability = 'web_search'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    capability: Mapped[str] = mapped_column(String(30), nullable=False)
    knowledge_base_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=True
    )
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user: Mapped['User'] = relationship(back_populates='permission_overrides')
