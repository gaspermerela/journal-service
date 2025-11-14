"""
End-to-end authentication flow tests.
Tests complete user journeys from registration to using the API.
"""
import uuid
import pytest
from httpx import AsyncClient
from pathlib import Path


@pytest.mark.asyncio
async def test_complete_auth_flow_register_login_upload_retrieve(
    client: AsyncClient,
    sample_mp3_path: Path
):
    """
    Test complete flow: Register -> Login -> Upload -> Retrieve Entry.
    This tests the entire user journey from account creation to API usage.
    """
    # Step 1: Register new user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e_user@example.com",
            "password": "E2EPassword123!"
        }
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == "e2e_user@example.com"
    assert user_data["is_active"] is True
    user_id = user_data["id"]

    # Step 2: Login with the registered user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "e2e_user@example.com",
            "password": "E2EPassword123!"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert "user" in tokens
    assert tokens["user"]["email"] == "e2e_user@example.com"
    access_token = tokens["access_token"]

    # Step 3: Upload a file using the access token
    client.headers["Authorization"] = f"Bearer {access_token}"

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("my_recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_data = upload_response.json()
    assert entry_data["original_filename"] == "my_recording.mp3"
    entry_id = entry_data["id"]

    # Step 4: Retrieve the uploaded entry
    retrieve_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert retrieve_response.status_code == 200
    retrieved_entry = retrieve_response.json()
    assert retrieved_entry["id"] == entry_id
    assert retrieved_entry["original_filename"] == "my_recording.mp3"


@pytest.mark.asyncio
async def test_e2e_token_refresh_flow(client: AsyncClient, sample_mp3_path: Path):
    """
    Test token refresh flow:
    Register -> Login -> Upload -> Use Access Token -> Refresh Token -> Use New Access Token.
    """
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh_user@example.com", "password": "RefreshPass123!"}
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh_user@example.com", "password": "RefreshPass123!"}
    )
    tokens = login_response.json()
    original_access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Upload a file with original access token
    client.headers["Authorization"] = f"Bearer {original_access_token}"
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]

    # Verify we can access the entry with original token
    response = await client.get(f"/api/v1/entries/{entry_id}")
    assert response.status_code == 200
    assert response.json()["id"] == entry_id

    # Wait to ensure new token has different timestamp
    import asyncio
    await asyncio.sleep(2)

    # Refresh tokens
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    new_access_token = new_tokens["access_token"]

    # Verify new token is different
    assert new_access_token != original_access_token

    # Verify user data is included in refresh response
    assert "user" in new_tokens
    assert new_tokens["user"]["email"] == "refresh_user@example.com"
    assert new_tokens["user"]["is_active"] is True

    # Use new access token to access the same entry
    client.headers["Authorization"] = f"Bearer {new_access_token}"
    response = await client.get(f"/api/v1/entries/{entry_id}")
    assert response.status_code == 200
    assert response.json()["id"] == entry_id  # Can still access our entry with new token


@pytest.mark.asyncio
async def test_e2e_multiple_uploads_and_list(
    client: AsyncClient,
    sample_mp3_path: Path
):
    """
    Test uploading multiple files and verifying they're all associated with the user.
    """
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "uploader@example.com", "password": "UploadPass123!"}
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "uploader@example.com", "password": "UploadPass123!"}
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Upload 3 files
    entry_ids = []
    for i in range(3):
        with open(sample_mp3_path, 'rb') as f:
            files = {"file": (f"recording_{i}.mp3", f, "audio/mpeg")}
            upload_response = await client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 201
        entry_ids.append(upload_response.json()["id"])

    # Verify all entries are accessible
    for entry_id in entry_ids:
        response = await client.get(f"/api/v1/entries/{entry_id}")
        assert response.status_code == 200
        assert response.json()["id"] == entry_id


@pytest.mark.asyncio
async def test_e2e_user_cannot_see_other_user_data(
    client: AsyncClient,
    sample_mp3_path: Path
):
    """
    Test that User A cannot see User B's uploaded files.
    """
    # User A: Register, login, upload
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user_a_e2e@example.com", "password": "PasswordA123!"}
    )
    login_a = await client.post(
        "/api/v1/auth/login",
        json={"email": "user_a_e2e@example.com", "password": "PasswordA123!"}
    )
    token_a = login_a.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token_a}"

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("user_a_file.mp3", f, "audio/mpeg")}
        upload_a = await client.post("/api/v1/upload", files=files)

    entry_a_id = upload_a.json()["id"]

    # User B: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user_b_e2e@example.com", "password": "PasswordB123!"}
    )
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "user_b_e2e@example.com", "password": "PasswordB123!"}
    )
    token_b = login_b.json()["access_token"]

    # User B tries to access User A's entry
    client.headers["Authorization"] = f"Bearer {token_b}"
    response = await client.get(f"/api/v1/entries/{entry_a_id}")

    # Should be 404 (not found) because User B doesn't have access
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_e2e_login_fails_with_wrong_password(client: AsyncClient):
    """Test that login fails with incorrect password."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "secure_user@example.com", "password": "CorrectPass123!"}
    )

    # Try to login with wrong password
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "secure_user@example.com", "password": "WrongPass123!"}
    )

    assert login_response.status_code == 401
    assert "invalid" in login_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_e2e_cannot_register_duplicate_email(client: AsyncClient):
    """Test that registering with duplicate email fails."""
    email = "duplicate_e2e@example.com"

    # First registration
    response1 = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!"}
    )
    assert response1.status_code == 201

    # Second registration with same email
    response2 = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "DifferentPass123!"}
    )
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_e2e_cannot_access_api_without_token(
    client: AsyncClient,
    sample_mp3_path: Path
):
    """Test that API endpoints are protected and require authentication."""
    # Try to upload without authentication
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code in [401, 403]

    # Try to get entry without authentication
    entry_response = await client.get(f"/api/v1/entries/{uuid.uuid4()}")
    assert entry_response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_e2e_health_check_no_auth_required(client: AsyncClient):
    """Test that health check endpoint doesn't require authentication."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


