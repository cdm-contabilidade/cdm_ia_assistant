"""Add encrypted provider API credentials.

Revision ID: 007_provider_credentials
Revises: 006_authorization_target_indexes

Only encrypted values are stored by the application.  The encryption master
key is supplied separately through PROVIDER_KEYS_ENCRYPTION_KEY and is never
part of this migration.
"""

from alembic import op
import sqlalchemy as sa


revision = '007_provider_credentials'
down_revision = '006_authorization_target_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'provider_credentials',
        sa.Column('provider', sa.String(length=20), primary_key=True),
        sa.Column('encrypted_api_key', sa.Text(), nullable=True),
        sa.Column('last4', sa.String(length=4), nullable=True),
        sa.Column('disabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("provider IN ('gemini', 'openai')", name='ck_provider_credentials_provider'),
    )


def downgrade() -> None:
    op.drop_table('provider_credentials')
