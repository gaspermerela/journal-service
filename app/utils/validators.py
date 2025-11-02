"""
File validation utilities.
"""
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("validators")

ALLOWED_CONTENT_TYPES = ["audio/mpeg", "audio/mp3"]
ALLOWED_EXTENSIONS = [".mp3"]


async def validate_audio_file(file: UploadFile) -> None:
    """
    Validate uploaded audio file.

    Checks:
    - File is present
    - File has correct extension
    - File has correct content type
    - File size is within limits

    Args:
        file: Uploaded file from FastAPI

    Raises:
        HTTPException: If validation fails
    """
    # Check if file is present
    if not file:
        logger.warning("Upload attempt with no file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Check filename
    if not file.filename:
        logger.warning("Upload attempt with no filename")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Check file extension
    file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(
            f"Invalid file type attempted",
            filename=file.filename,
            extension=file_ext
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
        )

    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            f"Invalid content type",
            filename=file.filename,
            content_type=file.content_type
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Expected audio/mpeg or audio/mp3"
        )

    # Check file size
    # Read file to check size, then reset position
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)  # Reset file position for later reading

    if file_size > settings.max_file_size_bytes:
        logger.warning(
            f"File too large",
            filename=file.filename,
            size_bytes=file_size,
            max_bytes=settings.max_file_size_bytes
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    if file_size == 0:
        logger.warning(f"Empty file uploaded", filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    logger.info(
        f"File validation successful",
        filename=file.filename,
        size_bytes=file_size
    )
