import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.config import settings
from app.database import get_db
from app.models.verification import Verification
from app.schemas.verify import VerificationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

MAX_HISTORY_LIMIT = 100


@router.get("/history", response_model=list[VerificationResult])
async def get_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[VerificationResult]:
    """Return user's single-email verification history, newest first."""
    limit = min(limit, MAX_HISTORY_LIMIT)
    result = await db.execute(
        select(Verification)
        .where(Verification.user_id == user.user_id)
        .order_by(Verification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.scalars().all()
    return [VerificationResult.model_validate(row) for row in rows]


@router.get("/usage")
async def get_usage(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Return monthly usage count and limit for the current user."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count(Verification.id)).where(
            Verification.user_id == user.user_id,
            extract("year", Verification.created_at) == now.year,
            extract("month", Verification.created_at) == now.month,
        )
    )
    used = result.scalar_one()

    if now.month == 12:
        renews_at = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        renews_at = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)

    return {
        "used_this_month": used,
        "monthly_limit": settings.mailscout_free_tier_limit,
        "renews_at": renews_at.date().isoformat(),
    }
