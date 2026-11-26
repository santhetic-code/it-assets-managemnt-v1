"""
State Dashboard ITAM Pro.
Memuat data dari api_client.get_dashboard_summary() dan memformat angka gaya Indonesia.
"""

import csv
import io
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, TypedDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import reflex as rx

from itam_pro.config import USE_MOCK
from itam_pro.services.api_client import api_client
from itam_pro.services.validators import format_rupiah, format_tanggal
from itam_pro.states.asset_state import AssetState
from itam_pro.styles import Color

try:
    _WIB_TZ = ZoneInfo("Asia/Jakarta")
except ZoneInfoNotFoundError:
    _WIB_TZ = timezone(timedelta(hours=7))


class KPICardItem(TypedDict):
    label: str
    value: str
    note: str
    note_tone: str
    icon: str
    chip_tone: str
    value_tone: str
    primary: bool
    href: str


class MonthlyPurchaseItem(TypedDict):
    month: str
    amount: int | float
    fill: str


class CategoryAssetItem(TypedDict):
    name: str
    value: int
    formatted_value: str
    fill: str
    href: str


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
    title: str
    actor: str
    relative_time: str
    is_warning: bool
    href: str


def format_id_number(value: int | float, decimals: int = 0) -> str:
    """Format angka ke gaya Indonesia (titik ribuan, koma desimal)."""
    if decimals == 0:
        return f"{round(value):,}".replace(",", ".")
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
    "router": Color.PURPLE_FG,
    "ssd": Color.SUCCESS_FG,
    "other": Color.CHART_OTHER,
}


