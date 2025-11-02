"""
End-to-end tests for running service instance.

These tests require the service to be running externally.
Start the service with: python -m uvicorn app.main:app

Run these tests with: pytest tests/test_e2e.py
"""

import os
from pathlib import Path
from typing import Optional

import pytest
import requests


# Configuration
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
TIMEOUT = 10  # seconds


def is_service_available() -> bool:
    """Check if the service is running and responding."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture(scope="module", autouse=True)
def check_service_running():
    """Ensure service is running before tests."""
    if not is_service_available():
        pytest.skip(
            f"Service not available at {BASE_URL}. "
            "Start with: python -m uvicorn app.main:app"
        )


@pytest.fixture
def temp_audio_file(tmp_path) -> Path:
    """Create a temporary valid MP3 file."""
    audio_path = tmp_path / "test_audio.mp3"

    # Create a minimal valid MP3 file (ID3v2 header + MPEG frame)
    # This is sufficient for file validation tests
    mp3_data = (
        b'ID3\x04\x00\x00\x00\x00\x00\x00'  # ID3v2.4 header
        b'\xff\xfb\x90\x00'  # MPEG sync + frame header (44.1kHz, 128kbps)
        + b'\x00' * 417  # Frame data padding
    )
    audio_path.write_bytes(mp3_data)

    return audio_path


@pytest.fixture
def temp_invalid_file(tmp_path) -> Path:
    """Create a temporary invalid file (not MP3)."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("This is not an MP3 file")
    return file_path


class TestE2EHealth:
    """End-to-end tests for health endpoint."""

    def test_health_endpoint_returns_200(self):
        """Health endpoint should return 200 OK."""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200

    def test_health_endpoint_json_format(self):
        """Health endpoint should return proper JSON."""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "database" in data

    def test_health_database_status(self):
        """Health endpoint should report database status."""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        data = response.json()

        # Database should be "connected" or "disconnected"
        assert data["database"] in ["connected", "disconnected"]

        # Status should be "healthy" or "degraded"
        assert data["status"] in ["healthy", "degraded"]


