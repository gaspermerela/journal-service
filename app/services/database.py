"""
Database service for CRUD operations on dream entries and transcriptions.
"""
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.dream_entry import DreamEntry
from app.models.transcription import Transcription
from app.schemas.dream_entry import DreamEntryCreate
from app.schemas.transcription import TranscriptionCreate
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

    # ===== Transcription Operations =====

    async def create_transcription(
        self,
        db: AsyncSession,
        transcription_data: TranscriptionCreate
    ) -> Transcription:
        """
        Create a new transcription record in the database.

        Args:
            db: Database session
            transcription_data: Transcription data to create

        Returns:
            Created Transcription instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            transcription = Transcription(
                entry_id=transcription_data.entry_id,
                status=transcription_data.status,
                model_used=transcription_data.model_used,
                language_code=transcription_data.language_code,
                is_primary=transcription_data.is_primary
            )

            db.add(transcription)
            await db.flush()
            await db.refresh(transcription)

            logger.info(
                f"Transcription record created",
                transcription_id=str(transcription.id),
                entry_id=str(transcription_data.entry_id),
                model=transcription_data.model_used
            )

            return transcription

        except Exception as e:
            logger.error(
                f"Failed to create transcription record",
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transcription record"
            )

    async def get_transcription_by_id(
        self,
        db: AsyncSession,
        transcription_id: UUID
    ) -> Optional[Transcription]:
        """
        Retrieve a transcription by ID.

        Args:
            db: Database session
            transcription_id: UUID of the transcription to retrieve

        Returns:
            Transcription if found, None otherwise
        """
        try:
            result = await db.execute(
                select(Transcription).where(Transcription.id == transcription_id)
            )
            transcription = result.scalar_one_or_none()

            if transcription:
                logger.info(f"Transcription retrieved", transcription_id=str(transcription_id))
            else:
                logger.info(f"Transcription not found", transcription_id=str(transcription_id))

            return transcription

        except Exception as e:
            logger.error(
                f"Failed to retrieve transcription",
                transcription_id=str(transcription_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve transcription from database"
            )

    async def get_transcriptions_for_entry(
        self,
        db: AsyncSession,
        entry_id: UUID
    ) -> list[Transcription]:
        """
        Get all transcriptions for a specific dream entry.

        Args:
            db: Database session
            entry_id: UUID of the entry

        Returns:
            List of Transcription objects
        """
        try:
            result = await db.execute(
                select(Transcription)
                .where(Transcription.entry_id == entry_id)
                .order_by(Transcription.created_at.desc())
            )
            transcriptions = result.scalars().all()

            logger.info(
                f"Retrieved transcriptions for entry",
                entry_id=str(entry_id),
                count=len(transcriptions)
            )

            return list(transcriptions)

        except Exception as e:
            logger.error(
                f"Failed to retrieve transcriptions",
                entry_id=str(entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve transcriptions from database"
            )

    async def get_primary_transcription(
        self,
        db: AsyncSession,
        entry_id: UUID
    ) -> Optional[Transcription]:
        """
        Get the primary transcription for an entry.

        Args:
            db: Database session
            entry_id: UUID of the entry

        Returns:
            Primary Transcription if found, None otherwise
        """
        try:
            result = await db.execute(
                select(Transcription)
                .where(
                    Transcription.entry_id == entry_id,
                    Transcription.is_primary == True
                )
            )
            transcription = result.scalar_one_or_none()

            return transcription

        except Exception as e:
            logger.error(
                f"Failed to retrieve primary transcription",
                entry_id=str(entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve primary transcription"
            )

    async def update_transcription_status(
        self,
        db: AsyncSession,
        transcription_id: UUID,
        status: str,
        transcribed_text: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Transcription]:
        """
        Update transcription status and related fields.

        Args:
            db: Database session
            transcription_id: UUID of the transcription
            status: New status value
            transcribed_text: Optional transcribed text
            error_message: Optional error message

        Returns:
            Updated Transcription instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            transcription = await self.get_transcription_by_id(db, transcription_id)

            if not transcription:
                logger.warning(f"Transcription not found for update", transcription_id=str(transcription_id))
                return None

            # Update fields
            transcription.status = status

            if status == "processing" and not transcription.transcription_started_at:
                transcription.transcription_started_at = datetime.now(timezone.utc)

            if status == "completed":
                transcription.transcription_completed_at = datetime.now(timezone.utc)
                if transcribed_text:
                    transcription.transcribed_text = transcribed_text

            if status == "failed":
                transcription.transcription_completed_at = datetime.now(timezone.utc)
                if error_message:
                    transcription.error_message = error_message

            await db.flush()
            await db.refresh(transcription)

            logger.info(
                f"Transcription status updated",
                transcription_id=str(transcription_id),
                status=status
            )

            return transcription

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update transcription status",
                transcription_id=str(transcription_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transcription status"
            )

    async def set_primary_transcription(
        self,
        db: AsyncSession,
        transcription_id: UUID
    ) -> Optional[Transcription]:
        """
        Set a transcription as primary for its entry.
        Unsets any existing primary transcription for the same entry.

        Args:
            db: Database session
            transcription_id: UUID of the transcription to set as primary

        Returns:
            Updated Transcription instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            transcription = await self.get_transcription_by_id(db, transcription_id)

            if not transcription:
                logger.warning(f"Transcription not found", transcription_id=str(transcription_id))
                return None

            # Unset any existing primary transcription for this entry
            await db.execute(
                update(Transcription)
                .where(
                    Transcription.entry_id == transcription.entry_id,
                    Transcription.is_primary == True
                )
                .values(is_primary=False)
            )

            # Set this transcription as primary
            transcription.is_primary = True
            await db.flush()
            await db.refresh(transcription)

            logger.info(
                f"Transcription set as primary",
                transcription_id=str(transcription_id),
                entry_id=str(transcription.entry_id)
            )

            return transcription

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to set primary transcription",
                transcription_id=str(transcription_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set primary transcription"
            )


# Global database service instance
db_service = DatabaseService()
