"""Add exclusive featured knowledge-base support.

Revision ID: 004_featured_knowledge_base
Revises: 003_multi_provider_catalog
"""
from alembic import op
import sqlalchemy as sa


revision = '004_featured_knowledge_base'
down_revision = '003_multi_provider_catalog'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'knowledge_bases',
        sa.Column('featured', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_check_constraint(
        'ck_knowledge_bases_featured_active',
        'knowledge_bases',
        'NOT featured OR active',
    )
    op.create_index(
        'uq_knowledge_bases_featured',
        'knowledge_bases',
        ['featured'],
        unique=True,
        postgresql_where=sa.text('featured IS TRUE'),
        sqlite_where=sa.text('featured = 1'),
    )


def downgrade() -> None:
    op.drop_index('uq_knowledge_bases_featured', table_name='knowledge_bases')
    op.drop_constraint('ck_knowledge_bases_featured_active', 'knowledge_bases', type_='check')
    op.drop_column('knowledge_bases', 'featured')
