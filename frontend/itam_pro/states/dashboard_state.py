"""
State Dashboard ITAM Pro.
Memuat data dari api_client.get_dashboard_summary() dan memformat angka gaya Indonesia.
"""

import asyncio
import csv
import io
import re
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


def _safe_int(val: Any) -> int:
    """Konversi aman int/float/string (termasuk format 'Rp 44.570.520') ke int."""
    if isinstance(val, bool) or val is None:
        return 0
    if isinstance(val, (int, float)):
        return round(val)
    text = str(val).strip()
    if not text:
        return 0
    digits = re.sub(r"[^\d]", "", text.split("(", 1)[0])
    return int(digits) if digits else 0


def _normalize_dashboard_activity(act: dict[str, Any]) -> ActivityItem | None:
    """Normalisasi baris Aktivitas Penting (sembunyikan login sukses & atribusi login gagal)."""
    aksi_raw = str(act.get("aksi") or act.get("action") or "").strip().lower()
    act_key = re.sub(r"[^a-z0-9]+", "_", aksi_raw).strip("_")
    aksi_lbl = str(act.get("aksi_label") or act.get("actor_and_action") or "Aktivitas").strip()
    hasil_low = str(act.get("hasil") or act.get("status") or "").strip().lower()

    is_login_success = (
        act_key in ("user_login", "login", "login_berhasil") and hasil_low != "ditolak"
    ) or ("login berhasil" in aksi_lbl.lower())
    if is_login_success:
        return None

    is_failed_login = (
        act_key == "login_gagal"
        or "login gagal" in aksi_lbl.lower()
        or "login_gagal" in aksi_lbl.lower()
    )
    is_unauth_failed = is_failed_login and act.get("is_authenticated") is not True

    tgt = str(act.get("target_id") or act.get("target") or "").strip()
    if is_failed_login and tgt and tgt != "-":
        title_txt = f"Login gagal akun '{tgt}'"
    elif tgt and tgt != "-" and tgt.lower() not in aksi_lbl.lower():
        title_txt = f"{aksi_lbl} {tgt}".strip()
    else:
        title_txt = aksi_lbl

    actor_txt = (
        "Tidak terautentikasi"
        if is_unauth_failed
        else str(act.get("nama_pengguna") or act.get("actor") or "System").strip() or "System"
    )

    tgl_wib = str(act.get("tanggal_wib") or "").strip()
    jam_wib = str(act.get("jam_wib") or "").replace(" WIB", "").strip()
    short_time = (
        f"{tgl_wib.rsplit(' ', 1)[0]} {jam_wib}".strip()
        if tgl_wib and jam_wib
        else str(act.get("waktu_wib") or act.get("relative_time") or "").strip()
    )
    is_warning = (
        str(act.get("tingkat") or "").strip().lower() == "peringatan"
        or is_failed_login
        or act_key in ("akun_terkunci", "reveal_ditolak", "hak_ditolak")
    )

    return {
        "title": title_txt,
        "actor": actor_txt,
        "relative_time": short_time,
        "is_warning": is_warning,
        "href": f"/audit-log?search={tgt}" if tgt and tgt != "-" else "/audit-log",
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

    # Scalar KPI (satu sumber data untuk hero_stat_card + 4 stat_card)
    kpi_total_assets: str = "0"
    kpi_category_breakdown: str = ""
    kpi_in_use: str = "0"
    kpi_in_use_pct: int = 0
    kpi_in_use_note: str = "0% dari total"
    kpi_overdue_maint: int = 0
    kpi_overdue_maint_display: str = "0"
    kpi_overdue_note: str = "semua jadwal tepat waktu"
    kpi_warranty_30d: int = 0
    kpi_warranty_display: str = "0"
    kpi_warranty_note: str = "tidak ada yang mendesak"
    kpi_power_kw_display: str = "0 kW"
    kpi_power_kwh_note: str = "batas atas ≈ 0 kWh/bulan"

    @rx.var(cache=True)
    def has_attention_items(self) -> bool:
        """True jika terdapat minimal 1 item Perlu Perhatian."""
        return len(self.attention_items) > 0

    @rx.event
    async def load_dashboard(self) -> None:
        """Muat ringkasan data dashboard secara dinamis (mock & live backend)."""
        self.is_loading = True
        data = await api_client.get_dashboard_summary()
        kpis = dict(data.get("kpis") or {})

        now_wib = datetime.now(UTC).astimezone(_WIB_TZ)
        self.last_updated_wib = f"{format_tanggal(now_wib)}, {now_wib.strftime('%H:%M')} WIB"

        total_assets = _safe_int(kpis.get("total_assets", 0))
        in_use = _safe_int(kpis.get("in_use_assets", 0))
        in_use_pct = (
            _safe_int(kpis.get("in_use_percent"))
            if "in_use_percent" in kpis
            else (round((in_use / total_assets) * 100) if total_assets > 0 else 0)
        )
        overdue_maint = _safe_int(
            kpis.get("overdue_maintenance", kpis.get("in_maintenance", 0))
        )
        warranty_30d = _safe_int(kpis.get("expiring_warranty_30d", 0))
        power_kw = float(kpis.get("server_power_kw", 0.0) or 0.0)
        energy_kwh = round(float(kpis.get("server_energy_kwh_month", 0) or 0))
        failed_24h = _safe_int(kpis.get("failed_logins_24h", 0))
        unlinked_assets = _safe_int(kpis.get("unlinked_assets", 0))
        total_purchase_rp = _safe_int(data.get("purchase_total_rp", 0))

        # Lengkapi metrik yang belum disediakan endpoint /api/v1/dashboard/summary saat live backend
        if not USE_MOCK:
            need_unlinked = "unlinked_assets" not in kpis
            need_failed = "failed_logins_24h" not in kpis
            need_purchase_total = total_purchase_rp <= 0

            tasks: dict[str, Any] = {}
            if need_unlinked:
                tasks["unlinked"] = api_client.get_assets(
                    filters={"no_purchase": "1"}, page=1, page_size=1
                )
            if need_failed:
                tasks["audit_24h"] = api_client.get_audit_logs(
                    filters={"tingkat": "Peringatan", "periode": "hari_ini"},
                    page=1,
                    page_size=50,
                )
            if need_purchase_total:
                tasks["purchases"] = api_client.get_purchases(filters={}, page=1, page_size=1)

            if tasks:
                keys = list(tasks.keys())
                results = await asyncio.gather(*tasks.values(), return_exceptions=True)
                res_map = dict(zip(keys, results, strict=False))

                unlinked_res = res_map.get("unlinked")
                if isinstance(unlinked_res, dict):
                    sum_u = unlinked_res.get("summary") or {}
                    unlinked_assets = _safe_int(
                        sum_u.get("belum_terhubung_pembelian", unlinked_res.get("total", 0))
                    )

                audit_res = res_map.get("audit_24h")
                if isinstance(audit_res, dict):
                    audit_items = list(audit_res.get("items") or [])
                    failed_24h = sum(
                        1
                        for it in audit_items
                        if "login_gagal"
                        in re.sub(
                            r"[^a-z0-9]+",
                            "_",
                            str(it.get("aksi") or it.get("action") or "").lower(),
                        )
                        or "login gagal" in str(it.get("aksi_label") or "").lower()
                    )
                    if failed_24h == 0:
                        banner_obj = audit_res.get("warning_banner") or {}
                        failed_24h = _safe_int(banner_obj.get("count", 0))

                purch_res = res_map.get("purchases")
                if isinstance(purch_res, dict):
                    total_purchase_rp = _safe_int(
                        (purch_res.get("summary") or {}).get("total_belanja", 0)
                    )

        # Hitung breakdown kategori dari assets_by_category bila belum ada di payload kpis
        raw_categories = list(data.get("assets_by_category") or [])
        category_breakdown = str(kpis.get("category_breakdown") or "").strip()
        if not category_breakdown and raw_categories:
            parts = [
                f"{c.get('name', '')} {_safe_int(c.get('count', 0))}"
                for c in raw_categories
                if _safe_int(c.get("count", 0)) > 0
            ]
            category_breakdown = " · ".join(parts[:4])

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

        # Update scalar KPI (dipakai oleh hero_stat_card + 4 stat_card)
        self.total_assets_formatted = format_id_number(total_assets)
        self.kpi_total_assets = format_id_number(total_assets)
        self.kpi_category_breakdown = (
            category_breakdown or f"{format_id_number(total_assets)} aset terdaftar"
        )
        self.kpi_in_use = format_id_number(in_use)
        self.kpi_in_use_pct = in_use_pct
        self.kpi_in_use_note = f"{format_id_number(in_use_pct)}% dari total"
        self.kpi_overdue_maint = overdue_maint
        self.kpi_overdue_maint_display = format_id_number(overdue_maint)
        self.kpi_overdue_note = (
            "maintenance melewati jadwal" if overdue_maint > 0 else "semua jadwal tepat waktu"
        )
        self.kpi_warranty_30d = warranty_30d
        self.kpi_warranty_display = format_id_number(warranty_30d)
        self.kpi_warranty_note = (
            "perlu tindak lanjut" if warranty_30d > 0 else "tidak ada yang mendesak"
        )
        self.kpi_power_kw_display = f"{format_id_number(power_kw, decimals=1)} kW"
        self.kpi_power_kwh_note = f"batas atas ≈ {format_id_number(energy_kwh)} kWh/bulan"

        # Tetap simpan kpi_cards untuk export_dashboard_report & kompatibilitas
        self.kpi_cards = [
            {
                "label": "TOTAL ASET",
                "value": self.kpi_total_assets,
                "note": self.kpi_category_breakdown,
                "note_tone": "neutral",
                "icon": "box",
                "chip_tone": "info",
                "value_tone": "default",
                "primary": True,
                "href": "/assets",
            },
            {
                "label": "SEDANG DIPAKAI",
                "value": self.kpi_in_use,
                "note": self.kpi_in_use_note,
                "note_tone": "neutral",
                "icon": "circle-check",
                "chip_tone": "purple",
                "value_tone": "default",
                "primary": False,
                "href": "/assets?status=Digunakan",
            },
            {
                "label": "JADWAL TERLAMBAT",
                "value": self.kpi_overdue_maint_display,
                "note": self.kpi_overdue_note,
                "note_tone": "neutral",
                "icon": "clock",
                "chip_tone": "success",
                "value_tone": "danger" if overdue_maint > 0 else "default",
                "primary": False,
                "href": "/operations/maintenance",
            },
            {
                "label": "GARANSI ≤ 30 HARI",
                "value": self.kpi_warranty_display,
                "note": self.kpi_warranty_note,
                "note_tone": "warning" if warranty_30d > 0 else "neutral",
                "icon": "shield",
                "chip_tone": "warning",
                "value_tone": "warning" if warranty_30d > 0 else "default",
                "primary": False,
                "href": "/assets?warranty=expiring",
            },
            {
                "label": "DAYA SERVER (TDP)",
                "value": self.kpi_power_kw_display,
                "note": self.kpi_power_kwh_note,
                "note_tone": "neutral",
                "icon": "zap",
                "chip_tone": "info",
                "value_tone": "default",
                "primary": False,
                "href": "/watt-server",
            },
        ]

        # Pembelian per Bulan (skala otomatis, total seragam dengan halaman Pembelian)
        raw_purchases = list(data.get("monthly_purchases") or [])
        if total_purchase_rp > 0:
            self.purchase_subtitle = (
                f"juta rupiah, skala otomatis · total {format_rupiah(total_purchase_rp)}"
            )
        else:
            total_jt = sum(float(item.get("amount_million", 0) or 0) for item in raw_purchases)
            self.purchase_subtitle = (
                "juta rupiah, skala otomatis · "
                f"total Rp {format_id_number(total_jt, decimals=1)} jt"
            )
        self.monthly_purchases = [
            {
                "month": str(item["month"]),
                "amount": round(float(item.get("amount_million", 0) or 0), 1),
                "fill": Color.ACCENT if item.get("is_latest") else Color.CHART_BAR,
            }
            for item in raw_purchases
        ]

        # Aset per Kategori (Donat + Legenda)
        if not USE_MOCK and raw_categories:
            try:
                asset_st = await self.get_state(AssetState)
                cat_map = {
                    str(c.get("category_key", "")).lower(): _safe_int(c.get("count", 0))
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
                "value": _safe_int(cat.get("count", 0)),
                "formatted_value": format_id_number(_safe_int(cat.get("count", 0))),
                "fill": CATEGORY_COLOR_MAP.get(
                    str(cat.get("category_key", "")).lower(), Color.CHART_OTHER
                ),
                "href": f"/assets?kategori={cat['name']}",
            }
            for cat in raw_categories
        ]

        # Beban UPS Tertinggi (3 teratas)
        raw_ups = list(data.get("ups_loads") or [])[:3]
        self.ups_loads = [
            {
                "label": str(u["name"]),
                "percent": round(float(u.get("load_percent", 0) or 0)),
                "percent_label": (
                    f"{format_id_number(round(float(u.get('load_percent', 0) or 0)))}%"
                ),
            }
            for u in raw_ups
        ]

        # Perlu Perhatian (maksimal 5 item paling mendesak)
        self.attention_items = [
            {
                "title": str(att["title"]),
                "description": str(att["description"]),
                "badge_label": str(att["badge_label"]),
                "badge_variant": str(att["badge_variant"]),
            }
            for att in list(data.get("attention_items") or [])[:5]
        ]

        # Aktivitas Penting (tanpa login sukses + atribusi Tidak terautentikasi untuk login gagal)
        raw_activities = list(data.get("recent_activities") or [])
        if USE_MOCK:
            from itam_pro.services.mock.audit_mock import query_audit_logs

            raw_activities = query_audit_logs(
                {"hide_login_success": "true"},
                page=1,
                page_size=4,
            ).get("items", [])

        important_acts: list[ActivityItem] = []
        for act in raw_activities:
            normalized = _normalize_dashboard_activity(act)
            if normalized is not None:
                important_acts.append(normalized)
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
