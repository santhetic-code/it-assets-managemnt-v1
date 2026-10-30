"""
Data Mock Ringkasan Dashboard ITAM Pro (USE_MOCK=true).
"""
from typing import Any

from itam_pro.services.dashboard_service import calculate_dashboard_metrics
from itam_pro.services.mock.finance_mock import MOCK_BILLS, MOCK_PURCHASES
from itam_pro.services.mock.ip_mock import get_ip_conflict_summary
from itam_pro.services.mock.maintenance_mock import (
    MOCK_MAINTENANCE_PLANS,
    calculate_plan_status,
)
from itam_pro.services.recurrence import calculate_bill_status


def build_maintenance_alerts() -> list[dict[str, str]]:
    """Peringatan Maintenance: jadwal terlambat dan hasil 'Perlu tindak lanjut'."""
    alerts: list[dict[str, str]] = []
    for plan in MOCK_MAINTENANCE_PLANS:
        target = plan.get("objek_asset_id") or plan.get("objek_teks", "")
        # 1. Deteksi hasil 'Perlu tindak lanjut'
        if plan.get("terakhir_hasil") == "Perlu tindak lanjut":
            alerts.append(
                {
                    "title": f"Tindak Lanjut: {target}",
                    "description": f"{plan.get('kegiatan', '')} - Perlu penanganan",
                    "badge_label": "Maintenance",
                    "badge_variant": "warning",
                }
            )
        # 2. Deteksi status Terlambat
        status_info = calculate_plan_status(plan.get("jadwal_berikutnya", ""))
        if status_info["status"] == "Terlambat":
            alerts.append(
                {
                    "title": f"Maintenance: {target}",
                    "description": f"{plan.get('kegiatan', '')} ({status_info['label']})",
                    "badge_label": "Maintenance",
                    "badge_variant": "danger",
                }
            )
    return alerts


def build_bill_alerts() -> list[dict[str, str]]:
    """Peringatan Tagihan Berulang yang Terlambat / Segera jatuh tempo."""
    alerts: list[dict[str, str]] = []
    for bill in MOCK_BILLS:
        if not bill["aktif"]:
            continue
        stat = calculate_bill_status(bill["jatuh_tempo"], bill["pengingat_hari"])
        if stat["status"] == "Terlambat":
            alerts.append(
                {
                    "title": f"Tagihan: {bill['nama']}",
                    "description": (
                        f"Jatuh tempo terlewat {stat['label'].replace('Terlambat ', '')}"
                    ),
                    "badge_label": "Finance",
                    "badge_variant": "danger",
                }
            )
        elif stat["status"] == "Segera":
            alerts.append(
                {
                    "title": f"Tagihan: {bill['nama']}",
                    "description": f"Jatuh tempo {stat['label']}",
                    "badge_label": "Finance",
                    "badge_variant": "warning",
                }
            )
    return alerts


