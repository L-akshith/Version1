import pytest
from httpx import AsyncClient
from fastapi import status

from app.core.config import get_settings
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_rate_limiting_remains_enabled(client: AsyncClient):
    """
    Verify that rate limiting is enabled and returns 429 when max_requests
    is exceeded in a single test, confirming production behavior is untouched.
    """
    settings = get_settings()
    
    # We must explicitly verify that RATE_LIMIT_ENABLED is True 
    # to ensure it hasn't been disabled globally for tests.
    assert settings.RATE_LIMIT_ENABLED is True
    
    max_requests = settings.RATE_LIMIT_REQUESTS
    
    # Make enough requests to hit the limit
    for _ in range(max_requests):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@examshield.gov.in", "password": "WrongPassword123!"},
        )
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]
        
    # The very next request should be rate limited
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@examshield.gov.in", "password": "WrongPassword123!"},
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    data = response.json()
    assert data["errors"][0]["type"] == "rate_limit"


async def test_rate_limiting_isolation(client: AsyncClient):
    """
    Verify that the rate limit state was cleared before this test started,
    even though the previous test (test_rate_limiting_remains_enabled) 
    completely exhausted the limit.
    """
    settings = get_settings()
    
    # Just a few requests should work completely fine because the state was cleared
    for _ in range(5):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@examshield.gov.in", "password": "WrongPassword123!"},
        )
        # Should not be 429
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]
