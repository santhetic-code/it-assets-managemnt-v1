"""Model database untuk pencatatan jejak audit keamanan & operasional (audit_logs)."""

from typing import Any

from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class AuditLog(TimestampMixin, SQLModel, table=True):
    """Tabel log audit aktivitas pengguna dan sistem ITAM Pro."""

    __tablename__: Any = "audit_logs"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kode_audit: str = Field(
        index=True,
        unique=True,
        max_length=30,
        nullable=False,
    )

    username: str = Field(index=True, max_length=50, nullable=False)
    nama_pengguna: str = Field(default="", max_length=100, nullable=False)
    role: str = Field(default="Viewer", index=True, max_length=30, nullable=False)

    aksi: str = Field(index=True, max_length=60, nullable=False)
    modul: str = Field(index=True, max_length=50, nullable=False)
    target_id: str = Field(default="-", index=True, max_length=80, nullable=False)
    detail: str = Field(default="", max_length=500, nullable=False)

    level_risiko: str = Field(default="Rendah", index=True, max_length=30, nullable=False)
    status: str = Field(default="Sukses", index=True, max_length=30, nullable=False)
    ip_address: str = Field(default="127.0.0.1", max_length=45, nullable=False)

