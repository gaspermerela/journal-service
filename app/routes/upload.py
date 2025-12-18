"""
Upload endpoint for audio file uploads.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.voice_entry import VoiceEntryCreate, VoiceEntryUploadResponse, VoiceEntryUploadAndTranscribeResponse
from app.schemas.transcription import TranscriptionCreate
from app.schemas.cleanup import UploadTranscribeCleanupResponse
from app.models.cleaned_entry import CleanupStatus
from app.services.storage import storage_service
from app.services.database import db_service
from app.services.transcription import TranscriptionService
from app.services.audio_preprocessing import preprocessing_service
from app.services.envelope_encryption import EnvelopeEncryptionService, get_encryption_service
from app.services.provider_registry import (
    get_effective_transcription_provider,
    get_effective_llm_provider,
    get_transcription_service_for_provider,
)
from app.middleware.jwt import get_current_user
from app.utils.validators import validate_audio_file
from app.utils.logger import get_logger
from app.utils.audio import get_audio_duration
from app.utils.encryption_helpers import (
    encrypt_audio_file,
    decrypt_text,
)
from app.config import settings

logger = get_logger("upload")
router = APIRouter()


async def preprocess_audio_always(file_path: str) -> str:
    """
    Preprocess audio file using ffmpeg pipeline.

    Always applies preprocessing to ensure consistent audio quality.

    Args:
        file_path: Path to the audio file

    Returns:
        Path to the preprocessed file (or original if preprocessing disabled/failed)
    """
    if not settings.ENABLE_AUDIO_PREPROCESSING:
        logger.info("Audio preprocessing disabled", file_path=file_path)
        return file_path

    # Always preprocess for consistent quality
    success, processed_path, error_msg = await preprocessing_service.preprocess_audio(file_path)

    if not success:
        logger.error(
            "Audio preprocessing failed, using original file",
            file_path=file_path,
            error=error_msg
        )
        return file_path

    logger.info(
        "Audio preprocessing completed",
        original_path=file_path,
        processed_path=processed_path,
    )

    return processed_path


async def transcription_then_cleanup_task(
    transcription_id: uuid.UUID,
    entry_id: uuid.UUID,
    audio_file_path: str,
    language: str,
    transcription_provider: str,
    cleaned_entry_id: uuid.UUID,
    entry_type: str,
    user_id: uuid.UUID,
    transcription_beam_size: Optional[int] = None,
    transcription_temperature: Optional[float] = None,
    transcription_model: Optional[str] = None,
    cleanup_temperature: Optional[float] = None,
    cleanup_top_p: Optional[float] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    enable_diarization: bool = False,
    speaker_count: int = 1
):
    """
    Background task that runs transcription, then triggers cleanup when done.

    This function is executed as a background task and handles the complete
    workflow of transcribing audio and then cleaning up the transcription.

    Args:
        transcription_provider: Transcription provider name (e.g., 'groq', 'assemblyai')
        transcription_beam_size: Beam size for transcription (1-10)
        transcription_temperature: Temperature for transcription (0.0-1.0)
        transcription_model: Model to use for transcription
        cleanup_temperature: Temperature for LLM cleanup (0.0-2.0)
        cleanup_top_p: Top-p for LLM cleanup (0.0-1.0)
        llm_model: Model to use for LLM cleanup
        llm_provider: LLM provider name (e.g., 'ollama', 'groq')
        enable_diarization: Enable speaker diarization
        speaker_count: Expected number of speakers
    """
    # Import here to avoid circular imports
    from app.routes.transcription import process_transcription_task
    from app.routes.cleanup import process_cleanup_background

    # Run transcription
    await process_transcription_task(
        transcription_id=transcription_id,
        entry_id=entry_id,
        user_id=user_id,
        audio_file_path=audio_file_path,
        language=language,
        transcription_provider=transcription_provider,
        beam_size=transcription_beam_size,
        temperature=transcription_temperature,
        transcription_model=transcription_model,
        enable_diarization=enable_diarization,
        speaker_count=speaker_count
    )

    # Check if transcription succeeded
    from app.database import get_session
    from app.main import app

    async with get_session() as db:
        transcription_result = await db_service.get_transcription_by_id(
            db=db,
            transcription_id=transcription_id
        )

        # Check for completed transcription with text
        has_text = (
            transcription_result
            and transcription_result.status == "completed"
            and transcription_result.transcribed_text is not None
        )

        if has_text:
            # Decrypt transcription text (always encrypted)
            encryption_service = app.state.encryption_service
            transcription_text = await decrypt_text(
                encryption_service=encryption_service,
                db=db,
                encrypted_bytes=transcription_result.transcribed_text,
                voice_entry_id=entry_id,
                user_id=user_id,
            )

            if transcription_text:
                # Trigger cleanup
                logger.info(
                    f"Transcription completed, starting cleanup for {cleaned_entry_id}",
                    cleanup_temperature=cleanup_temperature,
                    cleanup_top_p=cleanup_top_p,
                    llm_provider=llm_provider
                )
                await process_cleanup_background(
                    cleaned_entry_id=cleaned_entry_id,
                    transcription_text=transcription_text,
                    entry_type=entry_type,
                    user_id=user_id,
                    voice_entry_id=entry_id,
                    temperature=cleanup_temperature,
                    top_p=cleanup_top_p,
                    llm_model=llm_model,
                    llm_provider=llm_provider
                )
            else:
                # Decryption failed
                logger.warning(f"Failed to decrypt transcription text for {cleaned_entry_id}")
                await db_service.update_cleaned_entry_processing(
                    db=db,
                    cleaned_entry_id=cleaned_entry_id,
                    cleanup_status=CleanupStatus.FAILED,
                    error_message="Failed to decrypt transcription text"
                )
                await db.commit()
        else:
            # Transcription failed, mark cleanup as failed too
            logger.warning(f"Transcription failed, skipping cleanup for {cleaned_entry_id}")
            await db_service.update_cleaned_entry_processing(
                db=db,
                cleaned_entry_id=cleaned_entry_id,
                cleanup_status=CleanupStatus.FAILED,
                error_message="Transcription failed or produced no text"
            )
            await db.commit()


@router.post(
    "/upload",
    response_model=VoiceEntryUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload audio file",
    description="Upload an audio file (MP3 or M4A) for dream journaling. File is saved to disk and metadata stored in database.",
    responses={
        201: {"description": "File uploaded successfully"},
        400: {"description": "Invalid file type or missing file"},
        413: {"description": "File too large"},
        500: {"description": "Server error during upload"}
    }
)
async def upload_audio(
    request: Request,
    file: UploadFile = File(..., description="Audio file to upload (MP3 or M4A)"),
    entry_type: str = Form("dream", description="Type of voice entry (dream, journal, meeting, note, etc.)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service),
) -> VoiceEntryUploadResponse:
    """
    Upload audio file endpoint.

    Process:
    1. Validate file (type, size, extension)
    2. Generate UUID for entry
    3. Save file to disk
    4. Preprocess audio (if lossy format and enabled)
    5. Create database entry with specified entry_type
    6. Return entry metadata

    If any step fails:
    - Database transaction is rolled back automatically
    - Saved file is deleted if database write fails
    """
    file_id = uuid.uuid4()
    saved_file_path = None

    # Log upload request
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"File upload request received",
        ip=client_ip,
        filename=file.filename,
        content_type=file.content_type,
        entry_type=entry_type
    )

    try:
        # Step 1: Validate file
        await validate_audio_file(file)

        # Step 2: Save file to storage
        saved_filename, file_path = await storage_service.save_file(file, file_id)
        saved_file_path = file_path  # Store for potential rollback

        # Step 2.5: Preprocess audio (always, for consistency)
        final_file_path = await preprocess_audio_always(file_path)

        # Update saved_file_path if preprocessing changed the file
        if final_file_path != file_path:
            saved_file_path = final_file_path

        # Step 2.6: Calculate audio duration (using preprocessed file)
        duration_seconds = get_audio_duration(final_file_path)

        # Step 3: Create database entry (initially unencrypted)
        entry_data = VoiceEntryCreate(
            original_filename=file.filename,
            saved_filename=saved_filename,
            file_path=final_file_path,
            entry_type=entry_type,
            duration_seconds=duration_seconds,
            uploaded_at=datetime.now(timezone.utc),
            user_id=current_user.id
        )

        entry = await db_service.create_entry(db, entry_data)
        await db.flush()  # Get entry.id for encryption

        # Step 4: Encrypt audio file (always encrypted)
        encrypted_path, encryption_version = await encrypt_audio_file(
            encryption_service,
            db,
            final_file_path,
            entry.id,
            current_user.id,
        )
        # Update entry with encrypted file path
        entry = await db_service.update_entry_encryption(
            db,
            entry.id,
            current_user.id,
            file_path=encrypted_path,
            is_encrypted=True,
            encryption_version=encryption_version,
        )
        # Update saved_file_path for rollback in case of later failure
        saved_file_path = encrypted_path
        logger.info(
            "Audio file encrypted",
            entry_id=str(entry.id),
            encrypted_path=encrypted_path,
        )

        # Step 5: Commit transaction (handled by get_db dependency)
        await db.commit()

        logger.info(
            f"File upload completed successfully",
            entry_id=str(entry.id),
            filename=file.filename,
            saved_as=saved_filename,
            is_encrypted=entry.is_encrypted,
        )

        # Return response
        return VoiceEntryUploadResponse(
            id=entry.id,
            original_filename=entry.original_filename,
            saved_filename=entry.saved_filename,
            duration_seconds=entry.duration_seconds,
            entry_type=entry.entry_type,
            uploaded_at=entry.uploaded_at,
            message="File uploaded successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise

    except Exception as e:
        # Rollback: Delete saved file if it exists and database write failed
        if saved_file_path:
            logger.warning(
                f"Rolling back: deleting saved file due to error",
                file_path=saved_file_path
            )
            await storage_service.delete_file(saved_file_path)

        logger.error(
            f"Upload failed with unexpected error",
            filename=file.filename,
            error=str(e),
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process file upload"
        )


@router.post(
    "/upload-and-transcribe",
    response_model=VoiceEntryUploadAndTranscribeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload audio file and start transcription",
    description="Upload an audio file and immediately start transcription in a single request. Returns both entry details and transcription ID.",
    responses={
        202: {"description": "File uploaded and transcription started"},
        400: {"description": "Invalid file type, missing file, or unconfigured provider"},
        413: {"description": "File too large"},
        500: {"description": "Server error during upload"},
    }
)
async def upload_and_transcribe(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to upload (MP3 or M4A)"),
    entry_type: str = Form("dream", description="Type of voice entry (dream, journal, meeting, note, etc.)"),
    language: Optional[str] = Form(None, description="Language code for transcription (e.g., 'en', 'es', 'sl') or 'auto' for detection. If not provided, uses user preference."),
    transcription_beam_size: Optional[int] = Form(None, description="Beam size for transcription (1-10, higher = more accurate but slower). If not provided, uses default from config."),
    transcription_temperature: Optional[float] = Form(None, ge=0.0, le=1.0, description="Temperature for transcription sampling (0.0-1.0, higher = more random). If not provided, uses default."),
    transcription_model: Optional[str] = Form(None, description="Transcription model to use (e.g., 'whisper-large-v3'). If not provided, uses configured default."),
    transcription_provider: Optional[str] = Form(None, description="Transcription provider (e.g., 'groq', 'assemblyai', 'clarinsi_slovene_asr'). If not provided, uses configured default."),
    enable_diarization: bool = Form(False, description="Enable speaker diarization to identify different speakers."),
    speaker_count: int = Form(1, ge=1, le=10, description="Expected number of speakers (1-10). Only used if enable_diarization=True."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service),
) -> VoiceEntryUploadAndTranscribeResponse:
    """
    Combined endpoint to upload audio file and start transcription.

    Process:
    1. Validate file (type, size, extension)
    2. Generate UUID for entry
    3. Save file to disk
    4. Create database entry with specified entry_type
    5. Create transcription record
    6. Start background transcription task
    7. Return entry metadata and transcription ID

    If any step fails:
    - Database transaction is rolled back automatically
    - Saved file is deleted if database write fails
    """
    # Validate and get effective transcription provider
    try:
        effective_transcription_provider = get_effective_transcription_provider(transcription_provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get transcription service to obtain model name for database record
    # TODO: Simplify
    transcription_service = get_transcription_service_for_provider(effective_transcription_provider)

    file_id = uuid.uuid4()
    saved_file_path = None

    # Determine effective language: request → user preference → auto
    if language is None:
        user_preferences = await db_service.get_user_preferences(db, current_user.id)
        effective_language = user_preferences.preferred_transcription_language
        logger.info(
            f"Using user preference for language",
            user_id=str(current_user.id),
            language=effective_language
        )
    else:
        effective_language = language

    # Log upload request
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"Combined upload and transcribe request received",
        ip=client_ip,
        filename=file.filename,
        content_type=file.content_type,
        entry_type=entry_type,
        language=effective_language
    )

    try:
        # Step 1: Validate file
        await validate_audio_file(file)

        # Step 2: Save file to storage
        saved_filename, file_path = await storage_service.save_file(file, file_id)
        saved_file_path = file_path  # Store for potential rollback

        # Step 2.5: Preprocess audio (always, for consistency)
        final_file_path = await preprocess_audio_always(file_path)

        # Update saved_file_path if preprocessing changed the file
        if final_file_path != file_path:
            saved_file_path = final_file_path

        # Step 2.6: Calculate audio duration (using preprocessed file)
        duration_seconds = get_audio_duration(final_file_path)

        # Step 3: Create database entry (initially unencrypted)
        entry_data = VoiceEntryCreate(
            original_filename=file.filename,
            saved_filename=saved_filename,
            file_path=final_file_path,
            entry_type=entry_type,
            duration_seconds=duration_seconds,
            uploaded_at=datetime.now(timezone.utc),
            user_id=current_user.id
        )

        entry = await db_service.create_entry(db, entry_data)
        await db.flush()  # Get entry.id for encryption

        # Step 3.5: Encrypt audio file (always encrypted)
        encrypted_path, encryption_version = await encrypt_audio_file(
            encryption_service,
            db,
            final_file_path,
            entry.id,
            current_user.id,
        )
        # Update entry with encrypted file path
        entry = await db_service.update_entry_encryption(
            db,
            entry.id,
            current_user.id,
            file_path=encrypted_path,
            is_encrypted=True,
            encryption_version=encryption_version,
        )
        saved_file_path = encrypted_path
        logger.info(
            "Audio file encrypted",
            entry_id=str(entry.id),
            encrypted_path=encrypted_path,
        )

        await db.commit()

        logger.info(
            f"File upload completed successfully",
            entry_id=str(entry.id),
            filename=file.filename,
            saved_as=saved_filename,
            is_encrypted=entry.is_encrypted,
        )

        # Step 4: Create transcription record
        model_name = transcription_service.get_model_name()

        transcription_data = TranscriptionCreate(
            entry_id=entry.id,
            status="pending",
            model_used=model_name,
            language_code=effective_language,
            is_primary=False,
            beam_size=transcription_beam_size,
            temperature=transcription_temperature,
            enable_diarization=enable_diarization,
            speaker_count=speaker_count
        )

        transcription = await db_service.create_transcription(db, transcription_data)
        await db.commit()

        logger.info(
            f"Transcription record created",
            transcription_id=str(transcription.id),
            entry_id=str(entry.id),
            enable_diarization=enable_diarization,
            speaker_count=speaker_count
        )

        # Step 5: Add background task for transcription processing
        # Import the background task function from transcription routes
        from app.routes.transcription import process_transcription_task

        background_tasks.add_task(
            process_transcription_task,
            transcription_id=transcription.id,
            entry_id=entry.id,
            user_id=current_user.id,
            audio_file_path=entry.file_path,
            language=effective_language,
            transcription_provider=effective_transcription_provider,
            beam_size=transcription_beam_size,
            temperature=transcription_temperature,
            transcription_model=transcription_model,
            enable_diarization=enable_diarization,
            speaker_count=speaker_count
        )

        logger.info(
            f"Background transcription task queued",
            transcription_id=str(transcription.id)
        )

        # Return response
        return VoiceEntryUploadAndTranscribeResponse(
            entry_id=entry.id,
            transcription_id=transcription.id,
            original_filename=entry.original_filename,
            saved_filename=entry.saved_filename,
            duration_seconds=entry.duration_seconds,
            entry_type=entry.entry_type,
            uploaded_at=entry.uploaded_at,
            transcription_status="processing",
            transcription_language=effective_language,
            message="File uploaded and transcription started"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise

    except Exception as e:
        # Rollback: Delete saved file if it exists and database write failed
        if saved_file_path:
            logger.warning(
                f"Rolling back: deleting saved file due to error",
                file_path=saved_file_path
            )
            await storage_service.delete_file(saved_file_path)

        logger.error(
            f"Upload and transcribe failed with unexpected error",
            filename=file.filename,
            error=str(e),
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process file upload and transcription"
        )


@router.post(
    "/upload-transcribe-cleanup",
    response_model=UploadTranscribeCleanupResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload, transcribe, and cleanup audio file (complete workflow)",
    description="Upload an audio file, transcribe it, and clean it with LLM - all in one request. This is the recommended workflow for most use cases.",
    responses={
        202: {"description": "File uploaded, transcription and cleanup started"},
        400: {"description": "Invalid file type, missing file, or unconfigured provider"},
        413: {"description": "File too large"},
        500: {"description": "Server error during upload"},
    }
)
async def upload_transcribe_and_cleanup(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to upload (MP3 or M4A)"),
    entry_type: str = Form("dream", description="Type of voice entry (dream, journal, meeting, note, etc.)"),
    language: Optional[str] = Form(None, description="Language code for transcription (e.g., 'en', 'es', 'sl') or 'auto' for detection. If not provided, uses user preference."),
    transcription_beam_size: Optional[int] = Form(None, description="Beam size for transcription (1-10, higher = more accurate but slower). If not provided, uses default from config."),
    transcription_temperature: Optional[float] = Form(None, ge=0.0, le=1.0, description="Temperature for transcription sampling (0.0-1.0, higher = more random). If not provided, uses default."),
    transcription_model: Optional[str] = Form(None, description="Transcription model to use (e.g., 'whisper-large-v3'). If not provided, uses configured default."),
    transcription_provider: Optional[str] = Form(None, description="Transcription provider (e.g., 'groq', 'assemblyai', 'clarinsi_slovene_asr'). If not provided, uses configured default."),
    enable_diarization: bool = Form(False, description="Enable speaker diarization to identify different speakers."),
    speaker_count: int = Form(1, ge=1, le=10, description="Expected number of speakers (1-10). Only used if enable_diarization=True."),
    cleanup_temperature: Optional[float] = Form(None, ge=0.0, le=2.0, description="Temperature for LLM cleanup (0.0-2.0, higher = more creative). If not provided, uses default."),
    cleanup_top_p: Optional[float] = Form(None, ge=0.0, le=1.0, description="Top-p for LLM cleanup (0.0-1.0, nucleus sampling). If not provided, uses default."),
    llm_model: Optional[str] = Form(None, description="LLM model to use for cleanup (e.g., 'llama-3.3-70b-versatile'). If not provided, uses configured default."),
    llm_provider: Optional[str] = Form(None, description="LLM provider (e.g., 'ollama', 'groq'). If not provided, uses configured default."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service),
) -> UploadTranscribeCleanupResponse:
    """
    Complete workflow endpoint: upload audio file, transcribe, and cleanup with LLM.

    Process:
    1. Validate file (type, size, extension)
    2. Generate UUID for entry
    3. Save file to disk
    4. Create database entry with specified entry_type
    5. Create transcription record
    6. Create cleanup record
    7. Start background transcription task (which triggers cleanup when done)
    8. Return entry metadata, transcription ID, and cleanup ID

    The cleanup will automatically start after transcription completes.

    If any step fails:
    - Database transaction is rolled back automatically
    - Saved file is deleted if database write fails
    """
    from app.config import settings

    # Validate and get effective providers
    try:
        effective_transcription_provider = get_effective_transcription_provider(transcription_provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    try:
        effective_llm_provider = get_effective_llm_provider(llm_provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get transcription service to obtain model name for database record
    # TODO: Simplify
    transcription_service = get_transcription_service_for_provider(effective_transcription_provider)

    file_id = uuid.uuid4()
    saved_file_path = None

    # Determine effective language: request → user preference → auto
    if language is None:
        user_preferences = await db_service.get_user_preferences(db, current_user.id)
        effective_language = user_preferences.preferred_transcription_language
        logger.info(
            f"Using user preference for language",
            user_id=str(current_user.id),
            language=effective_language
        )
    else:
        effective_language = language

    # Log upload request
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"Complete workflow request received (upload + transcribe + cleanup)",
        ip=client_ip,
        filename=file.filename,
        content_type=file.content_type,
        entry_type=entry_type,
        language=effective_language
    )

    try:
        # Step 1: Validate file
        await validate_audio_file(file)

        # Step 2: Save file to storage
        saved_filename, file_path = await storage_service.save_file(file, file_id)
        saved_file_path = file_path  # Store for potential rollback

        # Step 2.5: Preprocess audio (always, for consistency)
        final_file_path = await preprocess_audio_always(file_path)

        # Update saved_file_path if preprocessing changed the file
        if final_file_path != file_path:
            saved_file_path = final_file_path

        # Step 2.6: Calculate audio duration (using preprocessed file)
        duration_seconds = get_audio_duration(final_file_path)

        # Step 3: Create database entry (initially unencrypted)
        entry_data = VoiceEntryCreate(
            original_filename=file.filename,
            saved_filename=saved_filename,
            file_path=final_file_path,
            entry_type=entry_type,
            duration_seconds=duration_seconds,
            uploaded_at=datetime.now(timezone.utc),
            user_id=current_user.id
        )

        entry = await db_service.create_entry(db, entry_data)
        await db.flush()  # Get entry.id for encryption

        # Step 3.5: Encrypt audio file (always encrypted)
        encrypted_path, encryption_version = await encrypt_audio_file(
            encryption_service,
            db,
            final_file_path,
            entry.id,
            current_user.id,
        )
        # Update entry with encrypted file path
        entry = await db_service.update_entry_encryption(
            db,
            entry.id,
            current_user.id,
            file_path=encrypted_path,
            is_encrypted=True,
            encryption_version=encryption_version,
        )
        saved_file_path = encrypted_path
        logger.info(
            "Audio file encrypted",
            entry_id=str(entry.id),
            encrypted_path=encrypted_path,
        )

        await db.commit()

        logger.info(
            f"File upload completed successfully",
            entry_id=str(entry.id),
            filename=file.filename,
            saved_as=saved_filename,
            is_encrypted=entry.is_encrypted,
        )

        # Step 4: Create transcription record
        model_name = transcription_service.get_model_name()

        transcription_data = TranscriptionCreate(
            entry_id=entry.id,
            status="pending",
            model_used=model_name,
            language_code=effective_language,
            is_primary=False,
            beam_size=transcription_beam_size,
            temperature=transcription_temperature,
            enable_diarization=enable_diarization,
            speaker_count=speaker_count
        )

        transcription = await db_service.create_transcription(db, transcription_data)
        await db.commit()

        logger.info(
            f"Transcription record created",
            transcription_id=str(transcription.id),
            entry_id=str(entry.id),
            enable_diarization=enable_diarization,
            speaker_count=speaker_count
        )

        # Step 5: Create cleanup record
        # Determine cleanup model name in {provider}-{model} format
        if llm_model:
            # User specified a custom model
            cleanup_model_name = f"{effective_llm_provider}-{llm_model}"
        else:
            # Use default from settings based on effective provider
            if effective_llm_provider == "groq":
                cleanup_model_name = f"groq-{settings.GROQ_LLM_MODEL}"
            else:
                cleanup_model_name = f"ollama-{settings.OLLAMA_MODEL}"

        cleaned_entry = await db_service.create_cleaned_entry(
            db=db,
            voice_entry_id=entry.id,
            transcription_id=transcription.id,
            user_id=current_user.id,
            model_name=cleanup_model_name,
            temperature=cleanup_temperature,
            top_p=cleanup_top_p
        )
        await db.commit()

        logger.info(
            f"Cleanup record created",
            cleanup_id=str(cleaned_entry.id),
            transcription_id=str(transcription.id)
        )

        # Step 6: Add background task for transcription + cleanup
        background_tasks.add_task(
            transcription_then_cleanup_task,
            transcription_id=transcription.id,
            entry_id=entry.id,
            audio_file_path=entry.file_path,
            language=effective_language,
            transcription_provider=effective_transcription_provider,
            cleaned_entry_id=cleaned_entry.id,
            entry_type=entry_type,
            user_id=current_user.id,
            transcription_beam_size=transcription_beam_size,
            transcription_temperature=transcription_temperature,
            transcription_model=transcription_model,
            cleanup_temperature=cleanup_temperature,
            cleanup_top_p=cleanup_top_p,
            llm_model=llm_model,
            llm_provider=effective_llm_provider,
            enable_diarization=enable_diarization,
            speaker_count=speaker_count
        )

        logger.info(
            f"Background transcription + cleanup task queued",
            transcription_id=str(transcription.id),
            cleanup_id=str(cleaned_entry.id)
        )

        # Return response
        return UploadTranscribeCleanupResponse(
            entry_id=entry.id,
            original_filename=entry.original_filename,
            saved_filename=entry.saved_filename,
            duration_seconds=entry.duration_seconds,
            entry_type=entry.entry_type,
            uploaded_at=entry.uploaded_at,
            transcription_id=transcription.id,
            transcription_status="processing",
            transcription_language=effective_language,
            cleanup_id=cleaned_entry.id,
            cleanup_status=cleaned_entry.status,
            cleanup_model=cleaned_entry.model_name,
            message="File uploaded, transcription and cleanup started"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise

    except Exception as e:
        # Rollback: Delete saved file if it exists and database write failed
        if saved_file_path:
            logger.warning(
                f"Rolling back: deleting saved file due to error",
                file_path=saved_file_path
            )
            await storage_service.delete_file(saved_file_path)

        logger.error(
            f"Upload, transcribe, and cleanup failed with unexpected error",
            filename=file.filename,
            error=str(e),
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process complete workflow"
        )
