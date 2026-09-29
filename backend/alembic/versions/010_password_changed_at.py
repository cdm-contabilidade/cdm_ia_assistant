"""Track password changes for session invalidation."""

from alembic import op
import sqlalchemy as sa


revision = '010_password_changed_at'
down_revision = '009_password_reset_requests'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_changed_at')
