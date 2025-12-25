"""
API routes for audio transcription operations.
"""
import json
from uuid import UUID
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.database import db_service
from app.services.transcription import TranscriptionService
from app.services.envelope_encryption import (
    EnvelopeEncryptionService,
    get_encryption_service,
    create_envelope_encryption_service,
)
from app.services.provider_registry import (
    get_effective_transcription_provider,
    get_transcription_service_for_provider,
)
from app.middleware.jwt import get_current_user
from app.schemas.transcription import (
    TranscriptionTriggerRequest,
    TranscriptionTriggerResponse,
    TranscriptionResponse,
    TranscriptionListResponse,
    TranscriptionStatusResponse,
    TranscriptionCreate,
    TranscriptionSegment,
)
from app.schemas.voice_entry import DeleteResponse
from app.utils.encryption_helpers import (
    decrypt_audio_to_temp,
    cleanup_temp_file,
    encrypt_text,
    decrypt_text,
)
from app.utils.logger import get_logger

logger = get_logger("transcription_routes")

router = APIRouter()


async def process_transcription_task(
    transcription_id: UUID,
    entry_id: UUID,
    user_id: UUID,
    audio_file_path: str,
    language: str,
    transcription_provider: str,
    beam_size: Optional[int] = None,
    temperature: Optional[float] = None,
    transcription_model: Optional[str] = None,
    enable_diarization: bool = False,
    speaker_count: int = 1
):
    """
    Background task to process audio transcription.

    Args:
        transcription_id: UUID of transcription record
        entry_id: UUID of voice entry
        user_id: UUID of the user (for encryption/decryption)
        audio_file_path: Path to audio file
        language: Language code for transcription
        transcription_provider: Transcription provider name (e.g., 'groq', 'assemblyai')
        beam_size: Beam size for transcription (1-10, optional)
        temperature: Temperature for transcription sampling (0.0-1.0, optional)
        transcription_model: Model to use for transcription (optional, uses service default if None)
        enable_diarization: Enable speaker diarization
        speaker_count: Expected number of speakers
    """
    from app.database import AsyncSessionLocal

    # Create transcription service for this provider
    transcription_service = get_transcription_service_for_provider(
        transcription_provider,
        model=transcription_model
    )

    logger.info(
        f"Starting transcription background task",
        transcription_id=str(transcription_id),
        entry_id=str(entry_id)
    )

    temp_decrypted_path = None
    encryption_service = None

    async with AsyncSessionLocal() as db:
        try:
            # Get voice entry to check encryption status
            voice_entry = await db_service.get_entry_by_id(db, entry_id, user_id)
            if not voice_entry:
                raise ValueError(f"Voice entry not found: {entry_id}")

            # Initialize encryption service if needed
            if voice_entry.is_encrypted:
                encryption_service = create_envelope_encryption_service()
                if encryption_service is None:
                    raise RuntimeError("Encryption service unavailable but audio is encrypted")

            # Update status to processing
            await db_service.update_transcription_status(
                db=db,
                transcription_id=transcription_id,
                status="processing"
            )
            await db.commit()

            logger.info(f"Transcription status updated to 'processing'", transcription_id=str(transcription_id))

            # Decrypt audio file if encrypted
            actual_audio_path = audio_file_path
            if voice_entry.is_encrypted:
                logger.info(
                    "Decrypting audio file for transcription",
                    entry_id=str(entry_id),
                    encrypted_path=audio_file_path
                )
                temp_decrypted_path = await decrypt_audio_to_temp(
                    encryption_service,
                    db,
                    audio_file_path,
                    entry_id,
                    user_id,
                )
                actual_audio_path = str(temp_decrypted_path)
                logger.info(
                    "Audio file decrypted for transcription",
                    entry_id=str(entry_id),
                    temp_path=actual_audio_path
                )

            # Perform transcription
            result = await transcription_service.transcribe_audio(
                audio_path=Path(actual_audio_path),
                language=language,
                beam_size=beam_size,
                temperature=temperature,
                model=transcription_model,
                enable_diarization=enable_diarization,
                speaker_count=speaker_count
            )

            diarization_applied = result.get("diarization_applied", False)
            segments = result.get("segments", [])

            logger.info(
                f"Transcription completed successfully",
                transcription_id=str(transcription_id),
                text_length=len(result["text"]),
                beam_size=result.get("beam_size"),
                diarization_applied=diarization_applied,
                segment_count=len(segments)
            )

            # Encrypt the transcription result (encryption is always on)
            # Re-create encryption service for saving (if needed)
            if encryption_service is None:
                encryption_service = create_envelope_encryption_service()

            encrypted_text = await encrypt_text(
                encryption_service,
                db,
                result["text"],
                entry_id,
                user_id,
            )
            logger.info(
                "Transcription text encrypted",
                transcription_id=str(transcription_id),
                encrypted_length=len(encrypted_text)
            )

            # Encrypt segments if diarization was applied and segments exist
            encrypted_segments = None
            if diarization_applied and segments:
                segments_json = json.dumps(segments)
                encrypted_segments = await encrypt_text(
                    encryption_service,
                    db,
                    segments_json,
                    entry_id,
                    user_id,
                )
                logger.info(
                    "Transcription segments encrypted",
                    transcription_id=str(transcription_id),
                    segment_count=len(segments)
                )

            # Update with encrypted result
            await db_service.update_transcription_status(
                db=db,
                transcription_id=transcription_id,
                status="completed",
                transcribed_text=encrypted_text,
                segments=encrypted_segments,
                diarization_applied=diarization_applied,
            )
            await db.commit()

            logger.info(f"Transcription result saved to database", transcription_id=str(transcription_id))

            # Auto-promote to primary if entry has no primary transcription yet
            primary_transcription = await db_service.get_primary_transcription(
                db=db,
                entry_id=entry_id
            )

            if primary_transcription is None:
                logger.info(
                    f"No primary transcription exists, auto-promoting this transcription",
                    transcription_id=str(transcription_id),
                    entry_id=str(entry_id)
                )
                await db_service.set_primary_transcription(
                    db=db,
                    transcription_id=transcription_id
                )
                await db.commit()
                logger.info(f"Transcription auto-promoted to primary", transcription_id=str(transcription_id))
            else:
                logger.info(
                    f"Primary transcription already exists, skipping auto-promotion",
                    transcription_id=str(transcription_id),
                    entry_id=str(entry_id),
                    existing_primary_id=str(primary_transcription.id)
                )

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

        finally:
            # Clean up temp decrypted file
            cleanup_temp_file(temp_decrypted_path)