class DashboardState(rx.State):
    is_loading: bool = False
    kpi_cards: list[KPICardItem] = []
    monthly_purchases: list[dict[str, Any]] = []
    purchase_subtitle: str = "Juta rupiah · total 6 bulan Rp 0 jt"
    category_assets: list[dict[str, Any]] = []
    total_assets_formatted: str = "0"
    ups_loads: list[UPSLoadItem] = []
    attention_items: list[AttentionItem] = []
    recent_activities: list[ActivityItem] = []
    banner_visible: bool = False
    banner_summary: str = ""
    last_updated_wib: str = "—"

    @rx.var(cache=True)
    def has_attention_items(self) -> bool:
        """True jika terdapat minimal 1 item Perlu Perhatian."""
        return len(self.attention_items) > 0

    @rx.event
    async def load_dashboard(self) -> None:
        """Muat ringkasan data dashboard secara dinamis (tanpa angka literal)."""
        self.is_loading = True
        data = await api_client.get_dashboard_summary()
        kpis = data.get("kpis", {})

        now_wib = datetime.now(UTC).astimezone(_WIB_TZ)
        self.last_updated_wib = f"{format_tanggal(now_wib)}, {now_wib.strftime('%H:%M')} WIB"

        total_assets = int(kpis.get("total_assets", 0))
        category_breakdown = str(kpis.get("category_breakdown") or "")
        in_use = int(kpis.get("in_use_assets", 0))
        in_use_pct = int(kpis.get("in_use_percent", 0))
        overdue_maint = int(kpis.get("overdue_maintenance", 0))
        warranty_30d = int(kpis.get("expiring_warranty_30d", 0))
        power_kw = float(kpis.get("server_power_kw", 0.0))
        energy_kwh = round(float(kpis.get("server_energy_kwh_month", 0)))
        failed_24h = int(kpis.get("failed_logins_24h", 0))
        unlinked_assets = int(kpis.get("unlinked_assets", 0))

        self.total_assets_formatted = format_id_number(total_assets)

        # Banner ringkas amber di bawah header
        banner_parts: list[str] = []
        if overdue_maint > 0:
            banner_parts.append(f"{format_id_number(overdue_maint)} jadwal maintenance terlambat")
        if failed_24h > 0:
            banner_parts.append(f"{format_id_number(failed_24h)} login gagal dalam 24 jam")
        if unlinked_assets > 0:
            banner_parts.append(
                f"{format_id_number(unlinked_assets)} aset belum tertaut ke pembelian"
            )
        self.banner_visible = len(banner_parts) > 0
        self.banner_summary = " · ".join(banner_parts)

        self.kpi_cards = [
            {
                "label": "TOTAL ASET",
                "value": format_id_number(total_assets),
                "note": category_breakdown or f"{format_id_number(total_assets)} aset terdaftar",
                "note_tone": "neutral",
                "icon": "",
                "chip_tone": "info",
                "value_tone": "default",
                "primary": True,
                "href": "/assets",
            },
            {
                "label": "SEDANG DIPAKAI",
                "value": format_id_number(in_use),
                "note": f"{format_id_number(in_use_pct)}% dari total",
                "note_tone": "neutral",
                "icon": "",
                "chip_tone": "success",
                "value_tone": "default",
                "primary": False,
                "href": "/assets?status=Digunakan",
            },
            {
                "label": "JADWAL TERLAMBAT",
                "value": format_id_number(overdue_maint),
                "note": (
                    "maintenance melewati jadwal"
                    if overdue_maint > 0
                    else "semua jadwal tepat waktu"
                ),
                "note_tone": "neutral",
                "icon": "",
                "chip_tone": "danger",
                "value_tone": "danger" if overdue_maint > 0 else "default",
                "primary": False,
                "href": "/maintenance",
            },
            {
                "label": "GARANSI ≤ 30 HARI",
                "value": format_id_number(warranty_30d),
                "note": (
                    "perlu tindak lanjut"
                    if warranty_30d > 0
                    else "tidak ada yang mendesak"
                ),
                "note_tone": "warning" if warranty_30d > 0 else "neutral",
                "icon": "",
                "chip_tone": "purple",
                "value_tone": "warning" if warranty_30d > 0 else "default",
                "primary": False,
                "href": "/assets?warranty=expiring",
            },
            {
                "label": "DAYA SERVER (TDP)",
                "value": f"{format_id_number(power_kw, decimals=1)} kW",
                "note": f"batas atas ≈ {format_id_number(energy_kwh)} kWh/bulan",
                "note_tone": "neutral",
                "icon": "",
                "chip_tone": "info",
                "value_tone": "default",
                "primary": False,
                "href": "/watt-server",
            },
        ]

        # Pembelian per Bulan (sumber agregasi tunggal dari dashboard_service.py)
        raw_purchases = data.get("monthly_purchases", [])
        total_purchase_rp = int(data.get("purchase_total_rp") or 0)
        if total_purchase_rp > 0:
            self.purchase_subtitle = (
                f"juta rupiah, skala otomatis · total {format_rupiah(total_purchase_rp)}"
            )
        else:
            total_jt = sum(float(item.get("amount_million", 0)) for item in raw_purchases)
            self.purchase_subtitle = (
                "juta rupiah, skala otomatis · "
                f"total Rp {format_id_number(total_jt, decimals=1)} jt"
            )
        self.monthly_purchases = [
            {
                "month": str(item["month"]),
                "amount": round(float(item["amount_million"]), 1),
                "fill": Color.ACCENT if item.get("is_latest") else Color.CHART_BAR,
            }
            for item in raw_purchases
        ]

        # Aset per Kategori (Donat + Legenda)
        raw_categories = data.get("assets_by_category", [])
        if not USE_MOCK and raw_categories:
            try:
                asset_st = await self.get_state(AssetState)
                cat_map = {
                    str(c.get("category_key", "")).lower(): int(c.get("count", 0))
                    for c in raw_categories
                }
                asset_st.sidebar_counts = {
                    "all": total_assets,
                    "pc": cat_map.get("pc", 0),
                    "server": cat_map.get("server", 0),
                    "monitor": cat_map.get("monitor", 0),
                    "ups": cat_map.get("ups", 0),
                }
            except Exception:
                pass
        self.category_assets = [
            {
                "name": str(cat["name"]),
                "value": int(cat["count"]),
                "formatted_value": format_id_number(int(cat["count"])),
                "fill": CATEGORY_COLOR_MAP.get(
                    str(cat.get("category_key", "")).lower(), Color.CHART_OTHER
                ),
                "href": f"/assets?kategori={cat['name']}",
            }
            for cat in raw_categories
        ]

        # Beban UPS Tertinggi (3 teratas)
        raw_ups = list(data.get("ups_loads", []))[:3]
        self.ups_loads = [
            {
                "label": str(u["name"]),
                "percent": round(float(u.get("load_percent", 0))),
                "percent_label": (
                    f"{format_id_number(round(float(u.get('load_percent', 0))))}%"
                ),
            }
            for u in raw_ups
        ]

        # Perlu Perhatian (maksimal 5 item paling mendesak di kartu)
        self.attention_items = [
            {
                "title": str(att["title"]),
                "description": str(att["description"]),
                "badge_label": str(att["badge_label"]),
                "badge_variant": str(att["badge_variant"]),
            }
            for att in list(data.get("attention_items", []))[:5]
        ]

        # Aktivitas Penting (tanpa login sukses)
        raw_activities = data.get("recent_activities", [])
        if USE_MOCK:
            from itam_pro.services.mock.audit_mock import query_audit_logs

            raw_activities = query_audit_logs(
                {"hide_login_success": "true"},
                page=1,
                page_size=4,
            ).get("items", [])

        important_acts: list[ActivityItem] = []
        for act in raw_activities:
            aksi_raw = str(act.get("aksi") or act.get("action") or "").lower()
            if (
                aksi_raw in ("user.login", "login", "login_berhasil")
                and act.get("hasil") == "Berhasil"
            ):
                continue
            aksi_lbl = str(act.get("aksi_label") or act.get("actor_and_action") or "Aktivitas")
            tgt = str(act.get("target_id") or act.get("target") or "").strip()
            title_txt = f"{aksi_lbl} {tgt}".strip() if tgt and tgt != "-" else aksi_lbl
            tgl_wib = str(act.get("tanggal_wib") or "")
            jam_wib = str(act.get("jam_wib") or "").replace(" WIB", "")
            short_time = (
                f"{tgl_wib.rsplit(' ', 1)[0]} {jam_wib}".strip()
                if tgl_wib and jam_wib
                else str(act.get("waktu_wib") or act.get("relative_time") or "")
            )
            important_acts.append(
                {
                    "title": title_txt,
                    "actor": str(act.get("nama_pengguna") or act.get("actor") or "System"),
                    "relative_time": short_time,
                    "is_warning": str(act.get("tingkat") or "") == "Peringatan",
                    "href": f"/audit-log?search={tgt}" if tgt and tgt != "-" else "/audit-log",
                }
            )
        self.recent_activities = important_acts[:4]
        self.is_loading = False

    @rx.event
    def scroll_to_attention(self) -> Any:
        """Gulir ke kartu Perlu Perhatian dari banner ringkas."""
        return rx.call_script(
            "const el = document.getElementById('dashboard-attention-section'); "
            "if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'});"
        )

    @rx.event
    def export_dashboard_report(self) -> Any:
        """Unduh ringkasan KPI Dashboard dalam format CSV."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Metrik", "Nilai", "Keterangan"])
        for card in self.kpi_cards:
            writer.writerow([card["label"], card["value"], card["note"]])
        return rx.download(data=buf.getvalue(), filename="Ringkasan_Dashboard_ITAM_Pro.csv")

    @rx.event
    def show_coming_soon(self, feature_name: str) -> Any:
        """Tampilkan toast 'Segera hadir' untuk tombol/tautan placeholder."""
        return rx.toast.info(
            f"{feature_name} — Segera hadir.",
            position="top-right",
        )
