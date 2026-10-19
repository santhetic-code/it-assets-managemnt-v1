"""
State Assets Inventory ITAM Pro.
Mengelola filter, paginasi, pilih baris, detail drawer, dan dialog konfirmasi hapus.
"""
from collections.abc import AsyncGenerator
import math
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client

CATEGORY_OPTIONS: list[str] = ["PC", "Monitor", "Server", "UPS"]
STATUS_OPTIONS: list[str] = ["In Use", "Maintenance", "In Storage", "Disposed"]
LOCATION_OPTIONS: list[str] = [
    "HQ Lt. 2 · Operasional",
    "HQ Lt. 3 · Finance",
    "Data Center Lt. 4",
    "Cabang Bandung",
    "Gudang IT",
]


class AssetState(rx.State):
    # Data & Loading
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    is_loading: bool = False
    deleted_ids: list[str] = []

    # Filter State
    search_query: str = ""
    category_filter: str = "Semua"
    status_filter: str = "Semua"
    location_filter: str = "Semua"

    # Seleksi Baris & Drawer State
    selected_ids: list[str] = []
    active_asset_id: str = ""
    active_asset: dict[str, Any] = {}
    drawer_open: bool = False
    drawer_tab: str = "detail"

    # Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    asset_to_delete: str = ""

    @rx.var
    def total_pages(self) -> int:
        if self.total <= 0:
            return 1
        return max(1, math.ceil(self.total / self.page_size))

    @rx.var
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var
    def result_count_label(self) -> str:
        return f"{self.total} aset ditemukan"

    @rx.var
    def pagination_summary(self) -> str:
        if self.total == 0:
            return "Menampilkan 0 dari 0"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.page * self.page_size, self.total)
        return f"Menampilkan {start}–{end} dari {self.total}"

    @rx.var
    def page_tokens(self) -> list[str]:
        """Hitung nomor halaman beserta elipsis '...' untuk halaman jauh."""
        total_p = self.total_pages
        cur = self.page
        if total_p <= 7:
            return [str(i) for i in range(1, total_p + 1)]
        if cur <= 4:
            return ["1", "2", "3", "4", "5", "...", str(total_p)]
        if cur >= total_p - 3:
            return [
                "1",
                "...",
                str(total_p - 4),
                str(total_p - 3),
                str(total_p - 2),
                str(total_p - 1),
                str(total_p),
            ]
        return ["1", "...", str(cur - 1), str(cur), str(cur + 1), "...", str(total_p)]

    @rx.var
    def all_current_selected(self) -> bool:
        if not self.items:
            return False
        current_ids = [str(row["id"]) for row in self.items]
        return all(rid in self.selected_ids for rid in current_ids)

    @rx.var
    def active_code(self) -> str:
        return str(self.active_asset.get("id", ""))

    @rx.var
    def active_name(self) -> str:
        return str(self.active_asset.get("name", ""))

    @rx.var
    def active_category(self) -> str:
        return str(self.active_asset.get("category", ""))

    @rx.var
    def active_status(self) -> str:
        return str(self.active_asset.get("status", "In Use"))

    @rx.var
    def active_general_info(self) -> list[dict[str, str]]:
        return self.active_asset.get("general_info", [])

    @rx.var
    def active_specs_info(self) -> list[dict[str, str]]:
        return self.active_asset.get("specs_info", [])

    @rx.var
    def active_related_info(self) -> list[dict[str, str]]:
        return self.active_asset.get("related_info", [])

    @rx.var
    def active_history_info(self) -> list[dict[str, str]]:
        return self.active_asset.get("history_info", [])

    @rx.event
    async def load_assets(self) -> None:
        """Ambil daftar aset dari api_client sesuai filter & halaman aktif."""
        self.is_loading = True
        filters = {
            "search": self.search_query,
            "category": self.category_filter,
            "status": self.status_filter,
            "location": self.location_filter,
            "excluded_ids": self.deleted_ids,
        }
        response = await api_client.get_assets(
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        self.items = response.get("items", [])
        self.total = int(response.get("total", 0))
        self.is_loading = False

    @rx.event
    async def set_search_query(self, value: str) -> None:
        self.search_query = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def set_category_filter(self, value: str) -> None:
        self.category_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def set_status_filter(self, value: str) -> None:
        self.status_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def set_location_filter(self, value: str) -> None:
        self.location_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.category_filter = "Semua"
        self.status_filter = "Semua"
        self.location_filter = "Semua"
        self.page = 1
        await self.load_assets()

    @rx.event
    async def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self.load_assets()

    @rx.event
    async def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self.load_assets()

    @rx.event
    async def select_page(self, token: str) -> None:
        if token.isdigit():
            target = int(token)
            if 1 <= target <= self.total_pages and target != self.page:
                self.page = target
                await self.load_assets()

    @rx.event
    def toggle_select_all(self, checked: bool) -> None:
        current_ids = [str(row["id"]) for row in self.items]
        if checked:
            merged = list(set(self.selected_ids + current_ids))
            self.selected_ids = merged
        else:
            self.selected_ids = [rid for rid in self.selected_ids if rid not in current_ids]

    @rx.event
    def toggle_row_selection(self, row_id: str) -> None:
        if row_id in self.selected_ids:
            self.selected_ids = [rid for rid in self.selected_ids if rid != row_id]
        else:
            self.selected_ids = [*self.selected_ids, row_id]

    @rx.event
    def open_drawer(self, row_id: str) -> Any:
        for item in self.items:
            if item["id"] == row_id:
                self.active_asset = item
                self.active_asset_id = row_id
                self.drawer_tab = "detail"
                self.drawer_open = True
                return rx.set_focus("global-detail-drawer")

    @rx.event
    def close_drawer(self) -> Any:
        last_id = self.active_asset_id
        self.drawer_open = False
        self.active_asset_id = ""
        if last_id:
            return rx.set_focus(f"table-row-{last_id}")

    @rx.event
    def handle_drawer_key_down(self, key: str) -> Any:
        if key == "Escape":
            return self.close_drawer()

    @rx.event
    def set_drawer_tab(self, tab_key: str) -> None:
        self.drawer_tab = tab_key

    @rx.event
    def trigger_coming_soon(self, action_name: str) -> Any:
        return rx.toast.info(
            f"{action_name} — Segera hadir.",
            position="top-right",
        )

    @rx.event
    def edit_asset(self, row_id: str = "") -> Any:
        target = row_id or self.active_asset_id
        return rx.toast.info(
            f"Form Edit Aset ({target}) — Segera hadir.",
            position="top-right",
        )

    @rx.event
    def confirm_delete_asset(self, row_id: str = "") -> None:
        target = row_id or self.active_asset_id
        if target:
            self.asset_to_delete = target
            self.delete_dialog_open = True

    @rx.event
    def cancel_delete(self) -> None:
        self.delete_dialog_open = False
        self.asset_to_delete = ""

    @rx.event
    async def execute_delete_asset(self) -> AsyncGenerator[Any, None]:
        target = self.asset_to_delete
        self.delete_dialog_open = False
        self.asset_to_delete = ""
        if target:
            self.deleted_ids = [*self.deleted_ids, target]
            if self.active_asset_id == target:
                self.drawer_open = False
                self.active_asset_id = ""
            await self.load_assets()
            yield rx.toast.info(
                f"Hapus permanen aset {target} ke backend — Segera hadir (dihapus dari tampilan).",
                position="top-right",
            )
