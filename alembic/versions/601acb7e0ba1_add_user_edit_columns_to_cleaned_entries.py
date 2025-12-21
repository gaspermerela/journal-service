"""add_user_edit_columns_to_cleaned_entries

Revision ID: 601acb7e0ba1
Revises: 931462e66fb0
Create Date: 2025-12-20 21:22:26.610812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '601acb7e0ba1'
down_revision: Union[str, None] = '931462e66fb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    op.add_column(
        'cleaned_entries',
        sa.Column('user_edited_text', sa.LargeBinary(), nullable=True),
        schema=schema
    )
    op.add_column(
        'cleaned_entries',
        sa.Column('user_edited_at', sa.DateTime(timezone=True), nullable=True, comment='When user last edited'),
        schema=schema
    )


def downgrade() -> None:
    schema = get_schema()
    op.drop_column('cleaned_entries', 'user_edited_at', schema=schema)
    op.drop_column('cleaned_entries', 'user_edited_text', schema=schema)
