"""State Controller untuk Halaman Audit Log (/audit-log)."""

from datetime import datetime
from typing import Any

import reflex as rx

from itam_pro.config import USE_MOCK
from itam_pro.services.api_client import api_client
from itam_pro.services.mock.audit_mock import query_audit_logs
from itam_pro.services.router_utils import (
    build_query_url,
    extract_client_origin_from_router,
    get_current_params,
)
from itam_pro.states.auth_state import AuthState


class AuditState(rx.State):
    logs: list[dict[str, Any]] = []
    total_items: int = 0
    raw_total_items: int = 0
    page: int = 1
    page_size: int = 10
    is_loading: bool = False

    # Tab tingkat & filter
    severity_tab: str = "Semua"  # Semua | Peringatan | Penting | Info
    search_query: str = ""
    module_filter: str = ""
    actor_filter: str = ""
    period_filter: str = ""  # "" | hari_ini | 7_hari | 30_hari | rentang
    date_from: str = ""
    date_to: str = ""
    hide_login_success: bool = False

    # Metadata tab, opsi filter, & banner peringatan 24 jam
    tab_counts: dict[str, int] = {"Semua": 0, "Peringatan": 0, "Penting": 0, "Info": 0}
    available_modules: list[str] = []
    available_actors: list[str] = []
    warning_banner_visible: bool = False
    warning_banner_count: int = 0
    warning_banner_summary: str = ""

    # Drawer detail (state eksplisit agar 100% aman di Reflex 0.9.12)
    drawer_open: bool = False
    selected_row_dom_id: str = ""
    selected_log: dict[str, Any] = {}
    selected_changes: list[dict[str, str]] = []
    selected_grouped_timestamps: list[dict[str, str]] = []

    @rx.var(cache=True)
    def module_options(self) -> list[str]:
        if self.available_modules:
            return self.available_modules
        return [
            "Autentikasi",
            "Aset",
            "IP",
            "Kredensial",
            "Maintenance",
            "Pengguna",
            "Audit Log",
        ]

    @rx.var(cache=True)
    def actor_options(self) -> list[str]:
        return self.available_actors

    @rx.var(cache=True)
    def period_options(self) -> list[str]:
        return ["Hari ini", "7 hari", "30 hari", "Rentang tanggal"]

    @rx.var(cache=True)
    def is_custom_date_range(self) -> bool:
        return self.period_filter == "Rentang tanggal"

    @rx.var(cache=True)
    def total_pages(self) -> int:
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)

    @rx.var(cache=True)
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var(cache=True)
    def page_tokens(self) -> list[str]:
        return [str(i) for i in range(1, self.total_pages + 1)]

    @rx.var(cache=True)
    def pagination_summary(self) -> str:
        if self.total_items == 0:
            return "Menampilkan 0 dari 0 kejadian"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return (
            f"Menampilkan {start}–{end} dari {self.total_items} kejadian · terbaru dulu"
        )

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total_items} kejadian"

    @rx.var(cache=True)
    def has_selected_changes(self) -> bool:
        return len(self.selected_changes) > 0

    @rx.var(cache=True)
    def is_selected_grouped(self) -> bool:
        return len(self.selected_grouped_timestamps) > 1

    @rx.var(cache=True)
    def selected_target_url(self) -> str:
        return str(self.selected_log.get("target_url", ""))

    @rx.var(cache=True)
    def selected_target_link_label(self) -> str:
        return str(self.selected_log.get("target_link_label", ""))

    def _build_filters_dict(self) -> dict[str, Any]:
        period_map = {
            "Hari ini": "hari_ini",
            "7 hari": "7_hari",
            "30 hari": "30_hari",
            "Rentang tanggal": "rentang",
        }
        mod_map = {
            "credential": "Kredensial",
            "asset": "Aset",
            "finance": "Keuangan",
            "maintenance": "Maintenance",
            "user": "Pengguna",
        }
        mod_val = (
            mod_map.get(self.module_filter.lower(), self.module_filter)
            if not USE_MOCK
            else self.module_filter
        )
        filters: dict[str, Any] = {}
        if self.search_query.strip():
            filters["search"] = self.search_query.strip()
        if self.severity_tab and self.severity_tab != "Semua":
            filters["tingkat"] = self.severity_tab
        if mod_val.strip():
            filters["module" if USE_MOCK else "modul"] = mod_val.strip()
        if self.actor_filter.strip():
            filters["pelaku"] = self.actor_filter.strip()
        if self.period_filter.strip():
            filters["periode"] = period_map.get(self.period_filter, self.period_filter)
        if self.period_filter == "Rentang tanggal":
            if self.date_from.strip():
                filters["date_from"] = self.date_from.strip()
            if self.date_to.strip():
                filters["date_to"] = self.date_to.strip()
        if self.hide_login_success:
            filters["hide_login_success"] = "true"
        return filters

    def _sync_url_script(self) -> Any:
        period_slug_map = {
            "Hari ini": "hari_ini",
            "7 hari": "7_hari",
            "30 hari": "30_hari",
            "Rentang tanggal": "rentang",
        }
        url = build_query_url(
            "/audit-log",
            {
                "tingkat": "" if self.severity_tab == "Semua" else self.severity_tab,
                "search": self.search_query,
                "modul": self.module_filter,
                "pelaku": self.actor_filter,
                "periode": period_slug_map.get(self.period_filter, ""),
                "date_from": (
                    self.date_from if self.period_filter == "Rentang tanggal" else ""
                ),
                "date_to": (
                    self.date_to if self.period_filter == "Rentang tanggal" else ""
                ),
                "hide_login": "1" if self.hide_login_success else "",
            },
        )
        return rx.call_script(f"window.history.replaceState(null, '', {url!r});")

    def _apply_response(self, res: dict[str, Any]) -> None:
        self.logs = list(res.get("items", []))
        self.total_items = int(res.get("total", len(self.logs)))
        self.raw_total_items = int(res.get("raw_total", self.total_items))

        tc = res.get("tab_counts") or {}
        self.tab_counts = {
            "Semua": int(tc.get("Semua", self.total_items)),
            "Peringatan": int(tc.get("Peringatan", 0)),
            "Penting": int(tc.get("Penting", 0)),
            "Info": int(tc.get("Info", 0)),
        }

        banner = res.get("warning_banner") or {}
        self.warning_banner_visible = bool(banner.get("visible", False))
        self.warning_banner_count = int(banner.get("count", 0))
        self.warning_banner_summary = str(banner.get("summary", ""))

        opts = res.get("filter_options") or {}
        if opts.get("modules"):
            self.available_modules = list(opts["modules"])
        if opts.get("actors"):
            self.available_actors = list(opts["actors"])

    def _sync_mock_logs(self) -> None:
        res = query_audit_logs(
            filters=self._build_filters_dict(),
            page=self.page,
            page_size=self.page_size,
        )
        self._apply_response(res)

    @rx.event
    async def load_page(self) -> None:
        """Baca filter dari query string URL (mendukung URL bagikan & drill-down Dashboard)."""
        client_ip, client_ua = extract_client_origin_from_router(self.router)
        api_client.set_client_origin(client_ip, client_ua)

        params = get_current_params(self.router)
        if params:
            raw_tingkat = (
                str(params.get("tingkat") or params.get("tab") or "").strip().lower()
            )
            tingkat_map = {
                "peringatan": "Peringatan",
                "penting": "Penting",
                "info": "Info",
                "semua": "Semua",
            }
            if raw_tingkat in tingkat_map:
                self.severity_tab = tingkat_map[raw_tingkat]
            if "search" in params or "q" in params:
                self.search_query = str(
                    params.get("search") or params.get("q") or ""
                ).strip()
            if "modul" in params or "module" in params:
                self.module_filter = str(
                    params.get("modul") or params.get("module") or ""
                ).strip()
            if "pelaku" in params or "username" in params:
                self.actor_filter = str(
                    params.get("pelaku") or params.get("username") or ""
                ).strip()
            raw_period = str(params.get("periode") or "").strip().lower()
            period_label_map = {
                "hari_ini": "Hari ini",
                "7_hari": "7 hari",
                "30_hari": "30 hari",
                "rentang": "Rentang tanggal",
            }
            if raw_period in period_label_map:
                self.period_filter = period_label_map[raw_period]
            if "date_from" in params:
                self.date_from = str(params.get("date_from") or "").strip()
            if "date_to" in params:
                self.date_to = str(params.get("date_to") or "").strip()
            if "hide_login" in params or "hide_login_success" in params:
                flag = str(
                    params.get("hide_login") or params.get("hide_login_success") or ""
                ).lower()
                self.hide_login_success = flag in ("1", "true", "yes")
            self.page = 1

        await self.fetch_logs()

    @rx.event
    async def fetch_logs(self) -> None:
        self.is_loading = True
        if USE_MOCK:
            self._sync_mock_logs()
            self.is_loading = False
            return

        client_ip, client_ua = extract_client_origin_from_router(self.router)
        api_client.set_client_origin(client_ip, client_ua)
        try:
            res = await api_client.get_audit_logs(
                filters=self._build_filters_dict(),
                page=self.page,
                page_size=self.page_size,
            )
            self._apply_response(res)
        except Exception:
            self.logs = []
            self.total_items = 0
        finally:
            self.is_loading = False

    def _refresh_after_filter_change(self) -> Any:
        self.page = 1
        if USE_MOCK:
            self._sync_mock_logs()
            return self._sync_url_script()
        return [AuditState.fetch_logs, self._sync_url_script()]

    @rx.event
    def set_severity_tab(self, tab: str) -> Any:
        if self.severity_tab == tab:
            return None
        self.severity_tab = tab
        return self._refresh_after_filter_change()

    @rx.event
    def show_warnings_from_banner(self) -> Any:
        self.severity_tab = "Peringatan"
        self.period_filter = "Hari ini"
        return self._refresh_after_filter_change()

    @rx.event
    def set_search_query(self, val: str) -> Any:
        if self.search_query == val:
            return None
        self.search_query = val
        return self._refresh_after_filter_change()

    @rx.event
    def set_module_filter(self, val: str) -> Any:
        clean = "" if val in ("Semua", "Semua modul") else val
        if self.module_filter == clean:
            return None
        self.module_filter = clean
        return self._refresh_after_filter_change()

    @rx.event
    def set_actor_filter(self, val: str) -> Any:
        clean = "" if val in ("Semua", "Semua pelaku") else val
        if self.actor_filter == clean:
            return None
        self.actor_filter = clean
        return self._refresh_after_filter_change()

    @rx.event
    def set_period_filter(self, val: str) -> Any:
        clean = "" if val in ("Semua", "Semua periode") else val
        if self.period_filter == clean:
            return None
        self.period_filter = clean
        if clean != "Rentang tanggal":
            self.date_from = ""
            self.date_to = ""
        return self._refresh_after_filter_change()

    @rx.event
    def set_date_from(self, val: str) -> Any:
        self.date_from = val
        return self._refresh_after_filter_change()

    @rx.event
    def set_date_to(self, val: str) -> Any:
        self.date_to = val
        return self._refresh_after_filter_change()

    @rx.event
    def toggle_hide_login_success(self, checked: bool) -> Any:
        self.hide_login_success = bool(checked)
        return self._refresh_after_filter_change()

    @rx.event
    def reset_filters(self) -> Any:
        self.severity_tab = "Semua"
        self.search_query = ""
        self.module_filter = ""
        self.actor_filter = ""
        self.period_filter = ""
        self.date_from = ""
        self.date_to = ""
        self.hide_login_success = False
        self.page = 1
        if USE_MOCK:
            self._sync_mock_logs()
            return self._sync_url_script()
        return [AuditState.fetch_logs, self._sync_url_script()]

    @rx.event
    def open_detail_drawer(self, row_id: Any) -> None:
        target = str(row_id)
        found = next(
            (r for r in self.logs if str(r.get("kode_audit") or r.get("id")) == target),
            None,
        )
        if not found:
            return
        self.selected_log = dict(found)
        self.selected_changes = list(found.get("changes") or [])
        self.selected_grouped_timestamps = list(found.get("grouped_timestamps") or [])
        self.selected_row_dom_id = f"audit-row-{target}"
        self.drawer_open = True

    @rx.event
    def close_detail_drawer(self) -> Any:
        self.drawer_open = False
        dom_id = self.selected_row_dom_id
        if dom_id:
            return rx.call_script(
                f"setTimeout(() => {{ const el = document.getElementById({dom_id!r}); "
                "if (el) el.focus(); }, 30);"
            )
        return None

    @rx.event
    def copy_selected_event_id(self) -> Any:
        kode = str(
            self.selected_log.get("kode_audit") or self.selected_log.get("id") or ""
        )
        if not kode:
            return None
        return [
            rx.set_clipboard(kode),
            rx.toast.success(f"ID kejadian {kode} disalin.", position="top-right"),
        ]

    @rx.event
    async def export_csv(self) -> Any:
        """Export CSV mengikuti filter aktif (khusus Administrator)."""
        actor_name = "Administrator IT"
        try:
            auth = await self.get_state(AuthState)
            if not auth.is_admin:
                return rx.toast.error(
                    "Hanya Administrator yang dapat mengekspor Audit Log."
                )
            actor_name = auth.user_display_name
        except Exception:
            pass

        client_ip, client_ua = extract_client_origin_from_router(self.router)
        api_client.set_client_origin(client_ip, client_ua)

        csv_bytes = await api_client.export_audit_logs_csv(
            filters=self._build_filters_dict(),
            actor=actor_name,
        )
        await self.fetch_logs()  # Refresh agar event 'audit_diekspor' langsung terlihat
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        return rx.download(data=csv_bytes, filename=f"audit_log_{stamp}.csv")

    @rx.event
    def prev_page(self) -> Any:
        if self.page > 1:
            self.page -= 1
            if USE_MOCK:
                self._sync_mock_logs()
                return None
            return AuditState.fetch_logs
        return None

    @rx.event
    def next_page(self) -> Any:
        if self.page < self.total_pages:
            self.page += 1
            if USE_MOCK:
                self._sync_mock_logs()
                return None
            return AuditState.fetch_logs
        return None

    @rx.event
    def select_page(self, token: str) -> Any:
        if token.isdigit():
            target = int(token)
            if target != self.page:
                self.page = target
                if USE_MOCK:
                    self._sync_mock_logs()
                    return None
                return AuditState.fetch_logs
        return None


__all__ = ["AuditState"]