@router.post(
    "/entries/{entry_id}/transcribe",
    response_model=TranscriptionTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger audio transcription",
    description="Start background transcription of an audio file using the specified or configured transcription provider"
)
async def trigger_transcription(
    entry_id: UUID,
    request_data: TranscriptionTriggerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger transcription for a voice entry audio file.

    The transcription runs in the background using the specified provider.
    Use the returned transcription_id to check status via GET /transcriptions/{transcription_id}.

    Args:
        entry_id: UUID of the voice entry
        request_data: Transcription parameters (language, provider)
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        TranscriptionTriggerResponse with transcription ID and status

    Raises:
        HTTPException: If entry not found, provider not configured, or transcription cannot be started
    """
    # Validate and get effective provider
    try:
        effective_provider = get_effective_transcription_provider(request_data.transcription_provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get transcription service to obtain model name for database record
    transcription_service = get_transcription_service_for_provider(
        effective_provider,
        model=request_data.transcription_model
    )
    model_name = transcription_service.get_model_name()

    logger.info(
        f"Transcription trigger requested",
        entry_id=str(entry_id),
        model=model_name,
        language=request_data.language,
        beam_size=request_data.beam_size
    )

    # Verify entry exists and belongs to current user
    entry = await db_service.get_entry_by_id(db, entry_id, current_user.id)
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
        is_primary=False,  # Can be set later via set-primary endpoint
        beam_size=request_data.beam_size,
        temperature=request_data.temperature,
        enable_diarization=request_data.enable_diarization,
        speaker_count=request_data.speaker_count
    )

    transcription = await db_service.create_transcription(db, transcription_data)
    await db.commit()

    logger.info(
        f"Transcription record created",
        transcription_id=str(transcription.id),
        entry_id=str(entry_id),
        enable_diarization=request_data.enable_diarization,
        speaker_count=request_data.speaker_count
    )

    # Add background task for transcription processing
    background_tasks.add_task(
        process_transcription_task,
        transcription_id=transcription.id,
        entry_id=entry_id,
        user_id=current_user.id,
        audio_file_path=entry.file_path,
        language=request_data.language,
        transcription_provider=effective_provider,
        beam_size=request_data.beam_size,
        temperature=request_data.temperature,
        transcription_model=request_data.transcription_model,
        enable_diarization=request_data.enable_diarization,
        speaker_count=request_data.speaker_count
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
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

    # Verify the transcription's entry belongs to the current user
    entry = await db_service.get_entry_by_id(db, transcription.entry_id, current_user.id)
    if not entry:
        logger.warning(
            f"Unauthorized access to transcription",
            transcription_id=str(transcription_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription not found: {transcription_id}"
        )

    # Decrypt transcription text (always encrypted)
    decrypted_text = await decrypt_text(
        encryption_service=encryption_service,
        db=db,
        encrypted_bytes=transcription.transcribed_text,
        voice_entry_id=entry.id,
        user_id=current_user.id,
    )

    # Decrypt segments if they exist
    decrypted_segments = None
    diarization_applied = False
    if transcription.segments is not None:
        segments_json = await decrypt_text(
            encryption_service=encryption_service,
            db=db,
            encrypted_bytes=transcription.segments,
            voice_entry_id=entry.id,
            user_id=current_user.id,
        )
        if segments_json:
            segments_data = json.loads(segments_json)
            decrypted_segments = [TranscriptionSegment(**s) for s in segments_data]
            # Check if any segment has a speaker label to determine if diarization was applied
            diarization_applied = any(s.speaker is not None for s in decrypted_segments)

    logger.info(f"Transcription retrieved", transcription_id=str(transcription_id))

    return TranscriptionStatusResponse(
        id=transcription.id,
        status=transcription.status,
        transcribed_text=decrypted_text,
        model_used=transcription.model_used,
        language_code=transcription.language_code,
        beam_size=transcription.beam_size,
        temperature=transcription.temperature,
        enable_diarization=transcription.enable_diarization,
        speaker_count=transcription.speaker_count,
        segments=decrypted_segments,
        diarization_applied=diarization_applied,
        transcription_started_at=transcription.transcription_started_at,
        transcription_completed_at=transcription.transcription_completed_at,
        error_message=transcription.error_message,
        is_primary=transcription.is_primary,
    )


@router.get(
    "/entries/{entry_id}/transcriptions",
    response_model=TranscriptionListResponse,
    summary="List all transcriptions for an entry",
    description="Get all transcription attempts for a voice entry, ordered by creation date"
)
async def list_transcriptions(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service),
):
    """
    List all transcriptions for a voice entry.

    Args:
        entry_id: UUID of the voice entry
        db: Database session

    Returns:
        TranscriptionListResponse with list of all transcriptions

    Raises:
        HTTPException: If entry not found
    """
    # Verify entry exists and belongs to current user
    entry = await db_service.get_entry_by_id(db, entry_id, current_user.id)
    if not entry:
        logger.warning(f"Entry not found", entry_id=str(entry_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry not found: {entry_id}"
        )

    transcriptions = await db_service.get_transcriptions_for_entry(db, entry_id, current_user.id)

    # Decrypt transcribed_text and segments for each transcription
    transcription_responses = []
    for t in transcriptions:
        decrypted_text = None
        if t.transcribed_text is not None:
            decrypted_text = await decrypt_text(
                encryption_service=encryption_service,
                db=db,
                encrypted_bytes=t.transcribed_text,
                voice_entry_id=entry_id,
                user_id=current_user.id,
            )

        # Decrypt segments if they exist
        decrypted_segments = None
        diarization_applied = False
        if t.segments is not None:
            segments_json = await decrypt_text(
                encryption_service=encryption_service,
                db=db,
                encrypted_bytes=t.segments,
                voice_entry_id=entry_id,
                user_id=current_user.id,
            )
            if segments_json:
                segments_data = json.loads(segments_json)
                decrypted_segments = [TranscriptionSegment(**s) for s in segments_data]
                diarization_applied = any(s.speaker is not None for s in decrypted_segments)

        transcription_responses.append(TranscriptionResponse(
            id=t.id,
            entry_id=t.entry_id,
            transcribed_text=decrypted_text,
            status=t.status,
            model_used=t.model_used,
            language_code=t.language_code,
            is_primary=t.is_primary,
            beam_size=t.beam_size,
            temperature=t.temperature,
            enable_diarization=t.enable_diarization,
            speaker_count=t.speaker_count,
            segments=decrypted_segments,
            diarization_applied=diarization_applied,
            transcription_started_at=t.transcription_started_at,
            transcription_completed_at=t.transcription_completed_at,
            error_message=t.error_message,
            created_at=t.created_at,
            updated_at=t.updated_at,
        ))

    logger.info(f"Transcriptions listed", entry_id=str(entry_id), count=len(transcriptions))

    return TranscriptionListResponse(
        transcriptions=transcription_responses,
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service),
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

    # Verify the transcription's entry belongs to the current user
    entry = await db_service.get_entry_by_id(db, transcription.entry_id, current_user.id)
    if not entry:
        logger.warning(
            f"Unauthorized access to transcription",
            transcription_id=str(transcription_id),
            user_id=str(current_user.id)
        )
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

    # Decrypt transcribed_text before returning
    decrypted_text = None
    if updated_transcription.transcribed_text is not None:
        decrypted_text = await decrypt_text(
            encryption_service=encryption_service,
            db=db,
            encrypted_bytes=updated_transcription.transcribed_text,
            voice_entry_id=updated_transcription.entry_id,
            user_id=current_user.id,
        )

    # Decrypt segments if they exist
    decrypted_segments = None
    diarization_applied = False
    if updated_transcription.segments is not None:
        segments_json = await decrypt_text(
            encryption_service=encryption_service,
            db=db,
            encrypted_bytes=updated_transcription.segments,
            voice_entry_id=updated_transcription.entry_id,
            user_id=current_user.id,
        )
        if segments_json:
            segments_data = json.loads(segments_json)
            decrypted_segments = [TranscriptionSegment(**s) for s in segments_data]
            diarization_applied = any(s.speaker is not None for s in decrypted_segments)

    logger.info(f"Transcription set as primary", transcription_id=str(transcription_id))

    return TranscriptionResponse(
        id=updated_transcription.id,
        entry_id=updated_transcription.entry_id,
        transcribed_text=decrypted_text,
        status=updated_transcription.status,
        model_used=updated_transcription.model_used,
        language_code=updated_transcription.language_code,
        is_primary=updated_transcription.is_primary,
        beam_size=updated_transcription.beam_size,
        temperature=updated_transcription.temperature,
        enable_diarization=updated_transcription.enable_diarization,
        speaker_count=updated_transcription.speaker_count,
        segments=decrypted_segments,
        diarization_applied=diarization_applied,
        transcription_started_at=updated_transcription.transcription_started_at,
        transcription_completed_at=updated_transcription.transcription_completed_at,
        error_message=updated_transcription.error_message,
        created_at=updated_transcription.created_at,
        updated_at=updated_transcription.updated_at,
    )


@router.delete(
    "/transcriptions/{transcription_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete transcription",
    description="Permanently delete a transcription and all associated cleaned entries. Prevents deletion of the only transcription for an entry.",
    responses={
        200: {"description": "Transcription deleted successfully"},
        404: {"description": "Transcription not found or not authorized"},
        409: {"description": "Cannot delete the only transcription for an entry"},
        500: {"description": "Server error"}
    }
)
async def delete_transcription(
    transcription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeleteResponse:
    """
    Permanently delete a transcription with user ownership verification.

    Deletes:
    - Transcription database record
    - All cleaned entries (cascaded)

    Validation:
    - Prevents deletion if this is the only transcription for the entry
    - Requires user to own the parent voice entry

    Security:
    - Requires JWT authentication
    - Users can only delete transcriptions for their own entries
    - Returns 404 for both non-existent and unauthorized access

    Args:
        transcription_id: UUID of the transcription to delete
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        DeleteResponse with success message and deleted transcription ID

    Raises:
        HTTPException: 404 if not found/unauthorized, 409 if validation fails
    """
    logger.info(
        "Transcription deletion requested",
        transcription_id=str(transcription_id),
        user_id=str(current_user.id)
    )

    # Delete from database (validates ownership and business rules)
    deleted = await db_service.delete_transcription(db, transcription_id, current_user.id)

    if not deleted:
        logger.warning(
            "Transcription not found or unauthorized for deletion",
            transcription_id=str(transcription_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )

    # Commit database transaction
    await db.commit()

    logger.info(
        "Transcription deleted successfully",
        transcription_id=str(transcription_id),
        user_id=str(current_user.id)
    )

    return DeleteResponse(
        message="Transcription deleted successfully",
        deleted_id=transcription_id
    )
