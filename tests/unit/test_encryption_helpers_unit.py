"""
Unit tests for encryption helper functions.

Tests cover:
- decrypt_text(): text decryption
- decrypt_json(): JSON decryption
- encrypt_text(): text encryption
- encrypt_json(): JSON encryption
- cleanup_temp_file(): secure temp file deletion
"""

import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.encryption_helpers import (
    decrypt_text,
    decrypt_json,
    encrypt_text,
    encrypt_json,
    cleanup_temp_file,
)


# =============================================================================
# decrypt_text() Tests
# =============================================================================


class TestDecryptText:
    """Tests for decrypt_text() helper."""

    @pytest.mark.asyncio
    async def test_returns_decrypted_text(self):
        """Returns decrypted text when data is encrypted."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        encrypted_bytes = b"encrypted_data"
        decrypted_text = "Hello, World!"

        mock_encryption_service.decrypt_data.return_value = decrypted_text.encode(
            "utf-8"
        )

        result = await decrypt_text(
            encryption_service=mock_encryption_service,
            db=mock_db,
            encrypted_bytes=encrypted_bytes,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result == decrypted_text
        mock_encryption_service.decrypt_data.assert_called_once_with(
            mock_db, encrypted_bytes, voice_entry_id, user_id
        )

    @pytest.mark.asyncio
    async def test_raises_error_when_service_none(self):
        """Raises RuntimeError when service is None."""
        mock_db = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        encrypted_bytes = b"encrypted_data"

        with pytest.raises(RuntimeError, match="unavailable"):
            await decrypt_text(
                encryption_service=None,
                db=mock_db,
                encrypted_bytes=encrypted_bytes,
                voice_entry_id=voice_entry_id,
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self):
        """Returns None when encrypted_bytes is None."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = await decrypt_text(
            encryption_service=mock_encryption_service,
            db=mock_db,
            encrypted_bytes=None,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result is None
        mock_encryption_service.decrypt_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_decryption_error(self):
        """Returns None when decryption fails."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        encrypted_bytes = b"corrupted_data"

        mock_encryption_service.decrypt_data.side_effect = Exception("Decryption failed")

        result = await decrypt_text(
            encryption_service=mock_encryption_service,
            db=mock_db,
            encrypted_bytes=encrypted_bytes,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result is None


# =============================================================================
# decrypt_json() Tests
# =============================================================================


class TestDecryptJson:
    """Tests for decrypt_json() helper."""

    @pytest.mark.asyncio
    async def test_returns_decrypted_dict(self):
        """Returns decrypted dict when data is encrypted."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        encrypted_bytes = b"encrypted_json"
        expected_dict = {"key": "value", "nested": {"a": 1}}

        mock_encryption_service.decrypt_data.return_value = json.dumps(
            expected_dict
        ).encode("utf-8")

        result = await decrypt_json(
            encryption_service=mock_encryption_service,
            db=mock_db,
            encrypted_bytes=encrypted_bytes,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result == expected_dict

    @pytest.mark.asyncio
    async def test_raises_error_when_service_none(self):
        """Raises RuntimeError when service is None."""
        mock_db = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        encrypted_bytes = b"encrypted_json"

        with pytest.raises(RuntimeError, match="unavailable"):
            await decrypt_json(
                encryption_service=None,
                db=mock_db,
                encrypted_bytes=encrypted_bytes,
                voice_entry_id=voice_entry_id,
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self):
        """Returns None when encrypted_bytes is None."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = await decrypt_json(
            encryption_service=mock_encryption_service,
            db=mock_db,
            encrypted_bytes=None,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result is None
        mock_encryption_service.decrypt_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_complex_nested_json(self):
        """Handles complex nested JSON structures."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        encrypted_bytes = b"encrypted_json"
        complex_dict = {
            "themes": ["adventure", "mystery"],
            "symbols": [{"name": "moon", "meaning": "change"}],
            "emotions": {"primary": "joy", "secondary": ["hope", "curiosity"]},
            "nested": {"level1": {"level2": {"level3": "deep value"}}},
        }

        mock_encryption_service.decrypt_data.return_value = json.dumps(
            complex_dict
        ).encode("utf-8")

        result = await decrypt_json(
            encryption_service=mock_encryption_service,
            db=mock_db,
            encrypted_bytes=encrypted_bytes,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result == complex_dict

    @pytest.mark.asyncio
    async def test_handles_decryption_error(self):
        """Returns None when decryption fails."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        encrypted_bytes = b"corrupted_data"

        mock_encryption_service.decrypt_data.side_effect = Exception("Decryption failed")

        result = await decrypt_json(
            encryption_service=mock_encryption_service,
            db=mock_db,
            encrypted_bytes=encrypted_bytes,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result is None


# =============================================================================
# encrypt_text() Tests
# =============================================================================


class TestEncryptText:
    """Tests for encrypt_text() helper."""

    @pytest.mark.asyncio
    async def test_encrypts_text_successfully(self):
        """Encrypts text and returns bytes."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        text = "Secret message"
        encrypted_bytes = b"encrypted_result"

        mock_encryption_service.encrypt_data.return_value = encrypted_bytes

        result = await encrypt_text(
            encryption_service=mock_encryption_service,
            db=mock_db,
            text=text,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result == encrypted_bytes
        mock_encryption_service.encrypt_data.assert_called_once_with(
            mock_db, text, voice_entry_id, user_id
        )

    @pytest.mark.asyncio
    async def test_returns_bytes(self):
        """Encrypt returns bytes type."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_encryption_service.encrypt_data.return_value = b"encrypted"

        result = await encrypt_text(
            encryption_service=mock_encryption_service,
            db=mock_db,
            text="any text",
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert isinstance(result, bytes)


# =============================================================================
# encrypt_json() Tests
# =============================================================================


class TestEncryptJson:
    """Tests for encrypt_json() helper."""

    @pytest.mark.asyncio
    async def test_encrypts_dict_successfully(self):
        """Encrypts dict by serializing to JSON first."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        data = {"key": "value"}
        encrypted_bytes = b"encrypted_json"

        mock_encryption_service.encrypt_data.return_value = encrypted_bytes

        result = await encrypt_json(
            encryption_service=mock_encryption_service,
            db=mock_db,
            data=data,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result == encrypted_bytes
        # Verify JSON serialization was used
        call_args = mock_encryption_service.encrypt_data.call_args
        assert call_args[0][1] == json.dumps(data)

    @pytest.mark.asyncio
    async def test_encrypts_nested_structure(self):
        """Handles nested structures during encryption."""
        mock_db = AsyncMock()
        mock_encryption_service = AsyncMock()
        voice_entry_id = uuid.uuid4()
        user_id = uuid.uuid4()
        nested_data = {
            "level1": {"level2": {"array": [1, 2, 3], "string": "deep"}},
            "list_of_dicts": [{"a": 1}, {"b": 2}],
        }
        encrypted_bytes = b"encrypted_nested"

        mock_encryption_service.encrypt_data.return_value = encrypted_bytes

        result = await encrypt_json(
            encryption_service=mock_encryption_service,
            db=mock_db,
            data=nested_data,
            voice_entry_id=voice_entry_id,
            user_id=user_id,
        )

        assert result == encrypted_bytes


# =============================================================================
# cleanup_temp_file() Tests
# =============================================================================


class TestCleanupTempFile:
    """Tests for cleanup_temp_file() helper."""

    def test_deletes_existing_file(self, tmp_path):
        """Successfully deletes existing temp file."""
        temp_file = tmp_path / "test.dec"
        temp_file.write_text("temp content")
        assert temp_file.exists()

        cleanup_temp_file(temp_file)

        assert not temp_file.exists()

    def test_handles_none_path(self):
        """Handles None path gracefully without error."""
        # Should not raise any exception
        cleanup_temp_file(None)

    def test_handles_nonexistent_file(self, tmp_path):
        """Handles nonexistent file path gracefully."""
        nonexistent = tmp_path / "nonexistent.dec"
        assert not nonexistent.exists()

        # Should not raise any exception
        cleanup_temp_file(nonexistent)

    def test_logs_warning_on_deletion_error(self, tmp_path):
        """Logs warning when file deletion fails."""
        # Create a file and make it read-only directory (can't delete file in it)
        temp_file = tmp_path / "test.dec"
        temp_file.write_text("temp content")

        # Mock the unlink to raise an exception
        with patch.object(Path, "unlink", side_effect=PermissionError("Access denied")):
            # Should not raise, just log warning
            cleanup_temp_file(temp_file)

        # File still exists because unlink was mocked
        assert temp_file.exists()
