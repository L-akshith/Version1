"""
ExamShield - Health Check API Route

System health endpoint checking database and Redis connectivity.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_async_session

router = APIRouter(tags=["System Health"])
logger = logging.getLogger("examshield.health")


@router.get(
    "/health",
    summary="System health check",
    description="Check the health of all system components: database, Redis, application.",
)
async def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive health check.

    Checks:
    - Application status
    - Database connectivity
    - Redis connectivity (if configured)
    """
    settings = get_settings()
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {},
    }

    # Check database
    try:
        from app.database.session import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql",
        }
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "type": "postgresql",
            "error": str(e),
        }

    # Check Redis (if configured)
    if settings.REDIS_URL:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.close()
            health_status["components"]["redis"] = {
                "status": "healthy",
                "type": "redis",
            }
        except Exception as e:
            logger.error("Redis health check failed: %s", str(e))
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "type": "redis",
                "error": str(e),
            }
    else:
        health_status["components"]["redis"] = {
            "status": "not_configured",
            "type": "redis",
        }

    # Application info
    health_status["components"]["application"] = {
        "status": "healthy",
        "name": settings.APP_NAME,
        "debug": settings.DEBUG,
    }

    return health_status
