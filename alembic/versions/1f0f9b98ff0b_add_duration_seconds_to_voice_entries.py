"""add duration_seconds to voice_entries

Revision ID: 1f0f9b98ff0b
Revises: 62d3b548dba1
Create Date: 2025-11-15 11:14:27.391848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f0f9b98ff0b'
down_revision: Union[str, None] = '62d3b548dba1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add duration_seconds column with default value 0.0
    op.add_column(
        'voice_entries',
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        schema='journal'
    )


def downgrade() -> None:
    # Remove duration_seconds column
    op.drop_column('voice_entries', 'duration_seconds', schema='journal')
