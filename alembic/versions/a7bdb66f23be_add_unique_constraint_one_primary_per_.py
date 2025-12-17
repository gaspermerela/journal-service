"""add_unique_constraint_one_primary_per_entry

Revision ID: a7bdb66f23be
Revises: 1f0f9b98ff0b
Create Date: 2025-11-15 15:56:04.577294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = 'a7bdb66f23be'
down_revision: Union[str, None] = '1f0f9b98ff0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Add partial unique index to ensure only one primary transcription per entry
    op.execute(f"""
        CREATE UNIQUE INDEX idx_one_primary_per_entry
        ON "{schema}".transcriptions (entry_id)
        WHERE is_primary = true
    """)


def downgrade() -> None:
    schema = get_schema()
    # Remove the partial unique index
    op.execute(f'DROP INDEX IF EXISTS "{schema}".idx_one_primary_per_entry')
