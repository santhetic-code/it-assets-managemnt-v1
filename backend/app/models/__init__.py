"""Daftarkan SEMUA model di sini agar terbaca oleh Alembic (autogenerate)."""

from app.models.asset import Asset
from app.models.audit import AuditLog
from app.models.base import NAMING_CONVENTION, TimestampMixin, utcnow
from app.models.credential import Credential
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation, IPSubnet
from app.models.maintenance import Maintenance
from app.models.user import User, UserRole

__all__ = [
    "NAMING_CONVENTION",
    "Asset",
    "AuditLog",
    "Credential",
    "IPAllocation",
    "IPSubnet",
    "Maintenance",
    "Purchase",
    "TimestampMixin",
    "User",
    "UserRole",
    "utcnow",
]
