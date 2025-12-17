"""add preferred_llm_model to user_preferences

Revision ID: 25dda16871b4
Revises: dc2d062ee961
Create Date: 2025-11-26 19:14:03.432715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '25dda16871b4'
down_revision: Union[str, None] = 'dc2d062ee961'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    op.add_column(
        'user_preferences',
        sa.Column('preferred_llm_model', sa.String(), nullable=True, comment="User's preferred LLM model for cleanup"),
        schema=schema
    )


def downgrade() -> None:
    schema = get_schema()
    op.drop_column('user_preferences', 'preferred_llm_model', schema=schema)
