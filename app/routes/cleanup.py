"""
API routes for LLM cleanup operations.
"""
import logging
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.jwt import get_current_user
from app.models.user import User
from app.models.cleaned_entry import CleanupStatus
from app.schemas.cleanup import (
    CleanupTriggerRequest,
    CleanupResponse,
    CleanedEntryDetail
)
from app.services.database import db_service
from app.services.llm_cleanup import LLMCleanupService
from app.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


async def process_cleanup_background(
    cleaned_entry_id: UUID,
    transcription_text: str,
    entry_type: str
):
    """
    Background task to process LLM cleanup.

    Args:
        cleaned_entry_id: UUID of the cleaned entry to update
        transcription_text: Raw transcription text to clean
        entry_type: Type of entry (dream, journal, etc.)
    """
    from app.database import get_session

    llm_service = LLMCleanupService()

    async with get_session() as db:
        try:
            # Update status to processing
            await db_service.update_cleaned_entry_processing(
                db=db,
                cleaned_entry_id=cleaned_entry_id,
                cleanup_status=CleanupStatus.PROCESSING
            )
            await db.commit()

            logger.info(f"Starting LLM cleanup for entry {cleaned_entry_id}")

            # Call LLM service
            result = await llm_service.cleanup_transcription(
                transcription_text=transcription_text,
                entry_type=entry_type
            )

            # Update with results
            await db_service.update_cleaned_entry_processing(
                db=db,
                cleaned_entry_id=cleaned_entry_id,
                cleanup_status=CleanupStatus.COMPLETED,
                cleaned_text=result["cleaned_text"],
                analysis=result["analysis"]
            )
            await db.commit()

            logger.info(f"LLM cleanup completed for entry {cleaned_entry_id}")

        except Exception as e:
            logger.error(
                f"LLM cleanup failed for entry {cleaned_entry_id}: {str(e)}",
                exc_info=True
            )
            # Update status to failed
            try:
                await db_service.update_cleaned_entry_processing(
                    db=db,
                    cleaned_entry_id=cleaned_entry_id,
                    cleanup_status=CleanupStatus.FAILED,
                    error_message=str(e)
                )
                await db.commit()
            except Exception as update_error:
                logger.error(
                    f"Failed to update cleanup entry status: {str(update_error)}"
                )


@router.post(
    "/transcriptions/{transcription_id}/cleanup",
    response_model=CleanupResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger LLM cleanup for a transcription",
    description="Start background processing to clean and analyze a transcription using LLM"
)
async def trigger_cleanup(
    transcription_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    request: CleanupTriggerRequest = CleanupTriggerRequest()
):
    """
    Trigger LLM cleanup for a completed transcription.

    The cleanup process:
    1. Validates that the transcription exists and is completed
    2. Creates a cleaned_entry record
    3. Starts background processing using the configured LLM model
    4. Returns immediately with cleanup ID and status

    Query the cleanup status using GET /api/v1/cleaned-entries/{cleanup_id}
    """
    # Get the transcription
    transcription = await db_service.get_transcription_by_id(
        db=db,
        transcription_id=transcription_id
    )

    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )

    # Verify transcription is completed
    if transcription.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transcription must be completed before cleanup. Current status: {transcription.status}"
        )

    # Verify there's text to clean
    if not transcription.transcribed_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcription has no text to clean"
        )

    # Get the voice entry to determine entry_type
    voice_entry = await db_service.get_entry_by_id(
        db=db,
        entry_id=transcription.entry_id,
        user_id=current_user.id
    )

    if not voice_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice entry not found"
        )

    # Create cleaned entry record
    cleaned_entry = await db_service.create_cleaned_entry(
        db=db,
        voice_entry_id=voice_entry.id,
        transcription_id=transcription_id,
        user_id=current_user.id,
        model_name=settings.OLLAMA_MODEL,
        prompt_used=f"{voice_entry.entry_type}_cleanup"
    )

    await db.commit()

    # Start background processing
    background_tasks.add_task(
        process_cleanup_background,
        cleaned_entry_id=cleaned_entry.id,
        transcription_text=transcription.transcribed_text,
        entry_type=voice_entry.entry_type
    )

    logger.info(
        f"Cleanup triggered for transcription {transcription_id}, "
        f"cleanup_id={cleaned_entry.id}"
    )

    return CleanupResponse(
        id=cleaned_entry.id,
        voice_entry_id=voice_entry.id,
        transcription_id=transcription_id,
        status=cleaned_entry.status,
        model_name=cleaned_entry.model_name,
        created_at=cleaned_entry.created_at,
        message="Cleanup processing started in background"
    )


@router.get(
    "/cleaned-entries/{cleaned_entry_id}",
    response_model=CleanedEntryDetail,
    summary="Get cleaned entry details",
    description="Retrieve complete details of a cleaned entry including status and results"
)
async def get_cleaned_entry(
    cleaned_entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a cleaned entry.

    Returns:
    - Cleanup status (pending, processing, completed, failed)
    - Cleaned text (when completed)
    - Analysis data (themes, emotions, characters, locations)
    - Processing time and error details (if applicable)
    """
    cleaned_entry = await db_service.get_cleaned_entry_by_id(
        db=db,
        cleaned_entry_id=cleaned_entry_id,
        user_id=current_user.id
    )

    if not cleaned_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cleaned entry not found"
        )

    return CleanedEntryDetail(
        id=cleaned_entry.id,
        voice_entry_id=cleaned_entry.voice_entry_id,
        transcription_id=cleaned_entry.transcription_id,
        user_id=cleaned_entry.user_id,
        cleaned_text=cleaned_entry.cleaned_text,
        analysis=cleaned_entry.analysis,
        status=cleaned_entry.status,
        model_name=cleaned_entry.model_name,
        error_message=cleaned_entry.error_message,
        processing_time_seconds=cleaned_entry.processing_time_seconds,
        created_at=cleaned_entry.created_at,
        processing_started_at=cleaned_entry.processing_started_at,
        processing_completed_at=cleaned_entry.processing_completed_at
    )


@router.get(
    "/entries/{entry_id}/cleaned",
    response_model=list[CleanedEntryDetail],
    summary="Get all cleaned entries for a voice entry",
    description="Retrieve all cleanup attempts/versions for a specific voice entry"
)
async def get_cleaned_entries_by_entry(
    entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get all cleaned entries associated with a voice entry.

    Useful for:
    - Viewing multiple cleanup attempts
    - Comparing different LLM models
    - Accessing historical cleanup versions
    """
    # Verify voice entry exists and belongs to user
    voice_entry = await db_service.get_entry_by_id(
        db=db,
        entry_id=entry_id,
        user_id=current_user.id
    )

    if not voice_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice entry not found"
        )

    # Get all cleaned entries
    cleaned_entries = await db_service.get_cleaned_entries_by_voice_entry(
        db=db,
        voice_entry_id=entry_id,
        user_id=current_user.id
    )

    return [
        CleanedEntryDetail(
            id=ce.id,
            voice_entry_id=ce.voice_entry_id,
            transcription_id=ce.transcription_id,
            user_id=ce.user_id,
            cleaned_text=ce.cleaned_text,
            analysis=ce.analysis,
            status=ce.status,
            model_name=ce.model_name,
            error_message=ce.error_message,
            processing_time_seconds=ce.processing_time_seconds,
            created_at=ce.created_at,
            processing_started_at=ce.processing_started_at,
            processing_completed_at=ce.processing_completed_at
        )
        for ce in cleaned_entries
    ]
