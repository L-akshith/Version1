"""
ExamShield - Application Configuration

Centralized configuration management using Pydantic Settings.
All environment variables are loaded and validated here.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import PrivateAttr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "ExamShield"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Secure Examination Paper Management and Distribution Platform"
    )
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Server ───────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://examshield:examshield@localhost:5432/examshield"
    )
    DATABASE_ECHO: bool = False
    DB_POOL_SIZE: Optional[int] = None
    DB_MAX_OVERFLOW: Optional[int] = None
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 5
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    _ssl_required_by_url: bool = PrivateAttr(default=False)

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-THIS-TO-A-LONG-RANDOM-SECRET-KEY-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: Optional[str] = None
    REDIS_PREFIX: str = "examshield:"

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # ── File Storage ─────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads/question_papers"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── AWS & Production Cloud Infrastructure ─────────────────────
    AWS_REGION: str = "us-east-1"
    AWS_KMS_KEY_ID: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_PREFIX: str = "question_papers"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    CRYPTO_PROVIDER: str = "local"  # "local" or "kms"
    STORAGE_PROVIDER: str = "local"  # "local" or "s3"

    # ── Security (Placeholders for future cryptography) ──────────
    ENCRYPTION_KEY: Optional[str] = None
    SIGNING_KEY: Optional[str] = None
    KEY_WRAPPING_ENABLED: bool = False

    # ── First Superuser ──────────────────────────────────────────
    FIRST_SUPERUSER_EMAIL: str = "admin@examshield.gov.in"
    FIRST_SUPERUSER_PASSWORD: str = "ChangeThisPassword123!"
    FIRST_SUPERUSER_FULL_NAME: str = "System Administrator"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL must be set")

        # Railway / Neon PostgreSQL scheme normalization
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Strip libpq-specific 'sslmode' query parameter for asyncpg compatibility
        if "sslmode" in v or "ssl=" in v:
            from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

            parsed = urlparse(v)
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            sslmode_vals = query_params.pop("sslmode", [])
            query_params.pop("channel_binding", None)

            is_ssl = any(
                val.lower() in ("require", "prefer", "verify-ca", "verify-full")
                for val in sslmode_vals
            ) or any(
                val.lower() in ("require", "true", "1")
                for val in query_params.get("ssl", [])
            )

            cls._last_ssl_required = is_ssl

            new_query = urlencode(query_params, doseq=True)
            v = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            ))
        else:
            cls._last_ssl_required = False

        return v

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if v == "CHANGE-THIS-TO-A-LONG-RANDOM-SECRET-KEY-IN-PRODUCTION":
            import warnings

            warnings.warn(
                "JWT_SECRET_KEY is using the default value. "
                "Set a secure random key in production.",
                UserWarning,
                stacklevel=2,
            )
        return v

    def model_post_init(self, __context) -> None:
        """Validate production configuration to fail fast if insecure."""
        if getattr(self, "_last_ssl_required", False):
            self._ssl_required_by_url = True

        if self.DB_POOL_SIZE is not None:
            self.DATABASE_POOL_SIZE = self.DB_POOL_SIZE
        if self.DB_MAX_OVERFLOW is not None:
            self.DATABASE_MAX_OVERFLOW = self.DB_MAX_OVERFLOW

        if self.ENVIRONMENT.lower() == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production environment")
            if self.JWT_SECRET_KEY == "CHANGE-THIS-TO-A-LONG-RANDOM-SECRET-KEY-IN-PRODUCTION":
                raise ValueError("Production mode requires explicit, strong JWT_SECRET_KEY")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("Production mode forbids wildcard '*' CORS origin")
            if self.CRYPTO_PROVIDER == "kms" and not self.AWS_KMS_KEY_ID:
                raise ValueError("KMS crypto provider requires AWS_KMS_KEY_ID to be set in production")
            if self.STORAGE_PROVIDER == "s3" and not self.S3_BUCKET:
                raise ValueError("S3 storage provider requires S3_BUCKET to be set in production")

    @property
    def is_ssl_required(self) -> bool:
        """Check whether SSL/TLS is required for the database connection."""
        raw_url = str(self.DATABASE_URL).lower()
        if raw_url.startswith("sqlite"):
            return False
        return (
            self.ENVIRONMENT.lower() == "production"
            or getattr(self, "_ssl_required_by_url", False)
            or "ssl=require" in raw_url
            or "ssl=true" in raw_url
            or "ssl=1" in raw_url
        )

    @property
    def sync_database_url(self) -> str:
        """Return synchronous database URL for Alembic."""
        url = self.DATABASE_URL.replace("+asyncpg", "")
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url





@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

