"""add completion_required_docs to cases

Revision ID: a1b2c3d4e5f6
Revises: 4734c3140a49
Create Date: 2026-03-21

"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4734c3140a49'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS completion_required_docs JSONB"
    )


def downgrade() -> None:
    op.drop_column('cases', 'completion_required_docs')
