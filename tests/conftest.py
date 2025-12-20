"""
Pytest configuration and fixtures for journal service tests.
"""
import os
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Generator, Tuple
from unittest.mock import Mock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Set required environment variables before importing Settings to avoid validation error
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-not-for-production")
os.environ.setdefault("DATABASE_PASSWORD", "password")  # Matches TEST_DATABASE_URL
os.environ.setdefault("TRANSCRIPTION_PROVIDER", "groq")  # Use Groq for E2E tests
os.environ.setdefault("LLM_PROVIDER", "groq")  # Use Groq for E2E tests
os.environ["DB_SCHEMA"] = "journal_test"  # MUST be set before app imports to use test schema

from app.config import Settings
from app.database import Base, get_db
from app.main import app
from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.user import User
from app.models.cleaned_entry import CleanedEntry  # noqa: F401
from app.models.notion_sync import NotionSync  # noqa: F401
from app.models.data_encryption_key import DataEncryptionKey  # noqa: F401
from app.models.user_preference import UserPreference  # noqa: F401
from app.models.prompt_template import PromptTemplate  # noqa: F401
from app.schemas.auth import UserCreate
from app.services.database import db_service


# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://journal_user:password@localhost:5432/postgres"
TEST_SCHEMA = "journal_test"

# E2E test timeout configuration (in seconds)
# Override via environment variables: E2E_TRANSCRIPTION_TIMEOUT, E2E_CLEANUP_TIMEOUT, E2E_NOTION_SYNC_TIMEOUT
E2E_TRANSCRIPTION_TIMEOUT = int(os.getenv("E2E_TRANSCRIPTION_TIMEOUT", "180"))  # 3 minutes
E2E_CLEANUP_TIMEOUT = int(os.getenv("E2E_CLEANUP_TIMEOUT", "180"))  # 3 minutes
E2E_NOTION_SYNC_TIMEOUT = int(os.getenv("E2E_NOTION_SYNC_TIMEOUT", "60"))  # 1 minute


@pytest.fixture(scope="module")
def test_db_schema():
    """Set up test database schema once per module."""
    import asyncio

    async def setup():
        engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
            await conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
            await conn.commit()
        async with engine.begin() as conn:
            await conn.execute(text(f"SET search_path TO {TEST_SCHEMA}"))

            # Create enum types manually before creating tables
            await conn.execute(text(
                f"CREATE TYPE {TEST_SCHEMA}.cleanupstatus AS ENUM ('pending', 'processing', 'completed', 'failed')"
            ))
            await conn.execute(text(
                f"CREATE TYPE {TEST_SCHEMA}.syncstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'retrying')"
            ))
            await conn.execute(text(
                f"CREATE TYPE {TEST_SCHEMA}.userrole AS ENUM ('user', 'admin')"
            ))

            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    async def teardown():
        engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
            await conn.commit()
        await engine.dispose()

    asyncio.run(setup())
    yield
    asyncio.run(teardown())


