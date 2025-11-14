"""
Logging configuration for structured text logging.
"""
import logging
import sys
from typing import Any, Dict
from app.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured text logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured key-value pairs."""
        # Base message
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S.%f")[:-3]
        base_msg = f"{timestamp} | {record.levelname:8} | {record.name} | {record.getMessage()}"

        # Add extra fields if present
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info"
            ]:
                extra_fields[key] = value

        if extra_fields:
            extra_str = " | " + " ".join(f"{k}={v}" for k, v in extra_fields.items())
            base_msg += extra_str

        # Add exception info if present
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)

        return base_msg


def setup_logging() -> logging.Logger:
    """
    Configure and return application logger.

    Supports per-module log level configuration via environment variables:
    - APP_LOG_LEVEL: Application logs (default: INFO)
    - SQLALCHEMY_LOG_LEVEL: SQLAlchemy logs (default: WARNING)
    - UVICORN_LOG_LEVEL: Uvicorn logs (default: INFO)
    - HTTPX_LOG_LEVEL: HTTPX logs (default: WARNING)

    Returns:
        Configured logger instance
    """
    # Get root logger
    logger = logging.getLogger("app")
    app_log_level = (settings.APP_LOG_LEVEL or settings.LOG_LEVEL).upper()
    logger.setLevel(getattr(logging, app_log_level))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, app_log_level))
    console_handler.setFormatter(StructuredFormatter())

    logger.addHandler(console_handler)

    # Don't propagate to root logger
    logger.propagate = False

    # Configure third-party library log levels
    log_config = _configure_third_party_loggers()

    # Print startup log configuration
    print("=" * 60)
    print("LOG CONFIGURATION")
    print("=" * 60)
    print(f"APP_LOG_LEVEL:        {app_log_level}")
    for lib_name, level in log_config.items():
        print(f"{lib_name:20} {level}")
    print("=" * 60)

    return logger


def _configure_third_party_loggers() -> Dict[str, str]:
    """
    Configure log levels for third-party libraries.

    Returns:
        Dictionary mapping logger names to configured levels
    """
    config = {}

    # SQLAlchemy (database queries, connection pool)
    sqlalchemy_level = (settings.SQLALCHEMY_LOG_LEVEL or "WARNING").upper()
    logging.getLogger("sqlalchemy.engine").setLevel(getattr(logging, sqlalchemy_level))
    logging.getLogger("sqlalchemy.pool").setLevel(getattr(logging, sqlalchemy_level))
    config["SQLALCHEMY_LOG_LEVEL:"] = sqlalchemy_level

    # Uvicorn
    uvicorn_level = (settings.UVICORN_LOG_LEVEL or "INFO").upper()
    logging.getLogger("uvicorn").setLevel(getattr(logging, uvicorn_level))
    logging.getLogger("uvicorn.access").setLevel(getattr(logging, uvicorn_level))
    config["UVICORN_LOG_LEVEL:"] = uvicorn_level

    # HTTPX (HTTP client used by Notion SDK)
    httpx_level = (settings.HTTPX_LOG_LEVEL or "WARNING").upper()
    logging.getLogger("httpx").setLevel(getattr(logging, httpx_level))
    config["HTTPX_LOG_LEVEL:"] = httpx_level

    # AsyncPG (PostgreSQL driver)
    asyncpg_level = (settings.ASYNCPG_LOG_LEVEL or "WARNING").upper()
    logging.getLogger("asyncpg").setLevel(getattr(logging, asyncpg_level))
    config["ASYNCPG_LOG_LEVEL:"] = asyncpg_level

    return config


class StructuredLogger:
    """Wrapper around logging.Logger that supports keyword arguments for structured logging."""

    # Reserved field names in LogRecord that should be prefixed
    RESERVED_FIELDS = {
        'name', 'msg', 'args', 'created', 'filename', 'funcName',
        'levelname', 'levelno', 'lineno', 'module', 'msecs',
        'message', 'pathname', 'process', 'processName', 'relativeCreated',
        'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
        'taskName'
    }

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, msg: str, *args, **kwargs):
        """Log with structured extra fields."""
        # Extract exc_info if present
        exc_info = kwargs.pop('exc_info', False)

        # Prefix reserved field names to avoid conflicts
        extra = {}
        for key, value in kwargs.items():
            if key in self.RESERVED_FIELDS:
                # Prefix reserved fields with 'ctx_'
                extra[f'ctx_{key}'] = value
            else:
                extra[key] = value

        self._logger.log(level, msg, *args, extra=extra, exc_info=exc_info, stacklevel=3)

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with extra fields."""
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message with extra fields."""
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with extra fields."""
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message with extra fields."""
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with extra fields."""
        self._log(logging.CRITICAL, msg, *args, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger with the specified name under the app namespace.

    Args:
        name: Logger name (will be prefixed with 'app.')

    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(f"app.{name}")
    return StructuredLogger(logger)


# Initialize application logger
app_logger = setup_logging()
