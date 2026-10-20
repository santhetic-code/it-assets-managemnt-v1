"""
State Assets Inventory ITAM Pro.
Mengelola daftar master, filter 5 dropdown, paginasi, detail drawer 2 grup,
dan form modal tambah/edit/duplikat × N dengan validasi aturan bisnis.
"""
from collections.abc import AsyncGenerator
import math
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.mock.master_data import (
    MASTER_KATEGORI,
    MASTER_KEPEMILIKAN,
    MASTER_KONDISI,
    MASTER_LOKASI,
    MASTER_STATUS,
)


class AssetState(rx.State):
    # Daftar Master dari services/mock/master_data.py
    master_kategori_options: list[str] = list(MASTER_KATEGORI)
    master_kepemilikan_options: list[str] = list(MASTER_KEPEMILIKAN)
    master_lokasi_options: list[str] = list(MASTER_LOKASI)
    master_kondisi_options: list[str] = list(MASTER_KONDISI)
    master_status_options: list[str] = list(MASTER_STATUS)

    # Data Tabel & Paginasi
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    is_loading: bool = False

    # State Filter Bar (Pencarian + 5 Dropdown Master)
    search_query: str = ""
    kategori_filter: str = "Semua"
    kepemilikan_filter: str = "Semua"
    lokasi_filter: str = "Semua"
    kondisi_filter: str = "Semua"
    status_filter: str = "Semua"

    # Seleksi Baris & Detail Drawer State
    selected_ids: list[str] = []
    active_asset_id: str = ""
    active_asset: dict[str, Any] = {}
    drawer_open: bool = False
    drawer_tab: str = "detail"

    # State Modal Form Tambah / Edit / Duplikat × N
    form_modal_open: bool = False
    form_mode: str = "add"
    form_editing_id: str = ""
    form_nama_aset: str = ""
    form_kategori: str = MASTER_KATEGORI[0]
    form_sn_pid: str = ""
    form_tgl_masuk: str = ""
    form_tgl_keluar: str = ""
    form_kepemilikan: str = MASTER_KEPEMILIKAN[0]
    form_lokasi: str = MASTER_LOKASI[0]
    form_kondisi: str = MASTER_KONDISI[0]
    form_status: str = MASTER_STATUS[0]
    form_digunakan_oleh: str = ""
    form_catatan: str = ""
    form_duplicate_count: str = "1"
    form_error: str = ""

    # State Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    asset_to_delete: str = ""
    asset_to_delete_name: str = ""

    @rx.var
    def is_digunakan_oleh_required(self) -> bool:
        """Bernilai True jika Status == 'Digunakan'."""
        return self.form_status == "Digunakan"

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
        return f"{self.total} unit ditemukan"

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

    @rx.var
    def active_code(self) -> str:
        return str(self.active_asset.get("id", ""))

    @rx.var
    def active_name(self) -> str:
        return str(self.active_asset.get("nama_aset", ""))

    @rx.var
    def active_category(self) -> str:
        return str(self.active_asset.get("kategori", ""))

    @rx.var
    def active_condition(self) -> str:
        return str(self.active_asset.get("kondisi", "Baru"))

    @rx.var
    def active_status(self) -> str:
        return str(self.active_asset.get("status", "Digunakan"))

    @rx.var
    def active_general_info(self) -> list[dict[str, str]]:
        return self.active_asset.get("general_info", [])

    @rx.var
    def active_usage_info(self) -> list[dict[str, str]]:
        return self.active_asset.get("usage_info", [])

    @rx.var
    def active_history_info(self) -> list[dict[str, str]]:
        return self.active_asset.get("history_info", [])

    @rx.event
    async def load_assets(self) -> None:
        """Muat daftar aset berdasarkan pencarian, 5 filter master, dan halaman aktif."""
        self.is_loading = True
        filters = {
            "search": self.search_query,
            "kategori": self.kategori_filter,
            "kepemilikan": self.kepemilikan_filter,
            "lokasi": self.lokasi_filter,
            "kondisi": self.kondisi_filter,
            "status": self.status_filter,
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
    async def set_kategori_filter(self, value: str) -> None:
        self.kategori_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def set_kepemilikan_filter(self, value: str) -> None:
        self.kepemilikan_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def set_lokasi_filter(self, value: str) -> None:
        self.lokasi_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def set_kondisi_filter(self, value: str) -> None:
        self.kondisi_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def set_status_filter(self, value: str) -> None:
        self.status_filter = value
        self.page = 1
        await self.load_assets()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.kategori_filter = "Semua"
        self.kepemilikan_filter = "Semua"
        self.lokasi_filter = "Semua"
        self.kondisi_filter = "Semua"
        self.status_filter = "Semua"
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
    def set_form_nama_aset(self, value: str) -> None:
        self.form_nama_aset = value
        self.form_error = ""

    @rx.event
    def set_form_kategori(self, value: str) -> None:
        self.form_kategori = value

    @rx.event
    def set_form_sn_pid(self, value: str) -> None:
        self.form_sn_pid = value

    @rx.event
    def set_form_tgl_masuk(self, value: str) -> None:
        self.form_tgl_masuk = value
        self.form_error = ""

    @rx.event
    def set_form_tgl_keluar(self, value: str) -> None:
        self.form_tgl_keluar = value
        self.form_error = ""

    @rx.event
    def set_form_kepemilikan(self, value: str) -> None:
        self.form_kepemilikan = value

    @rx.event
    def set_form_lokasi(self, value: str) -> None:
        self.form_lokasi = value

    @rx.event
    def set_form_kondisi(self, value: str) -> None:
        self.form_kondisi = value

    @rx.event
    def set_form_status(self, value: str) -> None:
        """Jika Status diubah ke 'Tidak Digunakan', kosongkan field 'Digunakan Oleh'."""
        self.form_status = value
        if value == "Tidak Digunakan":
            self.form_digunakan_oleh = ""
        self.form_error = ""

    @rx.event
    def set_form_digunakan_oleh(self, value: str) -> None:
        self.form_digunakan_oleh = value
        self.form_error = ""

    @rx.event
    def set_form_catatan(self, value: str) -> None:
        self.form_catatan = value

    @rx.event
    def set_form_duplicate_count(self, value: str) -> None:
        self.form_duplicate_count = value

    def _reset_form_fields(self) -> None:
        self.form_editing_id = ""
        self.form_nama_aset = ""
        self.form_kategori = self.master_kategori_options[0]
        self.form_sn_pid = ""
        self.form_tgl_masuk = ""
        self.form_tgl_keluar = ""
        self.form_kepemilikan = self.master_kepemilikan_options[0]
        self.form_lokasi = self.master_lokasi_options[0]
        self.form_kondisi = self.master_kondisi_options[0]
        self.form_status = self.master_status_options[0]
        self.form_digunakan_oleh = ""
        self.form_catatan = ""
        self.form_duplicate_count = "1"
        self.form_error = ""

    @rx.event
    def open_add_modal(self) -> None:
        """Buka modal form dalam mode tambah aset baru."""
        self._reset_form_fields()
        self.form_mode = "add"
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str) -> None:
        """Buka modal form dalam mode edit aset."""
        target_id = row_id or self.active_asset_id
        target_item = next((it for it in self.items if it["id"] == target_id), None)
        if not target_item and self.active_asset.get("id") == target_id:
            target_item = self.active_asset
        if not target_item:
            return

        self.form_mode = "edit"
        self.form_editing_id = target_id
        self.form_nama_aset = str(target_item.get("nama_aset", ""))
        self.form_kategori = str(target_item.get("kategori", self.master_kategori_options[0]))
        self.form_sn_pid = str(target_item.get("sn_pid_raw", ""))
        self.form_tgl_masuk = str(target_item.get("tanggal_masuk_iso", ""))
        self.form_tgl_keluar = str(target_item.get("tanggal_keluar_iso", ""))
        self.form_kepemilikan = str(
            target_item.get("kepemilikan", self.master_kepemilikan_options[0])
        )
        self.form_lokasi = str(target_item.get("lokasi", self.master_lokasi_options[0]))
        self.form_kondisi = str(target_item.get("kondisi", self.master_kondisi_options[0]))
        self.form_status = str(target_item.get("status", self.master_status_options[0]))
        self.form_digunakan_oleh = (
            str(target_item.get("digunakan_oleh_raw", ""))
            if self.form_status == "Digunakan"
            else ""
        )
        self.form_catatan = str(target_item.get("catatan_raw", ""))
        self.form_duplicate_count = "1"
        self.form_error = ""
        self.form_modal_open = True

    @rx.event
    def open_duplicate_modal(self, row_id: str) -> None:
        """Salin data baris terpilih ke mode Tambah dengan default Duplikat × 2."""
        self.open_edit_modal(row_id)
        self.form_mode = "add"
        self.form_editing_id = ""
        self.form_duplicate_count = "2"
        self.form_modal_open = True

    @rx.event
    def close_form_modal(self) -> None:
        self.form_modal_open = False
        self.form_error = ""

    def _validate_form(self) -> bool:
        """Validasi aturan bisnis form aset."""
        if not self.form_nama_aset.strip():
            self.form_error = "Nama Aset wajib diisi."
            return False

        if self.form_status == "Digunakan" and not self.form_digunakan_oleh.strip():
            self.form_error = "Field 'Digunakan Oleh' wajib diisi ketika Status adalah Digunakan."
            return False

        masuk = self.form_tgl_masuk.strip()
        keluar = self.form_tgl_keluar.strip()
        if masuk and keluar and keluar < masuk:
            self.form_error = (
                "Tanggal Keluar Gudang tidak boleh sebelum Tanggal Masuk Gudang."
            )
            return False

        if self.form_mode == "add":
            try:
                qty = int(self.form_duplicate_count)
                if qty < 1 or qty > 50:
                    self.form_error = "Jumlah Duplikat × N harus antara 1 sampai 50 unit."
                    return False
            except ValueError:
                self.form_error = "Jumlah Duplikat × N harus berupa angka bulat."
                return False

        self.form_error = ""
        return True

    def _build_payload(self) -> dict[str, Any]:
        return {
            "nama_aset": self.form_nama_aset.strip(),
            "kategori": self.form_kategori,
            "sn_pid": self.form_sn_pid.strip(),
            "tanggal_masuk_gudang": self.form_tgl_masuk.strip(),
            "tanggal_keluar_gudang": self.form_tgl_keluar.strip(),
            "kepemilikan": self.form_kepemilikan,
            "lokasi": self.form_lokasi,
            "kondisi": self.form_kondisi,
            "status": self.form_status,
            "digunakan_oleh": (
                self.form_digunakan_oleh.strip() if self.form_status == "Digunakan" else ""
            ),
            "catatan": self.form_catatan.strip(),
        }

    @rx.event
    async def save_asset_form(self) -> AsyncGenerator[Any, None]:
        """Simpan aset (Tambah / Duplikat × N / Edit) lalu tutup modal."""
        if not self._validate_form():
            return

        payload = self._build_payload()
        if self.form_mode == "edit" and self.form_editing_id:
            updated = await api_client.update_asset(self.form_editing_id, payload)
            self.form_modal_open = False
            await self.load_assets()
            if updated and self.active_asset_id == self.form_editing_id:
                self.active_asset = updated
            yield rx.toast.success(
                f"Perubahan pada {self.form_editing_id} berhasil disimpan.",
                position="top-right",
            )
            return

        qty = int(self.form_duplicate_count)
        created = await api_client.create_assets(payload, duplicate_count=qty)
        self.form_modal_open = False
        self.page = 1
        await self.load_assets()
        yield rx.toast.success(
            f"{len(created)} unit '{payload['nama_aset']}' berhasil ditambahkan.",
            position="top-right",
        )

    @rx.event
    async def save_and_add_another(self) -> AsyncGenerator[Any, None]:
        """Simpan aset baru lalu bersihkan Nama Aset & SN/PID untuk input unit berikutnya."""
        if not self._validate_form():
            return

        payload = self._build_payload()
        qty = int(self.form_duplicate_count)
        created = await api_client.create_assets(payload, duplicate_count=qty)
        self.page = 1
        await self.load_assets()

        self.form_nama_aset = ""
        self.form_sn_pid = ""
        self.form_catatan = ""
        self.form_duplicate_count = "1"
        self.form_error = ""
        yield rx.toast.success(
            f"{len(created)} unit disimpan. Silakan input unit berikutnya.",
            position="top-right",
        )

    @rx.event
    def confirm_delete_asset(self, row_id: str) -> None:
        target = row_id or self.active_asset_id
        if target:
            item = next((it for it in self.items if it["id"] == target), self.active_asset)
            self.asset_to_delete = target
            self.asset_to_delete_name = str(item.get("nama_aset", target))
            self.delete_dialog_open = True

    @rx.event
    def cancel_delete(self) -> None:
        self.delete_dialog_open = False
        self.asset_to_delete = ""
        self.asset_to_delete_name = ""

    @rx.event
    async def execute_delete_asset(self) -> AsyncGenerator[Any, None]:
        target = self.asset_to_delete
        target_name = self.asset_to_delete_name
        self.delete_dialog_open = False
        self.asset_to_delete = ""
        self.asset_to_delete_name = ""
        if target:
            await api_client.delete_asset(target)
            if self.active_asset_id == target:
                self.drawer_open = False
                self.active_asset_id = ""
            await self.load_assets()
            yield rx.toast.success(
                f"Unit '{target_name}' ({target}) telah dihapus.",
                position="top-right",
            )

    @rx.event
    def trigger_coming_soon(self, action_name: str) -> Any:
        return rx.toast.info(
            f"{action_name} — Segera hadir.",
            position="top-right",
        )


__all__ = ["AssetState"]
