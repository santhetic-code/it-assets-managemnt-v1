"""
State Controller untuk Modul Credential Manager ITAM Pro (Tahap 12).
Mendukung filter tab dinamis, pencarian, detail drawer, dan timer reveal 30 detik.
"""
import asyncio
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.router_utils import get_current_params


class CredentialState(rx.State):
    active_tab: str = "Semua"
    search_query: str = ""

    credentials: list[dict[str, Any]] = []
    total_items: int = 0
    page: int = 1
    page_size: int = 10

    tab_counts: dict[str, int] = {
        "Semua": 0,
        "Website & Aplikasi": 0,
        "Perangkat": 0,
        "Akun Online": 0,
    }

    # Detail Drawer / Modal
    is_detail_open: bool = False
    selected_crd: dict[str, Any] = {}

    # Secret Reveal State
    revealed_value: str = ""
    revealed_field: str = ""
    revealed_crd_id: str = ""
    reveal_countdown: int = 0

    # Kompatibilitas modal verifikasi PIN
    is_reveal_modal_open: bool = False
    reveal_target_id: str = ""
    reveal_pin: str = ""
    revealed_password: str = ""

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
    def summary(self) -> dict[str, Any]:
        """Ringkasan metrik untuk KPI cards."""
        return {
            "total_kredensial": self.total_items,
            "diperbarui_bulan_ini": self.tab_counts.get("Semua", self.total_items),
        }

    @rx.event
    def select_page(self, page_str: str):
        try:
            self.page = int(page_str)
            return self.fetch_data()
        except ValueError:
            pass

    @rx.event
    async def load_page(self):
        """Inisialisasi halaman dari parameter URL."""
        params = get_current_params(self.router)
        tab = params.get("tab")
        if not tab:
            tab = "Semua"
        self.active_tab = tab
        await self.fetch_data()

    @rx.event
    async def fetch_data(self):
        """Ambil data kredensial dari backend / mock."""
        filters = {"search": self.search_query, "tab": self.active_tab}
        res = await api_client.get_credentials(
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        self.credentials = res.get("items", [])
        self.total_items = res.get("total", 0)
        self.tab_counts = res.get("tab_counts", {})

    @rx.event
    def set_tab(self, tab: str):
        """Ganti tab aktif."""
        self.active_tab = tab
        self.page = 1
        return rx.redirect(f"/security/credentials?tab={tab}")

    @rx.event
    def set_search(self, query: str):
        """Pencarian teks kredensial."""
        self.search_query = query
        self.page = 1
        return self.fetch_data()

    @rx.event
    def open_detail(self, item: dict[str, Any]):
        """Buka drawer/modal detail satu kredensial."""
        self.selected_crd = item
        self.hide_revealed()
        self.is_detail_open = True

    @rx.event
    def close_detail(self):
        """Tutup drawer/modal detail."""
        self.is_detail_open = False
        self.hide_revealed()

    @rx.event
    def hide_revealed(self):
        """Sembunyikan secret yang sedang dibuka."""
        self.revealed_value = ""
        self.revealed_field = ""
        self.revealed_crd_id = ""
        self.reveal_countdown = 0
        self.revealed_password = ""

    @rx.event(background=True)
    async def fetch_and_reveal(self, crd_id: str, field_key: str):
        """Buka rahasia kredensial dan mulai countdown 30 detik."""
        res = await api_client.reveal_credential(crd_id, field_key, "Admin IT")
        secret_val = res.get("value", "")

        async with self:
            self.revealed_value = secret_val
            self.revealed_field = field_key
            self.revealed_crd_id = crd_id
            self.reveal_countdown = 30
            if field_key == "secret":
                self.revealed_password = secret_val

        # Countdown 30 detik
        for remaining in range(29, -1, -1):
            await asyncio.sleep(1)
            async with self:
                # Batalkan jika user membuka target lain atau menutup reveal
                if self.revealed_crd_id != crd_id or self.revealed_field != field_key:
                    return
                self.reveal_countdown = remaining
                if remaining == 0:
                    self.revealed_value = ""
                    self.revealed_field = ""
                    self.revealed_crd_id = ""
                    self.revealed_password = ""

    @rx.event(background=True)
    async def copy_secret(self, crd_id: str, field_key: str):
        """Salin nilai rahasia ke clipboard dan catat log audit."""
        res = await api_client.reveal_credential(crd_id, f"{field_key}_copy", "Admin IT")
        val = res.get("value", "")
        if val:
            yield rx.set_clipboard(val)
            yield rx.toast.success("Kredensial berhasil disalin ke clipboard!")

    # --- Dukungan kompatibilitas ---
    @rx.event
    def open_reveal_modal(self, crd_id: str):
        self.reveal_target_id = crd_id
        self.reveal_pin = ""
        self.revealed_password = ""
        self.is_reveal_modal_open = True

    @rx.event
    def close_reveal_modal(self):
        self.is_reveal_modal_open = False
        self.revealed_password = ""
        self.hide_revealed()

    @rx.event
    def set_reveal_pin(self, val: str):
        self.reveal_pin = val

    @rx.event
    def submit_reveal_pin(self):
        """Simulasi verifikasi PIN untuk melihat password."""
        return self.fetch_and_reveal(self.reveal_target_id, "secret")

    @rx.event
    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            return self.fetch_data()

    @rx.event
    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            return self.fetch_data()


__all__ = ["CredentialState"]
