"""
State Rekap Monitor ITAM Pro.
Mengelola tab (Semua, Digunakan, Backup), 4 dropdown filter, pengurutan kolom,
drawer 4 grup (Identitas, Layar, Konektivitas, Status), dan form tambah/edit/duplikat.
"""
from collections.abc import AsyncGenerator
import math
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.mock.master_data import (
    MASTER_KONEKTIVITAS_MONITOR,
    MASTER_MERK_MONITOR,
    MASTER_RESOLUSI_MONITOR,
    MASTER_STATUS_MONITOR,
    MASTER_UKURAN_MONITOR,
)
from itam_pro.services.mock.monitor_mock import (
    format_inch_label,
    get_next_monitor_id,
    is_monitor_id_taken,
    parse_inch_number,
)


class MonitorState(rx.State):
    # Opsi Master dari master_data.py (merk & resolusi dapat bertambah saat input baru)
    master_merk_options: list[str] = list(MASTER_MERK_MONITOR)
    master_ukuran_options: list[str] = list(MASTER_UKURAN_MONITOR)
    master_resolusi_options: list[str] = list(MASTER_RESOLUSI_MONITOR)
    master_konektivitas_options: list[str] = list(MASTER_KONEKTIVITAS_MONITOR)
    master_status_options: list[str] = list(MASTER_STATUS_MONITOR)

    # Tab Aktif & Jumlah Unit per Tab
    active_status_tab: str = "Semua"
    count_semua: int = 24
    count_digunakan: int = 19
    count_backup: int = 5

    # Data Tabel & Paginasi (8 baris per halaman sesuai artboard)
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 8
    is_loading: bool = False

    # Filter & Sorting State
    search_query: str = ""
    merk_filter: str = "Semua"
    ukuran_filter: str = "Semua"
    resolusi_filter: str = "Semua"
    konektivitas_filter: str = "Semua"
    sort_by: str = "id_aset"
    sort_dir: str = "asc"

    # Seleksi Baris & Detail Drawer
    selected_ids: list[str] = []
    active_monitor_id: str = ""
    active_monitor: dict[str, Any] = {}
    drawer_open: bool = False
    drawer_tab: str = "detail"

    # State Modal Form Tambah / Edit / Duplikat
    form_modal_open: bool = False
    form_mode: str = "add"  # "add" atau "edit"
    form_original_id: str = ""
    form_id_aset: str = ""
    form_merk: str = ""
    form_tipe_model: str = ""
    form_ukuran_layar: str = "24"
    form_resolusi_layar: str = "1920 × 1080"
    form_konektivitas: list[str] = ["HDMI", "VGA"]
    form_status: str = MASTER_STATUS_MONITOR[0]
    form_catatan: str = ""
    form_error: str = ""

    # State Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    monitor_to_delete: str = ""
    monitor_to_delete_label: str = ""

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
        return f"{self.total} unit"

    @rx.var
    def pagination_summary(self) -> str:
        if self.total == 0:
            return "Menampilkan 0 dari 0 unit"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.page * self.page_size, self.total)
        return f"Menampilkan {start}–{end} dari {self.total} unit"

    @rx.var
    def page_tokens(self) -> list[str]:
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
        current_ids = [str(row["id_aset"]) for row in self.items]
        return all(rid in self.selected_ids for rid in current_ids)

    @rx.var
    def has_active_filter(self) -> bool:
        return bool(
            self.search_query.strip()
            or self.merk_filter != "Semua"
            or self.ukuran_filter != "Semua"
            or self.resolusi_filter != "Semua"
            or self.konektivitas_filter != "Semua"
        )

    @rx.var
    def empty_state_title(self) -> str:
        if self.has_active_filter:
            return "Tidak ada monitor yang cocok"
        return "Belum ada monitor"

    @rx.var
    def empty_state_subtitle(self) -> str:
        if self.has_active_filter:
            return "Coba ubah kata kunci pencarian atau atur ulang kriteria filter Anda."
        return "Tambahkan data unit monitor pertama Anda beserta ukuran dan konektivitasnya."

    @rx.var
    def empty_state_action_label(self) -> str:
        if self.has_active_filter:
            return "Reset filter"
        return "+ Tambah Monitor"

    # Computed Vars untuk Detail Drawer "Rincian Monitor"
    @rx.var
    def active_code(self) -> str:
        return str(self.active_monitor.get("id_aset", ""))

    @rx.var
    def active_title(self) -> str:
        merk = str(self.active_monitor.get("merk", ""))
        tipe = str(self.active_monitor.get("tipe_model", ""))
        return f"{merk} {tipe}".strip()

    @rx.var
    def active_status(self) -> str:
        return str(self.active_monitor.get("status", "Digunakan"))

    @rx.var
    def active_identity_info(self) -> list[dict[str, str]]:
        return self.active_monitor.get("identity_info", [])

    @rx.var
    def active_screen_info(self) -> list[dict[str, str]]:
        return self.active_monitor.get("screen_info", [])

    @rx.var
    def active_konektivitas_chips(self) -> list[str]:
        return self.active_monitor.get("konektivitas", [])

    @rx.var
    def active_status_info(self) -> list[dict[str, str]]:
        return self.active_monitor.get("status_info", [])

    @rx.var
    def active_history_info(self) -> list[dict[str, str]]:
        return self.active_monitor.get("history_info", [])

    @rx.event
    async def load_monitors(self) -> None:
        """Muat daftar monitor dari api_client sesuai tab, filter, sort, dan halaman."""
        self.is_loading = True
        filters = {
            "search": self.search_query,
            "merk": self.merk_filter,
            "ukuran_layar": self.ukuran_filter,
            "resolusi_layar": self.resolusi_filter,
            "konektivitas": self.konektivitas_filter,
            "sort_by": self.sort_by,
            "sort_dir": self.sort_dir,
        }
        response = await api_client.get_monitors(
            status=self.active_status_tab,
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        self.items = response.get("items", [])
        self.total = int(response.get("total", 0))
        counts = response.get("counts_by_status", {})
        self.count_semua = int(counts.get("Semua", 0))
        self.count_digunakan = int(counts.get("Digunakan", 0))
        self.count_backup = int(counts.get("Backup", 0))
        self.is_loading = False

    # Tab, Filter & Sort Handlers
    @rx.event
    async def set_status_tab(self, tab_key: str) -> None:
        self.active_status_tab = tab_key
        self.page = 1
        self.selected_ids = []
        await self.load_monitors()

    @rx.event
    async def set_search_query(self, value: str) -> None:
        self.search_query = value
        self.page = 1
        await self.load_monitors()

    @rx.event
    async def set_merk_filter(self, value: str) -> None:
        self.merk_filter = value
        self.page = 1
        await self.load_monitors()

    @rx.event
    async def set_ukuran_filter(self, value: str) -> None:
        self.ukuran_filter = value
        self.page = 1
        await self.load_monitors()

    @rx.event
    async def set_resolusi_filter(self, value: str) -> None:
        self.resolusi_filter = value
        self.page = 1
        await self.load_monitors()

    @rx.event
    async def set_konektivitas_filter(self, value: str) -> None:
        self.konektivitas_filter = value
        self.page = 1
        await self.load_monitors()

    @rx.event
    async def toggle_sort(self, col_key: str) -> None:
        """Urutkan kolom ID Aset, Merk, atau Ukuran Layar (asc <-> desc)."""
        if self.sort_by == col_key:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_by = col_key
            self.sort_dir = "asc"
        self.page = 1
        await self.load_monitors()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.merk_filter = "Semua"
        self.ukuran_filter = "Semua"
        self.resolusi_filter = "Semua"
        self.konektivitas_filter = "Semua"
        self.sort_by = "id_aset"
        self.sort_dir = "asc"
        self.page = 1
        await self.load_monitors()

    @rx.event
    async def handle_empty_state_action(self) -> None:
        if self.has_active_filter:
            await self.reset_filters()
        else:
            self.open_add_modal()

    # Pagination Handlers
    @rx.event
    async def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self.load_monitors()

    @rx.event
    async def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self.load_monitors()

    @rx.event
    async def select_page(self, token: str) -> None:
        if token.isdigit():
            target = int(token)
            if 1 <= target <= self.total_pages and target != self.page:
                self.page = target
                await self.load_monitors()

    # Row Selection & Drawer Handlers
    @rx.event
    def toggle_select_all(self, checked: bool) -> None:
        current_ids = [str(row["id_aset"]) for row in self.items]
        if checked:
            self.selected_ids = list(set(self.selected_ids + current_ids))
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
            if item["id_aset"] == row_id:
                self.active_monitor = item
                self.active_monitor_id = row_id
                self.drawer_tab = "detail"
                self.drawer_open = True
                return rx.set_focus("global-detail-drawer")

    @rx.event
    def close_drawer(self) -> Any:
        last_id = self.active_monitor_id
        self.drawer_open = False
        self.active_monitor_id = ""
        if last_id:
            return rx.set_focus(f"table-row-{last_id}")

    @rx.event
    def set_drawer_tab(self, tab_key: str) -> None:
        self.drawer_tab = tab_key

    # Form Setters & Checkbox Group Handler
    @rx.event
    def set_form_id_aset(self, value: str) -> None:
        self.form_id_aset = value
        self.form_error = ""

    @rx.event
    def set_form_merk(self, value: str) -> None:
        self.form_merk = value
        self.form_error = ""

    @rx.event
    def set_form_tipe_model(self, value: str) -> None:
        self.form_tipe_model = value
        self.form_error = ""

    @rx.event
    def set_form_ukuran_layar(self, value: str) -> None:
        self.form_ukuran_layar = value
        self.form_error = ""

    @rx.event
    def set_form_resolusi_layar(self, value: str) -> None:
        self.form_resolusi_layar = value
        self.form_error = ""

    @rx.event
    def toggle_form_konektivitas(self, port: str) -> None:
        """Toggle pilihan konektor pada checkbox group."""
        if port in self.form_konektivitas:
            self.form_konektivitas = [p for p in self.form_konektivitas if p != port]
        else:
            # Urutkan sesuai urutan master konektivitas
            updated = [*self.form_konektivitas, port]
            self.form_konektivitas = [
                p for p in self.master_konektivitas_options if p in updated
            ]
        self.form_error = ""

    @rx.event
    def set_form_status(self, value: str) -> None:
        self.form_status = value

    @rx.event
    def set_form_catatan(self, value: str) -> None:
        self.form_catatan = value

    def _reset_form_fields(self) -> None:
        self.form_original_id = ""
        self.form_id_aset = get_next_monitor_id()
        self.form_merk = self.master_merk_options[0] if self.master_merk_options else "LG"
        self.form_tipe_model = ""
        self.form_ukuran_layar = "24"
        self.form_resolusi_layar = "1920 × 1080"
        self.form_konektivitas = ["HDMI", "VGA"]
        self.form_status = (
            self.active_status_tab
            if self.active_status_tab in self.master_status_options
            else self.master_status_options[0]
        )
        self.form_catatan = ""
        self.form_error = ""

    @rx.event
    def open_add_modal(self) -> None:
        self._reset_form_fields()
        self.form_mode = "add"
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str) -> None:
        target_id = row_id or self.active_monitor_id
        target_item = next((it for it in self.items if it["id_aset"] == target_id), None)
        if not target_item and self.active_monitor.get("id_aset") == target_id:
            target_item = self.active_monitor
        if not target_item:
            return

        self.form_mode = "edit"
        self.form_original_id = target_id
        self.form_id_aset = str(target_item.get("id_aset", target_id))
        self.form_merk = str(target_item.get("merk", ""))
        self.form_tipe_model = str(target_item.get("tipe_model", ""))
        self.form_ukuran_layar = str(target_item.get("ukuran_raw", "24"))
        self.form_resolusi_layar = str(target_item.get("resolusi_layar", "1920 × 1080"))
        self.form_konektivitas = list(target_item.get("konektivitas", ["HDMI"]))
        self.form_status = str(target_item.get("status", "Digunakan"))
        self.form_catatan = str(target_item.get("catatan_raw", ""))
        self.form_error = ""
        self.form_modal_open = True

    @rx.event
    def open_duplicate_modal(self, row_id: str) -> None:
        """Salin spesifikasi monitor ke mode Tambah dengan ID Aset baru otomatis."""
        self.open_edit_modal(row_id)
        self.form_mode = "add"
        self.form_original_id = ""
        self.form_id_aset = get_next_monitor_id()
        self.form_modal_open = True

    @rx.event
    def duplicate_current_form(self) -> None:
        """Ubah form edit yang sedang dibuka menjadi mode Tambah dengan ID baru."""
        self.form_mode = "add"
        self.form_original_id = ""
        self.form_id_aset = get_next_monitor_id()
        self.form_error = ""

    @rx.event
    def close_form_modal(self) -> None:
        self.form_modal_open = False
        self.form_error = ""

    def _validate_form(self) -> bool:
        id_val = self.form_id_aset.strip().upper()
        if not id_val:
            self.form_error = "ID Aset wajib diisi (contoh: MON-0025)."
            return False

        exclude_id = self.form_original_id if self.form_mode == "edit" else ""
        if is_monitor_id_taken(id_val, exclude_id=exclude_id):
            self.form_error = "ID aset sudah dipakai"
            return False

        if not self.form_merk.strip():
            self.form_error = "Merk monitor wajib diisi."
            return False

        if not self.form_tipe_model.strip():
            self.form_error = "Tipe / Model monitor wajib diisi."
            return False

        inch_num = parse_inch_number(self.form_ukuran_layar)
        if inch_num <= 0 or inch_num > 100:
            self.form_error = (
                "Ukuran layar harus berupa angka inci yang valid (contoh: 24 atau 21,5)."
            )
            return False

        if not self.form_resolusi_layar.strip():
            self.form_error = "Resolusi layar wajib diisi (contoh: 1920 × 1080)."
            return False

        if not self.form_konektivitas:
            self.form_error = "Pilih minimal 1 konektivitas monitor."
            return False

        self.form_error = ""
        return True

    def _sync_dynamic_masters(self, merk: str, ukuran_label: str, resolusi: str) -> None:
        """Jika user mengetik Merk, Ukuran, atau Resolusi baru di combobox, tambahkan ke master."""
        if merk not in self.master_merk_options:
            self.master_merk_options = [*self.master_merk_options, merk]
        if ukuran_label not in self.master_ukuran_options:
            self.master_ukuran_options = [*self.master_ukuran_options, ukuran_label]
        if resolusi not in self.master_resolusi_options:
            self.master_resolusi_options = [*self.master_resolusi_options, resolusi]

    def _build_payload(self) -> dict[str, Any]:
        merk_clean = self.form_merk.strip()
        ukuran_label = format_inch_label(self.form_ukuran_layar)
        resolusi_clean = (
            self.form_resolusi_layar.strip().replace("x", "×").replace("X", "×")
        )
        self._sync_dynamic_masters(merk_clean, ukuran_label, resolusi_clean)
        return {
            "id_aset": self.form_id_aset.strip().upper(),
            "merk": merk_clean,
            "tipe_model": self.form_tipe_model.strip(),
            "ukuran_layar": self.form_ukuran_layar.strip(),
            "resolusi_layar": resolusi_clean,
            "konektivitas": list(self.form_konektivitas),
            "status": self.form_status,
            "catatan": self.form_catatan.strip(),
        }

    @rx.event
    async def save_monitor_form(self) -> AsyncGenerator[Any, None]:
        """Simpan monitor (Tambah / Edit) lalu tutup modal."""
        if not self._validate_form():
            return

        payload = self._build_payload()
        if self.form_mode == "edit" and self.form_original_id:
            updated = await api_client.update_monitor(self.form_original_id, payload)
            self.form_modal_open = False
            await self.load_monitors()
            if updated and self.active_monitor_id == self.form_original_id:
                self.active_monitor = updated
                self.active_monitor_id = updated["id_aset"]
            yield rx.toast.success(
                f"Data monitor {payload['id_aset']} berhasil diperbarui.",
                position="top-right",
            )
            return

        created = await api_client.create_monitor(payload)
        self.form_modal_open = False
        self.page = 1
        await self.load_monitors()
        yield rx.toast.success(
            f"Monitor {created['id_aset']} ({created['merk']} "
            f"{created['tipe_model']}) ditambahkan.",
            position="top-right",
        )

    @rx.event
    async def save_and_add_another(self) -> AsyncGenerator[Any, None]:
        """Simpan monitor baru lalu siapkan ID Aset berikutnya dengan mempertahankan spesifikasi."""
        if not self._validate_form():
            return

        payload = self._build_payload()
        created = await api_client.create_monitor(payload)
        self.page = 1
        await self.load_monitors()

        self.form_id_aset = get_next_monitor_id()
        self.form_catatan = ""
        self.form_error = ""
        yield rx.toast.success(
            f"Monitor {created['id_aset']} disimpan. Siap menambah unit berikutnya.",
            position="top-right",
        )

    # Delete Confirmation Handlers
    @rx.event
    def confirm_delete_monitor(self, row_id: str) -> None:
        target = row_id or self.active_monitor_id
        if target:
            item = next((it for it in self.items if it["id_aset"] == target), self.active_monitor)
            merk = item.get("merk", "")
            tipe = item.get("tipe_model", "")
            self.monitor_to_delete = target
            self.monitor_to_delete_label = f"{merk} {tipe}".strip() or target
            self.delete_dialog_open = True

    @rx.event
    def cancel_delete(self) -> None:
        self.delete_dialog_open = False
        self.monitor_to_delete = ""
        self.monitor_to_delete_label = ""

    @rx.event
    async def execute_delete_monitor(self) -> AsyncGenerator[Any, None]:
        target = self.monitor_to_delete
        label = self.monitor_to_delete_label
        self.delete_dialog_open = False
        self.monitor_to_delete = ""
        self.monitor_to_delete_label = ""
        if target:
            await api_client.delete_monitor(target)
            if self.active_monitor_id == target:
                self.drawer_open = False
                self.active_monitor_id = ""
            await self.load_monitors()
            yield rx.toast.success(
                f"Monitor {target} ({label}) telah dihapus.",
                position="top-right",
            )

    @rx.event
    def trigger_coming_soon(self, action_name: str) -> Any:
        return rx.toast.info(
            f"{action_name} — Segera hadir.",
            position="top-right",
        )


__all__ = ["MonitorState"]
