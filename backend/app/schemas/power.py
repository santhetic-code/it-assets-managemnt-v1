"""Skema Pydantic dan fungsi kalkulasi untuk Rekap Watt Server & UPS (turunan dari Asset)."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.asset import Asset

DEFAULT_POWER_FACTOR = 0.6
DEFAULT_TARIF_PER_KWH: float | None = None  # Opsional: None = sembunyikan rupiah
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30
DEFAULT_LOAD_FACTOR_PCT = 100
DEFAULT_UPS_WARN_PCT = 70
DEFAULT_UPS_CRIT_PCT = 85

STANDARD_PSU_SIZES: tuple[int, ...] = (
    250,
    300,
    325,
    350,
    375,
    400,
    450,
    500,
    550,
    600,
    650,
    750,
    850,
    1000,
    1200,
)

LOAD_LEVEL_TOOLTIP = (
    "Rendah (< 220 W) · Sedang (220–299 W) · Tinggi (≥ 300 W). "
    "Dihitung dari beban efektif (W) terhadap TDP."
)

PSU_FORMULA_TEXT = (
    "PSU Minimum = Pembulatan ke ukuran standar PSU terdekat ke atas dari "
    "(Beban Efektif + Margin 75 W, min 250 W). "
    "PSU Rekomendasi = Pembulatan kelipatan 50 W ke atas dari "
    "(PSU Minimum + Margin 75 W, min 350 W)."
)


def calculate_psu_specs(
    effective_watt: int,
    override_min_w: int | None = None,
    override_rek_w: int | None = None,
) -> dict[str, Any]:
    """Satu rumus PSU terpusat untuk Rekap, Kalkulator, Export, dan Cetak."""
    if effective_watt <= 0:
        return {
            "psu_min_w": 0,
            "psu_rekomendasi_w": 0,
            "formula_psu_min_w": 0,
            "formula_psu_rek_w": 0,
            "psu_inconsistent": False,
            "psu_consistency_note": "",
            "psu_formula_text": PSU_FORMULA_TEXT,
        }

    raw_min = effective_watt + 75
    formula_min = next(
        (s for s in STANDARD_PSU_SIZES if s >= raw_min),
        ((raw_min + 49) // 50) * 50,
    )
    raw_rek = formula_min + 75
    formula_rek = max(350, ((raw_rek + 49) // 50) * 50)

    final_min = int(override_min_w) if (override_min_w and override_min_w > 0) else formula_min
    final_rek = int(override_rek_w) if (override_rek_w and override_rek_w > 0) else formula_rek

    inconsistent = (final_min != formula_min) or (final_rek != formula_rek)
    note = (
        f"Data historis aset mencatat {final_min} / {final_rek} W, sedangkan rumus standar untuk "
        f"{effective_watt} W menghasilkan {formula_min} / {formula_rek} W."
        if inconsistent
        else "Sesuai rumus standar PSU sistem."
    )
    return {
        "psu_min_w": final_min,
        "psu_rekomendasi_w": final_rek,
        "formula_psu_min_w": formula_min,
        "formula_psu_rek_w": formula_rek,
        "psu_inconsistent": inconsistent,
        "psu_consistency_note": note,
        "psu_formula_text": PSU_FORMULA_TEXT,
    }


def evaluate_installed_psu_status(
    psu_terpasang_w: int | None,
    psu_min_w: int,
    psu_rek_w: int,
) -> tuple[str, str]:
    """Menentukan status kecukupan PSU terpasang: Cukup | Minimum | Kurang | Belum Diisi."""
    if not psu_terpasang_w or psu_terpasang_w <= 0:
        return "Belum Diisi", "neutral"
    if psu_terpasang_w >= psu_rek_w:
        return "Cukup", "success"
    if psu_terpasang_w >= psu_min_w:
        return "Minimum", "warning"
    return "Kurang", "danger"


def effective_ups_watt(
    kapasitas_va: int,
    kapasitas_watt: int,
    power_factor: float = DEFAULT_POWER_FACTOR,
) -> int:
    """Menghitung kapasitas Watt efektif UPS (datasheet jika ada, jika tidak VA x faktor_daya)."""
    if kapasitas_watt and kapasitas_watt > 0:
        return int(kapasitas_watt)
    if kapasitas_va and kapasitas_va > 0:
        return round(kapasitas_va * power_factor)
    return 0


def ups_capacity_source_label(kapasitas_watt: int) -> str:
    """Mengembalikan label sumber kapasitas UPS: 'Datasheet' atau 'Perkiraan'."""
    return "Datasheet" if (kapasitas_watt and kapasitas_watt > 0) else "Perkiraan"


def calculate_load_status(
    load_percent: float,
    warn_pct: int = DEFAULT_UPS_WARN_PCT,
    crit_pct: int = DEFAULT_UPS_CRIT_PCT,
    is_estimated_capacity: bool = False,
) -> str:
    """Menentukan status utilisasi UPS (Aman | Waspada | Kritis / Kritis (Perkiraan))."""
    if load_percent <= 0:
        return "Tanpa Beban"
    if load_percent < warn_pct:
        return "Aman"
    if load_percent <= crit_pct:
        return "Waspada"
    return "Kritis (Perkiraan)" if is_estimated_capacity else "Kritis"


def calculate_power_metrics(
    base_watt: int,
    watt_terukur: int | None = None,
    jam_per_hari: int = HOURS_PER_DAY,
    hari_per_bulan: int = DAYS_PER_MONTH,
    faktor_beban_persen: int = DEFAULT_LOAD_FACTOR_PCT,
    tarif_per_kwh: float | None = DEFAULT_TARIF_PER_KWH,
) -> dict[str, Any]:
    """Mesin hitung tunggal beban efektif, kWh bulanan, biaya opsional, dan label sumber."""
    if watt_terukur is not None and watt_terukur > 0:
        effective_w = int(watt_terukur)
        source_label = "Terukur"
    else:
        effective_w = max(0, round(base_watt * (faktor_beban_persen / 100.0)))
        source_label = "Estimasi"

    total_hours = jam_per_hari * hari_per_bulan
    kwh_day = round((effective_w * jam_per_hari) / 1000.0, 2)
    kwh_month = round((effective_w * total_hours) / 1000.0, 1)

    has_tarif = tarif_per_kwh is not None and tarif_per_kwh > 0
    cost_month: int | None = round(kwh_month * float(tarif_per_kwh)) if has_tarif else None

    return {
        "base_watt": base_watt,
        "effective_watt": effective_w,
        "source_label": source_label,
        "jam_bulan": total_hours,
        "kwh_per_hari": kwh_day,
        "kwh_per_bulan": kwh_month,
        "estimasi_biaya_bulan": cost_month,
        "has_tarif": has_tarif,
    }


def _detect_cpu_brand(cpu: str) -> str:
    low = (cpu or "").lower()
    if "intel" in low or "xeon" in low or "core" in low:
        return "Intel"
    if "amd" in low or "ryzen" in low or "epyc" in low:
        return "AMD"
    return "Lainnya"


def _classify_load_level(effective_w: int) -> tuple[str, str, str]:
    """Klasifikasi beban Artboard 15 (<220W Rendah, 220-299W Sedang, >=300W Tinggi)."""
    if effective_w >= 300:
        return "Tinggi", "Tinggi", "danger"
    if effective_w >= 220:
        return "Sedang", "Sedang", "warning"
    return "Rendah", "Rendah", "success"


class PowerAssumptionSchema(BaseModel):
    jam_operasional_per_hari: int = Field(default=24, ge=1, le=24)
    hari_per_bulan: int = Field(default=30, ge=1, le=31)
    faktor_beban_persen: int = Field(default=100, ge=10, le=150)
    tarif_listrik_per_kwh: float | None = Field(default=None, ge=0)
    faktor_daya_ups: float = Field(default=0.6, gt=0.1, le=1.0)
    batas_waspada_ups: int = Field(default=70, ge=30, le=95)
    batas_kritis_ups: int = Field(default=85, ge=40, le=100)
    updated_by: str = "system"


class PowerCatalogItemSchema(BaseModel):
    id: int | None = None
    kategori: Literal[
        "cpu",
        "gpu",
        "motherboard",
        "ram",
        "ssd_sata",
        "nvme",
        "hdd",
        "fan",
        "optical",
        "pcie",
        "lainnya",
    ]
    nama: str = Field(min_length=1, max_length=150)
    merek: str = Field(default="", max_length=80)
    tdp_w: int = Field(default=0, ge=0)
    peak_w: int | None = Field(default=None, ge=0)
    jenis_data: Literal["resmi", "estimasi"] = "resmi"
    sumber: str = Field(default="", max_length=255)
    catatan: str = Field(default="", max_length=500)
    diperbarui_oleh: str = "admin"
    diperbarui_pada: datetime | None = None
    aktif: bool = True


class CalculatorComponentInput(BaseModel):
    slot: str
    kategori: str
    catalog_id: int | None = None
    nama: str = ""
    qty: int = Field(default=1, ge=0, le=64)
    custom_watt: int | None = Field(default=None, ge=0)


class CalculatorRequestSchema(BaseModel):
    mode: Literal["dasar", "puncak"] = "dasar"
    asset_id: str | None = None
    ups_id: str | None = None
    components: list[CalculatorComponentInput] = Field(default_factory=list)


class CalculatorResultSchema(BaseModel):
    beban_dasar_w: int
    beban_efektif_w: int
    mode: str
    faktor_beban_persen: int
    psu_min_w: int
    psu_rekomendasi_w: int
    formula_psu_min_w: int
    formula_psu_rek_w: int
    psu_formula_text: str
    kwh_per_bulan: float
    estimasi_biaya_bulan: int | None = None
    source_label: str = "Estimasi dari katalog"
    komposisi: dict[str, int]
    ups_check: dict[str, Any] | None = None


class WattScenarioSchema(BaseModel):
    id: int | None = None
    nama: str = Field(min_length=1, max_length=150)
    asset_id: str | None = None
    komponen: list[dict[str, Any]] = Field(default_factory=list)
    hasil: dict[str, Any] = Field(default_factory=dict)
    dibuat_oleh: str = "admin"
    created_at: datetime | None = None


class ServerPowerItem(BaseModel):
    """Representasi satu perangkat konsumen daya (turunan dari baris Asset)."""

    id: int
    id_aset: str
    nama_aset: str
    nama_server: str
    sub_label: str = ""
    grup_server: str = "Operasional"
    peran: str = "Operasional"
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
    beban_efektif_w: int = 0
    watt_terukur: int | None = None
    tanggal_ukur_watt: str | None = None
    sumber_daya_label: str = "Estimasi"
    psu_terpasang_w: int | None = None
    status_psu_terpasang: str = "Belum Diisi"
    status_psu_variant: str = "neutral"
    psu_min_w: int = 0
    psu_rekomendasi_w: int = 0
    formula_psu_min_w: int = 0
    formula_psu_rek_w: int = 0
    psu_inconsistent: bool = False
    psu_consistency_note: str = ""
    psu_formula_text: str = PSU_FORMULA_TEXT
    tdp_display: str = "0 W"
    psu_min_display: str = "0 W"
    psu_rek_display: str = "0 W"
    kwh_display: str = "0 kWh"
    biaya_display: str = ""
    beban_level: str = "Rendah"
    beban_badge: str = "Rendah"
    beban_variant: str = "success"
    beban_tooltip: str = LOAD_LEVEL_TOOLTIP
    kwh_per_hari: float
    kwh_per_bulan: float
    estimasi_biaya_bulan: int | None = None
    ups_id_aset: str = ""
    ups_nama: str = ""
    ups_utilisasi_pct: float = 0.0
    ups_status: str = "—"
    ups_source_label: str = ""
    ups_display: str = "—"
    komposisi_beban: dict[str, int] = Field(default_factory=dict)
    catalog_refs: dict[str, Any] = Field(default_factory=dict)
    ip_address: str
    beban_perangkat: str
    catatan: str

    @classmethod
    def from_asset(
        cls,
        asset: Asset,
        assumptions: PowerAssumptionSchema | None = None,
        ups_info: dict[str, Any] | None = None,
        tarif_per_kwh: float | None = DEFAULT_TARIF_PER_KWH,
    ) -> "ServerPowerItem":
        asmp = assumptions or PowerAssumptionSchema(tarif_listrik_per_kwh=tarif_per_kwh)
        extra = {**(asset.extra_specs or {}), **(asset.specs or {})}
        tdp_w = int(asset.watt or extra.get("tdp_total_w") or 0)
        watt_ukur_raw = extra.get("watt_terukur")
        watt_ukur = (
            int(watt_ukur_raw)
            if (watt_ukur_raw and str(watt_ukur_raw).isdigit() and int(watt_ukur_raw) > 0)
            else None
        )
        tgl_ukur = str(extra.get("tanggal_ukur_watt") or "") or None

        metrics = calculate_power_metrics(
            base_watt=tdp_w,
            watt_terukur=watt_ukur,
            jam_per_hari=asmp.jam_operasional_per_hari,
            hari_per_bulan=asmp.hari_per_bulan,
            faktor_beban_persen=asmp.faktor_beban_persen,
            tarif_per_kwh=asmp.tarif_listrik_per_kwh,
        )
        eff_w = metrics["effective_watt"]

        ov_min = int(extra["psu_min_w"]) if extra.get("psu_min_w") else None
        ov_rek = int(extra["psu_rekomendasi_w"]) if extra.get("psu_rekomendasi_w") else None
        psu_info = calculate_psu_specs(eff_w, override_min_w=ov_min, override_rek_w=ov_rek)
        psu_min = psu_info["psu_min_w"]
        psu_rek = psu_info["psu_rekomendasi_w"]

        psu_terpasang_raw = extra.get("psu_terpasang_watt") or extra.get("psu_terpasang_w")
        psu_terpasang = (
            int(psu_terpasang_raw)
            if (
                psu_terpasang_raw
                and str(psu_terpasang_raw).isdigit()
                and int(psu_terpasang_raw) > 0
            )
            else None
        )
        psu_st, psu_var = evaluate_installed_psu_status(psu_terpasang, psu_min, psu_rek)

        is_backup = (
            "BACKUP" in (asset.nama_aset or "").upper()
            or (asset.peran or "").lower() in ("backup", "cadangan")
            or (asset.status or "").lower() in ("backup", "cadangan", "gudang")
            or str(extra.get("jenis", "")).lower() == "backup"
        )
        grup_srv = "Backup" if is_backup else "Operasional"
        cpu_str = asset.processor or str(extra.get("cpu") or "—")
        vga_str = asset.gpu or str(extra.get("vga") or "—")
        hdd_str = asset.storage or str(extra.get("hdd_ssd") or "—")
        ram_str = asset.ram or str(extra.get("ram") or "—")
        b_level, b_badge, b_variant = _classify_load_level(eff_w)

        # Format Spesifikasi Ringkas ala Artboard 15
        short_cpu = (
            cpu_str.replace("Intel Core ", "")
            .replace("AMD ", "")
            .replace(" Desktop", "")
            .split(" ")[0]
            if cpu_str != "—"
            else "—"
        )
        short_gpu = (
            "UHD 620"
            if "UHD 620" in vga_str
            else vga_str.replace("NVIDIA GeForce ", "").replace(" Desktop", "")
        )
        short_ram = ram_str.replace(" dengan kilat LED", "").replace("x ", "×")
        short_disk = (
            hdd_str.replace("x ", " ").replace(", ", " + ").replace("SSD M.2", "M.2")
        )
        spec_parts = [p for p in (short_cpu, short_gpu, short_ram, short_disk) if p and p != "—"]
        spec_summary = " · ".join(spec_parts) if spec_parts else "-"

        # Komposisi beban komponen
        komposisi = extra.get("komposisi_beban")
        if not isinstance(komposisi, dict) or not komposisi:
            cpu_w = int(
                extra.get("tdp_cpu_w")
                or (
                    125
                    if "K" in short_cpu
                    else (
                        105
                        if "3800X" in short_cpu
                        else (165 if "9800X" in short_cpu else 65)
                    )
                )
            )
            gpu_w = int(
                extra.get("tdp_gpu_w")
                or (0 if "UHD" in short_gpu or "Terpadu" in short_gpu else 30)
            )
            ram_cnt = 4 if "4" in short_ram else (3 if "3" in short_ram else 2)
            ram_w = ram_cnt * 3
            disk_w = (
                (9 if "3" in short_disk else (6 if "2" in short_disk else 3))
                + (7 if "M.2" in short_disk else 0)
            )
            lainnya_w = max(0, eff_w - (cpu_w + gpu_w + ram_w + disk_w))
            komposisi = {
                "CPU": cpu_w,
                "GPU": gpu_w,
                "RAM": ram_w,
                "Storage": disk_w,
                "Lainnya": lainnya_w,
            }

        kwh_str = f"{str(metrics['kwh_per_bulan']).replace('.', ',')} kWh"
        cost_val = metrics["estimasi_biaya_bulan"]
        biaya_str = f"Rp {cost_val:,}".replace(",", ".") if cost_val is not None else ""

        u_id = str((ups_info or {}).get("id_aset") or "")
        u_pct = float((ups_info or {}).get("utilisasi_pct") or 0.0)
        u_st = str((ups_info or {}).get("status") or "—")
        u_src = str((ups_info or {}).get("source_label") or "")
        u_disp = f"{u_id} · {round(u_pct)}%" if u_id else "—"

        return cls(
            id=asset.id or 0,
            id_aset=asset.id_aset,
            nama_aset=asset.nama_aset,
            nama_server=asset.nama_aset,
            sub_label=f"{asset.id_aset} · {grup_srv}",
            grup_server=grup_srv,
            peran=asset.peran or grup_srv,
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
            daya_watt=eff_w,
            tdp_total_w=tdp_w,
            beban_efektif_w=eff_w,
            watt_terukur=watt_ukur,
            tanggal_ukur_watt=tgl_ukur,
            sumber_daya_label=metrics["source_label"],
            psu_terpasang_w=psu_terpasang,
            status_psu_terpasang=psu_st,
            status_psu_variant=psu_var,
            psu_min_w=psu_min,
            psu_rekomendasi_w=psu_rek,
            formula_psu_min_w=psu_info["formula_psu_min_w"],
            formula_psu_rek_w=psu_info["formula_psu_rek_w"],
            psu_inconsistent=psu_info["psu_inconsistent"],
            psu_consistency_note=psu_info["psu_consistency_note"],
            psu_formula_text=psu_info["psu_formula_text"],
            tdp_display=f"{eff_w} W",
            psu_min_display=f"{psu_min} W",
            psu_rek_display=f"{psu_rek} W",
            kwh_display=kwh_str,
            biaya_display=biaya_str,
            beban_level=b_level,
            beban_badge=b_badge,
            beban_variant=b_variant,
            kwh_per_hari=metrics["kwh_per_hari"],
            kwh_per_bulan=metrics["kwh_per_bulan"],
            estimasi_biaya_bulan=cost_val,
            ups_id_aset=u_id,
            ups_nama=str((ups_info or {}).get("nama_aset") or ""),
            ups_utilisasi_pct=u_pct,
            ups_status=u_st,
            ups_source_label=u_src,
            ups_display=u_disp,
            komposisi_beban=komposisi,
            catalog_refs=extra.get("catalog_refs") or {},
            ip_address=asset.ip_address,
            beban_perangkat=asset.beban_perangkat,
            catatan=asset.catatan,
        )


class UPSPowerItem(BaseModel):
    """Representasi unit UPS beserta utilisasi server yang tertaut dan label sumber kapasitas."""

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
    kapasitas_watt_manual: int = 0
    kapasitas_watt: int
    sumber_kapasitas: str = "Perkiraan"  # "Datasheet" | "Perkiraan"
    is_kapasitas_manual: bool = False
    warning_melebihi_va: bool = False
    baterai: str
    jumlah_baterai: int
    beban_perangkat: str
    linked_servers: list[str] = Field(default_factory=list)
    linked_server_ids: list[str] = Field(default_factory=list)
    beban_server_w: int = 0
    utilisasi_pct: float = 0.0
    status_utilisasi: str = "Tanpa Beban"
    ringkasan_beban: str = "0 W dari 0 W"
    catatan: str

    @classmethod
    def from_asset(
        cls,
        asset: Asset,
        power_factor: float = DEFAULT_POWER_FACTOR,
        warn_pct: int = DEFAULT_UPS_WARN_PCT,
        crit_pct: int = DEFAULT_UPS_CRIT_PCT,
        linked_servers: list[str] | None = None,
        linked_server_ids: list[str] | None = None,
        beban_server_w: int = 0,
    ) -> "UPSPowerItem":
        raw_manual_w = int(asset.kapasitas_watt or 0)
        eff_watt = effective_ups_watt(asset.kapasitas_va, raw_manual_w, power_factor=power_factor)
        is_manual = raw_manual_w > 0
        src_label = ups_capacity_source_label(raw_manual_w)
        util_pct = round((beban_server_w / eff_watt) * 100.0, 1) if eff_watt > 0 else 0.0
        st_util = calculate_load_status(
            util_pct,
            warn_pct=warn_pct,
            crit_pct=crit_pct,
            is_estimated_capacity=not is_manual,
        )
        warning_va = bool(
            is_manual and asset.kapasitas_va > 0 and raw_manual_w > asset.kapasitas_va
        )
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
            kapasitas_watt_manual=raw_manual_w,
            kapasitas_watt=eff_watt,
            sumber_kapasitas=src_label,
            is_kapasitas_manual=is_manual,
            warning_melebihi_va=warning_va,
            baterai=asset.baterai,
            jumlah_baterai=asset.jumlah_baterai,
            beban_perangkat=asset.beban_perangkat,
            linked_servers=linked_servers or [],
            linked_server_ids=linked_server_ids or [],
            beban_server_w=beban_server_w,
            utilisasi_pct=util_pct,
            status_utilisasi=st_util,
            ringkasan_beban=f"{beban_server_w} W dari {eff_watt} W ({src_label.lower()})",
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
    psu_terpasang_watt: int | None = Field(default=None, ge=0)
    watt_terukur: int | None = Field(default=None, ge=0)
    tanggal_ukur_watt: str | None = Field(default=None, max_length=30)
    catalog_refs: dict[str, Any] | None = None
    komposisi_beban: dict[str, int] | None = None


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
    assumptions: PowerAssumptionSchema = Field(default_factory=PowerAssumptionSchema)
    top_servers: list[ServerPowerItem] = Field(default_factory=list)
