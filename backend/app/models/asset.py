"""Model database untuk tabel aset TI (assets)."""

from datetime import date
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class Asset(TimestampMixin, SQLModel, table=True):
    """Tabel inventaris aset TI perusahaan."""

    __tablename__: Any = "assets"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    id_aset: str = Field(index=True, unique=True, max_length=30, nullable=False)
    nama_aset: str = Field(index=True, max_length=150, nullable=False)
    kategori: str = Field(index=True, max_length=50, nullable=False)
    merek: str = Field(default="", max_length=100, nullable=False)
    model: str = Field(default="", max_length=100, nullable=False)
    serial_number: str | None = Field(
        default=None,
        index=True,
        max_length=100,
        nullable=True,
    )
    lokasi: str = Field(index=True, max_length=100, nullable=False)
    detail_lokasi: str = Field(default="", max_length=150, nullable=False)
    penanggung_jawab: str = Field(default="", max_length=100, nullable=False)
    status: str = Field(default="Aktif", index=True, max_length=40, nullable=False)
    kondisi: str = Field(default="Baik", max_length=40, nullable=False)
    tanggal_masuk: date | None = Field(default=None, nullable=True)

    # Spesifikasi PC / Server / Laptop (tanpa Power Supply & tanpa Casing)
    processor: str = Field(default="", max_length=120, nullable=False)
    motherboard: str = Field(default="", max_length=120, nullable=False)
    ram: str = Field(default="", max_length=80, nullable=False)
    storage: str = Field(default="", max_length=120, nullable=False)
    gpu: str = Field(default="", max_length=120, nullable=False)
    os: str = Field(default="", max_length=80, nullable=False)
    watt: int = Field(default=0, nullable=False)

    # Spesifikasi Monitor
    ukuran_layar: str = Field(default="", max_length=50, nullable=False)
    resolusi: str = Field(default="", max_length=50, nullable=False)
    panel: str = Field(default="", max_length=50, nullable=False)
    port_display: str = Field(default="", max_length=100, nullable=False)

    # Spesifikasi UPS
    kapasitas_va: int = Field(default=0, nullable=False)
    kapasitas_watt: int = Field(default=0, nullable=False)
    baterai: str = Field(default="", max_length=120, nullable=False)
    jumlah_baterai: int = Field(default=0, nullable=False)
    beban_perangkat: str = Field(default="", max_length=255, nullable=False)

    # Spesifikasi Jaringan / CCTV / Printer
    ip_address: str = Field(default="", max_length=50, nullable=False)
    mac_address: str = Field(default="", max_length=50, nullable=False)
    koneksi: str = Field(default="", max_length=80, nullable=False)

    catatan: str = Field(default="", max_length=500, nullable=False)
    extra_specs: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )

