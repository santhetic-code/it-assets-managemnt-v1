"""Skema Pydantic untuk request, validasi, dan response modul Aset."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.master_data import (
    ASSET_CONDITIONS,
    ASSET_STATUSES,
    CATEGORY_PREFIXES,
    LOCATION_ALIASES,
    LOCATIONS,
)
from app.models.asset import Asset

FORBIDDEN_FIELDS = {
    "power_supply",
    "psu",
    "casing",
    "cassing",
    "vendor",
    "nilai_perolehan",
    "batas_garansi",
}


def _clean_serial_number(val: str | None) -> str | None:
    """Menormalisasi SN: string kosong atau '-' dianggap None (tidak punya SN)."""
    if val is None:
        return None
    cleaned = val.strip()
    if not cleaned or cleaned in ("-", "N/A", "n/a", "Tidak Ada"):
        return None
    return cleaned


def _validate_category(val: str) -> str:
    cleaned = val.strip()
    if not cleaned:
        raise ValueError("Kategori aset wajib diisi")
    valid_map = {k.lower(): k for k in CATEGORY_PREFIXES}
    if cleaned.lower() not in valid_map:
        raise ValueError(f"Kategori '{cleaned}' tidak valid")
    return valid_map[cleaned.lower()]


def _validate_location(val: str) -> str:
    cleaned = val.strip()
    if not cleaned:
        raise ValueError("Lokasi aset wajib diisi")
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc
    if cleaned.lower() in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned.lower()]
    raise ValueError(f"Lokasi '{cleaned}' tidak terdaftar di data master")


def _validate_status(val: str) -> str:
    cleaned = val.strip()
    for st in ASSET_STATUSES:
        if st.lower() == cleaned.lower():
            return st
    raise ValueError(f"Status aset '{cleaned}' tidak valid")


class AssetCreate(BaseModel):
    """Payload pembuatan aset baru."""

    model_config = ConfigDict(extra="allow")

    id_aset: str | None = Field(default=None, max_length=30)
    nama_aset: str = Field(min_length=1, max_length=150)
    kategori: str = Field(min_length=1, max_length=50)
    merek: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    lokasi: str = Field(min_length=1, max_length=100)
    detail_lokasi: str = Field(default="", max_length=150)
    ruangan: str | None = Field(default=None, max_length=150)
    penanggung_jawab: str = Field(default="", max_length=100)
    pengguna: str | None = Field(default=None, max_length=100)
    status: str = Field(default="Aktif", max_length=40)
    kondisi: str = Field(default="Baik", max_length=40)
    tanggal_masuk: date | None = Field(default=None)
    tanggal_masuk_gudang: date | None = Field(default=None)

    processor: str = Field(default="", max_length=120)
    motherboard: str = Field(default="", max_length=120)
    ram: str = Field(default="", max_length=80)
    storage: str = Field(default="", max_length=120)
    gpu: str = Field(default="", max_length=120)
    os: str = Field(default="", max_length=80)
    watt: int = Field(default=0, ge=0)

    ukuran_layar: str = Field(default="", max_length=50)
    resolusi: str = Field(default="", max_length=50)
    panel: str = Field(default="", max_length=50)
    port_display: str = Field(default="", max_length=100)

    kapasitas_va: int = Field(default=0, ge=0)
    kapasitas_watt: int = Field(default=0, ge=0)
    baterai: str = Field(default="", max_length=120)
    jumlah_baterai: int = Field(default=0, ge=0)
    beban_perangkat: str = Field(default="", max_length=255)

    ip_address: str = Field(default="", max_length=50)
    mac_address: str = Field(default="", max_length=50)
    koneksi: str = Field(default="", max_length=80)
    catatan: str = Field(default="", max_length=500)

    @field_validator("nama_aset")
    @classmethod
    def _check_nama(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Nama aset tidak boleh kosong")
        return cleaned

    @field_validator("kategori")
    @classmethod
    def _check_kategori(cls, v: str) -> str:
        return _validate_category(v)

    @field_validator("lokasi")
    @classmethod
    def _check_lokasi(cls, v: str) -> str:
        return _validate_location(v)

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        return _validate_status(v)

    @field_validator("serial_number", mode="before")
    @classmethod
    def _normalize_sn(cls, v: Any) -> str | None:
        return _clean_serial_number(str(v)) if v is not None else None

    @model_validator(mode="after")
    def _sync_aliases_and_strip_forbidden(self) -> "AssetCreate":
        if not self.detail_lokasi and self.ruangan:
            self.detail_lokasi = self.ruangan.strip()
        if not self.penanggung_jawab and self.pengguna:
            self.penanggung_jawab = self.pengguna.strip()
        if self.tanggal_masuk is None and self.tanggal_masuk_gudang is not None:
            self.tanggal_masuk = self.tanggal_masuk_gudang
        if self.kondisi:
            matched = next(
                (c for c in ASSET_CONDITIONS if c.lower() == self.kondisi.strip().lower()),
                None,
            )
            if matched:
                self.kondisi = matched
        return self


class AssetUpdate(BaseModel):
    """Payload pembaruan aset (semua field opsional untuk mendukung PUT/PATCH)."""

    model_config = ConfigDict(extra="allow")

    nama_aset: str | None = Field(default=None, max_length=150)
    kategori: str | None = Field(default=None, max_length=50)
    merek: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    lokasi: str | None = Field(default=None, max_length=100)
    detail_lokasi: str | None = Field(default=None, max_length=150)
    ruangan: str | None = Field(default=None, max_length=150)
    penanggung_jawab: str | None = Field(default=None, max_length=100)
    pengguna: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=40)
    kondisi: str | None = Field(default=None, max_length=40)
    tanggal_masuk: date | None = Field(default=None)
    tanggal_masuk_gudang: date | None = Field(default=None)

    processor: str | None = None
    motherboard: str | None = None
    ram: str | None = None
    storage: str | None = None
    gpu: str | None = None
    os: str | None = None
    watt: int | None = Field(default=None, ge=0)

    ukuran_layar: str | None = None
    resolusi: str | None = None
    panel: str | None = None
    port_display: str | None = None

    kapasitas_va: int | None = Field(default=None, ge=0)
    kapasitas_watt: int | None = Field(default=None, ge=0)
    baterai: str | None = None
    jumlah_baterai: int | None = Field(default=None, ge=0)
    beban_perangkat: str | None = None

    ip_address: str | None = None
    mac_address: str | None = None
    koneksi: str | None = None
    catatan: str | None = None

    @field_validator("kategori")
    @classmethod
    def _check_kategori(cls, v: str | None) -> str | None:
        return _validate_category(v) if v is not None else None

    @field_validator("lokasi")
    @classmethod
    def _check_lokasi(cls, v: str | None) -> str | None:
        return _validate_location(v) if v is not None else None

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        return _validate_status(v) if v is not None else None


class AssetPublic(BaseModel):
    """Representasi JSON aset yang dikembalikan ke frontend."""

    id: int
    id_aset: str
    nama_aset: str
    kategori: str
    merek: str
    model: str
    serial_number: str
    lokasi: str
    detail_lokasi: str
    ruangan: str
    penanggung_jawab: str
    pengguna: str
    status: str
    kondisi: str
    tanggal_masuk: str | None
    tanggal_masuk_gudang: str | None

    processor: str
    motherboard: str
    ram: str
    storage: str
    gpu: str
    os: str
    watt: int

    ukuran_layar: str
    resolusi: str
    panel: str
    port_display: str

    kapasitas_va: int
    kapasitas_watt: int
    baterai: str
    jumlah_baterai: int
    beban_perangkat: str

    ip_address: str
    mac_address: str
    koneksi: str
    catatan: str

    @classmethod
    def from_asset(cls, asset: Asset) -> "AssetPublic":
        tgl = asset.tanggal_masuk.isoformat() if asset.tanggal_masuk else None
        return cls(
            id=asset.id or 0,
            id_aset=asset.id_aset,
            nama_aset=asset.nama_aset,
            kategori=asset.kategori,
            merek=asset.merek,
            model=asset.model,
            serial_number=asset.serial_number or "-",
            lokasi=asset.lokasi,
            detail_lokasi=asset.detail_lokasi,
            ruangan=asset.detail_lokasi,
            penanggung_jawab=asset.penanggung_jawab,
            pengguna=asset.penanggung_jawab,
            status=asset.status,
            kondisi=asset.kondisi,
            tanggal_masuk=tgl,
            tanggal_masuk_gudang=tgl,
            processor=asset.processor,
            motherboard=asset.motherboard,
            ram=asset.ram,
            storage=asset.storage,
            gpu=asset.gpu,
            os=asset.os,
            watt=asset.watt,
            ukuran_layar=asset.ukuran_layar,
            resolusi=asset.resolusi,
            panel=asset.panel,
            port_display=asset.port_display,
            kapasitas_va=asset.kapasitas_va,
            kapasitas_watt=asset.kapasitas_watt,
            baterai=asset.baterai,
            jumlah_baterai=asset.jumlah_baterai,
            beban_perangkat=asset.beban_perangkat,
            ip_address=asset.ip_address,
            mac_address=asset.mac_address,
            koneksi=asset.koneksi,
            catatan=asset.catatan,
        )


class AssetPageResponse(BaseModel):
    """Respons daftar aset berhalaman beserta tab_counts dan summary untuk frontend."""

    items: list[AssetPublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, int]

