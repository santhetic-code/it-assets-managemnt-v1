"""
Layanan kalkulasi metrik ringkasan Dashboard ITAM Pro.
"""
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from dateutil.relativedelta import relativedelta

from itam_pro.services.mock.finance_mock import MOCK_BILLS, MOCK_PURCHASES
from itam_pro.services.mock.ip_mock import get_ip_conflict_summary
from itam_pro.services.mock.maintenance_mock import (
    MOCK_MAINTENANCE_PLANS,
    calculate_plan_status,
)
from itam_pro.services.mock.seed import MOCK_ASSETS
from itam_pro.services.power_service import energi_kwh_bulan, total_tdp
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


def calculate_dashboard_metrics() -> dict[str, Any]:
    today = date.today()

    # 1. Total & Digunakan
    total_assets = len(MOCK_ASSETS)
    in_use_assets = sum(1 for a in MOCK_ASSETS if a.get("status") == "Digunakan")
    in_use_percent = int((in_use_assets / total_assets * 100) if total_assets > 0 else 0)

    # 2. Donut (Aset per Kategori)
    cat_counts: dict[str, int] = defaultdict(int)
    for a in MOCK_ASSETS:
        cat_counts[a.get("kategori", "Lainnya")] += 1
    assets_by_category = [
        {"name": k, "count": v, "category_key": k.lower()}
        for k, v in cat_counts.items()
    ]

    # 3. Bar (Pembelian 6 Bulan Terakhir)
    six_months_ago = today - relativedelta(months=5)
    monthly_sales: dict[str, float] = defaultdict(float)
    for p in MOCK_PURCHASES:
        try:
            p_date = datetime.strptime(p["tanggal"], "%Y-%m-%d").date()
            if p_date >= six_months_ago.replace(day=1):
                key = f"{p_date.year}-{p_date.month:02d}"
                monthly_sales[key] += p["harga"] * p["pcs"]
        except (ValueError, TypeError):
            continue

    monthly_purchases = []
    curr = six_months_ago
    for idx in range(6):
        key = f"{curr.year}-{curr.month:02d}"
        val = monthly_sales.get(key, 0)
        monthly_purchases.append(
            {
                "month": _BULAN_ID[curr.month],
                "amount_million": round(val / 1_000_000, 1),
                "is_latest": (idx == 5),
            }
        )
        curr += relativedelta(months=1)

    # 4. Maintenance (Perlu Perhatian)
    maintenance_attention = 0
    for mp in MOCK_MAINTENANCE_PLANS:
        stat = calculate_plan_status(mp.get("jadwal_berikutnya", ""))
        if stat["status"] == "Terlambat" or mp.get("terakhir_hasil") == "Perlu tindak lanjut":
            maintenance_attention += 1

    # 5. Tagihan Segera Dibayar
    tagihan_segera = 0
    for b in MOCK_BILLS:
        if not b.get("aktif"):
            continue
        stat = calculate_bill_status(b.get("jatuh_tempo", ""), b.get("pengingat_hari", 7))
        if stat["status"] in ("Terlambat", "Segera"):
            tagihan_segera += 1

    # 6. Daya Server
    server_assets = [a for a in MOCK_ASSETS if a.get("kategori") == "Server"]
    tdp = total_tdp(server_assets)
    kwh = energi_kwh_bulan(tdp)

    # 7. Konflik IP
    ip_conflict = get_ip_conflict_summary()

    return {
        "kpis": {
            "total_assets": total_assets,
            "in_use_assets": in_use_assets,
            "in_use_percent": in_use_percent,
            "maintenance_attention": maintenance_attention,
            "tagihan_segera": tagihan_segera,
            "server_power_kw": round(tdp / 1000, 2),
            "server_energy_kwh_month": round(kwh, 1),
        },
        "monthly_purchases": monthly_purchases,
        "assets_by_category": assets_by_category,
        "ip_conflict_count": ip_conflict["conflict_entry_count"],
    }


__all__ = ["calculate_dashboard_metrics"]
