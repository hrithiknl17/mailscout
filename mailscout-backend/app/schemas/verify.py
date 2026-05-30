import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.verification import VerificationStatus


class VerifyRequest(BaseModel):
    email: str


class VerificationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
