"""Model database untuk tabel aset TI (assets)."""

from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin, utcnow


class Category(TimestampMixin, SQLModel, table=True):
    """Tabel pohon kategori aset schema-driven (Seksi 4.2)."""

    __tablename__: Any = "categories"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    parent_id: int | None = Field(default=None, index=True, nullable=True)
    kode: str = Field(index=True, unique=True, max_length=30, nullable=False)
    nama: str = Field(index=True, max_length=100, nullable=False)
    ikon: str = Field(default="box", max_length=50, nullable=False)
    tracking: str = Field(
        default="unit", max_length=20, nullable=False
    )  # "unit" | "threshold" | "stok"
    spec_schema: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )


class AssetLink(SQLModel, table=True):
    """Tabel relasi antar aset (Seksi 4.4: menyuplai_daya, terpasang, backup_dari)."""

    __tablename__: Any = "asset_links"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, max_length=30, nullable=False)
    linked_asset_id: str = Field(index=True, max_length=30, nullable=False)
    tipe: str = Field(default="menyuplai_daya", index=True, max_length=40, nullable=False)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=cast(Any, DateTime(timezone=True)),
        nullable=False,
    )


class AssetMovement(SQLModel, table=True):
    """Tabel riwayat mutasi, serah terima, dan pasang/lepas komponen (Seksi 4.4)."""

    __tablename__: Any = "asset_movements"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, max_length=30, nullable=False)
    jenis: str = Field(index=True, max_length=40, nullable=False)
    dari: str = Field(default="", max_length=150, nullable=False)
    ke: str = Field(default="", max_length=150, nullable=False)
    alasan: str = Field(default="", max_length=150, nullable=False)
    catatan: str = Field(default="", max_length=500, nullable=False)
    tanggal: date = Field(default_factory=date.today, nullable=False)
    oleh: str = Field(default="admin", max_length=80, nullable=False)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=cast(Any, DateTime(timezone=True)),
        nullable=False,
    )


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

    # Kolom Satu Data Induk (Seksi 4.1 & 4.6)
    asset_tag: str | None = Field(
        default=None, index=True, unique=True, max_length=30, nullable=True
    )
    nama: str = Field(default="", max_length=150, nullable=False)
    category_id: int | None = Field(default=None, index=True, nullable=True)
    peran: str | None = Field(default=None, index=True, max_length=40, nullable=True)
    pengguna_id: int | None = Field(default=None, index=True, nullable=True)
    pemakai_text: str = Field(default="", max_length=100, nullable=False)
    lokasi_id: int | None = Field(default=None, index=True, nullable=True)
    parent_asset_id: str | None = Field(default=None, index=True, max_length=30, nullable=True)
    tanggal_perolehan: date | None = Field(default=None, nullable=True)
    nilai_perolehan: int | None = Field(default=None, nullable=True)
    vendor: str = Field(default="", max_length=150, nullable=False)
    garansi_sampai: date | None = Field(default=None, index=True, nullable=True)
    purchase_item_id: int | None = Field(default=None, index=True, nullable=True)
    specs: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    tracking: str = Field(default="unit", max_length=20, nullable=False)
    qty: int = Field(default=1, nullable=False)
    created_by: str = Field(default="system", max_length=80, nullable=False)
    deleted_at: datetime | None = Field(
        default=None,
        index=True,
        sa_type=cast(Any, DateTime(timezone=True)),
        nullable=True,
    )


class PowerAssumption(TimestampMixin, SQLModel, table=True):
    """Tabel singleton pengaturan asumsi laporan & kalkulator Rekap Watt Server."""

    __tablename__: Any = "power_assumptions"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    jam_operasional_per_hari: int = Field(default=24, nullable=False)
    hari_per_bulan: int = Field(default=30, nullable=False)
    faktor_beban_persen: int = Field(default=100, nullable=False)
    tarif_listrik_per_kwh: float | None = Field(default=None, nullable=True)
    faktor_daya_ups: float = Field(default=0.6, nullable=False)
    batas_waspada_ups: int = Field(default=70, nullable=False)
    batas_kritis_ups: int = Field(default=85, nullable=False)
    updated_by: str = Field(default="system", max_length=80, nullable=False)


class PowerCatalogItem(TimestampMixin, SQLModel, table=True):
    """Tabel katalog komponen daya (power_catalog) untuk Rekap & Kalkulator."""

    __tablename__: Any = "power_catalog"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kategori: str = Field(index=True, max_length=40, nullable=False)
    nama: str = Field(index=True, max_length=150, nullable=False)
    merek: str = Field(default="", max_length=80, nullable=False)
    tdp_w: int = Field(default=0, nullable=False)
    peak_w: int | None = Field(default=None, nullable=True)
    jenis_data: str = Field(default="resmi", max_length=30, nullable=False)  # resmi | estimasi
    sumber: str = Field(default="", max_length=255, nullable=False)
    catatan: str = Field(default="", max_length=500, nullable=False)
    diperbarui_oleh: str = Field(default="system", max_length=80, nullable=False)
    aktif: bool = Field(default=True, index=True, nullable=False)


class WattScenario(TimestampMixin, SQLModel, table=True):
    """Tabel skenario tersimpan dari Kalkulator Watt Server (watt_scenarios)."""

    __tablename__: Any = "watt_scenarios"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    nama: str = Field(index=True, max_length=150, nullable=False)
    asset_id: str | None = Field(default=None, index=True, max_length=30, nullable=True)
    komponen: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    hasil: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    dibuat_oleh: str = Field(default="system", max_length=80, nullable=False)
