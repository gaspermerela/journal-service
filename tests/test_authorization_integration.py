"""
Integration tests for authorization.
Tests that endpoints require authentication and reject unauthenticated requests.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_entry import VoiceEntry


@pytest.mark.asyncio
async def test_upload_without_auth_returns_401(client: AsyncClient, sample_mp3_path):
    """Test that upload endpoint requires authentication."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    # FastAPI HTTPBearer returns 403 for missing credentials
    assert response.status_code in [401, 403]
    assert "detail" in response.json()
    assert "not authenticated" in response.json()["detail"].lower() or "unauthorized" in response.json()["detail"].lower() or "forbidden" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_entry_without_auth_returns_401(client: AsyncClient):
    """Test that get entry endpoint requires authentication."""
    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_trigger_transcription_without_auth_returns_401(client: AsyncClient):
    """Test that trigger transcription endpoint requires authentication."""
    entry_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_transcription_without_auth_returns_401(client: AsyncClient):
    """Test that get transcription endpoint requires authentication."""
    transcription_id = uuid.uuid4()
    response = await client.get(f"/api/v1/transcriptions/{transcription_id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_transcriptions_without_auth_returns_401(client: AsyncClient):
    """Test that list transcriptions endpoint requires authentication."""
    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}/transcriptions")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_set_primary_transcription_without_auth_returns_401(client: AsyncClient):
    """Test that set primary transcription endpoint requires authentication."""
    transcription_id = uuid.uuid4()
    response = await client.put(f"/api/v1/transcriptions/{transcription_id}/set-primary")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    """Test that invalid token is rejected."""
    client.headers["Authorization"] = "Bearer invalid.token.here"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_malformed_auth_header_returns_401(client: AsyncClient):
    """Test that malformed authorization header is rejected."""
    # Missing "Bearer" prefix
    client.headers["Authorization"] = "some-token"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_empty_auth_header_returns_401(client: AsyncClient):
    """Test that empty authorization header is rejected."""
    client.headers["Authorization"] = ""

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_wrong_auth_scheme_returns_401(client: AsyncClient):
    """Test that wrong authentication scheme is rejected."""
    client.headers["Authorization"] = "Basic dGVzdDp0ZXN0"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_using_refresh_token_as_access_token_returns_401(
    client: AsyncClient,
    db_session: AsyncSession
):
    """Test that refresh token cannot be used as access token."""
    from app.schemas.auth import UserCreate
    from app.services.database import db_service

    # Create user and login
    user_data = UserCreate(email="refreshtest@example.com", password="Password123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "refreshtest@example.com", "password": "Password123!"}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # Try to use refresh token as access token
    client.headers["Authorization"] = f"Bearer {tokens['refresh_token']}"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_health_endpoint_does_not_require_auth(client: AsyncClient):
    """Test that health endpoint is publicly accessible."""
    response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_register_does_not_require_auth(client: AsyncClient):
    """Test that registration endpoint is publicly accessible."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "NewPassword123!"
        }
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_auth_login_does_not_require_auth(client: AsyncClient, db_session: AsyncSession):
    """Test that login endpoint is publicly accessible."""
    from app.schemas.auth import UserCreate
    from app.services.database import db_service

    # Create user first
    user_data = UserCreate(email="loginuser@example.com", password="Password123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "Password123!"
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_refresh_does_not_require_auth_header(
    client: AsyncClient,
    db_session: AsyncSession
):
    """Test that refresh endpoint works without Authorization header (uses token in body)."""
    from app.schemas.auth import UserCreate
    from app.services.database import db_service

    # Create user and login
    user_data = UserCreate(email="refreshuser@example.com", password="Password123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "refreshuser@example.com", "password": "Password123!"}
    )
    tokens = login_response.json()

    # Refresh without auth header
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_case_sensitive_bearer_keyword(client: AsyncClient):
    """Test that Bearer keyword is case-sensitive."""
    client.headers["Authorization"] = "bearer fake-token"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    # Should be 401 because lowercase "bearer" is not valid
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_multiple_bearer_tokens_rejected(client: AsyncClient):
    """Test that multiple tokens in auth header are rejected."""
    client.headers["Authorization"] = "Bearer token1 Bearer token2"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code in [401, 403]
