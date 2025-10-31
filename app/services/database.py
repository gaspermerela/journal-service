"""
Database service for CRUD operations on dream entries.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.dream_entry import DreamEntry
from app.schemas.dream_entry import DreamEntryCreate
from app.utils.logger import get_logger

logger = get_logger("database_service")


class DatabaseService:
    """Service for database operations on dream entries."""

    async def create_entry(
        self,
        db: AsyncSession,
        entry_data: DreamEntryCreate
    ) -> DreamEntry:
        """
        Create a new dream entry in the database.

        Args:
            db: Database session
            entry_data: Entry data to create

        Returns:
            Created DreamEntry instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            entry = DreamEntry(
                original_filename=entry_data.original_filename,
                saved_filename=entry_data.saved_filename,
                file_path=entry_data.file_path,
                uploaded_at=entry_data.uploaded_at
            )

            db.add(entry)
            await db.flush()  # Flush to get the ID without committing
            await db.refresh(entry)

            logger.info(
                f"Database entry created",
                entry_id=str(entry.id),
                original_filename=entry_data.original_filename
            )

            return entry

        except Exception as e:
            logger.error(
                f"Failed to create database entry",
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create database record"
            )

    async def get_entry_by_id(
        self,
        db: AsyncSession,
        entry_id: UUID
    ) -> Optional[DreamEntry]:
        """
        Retrieve a dream entry by ID.

        Args:
            db: Database session
            entry_id: UUID of the entry to retrieve

        Returns:
            DreamEntry if found, None otherwise
        """
        try:
            result = await db.execute(
                select(DreamEntry).where(DreamEntry.id == entry_id)
            )
            entry = result.scalar_one_or_none()

            if entry:
                logger.info(f"Entry retrieved", entry_id=str(entry_id))
            else:
                logger.info(f"Entry not found", entry_id=str(entry_id))

            return entry

        except Exception as e:
            logger.error(
                f"Failed to retrieve entry",
                entry_id=str(entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve entry from database"
            )

    async def delete_entry(
        self,
        db: AsyncSession,
        entry_id: UUID
    ) -> bool:
        """
        Delete a dream entry by ID.

        Args:
            db: Database session
            entry_id: UUID of the entry to delete

        Returns:
            True if deletion successful, False if entry not found

        Raises:
            HTTPException: If database operation fails
        """
        try:
            entry = await self.get_entry_by_id(db, entry_id)

            if not entry:
                return False

            await db.delete(entry)
            await db.flush()

            logger.info(f"Entry deleted from database", entry_id=str(entry_id))
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to delete entry",
                entry_id=str(entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete entry from database"
            )


# Global database service instance
db_service = DatabaseService()
