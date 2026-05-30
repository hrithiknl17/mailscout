import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.queued)
    total_emails: Mapped[int] = mapped_column(Integer)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    deliverable_count: Mapped[int] = mapped_column(Integer, default=0)
    risky_count: Mapped[int] = mapped_column(Integer, default=0)
    undeliverable_count: Mapped[int] = mapped_column(Integer, default=0)
    dead_domain_count: Mapped[int] = mapped_column(Integer, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_csv_url: Mapped[str | None] = mapped_column(Text, nullable=True)
