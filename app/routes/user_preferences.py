"""
API routes for user preferences management.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.middleware.jwt import get_current_user
from app.schemas.user_preferences import UserPreferencesResponse, UserPreferencesUpdate
from app.services.database import DatabaseService
from app.utils.logger import get_logger

logger = get_logger("user_preferences_routes")

router = APIRouter()
db_service = DatabaseService()


@router.get(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="Get user preferences",
    description="Retrieve current user's preferences. Creates default preferences if they don't exist."
)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's preferences.

    If the user doesn't have preferences yet, default preferences will be created automatically.

    Args:
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        UserPreferencesResponse with user's current preferences

    Raises:
        HTTPException: If database operation fails
    """
    logger.info(f"Getting preferences", user_id=str(current_user.id))

    preferences = await db_service.get_user_preferences(db, current_user.id)
    await db.commit()

    logger.info(
        f"User preferences retrieved",
        user_id=str(current_user.id),
        language=preferences.preferred_transcription_language
    )

    return UserPreferencesResponse.model_validate(preferences)


@router.put(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="Update user preferences",
    description="Update current user's preferences. Only provided fields will be updated."
)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's preferences.

    Only the fields provided in the request body will be updated.
    Other fields will remain unchanged.

    Args:
        preferences_data: Preferences data to update
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        UserPreferencesResponse with updated preferences

    Raises:
        HTTPException: If validation fails or database operation fails
    """
    logger.info(
        f"Updating preferences",
        user_id=str(current_user.id),
        language=preferences_data.preferred_transcription_language,
        encryption_enabled=preferences_data.encryption_enabled
    )

    preferences = await db_service.update_user_preferences(
        db,
        current_user.id,
        preferred_transcription_language=preferences_data.preferred_transcription_language,
        preferred_llm_model=preferences_data.preferred_llm_model,
        encryption_enabled=preferences_data.encryption_enabled,
    )
    await db.commit()

    logger.info(
        f"User preferences updated successfully",
        user_id=str(current_user.id),
        language=preferences.preferred_transcription_language,
        encryption_enabled=preferences.encryption_enabled
    )

    return UserPreferencesResponse.model_validate(preferences)
