"""State Controller untuk Halaman Audit Log (/audit-log)."""
from typing import Any

import reflex as rx

from itam_pro.services.mock.audit_mock import query_audit_logs


class AuditState(rx.State):
    logs: list[dict[str, Any]] = []
    total_items: int = 0
    page: int = 1
    page_size: int = 15
    is_loading: bool = False

    search_query: str = ""
    module_filter: str = ""

    @rx.var
    def module_options(self) -> list[str]:
        return ["credential", "asset", "finance", "maintenance", "user"]

    @rx.var
    def total_pages(self) -> int:
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)

    @rx.var
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var
    def page_tokens(self) -> list[str]:
        return [str(i) for i in range(1, self.total_pages + 1)]

    @rx.var
    def pagination_summary(self) -> str:
        if self.total_items == 0:
            return "Menampilkan 0 dari 0 catatan"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return f"Menampilkan {start}-{end} dari {self.total_items} catatan"

    @rx.var
    def result_count_label(self) -> str:
        return f"{self.total_items} catatan"

    @rx.event
    def load_page(self) -> None:
        self.fetch_logs()

    @rx.event
    def fetch_logs(self) -> None:
        res = query_audit_logs(
            filters={"search": self.search_query, "module": self.module_filter},
            page=self.page,
            page_size=self.page_size,
        )
        self.logs = res["items"]
        self.total_items = res["total"]

    @rx.event
    def set_search_query(self, val: str) -> None:
        self.search_query = val
        self.page = 1
        self.fetch_logs()

    @rx.event
    def set_module_filter(self, val: str) -> None:
        self.module_filter = val
        self.page = 1
        self.fetch_logs()

    @rx.event
    def reset_filters(self) -> None:
        self.search_query = ""
        self.module_filter = ""
        self.page = 1
        self.fetch_logs()

    @rx.event
    def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            self.fetch_logs()

    @rx.event
    def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            self.fetch_logs()

    @rx.event
    def select_page(self, token: str) -> None:
        if token.isdigit():
            self.page = int(token)
            self.fetch_logs()


__all__ = ["AuditState"]

