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

# Pemetaan Kategori -> Prefix ID Aset Otomatis
CATEGORY_PREFIXES: dict[str, str] = {
    "PC": "PC",
    "Komputer": "PC",
    "PC / Komputer": "PC",
    "Server": "SRV",
    "Laptop": "LPT",
    "Monitor": "MON",
    "UPS": "UPS",
    "Jaringan": "NET",
    "Network": "NET",
    "Router": "NET",
    "Switch": "NET",
    "CCTV": "CCTV",
    "Printer": "PRT",
    "Periferal": "PRF",
    "Keyboard": "KBD",
    "Mouse": "MSE",
    "SSD": "SSD",
    "RAM": "RAM",
    "HDD": "HDD",
    "Komponen PC": "CMP",
    "Scanner": "SCN",
    "Lainnya": "AST",
}

# Daftar kategori utama yang tampil di UI / filter
CATEGORIES: list[str] = [
    "PC",
    "Server",
    "Laptop",
    "Monitor",
    "UPS",
    "Jaringan",
    "CCTV",
    "Printer",
    "Periferal",
    "Lainnya",
]

# Daftar status operasional aset
ASSET_STATUSES: list[str] = [
    "Aktif",
    "Digunakan",
    "Cadangan",
    "Backup",
    "Gudang",
    "Perbaikan",
    "Maintenance",
    "Rusak",
    "Tidak Digunakan",
    "Nonaktif",
]

# Daftar kondisi fisik aset
ASSET_CONDITIONS: list[str] = [
    "Baik",
    "Normal",
    "Perlu Pengecekan",
    "Rusak Ringan",
    "Rusak Berat",
    "Baru",
    "Bekas",
    "Tidak Terpakai / Rusak",
]

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
        "statuses": ASSET_STATUSES,
        "status": ASSET_STATUSES,
        "conditions": ASSET_CONDITIONS,
        "kondisi": ASSET_CONDITIONS,
        "category_prefixes": CATEGORY_PREFIXES,
        "category_fields": CATEGORY_SPEC_FIELDS,
    }

