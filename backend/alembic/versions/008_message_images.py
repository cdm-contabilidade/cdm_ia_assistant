"""Persist chat image bytes per message.

Revision ID: 008_message_images
Revises: 007_provider_credentials

Raw image bytes are keyed by (message_id, position) so the history endpoint
can rebuild data URLs without a separate asset store.
"""

from alembic import op
import sqlalchemy as sa


revision = '008_message_images'
down_revision = '007_provider_credentials'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'message_images',
        sa.Column('message_id', sa.Uuid(), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('mime', sa.String(length=20), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint('message_id', 'position', name='pk_message_images'),
        sa.CheckConstraint('position BETWEEN 0 AND 3', name='ck_message_images_position'),
    )


def downgrade() -> None:
    op.drop_table('message_images')
