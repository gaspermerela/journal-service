"""
Health check endpoint for monitoring.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.voice_entry import HealthResponse
from app.database import get_db
from app.utils.logger import get_logger

logger = get_logger("health")
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check application and database health status",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.

    Checks:
    - Application is running
    - Database connection is working

    Returns:
        HealthResponse with status and timestamp (200 if healthy, 503 if not)
    """
    # Check database connection by executing a simple query
    try:
        await db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False

    if db_healthy:
        logger.debug("Health check: all systems operational")
        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.now(timezone.utc)
        )
    else:
        logger.warning("Health check: database connection failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "degraded",
                "database": "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
