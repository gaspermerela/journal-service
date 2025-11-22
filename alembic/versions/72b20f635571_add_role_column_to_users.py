"""add_role_column_to_users

Revision ID: 72b20f635571
Revises: 9ef316529a2c
Create Date: 2025-11-21 23:03:46.732796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72b20f635571'
down_revision: Union[str, None] = '9ef316529a2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM type for user roles (if it doesn't exist)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'journal')) THEN
                CREATE TYPE journal.userrole AS ENUM ('user', 'admin');
            END IF;
        END$$;
    """)

    # Add role column to users table with default 'user'
    op.add_column(
        'users',
        sa.Column('role', sa.Enum('user', 'admin', name='userrole', schema='journal'),
                  nullable=False, server_default='user'),
        schema='journal'
    )

    # Add index on role column for query performance
    op.create_index('idx_users_role', 'users', ['role'], schema='journal')


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_users_role', table_name='users', schema='journal')

    # Drop role column
    op.drop_column('users', 'role', schema='journal')

    # Drop ENUM type
    role_enum = sa.Enum('user', 'admin', name='userrole', schema='journal')
    role_enum.drop(op.get_bind())
