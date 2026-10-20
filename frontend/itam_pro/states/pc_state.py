"""
State Daftar PC ITAM Pro.
Mengelola tab jenis PC (Operasional, Server, Backup), pencarian, paginasi,
drawer 3 grup (Identitas, Perangkat keras, Periferal), serta form tambah/edit/duplikat.
"""
from collections.abc import AsyncGenerator
import math
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.mock.master_data import MASTER_JENIS_PC


class PCState(rx.State):
    # Opsi Master Jenis PC
    master_jenis_options: list[str] = list(MASTER_JENIS_PC)

    # Tab Aktif & Jumlah Unit per Tab
    active_jenis_tab: str = MASTER_JENIS_PC[0]
    count_operasional: int = 0
    count_server: int = 0
    count_backup: int = 0

    # Data Tabel & Paginasi
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    is_loading: bool = False

    # Pencarian Filter Bar
    search_query: str = ""

    # Seleksi Baris & Detail Drawer
    selected_ids: list[str] = []
    active_pc_id: str = ""
    active_pc: dict[str, Any] = {}
    drawer_open: bool = False
    drawer_tab: str = "detail"

    # State Modal Form Tambah / Edit / Duplikat
    form_modal_open: bool = False
    form_mode: str = "add"  # "add" atau "edit"
    form_editing_id: str = ""
    form_jenis: str = MASTER_JENIS_PC[0]
    form_nama_pc: str = ""
    form_user: str = ""
    form_operasi_system: str = ""
    form_ram: str = ""
    form_vga: str = ""
    form_cpu: str = ""
    form_mainboard: str = ""
    form_hdd_ssd: str = ""
    form_monitor: str = ""
    form_keyboard: str = ""
    form_mouse: str = ""
    form_catatan: str = ""
    form_error: str = ""

    # State Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    pc_to_delete: str = ""
    pc_to_delete_name: str = ""

    @rx.var
    def user_column_header(self) -> str:
        """Label kolom USER menjadi 'User / Fungsi' di tab Server dan Backup."""
        if self.active_jenis_tab in ("Server", "Backup"):
            return "User / Fungsi"
        return "User"

    @rx.var
    def form_user_label(self) -> str:
        """Label field user di dalam form modal."""
        if self.form_jenis in ("Server", "Backup"):
            return "User / Fungsi (Opsional, mis. Server Database)"
        return "User / Pengguna (Opsional)"

    @rx.var
    def empty_state_title(self) -> str:
        """Judul empty state per tab."""
        if self.search_query.strip():
            return "Tidak ada PC yang cocok"
        return f"Belum ada PC {self.active_jenis_tab}"

    @rx.var
    def empty_state_subtitle(self) -> str:
        if self.search_query.strip():
            return "Coba ubah kata kunci pencarian hostname, user, CPU, atau mainboard."
        return f"Tambahkan spesifikasi unit PC {self.active_jenis_tab} pertama Anda."

    @rx.var
    def empty_state_action_label(self) -> str:
        if self.search_query.strip():
            return "Reset filter"
        return "+ Tambah PC"

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
        return f"{self.total} unit {self.active_jenis_tab}"

    @rx.var
    def pagination_summary(self) -> str:
        if self.total == 0:
            return "Menampilkan 0 dari 0"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.page * self.page_size, self.total)
        return f"Menampilkan {start}–{end} dari {self.total}"

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
        current_ids = [str(row["id"]) for row in self.items]
        return all(rid in self.selected_ids for rid in current_ids)

    # Computed Vars untuk Detail Drawer Rincian PC (3 Grup)
    @rx.var
    def active_code(self) -> str:
        return str(self.active_pc.get("id", ""))

    @rx.var
    def active_hostname(self) -> str:
        return str(self.active_pc.get("nama_pc", ""))

    @rx.var
    def active_jenis(self) -> str:
        return str(self.active_pc.get("jenis", "Operasional"))

    @rx.var
    def active_identity_info(self) -> list[dict[str, str]]:
        return self.active_pc.get("identity_info", [])

    @rx.var
    def active_hardware_info(self) -> list[dict[str, str]]:
        return self.active_pc.get("hardware_info", [])

    @rx.var
    def active_peripheral_info(self) -> list[dict[str, str]]:
        return self.active_pc.get("peripheral_info", [])

    @rx.var
    def active_history_info(self) -> list[dict[str, str]]:
        return self.active_pc.get("history_info", [])

    @rx.event
    async def load_pcs(self) -> None:
        """Muat daftar PC sesuai tab jenis aktif, kata kunci pencarian, dan halaman."""
        self.is_loading = True
        response = await api_client.get_pcs(
            jenis=self.active_jenis_tab,
            filters={"search": self.search_query},
            page=self.page,
            page_size=self.page_size,
        )
        self.items = response.get("items", [])
        self.total = int(response.get("total", 0))
        counts = response.get("counts_by_jenis", {})
        self.count_operasional = int(counts.get("Operasional", 0))
        self.count_server = int(counts.get("Server", 0))
        self.count_backup = int(counts.get("Backup", 0))
        self.is_loading = False

    @rx.event
    async def set_jenis_tab(self, jenis: str) -> None:
        """Ganti tab jenis aktif dan muat ulang tabel."""
        self.active_jenis_tab = jenis
        self.page = 1
        self.selected_ids = []
        await self.load_pcs()

    @rx.event
    async def set_search_query(self, value: str) -> None:
        self.search_query = value
        self.page = 1
        await self.load_pcs()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.page = 1
        await self.load_pcs()

    @rx.event
    async def handle_empty_state_action(self) -> None:
        """Jika sedang mencari -> reset filter; jika tab memang kosong -> buka modal tambah."""
        if self.search_query.strip():
            await self.reset_filters()
        else:
            self.open_add_modal()

    @rx.event
    async def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self.load_pcs()

    @rx.event
    async def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self.load_pcs()

    @rx.event
    async def select_page(self, token: str) -> None:
        if token.isdigit():
            target = int(token)
            if 1 <= target <= self.total_pages and target != self.page:
                self.page = target
                await self.load_pcs()

    @rx.event
    def toggle_select_all(self, checked: bool) -> None:
        current_ids = [str(row["id"]) for row in self.items]
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
            if item["id"] == row_id:
                self.active_pc = item
                self.active_pc_id = row_id
                self.drawer_tab = "detail"
                self.drawer_open = True
                return rx.set_focus("global-detail-drawer")

    @rx.event
    def close_drawer(self) -> Any:
        last_id = self.active_pc_id
        self.drawer_open = False
        self.active_pc_id = ""
        if last_id:
            return rx.set_focus(f"table-row-{last_id}")

    @rx.event
    def set_drawer_tab(self, tab_key: str) -> None:
        self.drawer_tab = tab_key

    # Form Setters
    @rx.event
    def set_form_jenis(self, value: str) -> None:
        self.form_jenis = value

    @rx.event
    def set_form_nama_pc(self, value: str) -> None:
        self.form_nama_pc = value
        self.form_error = ""

    @rx.event
    def set_form_user(self, value: str) -> None:
        self.form_user = value

    @rx.event
    def set_form_operasi_system(self, value: str) -> None:
        self.form_operasi_system = value

    @rx.event
    def set_form_ram(self, value: str) -> None:
        self.form_ram = value

    @rx.event
    def set_form_vga(self, value: str) -> None:
        self.form_vga = value

    @rx.event
    def set_form_cpu(self, value: str) -> None:
        self.form_cpu = value

    @rx.event
    def set_form_mainboard(self, value: str) -> None:
        self.form_mainboard = value

    @rx.event
    def set_form_hdd_ssd(self, value: str) -> None:
        self.form_hdd_ssd = value

    @rx.event
    def set_form_monitor(self, value: str) -> None:
        self.form_monitor = value

    @rx.event
    def set_form_keyboard(self, value: str) -> None:
        self.form_keyboard = value

    @rx.event
    def set_form_mouse(self, value: str) -> None:
        self.form_mouse = value

    @rx.event
    def set_form_catatan(self, value: str) -> None:
        self.form_catatan = value

    def _reset_form_fields(self) -> None:
        """Reset semua field form; jenis diisi otomatis dari tab yang sedang aktif."""
        self.form_editing_id = ""
        self.form_jenis = self.active_jenis_tab
        self.form_nama_pc = ""
        self.form_user = ""
        self.form_operasi_system = ""
        self.form_ram = ""
        self.form_vga = ""
        self.form_cpu = ""
        self.form_mainboard = ""
        self.form_hdd_ssd = ""
        self.form_monitor = ""
        self.form_keyboard = ""
        self.form_mouse = ""
        self.form_catatan = ""
        self.form_error = ""

    @rx.event
    def open_add_modal(self) -> None:
        """Buka modal tambah PC dengan jenis otomatis mengikuti tab aktif."""
        self._reset_form_fields()
        self.form_mode = "add"
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str) -> None:
        """Buka modal edit PC."""
        target_id = row_id or self.active_pc_id
        target_item = next((it for it in self.items if it["id"] == target_id), None)
        if not target_item and self.active_pc.get("id") == target_id:
            target_item = self.active_pc
        if not target_item:
            return

        self.form_mode = "edit"
        self.form_editing_id = target_id
        self.form_jenis = str(target_item.get("jenis", self.active_jenis_tab))
        self.form_nama_pc = str(target_item.get("nama_pc", ""))
        self.form_user = str(target_item.get("user_raw", ""))
        self.form_operasi_system = str(target_item.get("operasi_system_raw", ""))
        self.form_ram = str(target_item.get("ram_raw", ""))
        self.form_vga = str(target_item.get("vga_raw", ""))
        self.form_cpu = str(target_item.get("cpu_raw", ""))
        self.form_mainboard = str(target_item.get("mainboard_raw", ""))
        self.form_hdd_ssd = str(target_item.get("hdd_ssd_raw", ""))
        self.form_monitor = str(target_item.get("monitor_raw", ""))
        self.form_keyboard = str(target_item.get("keyboard_raw", ""))
        self.form_mouse = str(target_item.get("mouse_raw", ""))
        self.form_catatan = str(target_item.get("catatan_raw", ""))
        self.form_error = ""
        self.form_modal_open = True

    @rx.event
    def open_duplicate_modal(self, row_id: str) -> None:
        """Salin spesifikasi PC ke mode Tambah untuk membuat duplikat."""
        self.open_edit_modal(row_id)
        self.form_mode = "add"
        self.form_editing_id = ""
        if self.form_nama_pc:
            self.form_nama_pc = f"{self.form_nama_pc}-COPY"
        self.form_modal_open = True

    @rx.event
    def duplicate_current_form(self) -> None:
        """Ubah form yang sedang dibuka menjadi duplikat baru."""
        self.form_mode = "add"
        self.form_editing_id = ""
        if self.form_nama_pc and not self.form_nama_pc.endswith("-COPY"):
            self.form_nama_pc = f"{self.form_nama_pc}-COPY"

    @rx.event
    def close_form_modal(self) -> None:
        self.form_modal_open = False
        self.form_error = ""

    def _validate_form(self) -> bool:
        if not self.form_nama_pc.strip():
            self.form_error = "Nama PC / Hostname wajib diisi."
            return False
        self.form_error = ""
        return True

    def _build_payload(self) -> dict[str, Any]:
        return {
            "jenis": self.form_jenis,
            "nama_pc": self.form_nama_pc.strip(),
            "user": self.form_user.strip(),
            "operasi_system": self.form_operasi_system.strip(),
            "ram": self.form_ram.strip(),
            "vga": self.form_vga.strip(),
            "cpu": self.form_cpu.strip(),
            "mainboard": self.form_mainboard.strip(),
            "hdd_ssd": self.form_hdd_ssd.strip(),
            "monitor": self.form_monitor.strip(),
            "keyboard": self.form_keyboard.strip(),
            "mouse": self.form_mouse.strip(),
            "catatan": self.form_catatan.strip(),
            "asset_id": None,
        }

    @rx.event
    async def save_pc_form(self) -> AsyncGenerator[Any, None]:
        """Simpan PC (Tambah / Edit) lalu tutup modal."""
        if not self._validate_form():
            return

        payload = self._build_payload()
        if self.form_mode == "edit" and self.form_editing_id:
            updated = await api_client.update_pc(self.form_editing_id, payload)
            self.form_modal_open = False
            self.active_jenis_tab = payload["jenis"]
            await self.load_pcs()
            if updated and self.active_pc_id == self.form_editing_id:
                self.active_pc = updated
            yield rx.toast.success(
                f"Spesifikasi {payload['nama_pc']} berhasil diperbarui.",
                position="top-right",
            )
            return

        created = await api_client.create_pc(payload)
        self.form_modal_open = False
        self.active_jenis_tab = payload["jenis"]
        self.page = 1
        await self.load_pcs()
        yield rx.toast.success(
            f"PC '{created['nama_pc']}' ({created['id']}) berhasil ditambahkan.",
            position="top-right",
        )

    @rx.event
    async def save_and_add_another(self) -> AsyncGenerator[Any, None]:
        """Simpan PC lalu kosongkan Nama PC & User agar bisa langsung input unit berikutnya."""
        if not self._validate_form():
            return

        payload = self._build_payload()
        created = await api_client.create_pc(payload)
        self.active_jenis_tab = payload["jenis"]
        self.page = 1
        await self.load_pcs()

        # Pertahankan spesifikasi perangkat keras agar input PC rakitan sejenis cepat
        self.form_nama_pc = ""
        self.form_user = ""
        self.form_catatan = ""
        self.form_error = ""
        yield rx.toast.success(
            f"PC '{created['nama_pc']}' disimpan. Silakan isi Nama PC berikutnya.",
            position="top-right",
        )

    @rx.event
    def confirm_delete_pc(self, row_id: str) -> None:
        target = row_id or self.active_pc_id
        if target:
            item = next((it for it in self.items if it["id"] == target), self.active_pc)
            self.pc_to_delete = target
            self.pc_to_delete_name = str(item.get("nama_pc", target))
            self.delete_dialog_open = True

    @rx.event
    def cancel_delete(self) -> None:
        self.delete_dialog_open = False
        self.pc_to_delete = ""
        self.pc_to_delete_name = ""

    @rx.event
    async def execute_delete_pc(self) -> AsyncGenerator[Any, None]:
        target = self.pc_to_delete
        target_name = self.pc_to_delete_name
        self.delete_dialog_open = False
        self.pc_to_delete = ""
        self.pc_to_delete_name = ""
        if target:
            await api_client.delete_pc(target)
            if self.active_pc_id == target:
                self.drawer_open = False
                self.active_pc_id = ""
            await self.load_pcs()
            yield rx.toast.success(
                f"PC '{target_name}' ({target}) telah dihapus.",
                position="top-right",
            )

    @rx.event
    def trigger_coming_soon(self, action_name: str) -> Any:
        return rx.toast.info(
            f"{action_name} — Segera hadir.",
            position="top-right",
        )


__all__ = ["PCState"]
