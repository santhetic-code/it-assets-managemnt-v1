"""Router induk API v1. Semua modul tahap berikutnya didaftarkan di sini."""

from fastapi import APIRouter

from app.api.v1 import assets, auth, master

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(master.router, prefix="/master", tags=["master"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
