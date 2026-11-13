"""Layanan kalkulasi konsumsi daya (Thermal Design Power / TDP) server ITAM Pro."""

from copy import deepcopy
from typing import Any

from itam_pro.services.mock.audit_mock import record_audit_event
from itam_pro.services.mock.seed import (
    MOCK_ASSETS,
    create_mock_assets,
    delete_mock_asset,
    update_mock_asset,
)

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

MOCK_POWER_ASSUMPTIONS: dict[str, Any] = {
    "jam_operasional_per_hari": 24,
    "hari_per_bulan": 30,
    "faktor_beban_persen": 100,
    "tarif_listrik_per_kwh": None,  # Kosong = sembunyikan biaya rupiah di semua tempat
    "faktor_daya_ups": 0.6,
    "batas_waspada_ups": 70,
    "batas_kritis_ups": 85,
}

MOCK_POWER_CATALOG: list[dict[str, Any]] = [
    {
        "id": 1,
        "kategori": "cpu",
        "nama": "Intel Core i7-13700",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 219,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 2,
        "kategori": "cpu",
        "nama": "Intel Core i7-13700F",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 219,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 3,
        "kategori": "cpu",
        "nama": "Intel Core i7-12700",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 180,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 4,
        "kategori": "cpu",
        "nama": "Intel Core i5-13400",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 148,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 5,
        "kategori": "cpu",
        "nama": "Intel Core i5-12400",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 117,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 6,
        "kategori": "cpu",
        "nama": "Intel Core i5-10600K",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 182,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 7,
        "kategori": "cpu",
        "nama": "Intel Core i3-10105F",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 90,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 8,
        "kategori": "cpu",
        "nama": "Intel Core i7-10700",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 224,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 9,
        "kategori": "cpu",
        "nama": "Intel Core i7-10700F",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 224,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 10,
        "kategori": "cpu",
        "nama": "Intel Core i7-10700K",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 229,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 11,
        "kategori": "cpu",
        "nama": "Intel Core i9-10900K",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 250,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 12,
        "kategori": "cpu",
        "nama": "Intel Core i7-9800X",
        "merek": "Intel",
        "tdp_w": 165,
        "peak_w": 210,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 13,
        "kategori": "cpu",
        "nama": "Intel Core Ultra 7 265KF",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 250,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 14,
        "kategori": "cpu",
        "nama": "AMD Ryzen 7 3800X",
        "merek": "AMD",
        "tdp_w": 105,
        "peak_w": 142,
        "jenis_data": "resmi",
        "sumber": "AMD",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 15,
        "kategori": "cpu",
        "nama": "AMD Ryzen 5 5600G",
        "merek": "AMD",
        "tdp_w": 65,
        "peak_w": 88,
        "jenis_data": "resmi",
        "sumber": "AMD",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 16,
        "kategori": "gpu",
        "nama": "Intel UHD Graphics (terpadu)",
        "merek": "Intel",
        "tdp_w": 0,
        "peak_w": 0,
        "jenis_data": "resmi",
        "sumber": "Termasuk TDP CPU",
        "catatan": "termasuk TDP CPU",
        "aktif": True,
    },
    {
        "id": 17,
        "kategori": "gpu",
        "nama": "NVIDIA GeForce GT 1030 2GB",
        "merek": "NVIDIA",
        "tdp_w": 30,
        "peak_w": 35,
        "jenis_data": "resmi",
        "sumber": "NVIDIA",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 18,
        "kategori": "gpu",
        "nama": "NVIDIA GeForce GT 730 2GB",
        "merek": "NVIDIA",
        "tdp_w": 38,
        "peak_w": 45,
        "jenis_data": "resmi",
        "sumber": "NVIDIA",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 19,
        "kategori": "motherboard",
        "nama": "Desktop ATX",
        "merek": "Generic",
        "tdp_w": 40,
        "peak_w": 55,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 20,
        "kategori": "motherboard",
        "nama": "Desktop Micro-ATX",
        "merek": "Generic",
        "tdp_w": 30,
        "peak_w": 45,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 21,
        "kategori": "ram",
        "nama": "RAM DDR4 per modul",
        "merek": "Generic",
        "tdp_w": 3,
        "peak_w": 4,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 22,
        "kategori": "ram",
        "nama": "RAM DDR5 per modul",
        "merek": "Generic",
        "tdp_w": 4,
        "peak_w": 5,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 23,
        "kategori": "ssd_sata",
        "nama": "SSD SATA 2,5 inci",
        "merek": "Generic",
        "tdp_w": 3,
        "peak_w": 5,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 24,
        "kategori": "nvme",
        "nama": "SSD NVMe M.2",
        "merek": "Generic",
        "tdp_w": 7,
        "peak_w": 10,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 25,
        "kategori": "hdd",
        "nama": "HDD SATA 3,5 inci",
        "merek": "Generic",
        "tdp_w": 9,
        "peak_w": 15,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 26,
        "kategori": "fan",
        "nama": "Kipas casing",
        "merek": "Generic",
        "tdp_w": 3,
        "peak_w": 5,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 27,
        "kategori": "optical",
        "nama": "Tanpa drive optik",
        "merek": "Generic",
        "tdp_w": 0,
        "peak_w": 0,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 28,
        "kategori": "optical",
        "nama": "DVD-RW Internal",
        "merek": "Generic",
        "tdp_w": 15,
        "peak_w": 20,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 29,
        "kategori": "pcie",
        "nama": "Tanpa kartu PCIe",
        "merek": "Generic",
        "tdp_w": 0,
        "peak_w": 0,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
    {
        "id": 30,
        "kategori": "pcie",
        "nama": "Kartu PCIe NIC / HBA",
        "merek": "Generic",
        "tdp_w": 10,
        "peak_w": 15,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
        "catatan": "",
        "aktif": True,
    },
]

MOCK_WATT_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": 1,
        "nama": "Upgrade GPU SRV-003",
        "asset_id": "SRV-003",
        "subtitle": "+50 W · UPS-009 59%",
        "komponen": [],
        "hasil": {
            "saat_ini_w": 198,
            "skenario_w": 248,
            "selisih_w": "+50 W",
            "saat_ini_psu": "500 W",
            "skenario_psu": "500 W",
            "selisih_psu": "sama",
            "saat_ini_kwh": "142,6 kWh",
            "skenario_kwh": "178,6 kWh",
            "selisih_kwh": "+36,0 kWh",
            "ups_id": "UPS-009",
            "saat_ini_ups_pct": "47%",
            "skenario_ups_pct": "59%",
            "selisih_ups_pct": "+12 poin",
            "ups_status": "Aman",
            "saat_ini_psu_status": "Cukup",
            "skenario_psu_status": "Cukup",
        },
        "dibuat_oleh": "admin",
    },
    {
        "id": 2,
        "nama": "Server baru (rencana backup)",
        "asset_id": "",
        "subtitle": "142 W · PSU 350 W",
        "komponen": [],
        "hasil": {
            "saat_ini_w": 0,
            "skenario_w": 142,
            "selisih_w": "+142 W",
            "saat_ini_psu": "—",
            "skenario_psu": "350 W",
            "selisih_psu": "+350 W",
            "saat_ini_kwh": "0 kWh",
            "skenario_kwh": "102,2 kWh",
            "selisih_kwh": "+102,2 kWh",
            "ups_id": "UPS-009",
            "saat_ini_ups_pct": "0%",
            "skenario_ups_pct": "34%",
            "selisih_ups_pct": "+34 poin",
            "ups_status": "Aman",
            "saat_ini_psu_status": "—",
            "skenario_psu_status": "Cukup",
        },
        "dibuat_oleh": "admin",
    },
]