@pytest.fixture
async def db_session(test_db_schema) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Automatically rolls back changes after each test.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args={"server_settings": {"search_path": TEST_SCHEMA}}
    )

    async with engine.connect() as connection:
        trans = await connection.begin()
        Session = async_sessionmaker(bind=connection, expire_on_commit=False)
        session = Session()

        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
            await connection.close()

    await engine.dispose()


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
    JWT configuration is set at module level in conftest.
    """
    settings = Settings()
    settings.AUDIO_STORAGE_PATH = str(test_storage_path)
    return settings


@pytest.fixture
async def client(db_session: AsyncSession, test_settings: Settings, encryption_service) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for the FastAPI application.
    Overrides the database dependency to use test database.
    Includes encryption service (required for encryption-only mode).

    Note: AI services (transcription, LLM cleanup) are created per-request
    via the provider registry. Tests should use 'noop' provider to avoid
    calling real API services.
    """
    # Override dependencies
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Override settings
    from app import config
    config.settings = test_settings

    # Encryption service is required (encryption-only mode)
    app.state.encryption_service = encryption_service

    # Create client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()
    app.state.encryption_service = None


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create a test user for authentication testing.
    Email: testuser@example.com
    Password: TestPassword123!

    Note: Encryption is disabled by default for tests since the encryption
    service is not available in the test environment. Use separate fixtures
    for testing encrypted workflows.
    """
    user_data = UserCreate(
        email="testuser@example.com",
        password="TestPassword123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user: User
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an authenticated test client with a valid access token.
    The client automatically includes the Authorization header.
    """
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    access_token = tokens["access_token"]

    # Add authorization header to client
    client.headers["Authorization"] = f"Bearer {access_token}"

    yield client

    # Clean up authorization header
    client.headers.pop("Authorization", None)


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
def real_audio_mp3_path() -> Path:
    """
    Return path to a real audio MP3 file for end-to-end transcription testing.
    This file contains actual speech content for testing real transcription.
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    mp3_path = fixtures_dir / "crocodile.mp3"

    if not mp3_path.exists():
        pytest.skip(f"Real audio fixture not found: {mp3_path}")

    return mp3_path


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
async def sample_voice_entry(db_session: AsyncSession, test_storage_path: Path, test_user: User) -> VoiceEntry:
    """
    Create a sample voice entry in the test database.
    Used for testing retrieval and other operations.
    Associated with the test_user fixture.
    """
    entry_id = uuid.uuid4()
    saved_filename = f"{entry_id}_20250131T120000.mp3"
    file_path = test_storage_path / "2025-01-31" / saved_filename

    # Create the directory and file
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"fake mp3 data")

    # Create database entry
    entry = VoiceEntry(
        id=entry_id,
        original_filename="test_dream.mp3",
        saved_filename=saved_filename,
        file_path=str(file_path),
        duration_seconds=60.0,  # Default test duration
        user_id=test_user.id,  # Associate with test user
    )

    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    return entry


# ===== Transcription Test Fixtures =====

@pytest.fixture
def mock_transcription_service():
    """
    NoOp transcription service for integration tests.
    Avoids loading Whisper model while testing API endpoints.
    """
    from app.services.transcription_noop import NoOpTranscriptionService
    return NoOpTranscriptionService(model_name="noop-whisper-test")


@pytest.fixture
def mock_llm_cleanup_service():
    """
    NoOp LLM cleanup service for integration tests.
    Avoids loading Ollama/Groq while testing API endpoints.
    """
    from app.services.llm_cleanup_noop import NoOpLLMCleanupService
    return NoOpLLMCleanupService(model_name="noop-llm-test")


@pytest.fixture
async def sample_transcription(
    db_session: AsyncSession,
    sample_voice_entry: VoiceEntry,
    encryption_service
) -> Transcription:
    """
    Create a sample completed transcription for testing.
    Linked to the sample_voice_entry fixture.
    Data is properly encrypted using the encryption service.
    """
    from datetime import datetime, timezone

    # Encrypt the transcribed text properly
    plaintext = "I had a dream about flying over mountains and vast oceans."
    encrypted_text = await encryption_service.encrypt_data(
        db_session,
        plaintext,
        sample_voice_entry.id,
        sample_voice_entry.user_id
    )

    transcription = Transcription(
        id=uuid.uuid4(),
        entry_id=sample_voice_entry.id,
        transcribed_text=encrypted_text,
        status="completed",
        model_used="whisper-base",
        language_code="en",
        transcription_started_at=datetime.now(timezone.utc),
        transcription_completed_at=datetime.now(timezone.utc),
        is_primary=True
    )

    db_session.add(transcription)
    await db_session.commit()
    await db_session.refresh(transcription)

    return transcription


@pytest.fixture
async def sample_pending_transcription(
    db_session: AsyncSession,
    sample_voice_entry: VoiceEntry
) -> Transcription:
    """
    Create a sample pending transcription for testing status updates.
    """
    transcription = Transcription(
        id=uuid.uuid4(),
        entry_id=sample_voice_entry.id,
        transcribed_text=None,
        status="pending",
        model_used="whisper-base",
        language_code="en",
        is_primary=False
    )

    db_session.add(transcription)
    await db_session.commit()
    await db_session.refresh(transcription)

    return transcription

@pytest.fixture
async def real_api_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create a real HTTP client for e2e tests that connects to the running Docker app.

    This makes actual HTTP requests to http://localhost:8000 instead of using ASGI transport.
    Use this fixture for true end-to-end tests that need real services (Whisper, Ollama, etc.)

    Prerequisites:
    - Docker container must be running
    - App must be accessible at http://localhost:8000
    """
    async with AsyncClient(
        base_url="http://localhost:8000",
        timeout=120.0  # Longer timeout for e2e operations
    ) as client:
        yield client


@pytest.fixture
async def authenticated_e2e_client(real_api_client: AsyncClient) -> Tuple[AsyncClient, str]:
    """
    Create a new user, authenticate, and return the real HTTP client with auth token.

    Uses real_api_client which makes actual HTTP requests to the Docker container.
    This is a shared fixture for all e2e tests.

    Returns:
        Tuple of (authenticated client, user email)
    """
    import os

    # Generate unique email for this test
    email = f"e2e_user_{os.urandom(4).hex()}@example.com"
    password = "E2EPassword123!"

    # Register
    register_response = await real_api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password}
    )
    assert register_response.status_code == 201

    # Login
    login_response = await real_api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert login_response.status_code == 200

    # Set authorization header
    access_token = login_response.json()["access_token"]
    real_api_client.headers["Authorization"] = f"Bearer {access_token}"

    return real_api_client, email


# E2E Service Availability Checks

def app_is_available() -> bool:
    """Check if the app is reachable at http://localhost:8000."""
    try:
        import httpx
        response = httpx.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def ollama_available() -> bool:
    """Check if Ollama service is available at http://localhost:11434."""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


# ===== Encryption Test Fixtures =====


@pytest.fixture
def encryption_service():
    """
    Create encryption service for testing.

    Uses LocalKEKProvider with a test master key.
    This fixture provides a real encryption service for testing
    encrypted workflows.
    """
    from app.services.encryption_providers.local_kek import LocalKEKProvider
    from app.services.envelope_encryption import EnvelopeEncryptionService

    provider = LocalKEKProvider(master_key="test-master-key-for-testing-12345678")
    return EnvelopeEncryptionService(provider)


