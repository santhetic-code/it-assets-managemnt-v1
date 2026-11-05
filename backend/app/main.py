import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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

    # Kompresi payload JSON besar agar transfer data lebih cepat
    application.add_middleware(GZipMiddleware, minimum_size=500)

    # Middleware Keamanan Header HTTP
    @application.middleware("http")
    async def security_headers_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    # Global Exception Handler untuk unhandled exception
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
        if isinstance(exc, StarletteHTTPException):
            return await http_exception_handler(request, exc)
        logger.exception("Kesalahan server internal tidak tertangani: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Terjadi kesalahan internal pada server"},
        )

    application.include_router(health.router)
    application.include_router(api_router)
    return application


app = create_app()
