"""
State Navigasi & Layout ITAM Pro.
Mengelola item menu aktif, breadcrumb, pencarian topbar, dan drawer sidebar mobile.
"""
from typing import Any

import reflex as rx


class NavState(rx.State):
    active_menu: str = "Dashboard"
    breadcrumb_group: str = "Overview"
    breadcrumb_page: str = "Dashboard"
    mobile_sidebar_open: bool = False
    global_search_query: str = ""

    @rx.event
    def set_global_search_query(self, value: str) -> None:
        self.global_search_query = value

    @rx.event
    def toggle_mobile_sidebar(self) -> None:
        self.mobile_sidebar_open = not self.mobile_sidebar_open

    @rx.event
    def close_mobile_sidebar(self) -> None:
        self.mobile_sidebar_open = False

    @rx.event
    def set_page_context(self, group: str, page: str) -> None:
        """Set grup dan halaman aktif pada breadcrumb dan sidebar."""
        self.breadcrumb_group = group
        self.breadcrumb_page = page
        self.active_menu = page
        self.mobile_sidebar_open = False

    @rx.event
    def select_menu(
        self,
        group: str,
        label: str,
        route: str,
        is_ready: bool = False,
    ) -> Any:
        """
        Handler klik item menu di sidebar.
        Jika halaman sudah siap (is_ready=True), arahkan ke route-nya.
        Jika belum dibuat, tampilkan info placeholder tanpa merusak halaman saat ini.
        """
        self.mobile_sidebar_open = False
        if is_ready:
            self.breadcrumb_group = group
            self.breadcrumb_page = label
            self.active_menu = label
            return rx.redirect(route)

        return rx.toast.info(
            f"Halaman '{label}' ({group}) akan segera tersedia pada tahap berikutnya.",
            position="top-right",
        )
