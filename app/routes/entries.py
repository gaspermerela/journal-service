"""
Entries endpoint for retrieving dream entry metadata.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dream_entry import DreamEntryResponse
from app.services.database import db_service
from app.utils.logger import get_logger

logger = get_logger("entries")
router = APIRouter()


@router.get(
    "/entries/{entry_id}",
    response_model=DreamEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dream entry",
    description="Retrieve metadata for a specific dream entry by ID",
    responses={
        200: {"description": "Entry found"},
        404: {"description": "Entry not found"},
        500: {"description": "Server error"}
    }
)
async def get_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DreamEntryResponse:
    """
    Get dream entry by ID.

    Args:
        entry_id: UUID of the entry to retrieve
        db: Database session

    Returns:
        DreamEntryResponse with entry metadata

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

    logger.info(f"Entry retrieved successfully", entry_id=str(entry_id))

    return DreamEntryResponse(
        id=entry.id,
        original_filename=entry.original_filename,
        saved_filename=entry.saved_filename,
        file_path=entry.file_path,
        uploaded_at=entry.uploaded_at
    )
