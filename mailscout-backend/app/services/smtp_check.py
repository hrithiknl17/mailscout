import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)

RETRY_DELAY_SECONDS = 5
GREYLIST_CODES: frozenset[int] = frozenset({421, 450, 451, 452})
REJECT_CODES: frozenset[int] = frozenset({550, 551, 552, 553})


class SmtpStatus(str, Enum):
    deliverable = "deliverable"
    undeliverable = "undeliverable"
    temporary_failure = "temporary_failure"
    port_blocked = "port_blocked"   # connection refused / timeout on port 25
    unknown = "unknown"


@dataclass
class SmtpResult:
    status: SmtpStatus
    code: int = 0
    message: str = ""


async def _attempt_smtp(mx_host: str, email: str) -> SmtpResult:
    """Single SMTP probe: connect → HELO → MAIL FROM → RCPT TO → QUIT. Never sends DATA."""
    helo_domain = settings.mailscout_helo_domain
    sender = settings.mailscout_sender_email
    smtp = aiosmtplib.SMTP(
        hostname=mx_host,
        port=25,
        timeout=settings.smtp_timeout_seconds,
    )
    try:
        await smtp.connect()
        await smtp.helo(helo_domain)
        await smtp.mail(sender)
        try:
            code, message = await smtp.rcpt(email)
        except aiosmtplib.SMTPRecipientsRefused as exc:
            code, raw_msg = next(iter(exc.recipients.values()))
            message = raw_msg.decode() if isinstance(raw_msg, bytes) else str(raw_msg)
            await smtp.quit()
            if code in REJECT_CODES:
                return SmtpResult(SmtpStatus.undeliverable, code, message)
            if code in GREYLIST_CODES:
                return SmtpResult(SmtpStatus.temporary_failure, code, message)
            return SmtpResult(SmtpStatus.unknown, code, message)

        if code == 250:
            status = SmtpStatus.deliverable
        elif code in REJECT_CODES:
            status = SmtpStatus.undeliverable
        elif code in GREYLIST_CODES:
            status = SmtpStatus.temporary_failure
        else:
            status = SmtpStatus.unknown
        return SmtpResult(status, code, message)

    except (aiosmtplib.SMTPConnectError, aiosmtplib.SMTPTimeoutError, OSError) as exc:
        logger.warning("SMTP port 25 unreachable for %s: %s", mx_host, exc)
        return SmtpResult(SmtpStatus.port_blocked, 0, "SMTP unavailable (port 25 blocked or timed out)")
    except aiosmtplib.SMTPException as exc:
        logger.debug("SMTP error for %s via %s: %s", email, mx_host, exc)
        return SmtpResult(SmtpStatus.unknown, 0, str(exc))
    finally:
        try:
            await smtp.quit()
        except Exception:
            pass


async def check_smtp(mx_host: str, email: str) -> SmtpResult:
    """SMTP handshake with one retry on greylisting (4xx temporary failures)."""
    result = await _attempt_smtp(mx_host, email)
    if result.status == SmtpStatus.temporary_failure:
        logger.info("Greylisted for %s, retrying in %ds", email, RETRY_DELAY_SECONDS)
        await asyncio.sleep(RETRY_DELAY_SECONDS)
        retry = await _attempt_smtp(mx_host, email)
        if retry.status == SmtpStatus.temporary_failure:
            return SmtpResult(SmtpStatus.unknown, retry.code, "Still greylisted after retry")
        return retry
    return result
