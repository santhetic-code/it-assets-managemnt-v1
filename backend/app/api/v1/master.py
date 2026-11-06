"""Endpoint referensi Data Master untuk dropdown & konfigurasi form frontend."""

from typing import Any

from fastapi import APIRouter

from app.core.csv_importer import import_all_csv_data
from app.core.master_data import get_master_data_payload
from app.deps import AdminUserDep, CurrentUserDep, SessionDep

router = APIRouter()


@router.get("", response_model=dict[str, Any])
def get_master_data(_: CurrentUserDep) -> dict[str, Any]:
    """Mengembalikan daftar lokasi, kategori, status, kondisi, dan prefix ID aset."""
    return get_master_data_payload()


@router.post("/import-csv", response_model=dict[str, Any])
def import_csv_data(
    session: SessionDep,
    current_admin: AdminUserDep,
) -> dict[str, Any]:
    """Mengimpor seluruh data CSV operasional ke database (khusus Administrator)."""
    return import_all_csv_data(session, username=current_admin.username)
