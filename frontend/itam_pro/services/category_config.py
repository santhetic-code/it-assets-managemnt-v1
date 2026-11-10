"""
Pusat Konfigurasi Kategori Aset ITAM Pro (Single Source of Truth).
Mengatur slug, prefix ID, field atribut khusus, kolom tabel, tab, dan menu sidebar.
"""

from typing import Literal, NotRequired, Required, TypedDict

from itam_pro.components.tables.data_table import ColumnDef
from itam_pro.components.tables.filter_bar import ColumnToggleOption
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
    name: NotRequired[str]
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
    "Printer": "PRN",
    "Scanner": "SCN",
    "Lainnya": "AST",
}

DEFAULT_VIEW_COLUMNS: list[str] = [
    "id_aset",
    "nama_aset",
    "kategori",
    "sn_pid",
    "kepemilikan",
    "lokasi",
    "kondisi",
    "status",
    "digunakan_oleh",
    "tanggal_masuk_gudang",
    "tanggal_keluar_gudang",
]

# Default kolom tersembunyi per view (PC menyembunyikan Mainboard, Keyboard, Mouse)
DEFAULT_HIDDEN_COLUMNS_BY_SLUG: dict[str, list[str]] = {
    "": [],
    "pc": ["mainboard", "keyboard", "mouse"],
    "monitor": [],
    "ups": [],
    "printer": [],
}

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
    {
        "key": "tdp_cpu_w",
        "label": "TDP CPU (W)",
        "type": "number",
        "required": False,
        "show_in_list": False,
        "filterable": False,
        "placeholder": "Contoh: 65",
    },
    {
        "key": "tdp_gpu_w",
        "label": "TDP GPU (W)",
        "type": "number",
        "required": False,
        "show_in_list": False,
        "filterable": False,
        "placeholder": "Contoh: 30",
    },
]

VEHICLE_FIELDS: list[CategoryFieldDef] = [
    {
        "key": "nomor_polisi",
        "label": "Nomor Polisi",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: R 1234 AB",
    },
    {
        "key": "nomor_rangka",
        "label": "Nomor Rangka",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Nomor rangka fisik",
    },
    {
        "key": "nomor_mesin",
        "label": "Nomor Mesin",
        "type": "text",
        "required": True,
        "show_in_list": False,
        "filterable": False,
        "placeholder": "Nomor mesin kendaraan",
    },
    {
        "key": "masa_pajak",
        "label": "Masa Pajak Tahunan",
        "type": "date",
        "required": True,
        "show_in_list": True,
        "filterable": False,
    },
    {
        "key": "masa_stnk",
        "label": "Masa Berlaku STNK (5 Thn)",
        "type": "date",
        "required": True,
        "show_in_list": True,
        "filterable": False,
    },
]

AC_FIELDS: list[CategoryFieldDef] = [
    {
        "key": "kapasitas_pk",
        "label": "Kapasitas PK",
        "type": "text",
        "required": True,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: 1 PK / 2 PK",
    },
    {
        "key": "jenis_freon",
        "label": "Jenis Freon",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: R32 / R410A",
    },
]

