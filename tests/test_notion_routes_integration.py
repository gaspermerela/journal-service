"""
Integration tests for Notion routes.

Tests all Notion API endpoints with real database interactions.
Mocks external Notion API calls to avoid external dependencies.
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, Mock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.cleaned_entry import CleanedEntry
from app.models.user import User
from app.models.notion_sync import NotionSync, SyncStatus


@pytest.fixture
def mock_notion_service():
    """Mock NotionService for integration tests."""
    with patch("app.routes.notion.NotionService") as mock_service_class:
        mock_service = AsyncMock()

        # Mock validate_database
        mock_service.validate_database.return_value = {
            "id": "test_db_id",
            "title": [{"plain_text": "Dream Journal"}],
            "properties": {
                "Name": {"type": "title"},
                "Date": {"type": "date"},
                "Wake Time": {"type": "rich_text"}
            }
        }

        # Mock create_dream_page
        mock_service.create_dream_page.return_value = {
            "id": "notion_page_123",
            "url": "https://notion.so/page_123",
            "created_time": "2025-01-15T10:30:00.000Z"
        }

        # Mock update_dream_page
        mock_service.update_dream_page.return_value = {
            "id": "notion_page_123",
            "url": "https://notion.so/page_123",
            "last_edited_time": "2025-01-15T11:00:00.000Z"
        }

        # Mock close
        mock_service.close = AsyncMock()

        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
async def user_with_notion_configured(
    db_session: AsyncSession,
    test_user: User
) -> User:
    """Create a test user with Notion integration configured."""
    from app.services.encryption import encrypt_notion_key

    test_user.notion_enabled = True
    test_user.notion_api_key_encrypted = encrypt_notion_key("secret_test_key", test_user.id)
    test_user.notion_database_id = "test_db_id_123"
    test_user.notion_auto_sync = True

    await db_session.commit()
    await db_session.refresh(test_user)

    return test_user


@pytest.fixture
async def completed_cleaned_entry(
    db_session: AsyncSession,
    sample_voice_entry: VoiceEntry,
    sample_transcription: Transcription,
    test_user: User
) -> CleanedEntry:
    """Create a completed cleaned entry for Notion sync testing."""
    # Use timezone-naive datetime for database compatibility
    now = datetime.utcnow()

    cleaned_entry = CleanedEntry(
        id=uuid.uuid4(),
        voice_entry_id=sample_voice_entry.id,
        transcription_id=sample_transcription.id,
        user_id=test_user.id,
        cleaned_text="I had a lucid dream about flying over mountains.",
        analysis={
            "themes": ["flying", "nature"],
            "emotions": ["joy", "freedom"],
            "characters": [],
            "locations": ["mountains"]
        },
        model_name="llama3.2:3b",
        processing_started_at=now,
        processing_completed_at=now
    )
    cleaned_entry.status = "completed"

    db_session.add(cleaned_entry)
    await db_session.commit()
    await db_session.refresh(cleaned_entry)

    return cleaned_entry


class TestConfigureNotion:
    """Tests for POST /api/v1/notion/configure endpoint."""

    @pytest.mark.asyncio
    async def test_configure_notion_success(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        mock_notion_service
    ):
        """Test successfully configuring Notion integration."""
        request_data = {
            "api_key": "secret_notion_api_key",
            "database_id": "test_database_id_123",
            "auto_sync": True
        }

        response = await authenticated_client.post(
            "/api/v1/notion/configure",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Notion integration configured successfully"
        assert data["database_title"] == "Dream Journal"
        assert data["auto_sync"] is True

        # Verify database was updated
        await db_session.refresh(test_user)
        assert test_user.notion_enabled is True
        assert test_user.notion_database_id == "test_database_id_123"
        assert test_user.notion_auto_sync is True
        assert test_user.notion_api_key_encrypted is not None

        # Verify NotionService was called correctly
        mock_notion_service.validate_database.assert_called_once_with("test_database_id_123")
        mock_notion_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_configure_notion_auto_sync_false(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        mock_notion_service
    ):
        """Test configuring Notion with auto_sync disabled."""
        request_data = {
            "api_key": "secret_notion_api_key",
            "database_id": "test_database_id_123",
            "auto_sync": False
        }

        response = await authenticated_client.post(
            "/api/v1/notion/configure",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auto_sync"] is False

        await db_session.refresh(test_user)
        assert test_user.notion_auto_sync is False

    @pytest.mark.asyncio
    async def test_configure_notion_validation_error(
        self,
        authenticated_client: AsyncClient,
        mock_notion_service
    ):
        """Test configuration fails when database validation fails."""
        from app.services.notion_service import NotionValidationError

        # Mock validation error
        mock_notion_service.validate_database.side_effect = NotionValidationError(
            "Database is missing required property: Name"
        )

        request_data = {
            "api_key": "secret_notion_api_key",
            "database_id": "invalid_database_id",
            "auto_sync": True
        }

        response = await authenticated_client.post(
            "/api/v1/notion/configure",
            json=request_data
        )

        assert response.status_code == 400
        assert "missing required property" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_configure_notion_api_error(
        self,
        authenticated_client: AsyncClient,
        mock_notion_service
    ):
        """Test configuration fails when Notion API fails."""
        from app.services.notion_service import NotionAPIError

        # Mock API error
        mock_notion_service.validate_database.side_effect = NotionAPIError(
            "Failed to connect to Notion API"
        )

        request_data = {
            "api_key": "invalid_api_key",
            "database_id": "test_database_id",
            "auto_sync": True
        }

        response = await authenticated_client.post(
            "/api/v1/notion/configure",
            json=request_data
        )

        assert response.status_code == 502
        assert "failed to connect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_configure_notion_unauthorized(
        self,
        client: AsyncClient,
        mock_notion_service
    ):
        """Test configuration requires authentication."""
        request_data = {
            "api_key": "secret_notion_api_key",
            "database_id": "test_database_id",
            "auto_sync": True
        }

        response = await client.post(
            "/api/v1/notion/configure",
            json=request_data
        )

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_configure_notion_update_existing(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User,
        mock_notion_service
    ):
        """Test updating existing Notion configuration."""
        # User already has Notion configured
        old_db_id = user_with_notion_configured.notion_database_id

        request_data = {
            "api_key": "new_secret_key",
            "database_id": "new_database_id_456",
            "auto_sync": False
        }

        response = await authenticated_client.post(
            "/api/v1/notion/configure",
            json=request_data
        )

        assert response.status_code == 200

        # Verify configuration was updated
        await db_session.refresh(user_with_notion_configured)
        assert user_with_notion_configured.notion_database_id == "new_database_id_456"
        assert user_with_notion_configured.notion_database_id != old_db_id
        assert user_with_notion_configured.notion_auto_sync is False


class TestGetNotionSettings:
    """Tests for GET /api/v1/notion/settings endpoint."""

    @pytest.mark.asyncio
    async def test_get_settings_configured(
        self,
        authenticated_client: AsyncClient,
        user_with_notion_configured: User
    ):
        """Test getting settings when Notion is configured."""
        # Reconstruct authenticated client with configured user
        from app.middleware.jwt import get_current_user
        from app.database import get_db
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await authenticated_client.get("/api/v1/notion/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["database_id"] == "test_db_id_123"
        assert data["auto_sync"] is True
        assert data["has_api_key"] is True

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_settings_not_configured(
        self,
        authenticated_client: AsyncClient,
        test_user: User
    ):
        """Test getting settings when Notion is not configured."""
        response = await authenticated_client.get("/api/v1/notion/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["database_id"] is None
        assert data["auto_sync"] is True  # Default is True in the model
        assert data["has_api_key"] is False

    @pytest.mark.asyncio
    async def test_get_settings_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test getting settings requires authentication."""
        response = await client.get("/api/v1/notion/settings")

        assert response.status_code in [401, 403]


