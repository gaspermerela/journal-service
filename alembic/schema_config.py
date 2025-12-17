"""
Schema configuration helper for Alembic migrations.

This module provides a way for migrations to get the target schema name
dynamically, enabling per-branch database isolation.

Usage in migrations:
    from schema_config import get_schema

    def upgrade():
        schema = get_schema()
        op.create_table('my_table', ..., schema=schema)
"""
from app.config import settings


def get_schema() -> str:
    """
    Get the database schema name for migrations.

    Reads from DB_SCHEMA setting (loaded from .env), defaults to 'journal'.
    This allows different git branches/worktrees to use isolated schemas.

    Returns:
        str: The schema name to use for migrations
    """
    return settings.DB_SCHEMA
