"""Add password recovery requests."""

from alembic import op
import sqlalchemy as sa


revision = '009_password_reset_requests'
down_revision = '008_message_images'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'password_reset_requests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending', 'resolved')", name='ck_password_reset_requests_status'),
    )
    op.create_index(
        'ix_password_reset_requests_status_created_at',
        'password_reset_requests',
        ['status', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_password_reset_requests_status_created_at', table_name='password_reset_requests')
    op.drop_table('password_reset_requests')
