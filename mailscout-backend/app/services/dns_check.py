import asyncio
import logging
import socket
from dataclasses import dataclass, field

import dns.asyncresolver
import dns.exception

logger = logging.getLogger(__name__)


@dataclass
class DnsResult:
    has_a_record: bool
    mx_records: list[str] = field(default_factory=list)
    primary_mx: str = ""
    error: str = ""


async def check_domain_a_record(domain: str) -> bool:
    """Return True if domain resolves to an A record."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, socket.gethostbyname, domain)
        return True
    except socket.gaierror:
        return False


async def get_mx_records(domain: str) -> list[str]:
    """Resolve MX records sorted by priority (lowest preference = highest priority)."""
    try:
        answers = await dns.asyncresolver.resolve(domain, "MX")
        sorted_records = sorted(answers, key=lambda r: r.preference)
        return [str(r.exchange).rstrip(".") for r in sorted_records]
    except (dns.exception.DNSException, Exception) as exc:
        logger.debug("MX lookup failed for %s: %s", domain, exc)
        return []


async def check_dns(domain: str) -> DnsResult:
    """Run A-record then MX-record checks. Short-circuits on dead domain."""
    has_a = await check_domain_a_record(domain)
    if not has_a:
        return DnsResult(has_a_record=False, error="Domain does not resolve")

    mx = await get_mx_records(domain)
    return DnsResult(
        has_a_record=True,
        mx_records=mx,
        primary_mx=mx[0] if mx else "",
    )
