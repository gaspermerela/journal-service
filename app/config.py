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

    # Application Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Storage Configuration
    AUDIO_STORAGE_PATH: str = "/app/data/audio"
    MAX_FILE_SIZE_MB: int = 100

    # Whisper Transcription Configuration
    WHISPER_MODEL: str = "large-v3"  # Options: tiny, base, small, medium, large, large-v3
    WHISPER_DEVICE: str = "cpu"  # Options: cpu, cuda (for GPU)
    TORCH_NUM_THREADS: int = 10  # Number of CPU threads for PyTorch
    WHISPER_DEFAULT_BEAM_SIZE: int = 5  # Default beam size for transcription (1-10, higher = more accurate but slower)

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
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_TIMEOUT_SECONDS: int = 120
    LLM_MAX_RETRIES: int = 2

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


# Global settings instance
settings = Settings()
