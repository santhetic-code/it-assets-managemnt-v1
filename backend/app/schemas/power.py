"""Skema Pydantic dan fungsi kalkulasi untuk Rekap Watt Server & UPS (turunan dari Asset)."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.asset import Asset

DEFAULT_POWER_FACTOR = 0.6
DEFAULT_TARIF_PER_KWH = 1444.70  # Tarif bisnis standar PLN (Rp / kWh)
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30


def effective_ups_watt(kapasitas_va: int, kapasitas_watt: int) -> int:
    """Menghitung kapasitas Watt efektif UPS (memakai power factor 0.6 bila kapasitas_watt 0)."""
    if kapasitas_watt > 0:
        return kapasitas_watt
    if kapasitas_va > 0:
        return round(kapasitas_va * DEFAULT_POWER_FACTOR)
    return 0


def calculate_load_status(load_percent: float) -> str:
    """Menentukan status kesehatan beban daya UPS berdasarkan persentase beban."""
    if load_percent <= 0:
        return "Tanpa Beban"
    if load_percent < 70.0:
        return "Aman"
    if load_percent <= 85.0:
        return "Waspada"
    return "Overload"


class ServerPowerItem(BaseModel):
    """Representasi satu perangkat konsumen daya (turunan dari baris Asset)."""

    id: int
    id_aset: str
    nama_aset: str
    nama_server: str
    kategori: str
    merek: str
    model: str
    serial_number: str
    lokasi: str
    detail_lokasi: str
    ruangan: str
    penanggung_jawab: str
    status: str
    kondisi: str

    processor: str
    motherboard: str
    ram: str
    storage: str
    os: str
    spesifikasi_ringkas: str

    watt: int
    daya_watt: int
    kwh_per_hari: float
    kwh_per_bulan: float
    estimasi_biaya_bulan: int
    ip_address: str
    beban_perangkat: str
    catatan: str

    @classmethod
    def from_asset(
        cls,
        asset: Asset,
        tarif_per_kwh: float = DEFAULT_TARIF_PER_KWH,
    ) -> "ServerPowerItem":
        active_multiplier = 1.0 if asset.status.lower() in ("aktif", "digunakan") else 0.0
        effective_watt = asset.watt if active_multiplier > 0 else 0
        kwh_day = round((effective_watt * HOURS_PER_DAY) / 1000.0, 2)
        kwh_month = round(kwh_day * DAYS_PER_MONTH, 2)
        cost_month = round(kwh_month * tarif_per_kwh)

        spec_parts = [p for p in (asset.processor, asset.ram, asset.storage) if p]
        spec_summary = " / ".join(spec_parts) if spec_parts else "-"

        return cls(
            id=asset.id or 0,
            id_aset=asset.id_aset,
            nama_aset=asset.nama_aset,
            nama_server=asset.nama_aset,
            kategori=asset.kategori,
            merek=asset.merek,
            model=asset.model,
            serial_number=asset.serial_number or "-",
            lokasi=asset.lokasi,
            detail_lokasi=asset.detail_lokasi,
            ruangan=asset.detail_lokasi,
            penanggung_jawab=asset.penanggung_jawab,
            status=asset.status,
            kondisi=asset.kondisi,
            processor=asset.processor,
            motherboard=asset.motherboard,
            ram=asset.ram,
            storage=asset.storage,
            os=asset.os,
            spesifikasi_ringkas=spec_summary,
            watt=asset.watt,
            daya_watt=asset.watt,
            kwh_per_hari=kwh_day,
            kwh_per_bulan=kwh_month,
            estimasi_biaya_bulan=cost_month,
            ip_address=asset.ip_address,
            beban_perangkat=asset.beban_perangkat,
            catatan=asset.catatan,
        )


class UPSPowerItem(BaseModel):
    """Representasi unit UPS (turunan dari baris Asset kategori UPS)."""

    id: int
    id_aset: str
    nama_aset: str
    merek: str
    model: str
    lokasi: str
    detail_lokasi: str
    status: str
    kondisi: str
    kapasitas_va: int
    kapasitas_watt: int
    baterai: str
    jumlah_baterai: int
    beban_perangkat: str
    catatan: str

    @classmethod
    def from_asset(cls, asset: Asset) -> "UPSPowerItem":
        eff_watt = effective_ups_watt(asset.kapasitas_va, asset.kapasitas_watt)
        return cls(
            id=asset.id or 0,
            id_aset=asset.id_aset,
            nama_aset=asset.nama_aset,
            merek=asset.merek,
            model=asset.model,
            lokasi=asset.lokasi,
            detail_lokasi=asset.detail_lokasi,
            status=asset.status,
            kondisi=asset.kondisi,
            kapasitas_va=asset.kapasitas_va,
            kapasitas_watt=eff_watt,
            baterai=asset.baterai,
            jumlah_baterai=asset.jumlah_baterai,
            beban_perangkat=asset.beban_perangkat,
            catatan=asset.catatan,
        )


class LocationPowerSummary(BaseModel):
    """Rekapitulasi konsumsi daya dan kapasitas UPS per lokasi."""

    lokasi: str
    jumlah_server: int
    jumlah_perangkat_daya: int
    jumlah_ups: int
    total_watt: int
    total_va_ups: int
    total_kapasitas_watt_ups: int
    persentase_beban_ups: float
    status_beban: str
    kwh_per_bulan: float
    estimasi_biaya_bulan: int


class PowerUpdatePayload(BaseModel):
    """Payload untuk memperbarui atribut daya langsung ke tabel Asset."""

    watt: int | None = Field(default=None, ge=0)
    kapasitas_va: int | None = Field(default=None, ge=0)
    kapasitas_watt: int | None = Field(default=None, ge=0)
    baterai: str | None = Field(default=None, max_length=120)
    jumlah_baterai: int | None = Field(default=None, ge=0)
    beban_perangkat: str | None = Field(default=None, max_length=255)
    catatan: str | None = Field(default=None, max_length=500)


class WattServerPageResponse(BaseModel):
    """Respons utama endpoint Rekap Watt Server sesuai kontrak frontend."""

    items: list[ServerPowerItem]
    ups_items: list[UPSPowerItem]
    by_location: list[LocationPowerSummary]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, Any]
