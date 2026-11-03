"""Model database untuk Jadwal dan Riwayat Maintenance Aset TI (maintenances)."""

from datetime import date
from typing import Any

from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class Maintenance(TimestampMixin, SQLModel, table=True):
    """Tabel jadwal pemeliharaan rutin, perbaikan, dan riwayat servis aset TI."""

    __tablename__: Any = "maintenances"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kode_maintenance: str = Field(
        index=True,
        unique=True,
        max_length=30,
        nullable=False,
    )

    id_aset: str = Field(index=True, max_length=30, nullable=False)
    nama_aset: str = Field(index=True, max_length=150, nullable=False)
    kategori: str = Field(default="PC", index=True, max_length=50, nullable=False)
    lokasi: str = Field(
        default="Head Office (Office Blok 14)",
        index=True,
        max_length=100,
        nullable=False,
    )

    jenis_maintenance: str = Field(
        default="Preventif",
        index=True,
        max_length=50,
        nullable=False,
    )
    prioritas: str = Field(default="Normal", index=True, max_length=30, nullable=False)
    judul: str = Field(default="", max_length=150, nullable=False)
    deskripsi: str = Field(default="", max_length=500, nullable=False)
    tindakan: str = Field(default="", max_length=500, nullable=False)

    teknisi: str = Field(default="", index=True, max_length=100, nullable=False)
    vendor_servis: str = Field(default="", max_length=120, nullable=False)
    biaya: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
    )

    tanggal_jadwal: date = Field(index=True, nullable=False)
    tanggal_selesai: date | None = Field(default=None, index=True, nullable=True)

    status: str = Field(default="Terjadwal", index=True, max_length=40, nullable=False)
    kondisi_setelah: str = Field(default="Baik", max_length=40, nullable=False)

    # Atribut Jadwal Rutin Berulang
    is_recurring: bool = Field(default=False, index=True, nullable=False)
    siklus: str = Field(default="Sekali", max_length=30, nullable=False)

    catatan: str = Field(default="", max_length=500, nullable=False)

