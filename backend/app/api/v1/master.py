"""Endpoint referensi Data Master untuk dropdown & konfigurasi form frontend."""

from typing import Any

from fastapi import APIRouter

from app.core.master_data import get_master_data_payload
from app.deps import CurrentUserDep

router = APIRouter()


@router.get("", response_model=dict[str, Any])
def get_master_data(_: CurrentUserDep) -> dict[str, Any]:
    """Mengembalikan daftar lokasi, kategori, status, kondisi, dan prefix ID aset."""
    return get_master_data_payload()

