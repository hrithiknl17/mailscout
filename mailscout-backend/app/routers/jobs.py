import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs")


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> JobStatusResponse:
    """Get status and progress for a bulk verification job."""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user.user_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobStatusResponse.model_validate(job)