def _to_int_watt(val: Any) -> int:
    """Konversi nilai string/float watt ke integer aman."""
    try:
        cleaned = str(val or "0").strip().replace("W", "").replace("w", "").replace(",", ".")
        return max(0, round(float(cleaned)))
    except (ValueError, TypeError):
        return 0


def calculate_psu_specs(
    effective_watt: int,
    override_min_w: int = 0,
    override_rek_w: int = 0,
) -> dict[str, Any]:
    """Satu aturan PSU untuk Rekap dan Kalkulator (konsisten dengan data 16 server)."""
    if effective_watt <= 0:
        return {
            "psu_min_w": 0,
            "psu_rekomendasi_w": 0,
            "formula_psu_min_w": 0,
            "formula_psu_rek_w": 0,
            "psu_inconsistent": False,
        }
    raw_min = effective_watt + 75
    formula_min = next(
        (s for s in STANDARD_PSU_SIZES if s >= raw_min),
        ((raw_min + 49) // 50) * 50,
    )
    formula_rek = max(350, ((formula_min + 75 + 49) // 50) * 50)

    final_min = override_min_w if override_min_w > 0 else formula_min
    final_rek = override_rek_w if override_rek_w > 0 else formula_rek
    return {
        "psu_min_w": final_min,
        "psu_rekomendasi_w": final_rek,
        "formula_psu_min_w": formula_min,
        "formula_psu_rek_w": formula_rek,
        "psu_inconsistent": (final_min != formula_min) or (final_rek != formula_rek),
    }


def evaluate_psu_terpasang(
    psu_terpasang_w: int,
    psu_min_w: int,
    psu_rek_w: int,
) -> tuple[str, str]:
    """Status PSU terpasang: Cukup (>= rek), Minimum (>= min), Kurang (< min)."""
    if psu_terpasang_w <= 0:
        return "Belum Diisi", "neutral"
    if psu_terpasang_w >= psu_rek_w:
        return "Cukup", "success"
    if psu_terpasang_w >= psu_min_w:
        return "Minimum", "warning"
    return "Kurang", "danger"


def total_tdp(assets: list[dict[str, Any]]) -> float:
    """Hitung total Thermal Design Power (TDP) dalam Watt."""
    total = 0.0
    for a in assets:
        attrs = a.get("attributes", {})
        try:
            val = float(str(attrs.get("tdp_total_w", 0)).replace(",", "."))
            total += val
        except (ValueError, TypeError):
            pass
    return total


def energi_kwh_bulan(
    effective_w: float,
    jam_per_hari: int = 24,
    hari_per_bulan: int = 30,
    jam: int | None = None,
) -> float:
    """Hitung estimasi konsumsi energi bulanan dalam kWh."""
    total_hours = jam if jam is not None else (jam_per_hari * hari_per_bulan)
    return round((effective_w * total_hours) / 1000.0, 1)


def _build_ups_links_and_items(
    all_assets: list[dict[str, Any]],
    asmp: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Bangun daftar UPS yang terhubung ke server beserta utilisasi & sumber kapasitasnya."""
    pf = float(asmp.get("faktor_daya_ups", 0.6) or 0.6)
    warn_pct = int(asmp.get("batas_waspada_ups", 70) or 70)
    crit_pct = int(asmp.get("batas_kritis_ups", 85) or 85)
    faktor_beban = int(asmp.get("faktor_beban_persen", 100) or 100)

    servers_by_name: dict[str, dict[str, Any]] = {}
    for a in all_assets:
        if str(a.get("kategori", "")).lower() == "server":
            servers_by_name[str(a.get("nama_aset", "")).strip().upper()] = a

    ups_list: list[dict[str, Any]] = []
    srv_to_ups: dict[str, dict[str, Any]] = {}

    for a in all_assets:
        if str(a.get("kategori", "")).lower() != "ups":
            continue
        attrs = a.get("attributes") or {}
        u_id = str(a.get("id_aset", "")).strip()
        va = _to_int_watt(attrs.get("kapasitas_va", 650)) or 650
        manual_w = _to_int_watt(attrs.get("kapasitas_watt", 0))
        is_manual = manual_w > 0
        eff_cap_w = manual_w if is_manual else round(va * pf)
        sumber_kap = "Datasheet" if is_manual else "Perkiraan"

        raw_target = str(attrs.get("beban_perangkat") or a.get("digunakan_oleh") or "").upper()
        norm_target = (
            raw_target.replace("OTOMAX", "OTO")
            .replace("MENYUPLAI SERVER ", "")
            .replace("MENYUPLAI ", "")
            .strip()
        )

        ignore_targets = (
            "—",
            "-",
            "BACKUP",
            "RAK JARINGAN",
            "SYNOLOGY",
            "PC OWNER",
            "PC SUPERVISOR OPERASIONAL",
        )
        linked_srvs: list[dict[str, Any]] = []
        if norm_target and norm_target not in ignore_targets:
            for s_name, s_obj in servers_by_name.items():
                if s_name in norm_target:
                    linked_srvs.append(s_obj)

        load_w = 0
        for s_obj in linked_srvs:
            s_attrs = s_obj.get("attributes") or {}
            w_ukur = _to_int_watt(s_attrs.get("watt_terukur", 0))
            tdp_s = _to_int_watt(s_attrs.get("tdp_total_w", 0))
            eff_s = w_ukur if w_ukur > 0 else round(tdp_s * (faktor_beban / 100.0))
            load_w += eff_s

        util_pct = round((load_w / eff_cap_w) * 100.0, 1) if eff_cap_w > 0 else 0.0
        if util_pct <= 0:
            st_util = "Tanpa Beban"
            st_var = "neutral"
        elif util_pct < warn_pct:
            st_util = "Aman"
            st_var = "success"
        elif util_pct <= crit_pct:
            st_util = "Waspada"
            st_var = "warning"
        else:
            st_util = "Kritis (Perkiraan)" if not is_manual else "Kritis"
            st_var = "danger"

        merk_str = str(a.get("nama_aset", "")).replace("UPS ", "").split(" ")[0]
        srv_names_str = " & ".join(str(s.get("nama_aset", "")) for s in linked_srvs)
        header_lbl = (
            f"{u_id} · {merk_str} {va}VA → {srv_names_str}"
            if srv_names_str
            else f"{u_id} · {merk_str} {va}VA"
        )
        ups_entry = {
            "id_aset": u_id,
            "nama_aset": str(a.get("nama_aset", "")),
            "merek_va": f"{merk_str} {va}VA",
            "header_label": header_lbl,
            "kapasitas_va": va,
            "kapasitas_watt_manual": manual_w,
            "kapasitas_watt": eff_cap_w,
            "is_kapasitas_manual": is_manual,
            "sumber_kapasitas": sumber_kap,
            "warning_melebihi_va": is_manual and manual_w > va,
            "linked_servers": [str(s.get("nama_aset", "")) for s in linked_srvs],
            "linked_server_ids": [str(s.get("id_aset", "")) for s in linked_srvs],
            "beban_server_w": load_w,
            "utilisasi_pct": util_pct,
            "utilisasi_int": round(util_pct),
            "status_utilisasi": st_util,
            "status_variant": st_var,
            "sub_text": f"{load_w} W dari {eff_cap_w} W ({sumber_kap.lower()})",
            "dropdown_label": (
                f"{u_id} · {merk_str} {va}VA · {eff_cap_w} W ({sumber_kap.lower()})"
            ),
        }
        ups_list.append(ups_entry)
        for s_obj in linked_srvs:
            s_tag = str(s_obj.get("id_aset", "")).strip().upper()
            srv_to_ups[s_tag] = ups_entry

    return ups_list, srv_to_ups


def enrich_server_power_row(
    asset: dict[str, Any],
    assumptions: dict[str, Any] | None = None,
    ups_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Siapkan satu baris data server untuk tabel Rekap Watt Server (Artboard 15 & 16)."""
    asmp = assumptions or MOCK_POWER_ASSUMPTIONS
    attrs = asset.get("attributes") or {}
    id_aset = str(asset.get("id_aset", "")).strip()
    nama = str(asset.get("nama_aset", "")).strip()
    cpu = str(attrs.get("cpu", "") or "—").strip()
    vga = str(attrs.get("vga", "") or "—").strip()
    ram = str(attrs.get("ram", "") or "—").strip()
    hdd_ssd = str(attrs.get("hdd_ssd", "") or "—").strip()

    tdp_w = _to_int_watt(attrs.get("tdp_total_w", 0))
    watt_ukur = _to_int_watt(attrs.get("watt_terukur", 0))
    faktor_beban = int(asmp.get("faktor_beban_persen", 100) or 100)

    if watt_ukur > 0:
        beban_efektif_w = watt_ukur
        sumber_label = "Terukur"
    else:
        beban_efektif_w = max(0, round(tdp_w * (faktor_beban / 100.0)))
        sumber_label = "Estimasi"

    psu_calc = calculate_psu_specs(
        beban_efektif_w,
        override_min_w=_to_int_watt(attrs.get("psu_min_w", 0)),
        override_rek_w=_to_int_watt(attrs.get("psu_rekomendasi_w", 0)),
    )
    psu_min_w = psu_calc["psu_min_w"]
    psu_rek_w = psu_calc["psu_rekomendasi_w"]

    psu_terpasang_w = _to_int_watt(attrs.get("psu_terpasang_watt", 0))
    psu_status, psu_variant = evaluate_psu_terpasang(psu_terpasang_w, psu_min_w, psu_rek_w)

    is_backup = "BACKUP" in nama.upper() or str(asset.get("status", "")) in (
        "Backup",
        "Cadangan",
    )
    grup_server = "Backup" if is_backup else "Operasional"
    cpu_brand = (
        "AMD" if "AMD" in cpu.upper() else ("Intel" if "INTEL" in cpu.upper() else "Lainnya")
    )

    if beban_efektif_w >= 300:
        beban_level = "Tinggi"
        beban_badge = "Tinggi"
        beban_variant = "danger"
    elif beban_efektif_w >= 220:
        beban_level = "Sedang"
        beban_badge = "Sedang"
        beban_variant = "warning"
    else:
        beban_level = "Rendah"
        beban_badge = "Rendah"
        beban_variant = "success"

    jam_hari = int(asmp.get("jam_operasional_per_hari", 24) or 24)
    hari_bln = int(asmp.get("hari_per_bulan", 30) or 30)
    kwh_bln = energi_kwh_bulan(float(beban_efektif_w), jam_hari, hari_bln)
    kwh_str = f"{str(kwh_bln).replace('.', ',')} kWh"

    tarif = asmp.get("tarif_listrik_per_kwh")
    has_tarif = tarif is not None and float(tarif or 0) > 0
    biaya_rp = round(kwh_bln * float(tarif)) if has_tarif else None
    biaya_str = f"Rp {biaya_rp:,}".replace(",", ".") if biaya_rp is not None else ""

    short_cpu = (
        cpu.replace("Intel Core ", "")
        .replace("AMD ", "")
        .replace(" Desktop", "")
        .split(" ")[0]
        if cpu != "—"
        else "—"
    )
    short_gpu = (
        "UHD 620"
        if "UHD 620" in vga
        else vga.replace("NVIDIA GeForce ", "").replace(" Desktop", "")
    )
    short_ram = ram.replace(" dengan kilat LED", "").replace("x ", "×")
    short_disk = hdd_ssd.replace("x ", " ").replace(", ", " + ").replace("SSD M.2", "M.2")
    spesifikasi_ringkas = " · ".join(
        [p for p in (short_cpu, short_gpu, short_ram, short_disk) if p and p != "—"]
    )

    u_info = (ups_lookup or {}).get(id_aset.upper(), {})
    u_id = str(u_info.get("id_aset", ""))
    u_pct = float(u_info.get("utilisasi_pct", 0.0))

    return {
        "id": id_aset,
        "id_aset": id_aset,
        "nama_aset": nama,
        "sub_label": f"{id_aset} · {grup_server}",
        "grup_server": grup_server,
        "cpu": cpu,
        "cpu_brand": cpu_brand,
        "vga": vga,
        "ram": ram,
        "hdd_ssd": hdd_ssd,
        "spesifikasi_ringkas": spesifikasi_ringkas,
        "tdp_total_w": tdp_w,
        "beban_efektif_w": beban_efektif_w,
        "watt_terukur": watt_ukur if watt_ukur > 0 else None,
        "sumber_daya_label": sumber_label,
        "psu_min_w": psu_min_w,
        "psu_rekomendasi_w": psu_rek_w,
        "formula_psu_min_w": psu_calc["formula_psu_min_w"],
        "formula_psu_rek_w": psu_calc["formula_psu_rek_w"],
        "psu_inconsistent": psu_calc["psu_inconsistent"],
        "psu_terpasang_w": psu_terpasang_w,
        "status_psu_terpasang": psu_status,
        "status_psu_variant": psu_variant,
        "tdp_display": f"{beban_efektif_w} W",
        "psu_min_display": f"{psu_min_w} W",
        "psu_rek_display": f"{psu_rek_w} W",
        "psu_pair_display": f"{psu_min_w} / {psu_rek_w} W",
        "kwh_per_bulan": kwh_bln,
        "kwh_display": kwh_str,
        "estimasi_biaya_bulan": biaya_rp,
        "biaya_display": biaya_str,
        "beban_level": beban_level,
        "beban_badge": beban_badge,
        "beban_variant": beban_variant,
        "ups_id_aset": u_id,
        "ups_nama": str(u_info.get("nama_ups") or u_info.get("nama_aset", "—")),
        "ups_utilisasi_pct": u_pct,
        "ups_status": str(u_info.get("status_utilisasi") or u_info.get("status", "—")),
        "ups_source_label": str(u_info.get("sumber_kapasitas", "")),
        "ups_display": f"{u_id} · {round(u_pct)}%" if u_id else "—",
        "lokasi": str(asset.get("lokasi", "Kantor Pusat")),
        "status": str(asset.get("status", "Digunakan")),
        "catatan": str(asset.get("catatan", "") or "—"),
    }


def query_server_power(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 20,
    assumptions: dict[str, Any] | None = None,
    ups_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Ambil daftar Rekap Watt Server dengan filter, sort, paginasi, UPS, dan Asumsi."""
    asmp = deepcopy(assumptions or MOCK_POWER_ASSUMPTIONS)
    search = str(filters.get("search", "")).strip().lower()
    tab = str(filters.get("tab", "Semua")).strip()
    cpu_brand = str(filters.get("cpu_brand", "")).strip()
    beban_level = str(filters.get("beban_level", "")).strip()
    ups_filter = str(filters.get("ups_id", "")).strip().upper()
    psu_filter = str(filters.get("psu_status", "")).strip()
    sort_by = str(filters.get("sort_by", "")).strip()
    sort_dir = str(filters.get("sort_dir", "asc")).strip().lower()
    scope = str(filters.get("scope") or "server").strip().lower()

    if ups_lookup is not None:
        ups_all = []
        srv_to_ups = ups_lookup
    else:
        ups_all, srv_to_ups = _build_ups_links_and_items(MOCK_ASSETS, asmp)

    seen_ids: set[str] = set()
    all_servers: list[dict[str, Any]] = []
    for a in MOCK_ASSETS:
        kat = str(a.get("kategori", "")).strip().lower()
        tag = str(a.get("id_aset", "")).strip().upper()
        if not tag or tag in seen_ids:
            continue
        if scope in ("server", ""):
            is_match = kat == "server"
        elif scope in ("pc", "pc operasional"):
            is_match = kat in ("pc", "laptop")
        else:
            is_match = kat in ("server", "pc", "laptop")

        if is_match:
            seen_ids.add(tag)
            row = enrich_server_power_row(a, assumptions=asmp, ups_lookup=srv_to_ups)
            all_servers.append(row)

    tab_counts = {
        "Semua": len(all_servers),
        "Operasional": sum(1 for s in all_servers if s["grup_server"] == "Operasional"),
        "Backup": sum(1 for s in all_servers if s["grup_server"] == "Backup"),
    }

    filtered: list[dict[str, Any]] = []
    for item in all_servers:
        if tab in ("Operasional", "Backup") and item["grup_server"] != tab:
            continue
        if cpu_brand and cpu_brand not in ("Semua", "all") and item["cpu_brand"] != cpu_brand:
            continue
        if (
            beban_level
            and beban_level not in ("Semua", "all")
            and item["beban_level"].lower() != beban_level.lower()
        ):
            continue
        if (
            ups_filter
            and ups_filter not in ("SEMUA", "ALL")
            and item["ups_id_aset"].upper() != ups_filter
        ):
            continue
        if psu_filter and item["status_psu_terpasang"].lower() != psu_filter.lower():
            continue
        if search:
            haystack = " ".join(
                [
                    item["id_aset"],
                    item["nama_aset"],
                    item["cpu"],
                    item["vga"],
                    item["ram"],
                    item["hdd_ssd"],
                    item["ups_id_aset"],
                ]
            ).lower()
            if search not in haystack:
                continue
        filtered.append(deepcopy(item))

    if sort_by:
        reverse = sort_dir == "desc"
        numeric_keys = {
            "tdp_total_w",
            "beban_efektif_w",
            "psu_min_w",
            "psu_rekomendasi_w",
            "kwh_per_bulan",
            "ups_utilisasi_pct",
        }
        if sort_by in numeric_keys:
            filtered.sort(key=lambda x: float(x.get(sort_by, 0) or 0), reverse=reverse)
        else:
            filtered.sort(key=lambda x: str(x.get(sort_by, "")).lower(), reverse=reverse)

    sum_tdp = sum(x["beban_efektif_w"] for x in filtered)
    sum_psu_min = sum(x["psu_min_w"] for x in filtered)
    sum_psu_rek = sum(x["psu_rekomendasi_w"] for x in filtered)
    jam_h = int(asmp.get("jam_operasional_per_hari", 24) or 24)
    hari_b = int(asmp.get("hari_per_bulan", 30) or 30)
    est_kwh = energi_kwh_bulan(float(sum_tdp), jam_h, hari_b)
    avg_tdp = round(sum_tdp / len(filtered)) if filtered else 0
    tarif = asmp.get("tarif_listrik_per_kwh")
    has_tarif = tarif is not None and float(tarif or 0) > 0
    est_biaya = round(est_kwh * float(tarif)) if has_tarif else None

    highest_srv = max(filtered, key=lambda x: x["beban_efektif_w"], default=None)
    max_tdp = highest_srv["beban_efektif_w"] if highest_srv else 0
    max_srv_name = highest_srv["nama_aset"] if highest_srv else "—"
    max_srv_id = highest_srv["id_aset"] if highest_srv else ""

    for it in filtered:
        it["tdp_bar_pct"] = max(8, round((it["beban_efektif_w"] / max(300, max_tdp)) * 100))

    ranked_all = sorted(all_servers, key=lambda x: x["beban_efektif_w"], reverse=True)
    for r_it in ranked_all:
        r_it["tdp_bar_pct"] = max(8, round((r_it["beban_efektif_w"] / 300) * 100))

    monitored_ups = [u for u in ups_all if u.get("linked_servers")]
    monitored_ups.sort(key=lambda u: u.get("utilisasi_pct", 0.0), reverse=True)
    top_ups = monitored_ups[0] if monitored_ups else None
    unfilled_ups_cnt = sum(1 for u in monitored_ups if not u.get("is_kapasitas_manual"))
    psu_kurang_cnt = sum(1 for x in filtered if x["status_psu_terpasang"] == "Kurang")

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    return {
        "items": paginated,
        "top_servers": ranked_all,
        "ups_items": monitored_ups,
        "all_ups_options": ups_all,
        "assumptions": asmp,
        "total": total,
        "page": page,
        "page_size": page_size,
        "tab_counts": tab_counts,
        "summary": {
            "total_servers": total,
            "total_tdp_w": sum_tdp,
            "total_tdp_kw": round(sum_tdp / 1000, 2),
            "total_psu_min_w": sum_psu_min,
            "total_psu_rek_w": sum_psu_rek,
            "est_kwh_month": est_kwh,
            "estimasi_biaya_bulan": est_biaya,
            "avg_tdp_w": avg_tdp,
            "max_tdp_w": max_tdp,
            "max_tdp_server": max_srv_name,
            "max_tdp_id": max_srv_id,
            "monitored_ups_count": len(monitored_ups),
            "max_ups_util_pct": round(top_ups["utilisasi_pct"]) if top_ups else 0,
            "max_ups_source": (
                top_ups["sumber_kapasitas"].lower() if top_ups else "perkiraan"
            ),
            "max_ups_status": top_ups["status_utilisasi"] if top_ups else "Aman",
            "unfilled_ups_watt_count": unfilled_ups_cnt,
            "psu_kurang_count": psu_kurang_cnt,
        },
    }


def update_mock_power_assumptions(
    payload: dict[str, Any],
    actor: str = "Administrator IT",
) -> dict[str, Any]:
    """Perbarui pengaturan asumsi di memori & catat di Audit Log."""
    MOCK_POWER_ASSUMPTIONS["jam_operasional_per_hari"] = int(
        payload.get("jam_operasional_per_hari", 24) or 24
    )
    MOCK_POWER_ASSUMPTIONS["hari_per_bulan"] = int(
        payload.get("hari_per_bulan", 30) or 30
    )
    MOCK_POWER_ASSUMPTIONS["faktor_beban_persen"] = int(
        payload.get("faktor_beban_persen", 100) or 100
    )
    raw_tarif = payload.get("tarif_listrik_per_kwh")
    MOCK_POWER_ASSUMPTIONS["tarif_listrik_per_kwh"] = (
        float(raw_tarif)
        if (raw_tarif not in (None, "", "0", 0) and float(raw_tarif) > 0)
        else None
    )
    MOCK_POWER_ASSUMPTIONS["faktor_daya_ups"] = float(
        payload.get("faktor_daya_ups", 0.6) or 0.6
    )
    MOCK_POWER_ASSUMPTIONS["batas_waspada_ups"] = int(
        payload.get("batas_waspada_ups", 70) or 70
    )
    MOCK_POWER_ASSUMPTIONS["batas_kritis_ups"] = int(
        payload.get("batas_kritis_ups", 85) or 85
    )
    record_audit_event(
        actor,
        "power.assumptions.update",
        "POWER-ASSUMPTIONS",
        f"Ubah asumsi daya: {MOCK_POWER_ASSUMPTIONS['jam_operasional_per_hari']}j/hari, "
        f"faktor beban {MOCK_POWER_ASSUMPTIONS['faktor_beban_persen']}%, "
        f"tarif={MOCK_POWER_ASSUMPTIONS['tarif_listrik_per_kwh'] or 'Opsional (kosong)'}",
    )
    return deepcopy(MOCK_POWER_ASSUMPTIONS)


def update_mock_ups_capacity_watt(
    ups_id: str,
    kapasitas_watt: int,
    actor: str = "Administrator IT",
) -> dict[str, Any]:
    """Simpan kapasitas_watt manual pada aset UPS & catat di Audit Log."""
    clean_id = ups_id.strip().upper()
    for a in MOCK_ASSETS:
        if str(a.get("id_aset", "")).strip().upper() == clean_id:
            attrs = dict(a.get("attributes") or {})
            old_w = attrs.get("kapasitas_watt") or "Kosong"
            attrs["kapasitas_watt"] = str(kapasitas_watt) if kapasitas_watt > 0 else ""
            a["attributes"] = attrs
            record_audit_event(
                actor,
                "ups.capacity_watt.update",
                clean_id,
                f"Ubah kapasitas watt UPS {clean_id} dari {old_w} "
                f"menjadi {kapasitas_watt} W (Datasheet)",
            )
            return a
    return {}


def save_server_power_entry(
    payload: dict[str, Any],
    asset_id: str = "",
) -> dict[str, Any]:
    """Tambah atau perbarui data Rekap Watt Server secara manual di MOCK_ASSETS."""
    tdp_w = _to_int_watt(payload.get("tdp_total_w", 0))
    psu_min_w = _to_int_watt(payload.get("psu_min_w", 0))
    psu_rek_w = _to_int_watt(payload.get("psu_rekomendasi_w", 0))

    nama_aset = str(payload.get("nama_aset", "")).strip().upper()
    attributes = {
        "jenis": "Server",
        "cpu": str(payload.get("cpu", "")).strip(),
        "vga": str(payload.get("vga", "")).strip(),
        "ram": str(payload.get("ram", "")).strip(),
        "hdd_ssd": str(payload.get("hdd_ssd", "")).strip(),
        "tdp_total_w": str(tdp_w),
        "psu_min_w": str(psu_min_w),
        "psu_rekomendasi_w": str(psu_rek_w),
    }

    asset_payload = {
        "nama_aset": nama_aset,
        "kategori": "Server",
        "lokasi": str(payload.get("lokasi", "Kantor Pusat")).strip() or "Kantor Pusat",
        "status": str(payload.get("status", "Digunakan")).strip() or "Digunakan",
        "catatan": str(payload.get("catatan", "Input manual Rekap Watt Server")).strip(),
        "attributes": attributes,
    }

    if asset_id:
        updated = update_mock_asset(asset_id=asset_id, payload=asset_payload)
        if updated:
            return enrich_server_power_row(updated)

    created_list = create_mock_assets(payload=asset_payload, count=1)
    return enrich_server_power_row(created_list[0])


def remove_server_power_entry(asset_id: str) -> bool:
    """Hapus satu server dari daftar Rekap Watt Server."""
    return delete_mock_asset(asset_id=asset_id)


__all__ = [
    "MOCK_POWER_ASSUMPTIONS",
    "MOCK_POWER_CATALOG",
    "MOCK_WATT_SCENARIOS",
    "STANDARD_PSU_SIZES",
    "_build_ups_links_and_items",
    "calculate_psu_specs",
    "energi_kwh_bulan",
    "enrich_server_power_row",
    "evaluate_psu_terpasang",
    "query_server_power",
    "remove_server_power_entry",
    "save_server_power_entry",
    "total_tdp",
    "update_mock_power_assumptions",
    "update_mock_ups_capacity_watt",
]
