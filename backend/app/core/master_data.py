"""Referensi data master dan konfigurasi kategori aset ITAM Pro.

Pastikan daftar konstanta di bawah ini selaras dengan:
- frontend/itam_pro/services/mock/master_data.py
- frontend/itam_pro/services/category_config.py
"""

from typing import Any

# Daftar lokasi operasional resmi perusahaan
LOCATIONS: list[str] = [
    "Mess (Mess Blok 12)",
    "Konter (Ruko Rinjani)",
    "Office 437 (Office Blok 12)",
    "White House (Office Blok 13)",
    "Head Office (Office Blok 14)",
]

# Alias lokasi singkat dan nama legacy dari frontend yang tetap diterima saat validasi/impor CSV
LOCATION_ALIASES: dict[str, str] = {
    "mess": "Mess (Mess Blok 12)",
    "mess blok 12": "Mess (Mess Blok 12)",
    "mess blok 12 office": "Mess (Mess Blok 12)",
    "konter": "Konter (Ruko Rinjani)",
    "ruko": "Konter (Ruko Rinjani)",
    "ruko rinjani": "Konter (Ruko Rinjani)",
    "office 437": "Office 437 (Office Blok 12)",
    "office blok 12": "Office 437 (Office Blok 12)",
    "kantor blok 12": "Office 437 (Office Blok 12)",
    "white house": "White House (Office Blok 13)",
    "office blok 13": "White House (Office Blok 13)",
    "kantor blok 13": "White House (Office Blok 13)",
    "head office": "Head Office (Office Blok 14)",
    "office blok 14": "Head Office (Office Blok 14)",
    "kantor blok 14": "Head Office (Office Blok 14)",
}

DEFAULT_ASSET_VALUE_THRESHOLD: int = 1_000_000

# Pemetaan Kategori -> Prefix ID Aset Otomatis (Seksi 4.5)
CATEGORY_PREFIXES: dict[str, str] = {
    "PC": "PC",
    "Komputer": "PC",
    "PC / Komputer": "PC",
    "Laptop": "LTP",
    "Server": "SRV",
    "Monitor": "MON",
    "UPS": "UPS",
    "RAM": "RAM",
    "SSD": "SSD",
    "HDD": "HDD",
    "SSD/HDD": "SSD",
    "VGA": "VGA",
    "PSU": "PSU",
    "Keyboard": "KBD",
    "Mouse": "MSE",
    "Router/Switch": "NET",
    "Router": "NET",
    "Switch": "NET",
    "Access Point": "AP",
    "Jaringan": "NET",
    "Network": "NET",
    "CCTV": "CCTV",
    "Mobil": "KND",
    "Motor": "KND",
    "Kendaraan": "KND",
    "AC": "AC",
    "Meja": "FUR",
    "Kursi": "FUR",
    "Lemari": "FUR",
    "Furnitur": "FUR",
    "Printer": "PRT",
    "Scanner": "SCN",
    "Periferal": "PRF",
    "Komponen PC": "CMP",
    "Aset lain": "AST",
    "Lainnya": "AST",
}

