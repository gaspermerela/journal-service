"""
Health check endpoint for monitoring.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.schemas.dream_entry import HealthResponse
from app.database import check_db_connection
from app.utils.logger import get_logger

logger = get_logger("health")
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check application and database health status",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Checks:
    - Application is running
    - Database connection is working

    Returns:
        HealthResponse with status and timestamp
    """
    # Check database connection
    db_healthy = await check_db_connection()

    if db_healthy:
        logger.debug("Health check: all systems operational")
        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.now(timezone.utc)
        )
    else:
        logger.warning("Health check: database connection failed")
        return HealthResponse(
            status="degraded",
            database="disconnected",
            timestamp=datetime.now(timezone.utc)
        )
