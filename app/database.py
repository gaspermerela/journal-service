"""
Database connection and session management.
Provides async database engine and session factory.
"""
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("database")

# Create async engine
# Note: echo parameter is intentionally set to False
# Use SQLALCHEMY_LOG_LEVEL environment variable to control SQL logging
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=False,  # Control via SQLALCHEMY_LOG_LEVEL instead
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


def get_session():
    """
    Context manager for getting async database sessions in background tasks.

    Returns:
        AsyncSession context manager

    Example:
        async with get_session() as db:
            # Use db session
            ...
    """
    return AsyncSessionLocal()


async def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return False
