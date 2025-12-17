"""add_user_id_to_voice_entries

Revision ID: 7a458945ac76
Revises: c6459d14db37
Create Date: 2025-11-09 18:58:38.157990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '7a458945ac76'
down_revision: Union[str, None] = 'c6459d14db37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Add user_id column to voice_entries table
    op.add_column(
        'voice_entries',
        sa.Column('user_id', sa.UUID(), nullable=True),
        schema=schema
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_voice_entries_user_id_users',
        'voice_entries', 'users',
        ['user_id'], ['id'],
        source_schema=schema,
        referent_schema=schema,
        ondelete='CASCADE'
    )

    # Add index for user_id
    op.create_index(
        'idx_voice_entries_user_id',
        'voice_entries',
        ['user_id'],
        unique=False,
        schema=schema
    )


def downgrade() -> None:
    schema = get_schema()
    # Drop index
    op.drop_index('idx_voice_entries_user_id', table_name='voice_entries', schema=schema)

    # Drop foreign key
    op.drop_constraint('fk_voice_entries_user_id_users', 'voice_entries', schema=schema, type_='foreignkey')

    # Drop column
    op.drop_column('voice_entries', 'user_id', schema=schema)