# Pohon Kategori Utama & Subkategori beserta Mode Pelacakan dan Schema (Seksi 4.2 & 5)
CATEGORY_TREE: list[dict[str, Any]] = [
    {
        "kode": "GRP-IT",
        "slug": "perangkat-it",
        "nama": "Perangkat IT",
        "ikon": "monitor",
        "tracking": "unit",
        "children": [
            {
                "kode": "PC",
                "slug": "pc",
                "nama": "PC",
                "ikon": "monitor-speaker",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {"key": "cpu", "label": "CPU", "type": "text", "required": True},
                        {"key": "ram", "label": "RAM", "type": "text", "required": True},
                        {"key": "vga", "label": "VGA", "type": "text", "required": False},
                        {"key": "storage", "label": "Storage", "type": "text", "required": True},
                        {"key": "os", "label": "OS", "type": "text", "required": True},
                        {
                            "key": "tdp_cpu_w",
                            "label": "TDP CPU (W)",
                            "type": "number",
                            "required": False,
                        },
                        {
                            "key": "tdp_gpu_w",
                            "label": "TDP GPU (W)",
                            "type": "number",
                            "required": False,
                        },
                    ]
                },
            },
            {
                "kode": "LTP",
                "slug": "laptop",
                "nama": "Laptop",
                "ikon": "laptop",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {"key": "cpu", "label": "CPU", "type": "text", "required": True},
                        {"key": "ram", "label": "RAM", "type": "text", "required": True},
                        {"key": "vga", "label": "VGA", "type": "text", "required": False},
                        {"key": "storage", "label": "Storage", "type": "text", "required": True},
                        {"key": "os", "label": "OS", "type": "text", "required": True},
                        {
                            "key": "tdp_cpu_w",
                            "label": "TDP CPU (W)",
                            "type": "number",
                            "required": False,
                        },
                        {
                            "key": "tdp_gpu_w",
                            "label": "TDP GPU (W)",
                            "type": "number",
                            "required": False,
                        },
                    ]
                },
            },
            {
                "kode": "SRV",
                "slug": "server",
                "nama": "Server",
                "ikon": "server",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {"key": "cpu", "label": "CPU", "type": "text", "required": True},
                        {"key": "ram", "label": "RAM", "type": "text", "required": True},
                        {"key": "vga", "label": "VGA", "type": "text", "required": False},
                        {"key": "storage", "label": "Storage", "type": "text", "required": True},
                        {"key": "os", "label": "OS", "type": "text", "required": True},
                        {
                            "key": "tdp_cpu_w",
                            "label": "TDP CPU (W)",
                            "type": "number",
                            "required": False,
                        },
                        {
                            "key": "tdp_gpu_w",
                            "label": "TDP GPU (W)",
                            "type": "number",
                            "required": False,
                        },
                    ]
                },
            },
            {
                "kode": "MON",
                "slug": "monitor",
                "nama": "Monitor",
                "ikon": "monitor",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {
                            "key": "ukuran_layar",
                            "label": "Ukuran",
                            "type": "number",
                            "required": True,
                        },
                        {
                            "key": "resolusi_layar",
                            "label": "Resolusi",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "konektivitas",
                            "label": "Konektivitas",
                            "type": "multiselect",
                            "required": True,
                        },
                    ]
                },
            },
            {
                "kode": "UPS",
                "slug": "ups",
                "nama": "UPS",
                "ikon": "battery-charging",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {
                            "key": "kapasitas_va",
                            "label": "Kapasitas VA",
                            "type": "number",
                            "required": True,
                        },
                        {
                            "key": "jenis_aki",
                            "label": "Jenis Aki",
                            "type": "text",
                            "required": False,
                        },
                    ]
                },
            },
        ],
    },
    {
        "kode": "GRP-CMP",
        "slug": "komponen-periferal",
        "nama": "Komponen & Periferal",
        "ikon": "cpu",
        "tracking": "unit",
        "children": [
            {
                "kode": "RAM",
                "slug": "ram",
                "nama": "RAM",
                "ikon": "memory-stick",
                "tracking": "unit",
                "spec_schema": {},
            },
            {
                "kode": "SSD",
                "slug": "ssd",
                "nama": "SSD/HDD",
                "ikon": "hard-drive",
                "tracking": "unit",
                "spec_schema": {},
            },
            {
                "kode": "VGA",
                "slug": "vga",
                "nama": "VGA",
                "ikon": "cpu",
                "tracking": "unit",
                "spec_schema": {},
            },
            {
                "kode": "PSU",
                "slug": "psu",
                "nama": "PSU",
                "ikon": "zap",
                "tracking": "unit",
                "spec_schema": {},
            },
            {
                "kode": "KBD",
                "slug": "keyboard",
                "nama": "Keyboard",
                "ikon": "keyboard",
                "tracking": "threshold",
                "spec_schema": {},
            },
            {
                "kode": "MSE",
                "slug": "mouse",
                "nama": "Mouse",
                "ikon": "mouse",
                "tracking": "threshold",
                "spec_schema": {},
            },
        ],
    },
    {
        "kode": "GRP-NET",
        "slug": "jaringan",
        "nama": "Jaringan",
        "ikon": "network",
        "tracking": "unit",
        "children": [
            {
                "kode": "NET",
                "slug": "router",
                "nama": "Router/Switch",
                "ikon": "router",
                "tracking": "unit",
                "spec_schema": {},
            },
            {
                "kode": "AP",
                "slug": "access-point",
                "nama": "Access Point",
                "ikon": "wifi",
                "tracking": "unit",
                "spec_schema": {},
            },
            {
                "kode": "CCTV",
                "slug": "cctv",
                "nama": "CCTV",
                "ikon": "camera",
                "tracking": "unit",
                "spec_schema": {},
            },
        ],
    },
    {
        "kode": "GRP-KND",
        "slug": "kendaraan",
        "nama": "Kendaraan",
        "ikon": "car",
        "tracking": "unit",
        "children": [
            {
                "kode": "MBL",
                "slug": "mobil",
                "nama": "Mobil",
                "ikon": "car",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {
                            "key": "nomor_polisi",
                            "label": "Nomor Polisi",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "nomor_rangka",
                            "label": "Nomor Rangka",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "nomor_mesin",
                            "label": "Nomor Mesin",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "masa_pajak",
                            "label": "Masa Pajak",
                            "type": "date",
                            "required": True,
                        },
                        {
                            "key": "masa_stnk",
                            "label": "Masa STNK",
                            "type": "date",
                            "required": True,
                        },
                    ]
                },
            },
            {
                "kode": "MTR",
                "slug": "motor",
                "nama": "Motor",
                "ikon": "bike",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {
                            "key": "nomor_polisi",
                            "label": "Nomor Polisi",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "nomor_rangka",
                            "label": "Nomor Rangka",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "nomor_mesin",
                            "label": "Nomor Mesin",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "masa_pajak",
                            "label": "Masa Pajak",
                            "type": "date",
                            "required": True,
                        },
                        {
                            "key": "masa_stnk",
                            "label": "Masa STNK",
                            "type": "date",
                            "required": True,
                        },
                    ]
                },
            },
        ],
    },
    {
        "kode": "GRP-OFC",
        "slug": "peralatan-kantor",
        "nama": "Peralatan Kantor",
        "ikon": "air-vent",
        "tracking": "unit",
        "children": [
            {
                "kode": "AC",
                "slug": "ac",
                "nama": "AC",
                "ikon": "air-vent",
                "tracking": "unit",
                "spec_schema": {
                    "fields": [
                        {
                            "key": "kapasitas_pk",
                            "label": "Kapasitas (PK)",
                            "type": "text",
                            "required": True,
                        },
                        {
                            "key": "jenis_freon",
                            "label": "Jenis Freon",
                            "type": "text",
                            "required": False,
                        },
                    ]
                },
            },
        ],
    },
    {
        "kode": "GRP-FUR",
        "slug": "furnitur",
        "nama": "Furnitur",
        "ikon": "armchair",
        "tracking": "threshold",
        "children": [
            {
                "kode": "MJA",
                "slug": "meja",
                "nama": "Meja",
                "ikon": "table",
                "tracking": "threshold",
                "spec_schema": {
                    "fields": [
                        {"key": "material", "label": "Material", "type": "text", "required": False},
                        {"key": "dimensi", "label": "Dimensi", "type": "text", "required": False},
                    ]
                },
            },
            {
                "kode": "KRS",
                "slug": "kursi",
                "nama": "Kursi",
                "ikon": "armchair",
                "tracking": "threshold",
                "spec_schema": {
                    "fields": [
                        {"key": "material", "label": "Material", "type": "text", "required": False},
                        {"key": "dimensi", "label": "Dimensi", "type": "text", "required": False},
                    ]
                },
            },
            {
                "kode": "LMR",
                "slug": "lemari",
                "nama": "Lemari",
                "ikon": "archive",
                "tracking": "threshold",
                "spec_schema": {
                    "fields": [
                        {"key": "material", "label": "Material", "type": "text", "required": False},
                        {"key": "dimensi", "label": "Dimensi", "type": "text", "required": False},
                    ]
                },
            },
        ],
    },
    {
        "kode": "GRP-OTH",
        "slug": "lainnya",
        "nama": "Lainnya",
        "ikon": "box",
        "tracking": "threshold",
        "children": [
            {
                "kode": "AST",
                "slug": "aset-lain",
                "nama": "Aset lain",
                "ikon": "box",
                "tracking": "threshold",
                "spec_schema": {},
            },
        ],
    },
]

