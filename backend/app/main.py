import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    db_url = settings.sqlalchemy_url.render_as_string(hide_password=True)
    logger.info("ITAM Pro API siap (env=%s, db=%s)", settings.app_env, db_url)
    yield


def create_app() -> FastAPI:
    settings = get_settings()  # gagal cepat bila konfigurasi production tidak aman
    setup_logging(settings.log_level)

    application = FastAPI(
        title="ITAM Pro API",
        lifespan=lifespan,
        # Dokumentasi interaktif hanya di dev; backend tidak diekspos ke publik.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    application.include_router(health.router)
    application.include_router(api_router)
    return application


app = create_app()
