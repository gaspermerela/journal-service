"""
API routes for Notion integration.

Handles:
- Notion configuration (connect, disconnect, settings)
- Manual sync triggers
- Sync status queries
"""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.jwt import get_current_user
from app.models.user import User
from app.models.notion_sync import SyncStatus
from app.schemas.notion import (
    NotionConfigureRequest,
    NotionConfigureResponse,
    NotionSettingsResponse,
    NotionDisconnectResponse,
    NotionSyncResponse,
    NotionSyncDetailResponse,
    NotionSyncListResponse
)
from app.services.encryption import encrypt_notion_key, decrypt_notion_key
from app.services.notion_service import NotionService, NotionValidationError, NotionAPIError
from app.services.database import db_service
from app.utils.logger import get_logger

logger = get_logger("notion_routes")
router = APIRouter()


# Configuration Endpoints

@router.post(
    "/configure",
    response_model=NotionConfigureResponse,
    status_code=status.HTTP_200_OK,
    summary="Configure Notion integration",
    description="Set up Notion integration by providing API key and database ID. "
                "Validates the database has required properties before saving."
)
async def configure_notion(
    request: NotionConfigureRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Configure Notion integration for the current user.

    Validates:
    - API key works
    - Database exists and is accessible
    - Database has required properties (Name, Date, Wake Time)

    Stores:
    - Encrypted API key
    - Database ID
    - Auto-sync preference
    """
    try:
        # Validate API key and database
        notion_service = NotionService(api_key=request.api_key)

        try:
            database = await notion_service.validate_database(request.database_id)
            database_title = database.get("title", [{}])[0].get("plain_text", "Unknown")

            logger.info(
                "Notion database validated",
                user_id=current_user.id,
                database_id=request.database_id,
                database_title=database_title
            )

        finally:
            await notion_service.close()

        # Encrypt API key
        encrypted_key = encrypt_notion_key(request.api_key, current_user.id)

        # Update user settings
        current_user.notion_api_key_encrypted = encrypted_key
        current_user.notion_database_id = request.database_id
        current_user.notion_enabled = True
        current_user.notion_auto_sync = request.auto_sync

        await db.commit()

        logger.info(
            "Notion integration configured",
            user_id=current_user.id,
            auto_sync=request.auto_sync
        )

        return NotionConfigureResponse(
            message="Notion integration configured successfully",
            database_title=database_title,
            auto_sync=request.auto_sync
        )

    except NotionValidationError as e:
        logger.warning(
            "Notion database validation failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotionAPIError as e:
        logger.error(
            "Notion API error during configuration",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Notion: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Unexpected error during Notion configuration",
            user_id=current_user.id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure Notion integration"
        )


@router.get(
    "/settings",
    response_model=NotionSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Notion settings",
    description="Retrieve current Notion integration settings for the user."
)
async def get_notion_settings(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current Notion integration settings."""
    return NotionSettingsResponse(
        enabled=current_user.notion_enabled,
        database_id=current_user.notion_database_id,
        auto_sync=current_user.notion_auto_sync,
        has_api_key=bool(current_user.notion_api_key_encrypted)
    )


@router.delete(
    "/disconnect",
    response_model=NotionDisconnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Disconnect Notion integration",
    description="Remove Notion integration configuration and delete encrypted API key."
)
async def disconnect_notion(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Disconnect Notion integration for the current user."""
    # Clear Notion settings
    current_user.notion_api_key_encrypted = None
    current_user.notion_database_id = None
    current_user.notion_enabled = False
    current_user.notion_auto_sync = False

    await db.commit()

    logger.info(
        "Notion integration disconnected",
        user_id=current_user.id
    )

    return NotionDisconnectResponse(
        message="Notion integration disconnected successfully"
    )


# Sync Endpoints

async def process_notion_sync_background(
    sync_id: UUID,
    user_id: UUID,
    entry_id: UUID,
    database_id: str,
    encrypted_api_key: str
):
    """
    Background task to sync dream to Notion.

    Args:
        sync_id: NotionSync record ID
        user_id: User ID (for decryption)
        entry_id: Voice entry ID to sync
        database_id: Notion database ID
        encrypted_api_key: Encrypted Notion API key
    """
    from app.database import get_session

    async with get_session() as db:
        try:
            # Update status to processing
            await db_service.update_notion_sync_status(
                db=db,
                sync_id=sync_id,
                status=SyncStatus.PROCESSING
            )
            await db.commit()

            logger.info(
                "Starting Notion sync",
                sync_id=sync_id,
                entry_id=entry_id
            )

            # Get voice entry with latest cleaned entry
            voice_entry = await db_service.get_entry_by_id(db, entry_id, user_id)
            if not voice_entry:
                raise ValueError(f"Voice entry {entry_id} not found")

            # Get latest cleaned entry
            cleaned_entry = await db_service.get_latest_cleaned_entry(db, entry_id)
            if not cleaned_entry or not cleaned_entry.cleaned_text:
                raise ValueError(f"No cleaned text available for entry {entry_id}")

            # Decrypt API key
            api_key = decrypt_notion_key(encrypted_api_key, user_id)

            # Create Notion service
            notion_service = NotionService(api_key=api_key)

            try:
                # Create dream page
                page = await notion_service.create_dream_page(
                    database_id=database_id,
                    dream_content=cleaned_entry.cleaned_text,
                    uploaded_at=voice_entry.uploaded_at,
                    dream_name="Dream"  # Phase 5: hardcoded
                )

                # Update sync record with success
                await db_service.update_notion_sync_status(
                    db=db,
                    sync_id=sync_id,
                    status=SyncStatus.COMPLETED,
                    notion_page_id=page["id"],
                    cleaned_entry_id=cleaned_entry.id
                )
                await db.commit()

                logger.info(
                    "Notion sync completed",
                    sync_id=sync_id,
                    page_id=page["id"],
                    page_url=page.get("url")
                )

            finally:
                await notion_service.close()

        except Exception as e:
            logger.error(
                "Notion sync failed",
                sync_id=sync_id,
                error=str(e),
                exc_info=True
            )

            # Update sync record with failure
            try:
                # Increment retry count
                sync_record = await db_service.get_notion_sync_by_id(db, sync_id)
                new_retry_count = sync_record.retry_count + 1 if sync_record else 0

                # Determine if we should retry
                from app.config import settings
                should_retry = new_retry_count < settings.NOTION_MAX_RETRIES

                await db_service.update_notion_sync_status(
                    db=db,
                    sync_id=sync_id,
                    status=SyncStatus.RETRYING if should_retry else SyncStatus.FAILED,
                    error_message=str(e),
                    retry_count=new_retry_count
                )
                await db.commit()

            except Exception as update_error:
                logger.error(
                    "Failed to update sync status",
                    sync_id=sync_id,
                    error=str(update_error)
                )


@router.post(
    "/sync/{entry_id}",
    response_model=NotionSyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Manually sync entry to Notion",
    description="Trigger manual sync of a voice entry to Notion. "
                "Requires Notion integration to be configured."
)
async def sync_entry_to_notion(
    entry_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks
):
    """
    Manually trigger sync of a voice entry to Notion.

    Requires:
    - Notion integration configured
    - Voice entry exists and belongs to user
    - Cleaned text available for entry
    """
    # Check Notion is configured
    if not current_user.notion_enabled or not current_user.notion_api_key_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notion integration is not configured. Please configure it first."
        )

    # Verify entry exists and belongs to user
    # First check if entry exists at all (without user filter)
    voice_entry = await db_service.get_entry_by_id(db, entry_id, None)
    if not voice_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice entry {entry_id} not found"
        )

    # Then check ownership
    if voice_entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to sync this entry"
        )

    # Check if cleaned text exists
    cleaned_entry = await db_service.get_latest_cleaned_entry(db, entry_id)
    if not cleaned_entry or not cleaned_entry.cleaned_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No cleaned text available for this entry. Please run cleanup first."
        )

    # Create sync record
    sync_record = await db_service.create_notion_sync(
        db=db,
        user_id=current_user.id,
        entry_id=entry_id,
        notion_database_id=current_user.notion_database_id,
        status=SyncStatus.PENDING
    )
    await db.commit()

    # Trigger background sync
    background_tasks.add_task(
        process_notion_sync_background,
        sync_id=sync_record.id,
        user_id=current_user.id,
        entry_id=entry_id,
        database_id=current_user.notion_database_id,
        encrypted_api_key=current_user.notion_api_key_encrypted
    )

    logger.info(
        "Notion sync triggered",
        sync_id=sync_record.id,
        entry_id=entry_id,
        user_id=current_user.id
    )

    return NotionSyncResponse(
        sync_id=sync_record.id,
        entry_id=entry_id,
        status=SyncStatus.PENDING.value,
        message="Sync started in background",
        notion_page_id=None,
        notion_page_url=None
    )


@router.get(
    "/sync/{sync_id}",
    response_model=NotionSyncDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sync status",
    description="Retrieve detailed status of a specific sync operation."
)
async def get_sync_status(
    sync_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get detailed status of a specific sync operation."""
    sync_record = await db_service.get_notion_sync_by_id(db, sync_id)

    if not sync_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync record {sync_id} not found"
        )

    # Verify ownership
    if sync_record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this sync record"
        )

    return NotionSyncDetailResponse.model_validate(sync_record)


@router.get(
    "/syncs",
    response_model=NotionSyncListResponse,
    status_code=status.HTTP_200_OK,
    summary="List sync records",
    description="Retrieve list of all sync records for the current user."
)
async def list_syncs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0
):
    """List all sync records for the current user."""
    syncs = await db_service.get_notion_syncs_by_user(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

    total = await db_service.count_notion_syncs_by_user(db=db, user_id=current_user.id)

    return NotionSyncListResponse(
        syncs=[NotionSyncDetailResponse.model_validate(s) for s in syncs],
        total=total
    )
