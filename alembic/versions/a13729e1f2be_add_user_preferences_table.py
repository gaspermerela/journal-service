"""add_user_preferences_table

Revision ID: a13729e1f2be
Revises: 7e994c032373
Create Date: 2025-11-21 00:57:23.582221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a13729e1f2be'
down_revision: Union[str, None] = '7e994c032373'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('preferred_transcription_language', sa.String(length=10), server_default='auto', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['journal.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='journal'
    )
    # Create unique index on user_id (one preference record per user)
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'], unique=True, schema='journal')


def downgrade() -> None:
    # Drop user_preferences table
    op.drop_index('idx_user_preferences_user_id', table_name='user_preferences', schema='journal')
    op.drop_table('user_preferences', schema='journal')
