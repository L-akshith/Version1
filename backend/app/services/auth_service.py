"""
ExamShield - Authentication Service

Business logic for user registration, login, and token management.
Orchestrates UserRepository, password hashing, and JWT creation.
"""

import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import ConflictException
from app.exceptions.authentication import (
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.utils.password import hash_password, verify_password


class AuthService:
    """
    Service layer for authentication operations.

    Implements registration, login, and token-based user retrieval
    following the Clean Architecture pattern.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._role_repo = RoleRepository(session)

    async def register(self, request: RegisterRequest) -> UserResponse:
        """
        Register a new user.

        Args:
            request: Registration data including email, password, and full name.

        Returns:
            UserResponse with the newly created user's data.

        Raises:
            ConflictException: If the email is already registered.
        """
        if await self._user_repo.email_exists(request.email):
            raise ConflictException(
                message=f"Email '{request.email}' is already registered"
            )

        hashed = hash_password(request.password)

        # Assign default role (Observer) to new users
        default_role = await self._role_repo.get_by_name("Observer")
        role_id = default_role.id if default_role else None

        user_data: Dict[str, Any] = {
            "email": request.email,
            "hashed_password": hashed,
            "full_name": request.full_name,
            "is_active": True,
            "is_superuser": False,
            "role_id": role_id,
        }

        user = await self._user_repo.create(user_data)

        # Re-fetch with role eagerly loaded
        user = await self._user_repo.get_with_role(user.id)

        return UserResponse.model_validate({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "role_id": user.role_id,
            "role_name": user.role_name,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        })

    async def login(self, request: LoginRequest) -> TokenResponse:
        """
        Authenticate a user and issue JWT tokens.

        Args:
            request: Login data including email and password.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            InvalidCredentialsException: If email or password is wrong.
            InactiveUserException: If the user account is deactivated.
        """
        user = await self._user_repo.get_by_email(request.email)

        if user is None:
            raise InvalidCredentialsException()

        if not verify_password(request.password, user.hashed_password):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        extra_claims: Dict[str, Any] = {
            "email": user.email,
            "role": user.role_name,
            "is_superuser": user.is_superuser,
        }

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims=extra_claims,
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def get_current_user(self, token: str) -> UserResponse:
        """
        Retrieve the current user from a JWT access token.

        Args:
            token: The JWT access token.

        Returns:
            UserResponse with the authenticated user's data.

        Raises:
            InvalidTokenException: If the token is invalid.
            TokenExpiredException: If the token has expired.
            InactiveUserException: If the user account is deactivated.
        """
        from jose import JWTError, ExpiredSignatureError

        try:
            payload = decode_token(token)
        except ExpiredSignatureError:
            raise TokenExpiredException()
        except JWTError:
            raise InvalidTokenException()

        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise InvalidTokenException(message="Token missing subject claim")

        token_type = payload.get("type")
        if token_type != "access":
            raise InvalidTokenException(message="Invalid token type")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise InvalidTokenException(message="Invalid user ID in token")

        user = await self._user_repo.get_with_role(user_id)

        if user is None:
            raise InvalidTokenException(message="User not found")

        if not user.is_active:
            raise InactiveUserException()

        return UserResponse.model_validate({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "role_id": user.role_id,
            "role_name": user.role_name,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        })
