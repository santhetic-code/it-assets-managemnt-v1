"""
Daftar Master ITAM Pro (Single Source of Truth).
Nantinya disinkronkan dengan tabel master di Backend PostgreSQL.
"""

MASTER_KATEGORI: list[str] = [
    "Monitor",
    "Keyboard",
    "Mouse",
    "SSD",
    "RAM",
    "Laptop",
    "Router",
    "HDD",
    "PC",
    "Server",
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
    "Tidak Digunakan",
]


def get_all_master_options() -> dict[str, list[str]]:
    """Kembalikan seluruh daftar opsi master untuk kebutuhan State dan Form."""
    return {
        "kategori": list(MASTER_KATEGORI),
        "kepemilikan": list(MASTER_KEPEMILIKAN),
        "lokasi": list(MASTER_LOKASI),
        "kondisi": list(MASTER_KONDISI),
        "status": list(MASTER_STATUS),
    }


__all__ = [
    "MASTER_KATEGORI",
    "MASTER_KEPEMILIKAN",
    "MASTER_KONDISI",
    "MASTER_LOKASI",
    "MASTER_STATUS",
    "get_all_master_options",
]
