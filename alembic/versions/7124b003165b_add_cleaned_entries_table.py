"""add_cleaned_entries_table

Revision ID: 7124b003165b
Revises: 7a458945ac76
Create Date: 2025-11-10 09:24:26.691114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '7124b003165b'
down_revision: Union[str, None] = '7a458945ac76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Create enum type for cleanup status (only if it doesn't exist)
    # op.execute("""
    #     DO $$ BEGIN
    #         CREATE TYPE cleanupstatus AS ENUM ('pending', 'processing', 'completed', 'failed');
    #     EXCEPTION
    #         WHEN duplicate_object THEN null;
    #     END $$;
    # """)

    # Create cleaned_entries table
    op.create_table(
        'cleaned_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('voice_entry_id', sa.UUID(), nullable=False),
        sa.Column('transcription_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('cleaned_text', sa.Text(), nullable=True),
        sa.Column('analysis', sa.JSON(), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='cleanupstatus', schema=schema), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['voice_entry_id'], [f'{schema}.voice_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transcription_id'], [f'{schema}.transcriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], [f'{schema}.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema=schema
    )

    # Create indexes
    op.create_index('ix_cleaned_entries_voice_entry_id', 'cleaned_entries', ['voice_entry_id'], schema=schema)
    op.create_index('ix_cleaned_entries_transcription_id', 'cleaned_entries', ['transcription_id'], schema=schema)
    op.create_index('ix_cleaned_entries_user_id', 'cleaned_entries', ['user_id'], schema=schema)
    op.create_index('ix_cleaned_entries_status', 'cleaned_entries', ['status'], schema=schema)


def downgrade() -> None:
    schema = get_schema()
    # Drop indexes
    op.drop_index('ix_cleaned_entries_status', table_name='cleaned_entries', schema=schema)
    op.drop_index('ix_cleaned_entries_user_id', table_name='cleaned_entries', schema=schema)
    op.drop_index('ix_cleaned_entries_transcription_id', table_name='cleaned_entries', schema=schema)
    op.drop_index('ix_cleaned_entries_voice_entry_id', table_name='cleaned_entries', schema=schema)

    # Drop table (foreign keys will be dropped automatically with CASCADE)
    op.drop_table('cleaned_entries', schema=schema)

    # Drop enum type
    op.execute(f'DROP TYPE "{schema}".cleanupstatus')
