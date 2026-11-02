"""Fondasi model: aturan penamaan constraint dan mixin timestamp."""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

# Nama constraint yang konsisten membuat migrasi Alembic di PostgreSQL dapat diprediksi.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

SQLModel.metadata.naming_convention = NAMING_CONVENTION


def utcnow() -> datetime:
    """Waktu sekarang dalam UTC (timezone-aware). Semua timestamp disimpan UTC."""
    return datetime.now(UTC)


class TimestampMixin(SQLModel):
    """Tambahkan `created_at` dan `updated_at` ke model tabel."""

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utcnow},
        nullable=False,
    )

