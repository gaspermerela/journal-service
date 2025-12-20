"""
API routes for LLM cleanup operations.
"""
from uuid import UUID
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
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
from app.schemas.voice_entry import DeleteResponse
from app.services.database import db_service
from app.services.llm_cleanup_base import LLMCleanupService
from app.services.envelope_encryption import (
    EnvelopeEncryptionService,
    get_encryption_service,
    create_envelope_encryption_service,
)
from app.services.provider_registry import (
    get_effective_llm_provider,
    get_llm_service_for_provider,
)
from app.config import settings
from app.utils.encryption_helpers import (
    decrypt_text,
    encrypt_text,
)
from app.utils.logger import get_logger


logger = get_logger("routes.cleanup")
router = APIRouter()


def get_llm_cleanup_service(request: Request) -> LLMCleanupService:
    """
    Dependency to get LLM cleanup service from app state.

    Args:
        request: FastAPI request object

    Returns:
        LLMCleanupService instance

    Raises:
        HTTPException: If service not available
    """
    service = getattr(request.app.state, "llm_cleanup_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM cleanup service not available"
        )
    return service


async def process_cleanup_background(
    cleaned_entry_id: UUID,
    transcription_text: str,
    entry_type: str,
    user_id: UUID,
    voice_entry_id: UUID,
    temperature: float = None,
    top_p: float = None,
    llm_model: str = None,
    llm_provider: str = None
):
    """
    Background task to process LLM cleanup.

    Args:
        cleaned_entry_id: UUID of the cleaned entry to update
        transcription_text: Raw transcription text to clean (already decrypted if was encrypted)
        entry_type: Type of entry (dream, journal, etc.)
        user_id: User ID (for auto-sync and encryption check)
        voice_entry_id: Voice entry ID (for auto-sync and DEK lookup)
        temperature: Temperature for cleanup LLM sampling (0.0-2.0)
        top_p: Top-p for cleanup nucleus sampling (0.0-1.0)
        llm_model: Model to use for cleanup (optional, uses service default if None)
        llm_provider: LLM provider name (e.g., 'ollama', 'groq'). If None, uses default.
    """
    from app.database import get_session
    from app.models.notion_sync import SyncStatus as NotionSyncStatus
    from app.routes.notion import process_notion_sync_background
    from app.services.llm_cleanup import create_llm_cleanup_service

    # Use specified provider or fall back to settings default
    effective_provider = llm_provider or settings.LLM_PROVIDER

    async with get_session() as db:
        # Create LLM service using factory with database session for prompt lookup
        llm_service = create_llm_cleanup_service(
            provider=effective_provider,
            db_session=db
        )

        # Initialize encryption service for potential output encryption
        encryption_service = create_envelope_encryption_service()

        try:
            # Update status to processing
            await db_service.update_cleaned_entry_processing(
                db=db,
                cleaned_entry_id=cleaned_entry_id,
                cleanup_status=CleanupStatus.PROCESSING
            )
            await db.commit()

            logger.info(
                f"Starting LLM cleanup for entry {cleaned_entry_id}",
                temperature=temperature,
                top_p=top_p
            )

            # Step 1: Cleanup (plain text with paragraph breaks)
            cleanup_result = await llm_service.cleanup_transcription(
                transcription_text=transcription_text,
                entry_type=entry_type,
                temperature=temperature,
                top_p=top_p,
                model=llm_model
            )

            logger.info(f"Cleanup completed for entry {cleaned_entry_id}")

            # Step 2: Encrypt results (encryption is always on)
            encrypted_cleaned_text = await encrypt_text(
                encryption_service,
                db,
                cleanup_result["cleaned_text"],
                voice_entry_id,
                user_id,
            )
            logger.info(
                "Cleanup results encrypted",
                cleaned_entry_id=str(cleaned_entry_id),
                encrypted_text_length=len(encrypted_cleaned_text)
            )

            # Step 3: Store encrypted results
            await db_service.update_cleaned_entry_processing(
                db=db,
                cleaned_entry_id=cleaned_entry_id,
                cleanup_status=CleanupStatus.COMPLETED,
                cleaned_text=encrypted_cleaned_text,
                prompt_template_id=cleanup_result.get("prompt_template_id"),
                llm_raw_response=cleanup_result.get("llm_raw_response") if settings.LLM_STORE_RAW_RESPONSE else None
            )
            await db.commit()

            logger.info(f"LLM cleanup completed for entry {cleaned_entry_id}")

            # Get the cleaned entry to retrieve voice_entry_id for auto-promotion
            cleaned_entry = await db_service.get_cleaned_entry_by_id(
                db=db,
                cleaned_entry_id=cleaned_entry_id
            )

            # Auto-promote to primary if this voice entry has no primary cleanup yet
            try:
                primary_cleanup = await db_service.get_primary_cleanup_for_voice_entry(
                    db=db,
                    voice_entry_id=cleaned_entry.voice_entry_id
                )

                if primary_cleanup is None:
                    logger.info(
                        f"No primary cleanup exists, auto-promoting this cleanup",
                        cleanup_id=str(cleaned_entry_id),
                        voice_entry_id=str(cleaned_entry.voice_entry_id)
                    )
                    await db_service.set_primary_cleanup(
                        db=db,
                        cleanup_id=cleaned_entry_id
                    )
                    await db.commit()
                    logger.info(f"Cleanup auto-promoted to primary", cleanup_id=str(cleaned_entry_id))
                else:
                    logger.info(
                        f"Primary cleanup already exists, skipping auto-promotion",
                        cleanup_id=str(cleaned_entry_id),
                        voice_entry_id=str(cleaned_entry.voice_entry_id),
                        existing_primary_id=str(primary_cleanup.id)
                    )
            except Exception as promotion_error:
                # Don't fail cleanup if auto-promotion fails
                logger.error(
                    f"Failed to auto-promote cleanup to primary: {str(promotion_error)}",
                    cleanup_id=str(cleaned_entry_id),
                    exc_info=True
                )

            # Auto-sync to Notion if enabled
            try:
                user = await db_service.get_user_by_id(db, user_id)
                if user and user.notion_enabled and user.notion_auto_sync and user.notion_api_key_encrypted:
                    logger.info(
                        f"Auto-sync enabled, triggering Notion sync",
                        user_id=user_id,
                        voice_entry_id=voice_entry_id
                    )

                    # Create sync record
                    sync_record = await db_service.create_notion_sync(
                        db=db,
                        user_id=user_id,
                        entry_id=voice_entry_id,
                        notion_database_id=user.notion_database_id,
                        status=NotionSyncStatus.PENDING
                    )
                    await db.commit()

                    # Trigger Notion sync in background
                    import asyncio
                    asyncio.create_task(process_notion_sync_background(
                        sync_id=sync_record.id,
                        user_id=user_id,
                        entry_id=voice_entry_id,
                        database_id=user.notion_database_id,
                        encrypted_api_key=user.notion_api_key_encrypted
                    ))

                    logger.info(
                        f"Notion sync triggered automatically",
                        sync_id=sync_record.id
                    )
            except Exception as sync_error:
                # Don't fail cleanup if auto-sync fails
                logger.error(
                    f"Failed to auto-sync to Notion: {str(sync_error)}",
                    exc_info=True
                )

        except Exception as e:
            logger.error(
                f"LLM cleanup failed for entry {cleaned_entry_id}: {str(e)}",
                exc_info=True
            )

            # Extract debug information from custom exception if available
            llm_raw_response = None
            prompt_template_id = None

            # Import here to avoid circular dependency
            from app.services.llm_cleanup_base import LLMCleanupError

            if isinstance(e, LLMCleanupError):
                llm_raw_response = e.llm_raw_response
                prompt_template_id = e.prompt_template_id
                logger.info(
                    f"Extracted debug info from LLMCleanupError",
                    has_raw_response=llm_raw_response is not None,
                    has_template_id=prompt_template_id is not None
                )

            # Update status to failed with debug information
            try:
                await db_service.update_cleaned_entry_processing(
                    db=db,
                    cleaned_entry_id=cleaned_entry_id,
                    cleanup_status=CleanupStatus.FAILED,
                    error_message=str(e),
                    llm_raw_response=llm_raw_response if settings.LLM_STORE_RAW_RESPONSE else None,
                    prompt_template_id=prompt_template_id
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
    request: CleanupTriggerRequest = CleanupTriggerRequest(),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
):
    """
    Trigger LLM cleanup for a completed transcription.

    The cleanup process:
    1. Validates that the transcription exists and is completed
    2. Creates a cleaned_entry record
    3. Starts background processing using the specified or configured LLM provider
    4. Returns immediately with cleanup ID and status

    Query the cleanup status using GET /api/v1/cleaned-entries/{cleanup_id}
    """
    # Validate and get effective LLM provider
    try:
        effective_llm_provider = get_effective_llm_provider(request.llm_provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get LLM service to obtain model name for database record
    llm_service = get_llm_service_for_provider(effective_llm_provider)
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

    # Get the voice entry to determine entry_type and for DEK lookup
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

    # Get the transcription text (always encrypted)
    transcription_text = await decrypt_text(
        encryption_service=encryption_service,
        db=db,
        encrypted_bytes=transcription.transcribed_text,
        voice_entry_id=voice_entry.id,
        user_id=current_user.id,
    )

    # Verify there's text to clean
    if not transcription_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcription has no text to clean"
        )

    # Create cleaned entry record
    # Determine cleanup model name in {provider}-{model} format
    if request.llm_model:
        # User specified a custom model
        cleanup_model_name = f"{effective_llm_provider}-{request.llm_model}"
    else:
        # Use default from service
        cleanup_model_name = llm_service.get_model_name()

    cleaned_entry = await db_service.create_cleaned_entry(
        db=db,
        voice_entry_id=voice_entry.id,
        transcription_id=transcription_id,
        user_id=current_user.id,
        model_name=cleanup_model_name,
        temperature=request.temperature,
        top_p=request.top_p
    )

    await db.commit()

    # Start background processing with decrypted text
    background_tasks.add_task(
        process_cleanup_background,
        cleaned_entry_id=cleaned_entry.id,
        transcription_text=transcription_text,
        entry_type=voice_entry.entry_type,
        user_id=current_user.id,
        voice_entry_id=voice_entry.id,
        temperature=request.temperature,
        top_p=request.top_p,
        llm_model=request.llm_model,
        llm_provider=effective_llm_provider
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
    db: AsyncSession = Depends(get_db),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
):
    """
    Get detailed information about a cleaned entry.

    Returns:
    - Cleanup status (pending, processing, completed, failed)
    - Cleaned text (when completed)
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

    # Decrypt cleaned text if encrypted
    decrypted_text = await decrypt_text(
        encryption_service=encryption_service,
        db=db,
        encrypted_bytes=cleaned_entry.cleaned_text,
        voice_entry_id=cleaned_entry.voice_entry_id,
        user_id=current_user.id,
    )

    return CleanedEntryDetail(
        id=cleaned_entry.id,
        voice_entry_id=cleaned_entry.voice_entry_id,
        transcription_id=cleaned_entry.transcription_id,
        user_id=cleaned_entry.user_id,
        cleaned_text=decrypted_text,
        llm_raw_response=cleaned_entry.llm_raw_response,
        status=cleaned_entry.status,
        model_name=cleaned_entry.model_name,
        temperature=cleaned_entry.temperature,
        top_p=cleaned_entry.top_p,
        error_message=cleaned_entry.error_message,
        is_primary=cleaned_entry.is_primary,
        processing_time_seconds=cleaned_entry.processing_time_seconds,
        created_at=cleaned_entry.created_at,
        processing_started_at=cleaned_entry.processing_started_at,
        processing_completed_at=cleaned_entry.processing_completed_at,
        prompt_template_id=cleaned_entry.prompt_template_id,
        prompt_name=cleaned_entry.prompt_template.name if cleaned_entry.prompt_template else None,
        prompt_description=cleaned_entry.prompt_template.description if cleaned_entry.prompt_template else None
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
    db: AsyncSession = Depends(get_db),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
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

    # Decrypt each entry (always encrypted)
    result = []
    for ce in cleaned_entries:
        decrypted_text = await decrypt_text(
            encryption_service=encryption_service,
            db=db,
            encrypted_bytes=ce.cleaned_text,
            voice_entry_id=ce.voice_entry_id,
            user_id=current_user.id,
        )
        result.append(CleanedEntryDetail(
            id=ce.id,
            voice_entry_id=ce.voice_entry_id,
            transcription_id=ce.transcription_id,
            user_id=ce.user_id,
            cleaned_text=decrypted_text,
            llm_raw_response=ce.llm_raw_response,
            status=ce.status,
            model_name=ce.model_name,
            temperature=ce.temperature,
            top_p=ce.top_p,
            error_message=ce.error_message,
            is_primary=ce.is_primary,
            processing_time_seconds=ce.processing_time_seconds,
            created_at=ce.created_at,
            processing_started_at=ce.processing_started_at,
            processing_completed_at=ce.processing_completed_at,
            prompt_template_id=ce.prompt_template_id,
            prompt_name=ce.prompt_template.name if ce.prompt_template else None,
            prompt_description=ce.prompt_template.description if ce.prompt_template else None
        ))
    return result


@router.put(
    "/cleaned-entries/{cleanup_id}/set-primary",
    response_model=CleanedEntryDetail,
    summary="Set cleanup as primary",
    description="Mark a cleanup as the primary one to display. Automatically unsets any existing primary cleanup for the same transcription."
)
async def set_primary_cleanup(
    cleanup_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service),
):
    """
    Set a cleanup as primary for its transcription.

    This allows users to choose which cleanup version (e.g., which prompt/model)
    should be displayed as the main entry in the UI.

    Args:
        cleanup_id: UUID of the cleanup to set as primary
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated cleanup with is_primary=True

    Raises:
        HTTPException: If cleanup not found, not owned by user, or not completed
    """
    # Get cleanup by ID and verify ownership
    cleanup = await db_service.get_cleaned_entry_by_id(
        db=db,
        cleaned_entry_id=cleanup_id,
        user_id=current_user.id
    )

    if not cleanup:
        logger.warning(
            f"Cleanup not found or not owned by user",
            cleanup_id=str(cleanup_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cleanup not found"
        )

    # Verify cleanup is completed
    if cleanup.status != CleanupStatus.COMPLETED:
        logger.warning(
            f"Cannot set non-completed cleanup as primary",
            cleanup_id=str(cleanup_id),
            status=cleanup.status
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot set primary cleanup with status '{cleanup.status}'. Cleanup must be completed."
        )

    # Set as primary
    updated_cleanup = await db_service.set_primary_cleanup(
        db=db,
        cleanup_id=cleanup_id
    )
    await db.commit()

    if not updated_cleanup:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set primary cleanup"
        )

    # Decrypt cleaned_text before returning
    # This is somewhat wasteful but it avoids separate GET request from the client
    decrypted_text = None
    if updated_cleanup.cleaned_text is not None:
        decrypted_text = await decrypt_text(
            encryption_service=encryption_service,
            db=db,
            encrypted_bytes=updated_cleanup.cleaned_text,
            voice_entry_id=updated_cleanup.voice_entry_id,
            user_id=current_user.id,
        )

    logger.info(
        f"Cleanup set as primary",
        cleanup_id=str(cleanup_id),
        transcription_id=str(updated_cleanup.transcription_id),
        user_id=str(current_user.id)
    )

    return CleanedEntryDetail(
        id=updated_cleanup.id,
        voice_entry_id=updated_cleanup.voice_entry_id,
        transcription_id=updated_cleanup.transcription_id,
        user_id=updated_cleanup.user_id,
        cleaned_text=decrypted_text,
        llm_raw_response=updated_cleanup.llm_raw_response,
        status=updated_cleanup.status,
        model_name=updated_cleanup.model_name,
        temperature=updated_cleanup.temperature,
        top_p=updated_cleanup.top_p,
        error_message=updated_cleanup.error_message,
        is_primary=updated_cleanup.is_primary,
        processing_time_seconds=updated_cleanup.processing_time_seconds,
        created_at=updated_cleanup.created_at,
        processing_started_at=updated_cleanup.processing_started_at,
        processing_completed_at=updated_cleanup.processing_completed_at,
        prompt_template_id=updated_cleanup.prompt_template_id,
        prompt_name=updated_cleanup.prompt_template.name if updated_cleanup.prompt_template else None,
        prompt_description=updated_cleanup.prompt_template.description if updated_cleanup.prompt_template else None
    )


@router.delete(
    "/cleaned-entries/{cleaned_entry_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete cleaned entry",
    description="Permanently delete a cleaned entry. No restrictions - any cleanup can be deleted.",
    responses={
        200: {"description": "Cleaned entry deleted successfully"},
        404: {"description": "Cleaned entry not found or not authorized"},
        500: {"description": "Server error"}
    }
)
async def delete_cleaned_entry(
    cleaned_entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
) -> DeleteResponse:
    """
    Permanently delete a cleaned entry with user ownership verification.

    Deletes:
    - Cleaned entry database record
    - NotionSync records referencing this cleanup (set to NULL via foreign key)

    Security:
    - Requires JWT authentication
    - Users can only delete their own cleaned entries
    - Returns 404 for both non-existent and unauthorized access

    Args:
        cleaned_entry_id: UUID of the cleaned entry to delete
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        DeleteResponse with success message and deleted entry ID

    Raises:
        HTTPException: 404 if entry not found or user doesn't own it
    """
    logger.info(
        "Cleaned entry deletion requested",
        cleaned_entry_id=str(cleaned_entry_id),
        user_id=str(current_user.id)
    )

    # Delete from database (validates ownership)
    deleted = await db_service.delete_cleaned_entry(db, cleaned_entry_id, current_user.id)

    if not deleted:
        logger.warning(
            "Cleaned entry not found or unauthorized for deletion",
            cleaned_entry_id=str(cleaned_entry_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cleaned entry not found"
        )

    # Commit database transaction
    await db.commit()

    logger.info(
        "Cleaned entry deleted successfully",
        cleaned_entry_id=str(cleaned_entry_id),
        user_id=str(current_user.id)
    )

    return DeleteResponse(
        message="Cleaned entry deleted successfully",
        deleted_id=cleaned_entry_id
    )
