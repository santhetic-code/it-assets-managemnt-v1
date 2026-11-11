"""Model database untuk Jadwal dan Riwayat Maintenance Aset TI (maintenances)."""

from datetime import date
from typing import Any

from sqlalchemy import JSON, BigInteger, Column
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


class Location(TimestampMixin, SQLModel, table=True):
    """Tabel lokasi 2 tingkat: Lokasi Induk (Kantor Blok 12) > Ruangan (Ruang Kerja)."""

    __tablename__: Any = "locations"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    parent_id: int | None = Field(default=None, index=True, nullable=True)
    nama: str = Field(index=True, max_length=120, nullable=False)


class Vendor(TimestampMixin, SQLModel, table=True):
    """Tabel daftar vendor layanan maintenance (Teknisi AC, Servis Genset, dll.)."""

    __tablename__: Any = "vendors"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    nama: str = Field(index=True, max_length=120, nullable=False)
    jenis_layanan: str = Field(default="AC & Pendingin", max_length=80, nullable=False)
    kontak: str = Field(default="", max_length=100, nullable=False)
    catatan: str = Field(default="", max_length=500, nullable=False)


class MaintenanceTemplate(TimestampMixin, SQLModel, table=True):
    """Tabel template rencana maintenance
    (PC, Server, UPS, AC, Genset, Jaringan, Kendaraan, Fasilitas).
    """

    __tablename__: Any = "maintenance_templates"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    nama: str = Field(index=True, max_length=100, nullable=False)
    kategori_objek: str = Field(index=True, max_length=60, nullable=False)
    kegiatan: str = Field(default="", max_length=150, nullable=False)
    jenis: str = Field(default="Preventif", max_length=40, nullable=False)
    interval_nilai: int = Field(default=3, nullable=False)
    interval_satuan: str = Field(default="bulan", max_length=20, nullable=False)
    interval_pemakaian: int | None = Field(default=None, nullable=True)
    satuan_pemakaian: str = Field(default="jam", max_length=20, nullable=False)
    checklist: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    pelaksana_default: str = Field(default="Internal", max_length=30, nullable=False)


class MaintenancePlan(TimestampMixin, SQLModel, table=True):
    """Tabel aturan berulang (Rencana) yang menghasilkan tugas jatuh tempo (Jadwal)."""

    __tablename__: Any = "maintenance_plans"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kode_rencana: str = Field(index=True, unique=True, max_length=30, nullable=False)
    template_id: int | None = Field(default=None, index=True, nullable=True)
    kegiatan: str = Field(max_length=150, nullable=False)
    jenis: str = Field(default="Preventif", index=True, max_length=40, nullable=False)
    objek_tipe: str = Field(
        default="aset", index=True, max_length=30, nullable=False
    )  # aset | kelompok | lokasi
    asset_id: str | None = Field(default=None, index=True, max_length=30, nullable=True)
    kategori_objek: str = Field(default="PC", index=True, max_length=60, nullable=False)
    lokasi_nama: str = Field(
        default="Kantor Blok 14", index=True, max_length=120, nullable=False
    )
    ruangan_nama: str = Field(default="", max_length=120, nullable=False)
    filter_kelompok: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    jumlah_unit_manual: int = Field(default=1, nullable=False)
    interval_nilai: int = Field(default=3, nullable=False)
    interval_satuan: str = Field(default="bulan", max_length=20, nullable=False)
    interval_pemakaian: int | None = Field(default=None, nullable=True)
    hitung_dari: str = Field(default="tanggal_selesai", max_length=40, nullable=False)
    last_done_at: date | None = Field(default=None, nullable=True)
    last_result: str = Field(default="—", max_length=200, nullable=False)
    last_meter: int = Field(default=0, nullable=False)
    current_meter: int = Field(default=0, nullable=False)
    next_due_at: date | None = Field(default=None, index=True, nullable=True)
    pelaksana_tipe: str = Field(
        default="Internal", index=True, max_length=20, nullable=False
    )
    pic_user_id: int | None = Field(default=None, nullable=True)
    vendor_id: int | None = Field(default=None, nullable=True)
    pelaksana_nama: str = Field(
        default="Ridho", index=True, max_length=100, nullable=False
    )
    pengingat: list[int] = Field(
        default_factory=lambda: [7, 1],
        sa_column=Column(JSON, nullable=False, server_default="[7, 1]"),
    )
    checklist: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    aktif: bool = Field(default=True, index=True, nullable=False)
    created_by: str = Field(default="admin", max_length=80, nullable=False)


class MaintenanceLog(TimestampMixin, SQLModel, table=True):
    """Tabel catatan penyelesaian maintenance (Riwayat)."""

    __tablename__: Any = "maintenance_logs"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    plan_id: int | None = Field(default=None, index=True, nullable=True)
    kode_rencana: str = Field(default="", index=True, max_length=30, nullable=False)
    asset_id: str | None = Field(default=None, index=True, max_length=30, nullable=True)
    objek_display: str = Field(default="", max_length=200, nullable=False)
    kegiatan: str = Field(default="", max_length=150, nullable=False)
    jenis: str = Field(default="Preventif", max_length=40, nullable=False)
    dikerjakan_pada: date = Field(index=True, nullable=False)
    unit_dikerjakan: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    pelaksana_tipe: str = Field(default="Internal", max_length=20, nullable=False)
    pelaksana: str = Field(default="Ridho", index=True, max_length=100, nullable=False)
    biaya: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
    )
    nomor_nota: str = Field(default="", max_length=80, nullable=False)
    hasil_catatan: str = Field(default="", max_length=500, nullable=False)
    checklist_hasil: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    meter_reading: int | None = Field(default=None, nullable=True)
    lampiran: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    ada_temuan: bool = Field(default=False, index=True, nullable=False)
    repair_ticket_id: int | None = Field(default=None, nullable=True)
    purchase_id: int | None = Field(default=None, nullable=True)
    created_by: str = Field(default="admin", max_length=80, nullable=False)


class MaintenanceTicket(TimestampMixin, SQLModel, table=True):
    """Tabel tiket perbaikan dari hasil temuan maintenance (Bagian A.6 & B)."""

    __tablename__: Any = "maintenance_tickets"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    plan_id: int | None = Field(default=None, index=True, nullable=True)
    asset_id: str | None = Field(default=None, index=True, max_length=30, nullable=True)
    target_label: str = Field(default="", max_length=200, nullable=False)
    dilaporkan_oleh: str = Field(default="admin", max_length=80, nullable=False)
    masalah: str = Field(default="", max_length=500, nullable=False)
    status: str = Field(
        default="Dilaporkan", index=True, max_length=30, nullable=False
    )  # Dilaporkan | Dikerjakan | Selesai
    tanggal: date = Field(default_factory=date.today, index=True, nullable=False)
