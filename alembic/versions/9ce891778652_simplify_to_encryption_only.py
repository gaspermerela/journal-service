"""simplify_to_encryption_only

Revision ID: 9ce891778652
Revises: e1f2a3b4c5d6
Create Date: 2025-12-06 16:43:03.503086

Simplifies the database schema to encryption-only mode:
- Drops plaintext columns (data is always encrypted now)
- Renames encrypted columns to standard names
- Removes encryption toggle from user preferences
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '9ce891778652'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    SCHEMA = get_schema()
    # ==========================================================================
    # TRANSCRIPTIONS TABLE
    # ==========================================================================
    # Drop plaintext column (no longer used)
    op.drop_column("transcriptions", "transcribed_text", schema=SCHEMA)

    # Drop is_encrypted flag (always encrypted now)
    op.drop_column("transcriptions", "is_encrypted", schema=SCHEMA)

    # Rename encrypted column to standard name
    op.alter_column(
        "transcriptions",
        "transcribed_text_encrypted",
        new_column_name="transcribed_text",
        schema=SCHEMA,
    )

    # ==========================================================================
    # CLEANED_ENTRIES TABLE
    # ==========================================================================
    # Drop plaintext columns (no longer used)
    op.drop_column("cleaned_entries", "cleaned_text", schema=SCHEMA)
    op.drop_column("cleaned_entries", "analysis", schema=SCHEMA)

    # Drop is_encrypted flag (always encrypted now)
    op.drop_column("cleaned_entries", "is_encrypted", schema=SCHEMA)

    # Rename encrypted columns to standard names
    op.alter_column(
        "cleaned_entries",
        "cleaned_text_encrypted",
        new_column_name="cleaned_text",
        schema=SCHEMA,
    )
    op.alter_column(
        "cleaned_entries",
        "analysis_encrypted",
        new_column_name="analysis",
        schema=SCHEMA,
    )

    # ==========================================================================
    # USER_PREFERENCES TABLE
    # ==========================================================================
    # Drop encryption toggle (encryption is always on now)
    op.drop_column("user_preferences", "encryption_enabled", schema=SCHEMA)


def downgrade() -> None:
    SCHEMA = get_schema()
    # ==========================================================================
    # USER_PREFERENCES TABLE
    # ==========================================================================
    op.add_column(
        "user_preferences",
        sa.Column(
            "encryption_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        schema=SCHEMA,
    )

    # ==========================================================================
    # CLEANED_ENTRIES TABLE
    # ==========================================================================
    # Rename back to encrypted column names
    op.alter_column(
        "cleaned_entries",
        "analysis",
        new_column_name="analysis_encrypted",
        schema=SCHEMA,
    )
    op.alter_column(
        "cleaned_entries",
        "cleaned_text",
        new_column_name="cleaned_text_encrypted",
        schema=SCHEMA,
    )

    # Re-add is_encrypted flag
    op.add_column(
        "cleaned_entries",
        sa.Column(
            "is_encrypted",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        schema=SCHEMA,
    )

    # Re-add plaintext columns
    op.add_column(
        "cleaned_entries",
        sa.Column("analysis", sa.JSON(), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "cleaned_entries",
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        schema=SCHEMA,
    )

    # ==========================================================================
    # TRANSCRIPTIONS TABLE
    # ==========================================================================
    # Rename back to encrypted column name
    op.alter_column(
        "transcriptions",
        "transcribed_text",
        new_column_name="transcribed_text_encrypted",
        schema=SCHEMA,
    )

    # Re-add is_encrypted flag
    op.add_column(
        "transcriptions",
        sa.Column(
            "is_encrypted",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        schema=SCHEMA,
    )

    # Re-add plaintext column
    op.add_column(
        "transcriptions",
        sa.Column("transcribed_text", sa.Text(), nullable=True),
        schema=SCHEMA,
    )
