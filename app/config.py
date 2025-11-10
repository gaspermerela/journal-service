"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from typing import List
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
    WHISPER_MODEL: str = "base"  # Options: tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"  # Options: cpu, cuda (for GPU)
    TORCH_NUM_THREADS: int = 10  # Number of CPU threads for PyTorch

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


# Global settings instance
settings = Settings()
