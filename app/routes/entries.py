"""
Entries endpoint for retrieving voice entry metadata.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.voice_entry import VoiceEntryResponse
from app.schemas.transcription import TranscriptionResponse
from app.services.database import db_service
from app.utils.logger import get_logger

logger = get_logger("entries")
router = APIRouter()


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
    db: AsyncSession = Depends(get_db)
) -> VoiceEntryResponse:
    """
    Get voice entry by ID.

    Args:
        entry_id: UUID of the entry to retrieve
        db: Database session

    Returns:
        VoiceEntryResponse with entry metadata

    Raises:
        HTTPException: 404 if entry not found
    """
    logger.info(f"Entry retrieval requested", entry_id=str(entry_id))

    # Retrieve entry from database
    entry = await db_service.get_entry_by_id(db, entry_id)

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
