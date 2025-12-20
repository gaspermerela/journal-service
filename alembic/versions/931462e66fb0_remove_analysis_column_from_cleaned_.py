"""remove_analysis_column_from_cleaned_entries

Revision ID: 931462e66fb0
Revises: 27014772c518
Create Date: 2025-12-20 17:55:23.307514

Removes the analysis column from cleaned_entries table as part of
backbone separation refactoring. Analysis is now handled by wrapper
applications, not the core backbone service.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '931462e66fb0'
down_revision: Union[str, None] = '27014772c518'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Drop the analysis column (LargeBinary storing encrypted analysis JSON)
    op.drop_column('cleaned_entries', 'analysis', schema=schema)


def downgrade() -> None:
    schema = get_schema()
    # Re-add analysis column (LargeBinary for encrypted data)
    op.add_column(
        'cleaned_entries',
        sa.Column('analysis', postgresql.BYTEA(), nullable=True),
        schema=schema
    )
