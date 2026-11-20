"""Model database untuk pencatatan jejak audit keamanan & operasional (audit_logs)."""

from typing import Any

from sqlalchemy import JSON, Column, event
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class AuditLogImmutableError(ValueError):
    """Dilempar bila ada upaya mengubah atau menghapus baris AuditLog (append-only)."""


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
    ip_address: str = Field(default="tidak diketahui", max_length=45, nullable=False)
    user_agent: str = Field(default="tidak diketahui", max_length=255, nullable=False)
    changes: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


@event.listens_for(AuditLog, "before_update")
def _prevent_audit_log_update(_mapper: Any, _connection: Any, _target: Any) -> None:
    raise AuditLogImmutableError("Audit log bersifat append-only dan tidak dapat diubah")


@event.listens_for(AuditLog, "before_delete")
def _prevent_audit_log_delete(_mapper: Any, _connection: Any, _target: Any) -> None:
    raise AuditLogImmutableError("Audit log bersifat append-only dan tidak dapat dihapus")