class TestDisconnectNotion:
    """Tests for DELETE /api/v1/notion/disconnect endpoint."""

    @pytest.mark.asyncio
    async def test_disconnect_notion_success(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User
    ):
        """Test successfully disconnecting Notion integration."""
        # Override current_user to use configured user
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await authenticated_client.delete("/api/v1/notion/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert "disconnected successfully" in data["message"].lower()

        # Verify all Notion settings were cleared
        await db_session.refresh(user_with_notion_configured)
        assert user_with_notion_configured.notion_enabled is False
        assert user_with_notion_configured.notion_api_key_encrypted is None
        assert user_with_notion_configured.notion_database_id is None
        assert user_with_notion_configured.notion_auto_sync is False

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_disconnect_notion_when_not_configured(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test disconnecting when Notion was never configured."""
        response = await authenticated_client.delete("/api/v1/notion/disconnect")

        assert response.status_code == 200
        # Should succeed (idempotent operation)

    @pytest.mark.asyncio
    async def test_disconnect_notion_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test disconnecting requires authentication."""
        response = await client.delete("/api/v1/notion/disconnect")

        assert response.status_code in [401, 403]


class TestSyncEntryToNotion:
    """Tests for POST /api/v1/notion/sync/{entry_id} endpoint."""

    @pytest.mark.asyncio
    async def test_sync_entry_success(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User,
        sample_voice_entry: VoiceEntry,
        completed_cleaned_entry: CleanedEntry,
        mock_notion_service
    ):
        """Test successfully triggering manual sync."""
        # Override current_user
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await authenticated_client.post(
            f"/api/v1/notion/sync/{sample_voice_entry.id}"
        )

        assert response.status_code == 202
        data = response.json()
        assert "sync_id" in data
        assert data["entry_id"] == str(sample_voice_entry.id)
        assert data["status"] == "pending"
        assert "started in background" in data["message"].lower()

        # Verify sync record was created
        from app.services.database import db_service
        sync_record = await db_service.get_notion_sync_by_id(db_session, data["sync_id"])
        assert sync_record is not None
        assert sync_record.user_id == user_with_notion_configured.id
        assert sync_record.entry_id == sample_voice_entry.id

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_entry_notion_not_configured(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry,
        completed_cleaned_entry: CleanedEntry
    ):
        """Test sync fails when Notion is not configured."""
        response = await authenticated_client.post(
            f"/api/v1/notion/sync/{sample_voice_entry.id}"
        )

        assert response.status_code == 400
        assert "not configured" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_sync_entry_not_found(
        self,
        authenticated_client: AsyncClient,
        user_with_notion_configured: User
    ):
        """Test sync fails for non-existent entry."""
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        fake_entry_id = uuid.uuid4()
        response = await authenticated_client.post(
            f"/api/v1/notion/sync/{fake_entry_id}"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_entry_no_cleaned_text(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User,
        sample_voice_entry: VoiceEntry
    ):
        """Test sync fails when no cleaned text exists."""
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await authenticated_client.post(
            f"/api/v1/notion/sync/{sample_voice_entry.id}"
        )

        assert response.status_code == 400
        assert "no cleaned text" in response.json()["detail"].lower()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_entry_different_user(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User,
        completed_cleaned_entry: CleanedEntry
    ):
        """Test user cannot sync another user's entry."""
        from app.schemas.auth import UserCreate
        from app.services.database import db_service

        # Create another user
        other_user = await db_service.create_user(
            db_session,
            UserCreate(email="other@example.com", password="Password123!")
        )
        await db_session.commit()

        # Create voice entry for other user
        other_entry = VoiceEntry(
            id=uuid.uuid4(),
            original_filename="other_dream.mp3",
            saved_filename="other_saved.mp3",
            file_path="/fake/path.mp3",
            user_id=other_user.id
        )
        db_session.add(other_entry)
        await db_session.commit()

        # Override current_user to configured user
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await authenticated_client.post(
            f"/api/v1/notion/sync/{other_entry.id}"
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_entry_unauthorized(
        self,
        client: AsyncClient,
        sample_voice_entry: VoiceEntry
    ):
        """Test sync requires authentication."""
        response = await client.post(
            f"/api/v1/notion/sync/{sample_voice_entry.id}"
        )

        assert response.status_code in [401, 403]


class TestGetSyncStatus:
    """Tests for GET /api/v1/notion/sync/{sync_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_sync_status_success(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User,
        sample_voice_entry: VoiceEntry
    ):
        """Test successfully retrieving sync status."""
        # Create sync record
        from app.services.database import db_service

        sync_record = await db_service.create_notion_sync(
            db=db_session,
            user_id=user_with_notion_configured.id,
            entry_id=sample_voice_entry.id,
            notion_database_id="test_db_123",
            status=SyncStatus.COMPLETED
        )
        sync_record.notion_page_id = "notion_page_123"
        await db_session.commit()

        # Override current_user
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await authenticated_client.get(
            f"/api/v1/notion/sync/{sync_record.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sync_record.id)
        assert data["user_id"] == str(user_with_notion_configured.id)
        assert data["entry_id"] == str(sample_voice_entry.id)
        assert data["status"] == "completed"
        assert data["notion_page_id"] == "notion_page_123"
        assert data["retry_count"] == 0

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_sync_status_not_found(
        self,
        authenticated_client: AsyncClient,
        user_with_notion_configured: User
    ):
        """Test retrieving non-existent sync record."""
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        fake_sync_id = uuid.uuid4()
        response = await authenticated_client.get(
            f"/api/v1/notion/sync/{fake_sync_id}"
        )

        assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_sync_status_different_user(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        sample_voice_entry: VoiceEntry
    ):
        """Test user cannot view another user's sync record."""
        from app.schemas.auth import UserCreate
        from app.services.database import db_service

        # Create another user
        other_user = await db_service.create_user(
            db_session,
            UserCreate(email="other@example.com", password="Password123!")
        )
        await db_session.commit()

        # Create sync record for other user
        sync_record = await db_service.create_notion_sync(
            db=db_session,
            user_id=other_user.id,
            entry_id=sample_voice_entry.id,
            notion_database_id="test_db_123"
        )
        await db_session.commit()

        response = await authenticated_client.get(
            f"/api/v1/notion/sync/{sync_record.id}"
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_sync_status_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test getting sync status requires authentication."""
        fake_sync_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/notion/sync/{fake_sync_id}"
        )

        assert response.status_code in [401, 403]


class TestListSyncs:
    """Tests for GET /api/v1/notion/syncs endpoint."""

    @pytest.mark.asyncio
    async def test_list_syncs_success(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User,
        sample_voice_entry: VoiceEntry
    ):
        """Test successfully listing sync records."""
        from app.services.database import db_service

        # Create multiple sync records
        for i in range(3):
            await db_service.create_notion_sync(
                db=db_session,
                user_id=user_with_notion_configured.id,
                entry_id=sample_voice_entry.id,
                notion_database_id="test_db_123"
            )
        await db_session.commit()

        # Override current_user
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        response = await authenticated_client.get("/api/v1/notion/syncs")

        assert response.status_code == 200
        data = response.json()
        assert "syncs" in data
        assert "total" in data
        assert len(data["syncs"]) == 3
        assert data["total"] == 3

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_syncs_empty(
        self,
        authenticated_client: AsyncClient,
        test_user: User
    ):
        """Test listing syncs when none exist."""
        response = await authenticated_client.get("/api/v1/notion/syncs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["syncs"]) == 0
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_syncs_pagination(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        user_with_notion_configured: User,
        sample_voice_entry: VoiceEntry
    ):
        """Test pagination of sync list."""
        from app.services.database import db_service

        # Create 10 sync records
        for i in range(10):
            await db_service.create_notion_sync(
                db=db_session,
                user_id=user_with_notion_configured.id,
                entry_id=sample_voice_entry.id,
                notion_database_id="test_db_123"
            )
        await db_session.commit()

        # Override current_user
        from app.middleware.jwt import get_current_user
        from app.main import app

        async def override_get_current_user():
            return user_with_notion_configured

        app.dependency_overrides[get_current_user] = override_get_current_user

        # Get first page
        response = await authenticated_client.get(
            "/api/v1/notion/syncs?limit=5&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["syncs"]) == 5
        assert data["total"] == 10

        # Get second page
        response = await authenticated_client.get(
            "/api/v1/notion/syncs?limit=5&offset=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["syncs"]) == 5
        assert data["total"] == 10

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_syncs_user_isolation(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        sample_voice_entry: VoiceEntry
    ):
        """Test users can only see their own sync records."""
        from app.schemas.auth import UserCreate
        from app.services.database import db_service

        # Create another user
        other_user = await db_service.create_user(
            db_session,
            UserCreate(email="other@example.com", password="Password123!")
        )
        await db_session.commit()

        # Create syncs for both users
        await db_service.create_notion_sync(
            db=db_session,
            user_id=test_user.id,
            entry_id=sample_voice_entry.id,
            notion_database_id="test_db_123"
        )
        await db_service.create_notion_sync(
            db=db_session,
            user_id=other_user.id,
            entry_id=sample_voice_entry.id,
            notion_database_id="test_db_456"
        )
        await db_session.commit()

        # test_user should only see their own sync
        response = await authenticated_client.get("/api/v1/notion/syncs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["syncs"]) == 1
        assert data["total"] == 1
        assert data["syncs"][0]["user_id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_list_syncs_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test listing syncs requires authentication."""
        response = await client.get("/api/v1/notion/syncs")

        assert response.status_code in [401, 403]
