"""
Entries endpoint for retrieving voice entry metadata.
"""
import os
import re
from pathlib import Path
from uuid import UUID
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.voice_entry import (
    VoiceEntryResponse,
    VoiceEntryListResponse,
    VoiceEntrySummary,
    TranscriptionSummary,
    CleanedEntrySummary,
    DeleteResponse
)
from app.schemas.transcription import TranscriptionResponse
from app.services.database import db_service
from app.services.storage import storage_service
from app.services.envelope_encryption import (
    EnvelopeEncryptionService,
    get_encryption_service,
)
from app.middleware.jwt import get_current_user
from app.utils.encryption_helpers import (
    decrypt_text,
    decrypt_json,
    decrypt_audio_to_temp,
    cleanup_temp_file,
)
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
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
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

        # Get primary cleaned entry (or fallback to latest if no primary)
        latest_cleaned = None
        if entry.cleaned_entries:
            # Try to find primary cleanup first
            primary_cleanup = next((c for c in entry.cleaned_entries if c.is_primary), None)

            # Fallback to latest by created_at if no primary exists
            if not primary_cleanup:
                sorted_cleaned = sorted(entry.cleaned_entries, key=lambda c: c.created_at, reverse=True)
                primary_cleanup = sorted_cleaned[0]

            # Create text preview (first 200 chars), decrypt the encrypted data
            text_preview = None

            # TODO: lots of DB calls for encrypted DEK key, optimise with batching
            # Decrypt cleaned_text (always encrypted)
            cleaned_text = await decrypt_text(
                encryption_service=encryption_service,
                db=db,
                encrypted_bytes=primary_cleanup.cleaned_text,
                voice_entry_id=entry.id,
                user_id=current_user.id,
            )

            if cleaned_text:
                text_preview = cleaned_text[:200]

            # TODO: lots of DB calls for encrypted DEK key, optimise with batching
            # Decrypt analysis (always encrypted)
            analysis = await decrypt_json(
                encryption_service=encryption_service,
                db=db,
                encrypted_bytes=primary_cleanup.analysis,
                voice_entry_id=entry.id,
                user_id=current_user.id,
            )

            latest_cleaned = CleanedEntrySummary(
                id=primary_cleanup.id,
                status=primary_cleanup.status.value,  # Convert enum to string
                cleaned_text_preview=text_preview,
                analysis=analysis,
                error_message=primary_cleanup.error_message,
                created_at=primary_cleanup.created_at
            )

        entry_summaries.append(
            VoiceEntrySummary(
                id=entry.id,
                original_filename=entry.original_filename,
                saved_filename=entry.saved_filename,
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
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
) -> VoiceEntryResponse:
    """
    Get voice entry by ID (user can only access their own entries).

    Args:
        entry_id: UUID of the entry to retrieve
        db: Database session
        current_user: Authenticated user from JWT token
        encryption_service: Encryption service for decrypting transcription

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
        # Decrypt the transcribed_text before creating response
        decrypted_text = await decrypt_text(
            encryption_service=encryption_service,
            db=db,
            encrypted_bytes=primary_transcription.transcribed_text,
            voice_entry_id=entry_id,
            user_id=current_user.id,
        )

        primary_transcription_data = TranscriptionResponse(
            id=primary_transcription.id,
            entry_id=primary_transcription.entry_id,
            status=primary_transcription.status,
            model_used=primary_transcription.model_used,
            language_code=primary_transcription.language_code,
            beam_size=primary_transcription.beam_size,
            temperature=primary_transcription.temperature,
            transcribed_text=decrypted_text,
            transcription_started_at=primary_transcription.transcription_started_at,
            transcription_completed_at=primary_transcription.transcription_completed_at,
            error_message=primary_transcription.error_message,
            is_primary=primary_transcription.is_primary,
            created_at=primary_transcription.created_at,
            updated_at=primary_transcription.updated_at,
        )
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
        duration_seconds=entry.duration_seconds,
        entry_type=entry.entry_type,
        uploaded_at=entry.uploaded_at,
        primary_transcription=primary_transcription_data
    )


def _sanitize_filename(filename: str) -> str:
    """
    Remove any characters that could break Content-Disposition header.
    Keeps only alphanumeric, dots, hyphens, underscores, and spaces.
    """
    return re.sub(r'[^\w\s.-]', '', filename)


@router.get(
    "/entries/{entry_id}/audio",
    status_code=status.HTTP_200_OK,
    summary="Download entry audio file",
    description="Download the audio file for a specific voice entry. Returns preprocessed WAV format.",
    responses={
        200: {"description": "Audio file", "content": {"audio/wav": {}}},
        404: {"description": "Entry not found or audio file unavailable"},
        401: {"description": "Not authenticated"}
    }
)
async def get_entry_audio(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
):
    """
    Download audio file for a voice entry.

    Security:
    - Requires JWT authentication
    - Users can only download their own audio files
    - Returns 404 for both non-existent entries and unauthorized access
      (to avoid leaking information about which entry IDs exist)
    - Encrypted files are decrypted transparently before serving

    Technical details:
    - All audio files are preprocessed to 16kHz mono WAV format
    - Supports range requests for seeking in audio players
    - Files are cached for 1 hour with 'immutable' directive

    Args:
        entry_id: UUID of the entry
        db: Database session
        current_user: Authenticated user from JWT token
        encryption_service: Envelope encryption service for decryption

    Returns:
        FileResponse with audio file

    Raises:
        HTTPException: 404 if entry not found, user doesn't own it, or file missing
    """
    logger.info(
        "Audio download requested",
        entry_id=str(entry_id),
        user_id=str(current_user.id)
    )

    # Retrieve entry from database (filtered by user_id)
    entry = await db_service.get_entry_by_id(db, entry_id, current_user.id)

    if not entry:
        # Return 404 for both "not found" and "unauthorized" to avoid
        # leaking information about which entry IDs exist
        logger.warning(
            "Entry not found or unauthorized",
            entry_id=str(entry_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # Check if file exists on disk
    if not os.path.exists(entry.file_path):
        logger.error(
            "Audio file missing on disk (data integrity issue)",
            entry_id=str(entry_id),
            file_path=entry.file_path,
            user_id=str(current_user.id)
        )
        # Return 404 to client, but log as critical server issue
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not available"
        )

    # Sanitize filename for Content-Disposition header
    safe_filename = _sanitize_filename(entry.original_filename)

    # Change extension to .wav since all files are preprocessed to WAV format
    filename_base = safe_filename.rsplit('.', 1)[0] if '.' in safe_filename else safe_filename
    download_filename = f"{filename_base}.wav"

    # If file is encrypted, decrypt to temp file and serve
    if entry.is_encrypted:
        logger.info(
            "Decrypting encrypted audio file",
            entry_id=str(entry_id),
            user_id=str(current_user.id)
        )

        temp_decrypted_path = await decrypt_audio_to_temp(
            encryption_service=encryption_service,
            db=db,
            encrypted_file_path=entry.file_path,
            voice_entry_id=entry.id,
            user_id=current_user.id
        )

        if not temp_decrypted_path:
            logger.error(
                "Failed to decrypt audio file",
                entry_id=str(entry_id),
                user_id=str(current_user.id)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cannot decrypt audio file"
            )

        # Stream the decrypted file and clean up after
        async def stream_and_cleanup():
            try:
                with open(temp_decrypted_path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk
            finally:
                cleanup_temp_file(temp_decrypted_path)

        return StreamingResponse(
            stream_and_cleanup(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'inline; filename="{download_filename}"',
                "Cache-Control": "private, no-store",  # Don't cache decrypted content
            }
        )

    logger.info(
        "Serving audio file",
        entry_id=str(entry_id),
        file_path=entry.file_path,
        user_id=str(current_user.id)
    )

    # Return audio file with proper headers
    # All files are preprocessed to 16kHz mono WAV format
    return FileResponse(
        path=entry.file_path,
        media_type="audio/wav",
        filename=download_filename,
        headers={
            "Accept-Ranges": "bytes",  # Enable seeking in audio players
            "Cache-Control": "private, max-age=3600, immutable",  # Cache for 1 hour
            "Content-Disposition": f'inline; filename="{download_filename}"'  # Play in browser
        }
    )


@router.delete(
    "/entries/{entry_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete voice entry",
    description="Permanently delete a voice entry and all associated data (transcriptions, cleaned entries, notion syncs, audio file)",
    responses={
        200: {"description": "Entry deleted successfully"},
        404: {"description": "Entry not found or not authorized"},
        500: {"description": "Server error"}
    }
)
async def delete_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeleteResponse:
    """
    Permanently delete a voice entry with user ownership verification.

    Deletes:
    - Voice entry database record
    - All transcriptions (cascaded)
    - All cleaned entries (cascaded)
    - All notion sync records (cascaded)
    - Audio file from storage (best effort)

    Security:
    - Requires JWT authentication
    - Users can only delete their own entries
    - Returns 404 for both non-existent entries and unauthorized access

    Args:
        entry_id: UUID of the entry to delete
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        DeleteResponse with success message and deleted entry ID

    Raises:
        HTTPException: 404 if entry not found or user doesn't own it
    """
    logger.info(
        "Entry deletion requested",
        entry_id=str(entry_id),
        user_id=str(current_user.id)
    )

    # Delete from database (returns file_path if found, None if not found)
    file_path = await db_service.delete_entry(db, entry_id, current_user.id)

    if file_path is None:
        logger.warning(
            "Entry not found or unauthorized for deletion",
            entry_id=str(entry_id),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )

    # Commit database transaction
    await db.commit()

    # Attempt to delete audio file (best effort)
    if file_path:
        file_deleted = await storage_service.delete_file(file_path)
        if not file_deleted:
            logger.critical(
                "Failed to delete audio file after DB deletion (orphaned file)",
                entry_id=str(entry_id),
                file_path=file_path,
                user_id=str(current_user.id)
            )
            # Continue - DB deletion succeeded, file cleanup can be done manually

    logger.info(
        "Entry deleted successfully",
        entry_id=str(entry_id),
        user_id=str(current_user.id),
        file_deleted=file_path is not None
    )

    return DeleteResponse(
        message="Entry deleted successfully",
        deleted_id=entry_id
    )
