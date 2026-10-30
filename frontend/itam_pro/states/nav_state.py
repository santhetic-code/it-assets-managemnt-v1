"""
State Navigasi & Layout Responsif ITAM Pro.
Memastikan item sidebar hanya menyorot route yang benar-benar aktif.
"""
from typing import Any

import reflex as rx

from itam_pro.services.router_utils import get_current_raw_path


class NavState(rx.State):
    """State untuk drawer navigasi mobile dan deteksi path aktif."""

    mobile_drawer_open: bool = False
    mobile_sidebar_open: bool = False
    active_menu: str = "Dashboard"
    breadcrumb_group: str = "Overview"
    breadcrumb_page: str = "Dashboard"
    global_search_query: str = ""

    @rx.var
    def active_path(self) -> str:
        """Kembalikan path URL aktual tanpa query string atau trailing slash."""
        raw = get_current_raw_path(self.router).strip()
        if not raw:
            raw = str(getattr(self.router.page, "path", "/dashboard") or "/dashboard").strip()
        clean = raw.split("?", 1)[0].split("#", 1)[0].rstrip("/")
        return clean if clean else "/dashboard"

    @rx.event
    def toggle_mobile_drawer(self) -> None:
        self.mobile_drawer_open = not self.mobile_drawer_open
        self.mobile_sidebar_open = self.mobile_drawer_open

    @rx.event
    def close_mobile_drawer(self) -> None:
        self.mobile_drawer_open = False
        self.mobile_sidebar_open = False

    @rx.event
    def toggle_mobile_sidebar(self) -> None:
        self.toggle_mobile_drawer()

    @rx.event
    def close_mobile_sidebar(self) -> None:
        self.close_mobile_drawer()

    @rx.event
    def set_global_search_query(self, value: str) -> None:
        self.global_search_query = value

    @rx.event
    def set_page_context(self, group: str, page: str) -> None:
        self.breadcrumb_group = group
        self.breadcrumb_page = page
        self.active_menu = page
        self.close_mobile_drawer()

    @rx.event
    def select_menu(
        self,
        group: str,
        label: str,
        route: str,
        is_ready: bool,
    ) -> Any:
        self.close_mobile_drawer()
        if is_ready:
            self.breadcrumb_group = group
            self.breadcrumb_page = label
            self.active_menu = label
            return rx.redirect(route)

        return rx.toast.info(
            f"Halaman '{label}' ({group}) akan segera tersedia pada tahap berikutnya.",
            position="top-right",
        )


__all__ = ["NavState"]
