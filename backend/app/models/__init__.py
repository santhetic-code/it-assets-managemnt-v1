"""Daftarkan SEMUA model di sini agar terbaca oleh Alembic (autogenerate).

Contoh pada tahap berikutnya:
from app.models.user import User  # noqa: F401
"""

from app.models.base import NAMING_CONVENTION, TimestampMixin, utcnow

__all__ = ["NAMING_CONVENTION", "TimestampMixin", "utcnow"]

