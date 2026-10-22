"""
Pusat Konfigurasi Kategori Aset ITAM Pro (Single Source of Truth).
Mengatur slug, prefix ID, field atribut khusus, kolom tabel, tab, dan menu sidebar.
"""
from typing import Literal, NotRequired, Required, TypedDict

from itam_pro.components.tables.data_table import ColumnDef
from itam_pro.services.mock.master_data import (
    MASTER_JENIS_PC,
    MASTER_KONEKTIVITAS_MONITOR,
    MASTER_MERK_MONITOR,
    MASTER_RESOLUSI_MONITOR,
    MASTER_STATUS_MONITOR,
)

FieldType = Literal["text", "number", "select", "multiselect", "date"]


class CategoryFieldDef(TypedDict, total=False):
    key: Required[str]
    label: Required[str]
    type: Required[FieldType]
    unit: NotRequired[str]
    options: NotRequired[list[str]]
    required: Required[bool]
    show_in_list: Required[bool]
    filterable: Required[bool]
    placeholder: NotRequired[str]


class CategoryConfig(TypedDict, total=False):
    slug: Required[str]
    code: Required[str]
    name: Required[str]
    subtitle: Required[str]
    add_button_label: Required[str]
    pinned: Required[bool]
    included_categories: Required[list[str]]
    view_columns: Required[list[str]]
    tab_field: NotRequired[str]
    tab_options: NotRequired[list[str]]
    fields: Required[list[CategoryFieldDef]]


CATEGORY_PREFIX_MAP: dict[str, str] = {
    "PC": "PC",
    "Server": "SRV",
    "Monitor": "MON",
    "UPS": "UPS",
    "Keyboard": "KBD",
    "Mouse": "MSE",
    "SSD": "SSD",
    "RAM": "RAM",
    "Laptop": "LPT",
    "Router": "RTR",
    "HDD": "HDD",
    "Komponen PC": "CMP",
    "Lainnya": "AST",
}

DEFAULT_VIEW_COLUMNS: list[str] = [
    "id_aset",
    "nama_aset",
    "kategori",
    "kepemilikan",
    "lokasi",
    "kondisi",
    "status",
    "digunakan_oleh",
    "tanggal_masuk_gudang",
]

PC_FIELDS: list[CategoryFieldDef] = [
    {
        "key": "jenis",
        "label": "Jenis PC",
        "type": "select",
        "options": MASTER_JENIS_PC,
        "required": True,
        "show_in_list": False,
        "filterable": False,
    },
    {
        "key": "os",
        "label": "Operasi System",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": True,
        "placeholder": "Contoh: Windows 11 Pro / Ubuntu 24.04",
    },
    {
        "key": "ram",
        "label": "RAM",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": True,
        "placeholder": "Contoh: 16 GB DDR4",
    },
    {
        "key": "vga",
        "label": "VGA",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: Intel UHD / RTX 3060",
    },
    {
        "key": "cpu",
        "label": "CPU",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: Intel Core i5-12400",
    },
    {
        "key": "mainboard",
        "label": "Mainboard",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: ASUS Prime B660M-A",
    },
    {
        "key": "hdd_ssd",
        "label": "HDD / SSD",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: SSD NVMe 512 GB",
    },
    {
        "key": "monitor",
        "label": "Monitor",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": 'Contoh: LG 24" (MON-0001)',
    },
    {
        "key": "keyboard",
        "label": "Keyboard",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: Logitech K120",
    },
    {
        "key": "mouse",
        "label": "Mouse",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: Logitech B100",
    },
]

MONITOR_FIELDS: list[CategoryFieldDef] = [
    {
        "key": "merk",
        "label": "Merk",
        "type": "select",
        "options": MASTER_MERK_MONITOR,
        "required": True,
        "show_in_list": True,
        "filterable": True,
        "placeholder": "LG, Dell, Samsung, AOC, HP...",
    },
    {
        "key": "tipe_model",
        "label": "Tipe / Model",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: 24MK600M / UltraSharp U2422H",
    },
    {
        "key": "ukuran_layar",
        "label": "Ukuran Layar",
        "type": "number",
        "unit": 'inci (")',
        "required": True,
        "show_in_list": True,
        "filterable": True,
        "placeholder": "24 / 21,5 / 23,8",
    },
    {
        "key": "resolusi_layar",
        "label": "Resolusi Layar",
        "type": "select",
        "options": MASTER_RESOLUSI_MONITOR,
        "required": True,
        "show_in_list": True,
        "filterable": True,
        "placeholder": "Contoh: 1920 × 1080",
    },
    {
        "key": "konektivitas",
        "label": "Konektivitas",
        "type": "multiselect",
        "options": MASTER_KONEKTIVITAS_MONITOR,
        "required": True,
        "show_in_list": True,
        "filterable": True,
    },
]

