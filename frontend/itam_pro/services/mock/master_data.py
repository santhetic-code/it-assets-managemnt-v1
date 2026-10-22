"""
Daftar Master ITAM Pro (Single Source of Truth).
Nantinya disinkronkan dengan tabel master di Backend PostgreSQL.
"""

MASTER_KATEGORI: list[str] = [
    "PC",
    "Server",
    "Monitor",
    "UPS",
    "Keyboard",
    "Mouse",
    "SSD",
    "RAM",
    "Laptop",
    "Router",
    "HDD",
    "Komponen PC",
    "Lainnya",
]

MASTER_KEPEMILIKAN: list[str] = [
    "XML",
    "MBL",
]

MASTER_LOKASI: list[str] = [
    "Kantor Blok 14",
    "Kantor Blok 13",
    "Kantor Blok 12",
    "Ruko",
    "Mess Blok 12 Office",
    "Mess Blok 12",
]

MASTER_KONDISI: list[str] = [
    "Baru",
    "Bekas",
    "Tidak Terpakai / Rusak",
]

MASTER_STATUS: list[str] = [
    "Digunakan",
    "Backup",
    "Tidak Digunakan",
]

MASTER_JENIS_PC: list[str] = [
    "Operasional",
    "Server",
    "Backup",
]

MASTER_MERK_MONITOR: list[str] = [
    "LG",
    "Dell",
    "Samsung",
    "AOC",
    "HP",
]

MASTER_UKURAN_MONITOR: list[str] = [
    '18,5"',
    '19"',
    '21,5"',
    '23,8"',
    '24"',
    '27"',
]

MASTER_RESOLUSI_MONITOR: list[str] = [
    "1366 × 768",
    "1600 × 900",
    "1920 × 1080",
    "2560 × 1440",
]

MASTER_KONEKTIVITAS_MONITOR: list[str] = [
    "HDMI",
    "VGA",
    "DisplayPort",
    "DVI",
    "USB-C",
]

MASTER_STATUS_MONITOR: list[str] = [
    "Digunakan",
    "Backup",
]


def get_all_master_options() -> dict[str, list[str]]:
    """Kembalikan seluruh daftar opsi master untuk kebutuhan State dan Form."""
    return {
        "kategori": list(MASTER_KATEGORI),
        "kepemilikan": list(MASTER_KEPEMILIKAN),
        "lokasi": list(MASTER_LOKASI),
        "kondisi": list(MASTER_KONDISI),
        "status": list(MASTER_STATUS),
        "jenis_pc": list(MASTER_JENIS_PC),
        "merk_monitor": list(MASTER_MERK_MONITOR),
        "ukuran_monitor": list(MASTER_UKURAN_MONITOR),
        "resolusi_monitor": list(MASTER_RESOLUSI_MONITOR),
        "konektivitas_monitor": list(MASTER_KONEKTIVITAS_MONITOR),
        "status_monitor": list(MASTER_STATUS_MONITOR),
    }


__all__ = [
    "MASTER_JENIS_PC",
    "MASTER_KATEGORI",
    "MASTER_KEPEMILIKAN",
    "MASTER_KONDISI",
    "MASTER_KONEKTIVITAS_MONITOR",
    "MASTER_LOKASI",
    "MASTER_MERK_MONITOR",
    "MASTER_RESOLUSI_MONITOR",
    "MASTER_STATUS",
    "MASTER_STATUS_MONITOR",
    "MASTER_UKURAN_MONITOR",
    "get_all_master_options",
]
