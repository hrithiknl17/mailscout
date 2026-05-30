"""API integration tests — all external calls mocked, no real DB or Redis."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.main import app
from app.models.verification import VerificationStatus
from app.routers.verify import get_redis
from app.services.verifier import EmailCheckResult


def _make_user() -> CurrentUser:
    return CurrentUser(user_id="test-user-123", email="test@example.com")


def _make_result(email: str = "test@example.com") -> EmailCheckResult:
    return EmailCheckResult(
        id=uuid.uuid4(),
        email=email,
        status=VerificationStatus.deliverable,
        confidence=0.95,
        reason="SMTP 250 OK",
        mx_record="mail.example.com",
        is_catch_all=False,
        is_disposable=False,
        is_role=False,
        created_at=datetime.now(timezone.utc),
    )


async def _mock_get_db() -> None:
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    yield mock_session


async def _mock_get_redis() -> None:
    yield AsyncMock()


@pytest.mark.asyncio
async def test_health_ok() -> None:
    with (
        patch("app.routers.health._check_db", new=AsyncMock(return_value="ok")),
        patch("app.routers.health._check_redis", new=AsyncMock(return_value="ok")),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["checks"]["db"] == "ok"


@pytest.mark.asyncio
async def test_verify_single_happy_path() -> None:
    fake_result = _make_result()
    app.dependency_overrides[get_current_user] = _make_user
    app.dependency_overrides[get_db] = _mock_get_db
    app.dependency_overrides[get_redis] = _mock_get_redis

    with (
        patch("app.routers.verify.verify_email", new=AsyncMock(return_value=fake_result)),
        patch("app.routers.verify._check_monthly_limit", new=AsyncMock(return_value=0)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/verify/single",
                json={"email": "test@example.com"},
                headers={"Authorization": "Bearer fake-token"},
            )

    app.dependency_overrides = {}
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deliverable"
    assert data["email"] == "test@example.com"
    assert data["confidence"] == 0.95


@pytest.mark.asyncio
async def test_verify_single_missing_email_field() -> None:
    """Missing required 'email' field → 422 Unprocessable Entity."""
    app.dependency_overrides[get_current_user] = _make_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/verify/single",
            json={},
            headers={"Authorization": "Bearer fake-token"},
        )
    app.dependency_overrides = {}
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_single_no_auth() -> None:
    """No Authorization header → 403 Forbidden."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/verify/single",
            json={"email": "test@example.com"},
        )
    assert response.status_code == 403
