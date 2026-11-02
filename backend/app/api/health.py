"""Endpoint kesehatan (tanpa autentikasi)."""

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.deps import SessionDep

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: proses hidup. Tidak menyentuh database."""
    return {"status": "ok"}


@router.get("/health/db")
def health_db(session: SessionDep) -> dict[str, str]:
    """Readiness: database dapat dijangkau."""
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Health check database gagal: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database tidak dapat dijangkau",
        ) from exc
    return {"status": "ok", "database": "ok"}

