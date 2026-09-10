"""Initial CDM schema.

Revision ID: 001_initial_schema
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_table(
        'chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_chats_user_id', 'chats', ['user_id'], unique=False)
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('has_image', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('image_metadata', postgresql.JSONB(), nullable=True),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='ck_messages_role'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_messages_chat_id', 'messages', ['chat_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_messages_chat_id', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_chats_user_id', table_name='chats')
    op.drop_table('chats')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
