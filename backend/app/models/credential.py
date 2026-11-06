"""Model database untuk penyimpanan kredensial terenkripsi Fernet (credentials)."""

from typing import Any

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class Credential(TimestampMixin, SQLModel, table=True):
    """Tabel kredensial sistem & perangkat TI (password disimpan terenkripsi Fernet)."""

    __tablename__: Any = "credentials"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kode_kredensial: str = Field(
        index=True,
        unique=True,
        max_length=30,
        nullable=False,
    )

    nama_layanan: str = Field(index=True, max_length=150, nullable=False)
    jenis_kredensial: str = Field(
        default="Server",
        index=True,
        max_length=50,
        nullable=False,
    )
    lokasi: str = Field(
        default="Head Office (Office Blok 14)",
        index=True,
        max_length=100,
        nullable=False,
    )
    id_aset: str | None = Field(default=None, index=True, max_length=30, nullable=True)

    ip_address: str = Field(default="", max_length=80, nullable=False)
    port: str = Field(default="", max_length=30, nullable=False)
    url_akses: str = Field(default="", max_length=255, nullable=False)

    username: str = Field(index=True, max_length=120, nullable=False)
    password_encrypted: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    secret_extra_encrypted: str = Field(
        default="",
        sa_column=Column(Text, nullable=False, server_default=""),
    )

    level_akses: str = Field(
        default="Administrator",
        index=True,
        max_length=40,
        nullable=False,
    )
    allowed_roles: list[str] = Field(
        default_factory=lambda: ["Administrator"],
        sa_column=Column(JSON, nullable=False, server_default='["Administrator"]'),
    )

    status: str = Field(default="Aktif", index=True, max_length=30, nullable=False)
    terakhir_diubah_oleh: str = Field(default="admin", max_length=80, nullable=False)
    catatan: str = Field(default="", max_length=500, nullable=False)
