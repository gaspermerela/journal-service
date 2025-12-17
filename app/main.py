"""
Main FastAPI application for AI Journal Backend Service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import whisper

from app.config import settings
from app.database import check_db_connection
from app.routes import upload, health, entries, transcription, auth, cleanup, notion, user_preferences, models
from app.middleware.logging import RequestLoggingMiddleware
from app.services.transcription import create_transcription_service
from app.services.llm_cleanup import create_llm_cleanup_service
from app.services.envelope_encryption import create_envelope_encryption_service
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

    # Initialize transcription service based on provider
    logger.info(f"Initializing transcription service with provider: {settings.TRANSCRIPTION_PROVIDER}")
    try:
        if settings.TRANSCRIPTION_PROVIDER.lower() == "whisper":
            # Load local Whisper model
            logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
            whisper_model = whisper.load_model(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE
            )
            logger.info(
                f"Whisper model loaded successfully: "
                f"model={settings.WHISPER_MODEL}, device={settings.WHISPER_DEVICE}"
            )

            # Create local Whisper transcription service
            app.state.transcription_service = create_transcription_service(
                provider="whisper",
                model=whisper_model,
                model_name=settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                num_threads=settings.TORCH_NUM_THREADS
            )
            logger.info("Local Whisper transcription service initialized")

        elif settings.TRANSCRIPTION_PROVIDER.lower() == "groq":
            # Create Groq API transcription service
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is required when TRANSCRIPTION_PROVIDER is 'groq'")

            app.state.transcription_service = create_transcription_service(
                provider="groq",
                model_name=settings.GROQ_TRANSCRIPTION_MODEL,
                api_key=settings.GROQ_API_KEY
            )
            logger.info(
                f"Groq transcription service initialized: model={settings.GROQ_TRANSCRIPTION_MODEL}"
            )

        elif settings.TRANSCRIPTION_PROVIDER.lower() == "assemblyai":
            # Create AssemblyAI API transcription service
            if not settings.ASSEMBLYAI_API_KEY:
                raise ValueError("ASSEMBLYAI_API_KEY is required when TRANSCRIPTION_PROVIDER is 'assemblyai'")

            app.state.transcription_service = create_transcription_service(
                provider="assemblyai",
                model_name=settings.ASSEMBLYAI_MODEL,
                api_key=settings.ASSEMBLYAI_API_KEY
            )
            logger.info(
                f"AssemblyAI transcription service initialized: model={settings.ASSEMBLYAI_MODEL}"
            )

        elif settings.TRANSCRIPTION_PROVIDER.lower() == "clarinsi_slovene_asr":
            # Create RunPod API transcription service (Slovenian RSDO model)
            if not settings.RUNPOD_API_KEY:
                raise ValueError("RUNPOD_API_KEY is required when TRANSCRIPTION_PROVIDER is 'runpod'")
            if not settings.RUNPOD_ENDPOINT_ID:
                raise ValueError("RUNPOD_ENDPOINT_ID is required when TRANSCRIPTION_PROVIDER is 'runpod'")

            app.state.transcription_service = create_transcription_service(
                provider="clarinsi_slovene_asr",
                model_name=settings.RUNPOD_MODEL,
                api_key=settings.RUNPOD_API_KEY,
                endpoint_id=settings.RUNPOD_ENDPOINT_ID
            )
            logger.info(
                f"RunPod transcription service initialized: model={settings.RUNPOD_MODEL}, "
                f"endpoint_id={settings.RUNPOD_ENDPOINT_ID}"
            )

        else:
            raise ValueError(
                f"Unsupported TRANSCRIPTION_PROVIDER: {settings.TRANSCRIPTION_PROVIDER}. "
                f"Supported: whisper, groq, assemblyai, runpod"
            )

    except Exception as e:
        logger.error(f"Failed to initialize transcription service: {e}", exc_info=True)
        raise RuntimeError(f"Cannot start application without transcription service: {e}") from e

    # Initialize LLM cleanup service
    logger.info(f"Initializing LLM cleanup service with provider: {settings.LLM_PROVIDER}")
    try:
        app.state.llm_cleanup_service = create_llm_cleanup_service(
            provider=settings.LLM_PROVIDER,
            db_session=None  # DB session will be injected per-request
        )
        logger.info(f"LLM cleanup service initialized: provider={settings.LLM_PROVIDER}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM cleanup service: {e}", exc_info=True)
        raise RuntimeError(f"Cannot start application without LLM cleanup service: {e}") from e

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

    yield

    # Shutdown
    logger.info("Shutting down AI Journal Backend Service")
    app.state.transcription_service = None
    logger.info("Transcription service cleaned up")
    app.state.llm_cleanup_service = None
    logger.info("LLM cleanup service cleaned up")
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
