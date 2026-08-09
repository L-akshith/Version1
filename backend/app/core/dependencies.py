"""
ExamShield - Dependency Injection

FastAPI dependencies for database sessions, authentication,
and service layer access.
"""

import uuid
from typing import Annotated, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.subject_service import SubjectService
from app.services.user_service import UserService
from app.utils.jwt import decode_token

# ── Security Scheme ──────────────────────────────────────────────
security_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Enter your JWT access token",
    auto_error=True,
)

# ── Type Aliases ─────────────────────────────────────────────────
DBSession = Annotated[AsyncSession, Depends(get_async_session)]
BearerToken = Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)]


# ── Database Dependencies ────────────────────────────────────────
async def get_db(
    session: DBSession,
) -> AsyncSession:
    """Return the current database session."""
    return session


# ── Authentication Dependencies ──────────────────────────────────
async def get_current_user(
    credentials: BearerToken,
    session: DBSession,
) -> User:
    """
    Extract and validate the current user from the JWT bearer token.

    This is the primary authentication dependency used to protect routes.
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(session)
    user = await user_repo.get_with_role(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the current user only if they are active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the current user only if they are a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


# ── Permission Dependency Factory ────────────────────────────────
def require_permissions(required_permissions: List[str]):
    """
    Create a FastAPI dependency that checks for specific permissions.

    Usage:
        @router.get("/papers", dependencies=[Depends(require_permissions(["papers:list"]))])
    """

    async def _check_permissions(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.is_superuser:
            return current_user

        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned to user",
            )

        user_permissions = {p.name for p in current_user.role.permissions}
        missing = set(required_permissions) - user_permissions

        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(sorted(missing))}",
            )

        return current_user

    return _check_permissions


# ── Service Dependencies ─────────────────────────────────────────
async def get_auth_service(session: DBSession) -> AuthService:
    """Return an AuthService instance."""
    return AuthService(session)


async def get_user_service(session: DBSession) -> UserService:
    """Return a UserService instance."""
    return UserService(session)


async def get_subject_service(session: DBSession) -> SubjectService:
    """Return a SubjectService instance."""
    return SubjectService(session)


def get_storage_provider() -> "StorageInterface":
    """Return a StorageInterface instance."""
    from app.storage.local_storage import LocalStorageProvider
    from app.core.config import get_settings
    settings = get_settings()
    return LocalStorageProvider(base_dir=settings.UPLOAD_DIR)


async def get_question_paper_service(
    session: DBSession,
) -> "QuestionPaperService":
    """Return a QuestionPaperService instance."""
    from app.services.question_paper_service import QuestionPaperService
    return QuestionPaperService(
        session=session,
        storage_provider=get_storage_provider(),
    )


async def get_approval_workflow_service(
    session: DBSession,
) -> "ApprovalWorkflowService":
    """Return an ApprovalWorkflowService instance."""
    from app.services.approval_workflow_service import ApprovalWorkflowService
    return ApprovalWorkflowService(session=session)


async def get_key_provider() -> "KeyProvider":
    """Return a KeyProvider instance (Local for now)."""
    from app.modules.security.providers.local_provider import LocalKeyProvider
    return LocalKeyProvider()


async def get_key_management_service(
    session: DBSession,
) -> "KeyManagementService":
    """Return a KeyManagementService instance."""
    from app.modules.security.services.key_management_service import KeyManagementService
    return KeyManagementService(session=session, provider=await get_key_provider())


# ── Annotated Types for Convenience ──────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
