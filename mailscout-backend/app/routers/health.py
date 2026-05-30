import logging

import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


async def _check_db() -> str:
    """Ping the database with a trivial query."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return "error"


async def _check_redis() -> str:
    """Ping Redis."""
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        return "ok"
    except Exception as exc:
        logger.error("Redis health check failed: %s", exc)
        return "error"


@router.get("/health")
async def health() -> dict:
    """Public health check. Returns status of API, database, and Redis."""
    db_status = await _check_db()
    redis_status = await _check_redis()
    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return {
        "status": overall,
        "version": settings.app_version,
        "checks": {"db": db_status, "redis": redis_status},
    }
