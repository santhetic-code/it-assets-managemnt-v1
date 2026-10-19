"""
Data Mock Ringkasan Dashboard ITAM Pro (USE_MOCK=true).
"""
from typing import Any


def get_mock_dashboard_summary() -> dict[str, Any]:
    """Kembalikan data mentah ringkasan dashboard."""
    return {
        "kpis": {
            "total_assets": 482,
            "new_assets_this_month": 12,
            "in_use_assets": 391,
            "in_use_percent": 81,
            "in_maintenance": 18,
            "overdue_maintenance": 4,
            "expiring_warranty_30d": 9,
            "server_power_kw": 4.2,
            "server_energy_kwh_month": 3024,
        },
        "monthly_purchases": [
            {"month": "Mei", "amount_million": 42, "is_latest": False},
            {"month": "Jun", "amount_million": 18, "is_latest": False},
            {"month": "Jul", "amount_million": 65, "is_latest": False},
            {"month": "Agu", "amount_million": 31, "is_latest": False},
            {"month": "Sep", "amount_million": 88, "is_latest": False},
            {"month": "Okt", "amount_million": 54, "is_latest": True},
        ],
        "assets_by_category": [
            {"name": "PC", "count": 214, "category_key": "pc"},
            {"name": "Monitor", "count": 160, "category_key": "monitor"},
            {"name": "Server", "count": 38, "category_key": "server"},
            {"name": "UPS", "count": 24, "category_key": "ups"},
            {"name": "Lainnya", "count": 46, "category_key": "other"},
        ],
        "ups_loads": [
            {"name": "UPS Server 1", "capacity_kva": 6.0, "load_percent": 78},
            {"name": "UPS Server 2", "capacity_kva": 6.0, "load_percent": 64},
            {"name": "UPS Jaringan", "capacity_kva": 2.0, "load_percent": 91},
            {"name": "UPS Office", "capacity_kva": 1.5, "load_percent": 43},
        ],
        "attention_items": [
            {
                "title": "UPS Jaringan",
                "description": "Maintenance lewat 5 hari",
                "badge_label": "Terlambat",
                "badge_variant": "danger",
            },
            {
                "title": "VM-App-03",
                "description": "IP 10.10.1.24 bentrok",
                "badge_label": "Konflik IP",
                "badge_variant": "danger",
            },
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
        ],
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
