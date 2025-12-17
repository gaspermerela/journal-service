"""change_primary_cleanup_to_voice_entry_scope

Revision ID: 0a7bf1e29a1a
Revises: 72b20f635571
Create Date: 2025-11-22 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '0a7bf1e29a1a'
down_revision: Union[str, None] = '72b20f635571'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Change default value of is_primary to false
    op.alter_column(
        'cleaned_entries',
        'is_primary',
        server_default='false',
        schema=schema
    )

    # Add partial unique index to ensure only one primary cleanup per voice_entry
    op.execute(f"""
        CREATE UNIQUE INDEX idx_one_primary_cleanup_per_voice_entry
        ON "{schema}".cleaned_entries (voice_entry_id)
        WHERE is_primary = true
    """)


def downgrade() -> None:
    schema = get_schema()
    # Remove the partial unique index
    op.execute(f'DROP INDEX IF EXISTS "{schema}".idx_one_primary_cleanup_per_voice_entry')

    # Restore original default value
    op.alter_column(
        'cleaned_entries',
        'is_primary',
        server_default='true',
        schema=schema
    )