class TestE2EUpload:
    """End-to-end tests for upload endpoint."""

    def test_upload_valid_mp3(self, temp_audio_file):
        """Valid MP3 file should upload successfully."""
        with open(temp_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            response = requests.post(
                f"{BASE_URL}/api/v1/upload",
                files=files,
                timeout=TIMEOUT
            )

        assert response.status_code == 201  # Created
        data = response.json()

        assert "id" in data
        assert "original_filename" in data
        assert "saved_filename" in data
        assert "file_path" in data
        assert "uploaded_at" in data
        assert "message" in data

    def test_upload_returns_valid_uuid(self, temp_audio_file):
        """Upload should return a valid UUID."""
        import uuid

        with open(temp_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            response = requests.post(
                f"{BASE_URL}/api/v1/upload",
                files=files,
                timeout=TIMEOUT
            )

        data = response.json()

        # Should be able to parse as UUID
        try:
            uuid.UUID(data["id"])
        except ValueError:
            pytest.fail(f"Invalid UUID: {data['id']}")

    def test_upload_invalid_file_type(self, temp_invalid_file):
        """Non-MP3 file should be rejected."""
        with open(temp_invalid_file, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = requests.post(
                f"{BASE_URL}/api/v1/upload",
                files=files,
                timeout=TIMEOUT
            )

        assert response.status_code == 400

    def test_upload_no_file(self):
        """Upload without file should fail."""
        response = requests.post(f"{BASE_URL}/api/v1/upload", timeout=TIMEOUT)
        assert response.status_code == 422  # Validation error

    def test_upload_empty_file(self, tmp_path):
        """Empty file should be rejected."""
        empty_file = tmp_path / "empty.mp3"
        empty_file.write_bytes(b"")

        with open(empty_file, "rb") as f:
            files = {"file": ("empty.mp3", f, "audio/mpeg")}
            response = requests.post(
                f"{BASE_URL}/api/v1/upload",
                files=files,
                timeout=TIMEOUT
            )

        assert response.status_code == 400


class TestE2EEntries:
    """End-to-end tests for entries retrieval."""

    def test_get_existing_entry(self, temp_audio_file):
        """Should retrieve an entry that was just uploaded."""
        # First upload a file
        with open(temp_audio_file, "rb") as f:
            files = {"file": ("test.mp3", f, "audio/mpeg")}
            upload_response = requests.post(
                f"{BASE_URL}/api/v1/upload",
                files=files,
                timeout=TIMEOUT
            )

        assert upload_response.status_code == 201
        entry_id = upload_response.json()["id"]

        # Now retrieve it
        response = requests.get(
            f"{BASE_URL}/api/v1/entries/{entry_id}",
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == entry_id
        assert "original_filename" in data
        assert "saved_filename" in data
        assert "file_path" in data
        assert "uploaded_at" in data

    def test_get_nonexistent_entry(self):
        """Should return 404 for non-existent entry."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = requests.get(
            f"{BASE_URL}/api/v1/entries/{fake_uuid}",
            timeout=TIMEOUT
        )

        assert response.status_code == 404

    def test_get_entry_invalid_uuid(self):
        """Should return 422 for invalid UUID format."""
        response = requests.get(
            f"{BASE_URL}/api/v1/entries/not-a-uuid",
            timeout=TIMEOUT
        )

        assert response.status_code == 422


class TestE2EFullWorkflow:
    """End-to-end tests for complete workflows."""

    def test_complete_upload_retrieve_cycle(self, temp_audio_file):
        """Test complete cycle: upload → verify → retrieve."""
        # 1. Upload
        with open(temp_audio_file, "rb") as f:
            files = {"file": ("workflow_test.mp3", f, "audio/mpeg")}
            upload_response = requests.post(
                f"{BASE_URL}/api/v1/upload",
                files=files,
                timeout=TIMEOUT
            )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        entry_id = upload_data["id"]

        # 2. Verify upload response
        assert upload_data["original_filename"] == "workflow_test.mp3"
        assert "saved_filename" in upload_data
        assert "file_path" in upload_data
        assert "uploaded_at" in upload_data
        assert upload_data["message"] == "File uploaded successfully"

        # 3. Retrieve entry
        retrieve_response = requests.get(
            f"{BASE_URL}/api/v1/entries/{entry_id}",
            timeout=TIMEOUT
        )

        assert retrieve_response.status_code == 200
        retrieve_data = retrieve_response.json()

        # 4. Verify retrieved data matches upload
        assert retrieve_data["id"] == entry_id
        assert retrieve_data["original_filename"] == upload_data["original_filename"]
        assert retrieve_data["saved_filename"] == upload_data["saved_filename"]
        assert retrieve_data["file_path"] == upload_data["file_path"]
        assert retrieve_data["uploaded_at"] == upload_data["uploaded_at"]

    def test_multiple_uploads(self, tmp_path):
        """Test uploading multiple files in sequence."""
        uploaded_ids = []

        # Minimal MP3 data
        mp3_data = (
            b'ID3\x04\x00\x00\x00\x00\x00\x00'
            b'\xff\xfb\x90\x00'
            + b'\x00' * 417
        )

        for i in range(3):
            # Create unique audio file
            audio_path = tmp_path / f"multi_test_{i}.mp3"
            audio_path.write_bytes(mp3_data)

            # Upload
            with open(audio_path, "rb") as f:
                files = {"file": (f"multi_test_{i}.mp3", f, "audio/mpeg")}
                response = requests.post(
                    f"{BASE_URL}/api/v1/upload",
                    files=files,
                    timeout=TIMEOUT
                )

            assert response.status_code == 201
            uploaded_ids.append(response.json()["id"])

        # Verify all uploads have unique IDs
        assert len(uploaded_ids) == len(set(uploaded_ids))

        # Verify all can be retrieved
        for entry_id in uploaded_ids:
            response = requests.get(
                f"{BASE_URL}/api/v1/entries/{entry_id}",
                timeout=TIMEOUT
            )
            assert response.status_code == 200


class TestE2EDocumentation:
    """End-to-end tests for API documentation endpoints."""

    def test_openapi_json_available(self):
        """OpenAPI JSON schema should be accessible."""
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT)
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_page_available(self):
        """Swagger UI documentation should be accessible."""
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_page_available(self):
        """ReDoc documentation should be accessible."""
        response = requests.get(f"{BASE_URL}/redoc", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


if __name__ == "__main__":
    # Quick check if service is available
    if is_service_available():
        print(f"✓ Service is available at {BASE_URL}")
        print("Run tests with: pytest tests/test_e2e.py -v")
    else:
        print(f"✗ Service not available at {BASE_URL}")
        print("Start service with: python -m uvicorn app.main:app")