CATEGORIES: list[str] = [
    "PC",
    "Laptop",
    "Server",
    "Monitor",
    "UPS",
    "RAM",
    "SSD/HDD",
    "VGA",
    "PSU",
    "Keyboard",
    "Mouse",
    "Router/Switch",
    "Access Point",
    "CCTV",
    "Mobil",
    "Motor",
    "AC",
    "Meja",
    "Kursi",
    "Lemari",
    "Lainnya",
]

# Status siklus hidup aset resmi (Seksi 4.3) + kompatibilitas input lama
ASSET_STATUSES: list[str] = [
    "Digunakan",
    "Cadangan",
    "Dalam Perbaikan",
    "Rusak",
    "Dihapusbukukan",
    # Alias kompatibilitas
    "Aktif",
    "Backup",
    "Gudang",
    "Perbaikan",
    "Maintenance",
    "Tidak Digunakan",
    "Nonaktif",
]

STATUS_NORMALIZATION_MAP: dict[str, str] = {
    "digunakan": "Digunakan",
    "aktif": "Digunakan",
    "cadangan": "Cadangan",
    "backup": "Cadangan",
    "gudang": "Cadangan",
    "tidak digunakan": "Cadangan",
    "dalam perbaikan": "Dalam Perbaikan",
    "perbaikan": "Dalam Perbaikan",
    "maintenance": "Dalam Perbaikan",
    "rusak": "Rusak",
    "nonaktif": "Rusak",
    "dihapusbukukan": "Dihapusbukukan",
}

