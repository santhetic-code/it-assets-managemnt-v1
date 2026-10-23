"""
State Modul Infrastructure -> IP & Server (VM) (Tahap 8).
Mengelola 5 kartu KPI, banner konflik IP, tab grup, filter subnet /24,
pengurutan numerik IPv4, detail drawer (termasuk daftar VM di host), dan modal form.
"""
import math
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client


class IPState(rx.State):
    """State untuk halaman `/infrastructure/ip`."""

    is_loading: bool = False
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 10

    # 5 Kartu Ringkasan KPI
    kpi_total_ip: int = 26
    kpi_operasional: int = 16
    kpi_addon: int = 10
    kpi_bentrok: int = 2
    kpi_vm_tanpa_host: int = 2
    conflict_banner_text: str = ""

    # Tab & Sort (Default: urut IPv4 numerik naik)
    active_grup_tab: str = "Semua"
    sort_by: str = "ip_address"
    sort_dir: str = "asc"

    # Filter Bar
    search_query: str = ""
    jenis_filter: str = ""
    host_filter: str = ""
    subnet_filter: str = ""
    status_filter: str = ""
    only_conflict_filter: bool = False
    only_orphan_vm_filter: bool = False

    # Opsi dinamis dari data
    subnet_options: list[str] = []
    host_options: list[str] = []
    server_asset_ids: list[str] = ["SRV-0001", "SRV-0002"]
    os_suggestions: list[str] = []

    # Pilihan baris & Detail Drawer
    selected_ids: list[str] = []
    active_entry_id: str = ""
    drawer_open: bool = False
    drawer_tab: str = "detail"

    # Form Modal (660px)
    form_modal_open: bool = False
    form_mode: str = "add"  # "add" | "edit"
    form_entry_id: str = ""
    form_error: str = ""
    form_ip_address: str = ""
    form_nama: str = ""
    form_jenis: str = "VM"
    form_asset_id: str = ""
    form_host_asset_id: str = "SRV-0001"
    form_grup: str = "Operasional"
    form_fungsi: str = ""
    form_os: str = ""
    form_status: str = "Aktif"
    form_keterangan: str = ""

    # Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    entry_to_delete: str = ""
    entry_to_delete_label: str = ""

    # --- COMPUTED VARS ---

    @rx.var
    def jenis_options(self) -> list[str]:
        return ["Fisik", "VM"]

    @rx.var
    def grup_options(self) -> list[str]:
        return ["Operasional", "Addon (VM)"]

    @rx.var
    def status_options(self) -> list[str]:
        return ["Aktif", "Nonaktif"]

    @rx.var
    def has_conflict_banner(self) -> bool:
        return self.kpi_bentrok > 0 and self.conflict_banner_text != ""

    @rx.var
    def result_count_label(self) -> str:
        return f"{self.total} entri"

    @rx.var
    def all_current_selected(self) -> bool:
        if not self.items:
            return False
        return all(item.get("id") in self.selected_ids for item in self.items)

    @rx.var
    def total_pages(self) -> int:
        return max(1, math.ceil(self.total / self.page_size))

    @rx.var
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var
    def page_tokens(self) -> list[str]:
        tp = self.total_pages
        cp = self.page
        if tp <= 7:
            return [str(i) for i in range(1, tp + 1)]
        tokens: list[str] = ["1"]
        if cp > 3:
            tokens.append("...")
        for p in range(max(2, cp - 1), min(tp, cp + 2)):
            tokens.append(str(p))
        if cp < tp - 2:
            tokens.append("...")
        tokens.append(str(tp))
        return tokens

    @rx.var
    def pagination_summary(self) -> str:
        if self.total == 0:
            return "Menampilkan 0 dari 0"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total, self.page * self.page_size)
        return f"Menampilkan {start}–{end} dari {self.total}"

    # --- COMPUTED VARS: DETAIL DRAWER ---

    def _get_active_entry(self) -> dict[str, Any]:
        for item in self.items:
            if item.get("id") == self.active_entry_id:
                return item
        return {}

    @rx.var
    def active_ip_code(self) -> str:
        return str(self._get_active_entry().get("ip_address", ""))

    @rx.var
    def active_nama_title(self) -> str:
        return str(self._get_active_entry().get("nama", ""))

    @rx.var
    def active_jenis_badge(self) -> str:
        return str(self._get_active_entry().get("jenis", "VM"))

    @rx.var
    def active_status_badge(self) -> str:
        item = self._get_active_entry()
        if item.get("is_conflict"):
            return "Bentrok"
        return str(item.get("status", "Aktif"))

    @rx.var
    def active_general_items(self) -> list[dict[str, str]]:
        """Grup 1 Drawer: Data Entri IP & Server."""
        item = self._get_active_entry()
        if not item:
            return []
        return [
            {"label": "ID Entri", "value": str(item.get("id", "—"))},
            {"label": "IP Address", "value": str(item.get("ip_address", "—"))},
            {"label": "Subnet (/24)", "value": str(item.get("subnet", "—"))},
            {"label": "Nama Server / VM", "value": str(item.get("nama", "—"))},
            {"label": "Jenis", "value": str(item.get("jenis", "—"))},
            {"label": "Grup", "value": str(item.get("grup", "—"))},
            {"label": "Fungsi", "value": str(item.get("fungsi", "—"))},
            {"label": "Operasi System", "value": str(item.get("os", "—"))},
            {"label": "Status", "value": str(item.get("status", "—"))},
            {"label": "Keterangan", "value": str(item.get("keterangan", "—"))},
        ]

    @rx.var
    def active_relation_items(self) -> list[dict[str, str]]:
        """Grup 2 Drawer: Relasi Aset Fisik atau Daftar VM yang berjalan di Host ini."""
        item = self._get_active_entry()
        if not item:
            return []
        jenis = str(item.get("jenis", "VM"))
        if jenis == "Fisik":
            aid = str(item.get("asset_id", "")).strip()
            rows: list[dict[str, str]] = [
                {
                    "label": "Tautan Aset Fisik",
                    "value": f"Aset: {aid} (Lihat di menu PC/Server)" if aid else "Belum ditautkan",
                }
            ]
            vms = api_client.get_vms_on_host_sync(aid) if aid else []
            if vms:
                for vm in vms:
                    rows.append(vm)
            else:
                rows.append({"label": "Daftar VM", "value": "Tidak ada VM terdaftar di host ini"})
            return rows

        host_id = str(item.get("host_asset_id", "")).strip()
        return [
            {
                "label": "Host Server Fisik",
                "value": str(item.get("host_label", "Tanpa host")),
            },
            {
                "label": "Status Host",
                "value": f"Terhubung ke aset {host_id}"
                if host_id
                else "PERINGATAN: VM belum memiliki host fisik",
            },
        ]

    @rx.var
    def active_history_items(self) -> list[dict[str, str]]:
        item = self._get_active_entry()
        if not item:
            return []
        return [
            {
                "event": f"Alokasi IP {item.get('ip_address', '')} untuk {item.get('nama', '')}",
                "date": "20 Okt 2026",
                "note": f"Grup: {item.get('grup', '')} · Jenis: {item.get('jenis', '')}",
            }
        ]

    # --- EVENT HANDLERS: FETCH & FILTER ---

    @rx.event
    async def load_ip_page(self) -> None:
        await self.fetch_ip_entries()

    @rx.event
    async def fetch_ip_entries(self) -> None:
        self.is_loading = True
        filters: dict[str, Any] = {
            "search": self.search_query,
            "jenis": self.jenis_filter,
            "host": self.host_filter,
            "subnet": self.subnet_filter,
            "status": self.status_filter,
            "only_conflict": self.only_conflict_filter,
            "only_orphan_vm": self.only_orphan_vm_filter,
            "sort_by": self.sort_by,
            "sort_dir": self.sort_dir,
        }
        res = await api_client.get_ip_entries(
            grup=self.active_grup_tab,
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        self.items = res.get("items", [])
        self.total = int(res.get("total", 0))
        kpi = res.get("kpi", {})
        self.kpi_total_ip = int(kpi.get("total_ip", 0))
        self.kpi_operasional = int(kpi.get("operasional", 0))
        self.kpi_addon = int(kpi.get("addon", 0))
        self.kpi_bentrok = int(kpi.get("bentrok", 0))
        self.kpi_vm_tanpa_host = int(kpi.get("vm_tanpa_host", 0))
        self.conflict_banner_text = str(res.get("conflict_banner", ""))
        self.subnet_options = res.get("subnet_options", [])
        self.host_options = res.get("host_options", [])
        self.server_asset_ids = res.get("server_asset_ids", ["SRV-0001", "SRV-0002"])
        self.os_suggestions = res.get("os_suggestions", [])
        self.is_loading = False

    @rx.event
    async def set_grup_tab(self, tab_key: str) -> None:
        self.active_grup_tab = tab_key
        self.page = 1
        self.selected_ids = []
        await self.fetch_ip_entries()

    @rx.event
    async def set_search_query(self, val: str) -> None:
        self.search_query = val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_jenis_filter(self, val: str) -> None:
        self.jenis_filter = val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_host_filter(self, val: str) -> None:
        self.host_filter = val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_subnet_filter(self, val: str) -> None:
        self.subnet_filter = val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_status_filter(self, val: str) -> None:
        self.status_filter = val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def toggle_conflict_only(self) -> None:
        """Dipanggil oleh tombol 'Tampilkan' pada banner IP bentrok."""
        self.only_conflict_filter = not self.only_conflict_filter
        self.only_orphan_vm_filter = False
        self.active_grup_tab = "Semua"
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.jenis_filter = ""
        self.host_filter = ""
        self.subnet_filter = ""
        self.status_filter = ""
        self.only_conflict_filter = False
        self.only_orphan_vm_filter = False
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def toggle_sort(self, col_key: str) -> None:
        if self.sort_by == col_key:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_by = col_key
            self.sort_dir = "asc"
        await self.fetch_ip_entries()

    @rx.event
    async def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self.fetch_ip_entries()

    @rx.event
    async def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self.fetch_ip_entries()

    @rx.event
    async def select_page(self, token: str) -> None:
        if token.isdigit():
            target = int(token)
            if 1 <= target <= self.total_pages:
                self.page = target
                await self.fetch_ip_entries()

    # --- EVENT HANDLERS: ROW SELECTION & DRAWER ---

    @rx.event
    def toggle_row_selection(self, row_id: str, _checked: Any = None) -> None:
        if row_id in self.selected_ids:
            self.selected_ids = [x for x in self.selected_ids if x != row_id]
        else:
            self.selected_ids = [*self.selected_ids, row_id]

    @rx.event
    def toggle_select_all(self, _checked: Any = None) -> None:
        current_ids = [str(item["id"]) for item in self.items]
        if self.all_current_selected:
            self.selected_ids = [x for x in self.selected_ids if x not in current_ids]
        else:
            merged = list(self.selected_ids)
            for cid in current_ids:
                if cid not in merged:
                    merged.append(cid)
            self.selected_ids = merged

    @rx.event
    def open_drawer(self, row_id: str) -> None:
        self.active_entry_id = row_id
        self.drawer_tab = "detail"
        self.drawer_open = True

    @rx.event
    def close_drawer(self) -> None:
        self.drawer_open = False

    @rx.event
    def set_drawer_tab(self, tab_key: str) -> None:
        self.drawer_tab = tab_key

    # --- EVENT HANDLERS: FORM TAMBAH / EDIT / DUPLIKAT ---

    @rx.event
    def open_add_modal(self) -> None:
        self.form_mode = "add"
        self.form_entry_id = ""
        self.form_error = ""
        self.form_ip_address = ""
        self.form_nama = ""
        self.form_jenis = "VM"
        self.form_asset_id = ""
        self.form_host_asset_id = (
            self.server_asset_ids[0] if self.server_asset_ids else "SRV-0001"
        )
        self.form_grup = (
            self.active_grup_tab
            if self.active_grup_tab in ("Operasional", "Addon (VM)")
            else "Operasional"
        )
        self.form_fungsi = ""
        self.form_os = "Ubuntu Server 24.04 LTS"
        self.form_status = "Aktif"
        self.form_keterangan = ""
        self.form_modal_open = True

    def _populate_form(self, item: dict[str, Any], mode: str) -> None:
        self.form_mode = mode
        self.form_entry_id = str(item.get("id", "")) if mode == "edit" else ""
        self.form_error = ""
        self.form_ip_address = str(item.get("ip_address", "")) if mode == "edit" else ""
        self.form_nama = str(item.get("nama", ""))
        self.form_jenis = str(item.get("jenis", "VM"))
        self.form_asset_id = str(item.get("asset_id", ""))
        self.form_host_asset_id = str(item.get("host_asset_id", ""))
        self.form_grup = str(item.get("grup", "Operasional"))
        fungsi = str(item.get("fungsi", ""))
        self.form_fungsi = "" if fungsi == "—" else fungsi
        os_val = str(item.get("os", ""))
        self.form_os = "" if os_val == "—" else os_val
        self.form_status = str(item.get("status", "Aktif"))
        ket = str(item.get("keterangan", ""))
        self.form_keterangan = "" if ket == "—" else ket
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str = "") -> None:
        target = row_id or self.active_entry_id
        for item in self.items:
            if item.get("id") == target:
                self._populate_form(item, mode="edit")
                return

    @rx.event
    def open_duplicate_modal(self, row_id: str = "") -> None:
        target = row_id or self.active_entry_id
        for item in self.items:
            if item.get("id") == target:
                self._populate_form(item, mode="add")
                return

    @rx.event
    def close_form_modal(self) -> None:
        self.form_modal_open = False
        self.form_error = ""

    @rx.event
    def set_form_ip_address(self, val: str) -> None:
        self.form_ip_address = val

    @rx.event
    def set_form_nama(self, val: str) -> None:
        self.form_nama = val

    @rx.event
    def set_form_jenis(self, val: str) -> None:
        self.form_jenis = val
        if val == "Fisik":
            self.form_host_asset_id = ""
        else:
            self.form_asset_id = ""
            if not self.form_host_asset_id and self.server_asset_ids:
                self.form_host_asset_id = self.server_asset_ids[0]

    @rx.event
    def set_form_asset_id(self, val: str) -> None:
        self.form_asset_id = val

    @rx.event
    def set_form_host_asset_id(self, val: str) -> None:
        self.form_host_asset_id = val

    @rx.event
    def set_form_grup(self, val: str) -> None:
        self.form_grup = val

    @rx.event
    def set_form_fungsi(self, val: str) -> None:
        self.form_fungsi = val

    @rx.event
    def set_form_os(self, val: str) -> None:
        self.form_os = val

    @rx.event
    def set_form_status(self, val: str) -> None:
        self.form_status = val

    @rx.event
    def set_form_keterangan(self, val: str) -> None:
        self.form_keterangan = val

    def _validate_and_build_payload(self) -> dict[str, Any] | None:
        """Validasi format IPv4, duplikasi IP, nama, dan kewajiban host untuk VM."""
        self.form_error = ""
        ip = self.form_ip_address.strip()
        nama = self.form_nama.strip()

        if not ip:
            self.form_error = "IP Address wajib diisi."
            return None
        if not api_client.validate_ipv4_sync(ip):
            self.form_error = "Format IPv4 tidak valid (gunakan format 0-255.0-255.0-255.0-255)."
            return None

        exclude_id = self.form_entry_id if self.form_mode == "edit" else ""
        dup_owner = api_client.check_ip_duplicate_sync(ip, exclude_id=exclude_id)
        if dup_owner:
            self.form_error = f"IP sudah dipakai oleh {dup_owner}"
            return None

        if not nama:
            self.form_error = "Nama Server / VM wajib diisi."
            return None

        if self.form_jenis == "VM" and not self.form_host_asset_id.strip():
            self.form_error = "Host Server Fisik wajib dipilih untuk entri berjenis VM."
            return None

        return {
            "ip_address": ip,
            "nama": nama,
            "jenis": self.form_jenis,
            "asset_id": self.form_asset_id.strip() if self.form_jenis == "Fisik" else "",
            "host_asset_id": self.form_host_asset_id.strip() if self.form_jenis == "VM" else "",
            "grup": self.form_grup,
            "fungsi": self.form_fungsi.strip(),
            "os": self.form_os.strip(),
            "status": self.form_status,
            "keterangan": self.form_keterangan.strip(),
        }

    @rx.event
    async def save_ip_form(self) -> None:
        payload = self._validate_and_build_payload()
        if payload is None:
            return
        if self.form_mode == "edit":
            await api_client.update_ip_entry(entry_id=self.form_entry_id, payload=payload)
        else:
            await api_client.create_ip_entry(payload=payload)
        self.form_modal_open = False
        await self.fetch_ip_entries()

    @rx.event
    async def save_and_add_another(self) -> None:
        payload = self._validate_and_build_payload()
        if payload is None:
            return
        await api_client.create_ip_entry(payload=payload)
        await self.fetch_ip_entries()
        self.open_add_modal()

    # --- EVENT HANDLERS: HAPUS ENTRI ---

    @rx.event
    def confirm_delete_entry(self, row_id: str = "") -> None:
        target = row_id or self.active_entry_id
        for item in self.items:
            if item.get("id") == target:
                self.entry_to_delete = target
                self.entry_to_delete_label = f"{item.get('ip_address', '')} · {item.get('nama', '')}"
                self.delete_dialog_open = True
                return

    @rx.event
    def cancel_delete(self) -> None:
        self.delete_dialog_open = False
        self.entry_to_delete = ""
        self.entry_to_delete_label = ""

    @rx.event
    async def execute_delete_entry(self) -> None:
        if self.entry_to_delete:
            await api_client.delete_ip_entry(entry_id=self.entry_to_delete)
            if self.active_entry_id == self.entry_to_delete:
                self.drawer_open = False
                self.active_entry_id = ""
            self.selected_ids = [x for x in self.selected_ids if x != self.entry_to_delete]
        self.cancel_delete()
        await self.fetch_ip_entries()


__all__ = ["IPState"]
