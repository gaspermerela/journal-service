"""add_role_column_to_users

Revision ID: 72b20f635571
Revises: 9ef316529a2c
Create Date: 2025-11-21 23:03:46.732796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = '72b20f635571'
down_revision: Union[str, None] = '9ef316529a2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema = get_schema()
    # Create ENUM type for user roles (if it doesn't exist)
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '{schema}')) THEN
                CREATE TYPE "{schema}".userrole AS ENUM ('user', 'admin');
            END IF;
        END$$;
    """)

    # Add role column to users table with default 'user'
    op.add_column(
        'users',
        sa.Column('role', sa.Enum('user', 'admin', name='userrole', schema=schema),
                  nullable=False, server_default='user'),
        schema=schema
    )

    # Add index on role column for query performance
    op.create_index('idx_users_role', 'users', ['role'], schema=schema)


def downgrade() -> None:
    schema = get_schema()
    # Drop index
    op.drop_index('idx_users_role', table_name='users', schema=schema)

    # Drop role column
    op.drop_column('users', 'role', schema=schema)

    # Drop ENUM type
    role_enum = sa.Enum('user', 'admin', name='userrole', schema=schema)
    role_enum.drop(op.get_bind())
