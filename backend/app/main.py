"""
ExamShield - FastAPI Application Entrypoint

Initializes the FastAPI application, registers middleware, configures CORS,
and mounts API routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.roles import router as roles_router
from app.api.v1.papers import router as papers_router
from app.api.v1.exams import router as exams_router
from app.api.v1.subjects import router as subjects_router
from app.api.v1.question_papers import router as question_papers_router
from app.api.v1.approval_workflows import router as approval_workflows_router
from app.api.v1.audit import router as audit_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.exceptions.api_exception import register_exception_handlers
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── Exception Handlers ───────────────────────────────────────────
    register_exception_handlers(app)

    # ── Middleware Registration ──────────────────────────────────────
    # CORS Middleware (must be registered first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Custom Middlewares (executed in reverse order of addition)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # ── Router Mounting ──────────────────────────────────────────────
    # Mount API v1 router prefixing with /api/v1
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(roles_router, prefix="/api/v1")
    app.include_router(papers_router, prefix="/api/v1")
    app.include_router(exams_router, prefix="/api/v1")
    app.include_router(subjects_router, prefix="/api/v1")
    app.include_router(question_papers_router, prefix="/api/v1")
    app.include_router(approval_workflows_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")

    # Root route for basic landing page/health confirmation
    @app.get("/", tags=["General"])
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "documentation": "/docs",
        }

    return app


app = create_app()
