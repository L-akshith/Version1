"""
ExamShield - Authentication Schemas

Pydantic v2 schemas for authentication request/response payloads.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@examshield.gov.in"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password",
        examples=["SecurePassword123!"],
    )


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="Email address for the new account",
        examples=["newuser@examshield.gov.in"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters)",
        examples=["SecurePassword123!"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name of the user",
        examples=["Dr. Rajesh Kumar"],
    )


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token",
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )


class TokenPayload(BaseModel):
    """Schema representing decoded JWT token payload."""

    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(default="", description="User email")
    role: str = Field(default="", description="User role name")
    is_superuser: bool = Field(default=False, description="Superuser flag")
    type: str = Field(default="access", description="Token type")
    jti: str = Field(default="", description="JWT ID")
