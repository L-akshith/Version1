"""
ExamShield - Rate Limiting Middleware

In-memory rate limiter with sliding window algorithm.
Can be upgraded to Redis-backed rate limiting when Redis is available.
"""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings

logger = logging.getLogger("examshield.ratelimit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter.

    Tracks request counts per client IP within a configurable time window.
    Returns 429 Too Many Requests when the limit is exceeded.

    Note: This is an in-memory implementation suitable for single-instance
    deployments. For multi-instance deployments, replace with Redis-backed
    rate limiting.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Stores {client_ip: [(timestamp, ...)] }
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def _clean_old_requests(self, client_ip: str, now: float) -> None:
        """Remove request timestamps outside the current window."""
        cutoff = now - self.window_seconds
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > cutoff
        ]

    def _is_rate_limited(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if a client IP has exceeded the rate limit.

        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        now = time.time()
        self._clean_old_requests(client_ip, now)

        request_count = len(self._requests[client_ip])
        remaining = max(0, self.max_requests - request_count)

        if request_count >= self.max_requests:
            return True, remaining

        self._requests[client_ip].append(now)
        return False, remaining - 1

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        settings = get_settings()

        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/api/v1/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        is_limited, remaining = self._is_rate_limited(client_ip)

        if is_limited:
            logger.warning(
                "Rate limit exceeded for IP %s on %s %s",
                client_ip,
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "Too many requests. Please try again later.",
                    "data": None,
                    "errors": [
                        {
                            "type": "rate_limit",
                            "message": f"Rate limit of {self.max_requests} "
                            f"requests per {self.window_seconds} seconds exceeded",
                        }
                    ],
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        # Add rate limit headers to all responses
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
