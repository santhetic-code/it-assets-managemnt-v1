"""
Data Mock Ringkasan Dashboard ITAM Pro (USE_MOCK=true).
"""

from datetime import date
from typing import Any

from itam_pro.services.dashboard_service import (
    aggregate_monthly_purchases,
    calculate_dashboard_metrics,
)
from itam_pro.services.mock.audit_mock import query_audit_logs
from itam_pro.services.mock.finance_mock import MOCK_BILLS
from itam_pro.services.mock.ip_mock import get_ip_conflict_summary
from itam_pro.services.mock.maintenance_mock import (
    MOCK_MAINTENANCE_PLANS,
    calculate_plan_status,
)
from itam_pro.services.mock.seed import MOCK_ASSETS
from itam_pro.services.recurrence import calculate_bill_status
from itam_pro.services.validators import format_tanggal


def build_maintenance_alerts() -> list[dict[str, str]]:
    """Peringatan Maintenance: jadwal terlambat (badge 'Terlambat N hari') & tindak lanjut."""
    alerts: list[dict[str, str]] = []
    for plan in MOCK_MAINTENANCE_PLANS:
        target = plan.get("objek_asset_id") or plan.get("objek_teks", "")
        kegiatan = str(plan.get("kegiatan", "")).strip()
        pic = str(plan.get("pic", "")).strip()
        jadwal_fmt = format_tanggal(plan.get("jadwal_berikutnya", ""))
        status_info = calculate_plan_status(plan.get("jadwal_berikutnya", ""))

        if status_info["status"] == "Terlambat":
            alerts.append(
                {
                    "title": f"{target} · {kegiatan}" if kegiatan else str(target),
                    "description": f"Jadwal {jadwal_fmt}" + (f" · {pic}" if pic else ""),
                    "badge_label": status_info["label"],
                    "badge_variant": "danger",
                }
            )
        elif plan.get("terakhir_hasil") == "Perlu tindak lanjut":
            alerts.append(
                {
                    "title": f"{target} · {kegiatan}" if kegiatan else str(target),
                    "description": f"Perlu tindak lanjut · {pic}" if pic else "Perlu tindak lanjut",
                    "badge_label": "Tindak lanjut",
                    "badge_variant": "warning",
                }
            )
    return alerts


def build_warranty_alerts(today: date | None = None) -> list[dict[str, str]]:
    """Peringatan aset dengan garansi berakhir <= 30 hari dari MOCK_ASSETS."""
    ref = today or date.today()
    alerts: list[dict[str, str]] = []
    for asset in MOCK_ASSETS:
        raw_due = str(asset.get("garansi_sampai") or "").strip()
        if not raw_due:
            continue
        try:
            due = date.fromisoformat(raw_due[:10])
        except ValueError:
            continue
        diff = (due - ref).days
        if 0 <= diff <= 30:
            aid = str(asset.get("id_aset", ""))
            nama = str(asset.get("nama_aset", ""))
            alerts.append(
                {
                    "title": f"{aid} · {nama}".strip(" ·"),
                    "description": f"Garansi berakhir {format_tanggal(due)}",
                    "badge_label": "Hari ini" if diff == 0 else f"Garansi {diff} hari",
                    "badge_variant": "danger" if diff <= 7 else "warning",
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
                    "badge_label": stat["label"],
                    "badge_variant": "danger",
                }
            )
        elif stat["status"] == "Segera":
            alerts.append(
                {
                    "title": f"Tagihan: {bill['nama']}",
                    "description": f"Jatuh tempo {stat['label']}",
                    "badge_label": stat["label"],
                    "badge_variant": "warning",
                }
            )
    return alerts


def get_dynamic_monthly_purchases() -> list[dict[str, Any]]:
    """Agregasi dinamis dari MOCK_PURCHASES melalui aggregate_monthly_purchases."""
    return aggregate_monthly_purchases()["items"]


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
    """Kembalikan ringkasan dashboard 100% terhitung dari sumber data mock."""
    attention_items: list[dict[str, str]] = []
    attention_items.extend(build_maintenance_alerts())
    attention_items.extend(build_bill_alerts())
    attention_items.extend(build_warranty_alerts())

    conflict_alert = build_ip_conflict_alert()
    if conflict_alert is not None:
        attention_items.append(conflict_alert)

    metrics = calculate_dashboard_metrics()
    important_logs = query_audit_logs(
        {"hide_login_success": "true"},
        page=1,
        page_size=5,
    ).get("items", [])

    return {
        "kpis": dict(metrics.get("kpis", {})),
        "monthly_purchases": metrics.get("monthly_purchases", []),
        "purchase_total_rp": metrics.get("purchase_total_rp", 0),
        "purchase_total_million": metrics.get("purchase_total_million", 0.0),
        "assets_by_category": metrics.get("assets_by_category", []),
        "ups_loads": metrics.get("ups_loads", []),
        "attention_items": attention_items,
        "recent_activities": important_logs,
    }
