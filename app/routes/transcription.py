"""
API routes for audio transcription operations.
"""
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.database import db_service
from app.services.transcription import TranscriptionService
from app.schemas.transcription import (
    TranscriptionTriggerRequest,
    TranscriptionTriggerResponse,
    TranscriptionResponse,
    TranscriptionListResponse,
    TranscriptionStatusResponse,
    TranscriptionCreate,
)
from app.utils.logger import get_logger

logger = get_logger("transcription_routes")

router = APIRouter()


def get_transcription_service(request: Request) -> TranscriptionService:
    """
    Dependency to get transcription service from app state.

    Args:
        request: FastAPI request object

    Returns:
        TranscriptionService instance

    Raises:
        HTTPException: If transcription service is not available
    """
    service = request.app.state.transcription_service

    if service is None:
        logger.error("Transcription service not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service is currently unavailable"
        )

    return service


async def process_transcription_task(
    transcription_id: UUID,
    entry_id: UUID,
    audio_file_path: str,
    language: str,
    transcription_service: TranscriptionService
):
    """
    Background task to process audio transcription.

    Args:
        transcription_id: UUID of transcription record
        entry_id: UUID of dream entry
        audio_file_path: Path to audio file
        language: Language code for transcription
        transcription_service: Transcription service instance
    """
    from app.database import AsyncSessionLocal

    logger.info(
        f"Starting transcription background task",
        transcription_id=str(transcription_id),
        entry_id=str(entry_id)
    )

    async with AsyncSessionLocal() as db:
        try:
            # Update status to processing
            await db_service.update_transcription_status(
                db=db,
                transcription_id=transcription_id,
                status="processing"
            )
            await db.commit()

            logger.info(f"Transcription status updated to 'processing'", transcription_id=str(transcription_id))

            # Perform transcription
            result = await transcription_service.transcribe_audio(
                audio_path=Path(audio_file_path),
                language=language
            )

            logger.info(
                f"Transcription completed successfully",
                transcription_id=str(transcription_id),
                text_length=len(result["text"])
            )

            # Update with result
            await db_service.update_transcription_status(
                db=db,
                transcription_id=transcription_id,
                status="completed",
                transcribed_text=result["text"]
            )
            await db.commit()

            logger.info(f"Transcription result saved to database", transcription_id=str(transcription_id))

        except Exception as e:
            logger.error(
                f"Transcription failed",
                transcription_id=str(transcription_id),
                error=str(e),
                exc_info=True
            )

            try:
                await db_service.update_transcription_status(
                    db=db,
                    transcription_id=transcription_id,
                    status="failed",
                    error_message=str(e)
                )
                await db.commit()
            except Exception as db_error:
                logger.error(
                    f"Failed to update transcription failure status",
                    transcription_id=str(transcription_id),
                    error=str(db_error),
                    exc_info=True
                )


