import logging

from app.services.smtp_check import SmtpStatus, check_smtp

logger = logging.getLogger(__name__)

FAKE_LOCAL = "definitely-fake-mailbox-xyz789"

ACCEPT_ALL_DOMAINS: frozenset[str] = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com",
    "live.com", "yahoo.com", "ymail.com", "protonmail.com",
    "proton.me", "icloud.com",
})

ACCEPT_ALL_MX_SUFFIXES: tuple[str, ...] = (
    "google.com",
    "outlook.com",
    "yahoodns.net",
)


def is_accept_all_provider(domain: str, primary_mx: str) -> bool:
    """Return True if domain is a known accept-all provider (skip SMTP verification)."""
    if domain.lower() in ACCEPT_ALL_DOMAINS:
        return True
    mx_lower = primary_mx.lower()
    return any(mx_lower.endswith(suffix) for suffix in ACCEPT_ALL_MX_SUFFIXES)


async def is_catch_all(mx_host: str, domain: str) -> bool:
    """Probe domain with a guaranteed-fake address to detect catch-all behavior."""
    fake_email = f"{FAKE_LOCAL}@{domain}"
    result = await check_smtp(mx_host, fake_email)
    return result.status == SmtpStatus.deliverable
