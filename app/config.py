"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "postgres"
    DATABASE_USER: str = "journal_user"
    DATABASE_PASSWORD: str  # Required - no default for security
    DB_SCHEMA: str = "journal"  # Schema name for all tables (use "journal_test" for tests)

    # Application Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Storage Configuration
    AUDIO_STORAGE_PATH: str = "/app/data/audio"
    MAX_FILE_SIZE_MB: int = 100

    # Transcription Configuration
    TRANSCRIPTION_PROVIDER: str = "groq"  # Options: groq, assemblyai, clarin-slovene-asr

    # Audio Preprocessing Configuration
    ENABLE_AUDIO_PREPROCESSING: bool = True  # Enable ffmpeg preprocessing pipeline
    PREPROCESSING_SAMPLE_RATE: int = 16000  # Target sample rate (16kHz recommended for Whisper)
    PREPROCESSING_HIGHPASS_FREQ: int = 60  # High-pass filter frequency in Hz
    PREPROCESSING_LOUDNORM_I: int = -16  # Integrated loudness target (LUFS)
    PREPROCESSING_LOUDNORM_TP: float = -1.5  # True peak target (dBTP)
    PREPROCESSING_LOUDNORM_LRA: int = 11  # Loudness range target (LU)
    PREPROCESSING_SILENCE_THRESHOLD: str = "-80dB"  # Silence detection threshold
    PREPROCESSING_SILENCE_DURATION: float = 0.5  # Minimum silence duration in seconds

    # LLM Cleanup Configuration
    LLM_PROVIDER: str = "groq"  # Options: groq (API), runpod_llm_gams (Slovenian GaMS on RunPod)
    LLM_TIMEOUT_SECONDS: int = 120
    LLM_MAX_RETRIES: int = 2

    # Groq API Configuration (for both transcription and LLM)
    GROQ_API_KEY: Optional[str] = None  # Required when using Groq provider
    GROQ_TRANSCRIPTION_MODEL: str = "whisper-large-v3"  # Groq's Whisper model
    GROQ_LLM_MODEL: str = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Groq's chat model

    # AssemblyAI API Configuration
    ASSEMBLYAI_API_KEY: Optional[str] = None  # Required when using AssemblyAI provider
    ASSEMBLYAI_MODEL: str = "universal"
    ASSEMBLYAI_POLL_INTERVAL: float = 3.0  # Seconds between status polls
    ASSEMBLYAI_TIMEOUT: int = 1000  # Max seconds to wait for transcription
    ASSEMBLYAI_AUTO_DELETE: bool = True  # Auto-delete transcript after extraction (GDPR compliance)

    # RunPod API Configuration (for Slovenian transcription using PROTOVERB model)
    RUNPOD_API_KEY: Optional[str] = None  # Required when using RunPod provider
    RUNPOD_ENDPOINT_ID: Optional[str] = None  # RunPod serverless endpoint ID (legacy, use pipeline-specific IDs)
    RUNPOD_MODEL: str = "protoverb-slovenian-asr"  # PROTOVERB Slovenian ASR model
    RUNPOD_CHUNK_DURATION_SECONDS: int = 240  # Target chunk duration (4 minutes)
    RUNPOD_CHUNK_OVERLAP_SECONDS: int = 5  # Overlap between chunks to avoid cutting words
    RUNPOD_USE_SILENCE_DETECTION: bool = True  # Use silence detection for chunk boundaries
    RUNPOD_MAX_CONCURRENT_CHUNKS: int = 3  # Max parallel chunk transcriptions
    RUNPOD_TIMEOUT: int = 300  # Max seconds per chunk (5 minutes)
    RUNPOD_MAX_RETRIES: int = 3  # Max retry attempts on failure

    # RunPod NLP Pipeline Configuration
    RUNPOD_PUNCTUATE: bool = True  # Enable punctuation & capitalization by default
    RUNPOD_DENORMALIZE: bool = True  # Enable text denormalization by default
    RUNPOD_DENORMALIZE_STYLE: str = "default"  # Options: default, technical, everyday

    # Slovenian ASR Pipeline Endpoint IDs (RunPod)
    # Each pipeline has its own RunPod endpoint deployment
    SLOVENE_ASR_NFA_ENDPOINT_ID: Optional[str] = None  # NeMo ClusteringDiarizer + NFA alignment
    SLOVENE_ASR_MMS_ENDPOINT_ID: Optional[str] = None  # NeMo ClusteringDiarizer + MMS alignment
    SLOVENE_ASR_PYANNOTE_ENDPOINT_ID: Optional[str] = None  # pyannote 3.1 diarization + NFA alignment

    # GaMS LLM on RunPod Configuration (Slovenian text cleanup)
    # Reuses RUNPOD_API_KEY for authentication
    RUNPOD_LLM_GAMS_ENDPOINT_ID: Optional[str] = None  # RunPod serverless endpoint ID for GaMS
    RUNPOD_LLM_GAMS_MODEL: str = "GaMS-9B-Instruct"  # Native Slovenian LLM model
    RUNPOD_LLM_GAMS_TIMEOUT: int = 120  # Max seconds per request
    RUNPOD_LLM_GAMS_MAX_RETRIES: int = 3  # Max retry attempts on failure
    RUNPOD_LLM_GAMS_DEFAULT_TEMPERATURE: float = 0.0  # Lower = more deterministic
    RUNPOD_LLM_GAMS_DEFAULT_TOP_P: float = 0.0  # Nucleus sampling parameter
    RUNPOD_LLM_GAMS_MAX_TOKENS: int = 2048  # Max tokens to generate

    # CORS Configuration
    CORS_ORIGINS: str = "*"

    # Worker Configuration
    WORKERS: int = 1

    # Database Pool Configuration
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Development/Debug
    DEBUG: bool = False
    RELOAD: bool = False
    LLM_STORE_RAW_RESPONSE: bool = False  # Store raw LLM responses for debugging (disable in prod)

    # Authentication & JWT Configuration
    JWT_SECRET_KEY: str  # Required - no default for security
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Notion Integration Configuration
    NOTION_RATE_LIMIT_REQUESTS: int = 3  # Requests per second
    NOTION_RATE_LIMIT_PERIOD: int = 1    # Period in seconds
    NOTION_MAX_RETRIES: int = 3          # Max retry attempts on failure
    NOTION_RETRY_DELAY: int = 5          # Seconds between retries

    # Encryption Configuration
    # Uses JWT_SECRET_KEY for encryption by default
    # Can be overridden with dedicated ENCRYPTION_KEY for better security
    ENCRYPTION_KEY: Optional[str] = None  # Optional - falls back to JWT_SECRET_KEY

    # Envelope Encryption Configuration
    ENCRYPTION_PROVIDER: str = "local"  # Options: local (future: aws-kms, gcp-kms)

    # Spell-check Configuration
    SPELLCHECK_ENABLED: bool = True  # Enable spell-checking for supported languages
    SPELLCHECK_WORDLIST_PATH: str = "/app/data/dictionaries/sl-words.txt"  # Word list (baked into image)
    SPELLCHECK_CACHE_PATH: str = "/app/data/cache"  # Pickle cache (mounted volume for persistence)
    SPELLCHECK_MAX_EDIT_DISTANCE: int = 2  # Max edit distance for suggestions (1-3)
    SPELLCHECK_PREFIX_LENGTH: int = 7  # SymSpell optimization parameter
    SPELLCHECK_SUGGESTION_COUNT: int = 5  # Max suggestions per misspelled word
    SPELLCHECK_MIN_WORD_LENGTH: int = 2  # Skip words shorter than this

    # Test Configuration (Optional - only used in E2E tests)
    NOTION_TEST_API_KEY: Optional[str] = None
    NOTION_TEST_DATABASE_ID: Optional[str] = None

    # Logging Configuration (Optional - per-module log levels)
    APP_LOG_LEVEL: Optional[str] = None
    SQLALCHEMY_LOG_LEVEL: Optional[str] = None
    UVICORN_LOG_LEVEL: Optional[str] = None
    HTTPX_LOG_LEVEL: Optional[str] = None
    ASYNCPG_LOG_LEVEL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def api_encryption_key(self) -> str:
        """
        Key for encrypting API keys in database.
        Falls back to JWT_SECRET_KEY if ENCRYPTION_KEY not set.
        """
        return self.ENCRYPTION_KEY or self.JWT_SECRET_KEY


