"""
State Generik Inventaris Aset ITAM Pro (Tahap 6c-1).
Menangani halaman `/assets` (Semua Aset) dan `/assets/c/[slug]` (View Kategori)
berdasarkan konfigurasi di `services/category_config.py`.
Dioptimalkan dengan @rx.var(cache=True) & O(1) short-circuit lookup.
"""

import json
import math
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.category_config import (
    CATEGORY_CONFIGS,
    DEFAULT_HIDDEN_COLUMNS_BY_SLUG,
    CategoryFieldDef,
    get_config_by_slug,
    get_config_for_category_name,
)
from itam_pro.services.mock.master_data import (
    MASTER_JENIS_PC,
    MASTER_KATEGORI,
    MASTER_KEPEMILIKAN,
    MASTER_KONDISI,
    MASTER_KONEKTIVITAS_MONITOR,
    MASTER_LOKASI,
    MASTER_MERK_MONITOR,
    MASTER_RESOLUSI_MONITOR,
    MASTER_STATUS,
    MASTER_UKURAN_MONITOR,
)
from itam_pro.services.mock.seed import format_ukuran_layar
from itam_pro.services.router_utils import get_current_params, get_current_raw_path
from itam_pro.services.validators import validate_asset_business_rules


class AssetState(rx.State):
    """State tunggal untuk seluruh tampilan inventaris aset dan DynamicForm."""

    # Konteks kelompok utama & subkategori saat ini
    active_group: str = "all"
    current_slug: str = ""
    active_kpi_card: str = "total"  # "total" | "attention" | "warranty" | "no_purchase"
    is_loading: bool = False

    # Data tabel & paginasi
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 10

    # Tab & Sort
    active_tab: str = ""
    tab_counts: dict[str, int] = {}
    sort_by: str = ""
    sort_dir: str = "asc"

    # Counts seragam untuk Kartu, Baris Kategori, dan Sidebar (Seksi 7 & 8)
    sidebar_counts: dict[str, int] = {
        "all": 77,
        "pc": 33,
        "server": 16,
        "monitor": 4,
        "ups": 24,
        "perangkat-it": 77,
        "komponen-periferal": 0,
        "jaringan": 0,
        "kendaraan": 0,
        "peralatan-kantor": 0,
        "furnitur": 0,
        "lainnya": 0,
    }
    summary_counts: dict[str, int] = {
        "total": 77,
        "perlu_perhatian": 7,
        "garansi_segera_habis": 5,
        "belum_terhubung_pembelian": 41,
    }

    # Filter Inti
    search_query: str = ""
    kategori_filter: str = ""
    kepemilikan_filter: str = ""
    lokasi_filter: str = ""
    kondisi_filter: str = ""
    status_filter: str = ""
    pengguna_filter: str = ""
    warranty_filter: str = ""
    no_purchase_filter: int = 0

    # Filter Atribut Kategori
    attr_filters: dict[str, str] = {}

    column_prefs_json: str = rx.LocalStorage("{}", name="itam_asset_col_prefs")

    @rx.var(cache=True)
    def hidden_columns(self) -> list[str]:
        """Daftar key kolom yang disembunyikan untuk view saat ini (disimpan di LocalStorage)."""
        try:
            prefs = json.loads(self.column_prefs_json or "{}")
        except ValueError:
            prefs = {}
        slug_key = self.current_slug or "all"
        if slug_key in prefs and isinstance(prefs[slug_key], list):
            return [str(x) for x in prefs[slug_key]]
        return list(DEFAULT_HIDDEN_COLUMNS_BY_SLUG.get(self.current_slug, []))

    def toggle_column_visibility(self, col_key: str, _checked: Any = None) -> None:
        try:
            prefs = json.loads(self.column_prefs_json or "{}")
        except ValueError:
            prefs = {}
        slug_key = self.current_slug or "all"
        current_hidden = list(self.hidden_columns)
        if col_key in current_hidden:
            current_hidden = [k for k in current_hidden if k != col_key]
        else:
            current_hidden.append(col_key)
        prefs[slug_key] = current_hidden
        self.column_prefs_json = json.dumps(prefs)

    def reset_column_visibility(self) -> None:
        try:
            prefs = json.loads(self.column_prefs_json or "{}")
        except ValueError:
            prefs = {}
        slug_key = self.current_slug or "all"
        prefs[slug_key] = list(DEFAULT_HIDDEN_COLUMNS_BY_SLUG.get(self.current_slug, []))
        self.column_prefs_json = json.dumps(prefs)

    # Pilihan baris & Detail Drawer
    selected_ids: list[str] = []
    active_asset_id: str = ""
    drawer_open: bool = False
    drawer_tab: str = "detail"

    # Modal DynamicForm (Tambah / Edit / Duplikat)
    form_modal_open: bool = False
    form_mode: str = "add"  # "add" | "edit"
    form_category_locked: bool = False
    form_error: str = ""
    form_sn_warning: str = ""

    # Field Inti pada Form
    form_id_aset: str = ""
    form_nama_aset: str = ""
    form_kategori: str = "PC"
    form_sn_pid: str = ""
    form_tanggal_masuk: str = "2026-10-22"
    form_tanggal_keluar: str = ""
    form_kepemilikan: str = "XML"
    form_lokasi: str = "Kantor Blok 14"
    form_kondisi: str = "Baru"
    form_status: str = "Digunakan"
    form_digunakan_oleh: str = ""
    form_catatan: str = ""
    form_duplicate_count: str = "1"
    duplicate_count_form: int = 1

    # Field Spesifikasi Kategori pada Form (disimpan ke asset.attributes)
    form_attributes: dict[str, str] = {}
    form_konektivitas: list[str] = ["HDMI"]

    # Master options dinamis (mendukung combobox tambah Merk/Resolusi baru)
    custom_merk_options: list[str] = list(MASTER_MERK_MONITOR)
    custom_resolusi_options: list[str] = list(MASTER_RESOLUSI_MONITOR)

    # Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    asset_to_delete: str = ""
    asset_to_delete_label: str = ""

    # --- STATE FASE 2: DETAIL ASET (/assets/[id]), SERAH TERIMA, QR, & RELASI ---
    detail_asset_id: str = ""
    detail_tab: str = "ringkasan"
    detail_asset: dict[str, Any] = {}
    detail_monitors: list[dict[str, str]] = []
    detail_power_links: list[dict[str, str]] = []
    detail_ips: list[dict[str, Any]] = []
    detail_credentials: list[dict[str, str]] = []
    detail_credentials_summary: str = "Belum ada kredensial tertaut"
    detail_purchase: dict[str, Any] = {}
    detail_has_purchase: bool = False
    detail_maintenances: list[dict[str, str]] = []
    detail_movements: list[dict[str, str]] = []

    # Modal Serahkan / Pindahkan
    handover_modal_open: bool = False
    handover_jenis: str = "serah_terima"
    handover_pengguna: str = ""
    handover_lokasi: str = "Head Office (Office Blok 14)"
    handover_status: str = "Digunakan"
    handover_alasan: str = "Serah terima operasional"
    handover_tanggal: str = "2026-11-09"
    handover_catatan: str = ""

    # Modal Cetak Label QR
    qr_modal_open: bool = False

    # Modal Hubungkan Monitor / UPS
    link_modal_open: bool = False
    link_target_id: str = ""

    # --- STATE FASE 3: KOMPONEN PER UNIT (ARTBOARD 12) ---
    comp_is_tracked: bool = True
    comp_ram_summary_chip: str = "RAM total 16 GB · 2 modul"
    comp_storage_summary_chip: str = "Storage total 512 GB · 1 disk"
    comp_installed_list: list[dict[str, Any]] = []
    comp_spare_list: list[dict[str, Any]] = []
    comp_pc_targets: list[str] = ["PC-016 — PC CS H2H", "PC-001 — PC IT TIO"]

    # Modal Pindahkan / Pasang / Lepas Komponen (Artboard 12 Kanan)
    comp_modal_open: bool = False
    comp_modal_id: str = ""
    comp_modal_subtitle: str = ""
    comp_modal_is_disk: bool = False
    comp_modal_action: str = "pindah"  # "pindah" | "lepas" | "rusak" | "pasang"
    comp_modal_target_pc: str = "PC-016 — PC CS H2H"
    comp_modal_slot: str = "DIMM 2"
    comp_modal_alasan: str = "Upgrade RAM PC tujuan"
    comp_modal_tanggal: str = "2026-11-09"
    comp_modal_catatan: str = ""
    comp_modal_lokasi_cadangan: str = "Gudang"
    comp_modal_confirm_wipe: bool = False
    comp_modal_error: str = ""
    comp_modal_warning: str = ""
    comp_modal_impacts: list[dict[str, str]] = [
        {"label": "PC-003 RAM", "change": "16 GB -> 8 GB"},
        {"label": "PC-016 RAM", "change": "8 GB -> 16 GB"},
    ]

    # --- COMPUTED VARS: KONTEKS HALAMAN & HEADER ---

    @rx.var(cache=True)
    def page_title(self) -> str:
        cfg = get_config_by_slug(self.current_slug)
        if cfg:
            return cfg["name"]
        return "Semua Aset"

    @rx.var(cache=True)
    def page_subtitle(self) -> str:
        cfg = get_config_by_slug(self.current_slug)
        if cfg and cfg.get("subtitle"):
            return cfg["subtitle"]
        return "Kelola seluruh unit fisik perangkat keras IT dalam satu basis data terpadu."

    @rx.var(cache=True)
    def add_button_label(self) -> str:
        cfg = get_config_by_slug(self.current_slug)
        if cfg and cfg.get("add_button_label"):
            return cfg["add_button_label"]
        return "+ Tambah Aset"

    @rx.var(cache=True)
    def breadcrumb_title(self) -> str:
        cfg = get_config_by_slug(self.current_slug)
        return cfg["name"] if cfg else "Semua Aset"

    @rx.var(cache=True)
    def has_tabs(self) -> bool:
        cfg = get_config_by_slug(self.current_slug)
        return bool(cfg and cfg.get("tab_field"))

    @rx.var(cache=True)
    def current_tabs(self) -> list[dict[str, Any]]:
        cfg = get_config_by_slug(self.current_slug)
        if not cfg or not cfg.get("tab_field"):
            return []
        result: list[dict[str, Any]] = []
        for opt in cfg.get("tab_options", []):
            result.append(
                {
                    "key": opt,
                    "label": opt,
                    "count": self.tab_counts.get(opt, 0),
                }
            )
        return result

    # --- COMPUTED VARS: MASTER OPTIONS ---

    @rx.var(cache=True)
    def master_kategori_options(self) -> list[str]:
        if self.form_category_locked and self.current_slug == "pc":
            return ["PC", "Server"]
        return list(MASTER_KATEGORI)

    @rx.var(cache=True)
    def master_kepemilikan_options(self) -> list[str]:
        return list(MASTER_KEPEMILIKAN)

    @rx.var(cache=True)
    def master_lokasi_options(self) -> list[str]:
        return list(MASTER_LOKASI)

    @rx.var(cache=True)
    def master_kondisi_options(self) -> list[str]:
        return list(MASTER_KONDISI)

    @rx.var(cache=True)
    def master_status_options(self) -> list[str]:
        return list(MASTER_STATUS)

    @rx.var(cache=True)
    def master_jenis_pc_options(self) -> list[str]:
        return list(MASTER_JENIS_PC)

    @rx.var(cache=True)
    def master_merk_options(self) -> list[str]:
        return self.custom_merk_options

    @rx.var(cache=True)
    def master_ukuran_options(self) -> list[str]:
        return list(MASTER_UKURAN_MONITOR)

    @rx.var(cache=True)
    def master_resolusi_options(self) -> list[str]:
        return self.custom_resolusi_options

    @rx.var(cache=True)
    def master_konektivitas_options(self) -> list[str]:
        return list(MASTER_KONEKTIVITAS_MONITOR)

    @rx.var(cache=True)
    def os_filter_options(self) -> list[str]:
        return [
            "Windows 11 Pro",
            "Windows 10 Pro",
            "Proxmox VE 8.2",
            "Ubuntu Server 24.04 LTS",
        ]

    @rx.var(cache=True)
    def ram_filter_options(self) -> list[str]:
        return ["8 GB DDR4", "16 GB DDR4", "32 GB DDR4", "64 GB ECC DDR4"]

    # --- COMPUTED VARS: FILTER ATTRIBUT & TABEL ---

    @rx.var(cache=True)
    def filter_os_value(self) -> str:
        return self.attr_filters.get("os", "")

    @rx.var(cache=True)
    def filter_ram_value(self) -> str:
        return self.attr_filters.get("ram", "")

    @rx.var(cache=True)
    def filter_merk_value(self) -> str:
        return self.attr_filters.get("merk", "")

    @rx.var(cache=True)
    def filter_ukuran_value(self) -> str:
        return self.attr_filters.get("ukuran_layar", "")

    @rx.var(cache=True)
    def filter_resolusi_value(self) -> str:
        return self.attr_filters.get("resolusi_layar", "")

    @rx.var(cache=True)
    def filter_konektivitas_value(self) -> str:
        return self.attr_filters.get("konektivitas", "")

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total} unit"

    @rx.var(cache=True)
    def all_current_selected(self) -> bool:
        if not self.items or not self.selected_ids:
            return False
        selected_set = set(self.selected_ids)
        return all(item.get("id_aset") in selected_set for item in self.items)

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
        return f"Menampilkan {start}-{end} dari {self.total}"

    @rx.var(cache=True)
    def empty_state_title(self) -> str:
        return f"Tidak ada data pada {self.page_title}"

    @rx.var(cache=True)
    def empty_state_subtitle(self) -> str:
        return "Coba ubah kata kunci pencarian atau atur ulang kriteria filter Anda."

    @rx.var(cache=True)
    def empty_state_action_label(self) -> str:
        return "Reset filter"

    # --- COMPUTED VARS: DETAIL DRAWER ---

    def _get_active_item(self) -> dict[str, Any]:
        if not self.active_asset_id or not self.items:
            return {}
        target = self.active_asset_id
        for item in self.items:
            if item.get("id_aset") == target:
                return item
        return {}

    @rx.var(cache=True)
    def active_code(self) -> str:
        return str(self._get_active_item().get("id_aset", ""))

    @rx.var(cache=True)
    def active_title(self) -> str:
        return str(self._get_active_item().get("nama_aset", ""))

    @rx.var(cache=True)
    def active_category(self) -> str:
        return str(self._get_active_item().get("kategori", ""))

    @rx.var(cache=True)
    def active_condition(self) -> str:
        return str(self._get_active_item().get("kondisi", "Baru"))

    @rx.var(cache=True)
    def active_status(self) -> str:
        return str(self._get_active_item().get("status", "Digunakan"))

    @rx.var(cache=True)
    def active_asset_data_items(self) -> list[dict[str, str]]:
        """Grup 1 pada Drawer: Data aset (inti)."""
        item = self._get_active_item()
        if not item:
            return []
        return [
            {"label": "ID Aset", "value": str(item.get("id_aset", "—"))},
            {"label": "Nama Aset", "value": str(item.get("nama_aset", "—"))},
            {"label": "Kategori", "value": str(item.get("kategori", "—"))},
            {"label": "SN / PID", "value": str(item.get("sn_pid", "—"))},
            {"label": "Kepemilikan", "value": str(item.get("kepemilikan", "—"))},
            {"label": "Lokasi", "value": str(item.get("lokasi", "—"))},
            {"label": "Kondisi", "value": str(item.get("kondisi", "—"))},
            {"label": "Status", "value": str(item.get("status", "—"))},
            {"label": "Digunakan Oleh", "value": str(item.get("digunakan_oleh", "—"))},
            {"label": "Tgl Masuk Gudang", "value": str(item.get("tanggal_masuk_display", "—"))},
            {"label": "Tgl Keluar Gudang", "value": str(item.get("tanggal_keluar_display", "—"))},
            {"label": "Catatan", "value": str(item.get("catatan", "—"))},
        ]

    @rx.var(cache=True)
    def active_spec_items(self) -> list[dict[str, str]]:
        """Grup 2 pada Drawer: Spesifikasi (dibangun dinamis dari category_config)."""
        item = self._get_active_item()
        if not item:
            return []
        kategori = str(item.get("kategori", ""))
        cfg = get_config_for_category_name(kategori)
        if not cfg or not cfg["fields"]:
            return [{"label": "Spesifikasi Khusus", "value": "Tidak ada atribut khusus"}]

        attrs: dict[str, Any] = item.get("attributes") or {}
        rows: list[dict[str, str]] = []
        for f_def in cfg["fields"]:
            if f_def["type"] == "multiselect":
                continue
            key = f_def["key"]
            raw_val = attrs.get(key, "")
            if key == "ukuran_layar":
                val_str = format_ukuran_layar(raw_val)
            else:
                val_str = str(raw_val).strip() if raw_val else "—"
            rows.append({"label": f_def["label"], "value": val_str})
        return rows

    @rx.var(cache=True)
    def active_chips_items(self) -> list[str]:
        """Daftar chip untuk field multiselect (mis. Konektivitas Monitor)."""
        item = self._get_active_item()
        if not item:
            return []
        attrs: dict[str, Any] = item.get("attributes") or {}
        kon = attrs.get("konektivitas")
        if isinstance(kon, list):
            return [str(x) for x in kon]
        return []

    @rx.var(cache=True)
    def active_has_chips(self) -> bool:
        return len(self.active_chips_items) > 0

    @rx.var(cache=True)
    def active_maintenance_logs(self) -> list[dict[str, Any]]:
        item = self._get_active_item()
        if not item:
            return []
        code = str(item.get("id_aset", ""))
        from itam_pro.services.mock.maintenance_mock import MOCK_MAINTENANCE_LOGS

        return [log for log in MOCK_MAINTENANCE_LOGS if log.get("objek_asset_id") == code]

    @rx.var(cache=True)
    def active_history_info(self) -> list[dict[str, str]]:
        item = self._get_active_item()
        if not item:
            return []
        code = str(item.get("id_aset", ""))
        tgl = str(item.get("tanggal_masuk_display", "10 Jan 2025"))
        return [
            {
                "event": f"Aset {code} terdaftar di sistem",
                "date": tgl if tgl != "—" else "10 Jan 2025",
                "note": (
                    f"Lokasi: {item.get('lokasi', '—')} · Pemilik: {item.get('kepemilikan', '—')}"
                ),
            }
        ]

    # --- COMPUTED VARS: DYNAMIC FORM ---

    @rx.var(cache=True)
    def form_active_category_slug(self) -> str:
        cfg = get_config_for_category_name(self.form_kategori)
        return cfg["slug"] if cfg else ""

    @rx.var(cache=True)
    def form_has_spec_section(self) -> bool:
        cfg = get_config_for_category_name(self.form_kategori)
        return bool(cfg and len(cfg["fields"]) > 0)

    @rx.var(cache=True)
    def form_spec_fields(self) -> list[CategoryFieldDef]:
        cfg = get_config_for_category_name(self.form_kategori)
        return cfg["fields"] if cfg else []

    @rx.var(cache=True)
    def form_is_digunakan(self) -> bool:
        return self.form_status == "Digunakan"

    # --- EVENT HANDLERS: LOAD & NAVIGASI ---

    def _resolve_slug_from_router(self) -> str:
        params = get_current_params(self.router)
        slug = str(params.get("category") or params.get("slug") or "").strip().lower()
        path = get_current_raw_path(self.router)
        if not slug and "/assets/c/" in path:
            slug = path.split("/assets/c/", 1)[1].strip("/").lower()
        return slug if slug in CATEGORY_CONFIGS else ""

    @rx.event
    def redirect_legacy_category_route(self) -> Any:
        """Redirect 301 dari /assets/c/[slug] ke /assets?category=[slug] (Seksi 8)."""
        slug = self._resolve_slug_from_router()
        if slug:
            return rx.redirect(f"/assets?category={slug}")
        return rx.redirect("/assets")

    @rx.event
    async def load_view_data(self) -> None:
        """Dipanggil saat halaman /assets dimuat dengan membaca query string."""
        params = get_current_params(self.router)
        new_slug = self._resolve_slug_from_router()
        self.current_slug = new_slug
        if new_slug in ("pc", "server", "monitor", "ups"):
            self.active_group = "perangkat-it"
        elif new_slug == "":
            self.active_group = str(params.get("group", "all")).strip().lower() or "all"

        param_status = str(params.get("status", "")).strip()
        param_kategori = str(params.get("kategori", "")).strip()
        param_warranty = str(params.get("warranty", "")).strip()
        param_no_purchase = str(params.get("no_purchase", "")).strip()

        self.status_filter = param_status
        self.kategori_filter = param_kategori
        self.warranty_filter = param_warranty
        self.no_purchase_filter = 1 if param_no_purchase == "1" else 0

        if param_status in ("attention", "perlu_perhatian"):
            self.active_kpi_card = "attention"
        elif param_warranty == "expiring":
            self.active_kpi_card = "warranty"
        elif param_no_purchase == "1":
            self.active_kpi_card = "no_purchase"
        else:
            self.active_kpi_card = "total"

        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def select_kpi_card(self, card_key: str) -> None:
        """Klik salah satu dari 4 kartu KPI di Semua Aset (Artboard 10)."""
        self.active_kpi_card = card_key
        self.page = 1
        if card_key == "attention":
            self.status_filter = "attention"
            self.warranty_filter = ""
            self.no_purchase_filter = 0
        elif card_key == "warranty":
            self.status_filter = ""
            self.warranty_filter = "expiring"
            self.no_purchase_filter = 0
        elif card_key == "no_purchase":
            self.status_filter = ""
            self.warranty_filter = ""
            self.no_purchase_filter = 1
        else:
            self.status_filter = ""
            self.warranty_filter = ""
            self.no_purchase_filter = 0
        await self.fetch_assets()

    @rx.event
    async def select_category_group(self, group_key: str) -> None:
        """Klik kelompok kategori utama pada baris kategori (Artboard 10)."""
        self.active_group = group_key
        self.current_slug = ""
        self.kategori_filter = ""
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def select_subcategory(self, sub_slug: str) -> None:
        """Klik pill subkategori (misal Semua Perangkat IT, PC & Laptop, Server, Monitor, UPS)."""
        self.current_slug = sub_slug
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def set_pengguna_filter(self, val: str) -> None:
        if self.pengguna_filter == val:
            return
        self.pengguna_filter = val
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def fetch_assets(self) -> None:
        """Ambil daftar aset dari api_client.get_assets sesuai filter aktif."""
        self.is_loading = True
        filters: dict[str, Any] = {
            "slug": self.current_slug,
            "category": self.current_slug,
            "group": "" if self.active_group == "all" else self.active_group,
            "tab": self.active_tab,
            "search": self.search_query,
            "kategori": self.kategori_filter,
            "kepemilikan": self.kepemilikan_filter,
            "lokasi": self.lokasi_filter,
            "pengguna": self.pengguna_filter,
            "kondisi": self.kondisi_filter,
            "status": self.status_filter,
            "warranty": self.warranty_filter,
            "no_purchase": self.no_purchase_filter if self.no_purchase_filter else None,
            "attr_filters": self.attr_filters,
            "sort_by": self.sort_by,
            "sort_dir": self.sort_dir,
        }
        res = await api_client.get_assets(
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        self.items = res.get("items", [])
        self.total = int(res.get("total", 0))
        self.tab_counts = res.get("tab_counts", {})
        if "category_counts" in res and isinstance(res["category_counts"], dict):
            self.sidebar_counts = {**self.sidebar_counts, **res["category_counts"]}
        if "summary" in res and isinstance(res["summary"], dict):
            self.summary_counts = {**self.summary_counts, **res["summary"]}
        self.is_loading = False

    # --- EVENT HANDLERS: TAB, FILTER, SORT, PAGINASI ---

    @rx.event
    async def set_tab(self, tab_key: str) -> None:
        if self.active_tab == tab_key:
            return
        self.active_tab = tab_key
        self.page = 1
        self.selected_ids = []
        await self.fetch_assets()

    @rx.event
    async def set_search_query(self, val: str) -> None:
        if self.search_query == val:
            return
        self.search_query = val
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def set_kategori_filter(self, val: str) -> None:
        if self.kategori_filter == val:
            return
        self.kategori_filter = val
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def set_kepemilikan_filter(self, val: str) -> None:
        if self.kepemilikan_filter == val:
            return
        self.kepemilikan_filter = val
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def set_lokasi_filter(self, val: str) -> None:
        if self.lokasi_filter == val:
            return
        self.lokasi_filter = val
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def set_kondisi_filter(self, val: str) -> None:
        if self.kondisi_filter == val:
            return
        self.kondisi_filter = val
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def set_status_filter(self, val: str) -> None:
        if self.status_filter == val:
            return
        self.status_filter = val
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def set_attr_filter(self, key: str, val: str) -> None:
        if self.attr_filters.get(key) == val:
            return
        updated = dict(self.attr_filters)
        updated[key] = val
        self.attr_filters = updated
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.kategori_filter = ""
        self.kepemilikan_filter = ""
        self.lokasi_filter = ""
        self.pengguna_filter = ""
        self.kondisi_filter = ""
        self.status_filter = ""
        self.warranty_filter = ""
        self.no_purchase_filter = 0
        self.active_kpi_card = "total"
        self.attr_filters = {}
        self.page = 1
        await self.fetch_assets()

    @rx.event
    async def toggle_sort(self, col_key: str) -> None:
        if self.sort_by == col_key:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_by = col_key
            self.sort_dir = "asc"
        await self.fetch_assets()

    @rx.event
    async def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self.fetch_assets()

    @rx.event
    async def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self.fetch_assets()

    @rx.event
    async def select_page(self, token: str) -> None:
        if token.isdigit():
            target = int(token)
            if 1 <= target <= self.total_pages and target != self.page:
                self.page = target
                await self.fetch_assets()

    # --- EVENT HANDLERS: PILIHAN BARIS & DRAWER ---

    @rx.event
    def toggle_row_selection(self, row_id: str, _checked: Any = None) -> None:
        if row_id in self.selected_ids:
            self.selected_ids = [x for x in self.selected_ids if x != row_id]
        else:
            self.selected_ids = [*self.selected_ids, row_id]

    @rx.event
    def toggle_select_all(self, _checked: Any = None) -> None:
        current_ids = [str(item["id_aset"]) for item in self.items]
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
        self.active_asset_id = row_id
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

    # --- EVENT HANDLERS: DYNAMIC FORM MODAL ---

    def _init_default_attributes(self, kategori: str) -> None:
        if kategori in ("PC", "Server"):
            jenis_default = (
                "Server"
                if kategori == "Server"
                else (self.active_tab if self.active_tab in MASTER_JENIS_PC else "Operasional")
            )
            self.form_attributes = {
                "jenis": jenis_default,
                "os": "Windows 11 Pro" if kategori == "PC" else "Ubuntu Server 24.04 LTS",
                "ram": "16 GB DDR4",
                "vga": "",
                "cpu": "",
                "mainboard": "",
                "hdd_ssd": "",
                "monitor": "",
                "keyboard": "",
                "mouse": "",
            }
        elif kategori == "Monitor":
            self.form_attributes = {
                "merk": "LG",
                "tipe_model": "",
                "ukuran_layar": "24",
                "resolusi_layar": "1920 × 1080",
            }
            self.form_konektivitas = ["HDMI"]
        else:
            self.form_attributes = {}
            self.form_konektivitas = []

    @rx.event
    def open_add_modal(self) -> None:
        self.form_mode = "add"
        self.form_error = ""
        self.form_sn_warning = ""
        self.form_duplicate_count = "1"
        self.duplicate_count_form = 1

        cfg = get_config_by_slug(self.current_slug)
        if cfg:
            self.form_category_locked = True
            default_cat = (
                "Server"
                if (self.current_slug == "pc" and self.active_tab == "Server")
                else cfg["included_categories"][0]
            )
            self.form_kategori = default_cat
        else:
            self.form_category_locked = False
            self.form_kategori = "PC"

        self.form_id_aset = api_client.peek_next_id_sync(self.form_kategori)
        self.form_nama_aset = ""
        self.form_sn_pid = ""
        self.form_tanggal_masuk = "2026-10-22"
        self.form_tanggal_keluar = ""
        self.form_kepemilikan = "XML"
        self.form_lokasi = "Kantor Blok 14"
        self.form_kondisi = "Baru"
        self.form_status = "Backup" if self.active_tab == "Backup" else "Digunakan"
        self.form_digunakan_oleh = ""
        self.form_catatan = ""
        self._init_default_attributes(self.form_kategori)
        self.form_modal_open = True

    def _populate_form_from_item(self, item: dict[str, Any], mode: str) -> None:
        self.form_mode = mode
        self.form_error = ""
        self.form_duplicate_count = "1"
        self.duplicate_count_form = 1
        kategori = str(item.get("kategori", "PC"))
        self.form_kategori = kategori
        self.form_category_locked = self.current_slug != ""

        if mode == "edit":
            self.form_id_aset = str(item.get("id_aset", ""))
            self.form_nama_aset = str(item.get("nama_aset", ""))
        else:
            self.form_id_aset = api_client.peek_next_id_sync(kategori)
            self.form_nama_aset = str(item.get("nama_aset", ""))

        sn_val = str(item.get("sn_pid", ""))
        self.form_sn_pid = "" if sn_val == "—" else sn_val
        self.form_tanggal_masuk = str(item.get("tanggal_masuk_gudang", ""))
        self.form_tanggal_keluar = str(item.get("tanggal_keluar_gudang", ""))
        self.form_kepemilikan = str(item.get("kepemilikan", "XML"))
        self.form_lokasi = str(item.get("lokasi", "Kantor Blok 14"))
        self.form_kondisi = str(item.get("kondisi", "Baru"))
        self.form_status = str(item.get("status", "Digunakan"))
        user_val = str(item.get("digunakan_oleh", ""))
        self.form_digunakan_oleh = "" if user_val == "—" else user_val
        cat_val = str(item.get("catatan", ""))
        self.form_catatan = "" if cat_val == "—" else cat_val

        attrs: dict[str, Any] = item.get("attributes") or {}
        str_attrs: dict[str, str] = {}
        for k, v in attrs.items():
            if k == "konektivitas" and isinstance(v, list):
                self.form_konektivitas = [str(x) for x in v]
            else:
                str_attrs[k] = "" if str(v) == "—" else str(v)
        self.form_attributes = str_attrs
        self._check_sn_warning()
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str) -> None:
        target_id = row_id or self.active_asset_id
        for item in self.items:
            if item.get("id_aset") == target_id:
                self._populate_form_from_item(item, mode="edit")
                return

    @rx.event
    def open_duplicate_modal(self, row_id: str) -> None:
        target_id = row_id or self.active_asset_id
        for item in self.items:
            if item.get("id_aset") == target_id:
                self._populate_form_from_item(item, mode="add")
                return

    @rx.event
    def edit_active_asset(self) -> None:
        """Buka modal edit untuk aset aktif di detail drawer."""
        self.open_edit_modal(self.active_asset_id)

    @rx.event
    def duplicate_active_asset(self) -> None:
        """Buka modal duplikat untuk aset aktif di detail drawer."""
        self.open_duplicate_modal(self.active_asset_id)

    @rx.event
    def close_form_modal(self) -> None:
        if self.form_modal_open:
            self.form_modal_open = False
        self.form_error = ""
        self.form_sn_warning = ""

    @rx.event
    def set_form_kategori(self, val: str) -> None:
        self.form_kategori = val
        if self.form_mode == "add":
            self.form_id_aset = api_client.peek_next_id_sync(val)
        self._init_default_attributes(val)

    @rx.event
    def set_form_nama_aset(self, val: str) -> None:
        self.form_nama_aset = val

    def _check_sn_warning(self) -> None:
        exclude = self.form_id_aset if self.form_mode == "edit" else ""
        dup_id = api_client.check_sn_duplicate_sync(self.form_sn_pid, exclude_id=exclude)
        if dup_id:
            self.form_sn_warning = f"SN/PID ini sudah dipakai oleh {dup_id}"
        else:
            self.form_sn_warning = ""

    @rx.event
    def set_form_sn_pid(self, val: str) -> None:
        self.form_sn_pid = val
        self._check_sn_warning()

    @rx.event
    def set_form_tanggal_masuk(self, val: str) -> None:
        self.form_tanggal_masuk = val

    @rx.event
    def set_form_tanggal_keluar(self, val: str) -> None:
        self.form_tanggal_keluar = val

    @rx.event
    def set_form_kepemilikan(self, val: str) -> None:
        self.form_kepemilikan = val

    @rx.event
    def set_form_lokasi(self, val: str) -> None:
        self.form_lokasi = val

    @rx.event
    def set_form_kondisi(self, val: str) -> None:
        self.form_kondisi = val

    @rx.event
    def set_form_status(self, val: str) -> None:
        self.form_status = val
        if val == "Tidak Digunakan":
            self.form_digunakan_oleh = ""

    @rx.event
    def set_form_digunakan_oleh(self, val: str) -> None:
        self.form_digunakan_oleh = val

    @rx.event
    def set_form_catatan(self, val: str) -> None:
        self.form_catatan = val

    @rx.event
    def set_duplicate_count(self, value: str | float | int) -> None:
        """Atur jumlah unit dengan validasi ketat (maksimal 50)."""
        try:
            count = int(float(value)) if isinstance(value, (float, str)) else int(value)
            if count < 1:
                count = 1
            elif count > 50:
                count = 50
            self.duplicate_count_form = count
        except (ValueError, TypeError):
            self.duplicate_count_form = 1
        self.form_duplicate_count = str(self.duplicate_count_form)

    @rx.event
    def set_form_duplicate_count(self, val: str | float | int) -> None:
        self.set_duplicate_count(val)

    @rx.event
    def set_form_attr(self, key: str, val: str) -> None:
        updated = dict(self.form_attributes)
        updated[key] = val
        self.form_attributes = updated

    @rx.event
    def toggle_form_konektivitas(self, port: str, _checked: Any = None) -> None:
        if port in self.form_konektivitas:
            self.form_konektivitas = [p for p in self.form_konektivitas if p != port]
        else:
            self.form_konektivitas = [*self.form_konektivitas, port]

    def _validate_and_build_payload(self) -> dict[str, Any] | None:
        """Validasi field inti + field dinamis kategori sesuai aturan bisnis."""
        self.form_error = ""
        kat = self.form_kategori

        biz_err = validate_asset_business_rules(
            {
                "kategori": kat,
                "nama_aset": self.form_nama_aset,
                "status": self.form_status,
                "digunakan_oleh": self.form_digunakan_oleh,
                "tanggal_masuk_gudang": self.form_tanggal_masuk,
                "tanggal_keluar_gudang": self.form_tanggal_keluar,
            }
        )
        if biz_err:
            self.form_error = biz_err
            return None

        cfg = get_config_for_category_name(kat)
        attrs: dict[str, Any] = dict(self.form_attributes)
        if cfg:
            for f_def in cfg["fields"]:
                k = f_def["key"]
                if f_def["type"] == "multiselect":
                    if f_def["required"] and not self.form_konektivitas:
                        self.form_error = f"Pilih minimal satu {f_def['label']}."
                        return None
                    attrs[k] = list(self.form_konektivitas)
                elif f_def["required"] and not str(attrs.get(k, "")).strip():
                    self.form_error = f"Field '{f_def['label']}' wajib diisi."
                    return None

        if kat == "Monitor":
            merk = str(attrs.get("merk", "")).strip()
            res = str(attrs.get("resolusi_layar", "")).strip()
            if merk and merk not in self.custom_merk_options:
                self.custom_merk_options = [*self.custom_merk_options, merk]
            if res and res not in self.custom_resolusi_options:
                self.custom_resolusi_options = [*self.custom_resolusi_options, res]

        nama_final = self.form_nama_aset.strip()
        if kat == "Monitor" and not nama_final:
            merk = str(attrs.get("merk", "")).strip()
            tipe = str(attrs.get("tipe_model", "")).strip()
            ukuran = format_ukuran_layar(attrs.get("ukuran_layar", ""))
            nama_final = f"{merk} {tipe} {ukuran}".strip()

        return {
            "nama_aset": nama_final,
            "kategori": kat,
            "sn_pid": self.form_sn_pid.strip(),
            "tanggal_masuk_gudang": self.form_tanggal_masuk.strip(),
            "tanggal_keluar_gudang": self.form_tanggal_keluar.strip(),
            "kepemilikan": self.form_kepemilikan,
            "lokasi": self.form_lokasi,
            "kondisi": self.form_kondisi,
            "status": self.form_status,
            "digunakan_oleh": (
                "" if self.form_status == "Tidak Digunakan" else self.form_digunakan_oleh.strip()
            ),
            "catatan": self.form_catatan.strip(),
            "attributes": attrs,
        }

    @rx.event
    async def save_asset_form(self) -> None:
        payload = self._validate_and_build_payload()
        if payload is None:
            return

        if self.form_mode == "edit":
            await api_client.update_asset(asset_id=self.form_id_aset, payload=payload)
        else:
            try:
                dup_count = int(self.form_duplicate_count.strip())
                dup_count = max(1, min(50, dup_count))
            except (ValueError, AttributeError):
                dup_count = max(1, min(50, getattr(self, "duplicate_count_form", 1)))
            await api_client.create_assets(payload=payload, duplicate_count=dup_count)

        self.form_modal_open = False
        await self.fetch_assets()

    @rx.event
    async def save_and_add_another(self) -> None:
        payload = self._validate_and_build_payload()
        if payload is None:
            return
        try:
            dup_count = int(self.form_duplicate_count.strip())
            dup_count = max(1, min(50, dup_count))
        except (ValueError, AttributeError):
            dup_count = max(1, min(50, getattr(self, "duplicate_count_form", 1)))
        await api_client.create_assets(payload=payload, duplicate_count=dup_count)
        await self.fetch_assets()
        self.open_add_modal()

    # --- EVENT HANDLERS: HAPUS ASET ---

    @rx.event
    def confirm_delete_asset(self, row_id: str) -> None:
        target_id = row_id or self.active_asset_id
        for item in self.items:
            if item.get("id_aset") == target_id:
                self.asset_to_delete = target_id
                self.asset_to_delete_label = str(item.get("nama_aset", target_id))
                self.delete_dialog_open = True
                return

    @rx.event
    def delete_active_asset(self) -> None:
        """Buka dialog konfirmasi hapus untuk aset aktif di detail drawer."""
        self.confirm_delete_asset(self.active_asset_id)

    @rx.event
    def cancel_delete(self) -> None:
        if self.delete_dialog_open:
            self.delete_dialog_open = False
        self.asset_to_delete = ""
        self.asset_to_delete_label = ""

    @rx.event
    async def execute_delete_asset(self) -> None:
        if self.asset_to_delete:
            await api_client.delete_asset(asset_id=self.asset_to_delete)
            if self.active_asset_id == self.asset_to_delete:
                self.drawer_open = False
                self.active_asset_id = ""
            self.selected_ids = [x for x in self.selected_ids if x != self.asset_to_delete]
        self.cancel_delete()
        await self.fetch_assets()

    # --- COMPUTED VARS & EVENT HANDLERS FASE 2: DETAIL ASET (/assets/[id]) ---

    @rx.var(cache=True)
    def detail_category_hierarchy(self) -> str:
        kat = str(self.detail_asset.get("kategori") or "PC")
        grp = str(self.detail_asset.get("category_group") or "Perangkat IT")
        return f"{grp} › {kat}"

    @rx.var(cache=True)
    def detail_monitor_display(self) -> str:
        if self.detail_monitors:
            m0 = self.detail_monitors[0]
            return f'24" FHD (dari aset {m0.get("id_aset", "")})'
        return str(self.detail_asset.get("monitor") or "—")

    @rx.var(cache=True)
    def detail_primary_ip_summary(self) -> str:
        if self.detail_ips:
            return str(self.detail_ips[0].get("summary", "—"))
        ip_raw = str(self.detail_asset.get("ip_address") or "")
        return f"{ip_raw} · Aktif" if ip_raw else "Belum ada IP tertaut"

    @rx.var(cache=True)
    def detail_has_monitors(self) -> bool:
        return len(self.detail_monitors) > 0

    @rx.var(cache=True)
    def detail_has_maintenances(self) -> bool:
        return len(self.detail_maintenances) > 0

    @rx.var(cache=True)
    def detail_maintenances_summary(self) -> str:
        return f"{len(self.detail_maintenances)} jadwal terdaftar"

    @rx.var(cache=True)
    def detail_is_pc_or_server(self) -> bool:
        return str(self.detail_asset.get("kategori", "")).lower() in ("pc", "laptop", "server")

    @rx.var(cache=True)
    def detail_qr_url(self) -> str:
        code = str(self.detail_asset.get("id_aset") or self.detail_asset_id or "PC-003")
        return (
            "https://api.qrserver.com/v1/create-qr-code/?size=180x180"
            f"&data=https://itam.xmltronik.id/assets/{code}"
        )

    @rx.event
    def open_asset_detail_page(self, row_id: str) -> Any:
        """Buka halaman penuh /assets/[id] saat baris tabel diklik (Artboard 11)."""
        target = (row_id or "").strip()
        if not target:
            return None
        return rx.redirect(f"/assets/{target}")

    @rx.event
    async def load_asset_detail_page(self) -> None:
        """Muat data lengkap aset beserta relasinya saat halaman /assets/[id] dibuka."""
        params = get_current_params(self.router)
        raw_path = get_current_raw_path(self.router)
        asset_id = str(params.get("id") or "").strip()
        if not asset_id and "/assets/" in raw_path:
            tail = raw_path.split("/assets/", 1)[1].split("?")[0].strip("/")
            if tail and not tail.startswith("c/"):
                asset_id = tail

        if not asset_id:
            return

        self.detail_asset_id = asset_id.upper()
        tab_param = str(params.get("tab") or "").strip().lower()
        if tab_param in (
            "ringkasan",
            "spesifikasi",
            "komponen",
            "relasi",
            "pembelian",
            "maintenance",
            "riwayat",
        ):
            self.detail_tab = tab_param
        else:
            self.detail_tab = "ringkasan"

        res = await api_client.get_asset_full_detail(self.detail_asset_id)
        if not res:
            return
        self.detail_asset = res.get("asset") or {}
        rels = res.get("relations") or {}
        self.detail_monitors = list(rels.get("monitors") or [])
        self.detail_power_links = list(rels.get("power_links") or [])
        self.detail_ips = list(rels.get("ips") or [])
        self.detail_credentials = list(rels.get("credentials") or [])
        self.detail_credentials_summary = str(
            rels.get("credentials_summary") or "Belum ada kredensial tertaut"
        )
        purch = rels.get("purchase")
        self.detail_has_purchase = purch is not None
        self.detail_purchase = purch or {}
        self.detail_maintenances = list(rels.get("maintenances") or [])
        self.detail_movements = list(res.get("movements") or [])
        comp_data = res.get("components") or {}
        self.comp_is_tracked = bool(comp_data.get("is_tracked", False))
        self.comp_ram_summary_chip = str(
            comp_data.get("ram_summary_chip") or "RAM total 16 GB · 2 modul"
        )
        self.comp_storage_summary_chip = str(
            comp_data.get("storage_summary_chip") or "Storage total 512 GB · 1 disk"
        )
        self.comp_installed_list = list(comp_data.get("installed") or [])
        self.comp_spare_list = list(comp_data.get("spares") or [])
        if comp_data.get("pc_targets"):
            self.comp_pc_targets = list(comp_data["pc_targets"])
        self.active_asset_id = self.detail_asset_id

    @rx.event
    def set_detail_tab(self, tab_key: str) -> None:
        self.detail_tab = tab_key

    @rx.event
    def open_edit_from_detail(self) -> None:
        if self.detail_asset:
            self._populate_form_from_item(self.detail_asset, mode="edit")

    # --- Handlers Modal Serahkan / Pindahkan ---
    @rx.event
    def open_handover_modal(self) -> None:
        self.handover_jenis = "serah_terima"
        user_cur = str(self.detail_asset.get("digunakan_oleh") or "")
        self.handover_pengguna = "" if user_cur == "—" else user_cur
        self.handover_lokasi = str(
            self.detail_asset.get("lokasi") or "Head Office (Office Blok 14)"
        )
        self.handover_status = str(self.detail_asset.get("status") or "Digunakan")
        self.handover_alasan = "Serah terima operasional"
        self.handover_tanggal = "2026-11-09"
        self.handover_catatan = ""
        self.handover_modal_open = True

    @rx.event
    def close_handover_modal(self) -> None:
        self.handover_modal_open = False

    @rx.event
    def set_handover_jenis(self, val: str) -> None:
        self.handover_jenis = val

    @rx.event
    def set_handover_pengguna(self, val: str) -> None:
        self.handover_pengguna = val

    @rx.event
    def set_handover_lokasi(self, val: str) -> None:
        self.handover_lokasi = val

    @rx.event
    def set_handover_status(self, val: str) -> None:
        self.handover_status = val

    @rx.event
    def set_handover_alasan(self, val: str) -> None:
        self.handover_alasan = val

    @rx.event
    def set_handover_tanggal(self, val: str) -> None:
        self.handover_tanggal = val

    @rx.event
    def set_handover_catatan(self, val: str) -> None:
        self.handover_catatan = val

    @rx.event
    async def submit_handover(self) -> None:
        if not self.detail_asset_id:
            return
        await api_client.handover_asset(
            self.detail_asset_id,
            {
                "jenis": self.handover_jenis,
                "pengguna_baru": self.handover_pengguna,
                "lokasi_baru": self.handover_lokasi,
                "status_baru": self.handover_status,
                "alasan": self.handover_alasan,
                "tanggal": self.handover_tanggal,
                "catatan": self.handover_catatan,
            },
        )
        self.handover_modal_open = False
        await self.load_asset_detail_page()

    # --- Handlers Modal Label QR & Tautan Relasi ---
    @rx.event
    def open_qr_modal(self) -> None:
        self.qr_modal_open = True

    @rx.event
    def close_qr_modal(self) -> None:
        self.qr_modal_open = False

    @rx.event
    def open_link_modal(self) -> None:
        self.link_target_id = ""
        self.link_modal_open = True

    @rx.event
    def close_link_modal(self) -> None:
        self.link_modal_open = False

    @rx.event
    def set_link_target_id(self, val: str) -> None:
        self.link_target_id = val

    @rx.event
    async def submit_asset_link(self) -> None:
        if not self.detail_asset_id or not self.link_target_id.strip():
            return
        await api_client.link_asset_relation(
            self.detail_asset_id,
            {"action": "link", "target_asset_id": self.link_target_id.strip()},
        )
        self.link_modal_open = False
        await self.load_asset_detail_page()

    @rx.var(cache=True)
    def comp_slot_options(self) -> list[str]:
        if self.comp_modal_is_disk:
            return ["M.2", "M.2_2", "SATA 1", "SATA 2", "SATA 3", "SATA 4"]
        return ["DIMM 1", "DIMM 2", "DIMM 3", "DIMM 4"]

    @rx.var(cache=True)
    def comp_alasan_options(self) -> list[str]:
        return [
            "Upgrade RAM PC tujuan",
            "Upgrade Storage PC tujuan",
            "Backup / Cadangan Gudang",
            "Komponen Rusak / Bermasalah",
            "Lainnya",
        ]

    async def _refresh_comp_impact(self) -> None:
        if not self.comp_modal_id:
            return
        tgt = (
            f"{self.detail_asset_id}"
            if self.comp_modal_action == "pasang"
            else self.comp_modal_target_pc
        )
        prev = await api_client.preview_component_impact(
            self.comp_modal_id,
            action=self.comp_modal_action,
            target_pc_id=tgt,
        )
        self.comp_modal_impacts = list(prev.get("impacts") or [])
        self.comp_modal_warning = str(prev.get("warning") or "")

    @rx.event
    async def open_move_component_modal(
        self, comp_id: str, action: str
    ) -> None:
        all_comps = [*self.comp_installed_list, *self.comp_spare_list]
        target = next((c for c in all_comps if c.get("id_aset") == comp_id), None)
        if not target:
            return
        self.comp_modal_id = comp_id
        kat_str = str(target.get("komponen") or "RAM")
        spec_str = str(target.get("spesifikasi") or "")
        parent_str = str(target.get("parent_asset_id") or "")
        loc_info = f"terpasang di {parent_str}" if parent_str else "Cadangan — Gudang"
        self.comp_modal_subtitle = f"{comp_id} · {kat_str} {spec_str} · {loc_info}"
        self.comp_modal_is_disk = kat_str.upper() in ("SSD", "HDD", "SSD/HDD")
        self.comp_modal_action = action
        self.comp_modal_target_pc = (
            self.comp_pc_targets[0] if self.comp_pc_targets else "PC-016 — PC CS H2H"
        )
        default_slot = "M.2" if self.comp_modal_is_disk else "DIMM 2"
        self.comp_modal_slot = str(target.get("slot") or default_slot)
        self.comp_modal_alasan = (
            "Upgrade Storage PC tujuan" if self.comp_modal_is_disk else "Upgrade RAM PC tujuan"
        )
        self.comp_modal_tanggal = "2026-11-09"
        self.comp_modal_catatan = ""
        self.comp_modal_confirm_wipe = False
        self.comp_modal_error = ""
        self.comp_modal_open = True
        await self._refresh_comp_impact()

    @rx.event
    async def open_install_spare_modal(self, comp_id: str) -> None:
        await self.open_move_component_modal(comp_id, "pasang")
        nama = self.detail_asset.get("nama_aset", "")
        self.comp_modal_target_pc = f"{self.detail_asset_id} — {nama}"
        await self._refresh_comp_impact()

    @rx.event
    def close_comp_modal(self) -> None:
        self.comp_modal_open = False
        self.comp_modal_error = ""

    @rx.event
    async def set_comp_modal_action(self, act: str) -> None:
        self.comp_modal_action = act
        self.comp_modal_error = ""
        await self._refresh_comp_impact()

    @rx.event
    async def set_comp_modal_target_pc(self, val: str) -> None:
        self.comp_modal_target_pc = val
        await self._refresh_comp_impact()

    @rx.event
    def set_comp_modal_slot(self, val: str) -> None:
        self.comp_modal_slot = val

    @rx.event
    def set_comp_modal_alasan(self, val: str) -> None:
        self.comp_modal_alasan = val

    @rx.event
    def set_comp_modal_tanggal(self, val: str) -> None:
        self.comp_modal_tanggal = val

    @rx.event
    def set_comp_modal_catatan(self, val: str) -> None:
        self.comp_modal_catatan = val

    @rx.event
    def toggle_comp_modal_wipe(self, _checked: Any = None) -> None:
        self.comp_modal_confirm_wipe = not self.comp_modal_confirm_wipe

    @rx.event
    async def submit_component_mutation(self) -> None:
        self.comp_modal_error = ""
        tgt_pc = (
            self.detail_asset_id
            if self.comp_modal_action == "pasang"
            else self.comp_modal_target_pc
        )
        try:
            await api_client.mutate_component(
                {
                    "component_id": self.comp_modal_id,
                    "action": self.comp_modal_action,
                    "target_pc_id": tgt_pc,
                    "slot": self.comp_modal_slot,
                    "alasan": self.comp_modal_alasan,
                    "tanggal": self.comp_modal_tanggal,
                    "catatan": self.comp_modal_catatan,
                    "lokasi": self.comp_modal_lokasi_cadangan,
                    "confirm_wipe": self.comp_modal_confirm_wipe,
                }
            )
            self.comp_modal_open = False
            await self.load_asset_detail_page()
        except Exception as exc:
            self.comp_modal_error = str(exc)

    @rx.event
    async def execute_component_wizard(self) -> None:
        if not self.detail_asset_id:
            return
        await api_client.run_component_wizard(self.detail_asset_id)
        await self.load_asset_detail_page()


__all__ = ["AssetState"]
