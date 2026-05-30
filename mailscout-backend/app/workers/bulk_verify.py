import asyncio
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.job import Job, JobStatus
from app.models.verification import Verification, VerificationStatus
from app.services.verifier import EmailCheckResult, verify_email

logger = logging.getLogger(__name__)

BATCH_SIZE = 20

_STATUS_BUCKET: dict[VerificationStatus, str] = {
    VerificationStatus.deliverable: "deliverable",
    VerificationStatus.risky: "risky",
    VerificationStatus.undeliverable: "undeliverable",
    VerificationStatus.dead_domain: "dead_domain",
    VerificationStatus.no_mail_server: "dead_domain",
    VerificationStatus.invalid_syntax: "unknown",
    VerificationStatus.temporary_failure: "unknown",
    VerificationStatus.unknown: "unknown",
}


async def process_bulk_job(job_id: str, emails: list[str], user_id: str) -> None:
    """Entry point for background bulk verification task."""
    redis = aioredis.from_url(settings.redis_url)
    try:
        await _run_job(job_id, emails, user_id, redis)
    except Exception as exc:
        logger.error("Bulk job %s failed: %s", job_id, exc)
        await _set_job_status(job_id, JobStatus.failed)
    finally:
        await redis.aclose()


async def _run_job(
    job_id: str, emails: list[str], user_id: str, redis: aioredis.Redis
) -> None:
    """Process all emails in concurrent batches of BATCH_SIZE."""
    await _set_job_status(job_id, JobStatus.running)
    counts: dict[str, int] = {
        "deliverable": 0, "risky": 0, "undeliverable": 0,
        "dead_domain": 0, "unknown": 0,
    }
    all_results: list[EmailCheckResult] = []

    for i in range(0, len(emails), BATCH_SIZE):
        batch = emails[i : i + BATCH_SIZE]
        tasks = [verify_email(email, user_id, redis) for email in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for item in batch_results:
            if isinstance(item, BaseException):
                logger.warning("Verification error in batch: %s", item)
                counts["unknown"] += 1
                continue
            all_results.append(item)
            counts[_STATUS_BUCKET.get(item.status, "unknown")] += 1

        await _update_progress(job_id, i + len(batch), counts)

    await _save_results(all_results, user_id)
    await _complete_job(job_id, counts)


async def _set_job_status(job_id: str, new_status: JobStatus) -> None:
    """Update job status in the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job:
            job.status = new_status
            await session.commit()


async def _update_progress(job_id: str, processed: int, counts: dict[str, int]) -> None:
    """Persist current processed count and per-status counters."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job:
            job.processed = processed
            job.deliverable_count = counts["deliverable"]
            job.risky_count = counts["risky"]
            job.undeliverable_count = counts["undeliverable"]
            job.dead_domain_count = counts["dead_domain"]
            job.unknown_count = counts["unknown"]
            await session.commit()


async def _save_results(results: list[EmailCheckResult], user_id: str) -> None:
    """Bulk-insert all verification results."""
    if not results:
        return
    async with AsyncSessionLocal() as session:
        rows = [
            Verification(
                id=r.id, user_id=user_id, email=r.email, status=r.status,
                confidence=r.confidence, reason=r.reason, mx_record=r.mx_record,
                is_catch_all=r.is_catch_all, is_disposable=r.is_disposable,
                is_role=r.is_role, created_at=r.created_at,
            )
            for r in results
        ]
        session.add_all(rows)
        await session.commit()


async def _complete_job(job_id: str, counts: dict[str, int]) -> None:
    """Mark job as completed and record the completion timestamp."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job:
            job.status = JobStatus.completed
            job.completed_at = datetime.now(timezone.utc)
            job.deliverable_count = counts["deliverable"]
            job.risky_count = counts["risky"]
            job.undeliverable_count = counts["undeliverable"]
            job.dead_domain_count = counts["dead_domain"]
            job.unknown_count = counts["unknown"]
            await session.commit()
