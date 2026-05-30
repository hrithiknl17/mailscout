import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus


class JobResponse(BaseModel):
    job_id: uuid.UUID
    total: int
    status: JobStatus


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: JobStatus
    total_emails: int
    processed: int
    deliverable_count: int
    risky_count: int
    undeliverable_count: int
    dead_domain_count: int
    unknown_count: int
    created_at: datetime
    completed_at: datetime | None
    result_csv_url: str | None
