"""Add the multi-provider model and Gemini knowledge-base catalog.

Revision ID: 003_multi_provider_catalog
Revises: 002_user_roles
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '003_multi_provider_catalog'
down_revision = '002_user_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ai_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('display_name', sa.String(length=120), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("provider IN ('gemini', 'openai')", name='ck_ai_models_provider'),
        sa.UniqueConstraint('provider', 'model_id', name='uq_ai_models_provider_model_id'),
    )
    op.create_index('ix_ai_models_active', 'ai_models', ['active'], unique=False)

    op.create_table(
        'knowledge_bases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False, server_default='gemini'),
        sa.Column('file_search_store_id', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("provider = 'gemini'", name='ck_knowledge_bases_provider'),
        sa.UniqueConstraint('file_search_store_id', name='uq_knowledge_bases_file_search_store_id'),
    )
    op.create_index('ix_knowledge_bases_active', 'knowledge_bases', ['active'], unique=False)

    op.add_column(
        'messages',
        sa.Column('provider_metadata', postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('messages', 'provider_metadata')
    op.drop_index('ix_knowledge_bases_active', table_name='knowledge_bases')
    op.drop_table('knowledge_bases')
    op.drop_index('ix_ai_models_active', table_name='ai_models')
    op.drop_table('ai_models')