# Provider Parameter Configurations
# Used by /api/v1/options endpoint to inform frontend of available parameters

# Transcription Provider Parameters
TRANSCRIPTION_PROVIDER_PARAMETERS = {
    "groq": {
        "temperature": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Temperature for transcription sampling (0.0-1.0, higher = more random)"
        }
    },
    "assemblyai": {},  # AssemblyAI - no configurable parameters (no beam_size/temperature support)
    # Slovenian ASR with multiple model variants (nfa, mms, pyannote)
    "clarin-slovene-asr": {
        "punctuate": {
            "type": "bool",
            "default": True,
            "description": "Add punctuation and capitalization to transcription"
        },
        "denormalize": {
            "type": "bool",
            "default": True,
            "description": "Convert spoken numbers, dates, times to written form"
        },
        "denormalize_style": {
            "type": "string",
            "options": ["default", "technical", "everyday"],
            "default": "default",
            "description": "Denormalization style preset"
        },
        "enable_diarization": {
            "type": "bool",
            "default": False,
            "description": "Enable speaker diarization"
        },
        "speaker_count": {
            "type": "int",
            "min": 1,
            "max": 20,
            "default": None,
            "description": "Known speaker count (null for auto-detect)"
        },
        "max_speakers": {
            "type": "int",
            "min": 1,
            "max": 20,
            "default": 10,
            "description": "Maximum speakers for auto-detection"
        }
    },
    "noop": {}  # Test provider - no configurable parameters
}

# LLM Provider Parameters
LLM_PROVIDER_PARAMETERS = {
    "groq": {
        "temperature": {
            "type": "float",
            "min": 0.0,
            "max": 2.0,
            "default": 0.0,
            "description": "Temperature for LLM sampling (0.0-2.0, higher = more creative)"
        },
        "top_p": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Top-p nucleus sampling (0.0-1.0)"
        }
    },
    "runpod_llm_gams": {
        "temperature": {
            "type": "float",
            "min": 0.0,
            "max": 2.0,
            "default": 0.0,
            "description": "Temperature for GaMS sampling (0.0-2.0, lower = more deterministic)"
        },
        "top_p": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Top-p nucleus sampling for GaMS (0.0-1.0)"
        }
    },
    "noop": {}  # Test provider - no configurable parameters
}


# Global settings instance
settings = Settings()