@router.post(
    "/entries/{entry_id}/transcribe",
    response_model=TranscriptionTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger audio transcription",
    description="Start background transcription of an audio file using the configured Whisper model (set via WHISPER_MODEL env variable)"
)
async def trigger_transcription(
    entry_id: UUID,
    request_data: TranscriptionTriggerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    transcription_service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Trigger transcription for a dream entry audio file.

    The transcription runs in the background using the configured Whisper model.
    Use the returned transcription_id to check status via GET /transcriptions/{transcription_id}.

    Args:
        entry_id: UUID of the dream entry
        request_data: Transcription parameters (language)
        background_tasks: FastAPI background tasks
        db: Database session
        transcription_service: Transcription service

    Returns:
        TranscriptionTriggerResponse with transcription ID and status

    Raises:
        HTTPException: If entry not found or transcription cannot be started
    """
    # Get model name from loaded transcription service
    model_name = transcription_service.get_model_name()

    logger.info(
        f"Transcription trigger requested",
        entry_id=str(entry_id),
        model=model_name,
        language=request_data.language
    )

    # Verify entry exists
    entry = await db_service.get_entry_by_id(db, entry_id)
    if not entry:
        logger.warning(f"Entry not found for transcription", entry_id=str(entry_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry not found: {entry_id}"
        )

    # Create transcription record
    transcription_data = TranscriptionCreate(
        entry_id=entry_id,
        status="pending",
        model_used=model_name,
        language_code=request_data.language,
        is_primary=False  # Can be set later via set-primary endpoint
    )

    transcription = await db_service.create_transcription(db, transcription_data)
    await db.commit()

    logger.info(
        f"Transcription record created",
        transcription_id=str(transcription.id),
        entry_id=str(entry_id)
    )

    # Add background task for transcription processing
    background_tasks.add_task(
        process_transcription_task,
        transcription_id=transcription.id,
        entry_id=entry_id,
        audio_file_path=entry.file_path,
        language=request_data.language,
        transcription_service=transcription_service
    )

    logger.info(f"Background transcription task queued", transcription_id=str(transcription.id))

    return TranscriptionTriggerResponse(
        transcription_id=transcription.id,
        entry_id=entry_id,
        status="processing",
        message="Transcription started in background"
    )


@router.get(
    "/transcriptions/{transcription_id}",
    response_model=TranscriptionStatusResponse,
    summary="Get transcription status and result",
    description="Retrieve transcription details including status and transcribed text"
)
async def get_transcription(
    transcription_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transcription by ID.

    Args:
        transcription_id: UUID of the transcription
        db: Database session

    Returns:
        TranscriptionStatusResponse with full transcription details

    Raises:
        HTTPException: If transcription not found
    """
    transcription = await db_service.get_transcription_by_id(db, transcription_id)

    if not transcription:
        logger.warning(f"Transcription not found", transcription_id=str(transcription_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription not found: {transcription_id}"
        )

    logger.info(f"Transcription retrieved", transcription_id=str(transcription_id))

    return TranscriptionStatusResponse.model_validate(transcription)


@router.get(
    "/entries/{entry_id}/transcriptions",
    response_model=TranscriptionListResponse,
    summary="List all transcriptions for an entry",
    description="Get all transcription attempts for a dream entry, ordered by creation date"
)
async def list_transcriptions(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    List all transcriptions for a dream entry.

    Args:
        entry_id: UUID of the dream entry
        db: Database session

    Returns:
        TranscriptionListResponse with list of all transcriptions

    Raises:
        HTTPException: If entry not found
    """
    # Verify entry exists
    entry = await db_service.get_entry_by_id(db, entry_id)
    if not entry:
        logger.warning(f"Entry not found", entry_id=str(entry_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry not found: {entry_id}"
        )

    transcriptions = await db_service.get_transcriptions_for_entry(db, entry_id)

    logger.info(f"Transcriptions listed", entry_id=str(entry_id), count=len(transcriptions))

    return TranscriptionListResponse(
        transcriptions=[TranscriptionResponse.model_validate(t) for t in transcriptions],
        total=len(transcriptions)
    )


@router.put(
    "/transcriptions/{transcription_id}/set-primary",
    response_model=TranscriptionResponse,
    summary="Set transcription as primary",
    description="Mark a transcription as the primary one to display for its entry"
)
async def set_primary_transcription(
    transcription_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Set a transcription as primary for its entry.

    Automatically unsets any existing primary transcription for the same entry.

    Args:
        transcription_id: UUID of the transcription to set as primary
        db: Database session

    Returns:
        TranscriptionResponse with updated transcription

    Raises:
        HTTPException: If transcription not found or not completed
    """
    transcription = await db_service.get_transcription_by_id(db, transcription_id)

    if not transcription:
        logger.warning(f"Transcription not found", transcription_id=str(transcription_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription not found: {transcription_id}"
        )

    if transcription.status != "completed":
        logger.warning(
            f"Cannot set non-completed transcription as primary",
            transcription_id=str(transcription_id),
            status=transcription.status
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed transcriptions can be set as primary"
        )

    updated_transcription = await db_service.set_primary_transcription(db, transcription_id)
    await db.commit()

    logger.info(f"Transcription set as primary", transcription_id=str(transcription_id))

    return TranscriptionResponse.model_validate(updated_transcription)
