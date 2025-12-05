"""add envelope encryption

Adds support for GDPR-compliant envelope encryption:
- data_encryption_keys table for storing encrypted DEKs (one per VoiceEntry)
- is_encrypted and encryption_version columns on existing tables
- encryption_enabled preference for users

Revision ID: e1f2a3b4c5d6
Revises: dc2d062ee961
Create Date: 2025-12-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = '25dda16871b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create data_encryption_keys table (one DEK per VoiceEntry)
    op.create_table(
        'data_encryption_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('voice_entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encrypted_dek', postgresql.BYTEA(), nullable=False),
        sa.Column('encryption_version', sa.String(50), nullable=False),
        sa.Column('key_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['journal.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voice_entry_id'], ['journal.voice_entries.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('voice_entry_id', name='uq_dek_voice_entry'),
        schema='journal'
    )

    # Create indexes for data_encryption_keys
    op.create_index(
        'idx_dek_user_id',
        'data_encryption_keys',
        ['user_id'],
        schema='journal'
    )

    op.create_index(
        'idx_dek_active',
        'data_encryption_keys',
        ['voice_entry_id'],
        schema='journal',
        postgresql_where=sa.text('deleted_at IS NULL')
    )

    # Add encryption columns to voice_entries
    op.add_column(
        'voice_entries',
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='false'),
        schema='journal'
    )
    op.add_column(
        'voice_entries',
        sa.Column('encryption_version', sa.String(50), nullable=True),
        schema='journal'
    )

    # Add encryption columns to transcriptions
    op.add_column(
        'transcriptions',
        sa.Column('transcribed_text_encrypted', postgresql.BYTEA(), nullable=True),
        schema='journal'
    )
    op.add_column(
        'transcriptions',
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='false'),
        schema='journal'
    )

    # Add encryption columns to cleaned_entries
    op.add_column(
        'cleaned_entries',
        sa.Column('cleaned_text_encrypted', postgresql.BYTEA(), nullable=True),
        schema='journal'
    )
    op.add_column(
        'cleaned_entries',
        sa.Column('analysis_encrypted', postgresql.BYTEA(), nullable=True),
        schema='journal'
    )
    op.add_column(
        'cleaned_entries',
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='false'),
        schema='journal'
    )

    # Add encryption preference to user_preferences (enabled by default, opt-out)
    op.add_column(
        'user_preferences',
        sa.Column('encryption_enabled', sa.Boolean(), nullable=False, server_default='true'),
        schema='journal'
    )


def downgrade() -> None:
    # Remove encryption preference from user_preferences
    op.drop_column('user_preferences', 'encryption_enabled', schema='journal')

    # Remove encryption columns from cleaned_entries
    op.drop_column('cleaned_entries', 'is_encrypted', schema='journal')
    op.drop_column('cleaned_entries', 'analysis_encrypted', schema='journal')
    op.drop_column('cleaned_entries', 'cleaned_text_encrypted', schema='journal')

    # Remove encryption columns from transcriptions
    op.drop_column('transcriptions', 'is_encrypted', schema='journal')
    op.drop_column('transcriptions', 'transcribed_text_encrypted', schema='journal')

    # Remove encryption columns from voice_entries
    op.drop_column('voice_entries', 'encryption_version', schema='journal')
    op.drop_column('voice_entries', 'is_encrypted', schema='journal')

    # Drop indexes
    op.drop_index('idx_dek_active', table_name='data_encryption_keys', schema='journal')
    op.drop_index('idx_dek_user_id', table_name='data_encryption_keys', schema='journal')

    # Drop data_encryption_keys table (unique constraint dropped with table)
    op.drop_table('data_encryption_keys', schema='journal')
