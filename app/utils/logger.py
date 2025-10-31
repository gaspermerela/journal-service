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

    Returns:
        Configured logger instance
    """
    # Get root logger
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    console_handler.setFormatter(StructuredFormatter())

    logger.addHandler(console_handler)

    # Don't propagate to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name under the app namespace.

    Args:
        name: Logger name (will be prefixed with 'app.')

    Returns:
        Logger instance
    """
    return logging.getLogger(f"app.{name}")


# Initialize application logger
app_logger = setup_logging()
