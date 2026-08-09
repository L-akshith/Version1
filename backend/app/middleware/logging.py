"""
ExamShield - Request Logging Middleware

Logs every HTTP request with user info, endpoint, execution time,
and status code. Optionally writes audit log entries to the database.
"""

import logging
import time
import uuid
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("examshield.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every HTTP request with timing information.

    Log format includes:
    - Request ID (correlation ID)
    - User ID (if authenticated)
    - HTTP method and path
    - Status code
    - Execution time in milliseconds
    - Client IP address
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Extract user info from the request state if available
        user_id: Optional[str] = None
        user_email: Optional[str] = None

        # Store request ID in state for downstream use
        request.state.request_id = request_id

        # Extract client IP
        client_ip = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "REQ [%s] | %s | %-7s %s | 500 | %.1fms | %s | EXCEPTION: %s",
                request_id,
                client_ip,
                request.method,
                request.url.path,
                elapsed_ms,
                user_email or "anonymous",
                str(exc),
            )
            raise

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Try to extract user info from response headers or request state
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        if hasattr(request.state, "user_email"):
            user_email = request.state.user_email

        # Determine log level based on status code
        status_code = response.status_code
        if status_code >= 500:
            log_fn = logger.error
        elif status_code >= 400:
            log_fn = logger.warning
        else:
            log_fn = logger.info

        log_fn(
            "REQ [%s] | %s | %-7s %s | %d | %.1fms | %s",
            request_id,
            client_ip,
            request.method,
            request.url.path,
            status_code,
            elapsed_ms,
            user_email or "anonymous",
        )

        # Add correlation headers to the response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"

        return response
