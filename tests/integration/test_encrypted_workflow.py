"""
Integration tests for encrypted workflow.

Tests cover:
- Encrypted upload: file encryption when preference enabled
- Encryption preference behavior: toggle encryption on/off
- Service unavailability: 503 error when encryption enabled but service unavailable
- DEK creation: data encryption key created for encrypted entries
"""

import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.voice_entry import VoiceEntry
from app.models.data_encryption_key import DataEncryptionKey
from app.schemas.auth import UserCreate
from app.services.database import db_service


# =============================================================================
# Encrypted Upload Tests
# =============================================================================


class TestEncryptedUpload:
    """Tests for upload with encryption."""

    @pytest.mark.asyncio
    async def test_upload_encrypts_file_when_preference_enabled(
        self,
        authenticated_client_with_encryption: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user_with_encryption: User,
    ):
        """Upload creates encrypted file when user has encryption enabled."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client_with_encryption.post(
                "/api/v1/upload", files=files
            )

        assert response.status_code == 201
        data = response.json()
        entry_id = uuid.UUID(data["id"])

        # Verify entry is marked as encrypted in database
        # (response schema doesn't include is_encrypted field)
        entry = await db_session.get(VoiceEntry, entry_id)
        assert entry is not None
        assert entry.is_encrypted is True
        assert entry.file_path.endswith(".enc")
        assert entry.encryption_version == "local-v1"

    @pytest.mark.asyncio
    async def test_upload_does_not_encrypt_when_preference_disabled(
        self,
        authenticated_client: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Upload creates unencrypted file when user has encryption disabled."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client.post("/api/v1/upload", files=files)

        assert response.status_code == 201
        data = response.json()
        entry_id = uuid.UUID(data["id"])

        # Verify entry is NOT encrypted in database
        # (response schema doesn't include is_encrypted field)
        entry = await db_session.get(VoiceEntry, entry_id)
        assert entry is not None
        assert entry.is_encrypted is False
        assert not entry.file_path.endswith(".enc")
        assert entry.encryption_version is None

    @pytest.mark.asyncio
    async def test_dek_created_for_encrypted_entry(
        self,
        authenticated_client_with_encryption: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user_with_encryption: User,
    ):
        """DEK is created when encrypting a voice entry."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client_with_encryption.post(
                "/api/v1/upload", files=files
            )

        assert response.status_code == 201
        entry_id = uuid.UUID(response.json()["id"])

        # Verify DEK was created
        stmt = select(DataEncryptionKey).where(
            DataEncryptionKey.voice_entry_id == entry_id,
            DataEncryptionKey.user_id == test_user_with_encryption.id,
        )
        result = await db_session.execute(stmt)
        dek = result.scalar_one_or_none()

        assert dek is not None
        assert dek.voice_entry_id == entry_id
        assert dek.user_id == test_user_with_encryption.id
        assert dek.encrypted_dek is not None
        assert len(dek.encrypted_dek) > 0

    @pytest.mark.asyncio
    async def test_no_dek_created_for_unencrypted_entry(
        self,
        authenticated_client: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user: User,
    ):
        """No DEK is created for unencrypted voice entry."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client.post("/api/v1/upload", files=files)

        assert response.status_code == 201
        entry_id = uuid.UUID(response.json()["id"])

        # Verify no DEK was created
        stmt = select(DataEncryptionKey).where(
            DataEncryptionKey.voice_entry_id == entry_id
        )
        result = await db_session.execute(stmt)
        dek = result.scalar_one_or_none()

        assert dek is None


# =============================================================================
# Service Unavailability Tests
# =============================================================================


class TestEncryptionServiceUnavailability:
    """Tests for encryption service unavailability handling."""

    @pytest.mark.asyncio
    async def test_upload_returns_503_when_encryption_enabled_but_service_unavailable(
        self,
        db_session: AsyncSession,
        test_settings,
        mock_transcription_service,
        mock_llm_cleanup_service,
        sample_mp3_path: Path,
    ):
        """Upload returns 503 when user has encryption enabled but service is unavailable."""
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        from app.database import get_db

        # Create user with encryption enabled
        user_data = UserCreate(
            email="encryption_test_user@example.com",
            password="TestPassword123!",
        )
        user = await db_service.create_user(db_session, user_data)
        await db_session.commit()

        # Enable encryption for user
        user_prefs = await db_service.get_user_preferences(db_session, user.id)
        user_prefs.encryption_enabled = True
        await db_session.commit()

        # Override dependencies WITHOUT encryption service
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        from app import config

        config.settings = test_settings

        # Set services but NOT encryption service (None)
        app.state.transcription_service = mock_transcription_service
        app.state.llm_cleanup_service = mock_llm_cleanup_service
        app.state.encryption_service = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                # Login
                login_response = await ac.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "encryption_test_user@example.com",
                        "password": "TestPassword123!",
                    },
                )
                assert login_response.status_code == 200
                ac.headers["Authorization"] = (
                    f"Bearer {login_response.json()['access_token']}"
                )

                # Try to upload
                with open(sample_mp3_path, "rb") as f:
                    files = {"file": ("test.mp3", f, "audio/mpeg")}
                    response = await ac.post("/api/v1/upload", files=files)

                # Should get 503 Service Unavailable
                assert response.status_code == 503
                assert "unavailable" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()
            app.state.transcription_service = None
            app.state.llm_cleanup_service = None
            app.state.encryption_service = None


# =============================================================================
# Encryption Preference Tests
# =============================================================================


class TestEncryptionUserPreferences:
    """Tests for encryption preference behavior."""

    @pytest.mark.asyncio
    async def test_new_user_has_encryption_enabled_by_default(
        self, db_session: AsyncSession
    ):
        """New users have encryption enabled by default."""
        user_data = UserCreate(
            email="new_user_pref_test@example.com",
            password="NewUserPassword123!",
        )
        user = await db_service.create_user(db_session, user_data)
        await db_session.commit()

        # Get preferences (auto-created)
        user_prefs = await db_service.get_user_preferences(db_session, user.id)

        # Encryption should be enabled by default
        assert user_prefs.encryption_enabled is True

    @pytest.mark.asyncio
    async def test_user_can_disable_encryption(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """User can disable encryption via preferences API."""
        # First enable encryption
        response = await authenticated_client.put(
            "/api/v1/user/preferences", json={"encryption_enabled": True}
        )
        assert response.status_code == 200
        assert response.json()["encryption_enabled"] is True

        # Then disable it
        response = await authenticated_client.put(
            "/api/v1/user/preferences", json={"encryption_enabled": False}
        )
        assert response.status_code == 200
        assert response.json()["encryption_enabled"] is False

    @pytest.mark.asyncio
    async def test_user_can_enable_encryption(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """User can enable encryption via preferences API."""
        # test_user has encryption disabled by fixture
        response = await authenticated_client.put(
            "/api/v1/user/preferences", json={"encryption_enabled": True}
        )
        assert response.status_code == 200
        assert response.json()["encryption_enabled"] is True

    @pytest.mark.asyncio
    async def test_get_preferences_returns_encryption_status(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """GET preferences includes encryption_enabled field."""
        response = await authenticated_client.get("/api/v1/user/preferences")
        assert response.status_code == 200
        data = response.json()
        assert "encryption_enabled" in data
        # test_user has encryption disabled
        assert data["encryption_enabled"] is False


# =============================================================================
# Mixed Encrypted/Unencrypted Entries Tests
# =============================================================================


class TestMixedEncryptedEntries:
    """Tests for handling mixed encrypted and unencrypted entries."""

    @pytest.mark.asyncio
    async def test_list_entries_includes_both_encrypted_and_unencrypted(
        self,
        authenticated_client_with_encryption: AsyncClient,
        db_session: AsyncSession,
        test_user_with_encryption: User,
        test_storage_path: Path,
    ):
        """List entries returns both encrypted and unencrypted entries correctly."""
        # Create an unencrypted entry directly in DB
        unencrypted_entry = VoiceEntry(
            id=uuid.uuid4(),
            original_filename="unencrypted.mp3",
            saved_filename="unencrypted_saved.wav",
            file_path=str(test_storage_path / "unencrypted.wav"),
            user_id=test_user_with_encryption.id,
            is_encrypted=False,
        )
        # Create file
        (test_storage_path / "unencrypted.wav").write_bytes(b"fake audio data")
        db_session.add(unencrypted_entry)
        await db_session.commit()

        # Create an encrypted entry via upload
        from pathlib import Path
        import tempfile

        # Create a minimal valid MP3 file
        mp3_data = bytes(
            [
                0x49,
                0x44,
                0x33,
                0x03,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xFF,
                0xFB,
                0x90,
                0x00,
            ]
            + [0x00] * 100
        )

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".mp3", delete=False
        ) as temp_file:
            temp_file.write(mp3_data)
            temp_path = Path(temp_file.name)

        try:
            with open(temp_path, "rb") as f:
                files = {"file": ("encrypted.mp3", f, "audio/mpeg")}
                response = await authenticated_client_with_encryption.post(
                    "/api/v1/upload", files=files
                )
            assert response.status_code == 201
        finally:
            temp_path.unlink()

        # List all entries
        response = await authenticated_client_with_encryption.get("/api/v1/entries")
        assert response.status_code == 200
        data = response.json()

        # Should have at least 2 entries (1 unencrypted + 1 encrypted)
        assert data["total"] >= 2

        # Find our entries
        encrypted_count = 0
        unencrypted_count = 0
        for entry in data["entries"]:
            if entry.get("original_filename") == "encrypted.mp3":
                encrypted_count += 1
            if entry.get("original_filename") == "unencrypted.mp3":
                unencrypted_count += 1

        assert encrypted_count >= 1
        assert unencrypted_count >= 1
