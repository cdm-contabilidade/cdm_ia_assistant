"""Enforce unique logical authorization targets and index KBase FKs.

Revision ID: 006_authorization_target_indexes
Revises: 005_group_resource_authorization

The partial indexes are deliberately dialect-specific because both PostgreSQL
and SQLite support partial indexes but use separate Alembic dialect options.
They keep the nullable web-search target unique without allowing a KB grant
to collide with the web-search row.
"""

from alembic import op
import sqlalchemy as sa


revision = '006_authorization_target_indexes'
down_revision = '005_group_resource_authorization'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'ix_group_resource_grants_knowledge_base_id',
        'group_resource_grants',
        ['knowledge_base_id'],
    )
    op.create_index(
        'uq_group_resource_grants_knowledge_base_target',
        'group_resource_grants',
        ['group_id', 'knowledge_base_id'],
        unique=True,
        postgresql_where=sa.text("capability = 'knowledge_base'"),
        sqlite_where=sa.text("capability = 'knowledge_base'"),
    )
    op.create_index(
        'uq_group_resource_grants_web_target',
        'group_resource_grants',
        ['group_id'],
        unique=True,
        postgresql_where=sa.text("capability = 'web_search'"),
        sqlite_where=sa.text("capability = 'web_search'"),
    )
    op.create_index(
        'ix_user_permission_overrides_knowledge_base_id',
        'user_permission_overrides',
        ['knowledge_base_id'],
    )
    op.create_index(
        'uq_user_permission_overrides_knowledge_base_target',
        'user_permission_overrides',
        ['user_id', 'knowledge_base_id'],
        unique=True,
        postgresql_where=sa.text("capability = 'knowledge_base'"),
        sqlite_where=sa.text("capability = 'knowledge_base'"),
    )
    op.create_index(
        'uq_user_permission_overrides_web_target',
        'user_permission_overrides',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("capability = 'web_search'"),
        sqlite_where=sa.text("capability = 'web_search'"),
    )


def downgrade() -> None:
    op.drop_index('uq_user_permission_overrides_web_target', table_name='user_permission_overrides')
    op.drop_index('uq_user_permission_overrides_knowledge_base_target', table_name='user_permission_overrides')
    op.drop_index('ix_user_permission_overrides_knowledge_base_id', table_name='user_permission_overrides')
    op.drop_index('uq_group_resource_grants_web_target', table_name='group_resource_grants')
    op.drop_index('uq_group_resource_grants_knowledge_base_target', table_name='group_resource_grants')
    op.drop_index('ix_group_resource_grants_knowledge_base_id', table_name='group_resource_grants')
