import logging
from dataclasses import dataclass, field

from email_validator import EmailNotValidError, validate_email

from app.models.verification import ROLE_ADDRESSES

logger = logging.getLogger(__name__)


@dataclass
class SyntaxResult:
    is_valid: bool
    normalized: str
    local: str
    domain: str
    is_role: bool
    error: str = field(default="")


def check_syntax(email: str) -> SyntaxResult:
    """Validate email syntax per RFC 5322. Returns structured result."""
    try:
        validated = validate_email(email, check_deliverability=False)
        local = validated.local_part
        return SyntaxResult(
            is_valid=True,
            normalized=validated.normalized,
            local=local,
            domain=validated.domain,
            is_role=local.lower() in ROLE_ADDRESSES,
        )
    except EmailNotValidError as exc:
        logger.debug("Syntax invalid for %s: %s", email, exc)
        return SyntaxResult(
            is_valid=False,
            normalized=email,
            local="",
            domain="",
            is_role=False,
            error=str(exc),
        )
