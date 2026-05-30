import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, history, jobs, verify

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="MailScout API",
    description="Open-source email verification SaaS — an alternative to Hunter.io and NeverBounce",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# allow_credentials=True cannot be combined with allow_origins=["*"] — browsers reject it.
# In prod, set FRONTEND_URL to the Vercel deployment URL.
_origins = (
    [o.strip() for o in settings.frontend_url.split(",") if o.strip()]
    if settings.frontend_url
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=bool(settings.frontend_url),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(verify.router)
app.include_router(jobs.router)
app.include_router(history.router)
