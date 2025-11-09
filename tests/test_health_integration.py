"""
Integration tests for health endpoint.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_health_check_success(client: AsyncClient):
    """Test health check endpoint returns healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "timestamp" in data

    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_check_response_format(client: AsyncClient):
    """Test that health check response has correct format."""
    response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()

    # Check all required fields are present
    required_fields = ["status", "database", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check data types
    assert isinstance(data["status"], str)
    assert isinstance(data["database"], str)
    assert isinstance(data["timestamp"], str)


@pytest.mark.asyncio
async def test_health_check_timestamp_format(client: AsyncClient):
    """Test that timestamp is in ISO format."""
    response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()

    # Should be ISO 8601 format
    try:
        parsed_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        # Timestamp should be recent (within last minute)
        now = datetime.now(parsed_time.tzinfo)
        time_diff = abs((now - parsed_time).total_seconds())
        assert time_diff < 60, "Timestamp is not recent"
    except ValueError:
        pytest.fail("Invalid timestamp format in response")


@pytest.mark.asyncio
async def test_health_check_multiple_calls(client: AsyncClient):
    """Test that health check can be called multiple times."""
    for i in range(3):
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_check_with_database_operations(client: AsyncClient, sample_mp3_path):
    """Test health check after performing database operations."""
    # Upload a file (which involves database operations)
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201

    # Health check should still work
    health_response = await client.get("/health")

    assert health_response.status_code == 200
    data = health_response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_check_content_type(client: AsyncClient):
    """Test that health check returns JSON content type."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
