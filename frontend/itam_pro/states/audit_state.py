"""State Controller untuk Halaman Audit Log (/audit-log).
Dioptimalkan dengan @rx.var(cache=True) dan filter guards.
"""
from typing import Any

import reflex as rx

from itam_pro.config import USE_MOCK
from itam_pro.services.api_client import api_client
from itam_pro.services.mock.audit_mock import query_audit_logs


class AuditState(rx.State):
    logs: list[dict[str, Any]] = []
    total_items: int = 0
    page: int = 1
    page_size: int = 15
    is_loading: bool = False

    search_query: str = ""
    module_filter: str = ""

    @rx.var(cache=True)
    def module_options(self) -> list[str]:
        return ["credential", "asset", "finance", "maintenance", "user"]

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
            return "Menampilkan 0 dari 0 catatan"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return f"Menampilkan {start}-{end} dari {self.total_items} catatan"

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total_items} catatan"

    def _sync_mock_logs(self) -> None:
        res = query_audit_logs(
            filters={"search": self.search_query, "module": self.module_filter},
            page=self.page,
            page_size=self.page_size,
        )
        self.logs = res["items"]
        self.total_items = res["total"]

    @rx.event
    async def load_page(self) -> None:
        await self.fetch_logs()

    @rx.event
    async def fetch_logs(self) -> None:
        if USE_MOCK:
            self._sync_mock_logs()
            return

        mod_map = {
            "credential": "Kredensial",
            "asset": "Aset",
            "finance": "Keuangan",
            "maintenance": "Maintenance",
            "user": "Pengguna",
        }
        mod_val = mod_map.get(self.module_filter.lower(), self.module_filter)
        try:
            res = await api_client.get_audit_logs(
                filters={"search": self.search_query, "modul": mod_val},
                page=self.page,
                page_size=self.page_size,
            )
            self.logs = list(res.get("items", []))
            self.total_items = int(res.get("total", len(self.logs)))
        except Exception:
            self.logs = []
            self.total_items = 0

    @rx.event
    def set_search_query(self, val: str) -> Any:
        if self.search_query == val:
            return None
        self.search_query = val
        self.page = 1
        if USE_MOCK:
            self._sync_mock_logs()
            return None
        return AuditState.fetch_logs

    @rx.event
    def set_module_filter(self, val: str) -> Any:
        if self.module_filter == val:
            return None
        self.module_filter = val
        self.page = 1
        if USE_MOCK:
            self._sync_mock_logs()
            return None
        return AuditState.fetch_logs

    @rx.event
    def reset_filters(self) -> Any:
        self.search_query = ""
        self.module_filter = ""
        self.page = 1
        if USE_MOCK:
            self._sync_mock_logs()
            return None
        return AuditState.fetch_logs

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
