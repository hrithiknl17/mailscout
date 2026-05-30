import csv
import io
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.config import settings
from app.database import get_db
from app.models.job import Job, JobStatus
from app.models.verification import Verification
from app.schemas.job import JobResponse
from app.schemas.verify import VerificationResult, VerifyRequest
from app.services.verifier import verify_email
from app.workers.bulk_verify import process_bulk_job

logger = logging.getLogger(__name__)

MAX_BULK_EMAILS = 10_000

router = APIRouter(prefix="/api/verify")


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency: yields a Redis client."""
    r = aioredis.from_url(settings.redis_url)
    try:
        yield r
    finally:
        await r.aclose()


async def _check_monthly_limit(user_id: str, db: AsyncSession) -> int:
    """Return how many verifications user ran this calendar month."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count(Verification.id)).where(
            Verification.user_id == user_id,
            extract("year", Verification.created_at) == now.year,
            extract("month", Verification.created_at) == now.month,
        )
    )
    return result.scalar_one()


@router.post("/single", response_model=VerificationResult)
async def verify_single(
    body: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: CurrentUser = Depends(get_current_user),
) -> VerificationResult:
    """Verify a single email address through the 4-layer pipeline."""
    used = await _check_monthly_limit(user.user_id, db)
    if used >= settings.mailscout_free_tier_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly limit of {settings.mailscout_free_tier_limit} reached",
        )

    result = await verify_email(body.email, user.user_id, redis)

    row = Verification(
        id=result.id,
        user_id=user.user_id,
        email=result.email,
        status=result.status,
        confidence=result.confidence,
        reason=result.reason,
        mx_record=result.mx_record,
        is_catch_all=result.is_catch_all,
        is_disposable=result.is_disposable,
        is_role=result.is_role,
        created_at=result.created_at,
    )
    db.add(row)
    await db.commit()

    return VerificationResult.model_validate(row)


@router.post("/bulk", response_model=JobResponse)
async def verify_bulk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> JobResponse:
    """Queue bulk email verification from a CSV (email column) or TXT (one per line) file."""
    content = await file.read()
    text = content.decode("utf-8", errors="replace")

    filename = file.filename or ""
    emails = _parse_csv(text) if filename.endswith(".csv") else _parse_txt(text)

    if not emails:
        raise HTTPException(status_code=400, detail="No emails found in file")
    if len(emails) > MAX_BULK_EMAILS:
        raise HTTPException(
            status_code=400, detail=f"Max {MAX_BULK_EMAILS} emails per upload"
        )

    job = Job(
        id=uuid.uuid4(),
        user_id=user.user_id,
        status=JobStatus.queued,
        total_emails=len(emails),
    )
    db.add(job)
    await db.commit()

    background_tasks.add_task(process_bulk_job, str(job.id), emails, user.user_id)
    return JobResponse(job_id=job.id, total=len(emails), status=JobStatus.queued)


def _parse_csv(text: str) -> list[str]:
    """Extract email addresses from a CSV file with an 'email' column."""
    reader = csv.DictReader(io.StringIO(text))
    emails: list[str] = []
    for row in reader:
        email = row.get("email") or row.get("Email") or row.get("EMAIL") or ""
        if email.strip():
            emails.append(email.strip())
    return emails


def _parse_txt(text: str) -> list[str]:
    """Extract email addresses from a plain-text file (one per line)."""
    return [line.strip() for line in text.splitlines() if line.strip()]
