"""
State Modul Infrastructure -> IP & Server (VM).
Desain Baru (Tanpa Grup):
- 5 Kartu KPI: Total IP, Server Fisik (bar proporsi), VM (bar proporsi), IP Bentrok, VM Tanpa Host.
- Tab: Semua / Fisik / VM.
- Validasi Form: Host Server Fisik hanya muncul & wajib jika Jenis = VM.
- Fitur Import (.xlsx / .csv) 3 langkah dengan preview validasi & laporan error.
- Fitur Export (.xlsx & .pdf) mengikuti filter aktif dan urut IPv4 numerik.
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
    parts = str(ip_str).strip().split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), ip_str)
    return (999, 999, 999, 999, str(ip_str))


class IPState(rx.State):
    """State untuk halaman `/infrastructure/ip` (IP & Server (VM))."""

    is_loading: bool = False
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 10

    # 5 Kartu Ringkasan KPI (Tanpa Grup)
    kpi_total_ip: int = 0
    kpi_fisik: int = 0
    kpi_vm: int = 0
    kpi_bentrok: int = 0
    kpi_vm_tanpa_host: int = 0
    conflict_banner_text: str = ""

    # Tab & Sort (Default: urut IPv4 numerik naik)
    active_jenis_tab: str = "Semua"  # "Semua" | "Fisik" | "VM"
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

    # Form Modal Tambah / Edit IP
    form_modal_open: bool = False
    form_mode: str = "add"  # "add" | "edit"
    form_entry_id: str = ""
    form_error: str = ""
    form_ip_address: str = ""
    form_nama: str = ""
    form_jenis: str = "Fisik"
    form_asset_id: str = ""
    form_host_asset_id: str = ""
    form_fungsi: str = ""
    form_os: str = ""
    form_status: str = "Aktif"
    form_keterangan: str = ""

    # Modal Import 3 Langkah
    import_modal_open: bool = False
    import_is_processing: bool = False
    import_filename: str = ""
    import_valid_rows: list[dict[str, Any]] = []
    import_errors: list[dict[str, Any]] = []
    import_summary_text: str = ""
    import_error_detail_text: str = ""
    import_has_preview: bool = False

    # Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    entry_to_delete: str = ""
    entry_to_delete_label: str = ""

    # --- COMPUTED VARS: KPI & PROPORSIONAL ---

    @rx.var(cache=True)
    def kpi_operasional(self) -> int:
        """Alias kompatibilitas untuk test lama -> mengembalikan jumlah Server Fisik."""
        return self.kpi_fisik

    @rx.var(cache=True)
    def kpi_addon(self) -> int:
        """Alias kompatibilitas untuk test lama -> mengembalikan jumlah VM."""
        return self.kpi_vm

    @rx.var(cache=True)
    def active_grup_tab(self) -> str:
        """Alias kompatibilitas untuk komponen lama."""
        return self.active_jenis_tab

    @rx.var(cache=True)
    def fisik_percent(self) -> int:
        if self.kpi_total_ip <= 0:
            return 0
        return round((self.kpi_fisik / self.kpi_total_ip) * 100)

    @rx.var(cache=True)
    def vm_percent(self) -> int:
        if self.kpi_total_ip <= 0:
            return 0
        return round((self.kpi_vm / self.kpi_total_ip) * 100)

    @rx.var(cache=True)
    def fisik_subtitle(self) -> str:
        return f"PC & server fisik · {self.fisik_percent}%"

    @rx.var(cache=True)
    def vm_subtitle(self) -> str:
        return f"Mesin virtual · {self.vm_percent}%"

    @rx.var(cache=True)
    def jenis_options(self) -> list[str]:
        return ["Fisik", "VM"]

    @rx.var(cache=True)
    def status_options(self) -> list[str]:
        return ["Aktif", "Nonaktif"]

    @rx.var(cache=True)
    def is_form_vm(self) -> bool:
        """Bernilai True hanya jika Jenis pada form adalah VM."""
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
        tokens: list[str] = ["1"]
        if cp > 3:
            tokens.append("...")
        for p in range(max(2, cp - 1), min(tp, cp + 2)):
            tokens.append(str(p))
        if cp < tp - 2:
            tokens.append("...")
        tokens.append(str(tp))
        return tokens

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

    # --- COMPUTED VARS: DETAIL DRAWER ---

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
    def active_nama_title(self) -> str:
        return str(self._get_active_entry().get("nama", ""))

    @rx.var(cache=True)
    def active_jenis_badge(self) -> str:
        return str(self._get_active_entry().get("jenis", "Fisik"))

    @rx.var(cache=True)
    def active_status_badge(self) -> str:
        item = self._get_active_entry()
        if item.get("is_conflict"):
            return "Bentrok"
        return str(item.get("status", "Aktif"))

    @rx.var(cache=True)
    def active_general_items(self) -> list[dict[str, str]]:
        """Grup 1 Drawer: Data Entri IP & Server (Tanpa Grup)."""
        item = self._get_active_entry()
        if not item:
            return []
        return [
            {"label": "ID Entri", "value": str(item.get("id", "—"))},
            {"label": "IP Address", "value": str(item.get("ip_address", "—"))},
            {"label": "Subnet (/24)", "value": str(item.get("subnet", "—"))},
            {"label": "Nama Server / VM", "value": str(item.get("nama", "—"))},
            {"label": "Jenis", "value": str(item.get("jenis", "—"))},
            {"label": "Host", "value": str(item.get("host_display", item.get("host_label", "—")))},
            {"label": "Fungsi", "value": str(item.get("fungsi", "—"))},
            {"label": "Operating System", "value": str(item.get("os", "—"))},
            {"label": "Status", "value": str(item.get("status", "—"))},
            {"label": "Keterangan / Kendala", "value": str(item.get("keterangan", "—"))},
        ]

    @rx.var(cache=True)
    def active_relation_items(self) -> list[dict[str, str]]:
        """Grup 2 Drawer: Relasi Aset Fisik atau Daftar VM yang berjalan di Host ini."""
        item = self._get_active_entry()
        if not item:
            return []
        jenis = str(item.get("jenis", "Fisik"))
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
                "value": f"Terhubung ke server fisik {host_id}"
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
                "event": f"Alokasi IP {item.get('ip_address', '')} untuk {item.get('nama', '')}",
                "date": "06 Nov 2026",
                "note": f"Jenis: {item.get('jenis', '')} · Status: {item.get('status', 'Aktif')}",
            }
        ]

    # --- NORMALISASI BARIS TABEL (SUB-TEKS & KENDALA) ---

    @staticmethod
    def _enrich_row_for_view(raw: dict[str, Any]) -> dict[str, Any]:
        """Pastikan setiap baris memiliki informasi kendala, sub_label, dan host_display."""
        item = dict(raw)
        jenis = str(item.get("jenis", "Fisik")).strip() or "Fisik"
        ket_raw = str(item.get("keterangan", "")).strip()
        has_kendala = bool(ket_raw and ket_raw != "—")
        item["has_kendala"] = has_kendala
        item["kendala_label"] = "● Ada kendala (lihat keterangan)" if has_kendala else ""
        item["kendala_tooltip"] = ket_raw if has_kendala else ""

        asset_id = str(item.get("asset_id", "")).strip()
        host_id = str(item.get("host_asset_id", "")).strip()
        host_label = str(item.get("host_label", "")).strip()

        if jenis == "Fisik":
            base_sub = f"Aset: {asset_id}" if asset_id and asset_id != "—" else "Server / PC Fisik"
            host_col = "—"
        else:
            if host_id and host_id != "—":
                base_sub = f"Host: {host_id}"
                host_col = host_label if (host_label and host_label != "Tanpa host") else host_id
            else:
                base_sub = "Tanpa host"
                host_col = "Tanpa host"

        item["base_sub_label"] = base_sub
        item["sub_label"] = "● Ada kendala (lihat keterangan)" if has_kendala else base_sub
        item["host_display"] = host_col
        item["jenis_variant"] = "info" if jenis == "VM" else "neutral"
        return item

    # --- EVENT HANDLERS: FETCH & FILTER ---

    @rx.event
    async def load_ip_page(self) -> None:
        await self.fetch_ip_entries()

    @rx.event
    async def fetch_ip_entries(self) -> None:
        self.is_loading = True
        effective_jenis = (
            self.jenis_filter
            if self.jenis_filter
            else (self.active_jenis_tab if self.active_jenis_tab in ("Fisik", "VM") else "")
        )
        filters: dict[str, Any] = {
            "search": self.search_query,
            "jenis": effective_jenis,
            "host": self.host_filter,
            "subnet": self.subnet_filter,
            "status": self.status_filter,
            "only_conflict": self.only_conflict_filter,
            "only_orphan_vm": self.only_orphan_vm_filter,
            "sort_by": self.sort_by,
            "sort_dir": self.sort_dir,
        }
        res = await api_client.get_ip_entries(
            grup="Semua",
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        raw_items = res.get("items", [])
        self.items = [self._enrich_row_for_view(r) for r in raw_items]
        self.total = int(res.get("total", 0))

        kpi = res.get("kpi", {})
        total_ip = int(kpi.get("total_ip", self.total))
        fisik_cnt = int(kpi.get("fisik", kpi.get("operasional", 0)))
        vm_cnt = int(kpi.get("vm", kpi.get("addon", 0)))
        if fisik_cnt == 0 and vm_cnt == 0 and raw_items:
            fisik_cnt = sum(1 for x in raw_items if x.get("jenis") == "Fisik")
            vm_cnt = sum(1 for x in raw_items if x.get("jenis") == "VM")

        self.kpi_total_ip = total_ip
        self.kpi_fisik = fisik_cnt
        self.kpi_vm = vm_cnt
        self.kpi_bentrok = int(kpi.get("bentrok", 0))
        self.kpi_vm_tanpa_host = int(kpi.get("vm_tanpa_host", 0))
        self.conflict_banner_text = str(res.get("conflict_banner", ""))
        self.subnet_options = res.get("subnet_options", [])
        self.host_options = res.get("host_options", [])
        self.server_asset_ids = res.get("server_asset_ids", ["SRV-0001", "SRV-0002"])
        self.os_suggestions = res.get("os_suggestions", [])
        self.is_loading = False

    @rx.event
    async def set_jenis_tab(self, tab_key: str) -> None:
        """Ganti tab Semua / Fisik / VM."""
        if self.active_jenis_tab == tab_key:
            return
        self.active_jenis_tab = tab_key
        self.jenis_filter = "" if tab_key == "Semua" else tab_key
        self.page = 1
        self.selected_ids = []
        await self.fetch_ip_entries()

    @rx.event
    async def set_grup_tab(self, tab_key: str) -> None:
        """Alias kompatibilitas menuju set_jenis_tab."""
        mapped = "Fisik" if tab_key == "Operasional" else ("VM" if "Addon" in tab_key else tab_key)
        await self.set_jenis_tab(mapped)

    @rx.event
    async def set_search_query(self, val: str) -> None:
        if self.search_query == val:
            return
        self.search_query = val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_jenis_filter(self, val: str) -> None:
        clean_val = "" if val in ("Semua", "Semua jenis") else val
        if self.jenis_filter == clean_val:
            return
        self.jenis_filter = clean_val
        self.active_jenis_tab = clean_val if clean_val in ("Fisik", "VM") else "Semua"
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_host_filter(self, val: str) -> None:
        clean_val = "" if val in ("Semua", "Semua host") else val
        if self.host_filter == clean_val:
            return
        self.host_filter = clean_val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_subnet_filter(self, val: str) -> None:
        clean_val = "" if val in ("Semua", "Semua subnet") else val
        if self.subnet_filter == clean_val:
            return
        self.subnet_filter = clean_val
        self.page = 1
        await self.fetch_ip_entries()

    @rx.event
    async def set_status_filter(self, val: str) -> None:
        clean_val = "" if val in ("Semua", "Semua status") else val
        if self.status_filter == clean_val:
            return
        self.status_filter = clean_val
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
            if 1 <= target <= self.total_pages and target != self.page:
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
        if self.drawer_open:
            self.drawer_open = False

    @rx.event
    def set_drawer_tab(self, tab_key: str) -> None:
        if self.drawer_tab != tab_key:
            self.drawer_tab = tab_key

    # --- EVENT HANDLERS: POPUP FORM TAMBAH / EDIT / DUPLIKAT ---

    @rx.event
    def open_add_modal(self) -> None:
        self.form_mode = "add"
        self.form_entry_id = ""
        self.form_error = ""
        self.form_ip_address = ""
        self.form_nama = ""
        default_jenis = "VM" if self.active_jenis_tab == "VM" else "Fisik"
        self.form_jenis = default_jenis
        self.form_asset_id = ""
        self.form_host_asset_id = (
            (self.server_asset_ids[0] if self.server_asset_ids else "SRV-0001")
            if default_jenis == "VM"
            else ""
        )
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
        self.form_nama = str(item.get("nama", ""))
        jenis = str(item.get("jenis", "Fisik"))
        self.form_jenis = jenis if jenis in ("Fisik", "VM") else "Fisik"
        self.form_asset_id = str(item.get("asset_id", "")) if self.form_jenis == "Fisik" else ""
        self.form_host_asset_id = (
            str(item.get("host_asset_id", "")) if self.form_jenis == "VM" else ""
        )
        fungsi = str(item.get("fungsi", ""))
        self.form_fungsi = "" if fungsi == "—" else fungsi
        os_val = str(item.get("os", ""))
        self.form_os = "" if os_val == "—" else os_val
        self.form_status = str(item.get("status", "Aktif"))
        ket = str(item.get("keterangan", ""))
        self.form_keterangan = "" if ket == "—" else ket
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
    def set_form_nama(self, val: str) -> None:
        self.form_nama = val

    @rx.event
    def set_form_jenis(self, val: str) -> None:
        """Jika kembali ke Fisik: sembunyikan dan kosongkan nilai Host Server Fisik."""
        self.form_jenis = val
        if val == "Fisik":
            self.form_host_asset_id = ""
        else:
            self.form_asset_id = ""

    @rx.event
    def set_form_asset_id(self, val: str) -> None:
        self.form_asset_id = val

    @rx.event
    def set_form_host_asset_id(self, val: str) -> None:
        self.form_host_asset_id = val

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
        """Validasi urutan field baru: IPv4, Nama, Jenis, Host (wajib jika VM), Status."""
        self.form_error = ""
        ip = self.form_ip_address.strip()
        nama = self.form_nama.strip()
        jenis = self.form_jenis.strip()
        status_val = self.form_status.strip() or "Aktif"

        if not ip:
            self.form_error = "IP Address (IPv4) wajib diisi."
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

        if jenis not in ("Fisik", "VM"):
            self.form_error = "Jenis harus berupa Fisik atau VM."
            return None

        host_id = self.form_host_asset_id.strip() if jenis == "VM" else ""
        if jenis == "VM" and not host_id:
            self.form_error = "Host Server Fisik wajib dipilih untuk entri berjenis VM."
            return None

        if status_val not in ("Aktif", "Nonaktif"):
            self.form_error = "Status harus Aktif atau Nonaktif."
            return None

        derived_grup = "Addon (VM)" if jenis == "VM" else "Operasional"
        return {
            "ip_address": ip,
            "nama": nama,
            "jenis": jenis,
            "asset_id": self.form_asset_id.strip() if jenis == "Fisik" else "",
            "host_asset_id": host_id,
            "grup": derived_grup,
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

    # --- EVENT HANDLERS: IMPORT (3 LANGKAH) & EXPORT (EXCEL / PDF) ---

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
        self.import_valid_rows = []
        self.import_errors = []

    @rx.event
    async def download_import_template(self) -> Any:
        """Unduh file template .xlsx dengan header baku, 1 baris contoh, & dropdown validasi."""
        content_bytes = await api_client.get_ip_import_template_bytes()
        return rx.download(
            data=content_bytes,
            filename="Template_Import_IP_Server_ITAM_Pro.xlsx",
        )

    @rx.event
    async def handle_import_upload(self, files: list[rx.UploadFile]) -> None:
        """Proses unggahan file .xlsx atau .csv (maks 5 MB) dan tampilkan preview validasi."""
        if not files:
            return
        upload_file = files[0]
        fname = upload_file.filename or "data_ip.xlsx"
        raw_bytes = await upload_file.read()

        self.import_filename = fname
        if len(raw_bytes) > 5 * 1024 * 1024:
            self.import_has_preview = True
            self.import_valid_rows = []
            self.import_errors = [{"row": 0, "reason": "Ukuran file melebihi batas 5 MB"}]
            self.import_summary_text = "0 baris valid · 1 error (Ukuran file > 5 MB)"
            return

        preview = await api_client.preview_ip_import_bytes(
            file_bytes=raw_bytes,
            filename=fname,
            valid_hosts=self.server_asset_ids,
        )
        self.import_valid_rows = preview["valid_rows"]
        self.import_errors = preview["errors"]
        self.import_has_preview = True

        v_cnt = len(self.import_valid_rows)
        e_cnt = len(self.import_errors)
        if e_cnt > 0:
            first_err = self.import_errors[0]
            self.import_error_detail_text = (
                f"({first_err['reason']}, baris {first_err['row']}) — baris error dilewati."
            )
            self.import_summary_text = f"{v_cnt} baris valid · {e_cnt} baris error"
        else:
            self.import_error_detail_text = "— seluruh baris siap diimpor."
            self.import_summary_text = f"{v_cnt} baris valid · 0 baris error"

    @rx.event
    def download_import_error_report(self) -> Any:
        """Unduh laporan baris error dalam format CSV."""
        if not self.import_errors:
            return None
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Baris", "IP Address", "Nama Server/VM", "Alasan Error"])
        for err in self.import_errors:
            writer.writerow(
                [
                    err.get("row", ""),
                    err.get("ip_address", ""),
                    err.get("nama", ""),
                    err.get("reason", ""),
                ]
            )
        return rx.download(
            data=buf.getvalue().encode("utf-8-sig"),
            filename="Laporan_Error_Import_IP.csv",
        )

    @rx.event
    async def commit_import_data(self) -> Any:
        """Simpan seluruh baris valid hasil preview ke sistem."""
        if not self.import_valid_rows:
            return None
        count = len(self.import_valid_rows)
        for row_payload in self.import_valid_rows:
            await api_client.create_ip_entry(payload=row_payload)
        self.close_import_modal()
        await self.fetch_ip_entries()
        return rx.toast.success(
            f"Berhasil mengimpor {count} data IP & Server (VM).",
            position="top-right",
        )

    async def _collect_filtered_for_export(self) -> list[dict[str, Any]]:
        """Ambil seluruh entri sesuai filter aktif dan urutkan secara numerik IPv4."""
        effective_jenis = (
            self.jenis_filter
            if self.jenis_filter
            else (self.active_jenis_tab if self.active_jenis_tab in ("Fisik", "VM") else "")
        )
        filters: dict[str, Any] = {
            "search": self.search_query,
            "jenis": effective_jenis,
            "host": self.host_filter,
            "subnet": self.subnet_filter,
            "status": self.status_filter,
            "only_conflict": self.only_conflict_filter,
            "only_orphan_vm": self.only_orphan_vm_filter,
            "sort_by": "ip_address",
            "sort_dir": "asc",
        }
        res = await api_client.get_ip_entries(
            grup="Semua",
            filters=filters,
            page=1,
            page_size=5000,
        )
        rows = [self._enrich_row_for_view(r) for r in res.get("items", [])]
        rows.sort(key=lambda r: _ipv4_sort_tuple(str(r.get("ip_address", ""))))
        return rows

    @rx.event
    async def export_excel(self) -> Any:
        """Ekspor daftar IP aktif ke file Excel (.xlsx) terformat."""
        rows = await self._collect_filtered_for_export()
        xlsx_bytes = await api_client.generate_ip_excel_bytes(rows)
        today_str = datetime.now().strftime("%Y%m%d")
        return rx.download(
            data=xlsx_bytes,
            filename=f"Daftar_IP_Server_VM_{today_str}.xlsx",
        )

    @rx.event
    async def export_pdf(self) -> Any:
        """Ekspor daftar IP aktif ke file PDF A4 Landscape."""
        rows = await self._collect_filtered_for_export()
        now = datetime.now()
        tgl_indo = f"{now.day} {MONTHS_ID[now.month]} {now.year}"
        pdf_bytes = await api_client.generate_ip_pdf_bytes(
            rows=rows,
            export_date_label=tgl_indo,
            exporter_name="Administrator IT",
        )
        today_str = now.strftime("%Y%m%d")
        return rx.download(
            data=pdf_bytes,
            filename=f"Daftar_IP_Server_VM_{today_str}.pdf",
        )

    # --- EVENT HANDLERS: HAPUS ENTRI ---

    @rx.event
    def confirm_delete_entry(self, row_id: str) -> None:
        target = row_id or self.active_entry_id
        for item in self.items:
            if item.get("id") == target:
                self.entry_to_delete = target
                ip_val = item.get("ip_address", "")
                nama_val = item.get("nama", "")
                self.entry_to_delete_label = f"{ip_val} · {nama_val}"
                self.delete_dialog_open = True
                return

    @rx.event
    def cancel_delete(self) -> None:
        if self.delete_dialog_open:
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
