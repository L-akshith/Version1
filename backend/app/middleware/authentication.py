"""
ExamShield - Authentication Middleware

JWT validation middleware that extracts user information from
bearer tokens and injects it into the request state for
downstream logging and audit purposes.
"""

import logging
from typing import Optional

from fastapi import Request, Response
from jose import ExpiredSignatureError, JWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.utils.jwt import decode_token

logger = logging.getLogger("examshield.auth")

# Paths that do not require authentication
PUBLIC_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts JWT claims and injects user info
    into the request state for logging/audit purposes.

    This middleware does NOT enforce authentication — that is handled
    by the FastAPI dependency injection system (see dependencies.py).
    Its purpose is to enrich the request context with user information
    for the logging middleware.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Initialize default state
        request.state.user_id = None
        request.state.user_email = None
        request.state.user_role = None

        # Try to extract and decode the bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Strip "Bearer " prefix
            try:
                payload = decode_token(token)
                request.state.user_id = payload.get("sub")
                request.state.user_email = payload.get("email")
                request.state.user_role = payload.get("role")
            except ExpiredSignatureError:
                logger.debug("Expired token in request to %s", request.url.path)
            except JWTError:
                logger.debug("Invalid token in request to %s", request.url.path)

        return await call_next(request)