def get_dynamic_monthly_purchases() -> list[dict[str, Any]]:
    """Agregasi dinamis 6 bulan terakhir dari data MOCK_PURCHASES."""
    month_names = {5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt"}
    base_totals: dict[str, float] = {
        "Mei": 42.0,
        "Jun": 18.0,
        "Jul": 65.0,
        "Agu": 31.0,
        "Sep": 88.0,
        "Okt": 0.0,
    }
    for item in MOCK_PURCHASES:
        tgl = str(item.get("tanggal", ""))
        try:
            m = int(tgl.split("-")[1])
            m_name = month_names.get(m)
            if m_name:
                total_val = float(item.get("harga", 0)) * float(item.get("pcs", 1))
                base_totals[m_name] = base_totals.get(m_name, 0.0) + (total_val / 1_000_000)
        except (IndexError, ValueError):
            pass

    if base_totals["Okt"] == 0:
        base_totals["Okt"] = 54.0

    return [
        {"month": "Mei", "amount_million": round(base_totals["Mei"]), "is_latest": False},
        {"month": "Jun", "amount_million": round(base_totals["Jun"]), "is_latest": False},
        {"month": "Jul", "amount_million": round(base_totals["Jul"]), "is_latest": False},
        {"month": "Agu", "amount_million": round(base_totals["Agu"]), "is_latest": False},
        {"month": "Sep", "amount_million": round(base_totals["Sep"]), "is_latest": False},
        {"month": "Okt", "amount_million": max(1, round(base_totals["Okt"])), "is_latest": True},
    ]


def build_ip_conflict_alert() -> dict[str, str] | None:
    """Bangun item peringatan Konflik IP secara dinamis dari tabel ip_entries."""
    summary = get_ip_conflict_summary()
    if summary["conflict_entry_count"] == 0:
        return None
    first_detail = (
        summary["conflict_details"][0]
        if summary["conflict_details"]
        else f"{summary['conflict_entry_count']} entri bentrok"
    )
    return {
        "title": f"Konflik IP {first_detail}",
        "subtitle": f"{summary['conflict_entry_count']} entri menggunakan alamat IPv4 yang sama",
        "description": f"{summary['conflict_entry_count']} entri menggunakan alamat IPv4 yang sama",
        "badge": "Konflik IP",
        "badge_label": "Konflik IP",
        "tone": "danger",
        "badge_variant": "danger",
    }


def get_mock_dashboard_summary() -> dict[str, Any]:
    """Kembalikan data mentah ringkasan dashboard."""
    attention_items: list[dict[str, str]] = []

    conflict_alert = build_ip_conflict_alert()
    if conflict_alert is not None:
        attention_items.append(conflict_alert)

    attention_items.extend(build_maintenance_alerts())
    attention_items.extend(build_bill_alerts())

    attention_items.extend(
        [
            {
                "title": "Server Rack-02",
                "description": "Garansi habis 12 hari lagi",
                "badge_label": "Garansi",
                "badge_variant": "warning",
            },
            {
                "title": "UPS Server 1",
                "description": "Baterai berumur > 3 tahun",
                "badge_label": "Baterai",
                "badge_variant": "warning",
            },
        ]
    )

    overdue_maint_count = sum(
        1
        for p in MOCK_MAINTENANCE_PLANS
        if calculate_plan_status(p.get("jadwal_berikutnya", ""))["status"] == "Terlambat"
    )

    metrics = calculate_dashboard_metrics()
    kpis = dict(metrics.get("kpis", {}))
    kpis.setdefault("new_assets_this_month", 2)
    kpis.setdefault("in_maintenance", metrics["kpis"].get("maintenance_attention", 0))
    kpis.setdefault("overdue_maintenance", overdue_maint_count)
    kpis.setdefault("expiring_warranty_30d", 2)

    return {
        "kpis": kpis,
        "monthly_purchases": metrics.get("monthly_purchases", []),
        "assets_by_category": metrics.get("assets_by_category", []),
        "ups_loads": [
            {"name": "UPS Server 1", "capacity_kva": 6.0, "load_percent": 78},
            {"name": "UPS Server 2", "capacity_kva": 6.0, "load_percent": 64},
            {"name": "UPS Jaringan", "capacity_kva": 2.0, "load_percent": 91},
            {"name": "UPS Office", "capacity_kva": 1.5, "load_percent": 43},
        ],
        "attention_items": attention_items,
        "recent_activities": [
            {
                "actor_and_action": "Admin IT menambah aset ",
                "target": "PC-0214",
                "relative_time": "5 mnt lalu",
            },
            {
                "actor_and_action": "Teknisi 1 menjadwalkan maintenance ",
                "target": "UPS-03",
                "relative_time": "1 jam lalu",
            },
            {
                "actor_and_action": "Admin IT mengunggah invoice ",
                "target": "INV-2026-1017",
                "relative_time": "3 jam lalu",
            },
            {
                "actor_and_action": "Teknisi 2 mengubah IP ",
                "target": "VM-App-03",
                "relative_time": "Kemarin",
            },
            {
                "actor_and_action": "Admin IT membuka kredensial ",
                "target": "Router Core",
                "relative_time": "Kemarin",
            },
        ],
    }
