"""
Entries endpoint for retrieving voice entry metadata.
"""
from uuid import UUID
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.voice_entry import (
    VoiceEntryResponse,
    VoiceEntryListResponse,
    VoiceEntrySummary,
    TranscriptionSummary,
    CleanedEntrySummary
)
from app.schemas.transcription import TranscriptionResponse
from app.services.database import db_service
from app.middleware.jwt import get_current_user
from app.utils.logger import get_logger

logger = get_logger("entries")
router = APIRouter()


@router.get(
    "/entries",
    response_model=VoiceEntryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List voice entries",
    description="Retrieve paginated list of voice entries for authenticated user, ordered by newest first",
    responses={
        200: {"description": "Entries retrieved successfully"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Server error"}
    }
)
async def list_entries(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    entry_type: Annotated[Optional[str], Query(description="Filter by entry type (dream, journal, meeting, note)")] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VoiceEntryListResponse:
    """
    Get paginated list of voice entries for authenticated user.

    Returns entries ordered by uploaded_at DESC (newest first).
    Includes metadata for transcriptions and cleaned entries, but excludes text content.

    Args:
        limit: Maximum entries to return (1-100, default 20)
        offset: Number of entries to skip (default 0)
        entry_type: Optional filter by entry type
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        VoiceEntryListResponse with entries list and pagination metadata
    """
    logger.info(
        f"List entries requested",
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
        entry_type=entry_type
    )

    # Get entries with eager-loaded relationships
    entries = await db_service.get_entries_by_user(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        entry_type=entry_type
    )

    # Get total count for pagination
    total = await db_service.count_entries_by_user(
        db=db,
        user_id=current_user.id,
        entry_type=entry_type
    )

    # Build response with summary data
    entry_summaries = []
    for entry in entries:
        # Get primary transcription (is_primary=True)
        primary_trans = None
        for trans in entry.transcriptions:
            if trans.is_primary:
                primary_trans = TranscriptionSummary(
                    id=trans.id,
                    status=trans.status,
                    language_code=trans.language_code,
                    error_message=trans.error_message,
                    created_at=trans.created_at
                )
                break

        # Get latest cleaned entry (most recent by created_at)
        latest_cleaned = None
        if entry.cleaned_entries:
            # Sort by created_at descending and take first
            sorted_cleaned = sorted(entry.cleaned_entries, key=lambda c: c.created_at, reverse=True)
            latest = sorted_cleaned[0]

            # Create text preview (first 200 chars)
            text_preview = None
            if latest.cleaned_text:
                text_preview = latest.cleaned_text[:200]

            latest_cleaned = CleanedEntrySummary(
                id=latest.id,
                status=latest.status.value,  # Convert enum to string
                cleaned_text_preview=text_preview,
                analysis=latest.analysis,
                error_message=latest.error_message,
                created_at=latest.created_at
            )

        entry_summaries.append(
            VoiceEntrySummary(
                id=entry.id,
                original_filename=entry.original_filename,
                saved_filename=entry.saved_filename,
                file_path=entry.file_path,
                entry_type=entry.entry_type,
                duration_seconds=entry.duration_seconds,
                uploaded_at=entry.uploaded_at,
                primary_transcription=primary_trans,
                latest_cleaned_entry=latest_cleaned
            )
        )

    logger.info(
        f"Returning entries list",
        user_id=str(current_user.id),
        count=len(entry_summaries),
        total=total
    )

    return VoiceEntryListResponse(
        entries=entry_summaries,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/entries/{entry_id}",
    response_model=VoiceEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get voice entry",
    description="Retrieve metadata for a specific voice entry by ID",
    responses={
        200: {"description": "Entry found"},
        404: {"description": "Entry not found"},
        500: {"description": "Server error"}
    }
)
async def get_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VoiceEntryResponse:
    """
    Get voice entry by ID (user can only access their own entries).

    Args:
        entry_id: UUID of the entry to retrieve
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        VoiceEntryResponse with entry metadata

    Raises:
        HTTPException: 404 if entry not found or doesn't belong to user
    """
    logger.info(f"Entry retrieval requested", entry_id=str(entry_id), user_id=str(current_user.id))

    # Retrieve entry from database (filtered by user_id)
    entry = await db_service.get_entry_by_id(db, entry_id, current_user.id)

    if not entry:
        logger.warning(f"Entry not found", entry_id=str(entry_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry with ID {entry_id} not found"
        )

    # Get primary transcription if available
    primary_transcription = await db_service.get_primary_transcription(db, entry_id)
    primary_transcription_data = None

    if primary_transcription:
        primary_transcription_data = TranscriptionResponse.model_validate(primary_transcription)
        logger.info(
            f"Entry retrieved with primary transcription",
            entry_id=str(entry_id),
            transcription_id=str(primary_transcription.id)
        )
    else:
        logger.info(f"Entry retrieved without transcription", entry_id=str(entry_id))

    return VoiceEntryResponse(
        id=entry.id,
        original_filename=entry.original_filename,
        saved_filename=entry.saved_filename,
        file_path=entry.file_path,
        entry_type=entry.entry_type,
        uploaded_at=entry.uploaded_at,
        primary_transcription=primary_transcription_data
    )
