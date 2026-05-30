"""Layer 1 — syntax validation tests (no network, no mocks needed)."""
import pytest

from app.services.syntax_check import check_syntax


def test_valid_email() -> None:
    result = check_syntax("user@example.com")
    assert result.is_valid
    assert result.domain == "example.com"
    assert result.local == "user"
    assert not result.is_role


def test_invalid_format() -> None:
    result = check_syntax("not-an-email")
    assert not result.is_valid
    assert result.error != ""


def test_missing_at() -> None:
    result = check_syntax("userexample.com")
    assert not result.is_valid


def test_invalid_tld() -> None:
    # single-label domain — email-validator rejects these
    result = check_syntax("user@localhost")
    assert not result.is_valid


def test_too_long() -> None:
    local = "a" * 255
    result = check_syntax(f"{local}@example.com")
    assert not result.is_valid


def test_role_address() -> None:
    for local in ("admin", "support", "info", "sales", "hr", "careers"):
        result = check_syntax(f"{local}@example.com")
        assert result.is_valid
        assert result.is_role, f"Expected {local}@ to be a role address"


def test_non_role_address() -> None:
    result = check_syntax("john.smith@example.com")
    assert result.is_valid
    assert not result.is_role
