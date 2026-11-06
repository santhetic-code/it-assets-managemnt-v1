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


def _detect_cpu_brand(cpu: str) -> str:
    low = (cpu or "").lower()
    if "intel" in low or "xeon" in low or "core" in low:
        return "Intel"
    if "amd" in low or "ryzen" in low or "epyc" in low:
        return "AMD"
    return "Lainnya"


def _classify_load_level(tdp_w: int) -> tuple[str, str, str]:
    if tdp_w >= 450:
        return "Tinggi", f"Tinggi ({tdp_w} W)", "danger"
    if tdp_w >= 250:
        return "Sedang", f"Sedang ({tdp_w} W)", "warning"
    return "Rendah", f"Rendah ({tdp_w} W)", "success"


class ServerPowerItem(BaseModel):
    """Representasi satu perangkat konsumen daya (turunan dari baris Asset)."""

    id: int
    id_aset: str
    nama_aset: str
    nama_server: str
    sub_label: str = ""
    grup_server: str = "Operasional"
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
    cpu: str = ""
    cpu_brand: str = "Intel"
    vga: str = "—"
    motherboard: str
    ram: str
    storage: str
    hdd_ssd: str = "—"
    os: str
    spesifikasi_ringkas: str

    watt: int
    daya_watt: int
    tdp_total_w: int = 0
    psu_min_w: int = 0
    psu_rekomendasi_w: int = 0
    tdp_display: str = "0 W"
    psu_min_display: str = "0 W"
    psu_rek_display: str = "0 W"
    kwh_display: str = "0 kWh/bln"
    beban_level: str = "Rendah"
    beban_badge: str = "Rendah (0 W)"
    beban_variant: str = "success"
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

        extra = dict(asset.extra_specs or {})
        tdp_w = int(asset.watt or extra.get("tdp_total_w") or 0)
        psu_min = int(
            extra.get("psu_min_w") or extra.get("psu_minimum_watt") or round(tdp_w * 1.25)
        )
        psu_rek = int(
            extra.get("psu_rekomendasi_w")
            or extra.get("psu_rekomendasi_watt")
            or max(450, ((int(tdp_w * 1.6) + 49) // 50) * 50)
        )
        est_kwh_item = round((tdp_w * HOURS_PER_DAY * DAYS_PER_MONTH) / 1000.0, 1)

        is_backup = (
            "BACKUP" in (asset.nama_aset or "").upper()
            or (asset.status or "").lower() in ("backup", "cadangan", "gudang")
            or str(extra.get("jenis", "")).lower() == "backup"
        )
        grup_srv = "Backup" if is_backup else "Operasional"
        cpu_str = asset.processor or str(extra.get("cpu") or "—")
        vga_str = asset.gpu or str(extra.get("vga") or "—")
        hdd_str = asset.storage or str(extra.get("hdd_ssd") or "—")
        ram_str = asset.ram or str(extra.get("ram") or "—")
        b_level, b_badge, b_variant = _classify_load_level(tdp_w)

        spec_parts = [p for p in (asset.processor, asset.ram, asset.storage) if p]
        spec_summary = " / ".join(spec_parts) if spec_parts else "-"

        return cls(
            id=asset.id or 0,
            id_aset=asset.id_aset,
            nama_aset=asset.nama_aset,
            nama_server=asset.nama_aset,
            sub_label=f"{asset.id_aset} · {grup_srv}",
            grup_server=grup_srv,
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
            cpu=cpu_str,
            cpu_brand=_detect_cpu_brand(cpu_str),
            vga=vga_str,
            motherboard=asset.motherboard,
            ram=ram_str,
            storage=asset.storage,
            hdd_ssd=hdd_str,
            os=asset.os,
            spesifikasi_ringkas=spec_summary,
            watt=asset.watt,
            daya_watt=asset.watt,
            tdp_total_w=tdp_w,
            psu_min_w=psu_min,
            psu_rekomendasi_w=psu_rek,
            tdp_display=f"{tdp_w} W",
            psu_min_display=f"{psu_min} W",
            psu_rek_display=f"{psu_rek} W",
            kwh_display=f"~{est_kwh_item} kWh/bln",
            beban_level=b_level,
            beban_badge=b_badge,
            beban_variant=b_variant,
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
    """Payload untuk memperbarui atau menambah atribut daya langsung ke tabel Asset."""

    id_aset: str | None = Field(default=None, max_length=30)
    nama_aset: str | None = Field(default=None, max_length=150)
    cpu: str | None = Field(default=None, max_length=150)
    processor: str | None = Field(default=None, max_length=150)
    vga: str | None = Field(default=None, max_length=150)
    gpu: str | None = Field(default=None, max_length=150)
    ram: str | None = Field(default=None, max_length=100)
    hdd_ssd: str | None = Field(default=None, max_length=150)
    storage: str | None = Field(default=None, max_length=150)
    lokasi: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    tdp_total_w: int | None = Field(default=None, ge=0)
    psu_min_w: int | None = Field(default=None, ge=0)
    psu_rekomendasi_w: int | None = Field(default=None, ge=0)
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