FURNITURE_FIELDS: list[CategoryFieldDef] = [
    {
        "key": "material",
        "label": "Material / Bahan",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: Kayu Jati / Besi Minimalis",
    },
    {
        "key": "dimensi",
        "label": "Ukuran / Dimensi",
        "type": "text",
        "required": False,
        "show_in_list": True,
        "filterable": False,
        "placeholder": "Contoh: 120 x 60 x 75 cm",
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
        "name": "PC & Laptop",
        "subtitle": "Filter perangkat PC dan Laptop dari satu daftar induk Semua Aset.",
        "add_button_label": "+ Tambah PC",
        "pinned": True,
        "included_categories": ["PC", "Laptop"],
        "view_columns": [
            "id_aset",
            "nama_aset",
            "kategori",
            "digunakan_oleh",
            "lokasi",
            "cpu",
            "ram",
            "hdd_ssd",
            "os",
            "monitor",
            "status",
            "kondisi",
            "terkait_chips",
        ],
        "fields": PC_FIELDS,
    },
    "server": {
        "slug": "server",
        "code": "SRV",
        "name": "Server",
        "subtitle": "Filter perangkat Server fisik dan cadangan dari satu daftar induk Semua Aset.",
        "add_button_label": "+ Tambah Server",
        "pinned": True,
        "included_categories": ["Server"],
        "view_columns": [
            "id_aset",
            "nama_aset",
            "kategori",
            "lokasi",
            "cpu",
            "ram",
            "hdd_ssd",
            "os",
            "status",
            "kondisi",
            "terkait_chips",
        ],
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
    "printer": {
        "slug": "printer",
        "code": "PRN",
        "name": "Printer",
        "subtitle": "Inventaris printer dan scanner operasional.",
        "add_button_label": "+ Tambah Printer",
        "pinned": False,
        "included_categories": ["Printer", "Scanner"],
        "view_columns": ["kategori", "nama_aset", "lokasi", "status"],
        "tab_field": "jenis",
        "tab_options": ["Semua", "LaserJet", "InkJet", "Dot Matrix", "Thermal"],
        "fields": [
            {
                "key": "jenis",
                "name": "jenis",
                "label": "Jenis",
                "type": "select",
                "options": ["LaserJet", "InkJet", "Dot Matrix", "Thermal"],
                "required": True,
                "show_in_list": True,
                "filterable": True,
            },
            {
                "key": "konektivitas",
                "name": "konektivitas",
                "label": "Konektivitas",
                "type": "multiselect",
                "options": ["USB", "LAN", "Wi-Fi"],
                "required": False,
                "show_in_list": True,
                "filterable": True,
            },
        ],
    },
    "mobil": {
        "slug": "mobil",
        "code": "KND",
        "name": "Mobil",
        "subtitle": "Inventaris kendaraan operasional roda empat.",
        "add_button_label": "+ Tambah Mobil",
        "pinned": False,
        "included_categories": ["Mobil"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": VEHICLE_FIELDS,
    },
    "motor": {
        "slug": "motor",
        "code": "KND",
        "name": "Motor",
        "subtitle": "Inventaris kendaraan operasional roda dua.",
        "add_button_label": "+ Tambah Motor",
        "pinned": False,
        "included_categories": ["Motor"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": VEHICLE_FIELDS,
    },
    "ac": {
        "slug": "ac",
        "code": "AC",
        "name": "AC",
        "subtitle": "Inventaris pendingin ruangan (AC) per unit.",
        "add_button_label": "+ Tambah AC",
        "pinned": False,
        "included_categories": ["AC"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": AC_FIELDS,
    },
    "meja": {
        "slug": "meja",
        "code": "FUR",
        "name": "Meja",
        "subtitle": "Inventaris meja kerja kantor (mengikuti batas nilai Rp 1.000.000).",
        "add_button_label": "+ Tambah Meja",
        "pinned": False,
        "included_categories": ["Meja"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": FURNITURE_FIELDS,
    },
    "kursi": {
        "slug": "kursi",
        "code": "FUR",
        "name": "Kursi",
        "subtitle": "Inventaris kursi kantor (mengikuti batas nilai Rp 1.000.000).",
        "add_button_label": "+ Tambah Kursi",
        "pinned": False,
        "included_categories": ["Kursi"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": FURNITURE_FIELDS,
    },
    "lemari": {
        "slug": "lemari",
        "code": "FUR",
        "name": "Lemari",
        "subtitle": "Inventaris lemari & arsip kantor (mengikuti batas nilai Rp 1.000.000).",
        "add_button_label": "+ Tambah Lemari",
        "pinned": False,
        "included_categories": ["Lemari"],
        "view_columns": DEFAULT_VIEW_COLUMNS,
        "fields": FURNITURE_FIELDS,
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
    """Bangun kolom dasar Artboard 10 + kolom dinamis dari schema kategori bila kategori dipilih."""
    base_cols: list[ColumnDef] = [
        {
            "key": "id_aset",
            "header": "ASET ID",
            "width": "105px",
            "min_width": "95px",
            "render_type": "bold_blue",
            "sticky_left": True,
            "sortable": True,
            "sort_key": "id_aset",
        },
        {
            "key": "nama_aset",
            "header": "NAMA",
            "width": "210px",
            "min_width": "180px",
            "render_type": "bold",
            "sortable": True,
            "sort_key": "nama_aset",
        },
        {
            "key": "kategori",
            "header": "KATEGORI",
            "width": "110px",
            "min_width": "100px",
            "render_type": "badge",
        },
        {
            "key": "digunakan_oleh",
            "header": "PENGGUNA / PENEMPATAN",
            "width": "190px",
            "min_width": "165px",
            "render_type": "text",
        },
        {
            "key": "lokasi",
            "header": "LOKASI",
            "width": "165px",
            "min_width": "145px",
            "render_type": "text",
        },
    ]

    spec_cols: list[ColumnDef] = []
    if slug in ("pc", "server"):
        spec_cols = [
            {
                "key": "cpu",
                "header": "CPU",
                "width": "155px",
                "min_width": "135px",
                "render_type": "text",
            },
            {
                "key": "ram",
                "header": "RAM",
                "width": "120px",
                "min_width": "105px",
                "render_type": "text",
            },
            {
                "key": "hdd_ssd",
                "header": "STORAGE",
                "width": "140px",
                "min_width": "125px",
                "render_type": "text",
            },
            {
                "key": "os",
                "header": "OS",
                "width": "145px",
                "min_width": "130px",
                "render_type": "text",
            },
        ]
        if slug == "pc":
            spec_cols.append(
                {
                    "key": "monitor",
                    "header": "MONITOR",
                    "width": "155px",
                    "min_width": "135px",
                    "render_type": "text",
                }
            )
    elif slug == "monitor":
        spec_cols = [
            {
                "key": "ukuran_layar_display",
                "header": "UKURAN",
                "width": "105px",
                "min_width": "95px",
                "render_type": "text",
                "sortable": True,
                "sort_key": "ukuran_layar",
            },
            {
                "key": "resolusi_layar",
                "header": "RESOLUSI",
                "width": "135px",
                "min_width": "120px",
                "render_type": "text",
            },
            {
                "key": "konektivitas",
                "header": "KONEKTIVITAS",
                "width": "165px",
                "min_width": "145px",
                "render_type": "chips",
            },
        ]
    elif slug == "ups":
        spec_cols = [
            {
                "key": "kapasitas_va",
                "header": "KAPASITAS VA",
                "width": "130px",
                "min_width": "115px",
                "render_type": "text",
            },
        ]

    tail_cols: list[ColumnDef] = [
        {
            "key": "status",
            "header": "STATUS",
            "width": "130px",
            "min_width": "115px",
            "render_type": "status_badge",
        },
        {
            "key": "kondisi",
            "header": "KONDISI",
            "width": "120px",
            "min_width": "105px",
            "render_type": "condition_badge",
        },
        {
            "key": "terkait_chips",
            "header": "TERKAIT",
            "width": "210px",
            "min_width": "180px",
            "render_type": "chips",
        },
    ]
    return [*base_cols, *spec_cols, *tail_cols]


def build_column_toggle_options(slug: str) -> list[ColumnToggleOption]:
    """Kembalikan daftar kolom yang dapat disembunyikan/ditampilkan via 'Atur kolom'."""
    cols = build_table_columns_for_slug(slug)
    return [
        {"key": c["key"], "label": str(c["header"])}
        for c in cols
        if not c.get("sticky_left", False)
    ]


__all__ = [
    "AC_FIELDS",
    "CATEGORY_CONFIGS",
    "CATEGORY_PREFIX_MAP",
    "DEFAULT_HIDDEN_COLUMNS_BY_SLUG",
    "DEFAULT_VIEW_COLUMNS",
    "FURNITURE_FIELDS",
    "MONITOR_FIELDS",
    "PC_FIELDS",
    "VEHICLE_FIELDS",
    "CategoryConfig",
    "CategoryFieldDef",
    "FieldType",
    "build_column_toggle_options",
    "build_table_columns_for_slug",
    "get_config_by_slug",
    "get_config_for_category_name",
    "get_pinned_categories",
    "get_prefix_for_category",
]
