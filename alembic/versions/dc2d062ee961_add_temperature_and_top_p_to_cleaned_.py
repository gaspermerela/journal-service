"""add temperature and top_p to cleaned_entries

Revision ID: dc2d062ee961
Revises: 74592cf00921
Create Date: 2025-11-26 19:13:23.806380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = 'dc2d062ee961'
down_revision: Union[str, None] = '74592cf00921'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    op.add_column(
        'cleaned_entries',
        sa.Column('temperature', sa.Float(), nullable=True, comment='LLM sampling temperature (0-2)'),
        schema=schema
    )
    op.add_column(
        'cleaned_entries',
        sa.Column('top_p', sa.Float(), nullable=True, comment='LLM nucleus sampling (0-1)'),
        schema=schema
    )


def downgrade() -> None:
    schema = get_schema()
    op.drop_column('cleaned_entries', 'top_p', schema=schema)
    op.drop_column('cleaned_entries', 'temperature', schema=schema)
