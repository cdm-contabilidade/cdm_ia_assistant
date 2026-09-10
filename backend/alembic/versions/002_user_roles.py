"""Add roles and account status flags to users.

Revision ID: 002_user_roles
Revises: 001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = '002_user_roles'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='collaborator'))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('users', sa.Column('is_blacklisted', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('users', 'is_blacklisted')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'role')
