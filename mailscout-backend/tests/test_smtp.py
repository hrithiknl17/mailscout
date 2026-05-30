"""Layer 4c — SMTP handshake tests (all network calls mocked)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.smtp_check import SmtpResult, SmtpStatus, check_smtp


def _result(status: SmtpStatus, code: int = 0, msg: str = "") -> SmtpResult:
    return SmtpResult(status=status, code=code, message=msg)


@pytest.mark.asyncio
async def test_smtp_250_deliverable() -> None:
    with patch(
        "app.services.smtp_check._attempt_smtp",
        new=AsyncMock(return_value=_result(SmtpStatus.deliverable, 250, "OK")),
    ):
        result = await check_smtp("mail.example.com", "user@example.com")
    assert result.status == SmtpStatus.deliverable
    assert result.code == 250


@pytest.mark.asyncio
async def test_smtp_550_undeliverable() -> None:
    with patch(
        "app.services.smtp_check._attempt_smtp",
        new=AsyncMock(return_value=_result(SmtpStatus.undeliverable, 550, "No such user")),
    ):
        result = await check_smtp("mail.example.com", "nobody@example.com")
    assert result.status == SmtpStatus.undeliverable


@pytest.mark.asyncio
async def test_smtp_timeout_unknown() -> None:
    with patch(
        "app.services.smtp_check._attempt_smtp",
        new=AsyncMock(return_value=_result(SmtpStatus.unknown, 0, "Connection timed out")),
    ):
        result = await check_smtp("mail.example.com", "user@example.com")
    assert result.status == SmtpStatus.unknown


@pytest.mark.asyncio
async def test_smtp_connection_refused() -> None:
    with patch(
        "app.services.smtp_check._attempt_smtp",
        new=AsyncMock(return_value=_result(SmtpStatus.unknown, 0, "Connection refused")),
    ):
        result = await check_smtp("mail.example.com", "user@example.com")
    assert result.status == SmtpStatus.unknown


@pytest.mark.asyncio
async def test_smtp_greylist_421_then_unknown() -> None:
    """Both attempts return 421 → final status is unknown (not temporary_failure)."""
    greylist = _result(SmtpStatus.temporary_failure, 421, "Greylisted")
    with (
        patch(
            "app.services.smtp_check._attempt_smtp",
            new=AsyncMock(side_effect=[greylist, greylist]),
        ),
        patch("app.services.smtp_check.asyncio.sleep", new=AsyncMock()),
    ):
        result = await check_smtp("mail.example.com", "user@example.com")
    assert result.status == SmtpStatus.unknown


@pytest.mark.asyncio
async def test_smtp_greylist_then_success() -> None:
    """First attempt greylisted, retry succeeds → deliverable."""
    greylist = _result(SmtpStatus.temporary_failure, 421, "Greylisted")
    success = _result(SmtpStatus.deliverable, 250, "OK")
    with (
        patch(
            "app.services.smtp_check._attempt_smtp",
            new=AsyncMock(side_effect=[greylist, success]),
        ),
        patch("app.services.smtp_check.asyncio.sleep", new=AsyncMock()),
    ):
        result = await check_smtp("mail.example.com", "user@example.com")
    assert result.status == SmtpStatus.deliverable
