"""
State Modul Infrastructure -> IP & Server (VM).
Mendukung field Pengguna, Kategori (IP Operasional, IP Server, IP VM),
serta ekspor/impor teroptimasi.
"""

import csv
import io
import math
from datetime import datetime
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client

MONTHS_ID = [
    "",
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]


def _ipv4_sort_tuple(ip_str: str) -> tuple[int, int, int, int, str]:
    parts = ip_str.strip().split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), ip_str)
    return (999, 999, 999, 999, ip_str)


class IPState(rx.State):
    is_loading: bool = False
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 10

    kpi_total_ip: int = 0
    kpi_fisik: int = 0
    kpi_vm: int = 0
    kpi_bentrok: int = 0
    kpi_vm_tanpa_host: int = 0
    kpi_kosong_count: int = 254
    conflict_banner_text: str = ""

    view_mode: str = "table"  # "table" | "map"
    active_subnet: str = "192.168.1.0/24"
    subnet_options: list[str] = ["192.168.1.0/24", "192.168.2.0/24", "10.0.0.0/24"]
    map_cells: list[dict[str, Any]] = []
    map_stats: dict[str, Any] = {}
    map_selected_octet: int = -1
    map_selected_cell: dict[str, Any] = {}
    map_suggested_ips: list[str] = []
    map_largest_empty_range: str = ""
    map_only_empty: bool = False

    active_jenis_tab: str = "Semua"
    sort_by: str = "ip_address"
    sort_dir: str = "asc"

    search_query: str = ""
    jenis_filter: str = ""
    host_filter: str = ""
    kategori_filter: str = ""
    status_filter: str = ""
    only_conflict_filter: bool = False
    only_orphan_vm_filter: bool = False

    host_options: list[str] = []
    server_asset_ids: list[str] = ["SRV-0001", "SRV-0002"]
    os_suggestions: list[str] = []

    selected_ids: list[str] = []
    active_entry_id: str = ""
    drawer_open: bool = False
    drawer_tab: str = "detail"

    form_modal_open: bool = False
    form_mode: str = "add"
    form_entry_id: str = ""
    form_error: str = ""
    form_ip_address: str = ""
    form_pengguna: str = ""
    form_jenis: str = "Fisik"
    form_host_asset_id: str = ""
    form_kategori: str = "IP Operasional"
    form_fungsi: str = ""
    form_os: str = ""
    form_status: str = "Aktif"
    form_keterangan: str = ""

    import_modal_open: bool = False
    import_is_processing: bool = False
    import_filename: str = ""
    import_id: str = ""
    import_duplicate_mode: str = "skip"  # "skip" | "update"
    import_valid_rows: list[dict[str, Any]] = []
    import_errors: list[dict[str, Any]] = []
    import_summary_text: str = ""
    import_error_detail_text: str = ""
    import_has_preview: bool = False

    delete_dialog_open: bool = False
    entry_to_delete: str = ""
    entry_to_delete_label: str = ""

    @rx.var(cache=True)
    def fisik_percent(self) -> int:
        return round((self.kpi_fisik / self.kpi_total_ip) * 100) if self.kpi_total_ip > 0 else 0

    @rx.var(cache=True)
    def vm_percent(self) -> int:
        return round((self.kpi_vm / self.kpi_total_ip) * 100) if self.kpi_total_ip > 0 else 0

    @rx.var(cache=True)
    def is_map_view(self) -> bool:
        return self.view_mode == "map"

    @rx.var(cache=True)
    def kosong_percent(self) -> int:
        return int((self.kpi_kosong_count / 254) * 100) if self.kpi_kosong_count else 0

    @rx.var(cache=True)
    def jenis_options(self) -> list[str]:
        return ["Fisik", "VM"]

    @rx.var(cache=True)
    def kategori_options(self) -> list[str]:
        return ["IP Operasional", "IP Server", "IP VM"]

    @rx.var(cache=True)
    def status_options(self) -> list[str]:
        return ["Aktif", "Nonaktif"]

    @rx.var(cache=True)
    def is_form_vm(self) -> bool:
        return self.form_jenis == "VM"

    @rx.var(cache=True)
    def has_conflict_banner(self) -> bool:
        return self.kpi_bentrok > 0 and self.conflict_banner_text != ""

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total} entri"

    @rx.var(cache=True)
    def all_current_selected(self) -> bool:
        if not self.items or not self.selected_ids:
            return False
        selected_set = set(self.selected_ids)
        return all(item.get("id") in selected_set for item in self.items)

    @rx.var(cache=True)
    def total_pages(self) -> int:
        return max(1, math.ceil(self.total / self.page_size))

    @rx.var(cache=True)
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var(cache=True)
    def page_tokens(self) -> list[str]:
        tp = self.total_pages
        cp = self.page
        if tp <= 7:
            return [str(i) for i in range(1, tp + 1)]
        tokens = ["1"]
        if cp > 3:
            tokens.append("...")
        for p in range(max(2, cp - 1), min(tp, cp + 2)):
            tokens.append(str(p))
        if cp < tp - 2:
            tokens.append("...")
        tokens.append(str(tp))
        return tokens

    @rx.var
    def import_duplicate_mode_label(self) -> str:
        return (
            "Perbarui data jika IP ada"
            if self.import_duplicate_mode == "update"
            else "Lewati duplikat"
        )

    @rx.var(cache=True)
    def pagination_summary(self) -> str:
        if self.total == 0:
            return "Menampilkan 0 dari 0"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total, self.page * self.page_size)
        return f"Menampilkan {start}–{end} dari {self.total}"

    @rx.var(cache=True)
    def import_valid_count(self) -> int:
        return len(self.import_valid_rows)

    @rx.var(cache=True)
    def import_error_count(self) -> int:
        return len(self.import_errors)

    @rx.var(cache=True)
    def import_button_label(self) -> str:
        count = len(self.import_valid_rows)
        return f"Import {count} data" if count > 0 else "Import data"

    def _get_active_entry(self) -> dict[str, Any]:
        if not self.active_entry_id or not self.items:
            return {}
        target = self.active_entry_id
        for item in self.items:
            if item.get("id") == target:
                return item
        return {}

    @rx.var(cache=True)
    def active_ip_code(self) -> str:
        return str(self._get_active_entry().get("ip_address", ""))

    @rx.var(cache=True)
    def active_pengguna_title(self) -> str:
        entry = self._get_active_entry()
        return str(entry.get("pengguna") or entry.get("nama") or "")

    @rx.var(cache=True)
    def active_nama_title(self) -> str:
        return self.active_pengguna_title

    @rx.var(cache=True)
    def active_kategori_badge(self) -> str:
        return str(self._get_active_entry().get("kategori", "IP Operasional"))

    @rx.var(cache=True)
    def active_jenis_badge(self) -> str:
        return str(self._get_active_entry().get("jenis", "Fisik"))

    @rx.var(cache=True)
    def active_status_badge(self) -> str:
        item = self._get_active_entry()
        return "Bentrok" if item.get("is_conflict") else str(item.get("status", "Aktif"))

    @rx.var(cache=True)
    def drawer_has_kendala(self) -> bool:
        entry = self._get_active_entry()
        ket = str(entry.get("keterangan", "")).strip()
        fung = str(entry.get("fungsi", "")).strip()
        return bool(ket and ket != "—" and ket != fung)

    @rx.var(cache=True)
    def active_host_name(self) -> str:
        entry = self._get_active_entry()
        return str(
            entry.get("host_display")
            or entry.get("host_label")
            or entry.get("host_asset_id")
            or "Tidak ada (standalone)"
        )

    @rx.var(cache=True)
    def active_is_vm(self) -> bool:
        return self.active_jenis_badge == "VM"

    @rx.var(cache=True)
    def active_child_vms(self) -> list[dict[str, str]]:
        entry = self._get_active_entry()
        if not entry or entry.get("jenis") != "Fisik":
            return []
        return api_client.get_vms_on_host_sync(
            str(entry.get("asset_id") or entry.get("nama") or "")
        )

    @rx.var(cache=True)
    def active_has_child_vms(self) -> bool:
        return len(self.active_child_vms) > 0

    @rx.var(cache=True)
    def map_selected_ip_display(self) -> str:
        return str(self.map_selected_cell.get("ip_address", ""))

    @rx.var(cache=True)
    def has_map_selected_empty(self) -> bool:
        return bool(
            self.map_selected_octet >= 0 and self.map_selected_cell.get("status") == "kosong"
        )

    @rx.var(cache=True)
    def active_general_items(self) -> list[dict[str, str]]:
        item = self._get_active_entry()
        if not item:
            return []
        return [
            {"label": "ID Entri", "value": str(item.get("id", "—"))},
            {"label": "IP Address", "value": str(item.get("ip_address", "—"))},
            {"label": "Pengguna", "value": str(item.get("pengguna") or item.get("nama") or "—")},
            {"label": "Jenis", "value": str(item.get("jenis", "—"))},
            {"label": "Kategori", "value": str(item.get("kategori", "—"))},
            {"label": "Host", "value": str(item.get("host_display", item.get("host_label", "—")))},
            {"label": "Fungsi", "value": str(item.get("fungsi", "—"))},
            {"label": "Operating System", "value": str(item.get("os", "—"))},
            {"label": "Status", "value": str(item.get("status", "—"))},
            {"label": "Keterangan / Kendala", "value": str(item.get("keterangan", "—"))},
        ]

    @rx.var(cache=True)
    def active_relation_items(self) -> list[dict[str, str]]:
        item = self._get_active_entry()
        if not item:
            return []
        jenis = str(item.get("jenis", "Fisik"))
        if jenis == "Fisik":
            vms = api_client.get_vms_on_host_sync(
                str(item.get("asset_id") or item.get("ip_address", ""))
            )
            rows = [{"label": "Status", "value": "Aset Fisik Standalone"}]
            if vms:
                rows.extend(vms)
            else:
                rows.append({"label": "Daftar VM", "value": "Tidak ada VM menempel di host ini"})
            return rows

        host_id = str(item.get("host_asset_id", "")).strip()
        return [
            {"label": "Host Server Fisik", "value": str(item.get("host_label", "Tanpa host"))},
            {
                "label": "Status Host",
                "value": f"Terhubung ke {host_id}"
                if host_id
                else "PERINGATAN: VM belum memiliki host fisik",
            },
        ]

    @rx.var(cache=True)
    def active_history_items(self) -> list[dict[str, str]]:
        item = self._get_active_entry()
        if not item:
            return []
        return [
            {
                "event": f"Alokasi IP {item.get('ip_address', '')}",
                "date": "Hari ini",
                "note": f"Pengguna: {item.get('pengguna') or item.get('nama') or ''}",
            }
        ]

    @staticmethod
    def _enrich_row_for_view(raw: dict[str, Any]) -> dict[str, Any]:
        item = dict(raw)
        jenis = str(item.get("jenis", "Fisik")).strip() or "Fisik"
        ket_raw = str(item.get("keterangan", "")).strip()
        has_kendala = bool(ket_raw and ket_raw != "—")
        item["has_kendala"] = has_kendala

        item["pengguna"] = str(item.get("pengguna") or item.get("nama") or "—").strip() or "—"
        item["nama"] = str(item.get("nama") or item["pengguna"])
        item["kategori"] = str(item.get("kategori") or "IP Operasional").strip() or "IP Operasional"

        host_id = str(item.get("host_asset_id", "")).strip()
        host_label = str(item.get("host_label", "")).strip()

        if jenis == "Fisik":
            base_sub = "Perangkat Fisik"
            host_col = "—"
        else:
            if host_id and host_id != "—":
                base_sub = f"Host: {host_id}"
                host_col = host_label if (host_label and host_label != "Tanpa host") else host_id
            else:
                base_sub = "Tanpa host"
                host_col = "Tanpa host"

        item["sub_label"] = "● Ada kendala (lihat keterangan)" if has_kendala else base_sub
        item["host_display"] = host_col
        return item

    @rx.event
    async def load_ip_page(self) -> None:
        await self.fetch_ip_entries()
        if self.view_mode == "map":
            await self.fetch_ip_map()

    @rx.event
    async def set_view_mode(self, mode: str) -> None:
        if self.view_mode == mode:
            return
        self.view_mode = mode
        if mode == "map" and not self.map_cells:
            await self.fetch_ip_map()

    @rx.event
    async def set_active_subnet(self, val: str) -> None:
        if self.active_subnet == val:
            return
        self.active_subnet = val
        self.map_selected_octet = -1
        self.map_selected_cell = {}
        await self.fetch_ip_map()

    @rx.event
    async def fetch_ip_map(self) -> None:
        res = await api_client.get_ip_map(self.active_subnet)
        self.map_cells = res.get("cells", [])
        self.map_stats = res.get("stats", {})
        self.map_suggested_ips = res.get("suggested_ips", [])
        self.map_largest_empty_range = res.get("largest_empty_range", "")
        self.kpi_kosong_count = int(self.map_stats.get("kosong", max(0, 254 - self.total)))

    @rx.event
    def select_map_cell(self, cell: dict[str, Any]) -> Any:
        self.map_selected_octet = int(cell.get("octet", -1))
        self.map_selected_cell = cell
        if cell.get("is_occupied"):
            entry_id = str(cell.get("entry_id", ""))
            if entry_id:
                return self.open_detail_drawer_by_id(entry_id)
            return None
        if cell.get("is_reserved"):
            return rx.toast.info(
                "Alamat IP ini direservasi oleh sistem network.", position="top-right"
            )
        return None

    @rx.event
    def open_add_from_map(self, ip_address: str) -> None:
        self.open_add_modal()
        self.form_ip_address = ip_address

    @rx.event
    def toggle_map_only_empty(self) -> None:
        self.map_only_empty = not self.map_only_empty

    @rx.event
    def open_host_drawer_by_code(self, host_code: str) -> Any:
        clean = host_code.strip().lower()
        for item in self.items:
            aid = str(item.get("asset_id", "")).strip().lower()
            nama = str(item.get("nama", "")).strip().lower()
            if aid == clean or nama == clean:
                self.active_entry_id = str(item.get("id", ""))
                self.drawer_tab = "detail"
                self.drawer_open = True
                return None
        return rx.toast.info(
            f"Host '{host_code}' tidak ditemukan di tabel ini.", position="top-right"
        )

    @rx.event
    def open_detail_drawer_by_id(self, entry_id: str) -> None:
        self.active_entry_id = entry_id
        self.drawer_tab = "detail"
        self.drawer_open = True

    @rx.event
    def set_import_duplicate_mode(self, mode: str) -> None:
        if "perbarui" in mode.lower() or mode == "update":
            self.import_duplicate_mode = "update"
        else:
            self.import_duplicate_mode = "skip"

    @rx.event
    async def fetch_ip_entries(self) -> None:
        self.is_loading = True
        effective_jenis = (
            self.jenis_filter
            if self.jenis_filter
            else (self.active_jenis_tab if self.active_jenis_tab in ("Fisik", "VM") else "")
        )
        filters = {
            "search": self.search_query,
            "jenis": effective_jenis,
            "host": self.host_filter,
            "kategori": self.kategori_filter,
            "status": self.status_filter,
            "only_conflict": self.only_conflict_filter,
            "only_orphan_vm": self.only_orphan_vm_filter,
            "sort_by": self.sort_by,
            "sort_dir": self.sort_dir,
        }
        res = await api_client.get_ip_entries(
            grup="Semua", filters=filters, page=self.page, page_size=self.page_size
        )
        raw_items = res.get("items", [])
        self.items = [self._enrich_row_for_view(r) for r in raw_items]
        self.total = int(res.get("total", 0))

        kpi = res.get("kpi", {})
        self.kpi_total_ip = int(kpi.get("total_ip", self.total))
        self.kpi_fisik = int(
            kpi.get("fisik", sum(1 for x in raw_items if x.get("jenis") == "Fisik"))
        )
        self.kpi_vm = int(kpi.get("vm", sum(1 for x in raw_items if x.get("jenis") == "VM")))
        self.kpi_bentrok = int(kpi.get("bentrok", 0))
        self.kpi_vm_tanpa_host = int(kpi.get("vm_tanpa_host", 0))
        self.kpi_kosong_count = int(kpi.get("kosong", max(0, 254 - self.total)))
        self.conflict_banner_text = str(res.get("conflict_banner", ""))
        self.host_options = res.get("host_options", [])
        self.server_asset_ids = res.get("server_asset_ids", ["SRV-0001", "SRV-0002"])
        self.os_suggestions = res.get("os_suggestions", [])
        self.is_loading = False

    @rx.event
    async def set_jenis_tab(self, tab_key: str) -> None:
        if self.active_jenis_tab == tab_key:
            return
        self.active_jenis_tab = tab_key
        self.jenis_filter = "" if tab_key == "Semua" else tab_key
        self.page = 1
        self.selected_ids = []
        await self.fetch_ip_entries()

    @rx.event
    async def set_jenis_filter(self, val: str) -> None:
        clean = "" if val in ("Semua", "Semua jenis") else val
        if self.jenis_filter == clean:
            return
        self.jenis_filter = clean
        self.active_jenis_tab = clean if clean in ("Fisik", "VM") else "Semua"
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_search_query(self, val: str) -> None:
        if self.search_query == val:
            return
        self.search_query = val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_host_filter(self, val: str) -> None:
        clean = "" if val in ("Semua", "Semua host") else val
        if self.host_filter == clean:
            return
        self.host_filter = clean
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_kategori_filter(self, val: str) -> None:
        clean = "" if val in ("Semua", "Semua kategori") else val
        if self.kategori_filter == clean:
            return
        self.kategori_filter = clean
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_status_filter(self, val: str) -> None:
        clean = "" if val in ("Semua", "Semua status") else val
        if self.status_filter == clean:
            return
        self.status_filter = clean
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def toggle_conflict_only(self) -> None:
        self.only_conflict_filter = not self.only_conflict_filter
        self.only_orphan_vm_filter = False
        self.active_jenis_tab = "Semua"
        self.jenis_filter = ""
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def toggle_orphan_vm_only(self) -> None:
        self.only_orphan_vm_filter = not self.only_orphan_vm_filter
        self.only_conflict_filter = False
        self.active_jenis_tab = "VM" if self.only_orphan_vm_filter else "Semua"
        self.jenis_filter = "VM" if self.only_orphan_vm_filter else ""
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def reset_filters(self) -> None:
        self.active_jenis_tab = "Semua"
        self.search_query = ""
        self.jenis_filter = ""
        self.host_filter = ""
        self.kategori_filter = ""
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
            if 1 <= target <= self.total_pages and target != self.page:
                self.page = target
                await self.fetch_ip_entries()

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
        if self.drawer_open:
            self.drawer_open = False

    @rx.event
    def set_drawer_tab(self, tab_key: str) -> None:
        if self.drawer_tab != tab_key:
            self.drawer_tab = tab_key

    @rx.event
    def open_add_modal(self) -> None:
        self.form_mode = "add"
        self.form_entry_id = ""
        self.form_error = ""
        self.form_ip_address = ""
        self.form_pengguna = ""
        self.form_jenis = "VM" if self.active_jenis_tab == "VM" else "Fisik"
        self.form_host_asset_id = (
            (self.server_asset_ids[0] if self.server_asset_ids else "SRV-0001")
            if self.form_jenis == "VM"
            else ""
        )
        self.form_kategori = "IP VM" if self.form_jenis == "VM" else "IP Operasional"
        self.form_status = "Aktif"
        self.form_os = ""
        self.form_fungsi = ""
        self.form_keterangan = ""
        self.form_modal_open = True

    def _populate_form(self, item: dict[str, Any], mode: str) -> None:
        self.form_mode = mode
        self.form_entry_id = str(item.get("id", "")) if mode == "edit" else ""
        self.form_error = ""
        self.form_ip_address = str(item.get("ip_address", "")) if mode == "edit" else ""
        self.form_pengguna = str(item.get("pengguna") or item.get("nama") or "")
        self.form_jenis = str(item.get("jenis", "Fisik"))
        self.form_host_asset_id = (
            str(item.get("host_asset_id", "")) if self.form_jenis == "VM" else ""
        )
        self.form_kategori = str(item.get("kategori", "IP Operasional"))
        self.form_fungsi = str(item.get("fungsi", "")) if str(item.get("fungsi", "")) != "—" else ""
        self.form_os = str(item.get("os", "")) if str(item.get("os", "")) != "—" else ""
        self.form_status = str(item.get("status", "Aktif"))
        self.form_keterangan = (
            str(item.get("keterangan", "")) if str(item.get("keterangan", "")) != "—" else ""
        )
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str) -> None:
        target = row_id or self.active_entry_id
        for item in self.items:
            if item.get("id") == target:
                self._populate_form(item, mode="edit")
                return

    @rx.event
    def open_duplicate_modal(self, row_id: str) -> None:
        target = row_id or self.active_entry_id
        for item in self.items:
            if item.get("id") == target:
                self._populate_form(item, mode="add")
                return

    @rx.event
    def close_form_modal(self) -> None:
        if self.form_modal_open:
            self.form_modal_open = False
        self.form_error = ""

    @rx.event
    def set_form_ip_address(self, val: str) -> None:
        self.form_ip_address = val

    @rx.event
    def set_form_pengguna(self, val: str) -> None:
        self.form_pengguna = val

    @rx.event
    def set_form_jenis(self, val: str) -> None:
        self.form_jenis = val
        if val == "Fisik":
            self.form_host_asset_id = ""
        else:
            if not self.form_host_asset_id and self.server_asset_ids:
                self.form_host_asset_id = self.server_asset_ids[0]

    @rx.event
    def set_form_host_asset_id(self, val: str) -> None:
        self.form_host_asset_id = val

    @rx.event
    def set_form_kategori(self, val: str) -> None:
        self.form_kategori = val

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
        self.form_error = ""
        ip = self.form_ip_address.strip()
        pengguna = self.form_pengguna.strip()
        jenis = self.form_jenis.strip()
        status_val = self.form_status.strip() or "Aktif"

        if not ip:
            self.form_error = "IP Address (IPv4) wajib diisi."
            return None
        exclude_id = self.form_entry_id if self.form_mode == "edit" else ""
        dup_owner = api_client.check_ip_duplicate_sync(ip, exclude_id=exclude_id)
        if dup_owner:
            self.form_error = f"IP sudah dipakai oleh {dup_owner}"
            return None
        if not pengguna:
            self.form_error = "Pengguna wajib diisi."
            return None
        if jenis == "VM" and not self.form_host_asset_id.strip():
            self.form_error = "Host Server Fisik wajib dipilih untuk entri berjenis VM."
            return None

        return {
            "ip_address": ip,
            "nama": pengguna,
            "pengguna": pengguna,
            "jenis": jenis,
            "host_asset_id": self.form_host_asset_id.strip() if jenis == "VM" else "",
            "kategori": self.form_kategori,
            "fungsi": self.form_fungsi.strip(),
            "os": self.form_os.strip(),
            "status": status_val,
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

    @rx.event
    def open_import_modal(self) -> None:
        self.import_modal_open = True
        self.import_is_processing = False
        self.import_filename = ""
        self.import_valid_rows = []
        self.import_errors = []
        self.import_summary_text = ""
        self.import_error_detail_text = ""
        self.import_has_preview = False

    @rx.event
    def close_import_modal(self) -> None:
        if self.import_modal_open:
            self.import_modal_open = False
        self.import_has_preview = False

    @rx.event
    async def download_import_template(self) -> Any:
        content_bytes = await api_client.get_ip_import_template_bytes()
        return rx.download(data=content_bytes, filename="Template_Import_IP.xlsx")

    @rx.event
    async def handle_import_upload(self, files: list[rx.UploadFile]) -> None:
        if not files:
            return
        upload_file = files[0]
        fname = upload_file.filename or "data.xlsx"
        raw_bytes = await upload_file.read()

        self.import_is_processing = True
        preview = await api_client.preview_ip_import_bytes(raw_bytes, fname, self.server_asset_ids)
        self.import_valid_rows = preview.get("valid_rows", [])
        self.import_errors = preview.get("errors", [])
        self.import_id = preview.get("import_id", "")
        self.import_has_preview = True
        self.import_is_processing = False

        v_cnt = len(self.import_valid_rows)
        e_cnt = len(self.import_errors)
        if e_cnt > 0:
            self.import_error_detail_text = (
                f"({self.import_errors[0]['reason']}, baris {self.import_errors[0]['row']}) "
                "— error dilewati."
            )
            self.import_summary_text = f"{v_cnt} valid · {e_cnt} error"
        else:
            self.import_error_detail_text = "— seluruh baris siap diimpor."
            self.import_summary_text = f"{v_cnt} valid · 0 error"

    @rx.event
    def download_import_error_report(self) -> Any:
        if not self.import_errors:
            return None
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Baris", "IP Address", "Pengguna", "Alasan Error"])
        for err in self.import_errors:
            writer.writerow(
                [
                    err.get("row", ""),
                    err.get("ip_address", ""),
                    err.get("nama", ""),
                    err.get("reason", ""),
                ]
            )
        return rx.download(data=buf.getvalue().encode("utf-8-sig"), filename="Error_Import_IP.csv")

    @rx.event
    async def commit_import_data(self) -> Any:
        if not self.import_valid_rows:
            return None
        self.import_is_processing = True
        res = await api_client.commit_ip_import(
            import_id=self.import_id,
            duplicate_mode=self.import_duplicate_mode,
            valid_rows=self.import_valid_rows,
        )
        self.import_is_processing = False
        self.close_import_modal()
        await self.fetch_ip_entries()
        if self.view_mode == "map":
            await self.fetch_ip_map()
        imp_cnt = res.get("imported_count", len(self.import_valid_rows))
        upd_cnt = res.get("updated_count", 0)
        return rx.toast.success(
            f"Import berhasil ({imp_cnt} baru, {upd_cnt} diperbarui).",
            position="top-right",
        )

    async def _collect_filtered_for_export(self) -> list[dict[str, Any]]:
        effective_jenis = (
            self.jenis_filter
            if self.jenis_filter
            else (self.active_jenis_tab if self.active_jenis_tab in ("Fisik", "VM") else "")
        )
        filters = {
            "search": self.search_query,
            "jenis": effective_jenis,
            "host": self.host_filter,
            "kategori": self.kategori_filter,
            "status": self.status_filter,
            "only_conflict": self.only_conflict_filter,
            "only_orphan_vm": self.only_orphan_vm_filter,
        }

        all_rows = []
        page_num = 1
        page_size_limit = 100
        while True:
            res = await api_client.get_ip_entries(
                grup="Semua", filters=filters, page=page_num, page_size=page_size_limit
            )
            items = res.get("items", [])
            if not items:
                break
            all_rows.extend(items)
            if len(all_rows) >= res.get("total", 0):
                break
            page_num += 1

        enriched = [self._enrich_row_for_view(r) for r in all_rows]
        enriched.sort(key=lambda r: _ipv4_sort_tuple(str(r.get("ip_address", ""))))
        return enriched

    @rx.event
    async def export_excel(self) -> Any:
        rows = await self._collect_filtered_for_export()
        xlsx_bytes = await api_client.generate_ip_excel_bytes(rows)
        today = datetime.now().strftime("%Y%m%d")
        return rx.download(data=xlsx_bytes, filename=f"Daftar_IP_{today}.xlsx")

    @rx.event
    async def export_pdf(self) -> Any:
        rows = await self._collect_filtered_for_export()
        now = datetime.now()
        tgl = f"{now.day} {MONTHS_ID[now.month]} {now.year}"
        pdf_bytes = await api_client.generate_ip_pdf_bytes(rows, tgl, "Administrator IT")
        today = now.strftime("%Y%m%d")
        return rx.download(data=pdf_bytes, filename=f"Daftar_IP_{today}.pdf")

    @rx.event
    def confirm_delete_entry(self, row_id: str) -> Any:
        target = row_id or self.active_entry_id
        for item in self.items:
            if str(item.get("id")) == str(target):
                if item.get("jenis") == "Fisik":
                    vms = api_client.get_vms_on_host_sync(
                        str(item.get("asset_id") or item.get("nama") or "")
                    )
                    if vms:
                        return rx.toast.error(
                            f"Masih ada {len(vms)} VM di host ini. "
                            "Pindahkan atau hapus VM terlebih dahulu.",
                            position="top-right",
                        )
                self.entry_to_delete = str(target)
                self.entry_to_delete_label = (
                    f"{item.get('ip_address', '')} · {item.get('pengguna', '')}"
                )
                self.delete_dialog_open = True
                return None
        return None

    @rx.event
    def cancel_delete(self) -> None:
        if self.delete_dialog_open:
            self.delete_dialog_open = False
        self.entry_to_delete = ""

    @rx.event
    async def execute_delete_entry(self) -> None:
        if self.entry_to_delete:
            await api_client.delete_ip_entry(entry_id=self.entry_to_delete)
            if self.active_entry_id == self.entry_to_delete:
                self.drawer_open = False
                self.active_entry_id = ""
        self.cancel_delete()
        await self.fetch_ip_entries()


__all__ = ["IPState"]
