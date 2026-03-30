"""add extra_permissions to users

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-30

"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.add_column(
            'users',
            sa.Column('extra_permissions', JSONB, nullable=False, server_default='[]')
        )
    else:
        op.add_column(
            'users',
            sa.Column('extra_permissions', sa.JSON, nullable=False, server_default='[]')
        )


def downgrade() -> None:
    op.drop_column('users', 'extra_permissions')
