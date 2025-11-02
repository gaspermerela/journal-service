"""
File storage service for saving audio files to disk.
"""
import os
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
import aiofiles

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("storage")


class StorageService:
    """Service for handling file storage operations."""

    def __init__(self):
        self.base_path = Path(settings.AUDIO_STORAGE_PATH)

    def _generate_filename(self, file_id: uuid.UUID) -> str:
        """
        Generate unique filename with UUID and timestamp.

        Args:
            file_id: UUID for the file

        Returns:
            Filename in format: {uuid}_{timestamp}.mp3
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        return f"{file_id}_{timestamp}.mp3"

    def _get_date_folder(self) -> str:
        """
        Get date-based folder name for current date.

        Returns:
            Folder name in format: YYYY-MM-DD
        """
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _ensure_directory_exists(self, directory: Path) -> None:
        """
        Create directory if it doesn't exist.

        Args:
            directory: Directory path to create

        Raises:
            HTTPException: If directory creation fails
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ensured", path=str(directory))
        except Exception as e:
            logger.error(f"Failed to create directory", path=str(directory), error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create storage directory"
            )

    async def save_file(self, file: UploadFile, file_id: uuid.UUID) -> Tuple[str, str]:
        """
        Save uploaded file to disk with atomic write operation.

        Args:
            file: Uploaded file from FastAPI
            file_id: UUID for the file

        Returns:
            Tuple of (saved_filename, absolute_file_path)

        Raises:
            HTTPException: If file save operation fails
        """
        # Generate filename and path
        saved_filename = self._generate_filename(file_id)
        date_folder = self._get_date_folder()
        target_dir = self.base_path / date_folder
        target_path = target_dir / saved_filename

        # Ensure directory exists
        self._ensure_directory_exists(target_dir)

        # Create temporary file path
        temp_path = target_dir / f"{saved_filename}.tmp"

        try:
            # Write to temporary file first (atomic operation)
            async with aiofiles.open(temp_path, 'wb') as out_file:
                # Read and write in chunks
                chunk_size = 1024 * 1024  # 1MB chunks
                while content := await file.read(chunk_size):
                    await out_file.write(content)

            # Move temp file to final location
            shutil.move(str(temp_path), str(target_path))

            # Set file permissions (644)
            os.chmod(target_path, 0o644)

            logger.info(
                f"File saved successfully",
                filename=saved_filename,
                path=str(target_path)
            )

            return saved_filename, str(target_path)

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

            logger.error(
                f"Failed to save file",
                filename=file.filename,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file to storage"
            )

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Absolute path to the file

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted", path=file_path)
                return True
            else:
                logger.warning(f"File not found for deletion", path=file_path)
                return False
        except Exception as e:
            logger.error(
                f"Failed to delete file",
                path=file_path,
                error=str(e),
                exc_info=True
            )
            return False


# Global storage service instance
storage_service = StorageService()
