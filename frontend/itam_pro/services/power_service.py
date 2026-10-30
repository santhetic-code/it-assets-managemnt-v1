"""
Layanan kalkulasi konsumsi daya (Thermal Design Power / TDP) server ITAM Pro.
"""
from copy import deepcopy
from typing import Any

from itam_pro.services.mock.seed import (
    MOCK_ASSETS,
    create_mock_assets,
    delete_mock_asset,
    update_mock_asset,
)


def _to_int_watt(val: Any) -> int:
    """Konversi nilai string/float watt ke integer aman."""
    try:
        cleaned = str(val or "0").strip().replace("W", "").replace("w", "").replace(",", ".")
        return max(0, round(float(cleaned)))
    except (ValueError, TypeError):
        return 0


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


def energi_kwh_bulan(total_w: float, jam: int = 720) -> float:
    """Hitung estimasi konsumsi energi bulanan dalam kWh."""
    return (total_w / 1000) * jam


def enrich_server_power_row(asset: dict[str, Any]) -> dict[str, Any]:
    """Siapkan satu baris data server untuk tabel Rekap Watt Server."""
    attrs = asset.get("attributes") or {}
    nama = str(asset.get("nama_aset", "")).strip()
    cpu = str(attrs.get("cpu", "") or "—").strip()
    vga = str(attrs.get("vga", "") or "—").strip()
    ram = str(attrs.get("ram", "") or "—").strip()
    hdd_ssd = str(attrs.get("hdd_ssd", "") or "—").strip()

    tdp_w = _to_int_watt(attrs.get("tdp_total_w", 0))
    psu_min_w = _to_int_watt(attrs.get("psu_min_w", 0))
    psu_rek_w = _to_int_watt(attrs.get("psu_rekomendasi_w", 0))

    is_backup = "BACKUP" in nama.upper() or str(asset.get("status", "")) == "Backup"
    grup_server = "Backup" if is_backup else "Operasional"

    if "AMD" in cpu.upper():
        cpu_brand = "AMD"
    elif "INTEL" in cpu.upper():
        cpu_brand = "Intel"
    else:
        cpu_brand = "Lainnya"

    if tdp_w >= 220:
        beban_level = "Tinggi (> 220 W)"
        beban_badge = "Tinggi"
        beban_variant = "warning"
    elif tdp_w >= 170:
        beban_level = "Menengah (170 - 220 W)"
        beban_badge = "Menengah"
        beban_variant = "info"
    else:
        beban_level = "Rendah (< 170 W)"
        beban_badge = "Efisien"
        beban_variant = "success"

    kwh_bln = round(energi_kwh_bulan(float(tdp_w)), 1)

    return {
        "id": str(asset.get("id_aset", "")),
        "id_aset": str(asset.get("id_aset", "")),
        "nama_aset": nama,
        "sub_label": f"Aset: {asset.get('id_aset', '')} · {grup_server}",
        "grup_server": grup_server,
        "cpu": cpu,
        "cpu_brand": cpu_brand,
        "vga": vga,
        "ram": ram,
        "hdd_ssd": hdd_ssd,
        "tdp_total_w": tdp_w,
        "psu_min_w": psu_min_w,
        "psu_rekomendasi_w": psu_rek_w,
        "tdp_display": f"{tdp_w} W",
        "psu_min_display": f"{psu_min_w} W",
        "psu_rek_display": f"{psu_rek_w} W",
        "kwh_display": f"{kwh_bln} kWh/bln",
        "beban_level": beban_level,
        "beban_badge": beban_badge,
        "beban_variant": beban_variant,
        "lokasi": str(asset.get("lokasi", "Kantor Pusat")),
        "status": str(asset.get("status", "Digunakan")),
        "catatan": str(asset.get("catatan", "") or "—"),
    }


def query_server_power(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Ambil daftar Rekap Watt Server dengan filter, sort, paginasi, dan total ESTIMASI."""
    search = str(filters.get("search", "")).strip().lower()
    tab = str(filters.get("tab", "Semua")).strip()
    cpu_brand = str(filters.get("cpu_brand", "")).strip()
    beban_level = str(filters.get("beban_level", "")).strip()
    sort_by = str(filters.get("sort_by", "")).strip()
    sort_dir = str(filters.get("sort_dir", "asc")).strip().lower()

    all_servers: list[dict[str, Any]] = [
        enrich_server_power_row(a)
        for a in MOCK_ASSETS
        if str(a.get("kategori", "")) == "Server"
    ]

    tab_counts = {
        "Semua": len(all_servers),
        "Operasional": sum(1 for s in all_servers if s["grup_server"] == "Operasional"),
        "Backup": sum(1 for s in all_servers if s["grup_server"] == "Backup"),
    }

    filtered: list[dict[str, Any]] = []
    for item in all_servers:
        if tab in ("Operasional", "Backup") and item["grup_server"] != tab:
            continue
        if cpu_brand and item["cpu_brand"] != cpu_brand:
            continue
        if beban_level and item["beban_level"] != beban_level:
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
                ]
            ).lower()
            if search not in haystack:
                continue
        filtered.append(deepcopy(item))

    if sort_by:
        reverse = sort_dir == "desc"
        numeric_keys = {"tdp_total_w", "psu_min_w", "psu_rekomendasi_w"}
        if sort_by in numeric_keys:
            filtered.sort(key=lambda x: int(x.get(sort_by, 0)), reverse=reverse)
        else:
            filtered.sort(key=lambda x: str(x.get(sort_by, "")).lower(), reverse=reverse)

    # Kalkulasi agregat untuk kartu KPI & baris ESTIMASI (mengikuti hasil filter)
    sum_tdp = sum(x["tdp_total_w"] for x in filtered)
    sum_psu_min = sum(x["psu_min_w"] for x in filtered)
    sum_psu_rek = sum(x["psu_rekomendasi_w"] for x in filtered)
    est_kwh = round(energi_kwh_bulan(float(sum_tdp)), 1)
    avg_tdp = round(sum_tdp / len(filtered), 1) if filtered else 0.0

    highest_srv = max(filtered, key=lambda x: x["tdp_total_w"], default=None)
    max_tdp = highest_srv["tdp_total_w"] if highest_srv else 0
    max_srv_name = highest_srv["nama_aset"] if highest_srv else "—"

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    return {
        "items": paginated,
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
            "avg_tdp_w": avg_tdp,
            "max_tdp_w": max_tdp,
            "max_tdp_server": max_srv_name,
        },
    }


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
    "energi_kwh_bulan",
    "enrich_server_power_row",
    "query_server_power",
    "remove_server_power_entry",
    "save_server_power_entry",
    "total_tdp",
]
