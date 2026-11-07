"""
State Modul Infrastructure -> IP & Server (VM).
Mendukung field Pengguna, Kategori (IP Operasional, IP Server, IP VM),
serta ekspor/impor teroptimasi.
"""

import csv
import html
import io
import json
import math
import time
from datetime import datetime
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.mock.ip_mock import (
    REGISTERED_SUBNET_CIDR,
    has_kendala,
    is_ip_in_registered_subnet,
)
from itam_pro.styles.colors import Color

# C2: Cache sisi client (TTL 45 detik) untuk deduplikasi & perpindahan instan Tabel <-> Peta IP
_CLIENT_LIST_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CLIENT_MAP_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CLIENT_CACHE_TTL = 45.0


def _invalidate_client_ip_cache() -> None:
    _CLIENT_LIST_CACHE.clear()
    _CLIENT_MAP_CACHE.clear()


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
    active_subnet: str = REGISTERED_SUBNET_CIDR
    subnet_options: list[str] = [REGISTERED_SUBNET_CIDR]
    subnets_list: list[dict[str, Any]] = [
        {"id": 1, "cidr": REGISTERED_SUBNET_CIDR, "nama": "Subnet Utama LAN"}
    ]
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
    host_server_options: list[str] = ["SRV-0001 (SRV-PROXMOX-01)", "SRV-0002 (SRV-ZABBIX-MON)"]
    server_asset_ids: list[str] = ["SRV-0001", "SRV-0002"]
    os_suggestions: list[str] = []
    _search_seq: int = 0

    # B2: State Modal Cetak Data IP (Artboard 6)
    print_modal_open: bool = False
    print_is_loading: bool = False
    print_follow_filter: bool = True
    print_col_ip: bool = True
    print_col_pengguna: bool = True
    print_col_jenis: bool = True
    print_col_host: bool = True
    print_col_kategori: bool = True
    print_col_fungsi: bool = True
    print_col_os: bool = True
    print_col_status: bool = True
    print_col_keterangan: bool = False  # Default tidak dicentang (data internal)
    print_rows: list[dict[str, Any]] = []
    print_filter_label: str = "Semua Data"
    print_date_label: str = ""
    print_user_label: str = "Administrator IT"

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
    def used_subnet_percent(self) -> int:
        used = max(0, 254 - self.kpi_kosong_count)
        return min(100, round((used / 254) * 100))

    @rx.var(cache=True)
    def has_multiple_subnets(self) -> bool:
        return len(self.subnets_list) > 1

    @rx.var(cache=True)
    def has_connected_vm_hosts(self) -> bool:
        """A3: True jika ada minimal 1 host yang memiliki VM terhubung."""
        return any(h not in ("", "Semua", "Semua host") for h in self.host_options)

    @rx.var(cache=True)
    def clean_host_options(self) -> list[str]:
        """A3: Daftar opsi host unik tanpa duplikasi 'Semua host'."""
        return [h for h in self.host_options if h not in ("", "Semua", "Semua host")]

    @rx.var(cache=True)
    def active_stat_card(self) -> str:
        """B3: Penanda kartu statistik aktif ('total'|'fisik'|'vm'|'kosong'|'bentrok')."""
        if self.view_mode == "map":
            return "kosong"
        if self.only_conflict_filter:
            return "bentrok"
        if self.active_jenis_tab == "Fisik" or self.jenis_filter == "Fisik":
            return "fisik"
        if self.active_jenis_tab == "VM" or self.jenis_filter == "VM":
            return "vm"
        return "total"

    @rx.var(cache=True)
    def import_total_count(self) -> int:
        return len(self.import_valid_rows) + len(self.import_errors)

    @rx.var(cache=True)
    def import_preview_rows(self) -> list[dict[str, Any]]:
        """B1: Error ditampilkan lebih dulu (latar merah muda), diikuti baris valid."""
        err_items = [
            {
                "row": str(e.get("row") or e.get("row_number") or "—"),
                "ip_address": str(e.get("ip_address") or "—"),
                "pengguna": str(e.get("nama") or e.get("pengguna") or "—"),
                "jenis": str(e.get("jenis") or "—"),
                "status_label": str(e.get("reason") or "Error validasi"),
                "is_error": True,
            }
            for e in self.import_errors
        ]
        val_items = [
            {
                "row": str(r.get("row") or idx),
                "ip_address": str(r.get("ip_address") or "—"),
                "pengguna": str(
                    r.get("pengguna") or r.get("nama_perangkat") or r.get("nama") or "—"
                ),
                "jenis": str(r.get("jenis") or r.get("tipe") or "Fisik"),
                "status_label": "Siap diimpor",
                "is_error": False,
            }
            for idx, r in enumerate(self.import_valid_rows, start=1)
        ]
        return (err_items + val_items)[:50]

    @rx.var(cache=True)
    def print_preview_rows(self) -> list[dict[str, Any]]:
        return self.print_rows[:12]

    @rx.var(cache=True)
    def print_total_count(self) -> int:
        return len(self.print_rows)

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
        """A2: Gunakan helper has_kendala yang sama dengan tabel dan Peta IP."""
        entry = self._get_active_entry()
        return has_kendala(entry)

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
        ip_str = str(item.get("ip_address", "")).strip()
        jenis = str(item.get("jenis", "Fisik")).strip() or "Fisik"
        fungsi_val = str(item.get("fungsi") or "").strip()
        ket_raw = str(item.get("keterangan") or "").strip()

        # A2: Konsisten menggunakan satu helper has_kendala
        kendala = has_kendala(ket_raw, fungsi_val)
        outside_subnet = bool(
            item.get("is_outside_subnet") or (ip_str and not is_ip_in_registered_subnet(ip_str))
        )
        item["has_kendala"] = kendala
        item["is_outside_subnet"] = outside_subnet
        item["keterangan"] = ket_raw if kendala else ""

        item["pengguna"] = str(item.get("pengguna") or item.get("nama") or "—").strip() or "—"
        item["nama"] = str(item.get("nama") or item["pengguna"])
        item["kategori"] = str(item.get("kategori") or "IP Operasional").strip() or "IP Operasional"

        host_id = str(item.get("host_asset_id") or item.get("id_aset_host") or "").strip()
        host_label = str(item.get("host_label") or "").strip()

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

        if kendala:
            item["sub_label"] = "● Ada kendala (lihat keterangan)"
        elif outside_subnet:
            item["sub_label"] = f"{base_sub} · Di luar subnet"
        else:
            item["sub_label"] = base_sub

        item["host_display"] = host_col
        return item

    def _build_url_query_script(self) -> Any:
        """B3: Sinkronkan state view & jenis ke query string browser tanpa reload halaman."""
        v_param = "map" if self.view_mode == "map" else "table"
        j_param = "all"
        if self.active_jenis_tab == "Fisik" or self.jenis_filter == "Fisik":
            j_param = "fisik"
        elif self.active_jenis_tab == "VM" or self.jenis_filter == "VM":
            j_param = "vm"
        return rx.call_script(
            "window.history.replaceState("
            f"null, '', '/infrastructure/ip?view={v_param}&jenis={j_param}');"
        )

    @rx.event
    async def load_ip_page(self) -> Any:
        """B3 & C2: Baca query string (?view=table|map&jenis=all|fisik|vm) saat halaman dibuka."""
        params = self.router.page.params or {}
        q_view = str(params.get("view", "")).strip().lower()
        q_jenis = str(params.get("jenis", "")).strip().lower()

        if q_view in ("table", "map"):
            self.view_mode = q_view
        if q_jenis == "fisik":
            self.active_jenis_tab = "Fisik"
            self.jenis_filter = "Fisik"
        elif q_jenis == "vm":
            self.active_jenis_tab = "VM"
            self.jenis_filter = "VM"
        elif q_jenis == "all":
            self.active_jenis_tab = "Semua"
            self.jenis_filter = ""

        await self.fetch_ip_entries()
        if self.view_mode == "map":
            await self.fetch_ip_map()

    @rx.event
    async def set_view_mode(self, mode: str) -> Any:
        if self.view_mode == mode:
            return None
        self.view_mode = mode
        if mode == "map" and not self.map_cells:
            await self.fetch_ip_map()
        return self._build_url_query_script()

    @rx.event
    async def click_stat_card(self, card_key: str) -> Any:
        """B3: Handler interaktif untuk kelima Stats Card."""
        if card_key == "bentrok" and self.kpi_bentrok <= 0:
            return None

        self.page = 1
        self.search_query = ""
        self.selected_ids = []

        if card_key == "kosong":
            self.view_mode = "map"
            self.only_conflict_filter = False
            if not self.map_cells:
                await self.fetch_ip_map()
        elif card_key == "bentrok":
            self.view_mode = "table"
            self.only_conflict_filter = not self.only_conflict_filter
            self.only_orphan_vm_filter = False
            self.active_jenis_tab = "Semua"
            self.jenis_filter = ""
            await self.fetch_ip_entries()
        elif card_key == "fisik":
            self.view_mode = "table"
            self.only_conflict_filter = False
            self.only_orphan_vm_filter = False
            self.active_jenis_tab = "Fisik"
            self.jenis_filter = "Fisik"
            await self.fetch_ip_entries()
        elif card_key == "vm":
            self.view_mode = "table"
            self.only_conflict_filter = False
            self.only_orphan_vm_filter = False
            self.active_jenis_tab = "VM"
            self.jenis_filter = "VM"
            await self.fetch_ip_entries()
        else:
            # Total IP
            self.view_mode = "table"
            self.only_conflict_filter = False
            self.only_orphan_vm_filter = False
            self.active_jenis_tab = "Semua"
            self.jenis_filter = ""
            await self.fetch_ip_entries()

        v_param = "map" if self.view_mode == "map" else "table"
        j_param = (
            "fisik"
            if self.active_jenis_tab == "Fisik"
            else ("vm" if self.active_jenis_tab == "VM" else "all")
        )
        return rx.call_script(
            "window.history.replaceState("
            f"null, '', '/infrastructure/ip?view={v_param}&jenis={j_param}');"
            "if (window.innerWidth < 900) {"
            "  var el = document.getElementById('ip-main-content-card');"
            "  if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});"
            "}"
        )

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
        now = time.time()
        cache_key = self.active_subnet or "1"
        cached = _CLIENT_MAP_CACHE.get(cache_key)
        if cached and (now - cached[0]) < _CLIENT_CACHE_TTL:
            res = cached[1]
        else:
            res = await api_client.get_ip_map(cache_key)
            _CLIENT_MAP_CACHE[cache_key] = (now, res)

        self.map_cells = res.get("cells", [])
        raw_stats = res.get("stats", {})
        fisik_c = int(raw_stats.get("fisik", 0) or 0)
        vm_c = int(raw_stats.get("vm", 0) or 0)
        bentrok_c = int(raw_stats.get("bentrok", 0) or 0)
        kosong_c = int(raw_stats.get("kosong", max(0, 254 - self.total)) or 0)
        # A4: Pastikan bentrok dan persentase tidak pernah undefined
        self.map_stats = {
            **raw_stats,
            "fisik": fisik_c,
            "vm": vm_c,
            "bentrok": bentrok_c,
            "kosong": kosong_c,
            "fisik_percent": raw_stats.get("fisik_percent", round((fisik_c / 254) * 100, 1)),
            "vm_percent": raw_stats.get("vm_percent", round((vm_c / 254) * 100, 1)),
            "bentrok_percent": raw_stats.get("bentrok_percent", round((bentrok_c / 254) * 100, 1)),
            "kosong_percent": raw_stats.get("kosong_percent", round((kosong_c / 254) * 100, 1)),
        }
        self.map_suggested_ips = res.get("suggested_ips", [])
        self.map_largest_empty_range = res.get("largest_empty_range", "")
        self.kpi_kosong_count = kosong_c
        if res.get("subnets"):
            self.subnets_list = res["subnets"]

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
        cache_key = f"{self.page}:{self.page_size}:{sorted(filters.items())}"
        now = time.time()
        cached = _CLIENT_LIST_CACHE.get(cache_key)

        if cached and (now - cached[0]) < _CLIENT_CACHE_TTL:
            res = cached[1]
        else:
            if not self.items:
                self.is_loading = True
            req_token = self._search_seq
            res = await api_client.get_ip_entries(
                grup="Semua", filters=filters, page=self.page, page_size=self.page_size
            )
            if req_token != self._search_seq:
                self.is_loading = False
                return
            _CLIENT_LIST_CACHE[cache_key] = (now, res)

        raw_items = res.get("items", [])
        self.items = [self._enrich_row_for_view(r) for r in raw_items]
        self.total = int(res.get("total", 0))

        kpi = res.get("kpi", {})
        self.kpi_total_ip = int(kpi.get("total_ip", self.total))
        self.kpi_fisik = int(
            kpi.get("fisik", sum(1 for x in raw_items if x.get("jenis") == "Fisik"))
        )
        self.kpi_vm = int(kpi.get("vm", sum(1 for x in raw_items if x.get("jenis") == "VM")))
        self.kpi_bentrok = int(kpi.get("bentrok", 0) or 0)
        self.kpi_vm_tanpa_host = int(kpi.get("vm_tanpa_host", 0) or 0)
        self.kpi_kosong_count = int(kpi.get("kosong", max(0, 254 - self.total)))
        self.conflict_banner_text = str(res.get("conflict_banner", ""))
        self.host_options = [
            h
            for h in res.get("host_options", [])
            if h not in ("", "Semua", "Semua host", "Tanpa host")
        ]
        if res.get("host_server_options"):
            self.host_server_options = res["host_server_options"]
        self.server_asset_ids = [
            s for s in res.get("server_asset_ids", ["SRV-0001", "SRV-0002"]) if s not in ("", "—")
        ]
        self.os_suggestions = res.get("os_suggestions", [])
        if res.get("subnets"):
            self.subnets_list = res["subnets"]
        self.is_loading = False

    @rx.event
    async def set_jenis_tab(self, tab_key: str) -> Any:
        if self.active_jenis_tab == tab_key and self.view_mode == "table":
            return None
        self.view_mode = "table"
        self.active_jenis_tab = tab_key
        self.jenis_filter = "" if tab_key == "Semua" else tab_key
        self.only_conflict_filter = False
        self.page = 1
        self.selected_ids = []
        await self.fetch_ip_entries()
        return self._build_url_query_script()

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
        self._search_seq += 1
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
        if not api_client.validate_ipv4_sync(ip):
            self.form_error = f"Format alamat IPv4 '{ip}' tidak valid."
            return None

        # B4: Tolak IP di luar subnet terdaftar (192.168.1.0/24) saat Tambah atau IP diubah
        existing_ip = ""
        if self.form_mode == "edit":
            for it in self.items:
                if str(it.get("id")) == str(self.form_entry_id):
                    existing_ip = str(it.get("ip_address", "")).strip()
                    break
        if (self.form_mode != "edit" or ip != existing_ip) and not is_ip_in_registered_subnet(ip):
            self.form_error = "IP di luar subnet terdaftar (192.168.1.0/24)"
            return None

        exclude_id = self.form_entry_id if self.form_mode == "edit" else ""
        dup_owner = api_client.check_ip_duplicate_sync(ip, exclude_id=exclude_id)
        if dup_owner and status_val.lower() not in ("nonaktif", "bebas"):
            self.form_error = f"IP sudah dipakai oleh {dup_owner}"
            return None
        if not pengguna:
            self.form_error = "Pengguna wajib diisi."
            return None

        host_raw = self.form_host_asset_id.strip() if jenis == "VM" else ""
        host_code = host_raw.split(" ")[0].strip() if host_raw else ""
        if jenis == "VM" and not host_code:
            self.form_error = "Host Server Fisik wajib dipilih untuk entri berjenis VM."
            return None

        fungsi_clean = self.form_fungsi.strip()
        ket_raw = self.form_keterangan.strip()
        # A2: Normalisasi keterangan kosong/spasi atau identik fungsi
        ket_clean = ket_raw if has_kendala(ket_raw, fungsi_clean) else ""

        return {
            "ip_address": ip,
            "nama": pengguna,
            "nama_perangkat": pengguna,
            "pengguna": pengguna,
            "jenis": jenis,
            "tipe": jenis,
            "is_vm": jenis == "VM",
            "host_asset_id": host_code,
            "id_aset_host": host_code or None,
            "kategori": self.form_kategori,
            "fungsi": fungsi_clean,
            "os": self.form_os.strip(),
            "status": status_val,
            "keterangan": ket_clean,
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
        _invalidate_client_ip_cache()
        await self.fetch_ip_entries()
        if self.view_mode == "map":
            await self.fetch_ip_map()

    @rx.event
    async def save_and_add_another(self) -> None:
        payload = self._validate_and_build_payload()
        if payload is None:
            return
        await api_client.create_ip_entry(payload=payload)
        _invalidate_client_ip_cache()
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
        self.import_filename = fname
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
        _invalidate_client_ip_cache()
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
        _invalidate_client_ip_cache()
        await self.fetch_ip_entries()
        if self.view_mode == "map":
            await self.fetch_ip_map()

    @rx.event
    def clear_import_file(self) -> None:
        """B1: Ganti file pada modal Import."""
        self.import_filename = ""
        self.import_id = ""
        self.import_valid_rows = []
        self.import_errors = []
        self.import_has_preview = False

    @rx.event
    async def open_print_modal(self) -> None:
        """B2: Buka modal Cetak Data IP & muat pratinjau baris sesuai filter aktif."""
        self.print_modal_open = True
        self.print_is_loading = True
        now = datetime.now()
        self.print_date_label = (
            f"{now.day} {MONTHS_ID[now.month]} {now.year}, {now.strftime('%H:%M')} WIB"
        )
        await self._refresh_print_preview_rows(record_log=False)
        self.print_is_loading = False

    @rx.event
    def close_print_modal(self) -> None:
        self.print_modal_open = False

    @rx.event
    async def toggle_print_follow_filter(self) -> None:
        self.print_follow_filter = not self.print_follow_filter
        await self._refresh_print_preview_rows(record_log=False)

    @rx.event
    def toggle_print_col(self, col_name: str) -> None:
        attr_name = f"print_col_{col_name}"
        if hasattr(self, attr_name):
            setattr(self, attr_name, not getattr(self, attr_name))

    async def _refresh_print_preview_rows(self, record_log: bool = False) -> None:
        if self.print_follow_filter:
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
        else:
            filters = {}

        res = await api_client.get_ip_print_data(filters=filters, record_log=record_log)
        raw_rows = res.get("items", [])
        self.print_rows = [self._enrich_row_for_view(r) for r in raw_rows]
        self.print_filter_label = str(res.get("filter_label") or "Semua Data")

    def _get_selected_print_columns(self) -> list[tuple[str, str]]:
        cols: list[tuple[str, str]] = [("no", "No")]
        if self.print_col_ip:
            cols.append(("ip_address", "IP Address"))
        if self.print_col_pengguna:
            cols.append(("pengguna", "Pengguna"))
        if self.print_col_jenis:
            cols.append(("jenis", "Jenis"))
        if self.print_col_host:
            cols.append(("host", "Host"))
        if self.print_col_kategori:
            cols.append(("kategori", "Kategori"))
        if self.print_col_fungsi:
            cols.append(("fungsi", "Fungsi"))
        if self.print_col_os:
            cols.append(("os", "OS"))
        if self.print_col_status:
            cols.append(("status", "Status"))
        if self.print_col_keterangan:
            cols.append(("keterangan", "Keterangan"))
        return cols

    @rx.event
    async def download_print_pdf(self) -> Any:
        """B2: Unduh PDF sesuai kolom yang dicentang di modal Cetak."""
        await self._refresh_print_preview_rows(record_log=True)
        now = datetime.now()
        tgl = f"{now.day} {MONTHS_ID[now.month]} {now.year}"
        sel_keys = [k for k, _ in self._get_selected_print_columns()]
        pdf_bytes = await api_client.generate_ip_pdf_bytes(
            self.print_rows, tgl, self.print_user_label, selected_columns=sel_keys
        )
        return rx.download(data=pdf_bytes, filename=f"Cetak_IP_{now.strftime('%Y%m%d')}.pdf")

    @rx.event
    async def execute_direct_print(self) -> Any:
        """B2: Ambil baris (maks 5.000), catat Audit Log, & panggil window.print()."""
        await self._refresh_print_preview_rows(record_log=True)
        if len(self.print_rows) > 5000:
            return rx.toast.warning(
                "Data melebihi 5.000 baris. Gunakan Export Excel/PDF.",
                position="top-right",
            )

        cols = self._get_selected_print_columns()
        th_html = "".join(f"<th>{html.escape(label)}</th>" for _, label in cols)
        tr_list: list[str] = []
        for idx, r in enumerate(self.print_rows, start=1):
            tds: list[str] = []
            for key, _ in cols:
                if key == "no":
                    tds.append(f"<td>{idx}</td>")
                elif key == "ip_address":
                    tds.append(
                        f"<td class='mono'>{html.escape(str(r.get('ip_address', '—')))}</td>"
                    )
                elif key == "jenis":
                    jv = str(r.get("jenis", "Fisik"))
                    cls = "chip-vm" if jv == "VM" else "chip-fisik"
                    tds.append(f"<td><span class='chip {cls}'>{html.escape(jv)}</span></td>")
                elif key == "host":
                    tds.append(f"<td>{html.escape(str(r.get('host_display', '—')))}</td>")
                elif key == "status":
                    sv = str(r.get("status", "Aktif"))
                    cls = "st-aktif" if sv.lower() == "aktif" else "st-nonaktif"
                    tds.append(f"<td><span class='chip {cls}'>{html.escape(sv)}</span></td>")
                else:
                    val = str(r.get(key) or "—")
                    tds.append(f"<td>{html.escape(val)}</td>")
            tr_list.append(f"<tr>{''.join(tds)}</tr>")

        sub_esc = html.escape(self.active_subnet)
        flt_esc = html.escape(self.print_filter_label)
        dt_esc = html.escape(self.print_date_label)
        usr_esc = html.escape(self.print_user_label)
        total_cnt = len(self.print_rows)

        doc_html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
            "<title>Daftar IP & Server (VM) - ITAM Pro</title><style>"
            "@page { size: A4 landscape; margin: 12mm; }"
            "* { box-sizing: border-box; -webkit-print-color-adjust: exact !important; "
            "print-color-adjust: exact !important; }"
            "body { font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "
            f"sans-serif; font-size: 10.5px; color: {Color.NAVY_900}; margin: 0; padding: 0; }}"
            ".hdr { display: flex; justify-content: space-between; align-items: flex-start; "
            f"margin-bottom: 12px; border-bottom: 2px solid {Color.NAVY_900}; "
            "padding-bottom: 8px; }"
            f".hdr h1 {{ font-size: 16px; margin: 0 0 4px 0; color: {Color.NAVY_900}; }}"
            f".hdr .meta {{ font-size: 10px; color: {Color.NEUTRAL_FG}; }}"
            f".brand {{ font-size: 12px; font-weight: 800; color: {Color.ACCENT}; }}"
            "table { width: 100%; border-collapse: collapse; }"
            "thead { display: table-header-group; }"
            "tr { break-inside: avoid; page-break-inside: avoid; }"
            f"th {{ background-color: {Color.NAVY_900} !important; "
            f"color: {Color.WHITE} !important; text-align: left; padding: 6px 8px; "
            "font-size: 10px; font-weight: 700; }"
            f"td {{ padding: 5px 8px; border-bottom: 1px solid {Color.SLATE_200}; "
            "vertical-align: top; }"
            f"tbody tr:nth-child(even) {{ background-color: {Color.SLATE_50} !important; }}"
            ".mono { font-family: ui-monospace, monospace; font-weight: 700; "
            f"color: {Color.ACCENT}; }}"
            ".chip { display: inline-block; padding: 2px 6px; border-radius: 999px; "
            "font-size: 9.5px; font-weight: 700; }"
            f".chip-fisik {{ background: {Color.BLUE_100} !important; "
            f"color: {Color.ACCENT} !important; }}"
            f".chip-vm {{ background: {Color.PURPLE_100} !important; "
            f"color: {Color.PURPLE_700} !important; }}"
            f".st-aktif {{ background: {Color.GREEN_100} !important; "
            f"color: {Color.GREEN_700} !important; }}"
            f".st-nonaktif {{ background: {Color.RED_100} !important; "
            f"color: {Color.RED_700} !important; }}"
            "</style></head><body><div class='hdr'><div>"
            "<h1>Daftar IP &amp; Server (VM)</h1>"
            f"<div class='meta'>Subnet: {sub_esc} &middot; Filter: {flt_esc} "
            f"&middot; Total: {total_cnt} entri</div>"
            f"<div class='meta'>Dicetak: {dt_esc} &middot; Pengguna: {usr_esc}</div>"
            "</div><div class='brand'>ITAM Pro</div></div>"
            f"<table><thead><tr>{th_html}</tr></thead>"
            f"<tbody>{''.join(tr_list)}</tbody></table></body></html>"
        )

        escaped_doc = json.dumps(doc_html)
        js_print = f"""
        (function() {{
            var oldFrame = document.getElementById('itam-ip-print-frame');
            if (oldFrame) oldFrame.remove();
            var iframe = document.createElement('iframe');
            iframe.id = 'itam-ip-print-frame';
            iframe.style.position = 'fixed';
            iframe.style.right = '0';
            iframe.style.bottom = '0';
            iframe.style.width = '0';
            iframe.style.height = '0';
            iframe.style.border = '0';
            document.body.appendChild(iframe);
            var doc = iframe.contentWindow.document;
            doc.open();
            doc.write({escaped_doc});
            doc.close();
            setTimeout(function() {{
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
            }}, 250);
        }})();
        """
        self.print_modal_open = False
        return rx.call_script(js_print)


__all__ = ["IPState"]
