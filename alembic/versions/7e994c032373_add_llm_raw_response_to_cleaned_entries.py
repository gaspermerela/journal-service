"""add llm_raw_response to cleaned_entries

Revision ID: 7e994c032373
Revises: a7bdb66f23be
Create Date: 2025-11-17 19:17:45.904141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '7e994c032373'
down_revision: Union[str, None] = 'a7bdb66f23be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Add llm_raw_response column to cleaned_entries table
    op.add_column(
        'cleaned_entries',
        sa.Column('llm_raw_response', sa.Text(), nullable=True),
        schema=schema
    )


def downgrade() -> None:
    schema = get_schema()
    # Remove llm_raw_response column from cleaned_entries table
    op.drop_column('cleaned_entries', 'llm_raw_response', schema=schema)
