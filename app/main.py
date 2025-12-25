"""
Main FastAPI application for AI Journal Backend Service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_db_connection
from app.routes import upload, health, entries, transcription, auth, cleanup, notion, user_preferences, models
from app.middleware.logging import RequestLoggingMiddleware
from app.services.envelope_encryption import create_envelope_encryption_service
from app.services.provider_registry import (
    get_available_transcription_providers,
    get_available_llm_providers,
)
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

    # Validate default providers are configured (required - app fails without them)
    from app.services.provider_registry import get_effective_transcription_provider, get_effective_llm_provider
    try:
        get_effective_transcription_provider(None)
        logger.info(f"Default transcription provider '{settings.DEFAULT_TRANSCRIPTION_PROVIDER}' is configured")
    except ValueError as e:
        raise RuntimeError(str(e)) from e

    try:
        get_effective_llm_provider(None)
        logger.info(f"Default LLM provider '{settings.DEFAULT_LLM_PROVIDER}' is configured")
    except ValueError as e:
        raise RuntimeError(str(e)) from e

    logger.info(f"Available transcription providers: {get_available_transcription_providers()}")
    logger.info(f"Available LLM providers: {get_available_llm_providers()}")

    # Store default provider names in app.state for backwards compatibility
    app.state.default_transcription_provider = settings.DEFAULT_TRANSCRIPTION_PROVIDER
    app.state.default_llm_provider = settings.DEFAULT_LLM_PROVIDER

    # Initialize envelope encryption service (required - app fails without it)
    logger.info(f"Initializing encryption service with provider: {settings.ENCRYPTION_PROVIDER}")
    try:
        app.state.encryption_service = create_envelope_encryption_service(
            provider=settings.ENCRYPTION_PROVIDER
        )
        logger.info(f"Envelope encryption service initialized: provider={settings.ENCRYPTION_PROVIDER}")
    except Exception as e:
        logger.error(f"Failed to initialize encryption service: {e}", exc_info=True)
        raise RuntimeError(f"Cannot start application without encryption service: {e}") from e

    # Initialize Slovenian spell-check service (optional - graceful degradation)
    if settings.SPELLCHECK_ENABLED:
        from app.services.spellcheck import initialize_slovenian_spellcheck
        try:
            if initialize_slovenian_spellcheck():
                logger.info("Slovenian spell-check service initialized")
            else:
                logger.warning("Slovenian spell-check service failed to initialize (spell-check disabled)")
        except Exception as e:
            logger.warning(f"Spell-check initialization error (disabled): {e}")
    else:
        logger.info("Spell-check service disabled via configuration")

    yield

    # Shutdown
    logger.info("Shutting down AI Journal Backend Service")
    app.state.encryption_service = None
    logger.info("Encryption service cleaned up")


# Create FastAPI application
app = FastAPI(
    title="AI Journal Backend Service",
    description="Backend service for voice-based dream journaling with audio file uploads",
    version="0.2.0",
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
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)
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
app.include_router(
    transcription.router,
    prefix="/api/v1",
    tags=["Transcription"]
)
app.include_router(
    cleanup.router,
    prefix="/api/v1",
    tags=["Cleanup"]
)
app.include_router(
    notion.router,
    prefix="/api/v1/notion",
    tags=["Notion"]
)
app.include_router(
    user_preferences.router,
    prefix="/api/v1/user",
    tags=["User Preferences"]
)
app.include_router(
    models.router,
    tags=["Models"]
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
