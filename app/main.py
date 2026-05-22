import logging

from fastapi import FastAPI

from app.core.config import settings
from app.lifespan import lifespan
from app.api.routes import health

logging.basicConfig(level=settings.log_level.upper())

app = FastAPI(
    title="Nukan",
    description="Read-only unofficial API for NovelUpdates metadata.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
