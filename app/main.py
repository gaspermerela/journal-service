"""
Main FastAPI application for AI Journal Backend Service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_db_connection
from app.routes import upload, health, entries
from app.middleware.logging import RequestLoggingMiddleware
from app.utils.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI Journal Backend Service")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")

    # Check database connection
    db_connected = await check_db_connection()
    if db_connected:
        logger.info("Database connection established")
    else:
        logger.error("Failed to connect to database")

    # Create storage directory if it doesn't exist
    from pathlib import Path
    storage_path = Path(settings.AUDIO_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Storage path configured: {settings.AUDIO_STORAGE_PATH}")

    yield

    # Shutdown
    logger.info("Shutting down AI Journal Backend Service")


# Create FastAPI application
app = FastAPI(
    title="AI Journal Backend Service",
    description="Backend service for voice-based dream journaling with audio file uploads",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(
    upload.router,
    prefix="/api/v1",
    tags=["Upload"]
)
app.include_router(
    entries.router,
    prefix="/api/v1",
    tags=["Entries"]
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "AI Journal Backend Service",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
