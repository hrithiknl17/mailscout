"""Layer 2+3 — DNS check tests (all network calls mocked)."""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.dns_check import check_dns


@pytest.mark.asyncio
async def test_good_domain() -> None:
    with (
        patch("app.services.dns_check.check_domain_a_record", new=AsyncMock(return_value=True)),
        patch("app.services.dns_check.get_mx_records", new=AsyncMock(return_value=["mail.example.com"])),
    ):
        result = await check_dns("example.com")
    assert result.has_a_record
    assert result.primary_mx == "mail.example.com"
    assert result.mx_records == ["mail.example.com"]


@pytest.mark.asyncio
async def test_dead_domain() -> None:
    with patch("app.services.dns_check.check_domain_a_record", new=AsyncMock(return_value=False)):
        result = await check_dns("dead-domain-xyz-404.com")
    assert not result.has_a_record
    assert result.primary_mx == ""


@pytest.mark.asyncio
async def test_domain_with_no_mx() -> None:
    """Domain resolves but has no MX records — valid A record, empty MX list."""
    with (
        patch("app.services.dns_check.check_domain_a_record", new=AsyncMock(return_value=True)),
        patch("app.services.dns_check.get_mx_records", new=AsyncMock(return_value=[])),
    ):
        result = await check_dns("example.com")
    assert result.has_a_record
    assert result.mx_records == []
    assert result.primary_mx == ""
