"""
Database service for CRUD operations on voice entries and transcriptions.
"""
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import User
from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.cleaned_entry import CleanedEntry, CleanupStatus
from app.models.prompt_template import PromptTemplate
from app.models.notion_sync import NotionSync, SyncStatus
from app.models.user_preference import UserPreference
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
                duration_seconds=entry_data.duration_seconds,
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
        entry_id: UUID,
        user_id: UUID
    ) -> Optional[str]:
        """
        Delete a voice entry by ID with user ownership verification.
        Cascades to all child records (transcriptions, cleaned_entries, notion_syncs).

        Args:
            db: Database session
            entry_id: UUID of the entry to delete
            user_id: UUID of the user (for ownership verification)

        Returns:
            File path to delete if entry found and deleted, None if not found

        Raises:
            HTTPException: If database operation fails
        """
        try:
            entry = await self.get_entry_by_id(db, entry_id, user_id)

            if not entry:
                return None

            file_path = entry.file_path
            await db.delete(entry)
            await db.flush()

            logger.info(
                f"Entry deleted from database",
                entry_id=str(entry_id),
                user_id=str(user_id),
                file_path=file_path
            )
            return file_path

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

    async def get_entries_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        entry_type: Optional[str] = None
    ) -> list[VoiceEntry]:
        """
        Get paginated list of voice entries for a user.

        Uses eager loading (selectinload) to avoid N+1 queries when fetching
        related transcriptions and cleaned_entries.

        Args:
            db: Database session
            user_id: UUID of the user
            limit: Maximum number of entries to return (default: 20, max: 100)
            offset: Number of entries to skip (default: 0)
            entry_type: Optional filter by entry type (dream, journal, etc.)

        Returns:
            List of VoiceEntry instances with eager-loaded relationships
        """
        try:
            # Build query with eager loading
            query = (
                select(VoiceEntry)
                .where(VoiceEntry.user_id == user_id)
                .options(
                    selectinload(VoiceEntry.transcriptions),
                    selectinload(VoiceEntry.cleaned_entries)
                )
                .order_by(VoiceEntry.uploaded_at.desc())
            )

            # Add optional entry_type filter
            if entry_type:
                query = query.where(VoiceEntry.entry_type == entry_type)

            # Add pagination
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            entries = list(result.scalars().all())

            logger.info(
                f"Retrieved voice entries for user",
                user_id=str(user_id),
                count=len(entries),
                limit=limit,
                offset=offset,
                entry_type=entry_type
            )

            return entries

        except Exception as e:
            logger.error(
                f"Failed to retrieve entries for user",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve entries"
            )

    async def count_entries_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_type: Optional[str] = None
    ) -> int:
        """
        Count total number of voice entries for a user.

        Args:
            db: Database session
            user_id: UUID of the user
            entry_type: Optional filter by entry type (dream, journal, etc.)

        Returns:
            Total count of entries
        """
        try:
            query = (
                select(func.count())
                .select_from(VoiceEntry)
                .where(VoiceEntry.user_id == user_id)
            )

            # Add optional entry_type filter
            if entry_type:
                query = query.where(VoiceEntry.entry_type == entry_type)

            result = await db.execute(query)
            count = result.scalar() or 0

            logger.info(
                f"Counted voice entries for user",
                user_id=str(user_id),
                count=count,
                entry_type=entry_type
            )

            return count

        except Exception as e:
            logger.error(
                f"Failed to count entries for user",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to count entries"
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
                is_primary=transcription_data.is_primary,
                beam_size=transcription_data.beam_size,
                temperature=transcription_data.temperature
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

    async def delete_transcription(
        self,
        db: AsyncSession,
        transcription_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a transcription by ID with user ownership verification.
        Validates that user owns the parent voice entry.
        Prevents deletion if this is the only/last primary transcription.

        Args:
            db: Database session
            transcription_id: UUID of the transcription to delete
            user_id: UUID of the user (for ownership verification)

        Returns:
            True if deleted, False if not found

        Raises:
            HTTPException: If validation fails or database operation fails
        """
        try:
            # Get transcription with entry relationship
            result = await db.execute(
                select(Transcription)
                .options(selectinload(Transcription.entry))
                .where(Transcription.id == transcription_id)
            )
            transcription = result.scalar_one_or_none()

            if not transcription:
                return False

            # Verify user owns the parent voice entry
            if transcription.entry.user_id != user_id:
                logger.warning(
                    f"User attempted to delete transcription they don't own",
                    user_id=str(user_id),
                    transcription_id=str(transcription_id),
                    entry_owner=str(transcription.entry.user_id)
                )
                return False

            # Check if this is the only transcription for the entry
            other_transcriptions = await db.execute(
                select(Transcription)
                .where(
                    Transcription.entry_id == transcription.entry_id,
                    Transcription.id != transcription_id
                )
            )
            if not other_transcriptions.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot delete the only transcription for this entry"
                )

            await db.delete(transcription)
            await db.flush()

            logger.info(
                f"Transcription deleted",
                transcription_id=str(transcription_id),
                user_id=str(user_id),
                entry_id=str(transcription.entry_id)
            )
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to delete transcription",
                transcription_id=str(transcription_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete transcription from database"
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
        error_message: Optional[str] = None,
        beam_size: Optional[int] = None
    ) -> Optional[Transcription]:
        """
        Update transcription status and related fields.

        Args:
            db: Database session
            transcription_id: UUID of the transcription
            status: New status value
            transcribed_text: Optional transcribed text
            error_message: Optional error message
            beam_size: Optional beam size used for transcription

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
                # beam_size and temperature are set at creation time and are immutable

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

    # ===== Cleaned Entry / Cleanup Methods =====

    async def get_primary_cleanup_for_voice_entry(
        self,
        db: AsyncSession,
        voice_entry_id: UUID
    ) -> Optional[CleanedEntry]:
        """
        Get the primary cleanup for a voice entry.

        Args:
            db: Database session
            voice_entry_id: UUID of the voice entry

        Returns:
            CleanedEntry instance if found, None otherwise

        Raises:
            HTTPException: If database operation fails
        """
        try:
            result = await db.execute(
                select(CleanedEntry)
                .where(
                    CleanedEntry.voice_entry_id == voice_entry_id,
                    CleanedEntry.is_primary == True
                )
            )
            cleanup = result.scalars().first()

            if cleanup:
                logger.debug(
                    f"Primary cleanup found",
                    cleanup_id=str(cleanup.id),
                    voice_entry_id=str(voice_entry_id)
                )
            else:
                logger.debug(
                    f"No primary cleanup found for voice entry",
                    voice_entry_id=str(voice_entry_id)
                )

            return cleanup

        except Exception as e:
            logger.error(
                f"Failed to retrieve primary cleanup",
                voice_entry_id=str(voice_entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve primary cleanup"
            )

    async def set_primary_cleanup(
        self,
        db: AsyncSession,
        cleanup_id: UUID
    ) -> Optional[CleanedEntry]:
        """
        Set a cleanup as primary for its voice entry.
        Unsets any existing primary cleanup for the same voice entry.

        Args:
            db: Database session
            cleanup_id: UUID of the cleanup to set as primary

        Returns:
            Updated CleanedEntry instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            # Get cleanup by ID
            result = await db.execute(
                select(CleanedEntry).where(CleanedEntry.id == cleanup_id)
            )
            cleanup = result.scalars().first()

            if not cleanup:
                logger.warning(f"Cleanup not found", cleanup_id=str(cleanup_id))
                return None

            # Unset any existing primary cleanup for this voice entry
            await db.execute(
                update(CleanedEntry)
                .where(
                    CleanedEntry.voice_entry_id == cleanup.voice_entry_id,
                    CleanedEntry.is_primary == True
                )
                .values(is_primary=False)
            )

            # Set this cleanup as primary
            cleanup.is_primary = True
            await db.flush()
            await db.refresh(cleanup)

            logger.info(
                f"Cleanup set as primary",
                cleanup_id=str(cleanup_id),
                voice_entry_id=str(cleanup.voice_entry_id)
            )

            return cleanup

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to set primary cleanup",
                cleanup_id=str(cleanup_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set primary cleanup"
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
    # User Preferences Operations
    # ==========================================

    async def get_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[UserPreference]:
        """
        Get user preferences by user ID.
        If preferences don't exist, creates default preferences.

        Args:
            db: Database session
            user_id: User's UUID

        Returns:
            UserPreference instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            result = await db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            preferences = result.scalar_one_or_none()

            # Create default preferences if they don't exist
            if not preferences:
                logger.info(f"Creating default preferences for user", user_id=str(user_id))
                preferences = UserPreference(
                    user_id=user_id,
                    preferred_transcription_language="auto"
                )
                db.add(preferences)
                await db.flush()
                await db.refresh(preferences)

            return preferences

        except Exception as e:
            logger.error(
                f"Failed to get user preferences",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user preferences"
            )

    async def update_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        preferred_transcription_language: Optional[str] = None
    ) -> UserPreference:
        """
        Update user preferences.

        Args:
            db: Database session
            user_id: User's UUID
            preferred_transcription_language: Language code for transcription

        Returns:
            Updated UserPreference instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            # Get or create preferences
            preferences = await self.get_user_preferences(db, user_id)

            # Update fields if provided
            if preferred_transcription_language is not None:
                preferences.preferred_transcription_language = preferred_transcription_language

            # Update timestamp
            preferences.updated_at = datetime.now(timezone.utc)

            await db.flush()
            await db.refresh(preferences)

            logger.info(
                f"User preferences updated",
                user_id=str(user_id),
                language=preferred_transcription_language
            )

            return preferences

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update user preferences",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user preferences"
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
        model_name: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
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
                status=CleanupStatus.PENDING,
                temperature=temperature,
                top_p=top_p
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
            query = query.options(selectinload(CleanedEntry.prompt_template))

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

    async def delete_cleaned_entry(
        self,
        db: AsyncSession,
        cleaned_entry_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a cleaned entry by ID with user ownership verification.

        Args:
            db: Database session
            cleaned_entry_id: UUID of the cleaned entry to delete
            user_id: UUID of the user (for ownership verification)

        Returns:
            True if deleted, False if not found or user doesn't own it

        Raises:
            HTTPException: If database operation fails
        """
        try:
            cleaned_entry = await self.get_cleaned_entry_by_id(db, cleaned_entry_id, user_id)

            if not cleaned_entry:
                return False

            await db.delete(cleaned_entry)
            await db.flush()

            logger.info(
                f"Cleaned entry deleted",
                cleaned_entry_id=str(cleaned_entry_id),
                user_id=str(user_id),
                voice_entry_id=str(cleaned_entry.voice_entry_id)
            )
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to delete cleaned entry",
                cleaned_entry_id=str(cleaned_entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete cleaned entry from database"
            )

    async def update_cleaned_entry_processing(
        self,
        db: AsyncSession,
        cleaned_entry_id: UUID,
        cleanup_status: CleanupStatus,
        cleaned_text: Optional[str] = None,
        analysis: Optional[dict] = None,
        error_message: Optional[str] = None,
        prompt_template_id: Optional[int] = None,
        llm_raw_response: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
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
            llm_raw_response: Raw LLM response before parsing (optional)
            temperature: Temperature used for LLM (optional)
            top_p: Top-p value used for LLM (optional)

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
            if llm_raw_response is not None:
                cleaned_entry.llm_raw_response = llm_raw_response
            # temperature and top_p are set at creation time and are immutable

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

    async def get_latest_cleaned_entry(
        self,
        db: AsyncSession,
        voice_entry_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[CleanedEntry]:
        """
        Get the latest (most recent) cleaned entry for a voice entry.

        Args:
            db: Database session
            voice_entry_id: Voice entry UUID
            user_id: Optional UUID to filter by user ownership

        Returns:
            Latest CleanedEntry instance or None if none exist
        """
        try:
            query = select(CleanedEntry).where(
                CleanedEntry.voice_entry_id == voice_entry_id
            )

            if user_id is not None:
                query = query.where(CleanedEntry.user_id == user_id)

            query = query.order_by(CleanedEntry.created_at.desc()).limit(1)

            result = await db.execute(query)
            cleaned_entry = result.scalar_one_or_none()

            if cleaned_entry:
                logger.info(
                    "Latest cleaned entry retrieved",
                    voice_entry_id=voice_entry_id,
                    cleaned_entry_id=cleaned_entry.id
                )
            else:
                logger.info(
                    "No cleaned entry found",
                    voice_entry_id=voice_entry_id
                )

            return cleaned_entry

        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving latest cleaned entry: {str(e)}",
                voice_entry_id=voice_entry_id,
                exc_info=True
            )
            raise

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
            query = query.options(selectinload(CleanedEntry.prompt_template))

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

    # Notion Sync Methods

    async def get_latest_completed_sync(
        self,
        db: AsyncSession,
        entry_id: UUID,
        user_id: UUID
    ) -> Optional[NotionSync]:
        """
        Get the most recent successfully completed Notion sync for an entry.

        Args:
            db: Database session
            entry_id: Voice entry ID
            user_id: User ID (for ownership verification)

        Returns:
            Most recent completed NotionSync instance or None

        Raises:
            HTTPException: If database operation fails
        """
        try:
            query = (
                select(NotionSync)
                .where(
                    NotionSync.entry_id == entry_id,
                    NotionSync.user_id == user_id,
                    NotionSync.status == SyncStatus.COMPLETED
                )
                .order_by(NotionSync.created_at.desc())
                .limit(1)
            )
            result = await db.execute(query)
            sync_record = result.scalar_one_or_none()

            if sync_record:
                logger.debug(
                    "Latest completed sync found",
                    sync_id=str(sync_record.id),
                    entry_id=str(entry_id),
                    notion_page_id=sync_record.notion_page_id
                )

            return sync_record

        except Exception as e:
            logger.error(
                "Failed to get latest completed sync",
                entry_id=str(entry_id),
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve sync record"
            )

    async def get_in_progress_sync(
        self,
        db: AsyncSession,
        entry_id: UUID,
        user_id: UUID
    ) -> Optional[NotionSync]:
        """
        Get any in-progress sync for an entry (PENDING or PROCESSING).

        Args:
            db: Database session
            entry_id: Voice entry ID
            user_id: User ID (for ownership verification)

        Returns:
            In-progress NotionSync instance or None

        Raises:
            HTTPException: If database operation fails
        """
        try:
            query = (
                select(NotionSync)
                .where(
                    NotionSync.entry_id == entry_id,
                    NotionSync.user_id == user_id,
                    NotionSync.status.in_([SyncStatus.PENDING, SyncStatus.PROCESSING])
                )
            )
            result = await db.execute(query)
            sync_record = result.scalar_one_or_none()

            if sync_record:
                logger.debug(
                    "In-progress sync found",
                    sync_id=str(sync_record.id),
                    entry_id=str(entry_id),
                    status=sync_record.status.value
                )

            return sync_record

        except Exception as e:
            logger.error(
                "Failed to get in-progress sync",
                entry_id=str(entry_id),
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve sync record"
            )

    async def create_notion_sync(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
        notion_database_id: str,
        status: SyncStatus = SyncStatus.PENDING
    ) -> NotionSync:
        """
        Create a new Notion sync record.

        Args:
            db: Database session
            user_id: User ID
            entry_id: Voice entry ID to sync
            notion_database_id: Target Notion database ID
            status: Initial sync status (default: PENDING)

        Returns:
            Created NotionSync instance

        Raises:
            HTTPException: If database operation fails
        """
        try:
            sync_record = NotionSync(
                user_id=user_id,
                entry_id=entry_id,
                notion_database_id=notion_database_id,
                status=status,
                retry_count=0
            )

            db.add(sync_record)
            await db.flush()

            logger.info(
                "Created Notion sync record",
                sync_id=str(sync_record.id),
                entry_id=str(entry_id),
                status=status.value
            )

            return sync_record

        except Exception as e:
            logger.error(
                "Failed to create Notion sync record",
                user_id=str(user_id),
                entry_id=str(entry_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create sync record"
            )

    async def get_notion_sync_by_id(
        self,
        db: AsyncSession,
        sync_id: UUID
    ) -> Optional[NotionSync]:
        """
        Get a Notion sync record by ID.

        Args:
            db: Database session
            sync_id: Sync record ID

        Returns:
            NotionSync instance or None if not found

        Raises:
            HTTPException: If database operation fails
        """
        try:
            query = select(NotionSync).where(NotionSync.id == sync_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                "Failed to get Notion sync by ID",
                sync_id=str(sync_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve sync record"
            )

    async def get_notion_syncs_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[NotionSync]:
        """
        Get all Notion sync records for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of NotionSync instances

        Raises:
            HTTPException: If database operation fails
        """
        try:
            query = (
                select(NotionSync)
                .where(NotionSync.user_id == user_id)
                .order_by(NotionSync.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(
                "Failed to get Notion syncs by user",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve sync records"
            )

    async def count_notion_syncs_by_user(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> int:
        """
        Count total Notion sync records for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Total count of sync records

        Raises:
            HTTPException: If database operation fails
        """
        try:
            from sqlalchemy import func
            query = select(func.count()).select_from(NotionSync).where(NotionSync.user_id == user_id)
            result = await db.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error(
                "Failed to count Notion syncs",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to count sync records"
            )

    async def update_notion_sync_status(
        self,
        db: AsyncSession,
        sync_id: UUID,
        status: SyncStatus,
        notion_page_id: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
        cleaned_entry_id: Optional[UUID] = None
    ) -> NotionSync:
        """
        Update Notion sync record status.

        Args:
            db: Database session
            sync_id: Sync record ID
            status: New sync status
            notion_page_id: Notion page ID (if sync completed)
            error_message: Error message (if sync failed)
            retry_count: New retry count
            cleaned_entry_id: Cleaned entry ID used for sync

        Returns:
            Updated NotionSync instance

        Raises:
            HTTPException: If database operation fails or record not found
        """
        try:
            sync_record = await self.get_notion_sync_by_id(db, sync_id)
            if not sync_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sync record {sync_id} not found"
                )

            # Update fields
            sync_record.status = status

            if notion_page_id is not None:
                sync_record.notion_page_id = notion_page_id

            if error_message is not None:
                sync_record.error_message = error_message

            if retry_count is not None:
                sync_record.retry_count = retry_count

            if cleaned_entry_id is not None:
                sync_record.cleaned_entry_id = cleaned_entry_id

            # Update timestamps
            if status == SyncStatus.PROCESSING and not sync_record.sync_started_at:
                sync_record.sync_started_at = datetime.now(timezone.utc)

            if status == SyncStatus.COMPLETED:
                sync_record.sync_completed_at = datetime.now(timezone.utc)

            await db.flush()

            logger.info(
                "Updated Notion sync status",
                sync_id=str(sync_id),
                status=status.value,
                notion_page_id=notion_page_id
            )

            return sync_record

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to update Notion sync status",
                sync_id=str(sync_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update sync record"
            )

    # ==========================================
    # Prompt Template Operations
    # ==========================================

    async def activate_prompt_template(
        self,
        db: AsyncSession,
        template_id: int
    ) -> PromptTemplate:
        """
        Activate a prompt template and deactivate all others for the same entry_type.
        This ensures only one prompt is active per entry_type.

        Args:
            db: Database session
            template_id: ID of the prompt template to activate

        Returns:
            Activated PromptTemplate instance

        Raises:
            HTTPException: If template not found or update fails
        """
        try:
            # Get the template to activate
            result = await db.execute(
                select(PromptTemplate).where(PromptTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()

            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Prompt template {template_id} not found"
                )

            # Deactivate all other prompts for the same entry_type
            await db.execute(
                update(PromptTemplate)
                .where(
                    PromptTemplate.entry_type == template.entry_type,
                    PromptTemplate.id != template_id
                )
                .values(is_active=False)
            )

            # Activate the target template
            template.is_active = True
            template.updated_at = datetime.utcnow()
            await db.flush()
            await db.refresh(template)

            logger.info(
                f"Prompt template activated",
                template_id=template_id,
                entry_type=template.entry_type,
                template_name=template.name
            )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to activate prompt template",
                template_id=template_id,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate prompt template"
            )


# Global database service instance
db_service = DatabaseService()