# Kondisi fisik aset resmi (Seksi 4.3) + kompatibilitas input lama
ASSET_CONDITIONS: list[str] = [
    "Baru",
    "Baik",
    "Perlu Servis",
    "Rusak",
    # Alias kompatibilitas
    "Normal",
    "Bekas",
    "Perlu Pengecekan",
    "Rusak Ringan",
    "Rusak Berat",
    "Tidak Terpakai / Rusak",
]

CONDITION_NORMALIZATION_MAP: dict[str, str] = {
    "baru": "Baru",
    "baik": "Baik",
    "normal": "Baik",
    "bekas": "Baik",
    "perlu servis": "Perlu Servis",
    "perlu pengecekan": "Perlu Servis",
    "rusak ringan": "Perlu Servis",
    "rusak": "Rusak",
    "rusak berat": "Rusak",
    "tidak terpakai / rusak": "Rusak",
}

ASSET_ROLES: list[str] = ["Operasional", "Server", "Backup"]


def normalize_asset_status(raw: str | None) -> str:
    cleaned = (raw or "").strip().lower()
    return STATUS_NORMALIZATION_MAP.get(cleaned, "Digunakan")


def normalize_asset_condition(raw: str | None) -> str:
    cleaned = (raw or "").strip().lower()
    return CONDITION_NORMALIZATION_MAP.get(cleaned, "Baik")


def resolve_tracking_mode(kategori: str, nilai_perolehan: int | None = None) -> str:
    """Menentukan mode pelacakan ('unit' atau 'stok') berdasarkan aturan Seksi 4.2."""
    clean_kat = (kategori or "").strip().lower()
    for group in CATEGORY_TREE:
        for sub in group.get("children", []):
            if sub["nama"].lower() == clean_kat or sub["kode"].lower() == clean_kat:
                if sub["tracking"] == "unit":
                    return "unit"
                if (
                    nilai_perolehan is not None
                    and 0 < nilai_perolehan < DEFAULT_ASSET_VALUE_THRESHOLD
                ):
                    return "stok"
                return "unit"
    return "unit"


# Spesifikasi field per kategori (tanpa Power Supply dan tanpa Casing)
CATEGORY_SPEC_FIELDS: dict[str, list[str]] = {
    "PC": ["processor", "motherboard", "ram", "storage", "gpu", "os", "watt"],
    "Server": ["processor", "motherboard", "ram", "storage", "os", "watt"],
    "Laptop": ["processor", "ram", "storage", "ukuran_layar", "os", "baterai"],
    "Monitor": ["ukuran_layar", "resolusi", "panel", "refresh_rate", "port_display"],
    "UPS": ["kapasitas_va", "kapasitas_watt", "baterai", "jumlah_baterai", "beban_perangkat"],
    "Jaringan": ["tipe_perangkat", "jumlah_port", "kecepatan", "ip_address", "mac_address"],
    "CCTV": ["resolusi", "tipe_kamera", "ip_address", "lokasi_titik"],
    "Printer": ["tipe_printer", "koneksi", "tinta_toner", "ip_address"],
    "Periferal": ["spesifikasi_teknis"],
    "Lainnya": ["spesifikasi_teknis"],
}


def get_prefix_for_category(kategori: str) -> str:
    """Mengambil prefix 3-4 huruf untuk kategori aset."""
    clean = kategori.strip()
    if clean in CATEGORY_PREFIXES:
        return CATEGORY_PREFIXES[clean]
    for key, prefix in CATEGORY_PREFIXES.items():
        if key.lower() == clean.lower():
            return prefix
    return "AST"


def get_master_data_payload() -> dict[str, Any]:
    """Mengembalikan payload lengkap data master untuk frontend."""
    return {
        "locations": LOCATIONS,
        "lokasi": LOCATIONS,
        "categories": CATEGORIES,
        "kategori": CATEGORIES,
        "category_tree": CATEGORY_TREE,
        "statuses": ASSET_STATUSES,
        "status": ASSET_STATUSES,
        "conditions": ASSET_CONDITIONS,
        "kondisi": ASSET_CONDITIONS,
        "asset_roles": ASSET_ROLES,
        "default_value_threshold": DEFAULT_ASSET_VALUE_THRESHOLD,
        "category_prefixes": CATEGORY_PREFIXES,
        "category_fields": CATEGORY_SPEC_FIELDS,
    }