CATEGORY_CONFIGS: dict[str, CategoryConfig] = {
    "pc": {
        "slug": "pc",
        "code": "PC",
        "name": "PC",
        "subtitle": "Daftar spesifikasi perangkat PC Operasional, Server, dan Backup.",
        "add_button_label": "+ Tambah PC",
        "pinned": True,
        "included_categories": ["PC", "Server"],
        "view_columns": [
            "nama_aset",
            "digunakan_oleh",
            "os",
            "ram",
            "vga",
            "cpu",
            "mainboard",
            "hdd_ssd",
            "monitor",
            "keyboard",
            "mouse",
        ],
        "tab_field": "jenis",
        "tab_options": MASTER_JENIS_PC,
        "fields": PC_FIELDS,
    },
    "monitor": {
        "slug": "monitor",
        "code": "MON",
        "name": "Monitor",
        "subtitle": "Daftar monitor beserta ukuran, resolusi, dan konektivitasnya.",
        "add_button_label": "+ Tambah Monitor",
        "pinned": True,
        "included_categories": ["Monitor"],
        "view_columns": [
            "id_aset",
            "merk",
            "tipe_model",
            "ukuran_layar",
            "resolusi_layar",
            "konektivitas",
            "status",
        ],
        "tab_field": "status",
        "tab_options": ["Semua", *MASTER_STATUS_MONITOR],
        "fields": MONITOR_FIELDS,
    },
    "ups": {
        "slug": "ups",
        "code": "UPS",
        "name": "UPS",
        "subtitle": "Daftar inventaris unit UPS beserta lokasi dan status pemakaiannya.",
        "add_button_label": "+ Tambah UPS",
        "pinned": True,
        "included_categories": ["UPS"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "keyboard": {
        "slug": "keyboard",
        "code": "KBD",
        "name": "Keyboard",
        "subtitle": "Inventaris periferal keyboard.",
        "add_button_label": "+ Tambah Keyboard",
        "pinned": False,
        "included_categories": ["Keyboard"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "mouse": {
        "slug": "mouse",
        "code": "MSE",
        "name": "Mouse",
        "subtitle": "Inventaris periferal mouse.",
        "add_button_label": "+ Tambah Mouse",
        "pinned": False,
        "included_categories": ["Mouse"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "ssd": {
        "slug": "ssd",
        "code": "SSD",
        "name": "SSD",
        "subtitle": "Inventaris media penyimpanan SSD.",
        "add_button_label": "+ Tambah SSD",
        "pinned": False,
        "included_categories": ["SSD"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "ram": {
        "slug": "ram",
        "code": "RAM",
        "name": "RAM",
        "subtitle": "Inventaris modul memori RAM.",
        "add_button_label": "+ Tambah RAM",
        "pinned": False,
        "included_categories": ["RAM"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "laptop": {
        "slug": "laptop",
        "code": "LPT",
        "name": "Laptop",
        "subtitle": "Inventaris perangkat laptop operasional.",
        "add_button_label": "+ Tambah Laptop",
        "pinned": False,
        "included_categories": ["Laptop"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "router": {
        "slug": "router",
        "code": "RTR",
        "name": "Router",
        "subtitle": "Inventaris perangkat jaringan dan router.",
        "add_button_label": "+ Tambah Router",
        "pinned": False,
        "included_categories": ["Router"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "hdd": {
        "slug": "hdd",
        "code": "HDD",
        "name": "HDD",
        "subtitle": "Inventaris media penyimpanan hard disk.",
        "add_button_label": "+ Tambah HDD",
        "pinned": False,
        "included_categories": ["HDD"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "komponen-pc": {
        "slug": "komponen-pc",
        "code": "CMP",
        "name": "Komponen PC",
        "subtitle": "Inventaris komponen dan suku cadang PC.",
        "add_button_label": "+ Tambah Komponen",
        "pinned": False,
        "included_categories": ["Komponen PC"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
    "lainnya": {
        "slug": "lainnya",
        "code": "AST",
        "name": "Lainnya",
        "subtitle": "Inventaris perangkat IT lainnya.",
        "add_button_label": "+ Tambah Aset",
        "pinned": False,
        "included_categories": ["Lainnya"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": [],
    },
}


def get_prefix_for_category(kategori: str) -> str:
    """Kembalikan kode prefix 3 huruf untuk kategori tertentu."""
    return CATEGORY_PREFIX_MAP.get(kategori, "AST")


def get_config_by_slug(slug: str) -> CategoryConfig | None:
    """Ambil konfigurasi kategori berdasarkan slug route."""
    return CATEGORY_CONFIGS.get(slug.lower().strip())


def get_config_for_category_name(kategori: str) -> CategoryConfig | None:
    """Cari konfigurasi berdasarkan nama kategori aset (mis. 'PC' atau 'Server' -> pc)."""
    for cfg in CATEGORY_CONFIGS.values():
        if kategori in cfg["included_categories"]:
            return cfg
    return None


def get_pinned_categories() -> list[CategoryConfig]:
    """Kembalikan daftar kategori dengan pinned=True untuk dirender di Sidebar."""
    return [cfg for cfg in CATEGORY_CONFIGS.values() if cfg["pinned"]]


def build_table_columns_for_slug(slug: str) -> list[ColumnDef]:
    """Bangun daftar ColumnDef tabel berdasarkan view_columns kategori atau Semua Aset."""
    if slug == "pc":
        return [
            {
                "key": "nama_aset",
                "header": "Nama PC",
                "width": "150px",
                "render_type": "bold_blue",
                "sticky_left": True,
                "sortable": True,
                "sort_key": "nama_aset",
            },
            {
                "key": "digunakan_oleh",
                "header": "User / Fungsi",
                "width": "150px",
                "render_type": "bold",
            },
            {"key": "os", "header": "Operasi System", "width": "145px", "render_type": "text"},
            {"key": "ram", "header": "RAM", "width": "120px", "render_type": "text"},
            {"key": "vga", "header": "VGA", "width": "140px", "render_type": "text"},
            {"key": "cpu", "header": "CPU", "width": "160px", "render_type": "text"},
            {"key": "mainboard", "header": "Mainboard", "width": "150px", "render_type": "text"},
            {"key": "hdd_ssd", "header": "HDD / SSD", "width": "140px", "render_type": "text"},
            {"key": "monitor", "header": "Monitor", "width": "135px", "render_type": "text"},
            {"key": "keyboard", "header": "Keyboard", "width": "125px", "render_type": "text"},
            {"key": "mouse", "header": "Mouse", "width": "120px", "render_type": "text"},
        ]

    if slug == "monitor":
        return [
            {
                "key": "id_aset",
                "header": "ID Aset",
                "width": "12%",
                "render_type": "bold_blue",
                "sticky_left": True,
                "sortable": True,
                "sort_key": "id_aset",
            },
            {
                "key": "merk",
                "header": "Merk",
                "width": "11%",
                "render_type": "bold",
                "sortable": True,
                "sort_key": "merk",
            },
            {"key": "tipe_model", "header": "Tipe / Model", "width": "18%", "render_type": "text"},
            {
                "key": "ukuran_layar_display",
                "header": "Ukuran Layar",
                "width": "13%",
                "render_type": "text",
                "sortable": True,
                "sort_key": "ukuran_layar",
            },
            {
                "key": "resolusi_layar",
                "header": "Resolusi Layar",
                "width": "14%",
                "render_type": "text",
            },
            {
                "key": "konektivitas",
                "header": "Konektivitas",
                "width": "20%",
                "render_type": "chips",
            },
            {
                "key": "status",
                "header": "Status",
                "width": "12%",
                "render_type": "status_badge",
            },
        ]

    # Default (Semua Aset / Kategori tanpa field khusus seperti UPS)
    return [
        {
            "key": "id_aset",
            "header": "ID Aset",
            "width": "120px",
            "render_type": "bold_blue",
            "sticky_left": True,
            "sortable": True,
            "sort_key": "id_aset",
        },
        {
            "key": "nama_aset",
            "header": "Nama Aset",
            "width": "210px",
            "render_type": "bold",
            "sortable": True,
            "sort_key": "nama_aset",
        },
        {"key": "kategori", "header": "Kategori", "width": "125px", "render_type": "badge"},
        {"key": "sn_pid", "header": "SN / PID", "width": "140px", "render_type": "text"},
        {"key": "kepemilikan", "header": "Pemilik", "width": "95px", "render_type": "badge"},
        {"key": "lokasi", "header": "Lokasi", "width": "155px", "render_type": "text"},
        {
            "key": "kondisi",
            "header": "Kondisi",
            "width": "155px",
            "render_type": "condition_badge",
        },
        {"key": "status", "header": "Status", "width": "140px", "render_type": "status_badge"},
        {
            "key": "digunakan_oleh",
            "header": "Digunakan Oleh",
            "width": "155px",
            "render_type": "text",
        },
        {
            "key": "tanggal_masuk_display",
            "header": "Tgl Masuk",
            "width": "125px",
            "render_type": "date",
        },
    ]


__all__ = [
    "CATEGORY_CONFIGS",
    "CATEGORY_PREFIX_MAP",
    "DEFAULT_VIEW_COLUMNS",
    "MONITOR_FIELDS",
    "PC_FIELDS",
    "CategoryConfig",
    "CategoryFieldDef",
    "FieldType",
    "build_table_columns_for_slug",
    "get_config_by_slug",
    "get_config_for_category_name",
    "get_pinned_categories",
    "get_prefix_for_category",
]
