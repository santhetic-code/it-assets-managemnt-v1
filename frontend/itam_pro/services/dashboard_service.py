"""
Layanan kalkulasi metrik ringkasan Dashboard ITAM Pro.
"""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from itam_pro.services.mock.audit_mock import MOCK_AUDIT_LOGS
from itam_pro.services.mock.finance_mock import MOCK_BILLS, MOCK_PURCHASES
from itam_pro.services.mock.ip_mock import get_ip_conflict_summary
from itam_pro.services.mock.maintenance_mock import (
    MOCK_MAINTENANCE_PLANS,
    calculate_plan_status,
)
from itam_pro.services.mock.seed import MOCK_ASSETS
from itam_pro.services.power_service import (
    MOCK_POWER_ASSUMPTIONS,
    _build_ups_links_and_items,
    energi_kwh_bulan,
    total_tdp,
)
from itam_pro.services.recurrence import calculate_bill_status

_BULAN_ID = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
]


def aggregate_monthly_purchases(
    purchases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Satu fungsi agregasi pembelian bulanan (hanya bulan yang punya data)."""
    source = MOCK_PURCHASES if purchases is None else purchases
    monthly_totals: dict[tuple[int, int], int] = defaultdict(int)
    total_rp = 0

    for p in source:
        try:
            line_total = int(p.get("harga", 0)) * int(p.get("pcs", 1))
        except (ValueError, TypeError):
            line_total = 0
        if line_total <= 0:
            continue
        total_rp += line_total
        try:
            p_date = datetime.strptime(str(p.get("tanggal", ""))[:10], "%Y-%m-%d").date()
            monthly_totals[(p_date.year, p_date.month)] += line_total
        except (ValueError, TypeError):
            continue

    sorted_keys = sorted(k for k, v in monthly_totals.items() if v > 0)
    years = {y for y, _ in sorted_keys}
    items: list[dict[str, Any]] = []
    for idx, (yr, mo) in enumerate(sorted_keys):
        val = monthly_totals[(yr, mo)]
        label = f"{_BULAN_ID[mo]} {str(yr)[2:]}" if len(years) > 1 else _BULAN_ID[mo]
        items.append(
            {
                "month": label,
                "year_month": f"{yr}-{mo:02d}",
                "amount_rp": val,
                "amount_million": round(val / 1_000_000, 1),
                "is_latest": idx == len(sorted_keys) - 1,
            }
        )

    return {
        "items": items,
        "total_rp": total_rp,
        "total_million": round(total_rp / 1_000_000, 1),
        "month_count": len(items),
    }


def _count_expiring_warranties(today: date, days: int = 30) -> int:
    count = 0
    for a in MOCK_ASSETS:
        raw_due = str(a.get("garansi_sampai") or "").strip()
        if not raw_due:
            continue
        try:
            due = date.fromisoformat(raw_due[:10])
        except ValueError:
            continue
        if 0 <= (due - today).days <= days:
            count += 1
    return count


def _count_failed_logins_24h() -> int:
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    count = 0
    for log in MOCK_AUDIT_LOGS:
        act = str(log.get("action") or log.get("aksi") or "").strip().lower()
        if act != "login_gagal":
            continue
        raw_ts = str(log.get("timestamp") or "").replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(raw_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            if dt.astimezone(UTC) >= cutoff:
                count += 1
        except ValueError:
            continue
    return count


def _get_top_ups_loads(limit: int = 3) -> list[dict[str, Any]]:
    """Ambil 3 UPS dengan persentase beban tertinggi langsung dari power_service."""
    ups_all, _ = _build_ups_links_and_items(MOCK_ASSETS, MOCK_POWER_ASSUMPTIONS)
    monitored = [u for u in ups_all if u.get("linked_servers")]
    pool = monitored if monitored else ups_all
    pool.sort(key=lambda u: float(u.get("utilisasi_pct", 0.0)), reverse=True)
    return [
        {
            "id_aset": str(u["id_aset"]),
            "name": f"{u['id_aset']} · {u['merek_va']}",
            "capacity_kva": round(float(u.get("kapasitas_va", 650)) / 1000.0, 2),
            "load_percent": round(float(u.get("utilisasi_pct", 0.0))),
        }
        for u in pool[:limit]
    ]


def calculate_dashboard_metrics() -> dict[str, Any]:
    today = date.today()

    # 1. Total, Digunakan, & Belum Tertaut Pembelian
    total_assets = len(MOCK_ASSETS)
    in_use_assets = sum(1 for a in MOCK_ASSETS if a.get("status") == "Digunakan")
    in_use_percent = round((in_use_assets / total_assets) * 100) if total_assets > 0 else 0
    unlinked_assets = sum(
        1 for a in MOCK_ASSETS if not a.get("purchase_item_id") and not a.get("purchase_id")
    )
    new_assets_this_month = sum(
        1
        for a in MOCK_ASSETS
        if str(a.get("tanggal_masuk_gudang", "")).startswith(f"{today.year}-{today.month:02d}")
    )

    # 2. Donut (Aset per Kategori) & Ringkasan Breakdown
    cat_counts: dict[str, int] = defaultdict(int)
    for a in MOCK_ASSETS:
        cat_counts[str(a.get("kategori") or "Lainnya")] += 1
    assets_by_category = [
        {"name": k, "count": v, "category_key": k.lower()} for k, v in cat_counts.items()
    ]
    preferred_order = ("PC", "Server", "UPS", "Monitor")
    breakdown_parts = [f"{k} {cat_counts[k]}" for k in preferred_order if cat_counts.get(k, 0) > 0]
    for k, v in cat_counts.items():
        if k not in preferred_order and v > 0 and len(breakdown_parts) < 5:
            breakdown_parts.append(f"{k} {v}")
    category_breakdown = " · ".join(breakdown_parts) if breakdown_parts else "Belum ada aset"

    # 3. Pembelian per Bulan (sumber tunggal dari MOCK_PURCHASES)
    purchase_agg = aggregate_monthly_purchases()

    # 4. Maintenance (Terlambat & Perlu Perhatian)
    overdue_maintenance = 0
    maintenance_attention = 0
    for mp in MOCK_MAINTENANCE_PLANS:
        stat = calculate_plan_status(mp.get("jadwal_berikutnya", ""))
        if stat["status"] == "Terlambat":
            overdue_maintenance += 1
            maintenance_attention += 1
        elif mp.get("terakhir_hasil") == "Perlu tindak lanjut":
            maintenance_attention += 1

    # 5. Tagihan Segera Dibayar & Garansi <= 30 Hari
    tagihan_segera = 0
    for b in MOCK_BILLS:
        if not b.get("aktif"):
            continue
        stat = calculate_bill_status(b.get("jatuh_tempo", ""), b.get("pengingat_hari", 7))
        if stat["status"] in ("Terlambat", "Segera"):
            tagihan_segera += 1
    expiring_warranty_30d = _count_expiring_warranties(today, days=30)

    # 6. Daya Server (TDP & Batas Atas kWh/bulan) + Top 3 UPS
    server_assets = [a for a in MOCK_ASSETS if a.get("kategori") == "Server"]
    tdp = total_tdp(server_assets)
    kwh = energi_kwh_bulan(tdp)
    top_ups_loads = _get_top_ups_loads(limit=3)

    # 7. Konflik IP & Login Gagal 24 Jam
    ip_conflict = get_ip_conflict_summary()
    failed_logins_24h = _count_failed_logins_24h()

    return {
        "kpis": {
            "total_assets": total_assets,
            "category_breakdown": category_breakdown,
            "new_assets_this_month": new_assets_this_month,
            "in_use_assets": in_use_assets,
            "in_use_percent": in_use_percent,
            "overdue_maintenance": overdue_maintenance,
            "maintenance_attention": maintenance_attention,
            "in_maintenance": overdue_maintenance,
            "expiring_warranty_30d": expiring_warranty_30d,
            "tagihan_segera": tagihan_segera,
            "unlinked_assets": unlinked_assets,
            "failed_logins_24h": failed_logins_24h,
            "server_power_kw": round(tdp / 1000, 2),
            "server_energy_kwh_month": round(kwh, 1),
        },
        "monthly_purchases": purchase_agg["items"],
        "purchase_total_rp": purchase_agg["total_rp"],
        "purchase_total_million": purchase_agg["total_million"],
        "assets_by_category": assets_by_category,
        "ups_loads": top_ups_loads,
        "ip_conflict_count": ip_conflict["conflict_entry_count"],
    }


__all__ = ["aggregate_monthly_purchases", "calculate_dashboard_metrics"]
