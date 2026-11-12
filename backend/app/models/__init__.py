"""Daftarkan SEMUA model di sini agar terbaca oleh Alembic (autogenerate)."""

from app.models.asset import (
    Asset,
    AssetLink,
    AssetMovement,
    Category,
    PowerAssumption,
    PowerCatalogItem,
    WattScenario,
)
from app.models.audit import AuditLog
from app.models.base import NAMING_CONVENTION, TimestampMixin, utcnow
from app.models.credential import (
    Credential,
    CredentialACL,
    CredentialType,
    Division,
    DivisionGrant,
    RoleTypePermission,
)
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation, IPSubnet
from app.models.maintenance import (
    Location,
    Maintenance,
    MaintenanceLog,
    MaintenancePlan,
    MaintenanceTemplate,
    MaintenanceTicket,
    Vendor,
)
from app.models.user import User, UserRole

__all__ = [
    "NAMING_CONVENTION",
    "Asset",
    "AssetLink",
    "AssetMovement",
    "AuditLog",
    "Category",
    "Credential",
    "CredentialACL",
    "CredentialType",
    "Division",
    "DivisionGrant",
    "IPAllocation",
    "IPSubnet",
    "Location",
    "Maintenance",
    "MaintenanceLog",
    "MaintenancePlan",
    "MaintenanceTemplate",
    "MaintenanceTicket",
    "PowerAssumption",
    "PowerCatalogItem",
    "Purchase",
    "RoleTypePermission",
    "TimestampMixin",
    "User",
    "UserRole",
    "Vendor",
    "WattScenario",
    "utcnow",
]
