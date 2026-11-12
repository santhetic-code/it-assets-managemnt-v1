"""Layanan kalkulasi konsumsi daya (Thermal Design Power / TDP) server ITAM Pro."""

from copy import deepcopy
from typing import Any

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
        "ups_nama": str(u_info.get("nama_ups", "—")),
        "ups_utilisasi_pct": u_pct,
        "ups_status": str(u_info.get("status", "—")),
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
    """Ambil daftar Rekap Watt Server dengan filter, sort, paginasi, dan total ESTIMASI."""
    search = str(filters.get("search", "")).strip().lower()
    tab = str(filters.get("tab", "Semua")).strip()
    cpu_brand = str(filters.get("cpu_brand", "")).strip()
    beban_level = str(filters.get("beban_level", "")).strip()
    sort_by = str(filters.get("sort_by", "")).strip()
    sort_dir = str(filters.get("sort_dir", "asc")).strip().lower()

    scope = str(filters.get("scope") or "server").strip().lower()

    seen_ids: set[str] = set()
    all_servers: list[dict[str, Any]] = []
    for a in MOCK_ASSETS:
        kat = str(a.get("kategori", "")).strip().lower()
        tag = str(a.get("id_aset", "")).strip().upper()
        if not tag or tag in seen_ids:
            continue

        is_match = False
        if scope in ("server", ""):
            is_match = kat == "server"
        elif scope in ("pc", "pc operasional"):
            is_match = kat in ("pc", "laptop")
        elif scope in ("all", "semua"):
            is_match = kat in ("server", "pc", "laptop")

        if is_match:
            seen_ids.add(tag)
            row = enrich_server_power_row(a, assumptions=assumptions, ups_lookup=ups_lookup)
            if kat in ("pc", "laptop"):
                if row.get("tdp_total_w", 0) <= 0:
                    row["tdp_total_w"] = 95
                    row["beban_efektif_w"] = 95
                if row.get("psu_min_w", 0) <= 0:
                    row["psu_min_w"] = 250
                if row.get("psu_rekomendasi_w", 0) <= 0:
                    row["psu_rekomendasi_w"] = 450
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
        numeric_keys = {
            "tdp_total_w",
            "beban_efektif_w",
            "psu_min_w",
            "psu_rekomendasi_w",
        }
        if sort_by in numeric_keys:
            filtered.sort(key=lambda x: int(x.get(sort_by, 0)), reverse=reverse)
        else:
            filtered.sort(key=lambda x: str(x.get(sort_by, "")).lower(), reverse=reverse)

    sum_tdp = sum(x["tdp_total_w"] for x in filtered)
    sum_beban = sum(x["beban_efektif_w"] for x in filtered)
    sum_psu_min = sum(x["psu_min_w"] for x in filtered)
    sum_psu_rek = sum(x["psu_rekomendasi_w"] for x in filtered)
    est_kwh = energi_kwh_bulan(float(sum_beban))
    avg_tdp = round(sum_beban / len(filtered), 1) if filtered else 0.0

    highest_srv = max(filtered, key=lambda x: x["beban_efektif_w"], default=None)
    max_tdp = highest_srv["beban_efektif_w"] if highest_srv else 0
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
            "total_beban_w": sum_beban,
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
    "MOCK_POWER_ASSUMPTIONS",
    "STANDARD_PSU_SIZES",
    "calculate_psu_specs",
    "energi_kwh_bulan",
    "enrich_server_power_row",
    "evaluate_psu_terpasang",
    "query_server_power",
    "remove_server_power_entry",
    "save_server_power_entry",
    "total_tdp",
]
