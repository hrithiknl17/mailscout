import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import redis.asyncio as aioredis
import redis.exceptions as _redis_exc

from app.models.verification import VerificationStatus
from app.services.catch_all import is_accept_all_provider, is_catch_all
from app.services.dns_check import check_dns
from app.services.smtp_check import SmtpStatus, check_smtp
from app.services.syntax_check import check_syntax

logger = logging.getLogger(__name__)

_REDIS_ERRORS = (_redis_exc.ConnectionError, _redis_exc.TimeoutError)


async def _cache_get(redis_client: aioredis.Redis, key: str) -> bytes | None:
    try:
        return await redis_client.get(key)
    except _REDIS_ERRORS:
        logger.warning("Redis unavailable, skipping cache")
        return None


async def _cache_set(redis_client: aioredis.Redis, key: str, ttl: int, value: str) -> None:
    try:
        await redis_client.setex(key, ttl, value)
    except _REDIS_ERRORS:
        pass  # already warned on get; silently skip


MX_CACHE_TTL = 86400       # 24 hours
CATCH_ALL_CACHE_TTL = 604800  # 7 days
CONFIDENCE_SMTP = 0.95
CONFIDENCE_ACCEPT_ALL = 0.5
CONFIDENCE_CATCH_ALL = 0.6
CONFIDENCE_UNKNOWN = 0.3


@dataclass
class EmailCheckResult:
    id: uuid.UUID
    email: str
    status: VerificationStatus
    confidence: float
    reason: str
    mx_record: str | None
    is_catch_all: bool
    is_disposable: bool
    is_role: bool
    created_at: datetime


async def verify_email(
    email: str,
    user_id: str,
    redis_client: aioredis.Redis,
) -> EmailCheckResult:
    """Run 4-layer email verification pipeline and return a structured result."""
    result_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Layer 1 — Syntax
    syntax = check_syntax(email)
    if not syntax.is_valid:
        return EmailCheckResult(
            id=result_id, email=email,
            status=VerificationStatus.invalid_syntax, confidence=1.0,
            reason=syntax.error, mx_record=None,
            is_catch_all=False, is_disposable=False, is_role=False,
            created_at=now,
        )

    domain = syntax.domain
    is_role = syntax.is_role

    # Layers 2 + 3 — DNS + MX (with Redis cache)
    cache_key = f"mx:{domain}"
    cached_mx = await _cache_get(redis_client, cache_key)

    if cached_mx is not None:
        mx_list: list[str] = cached_mx.decode().split(",") if cached_mx != b"NONE" else []
    else:
        dns_result = await check_dns(domain)
        if not dns_result.has_a_record:
            return EmailCheckResult(
                id=result_id, email=syntax.normalized,
                status=VerificationStatus.dead_domain, confidence=1.0,
                reason="Domain does not resolve", mx_record=None,
                is_catch_all=False, is_disposable=False, is_role=is_role,
                created_at=now,
            )
        mx_list = dns_result.mx_records
        cache_val = ",".join(mx_list) if mx_list else "NONE"
        await _cache_set(redis_client, cache_key, MX_CACHE_TTL, cache_val)

    if not mx_list:
        return EmailCheckResult(
            id=result_id, email=syntax.normalized,
            status=VerificationStatus.no_mail_server, confidence=1.0,
            reason="Domain has no MX records", mx_record=None,
            is_catch_all=False, is_disposable=False, is_role=is_role,
            created_at=now,
        )

    primary_mx = mx_list[0]

    # Layer 4a — Accept-all provider
    if is_accept_all_provider(domain, primary_mx):
        return EmailCheckResult(
            id=result_id, email=syntax.normalized,
            status=VerificationStatus.risky, confidence=CONFIDENCE_ACCEPT_ALL,
            reason="Provider refuses SMTP verification (accept-all)",
            mx_record=primary_mx, is_catch_all=False, is_disposable=False,
            is_role=is_role, created_at=now,
        )

    # Layer 4b — Catch-all detection (with Redis cache)
    catch_all_key = f"catchall:{domain}"
    cached_catch = await _cache_get(redis_client, catch_all_key)
    if cached_catch is not None:
        domain_is_catch_all = cached_catch == b"true"
    else:
        domain_is_catch_all = await is_catch_all(primary_mx, domain)
        await _cache_set(
            redis_client, catch_all_key,
            CATCH_ALL_CACHE_TTL,
            "true" if domain_is_catch_all else "false",
        )

    if domain_is_catch_all:
        return EmailCheckResult(
            id=result_id, email=syntax.normalized,
            status=VerificationStatus.risky, confidence=CONFIDENCE_CATCH_ALL,
            reason="Domain accepts all addresses (catch-all)",
            mx_record=primary_mx, is_catch_all=True, is_disposable=False,
            is_role=is_role, created_at=now,
        )

    # Layer 4c — SMTP handshake
    smtp_result = await check_smtp(primary_mx, syntax.normalized)
    status_map: dict[SmtpStatus, tuple[VerificationStatus, float, str]] = {
        SmtpStatus.deliverable: (VerificationStatus.deliverable, CONFIDENCE_SMTP, "SMTP 250 OK"),
        SmtpStatus.undeliverable: (VerificationStatus.undeliverable, CONFIDENCE_SMTP, "SMTP rejected address"),
        SmtpStatus.temporary_failure: (VerificationStatus.temporary_failure, 0.5, "Greylisted, retry later"),
        SmtpStatus.port_blocked: (VerificationStatus.risky, CONFIDENCE_CATCH_ALL, "SMTP unavailable (port 25 blocked or timed out)"),
        SmtpStatus.unknown: (VerificationStatus.unknown, CONFIDENCE_UNKNOWN, smtp_result.message or "SMTP check inconclusive"),
    }
    v_status, confidence, reason = status_map[smtp_result.status]

    return EmailCheckResult(
        id=result_id, email=syntax.normalized,
        status=v_status, confidence=confidence,
        reason=reason, mx_record=primary_mx,
        is_catch_all=False, is_disposable=False, is_role=is_role,
        created_at=now,
    )
