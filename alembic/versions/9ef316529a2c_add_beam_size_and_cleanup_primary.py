"""add_beam_size_and_cleanup_primary

Revision ID: 9ef316529a2c
Revises: a13729e1f2be
Create Date: 2025-11-21 19:53:45.222835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '9ef316529a2c'
down_revision: Union[str, None] = 'a13729e1f2be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Add beam_size to transcriptions table (nullable for backward compatibility)
    op.add_column(
        'transcriptions',
        sa.Column('beam_size', sa.Integer(), nullable=True),
        schema=schema
    )

    # Add is_primary to cleaned_entries table
    op.add_column(
        'cleaned_entries',
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        schema=schema
    )

    # Add index on cleaned_entries.is_primary for query performance
    op.create_index(
        'idx_cleaned_entries_is_primary',
        'cleaned_entries',
        ['is_primary'],
        schema=schema
    )


def downgrade() -> None:
    schema = get_schema()
    # Drop index first
    op.drop_index(
        'idx_cleaned_entries_is_primary',
        table_name='cleaned_entries',
        schema=schema
    )

    # Drop columns
    op.drop_column('cleaned_entries', 'is_primary', schema=schema)
    op.drop_column('transcriptions', 'beam_size', schema=schema)
