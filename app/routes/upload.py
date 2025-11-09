"""
Upload endpoint for audio file uploads.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.voice_entry import VoiceEntryCreate, VoiceEntryUploadResponse
from app.services.storage import storage_service
from app.services.database import db_service
from app.utils.validators import validate_audio_file
from app.utils.logger import get_logger

logger = get_logger("upload")
router = APIRouter()


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
    db: AsyncSession = Depends(get_db)
) -> VoiceEntryUploadResponse:
    """
    Upload audio file endpoint.

    Process:
    1. Validate file (type, size, extension)
    2. Generate UUID for entry
    3. Save file to disk
    4. Create database entry with specified entry_type
    5. Return entry metadata

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

        # Step 3: Create database entry
        entry_data = VoiceEntryCreate(
            original_filename=file.filename,
            saved_filename=saved_filename,
            file_path=file_path,
            entry_type=entry_type,
            uploaded_at=datetime.now(timezone.utc)
        )

        entry = await db_service.create_entry(db, entry_data)

        # Step 4: Commit transaction (handled by get_db dependency)
        await db.commit()

        logger.info(
            f"File upload completed successfully",
            entry_id=str(entry.id),
            filename=file.filename,
            saved_as=saved_filename
        )

        # Return response
        return VoiceEntryUploadResponse(
            id=entry.id,
            original_filename=entry.original_filename,
            saved_filename=entry.saved_filename,
            file_path=entry.file_path,
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
