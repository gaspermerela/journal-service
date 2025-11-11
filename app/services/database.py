"""
Database service for CRUD operations on voice entries and transcriptions.
"""
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.user import User
from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.cleaned_entry import CleanedEntry, CleanupStatus
from app.schemas.auth import UserCreate
from app.schemas.voice_entry import VoiceEntryCreate
from app.schemas.transcription import TranscriptionCreate
from app.utils.logger import get_logger
from app.utils.security import hash_password

logger = get_logger("database_service")


class DatabaseService:
    """Service for database operations on voice entries."""

    async def create_entry(
        self,
        db: AsyncSession,
        entry_data: VoiceEntryCreate
    ) -> VoiceEntry:
        """
        Create a new voice entry in the database.

        Args:
            db: Database session
            entry_data: Entry data to create

        Returns:
            Created VoiceEntry instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            entry = VoiceEntry(
                original_filename=entry_data.original_filename,
                saved_filename=entry_data.saved_filename,
                file_path=entry_data.file_path,
                entry_type=entry_data.entry_type,
                uploaded_at=entry_data.uploaded_at,
                user_id=entry_data.user_id
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
        entry_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[VoiceEntry]:
        """
        Retrieve a voice entry by ID, optionally filtered by user_id.

        Args:
            db: Database session
            entry_id: UUID of the entry to retrieve
            user_id: Optional UUID to filter by user ownership

        Returns:
            VoiceEntry if found, None otherwise
        """
        try:
            query = select(VoiceEntry).where(VoiceEntry.id == entry_id)

            # Add user_id filter if provided
            if user_id is not None:
                query = query.where(VoiceEntry.user_id == user_id)

            result = await db.execute(query)
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
        Delete a voice entry by ID.

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
        entry_id: UUID,
        user_id: Optional[UUID] = None
    ) -> list[Transcription]:
        """
        Get all transcriptions for a specific voice entry, with optional user verification.

        Args:
            db: Database session
            entry_id: UUID of the entry
            user_id: Optional UUID to verify entry ownership before retrieving transcriptions

        Returns:
            List of Transcription objects (empty list if entry not found or user doesn't own it)
        """
        try:
            # If user_id provided, first verify the entry belongs to the user
            if user_id is not None:
                entry = await self.get_entry_by_id(db, entry_id, user_id)
                if not entry:
                    logger.warning(
                        f"Entry not found or user doesn't have access",
                        entry_id=str(entry_id),
                        user_id=str(user_id)
                    )
                    return []

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

    # ===== User Management Methods =====

    async def create_user(
        self,
        db: AsyncSession,
        user_data: UserCreate
    ) -> User:
        """
        Create a new user in the database.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created User instance

        Raises:
            HTTPException: If user already exists or database operation fails
        """
        try:
            # Check if user with this email already exists
            existing_user = await self.get_user_by_email(db, user_data.email)
            if existing_user:
                logger.warning(f"User registration failed - email already exists", email=user_data.email)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Create new user with hashed password
            user = User(
                email=user_data.email,
                hashed_password=hash_password(user_data.password),
                is_active=True
            )

            db.add(user)
            await db.flush()
            await db.refresh(user)

            logger.info(f"User created successfully", user_id=str(user.id), email=user.email)

            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to create user",
                email=user_data.email,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """
        Get a user by email address.

        Args:
            db: Database session
            email: User's email address

        Returns:
            User instance if found, None otherwise

        Raises:
            HTTPException: If database operation fails
        """
        try:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if user:
                logger.debug(f"User found by email", email=email, user_id=str(user.id))
            else:
                logger.debug(f"User not found by email", email=email)

            return user

        except Exception as e:
            logger.error(
                f"Failed to get user by email",
                email=email,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user"
            )

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            db: Database session
            user_id: User's UUID

        Returns:
            User instance if found, None otherwise

        Raises:
            HTTPException: If database operation fails
        """
        try:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                logger.debug(f"User found by ID", user_id=str(user_id))
            else:
                logger.debug(f"User not found by ID", user_id=str(user_id))

            return user

        except Exception as e:
            logger.error(
                f"Failed to get user by ID",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user"
            )

    # ==========================================
    # Cleaned Entry Operations
    # ==========================================

    async def create_cleaned_entry(
        self,
        db: AsyncSession,
        voice_entry_id: UUID,
        transcription_id: UUID,
        user_id: UUID,
        model_name: str
    ) -> CleanedEntry:
        """
        Create a new cleaned entry record.

        Args:
            db: Database session
            voice_entry_id: Voice entry UUID
            transcription_id: Transcription UUID
            user_id: User UUID
            model_name: LLM model name used

        Returns:
            Created CleanedEntry instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            cleaned_entry = CleanedEntry(
                voice_entry_id=voice_entry_id,
                transcription_id=transcription_id,
                user_id=user_id,
                model_name=model_name,
                status=CleanupStatus.PENDING
            )

            db.add(cleaned_entry)
            await db.flush()
            await db.refresh(cleaned_entry)

            logger.info(
                f"Cleaned entry created",
                cleaned_entry_id=str(cleaned_entry.id),
                transcription_id=str(transcription_id)
            )

            return cleaned_entry

        except Exception as e:
            logger.error(
                f"Failed to create cleaned entry",
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create cleaned entry record"
            )

    async def get_cleaned_entry_by_id(
        self,
        db: AsyncSession,
        cleaned_entry_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[CleanedEntry]:
        """
        Retrieve a cleaned entry by ID, optionally filtered by user_id.

        Args:
            db: Database session
            cleaned_entry_id: UUID of the cleaned entry
            user_id: Optional UUID to filter by user ownership

        Returns:
            CleanedEntry if found, None otherwise
        """
        try:
            query = select(CleanedEntry).where(CleanedEntry.id == cleaned_entry_id)

            if user_id is not None:
                query = query.where(CleanedEntry.user_id == user_id)

            result = await db.execute(query)
            cleaned_entry = result.scalar_one_or_none()

            if cleaned_entry:
                logger.debug(
                    f"Cleaned entry found",
                    cleaned_entry_id=str(cleaned_entry_id)
                )
            else:
                logger.debug(
                    f"Cleaned entry not found",
                    cleaned_entry_id=str(cleaned_entry_id)
                )

            return cleaned_entry

        except Exception as e:
            logger.error(
                f"Failed to get cleaned entry",
                cleaned_entry_id=str(cleaned_entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve cleaned entry"
            )

    async def update_cleaned_entry_processing(
        self,
        db: AsyncSession,
        cleaned_entry_id: UUID,
        cleanup_status: CleanupStatus,
        cleaned_text: Optional[str] = None,
        analysis: Optional[dict] = None,
        error_message: Optional[str] = None,
        prompt_template_id: Optional[int] = None
    ) -> CleanedEntry:
        """
        Update cleaned entry with processing results.

        Args:
            db: Database session
            cleaned_entry_id: UUID of the cleaned entry
            cleanup_status: New cleanup status
            cleaned_text: Cleaned text result
            analysis: Analysis data dict
            error_message: Error message if failed
            prompt_template_id: ID of prompt template used (optional)

        Returns:
            Updated CleanedEntry instance

        Raises:
            HTTPException: If entry not found or update fails
        """
        try:
            cleaned_entry = await self.get_cleaned_entry_by_id(db, cleaned_entry_id)

            if not cleaned_entry:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cleaned entry not found"
                )

            # Update fields
            cleaned_entry.status = cleanup_status
            if cleaned_text is not None:
                cleaned_entry.cleaned_text = cleaned_text
            if analysis is not None:
                cleaned_entry.analysis = analysis
            if error_message is not None:
                cleaned_entry.error_message = error_message
            if prompt_template_id is not None:
                cleaned_entry.prompt_template_id = prompt_template_id

            # Update timestamps based on status (use timezone-naive datetime)
            if cleanup_status == CleanupStatus.PROCESSING and not cleaned_entry.processing_started_at:
                cleaned_entry.processing_started_at = datetime.utcnow()
            elif cleanup_status in [CleanupStatus.COMPLETED, CleanupStatus.FAILED]:
                cleaned_entry.processing_completed_at = datetime.utcnow()

            await db.flush()
            await db.refresh(cleaned_entry)

            logger.info(
                f"Cleaned entry updated",
                cleaned_entry_id=str(cleaned_entry_id),
                status=cleanup_status.value
            )

            return cleaned_entry

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update cleaned entry",
                cleaned_entry_id=str(cleaned_entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update cleaned entry"
            )

    async def get_cleaned_entries_by_voice_entry(
        self,
        db: AsyncSession,
        voice_entry_id: UUID,
        user_id: Optional[UUID] = None
    ) -> list[CleanedEntry]:
        """
        Get all cleaned entries for a voice entry.

        Args:
            db: Database session
            voice_entry_id: Voice entry UUID
            user_id: Optional UUID to filter by user ownership

        Returns:
            List of CleanedEntry instances
        """
        try:
            query = select(CleanedEntry).where(
                CleanedEntry.voice_entry_id == voice_entry_id
            )

            if user_id is not None:
                query = query.where(CleanedEntry.user_id == user_id)

            query = query.order_by(CleanedEntry.created_at.desc())

            result = await db.execute(query)
            cleaned_entries = result.scalars().all()

            logger.debug(
                f"Found {len(cleaned_entries)} cleaned entries for voice entry",
                voice_entry_id=str(voice_entry_id)
            )

            return list(cleaned_entries)

        except Exception as e:
            logger.error(
                f"Failed to get cleaned entries by voice entry",
                voice_entry_id=str(voice_entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve cleaned entries"
            )


# Global database service instance
db_service = DatabaseService()
