"""Add transcriptions table

Revision ID: b1c2d3e4f5a6
Revises: aa773922106b
Create Date: 2025-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'aa773922106b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create transcriptions table
    op.create_table(
        'transcriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transcribed_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('model_used', sa.String(length=50), nullable=False),
        sa.Column('language_code', sa.String(length=10), nullable=False),
        sa.Column('transcription_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transcription_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['entry_id'], ['journal.voice_entries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='journal'
    )

    # Create indexes
    op.create_index(
        'idx_transcriptions_entry_id',
        'transcriptions',
        ['entry_id'],
        unique=False,
        schema='journal'
    )
    op.create_index(
        'idx_transcriptions_entry_id_is_primary',
        'transcriptions',
        ['entry_id', 'is_primary'],
        unique=False,
        schema='journal'
    )
    op.create_index(
        'idx_transcriptions_status',
        'transcriptions',
        ['status'],
        unique=False,
        schema='journal'
    )
    op.create_index(
        'idx_transcriptions_created_at',
        'transcriptions',
        ['created_at'],
        unique=False,
        schema='journal'
    )
    op.create_index(
        'idx_transcriptions_is_primary',
        'transcriptions',
        ['is_primary'],
        unique=False,
        schema='journal'
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_transcriptions_is_primary', table_name='transcriptions', schema='journal')
    op.drop_index('idx_transcriptions_created_at', table_name='transcriptions', schema='journal')
    op.drop_index('idx_transcriptions_status', table_name='transcriptions', schema='journal')
    op.drop_index('idx_transcriptions_entry_id_is_primary', table_name='transcriptions', schema='journal')
    op.drop_index('idx_transcriptions_entry_id', table_name='transcriptions', schema='journal')

    # Drop table
    op.drop_table('transcriptions', schema='journal')
