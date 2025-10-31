"""
Pytest configuration and fixtures for journal service tests.
"""
import asyncio
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.config import Settings
from app.database import Base, get_db
from app.main import app
from app.models.dream_entry import DreamEntry


# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://journal_user:password@localhost:5432/postgres"
TEST_SCHEMA = "journal_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.
    Required for pytest-asyncio to work properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """
    Create a test database engine.
    Uses a separate test schema to avoid conflicts with dev data.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    # Create test schema
    async with engine.connect() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        await conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
        await conn.commit()

    # Create tables in test schema
    async with engine.begin() as conn:
        # Set search path to test schema
        await conn.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: drop test schema
    async with engine.connect() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        await conn.commit()

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Automatically rolls back changes after each test.
    """
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        # Set search path for this session
        await session.execute(text(f"SET search_path TO {TEST_SCHEMA}"))

        yield session

        # Rollback any changes
        await session.rollback()

        # Clean up all data after test
        await session.execute(text(f"TRUNCATE TABLE {TEST_SCHEMA}.dream_entries CASCADE"))
        await session.commit()


@pytest.fixture
def test_storage_path(tmp_path) -> Generator[Path, None, None]:
    """
    Create a temporary directory for test file storage.
    Automatically cleaned up after each test.
    """
    storage_path = tmp_path / "test_audio"
    storage_path.mkdir(parents=True, exist_ok=True)
    yield storage_path
    # Cleanup is automatic with tmp_path


@pytest.fixture
def test_settings(test_storage_path) -> Settings:
    """
    Create test settings with overridden storage path.
    """
    settings = Settings()
    settings.AUDIO_STORAGE_PATH = str(test_storage_path)
    return settings


@pytest.fixture
async def client(db_session: AsyncSession, test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for the FastAPI application.
    Overrides the database dependency to use test database.
    """
    # Override dependencies
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Override settings
    from app import config
    config.settings = test_settings

    # Create client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_mp3_path() -> Generator[Path, None, None]:
    """
    Create a minimal valid MP3 file for testing.
    Returns the path to the test file.
    """
    # Create a minimal valid MP3 file (ID3v2 header + minimal MP3 frame)
    # This is a valid but silent MP3 file
    mp3_data = bytes([
        # ID3v2 header
        0x49, 0x44, 0x33,  # "ID3"
        0x03, 0x00,        # Version 2.3.0
        0x00,              # Flags
        0x00, 0x00, 0x00, 0x00,  # Size (0)
        # MP3 frame header (MPEG-1 Layer III, 128kbps, 44.1kHz)
        0xFF, 0xFB, 0x90, 0x00,
        # Some padding to make it look more realistic
    ] + [0x00] * 100)

    # Write to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=False)
    temp_file.write(mp3_data)
    temp_file.close()

    yield Path(temp_file.name)

    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def large_mp3_path(test_settings: Settings) -> Generator[Path, None, None]:
    """
    Create an MP3 file that exceeds the maximum file size.
    Used for testing file size validation.
    """
    # Create a file larger than MAX_FILE_SIZE_MB
    size_mb = test_settings.MAX_FILE_SIZE_MB + 1
    size_bytes = size_mb * 1024 * 1024

    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=False)

    # Write MP3 header
    mp3_header = bytes([0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    temp_file.write(mp3_header)

    # Write zeros to fill the file
    remaining = size_bytes - len(mp3_header)
    chunk_size = 1024 * 1024  # 1MB chunks
    while remaining > 0:
        write_size = min(chunk_size, remaining)
        temp_file.write(b'\x00' * write_size)
        remaining -= write_size

    temp_file.close()

    yield Path(temp_file.name)

    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def invalid_file_path() -> Generator[Path, None, None]:
    """
    Create an invalid (non-MP3) file for testing validation.
    """
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write("This is not an MP3 file")
    temp_file.close()

    yield Path(temp_file.name)

    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
async def sample_dream_entry(db_session: AsyncSession, test_storage_path: Path) -> DreamEntry:
    """
    Create a sample dream entry in the test database.
    Used for testing retrieval and other operations.
    """
    entry_id = uuid.uuid4()
    saved_filename = f"{entry_id}_20250131T120000.mp3"
    file_path = test_storage_path / "2025-01-31" / saved_filename

    # Create the directory and file
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"fake mp3 data")

    # Create database entry
    entry = DreamEntry(
        id=entry_id,
        original_filename="test_dream.mp3",
        saved_filename=saved_filename,
        file_path=str(file_path),
    )

    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    return entry
