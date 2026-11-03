"""Daftarkan SEMUA model di sini agar terbaca oleh Alembic (autogenerate)."""

from app.models.asset import Asset
from app.models.base import NAMING_CONVENTION, TimestampMixin, utcnow
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation
from app.models.maintenance import Maintenance
from app.models.user import User, UserRole

__all__ = [
    "NAMING_CONVENTION",
    "Asset",
    "IPAllocation",
    "Maintenance",
    "Purchase",
    "TimestampMixin",
    "User",
    "UserRole",
    "utcnow",
]
