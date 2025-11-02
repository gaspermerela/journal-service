"""
Request logging middleware for tracking HTTP requests.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import get_logger

logger = get_logger("middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Logs:
    - Request method, path, client IP
    - Response status code
    - Request processing time
    - Request ID for tracing
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response from handler
        """
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log incoming request
        logger.info(
            f"Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            ip=client_ip,
            user_agent=user_agent
        )

        # Process request and measure time
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000  # Convert to ms

            # Log response
            logger.info(
                f"Request completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=f"{process_time:.2f}"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            process_time = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=f"{process_time:.2f}",
                error=str(e),
                exc_info=True
            )

            raise
