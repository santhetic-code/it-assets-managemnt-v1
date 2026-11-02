"""Router induk API v1. Semua modul tahap berikutnya didaftarkan di sini."""

from fastapi import APIRouter

from app.api.v1 import auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
