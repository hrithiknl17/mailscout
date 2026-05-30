import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VerificationStatus(str, enum.Enum):
    deliverable = "deliverable"
    undeliverable = "undeliverable"
    risky = "risky"
    invalid_syntax = "invalid_syntax"
    dead_domain = "dead_domain"
    no_mail_server = "no_mail_server"
    temporary_failure = "temporary_failure"
    unknown = "unknown"


ROLE_ADDRESSES: frozenset[str] = frozenset(
    {"info", "admin", "support", "contact", "hello", "sales", "help", "hr", "careers", "jobs"}
)


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(Text)
    status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(Text, default="")
    mx_record: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_catch_all: Mapped[bool] = mapped_column(Boolean, default=False)
    is_disposable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_role: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
