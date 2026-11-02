"""Router induk API v1. Semua modul tahap berikutnya didaftarkan di sini.

Contoh (B1): api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
"""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

