"""add temperature to transcriptions

Revision ID: 74592cf00921
Revises: 0a7bf1e29a1a
Create Date: 2025-11-26 19:12:45.507051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '74592cf00921'
down_revision: Union[str, None] = '0a7bf1e29a1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    op.add_column(
        'transcriptions',
        sa.Column('temperature', sa.Float(), nullable=True, comment='Sampling temperature (0-2)'),
        schema=schema
    )


def downgrade() -> None:
    schema = get_schema()
    op.drop_column('transcriptions', 'temperature', schema=schema)
