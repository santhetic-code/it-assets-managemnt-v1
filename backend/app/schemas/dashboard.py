"""Skema Pydantic untuk respons agregasi Dashboard utama ITAM Pro (B8)."""

from typing import Any

from pydantic import BaseModel

from app.schemas.audit import AuditLogPublic
from app.schemas.finance import PurchasePublic
from app.schemas.maintenance import MaintenancePublic


class DashboardAlertItem(BaseModel):
    """Item peringatan operasional/keamanan pada Dashboard."""

    kategori: str
    judul: str
    pesan: str
    tingkat: str
    jumlah: int


class DashboardResponse(BaseModel):
    """Respons terpadu GET /api/v1/dashboard (dan /summary) sesuai kontrak frontend."""

    kpi: dict[str, Any]
    kpis: dict[str, Any] = {}
    summary: dict[str, Any]
    asset_by_category: list[dict[str, Any]]
    assets_by_category: list[dict[str, Any]] = []
    distribusi_kategori: list[dict[str, Any]]
    asset_by_location: list[dict[str, Any]]
    distribusi_lokasi: list[dict[str, Any]]
    asset_by_status: dict[str, int]
    monthly_purchases: list[dict[str, Any]] = []
    ups_loads: list[dict[str, Any]] = []
    attention_items: list[dict[str, Any]] = []
    upcoming_maintenance: list[MaintenancePublic]
    jadwal_maintenance: list[MaintenancePublic]
    upcoming_bills: list[PurchasePublic]
    tagihan_mendatang: list[PurchasePublic]
    recent_activities: list[AuditLogPublic]
    aktivitas_terbaru: list[AuditLogPublic]
    alerts: list[DashboardAlertItem]
    peringatan: list[DashboardAlertItem]

