"""
State Dashboard ITAM Pro.
Memuat data dari api_client.get_dashboard_summary() dan memformat angka gaya Indonesia.
"""
from typing import Any, TypedDict

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.styles import Color


class KPICardItem(TypedDict):
    label: str
    value: str
    note: str
    note_tone: str
    icon: str
    chip_tone: str


class MonthlyPurchaseItem(TypedDict):
    month: str
    amount: int
    fill: str


class CategoryAssetItem(TypedDict):
    name: str
    value: int
    formatted_value: str
    fill: str


class UPSLoadItem(TypedDict):
    label: str
    percent: int
    percent_label: str


class AttentionItem(TypedDict):
    title: str
    description: str
    badge_label: str
    badge_variant: str


class ActivityItem(TypedDict):
    actor_and_action: str
    target: str
    relative_time: str


def format_id_number(value: int | float, decimals: int = 0) -> str:
    """Format angka ke gaya Indonesia (titik ribuan, koma desimal)."""
    if decimals == 0:
        return f"{int(round(value)):,}".replace(",", ".")
    formatted = f"{float(value):,.{decimals}f}"
    parts = formatted.split(".")
    integer_part = parts[0].replace(",", ".")
    decimal_part = parts[1].rstrip("0")
    if not decimal_part:
        return integer_part
    return f"{integer_part},{decimal_part}"


CATEGORY_COLOR_MAP: dict[str, str] = {
    "pc": Color.ACCENT,
    "monitor": Color.CHART_MONITOR,
    "server": Color.SIDEBAR,
    "ups": Color.CHART_UPS,
    "other": Color.CHART_OTHER,
}


class DashboardState(rx.State):
    is_loading: bool = False
    kpi_cards: list[KPICardItem] = []
    monthly_purchases: list[MonthlyPurchaseItem] = []
    purchase_subtitle: str = "Juta rupiah · total 6 bulan Rp 0 jt"
    category_assets: list[CategoryAssetItem] = []
    total_assets_formatted: str = "0"
    ups_loads: list[UPSLoadItem] = []
    attention_items: list[AttentionItem] = []
    recent_activities: list[ActivityItem] = []

    @rx.event
    async def load_dashboard(self) -> None:
        """Muat ringkasan data dashboard saat halaman dibuka (on_load)."""
        self.is_loading = True
        data = await api_client.get_dashboard_summary()
        kpis = data.get("kpis", {})

        total_assets = int(kpis.get("total_assets", 0))
        new_month = int(kpis.get("new_assets_this_month", 0))
        in_use = int(kpis.get("in_use_assets", 0))
        in_use_pct = int(kpis.get("in_use_percent", 0))
        in_maint = int(kpis.get("in_maintenance", 0))
        overdue_maint = int(kpis.get("overdue_maintenance", 0))
        warranty_30d = int(kpis.get("expiring_warranty_30d", 0))
        power_kw = float(kpis.get("server_power_kw", 0.0))
        energy_kwh = int(kpis.get("server_energy_kwh_month", 0))

        self.total_assets_formatted = format_id_number(total_assets)

        self.kpi_cards = [
            {
                "label": "Total Aset",
                "value": format_id_number(total_assets),
                "note": f"+{format_id_number(new_month)} bulan ini",
                "note_tone": "success",
                "icon": "box",
                "chip_tone": "info",
            },
            {
                "label": "Sedang Dipakai",
                "value": format_id_number(in_use),
                "note": f"{format_id_number(in_use_pct)}% dari total",
                "note_tone": "muted",
                "icon": "smartphone",
                "chip_tone": "success",
            },
            {
                "label": "Dalam Maintenance",
                "value": format_id_number(in_maint),
                "note": f"{format_id_number(overdue_maint)} terlambat",
                "note_tone": "danger",
                "icon": "calendar",
                "chip_tone": "warning",
            },
            {
                "label": "Garansi ≤ 30 Hari",
                "value": format_id_number(warranty_30d),
                "note": "perlu tindak lanjut",
                "note_tone": "warning",
                "icon": "shield-check",
                "chip_tone": "purple",
            },
            {
                "label": "Daya Server",
                "value": f"{format_id_number(power_kw, decimals=1)} kW",
                "note": f"≈ {format_id_number(energy_kwh)} kWh / bulan",
                "note_tone": "muted",
                "icon": "zap",
                "chip_tone": "info",
            },
        ]

        raw_purchases = data.get("monthly_purchases", [])
        total_purchase = sum(int(item.get("amount_million", 0)) for item in raw_purchases)
        self.purchase_subtitle = (
            f"Juta rupiah · total 6 bulan Rp {format_id_number(total_purchase)} jt"
        )
        self.monthly_purchases = [
            {
                "month": str(item["month"]),
                "amount": int(item["amount_million"]),
                "fill": Color.ACCENT if item.get("is_latest") else Color.CHART_BAR,
            }
            for item in raw_purchases
        ]

        raw_categories = data.get("assets_by_category", [])
        self.category_assets = [
            {
                "name": str(cat["name"]),
                "value": int(cat["count"]),
                "formatted_value": format_id_number(int(cat["count"])),
                "fill": CATEGORY_COLOR_MAP.get(
                    str(cat.get("category_key", "")), Color.CHART_OTHER
                ),
            }
            for cat in raw_categories
        ]

        raw_ups = data.get("ups_loads", [])
        self.ups_loads = [
            {
                "label": (
                    f"{u['name']} · {format_id_number(float(u['capacity_kva']), decimals=1)} kVA"
                ),
                "percent": int(u["load_percent"]),
                "percent_label": f"{format_id_number(int(u['load_percent']))}%",
            }
            for u in raw_ups
        ]

        self.attention_items = [
            {
                "title": str(att["title"]),
                "description": str(att["description"]),
                "badge_label": str(att["badge_label"]),
                "badge_variant": str(att["badge_variant"]),
            }
            for att in data.get("attention_items", [])
        ]

        self.recent_activities = [
            {
                "actor_and_action": str(act["actor_and_action"]),
                "target": str(act["target"]),
                "relative_time": str(act["relative_time"]),
            }
            for act in data.get("recent_activities", [])
        ]
        self.is_loading = False

    @rx.event
    def show_coming_soon(self, feature_name: str = "Fitur ini") -> Any:
        """Tampilkan toast 'Segera hadir' untuk tombol/tautan placeholder."""
        return rx.toast.info(
            f"{feature_name} — Segera hadir.",
            position="top-right",
        )
