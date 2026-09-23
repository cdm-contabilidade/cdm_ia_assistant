"""Add group and resource authorization.

Revision ID: 005_group_resource_authorization
Revises: 004_featured_knowledge_base

The fixed ``legacy-default`` group is intentional.  During this migration it
receives every existing knowledge base and web-search grant, and every
currently active, non-blacklisted collaborator is added to it.  This keeps
existing accounts working after authorization becomes default-deny.  It is a
one-time migration snapshot; administrators can subsequently narrow access by
changing the group's grants or moving users to other groups.
"""

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '005_group_resource_authorization'
down_revision = '004_featured_knowledge_base'
branch_labels = None
depends_on = None

LEGACY_GROUP_ID = uuid.UUID('00000000-0000-0000-0000-000000000005')
LEGACY_GROUP_NAME = 'legacy-default'


def upgrade() -> None:
    op.create_table(
        'groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('name', name='uq_groups_name'),
    )
    op.create_table(
        'group_memberships',
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('group_id', 'user_id'),
    )
    op.create_index('ix_group_memberships_user_id', 'group_memberships', ['user_id'], unique=False)
    op.create_table(
        'group_resource_grants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capability', sa.String(length=30), nullable=False),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('allowed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint(
            "(capability = 'web_search' AND knowledge_base_id IS NULL) OR "
            "(capability = 'knowledge_base' AND knowledge_base_id IS NOT NULL)",
            name='ck_group_resource_grants_target',
        ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
    )
    op.create_index(
        'ix_group_resource_grants_lookup', 'group_resource_grants',
        ['group_id', 'capability', 'knowledge_base_id'], unique=False,
    )
    op.create_table(
        'user_permission_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capability', sa.String(length=30), nullable=False),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('allowed', sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "(capability = 'web_search' AND knowledge_base_id IS NULL) OR "
            "(capability = 'knowledge_base' AND knowledge_base_id IS NOT NULL)",
            name='ck_user_permission_overrides_target',
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
    )
    op.create_index(
        'ix_user_permission_overrides_lookup', 'user_permission_overrides',
        ['user_id', 'capability', 'knowledge_base_id'], unique=False,
    )

    bind = op.get_bind()
    groups = sa.table('groups', sa.column('id', postgresql.UUID(as_uuid=True)), sa.column('name', sa.String()))
    memberships = sa.table(
        'group_memberships', sa.column('group_id', postgresql.UUID(as_uuid=True)),
        sa.column('user_id', postgresql.UUID(as_uuid=True)),
    )
    grants = sa.table(
        'group_resource_grants', sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('group_id', postgresql.UUID(as_uuid=True)), sa.column('capability', sa.String()),
        sa.column('knowledge_base_id', postgresql.UUID(as_uuid=True)), sa.column('allowed', sa.Boolean()),
    )
    op.bulk_insert(groups, [{'id': LEGACY_GROUP_ID, 'name': LEGACY_GROUP_NAME}])

    users = sa.table(
        'users', sa.column('id', postgresql.UUID(as_uuid=True)), sa.column('role', sa.String()),
        sa.column('is_active', sa.Boolean()), sa.column('is_blacklisted', sa.Boolean()),
    )
    knowledge_bases = sa.table('knowledge_bases', sa.column('id', postgresql.UUID(as_uuid=True)))
    active_users = bind.execute(
        sa.select(users.c.id).where(
            users.c.role == 'collaborator', users.c.is_active.is_(True), users.c.is_blacklisted.is_(False)
        )
    ).scalars().all()
    base_ids = bind.execute(sa.select(knowledge_bases.c.id)).scalars().all()
    op.bulk_insert(memberships, [{'group_id': LEGACY_GROUP_ID, 'user_id': user_id} for user_id in active_users])
    grant_rows = [{
        'id': uuid.uuid5(LEGACY_GROUP_ID, f'knowledge_base:{base_id}'),
        'group_id': LEGACY_GROUP_ID,
        'capability': 'knowledge_base',
        'knowledge_base_id': base_id,
        'allowed': True,
    } for base_id in base_ids]
    grant_rows.append({
        'id': uuid.uuid5(LEGACY_GROUP_ID, 'web_search'), 'group_id': LEGACY_GROUP_ID,
        'capability': 'web_search', 'knowledge_base_id': None, 'allowed': True,
    })
    op.bulk_insert(grants, grant_rows)


def downgrade() -> None:
    op.drop_index('ix_user_permission_overrides_lookup', table_name='user_permission_overrides')
    op.drop_table('user_permission_overrides')
    op.drop_index('ix_group_resource_grants_lookup', table_name='group_resource_grants')
    op.drop_table('group_resource_grants')
    op.drop_index('ix_group_memberships_user_id', table_name='group_memberships')
    op.drop_table('group_memberships')
    op.drop_table('groups')
