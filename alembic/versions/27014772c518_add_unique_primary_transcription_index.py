"""add_unique_primary_transcription_index

Revision ID: 27014772c518
Revises: 9ce891778652
Create Date: 2025-12-06 20:14:01.960809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27014772c518'
down_revision: Union[str, None] = '9ce891778652'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add partial unique index to ensure only one primary transcription per entry."""
    op.create_index(
        'ix_transcriptions_unique_primary',
        'transcriptions',
        ['entry_id'],
        unique=True,
        schema='journal',
        postgresql_where=sa.text('is_primary = true')
    )


def downgrade() -> None:
    """Remove the partial unique index."""
    op.drop_index(
        'ix_transcriptions_unique_primary',
        table_name='transcriptions',
        schema='journal'
    )
