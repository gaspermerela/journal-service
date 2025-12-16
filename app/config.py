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
    TRANSCRIPTION_PROVIDER: str = "groq"  # Options: whisper (local), groq, assemblyai, runpod (Slovenian)

    # Whisper (Local) Transcription Configuration
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
    LLM_PROVIDER: str = "groq"  # Options: ollama (local), groq (API)

    # Ollama (Local) LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
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

    # RunPod API Configuration (for Slovenian transcription using RSDO model)
    RUNPOD_API_KEY: Optional[str] = None  # Required when using RunPod provider
    RUNPOD_ENDPOINT_ID: Optional[str] = None  # RunPod serverless endpoint ID
    RUNPOD_MODEL: str = "rsdo-slovenian-asr"  # RSDO Slovenian ASR model
    RUNPOD_CHUNK_DURATION_SECONDS: int = 240  # Target chunk duration (4 minutes)
    RUNPOD_CHUNK_OVERLAP_SECONDS: int = 5  # Overlap between chunks to avoid cutting words
    RUNPOD_USE_SILENCE_DETECTION: bool = True  # Use silence detection for chunk boundaries
    RUNPOD_MAX_CONCURRENT_CHUNKS: int = 3  # Max parallel chunk transcriptions
    RUNPOD_TIMEOUT: int = 300  # Max seconds per chunk (5 minutes)
    RUNPOD_MAX_RETRIES: int = 3  # Max retry attempts on failure

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
    "whisper": {
        "temperature": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Temperature for transcription sampling (0.0-1.0, higher = more random)"
        }
    },
    "assemblyai": {},  # AssemblyAI - no configurable parameters (no beam_size/temperature support)
    "runpod": {},  # RunPod RSDO - Slovenian only, no configurable parameters (fixed model)
    "noop": {}  # Test provider - no configurable parameters
}

# LLM Provider Parameters
LLM_PROVIDER_PARAMETERS = {
    "groq": {
        "temperature": {
            "type": "float",
            "min": 0.0,
            "max": 2.0,
            "default": 1.0,
            "description": "Temperature for LLM sampling (0.0-2.0, higher = more creative)"
        },
        "top_p": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 1.0,
            "description": "Top-p nucleus sampling (0.0-1.0)"
        }
    },
    "ollama": {
        "temperature": {
            "type": "float",
            "min": 0.0,
            "max": 2.0,
            "default": 1.0,
            "description": "Temperature for LLM sampling (0.0-2.0, higher = more creative)"
        },
        "top_p": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 1.0,
            "description": "Top-p nucleus sampling (0.0-1.0)"
        }
    },
    "noop": {}  # Test provider - no configurable parameters
}


# Output Schema Definitions
# Used by LLM cleanup services to define expected JSON structure per entry_type
# TODO: schemas and their LLM instructions will probably change multiple times in the future.
OUTPUT_SCHEMAS = {
    "dream": {
        "description": "Analysis schema for dream journal entries",
        "fields": {
            "themes": {
                "type": "array",
                "item_type": "string",
                "description": "Main themes and motifs of the dream",
                "required": False
            },
            "emotions": {
                "type": "array",
                "item_type": "string",
                "description": "Emotions experienced in the dream",
                "required": False
            },
            "characters": {
                "type": "array",
                "item_type": "string",
                "description": "People, creatures, or entities in the dream",
                "required": False
            },
            "locations": {
                "type": "array",
                "item_type": "string",
                "description": "Places and settings in the dream",
                "required": False
            }
        }
    },
    "therapy": {
        "description": "Analysis schema for therapy session transcriptions",
        "fields": {
            "topics": {
                "type": "array",
                "item_type": "string",
                "description": "Main topics discussed in session",
                "required": False
            },
            "insights": {
                "type": "array",
                "item_type": "string",
                "description": "Key insights or realizations",
                "required": False
            },
            "action_items": {
                "type": "array",
                "item_type": "string",
                "description": "Action items or next steps identified",
                "required": False
            }
        }
    },
    # Add more entry types here as needed
    # "meeting": { ... },
    # "journal": { ... },
}


def get_output_schema(entry_type: str) -> dict:
    """
    Get output schema for a given entry type.

    Args:
        entry_type: The entry type (e.g., "dream", "therapy")

    Returns:
        Schema definition dict

    Raises:
        ValueError: If entry_type not found in OUTPUT_SCHEMAS
    """
    if entry_type not in OUTPUT_SCHEMAS:
        raise ValueError(
            f"Unknown entry_type '{entry_type}'. "
            f"Available types: {', '.join(OUTPUT_SCHEMAS.keys())}"
        )
    return OUTPUT_SCHEMAS[entry_type]


def generate_json_schema_instruction(entry_type: str) -> str:
    """
    Generate JSON schema instruction to append to prompts.

    This creates the standardized JSON output format instruction
    that tells the LLM what structure to return.

    Args:
        entry_type: The entry type (e.g., "dream", "therapy")

    Returns:
        Multi-line string with JSON schema instruction

    Example output:
        '''
        Respond ONLY with valid JSON in this exact format:
        {{
          "cleaned_text": "The cleaned text here",
          "themes": ["theme1", "theme2"],
          "emotions": ["emotion1"],
          ...
        }}
        '''
    """
    schema = get_output_schema(entry_type)

    # Build example JSON structure
    example_fields = []
    example_fields.append('  "cleaned_text": "The cleaned and formatted text here"')

    for field_name, field_config in schema["fields"].items():
        if field_config["type"] == "array":
            example_fields.append(f'  "{field_name}": ["{field_config["description"]}"]')
        else:
            example_fields.append(f'  "{field_name}": "{field_config["description"]}"')

    example_json = "{{\n" + ",\n".join(example_fields) + "\n}}"

    instruction = f"""
Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{example_json}
"""

    return instruction.strip()


# Global settings instance
settings = Settings()
