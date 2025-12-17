"""add_notion_integration

Revision ID: 62d3b548dba1
Revises: 240e345c9e39
Create Date: 2025-11-12 16:14:01.301841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from schema_config import get_schema

# revision identifiers, used by Alembic.
revision: str = '62d3b548dba1'
down_revision: Union[str, None] = '240e345c9e39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Create SyncStatus enum type
    op.execute(f'CREATE TYPE "{schema}".syncstatus AS ENUM (\'pending\', \'processing\', \'completed\', \'failed\', \'retrying\')')

    # Add Notion fields to users table
    op.add_column('users',
        sa.Column('notion_api_key_encrypted', sa.String(500), nullable=True),
        schema=schema
    )
    op.add_column('users',
        sa.Column('notion_database_id', sa.String(100), nullable=True),
        schema=schema
    )
    op.add_column('users',
        sa.Column('notion_enabled', sa.Boolean(), nullable=False, server_default='false'),
        schema=schema
    )
    op.add_column('users',
        sa.Column('notion_auto_sync', sa.Boolean(), nullable=False, server_default='true'),
        schema=schema
    )

    # Create notion_syncs table
    op.create_table(
        'notion_syncs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cleaned_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notion_page_id', sa.String(100), nullable=True),
        sa.Column('notion_database_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('sync_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_synced_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], [f'{schema}.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entry_id'], [f'{schema}.voice_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cleaned_entry_id'], [f'{schema}.cleaned_entries.id'], ondelete='SET NULL'),
        schema=schema
    )

    # Create indexes
    op.create_index('idx_notion_syncs_user_id', 'notion_syncs', ['user_id'], schema=schema)
    op.create_index('idx_notion_syncs_entry_id', 'notion_syncs', ['entry_id'], schema=schema)
    op.create_index('idx_notion_syncs_status', 'notion_syncs', ['status'], schema=schema)
    op.create_index('idx_notion_syncs_notion_page_id', 'notion_syncs', ['notion_page_id'], schema=schema)


def downgrade() -> None:
    schema = get_schema()
    # Drop indexes
    op.drop_index('idx_notion_syncs_notion_page_id', table_name='notion_syncs', schema=schema)
    op.drop_index('idx_notion_syncs_status', table_name='notion_syncs', schema=schema)
    op.drop_index('idx_notion_syncs_entry_id', table_name='notion_syncs', schema=schema)
    op.drop_index('idx_notion_syncs_user_id', table_name='notion_syncs', schema=schema)

    # Drop notion_syncs table
    op.drop_table('notion_syncs', schema=schema)

    # Drop columns from users table
    op.drop_column('users', 'notion_auto_sync', schema=schema)
    op.drop_column('users', 'notion_enabled', schema=schema)
    op.drop_column('users', 'notion_database_id', schema=schema)
    op.drop_column('users', 'notion_api_key_encrypted', schema=schema)

    # Drop enum type
    op.execute(f'DROP TYPE "{schema}".syncstatus')
