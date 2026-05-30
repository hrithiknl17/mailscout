"""Shared pytest fixtures. asyncio_mode=auto is set in pyproject.toml."""
import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
