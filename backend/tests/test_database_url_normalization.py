"""
ExamShield - Tests for Database URL Normalization and SSL Configuration

Verifies:
1. Railway / Neon PostgreSQL URLs containing `?sslmode=require` are normalized to `postgresql+asyncpg://`.
2. `sslmode` query parameter is stripped from `DATABASE_URL` so `asyncpg` driver does not receive unexpected keyword arguments.
3. TLS/SSL requirement is preserved via `is_ssl_required`.
4. Local development and test database URLs (SQLite, local Postgres) maintain expected default behavior.
5. `sync_database_url` outputs clean URL for synchronous Alembic migrations.
"""

import pytest
from app.core.config import Settings, get_settings


def test_neon_url_normalization_and_ssl_preservation():
    get_settings.cache_clear()
    
    neon_raw_url = "postgres://alex:secretpass@ep-cool-db-12345.us-east-1.aws.neon.tech/neondb?sslmode=require"
    
    settings = Settings(_env_file=None, DATABASE_URL=neon_raw_url)
    
    # 1. Scheme normalized to postgresql+asyncpg://
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    
    # 2. sslmode query parameter stripped from URL for asyncpg compatibility
    assert "sslmode" not in settings.DATABASE_URL
    assert settings.DATABASE_URL == "postgresql+asyncpg://alex:secretpass@ep-cool-db-12345.us-east-1.aws.neon.tech/neondb"
    
    # 3. TLS requirement preserved
    assert settings.is_ssl_required is True
    
    # 4. Sync database URL for Alembic
    assert settings.sync_database_url == "postgresql://alex:secretpass@ep-cool-db-12345.us-east-1.aws.neon.tech/neondb"
    
    get_settings.cache_clear()


def test_local_postgres_url_normalization():
    get_settings.cache_clear()
    
    local_url = "postgresql://examshield:examshield@localhost:5432/examshield"
    settings = Settings(_env_file=None, DATABASE_URL=local_url)
    
    assert settings.DATABASE_URL == "postgresql+asyncpg://examshield:examshield@localhost:5432/examshield"
    assert "sslmode" not in settings.DATABASE_URL
    assert settings.is_ssl_required is False
    
    get_settings.cache_clear()


def test_sqlite_url_normalization():
    get_settings.cache_clear()
    
    sqlite_url = "sqlite+aiosqlite:///:memory:"
    settings = Settings(_env_file=None, DATABASE_URL=sqlite_url)
    
    assert settings.DATABASE_URL == sqlite_url
    assert settings.is_ssl_required is False
    
    get_settings.cache_clear()


def test_production_environment_forces_ssl():
    get_settings.cache_clear()
    
    local_url = "postgresql+asyncpg://examshield:examshield@localhost:5432/examshield"
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        DEBUG=False,
        JWT_SECRET_KEY="A-VERY-SECURE-PRODUCTION-JWT-SECRET-KEY-12345",
        CORS_ORIGINS=["https://examshield.gov.in"],
        DATABASE_URL=local_url,
    )
    
    assert settings.is_ssl_required is True
    
    get_settings.cache_clear()
