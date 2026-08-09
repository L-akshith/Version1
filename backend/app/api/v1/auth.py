"""
ExamShield - Authentication API Routes

Endpoints for user registration, login, and profile retrieval.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_auth_service, get_async_session
from app.database.session import get_async_session
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.response import APIResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=201,
    summary="Register a new user",
    description="Create a new user account. New users are assigned the 'Observer' role by default.",
)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[UserResponse]:
    """Register a new user and return their profile."""
    service = AuthService(session)
    user = await service.register(request)
    return APIResponse.ok(data=user, message="User registered successfully")


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Login and get JWT tokens",
    description="Authenticate with email and password to receive JWT access and refresh tokens.",
)
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[TokenResponse]:
    """Authenticate user and return JWT tokens."""
    service = AuthService(session)
    tokens = await service.login(request)
    return APIResponse.ok(data=tokens, message="Login successful")


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="Get current user profile",
    description="Retrieve the profile of the currently authenticated user.",
)
async def get_me(
    current_user: CurrentUser,
) -> APIResponse[UserResponse]:
    """Return the current authenticated user's profile."""
    user_response = UserResponse.model_validate({
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "role_id": current_user.role_id,
        "role_name": current_user.role_name,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    })
    return APIResponse.ok(data=user_response, message="User profile retrieved")

