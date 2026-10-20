"""
Data Mock Rekap Monitor ITAM Pro (24 unit: 19 Digunakan, 5 Backup).
Merk: LG, Dell, Samsung, AOC, HP.
"""
from typing import Any


def parse_inch_number(val: str | float | int) -> float:
    """Konversi string ukuran layar ('21,5\"' atau '21.5') menjadi float untuk sorting."""
    cleaned = str(val).replace('"', "").replace("inci", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def format_inch_label(val: str | float | int) -> str:
    """Format angka inci menjadi tampilan '24\"' atau '21,5\"'."""
    num = parse_inch_number(val)
    if num <= 0:
        raw_str = str(val).replace('"', "").strip().replace(".", ",")
        return f'{raw_str}"' if raw_str else '24"'
    if num.is_integer():
        return f'{int(num)}"'
    formatted = f"{num:.1f}".rstrip("0").rstrip(".").replace(".", ",")
    return f'{formatted}"'


def _format_monitor_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Lengkapi field tampilan tabel dan grup informasi untuk Detail Drawer."""
    id_aset = str(raw["id_aset"]).strip().upper()
    merk = str(raw["merk"]).strip()
    tipe_model = str(raw["tipe_model"]).strip()
    ukuran_num = parse_inch_number(raw["ukuran_layar"])
    ukuran_display = format_inch_label(raw["ukuran_layar"])
    resolusi = str(raw["resolusi_layar"]).strip().replace("x", "×").replace("X", "×")
    konektivitas: list[str] = list(raw.get("konektivitas", ["HDMI"]))
    status = str(raw.get("status", "Digunakan")).strip()
    catatan_raw = str(raw.get("catatan", "")).strip()
    catatan_display = catatan_raw or "—"

    return {
        "id_aset": id_aset,
        "merk": merk,
        "tipe_model": tipe_model,
        "ukuran_layar": ukuran_display,
        "ukuran_num": ukuran_num,
        "ukuran_raw": str(ukuran_num if not ukuran_num.is_integer() else int(ukuran_num)).replace(
            ".", ","
        ),
        "resolusi_layar": resolusi,
        "konektivitas": konektivitas,
        "status": status,
        "catatan": catatan_display,
        "catatan_raw": catatan_raw,
        "identity_info": [
            {"label": "ID Aset", "value": id_aset},
            {"label": "Merk", "value": merk},
            {"label": "Tipe / Model", "value": tipe_model},
        ],
        "screen_info": [
            {"label": "Ukuran Layar", "value": ukuran_display},
            {"label": "Resolusi Layar", "value": resolusi},
        ],
        "status_info": [
            {"label": "Status Unit", "value": status},
            {"label": "Catatan", "value": catatan_display},
        ],
        "history_info": raw.get(
            "history_info",
            [
                {
                    "event": "Registrasi Unit Monitor",
                    "date": "14 Okt 2026",
                    "note": (
                        f"Monitor {merk} {tipe_model} ({ukuran_display}) "
                        f"tercatat dengan status {status}."
                    ),
                }
            ],
        ),
    }


def _seed_initial_monitors() -> list[dict[str, Any]]:
    """Bangun 24 unit monitor (19 Digunakan, 5 Backup) sesuai referensi desain."""
    seed_rows: list[dict[str, Any]] = [
        # 8 Baris Pertama Persis Artboard Rekap Monitor
        {
            "id_aset": "MON-0001",
            "merk": "LG",
            "tipe_model": "24MK600M",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Monitor utama meja operasional Kantor Blok 14.",
        },
        {
            "id_aset": "MON-0002",
            "merk": "LG",
            "tipe_model": "24MK600M",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Monitor kedua (dual setup) operasional Blok 14.",
        },
        {
            "id_aset": "MON-0003",
            "merk": "Dell",
            "tipe_model": "UltraSharp U2422H",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "DisplayPort"],
            "status": "Digunakan",
            "catatan": "Digunakan di workstation tim IT Support & QA.",
        },
        {
            "id_aset": "MON-0004",
            "merk": "Samsung",
            "tipe_model": "S27R350",
            "ukuran_layar": "27",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Monitor dashboard monitoring Zabbix & Grafana.",
        },
        {
            "id_aset": "MON-0005",
            "merk": "AOC",
            "tipe_model": "22B1HS",
            "ukuran_layar": "21,5",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja kerja admin Ruko.",
        },
        {
            "id_aset": "MON-0006",
            "merk": "LG",
            "tipe_model": "22MK430H",
            "ukuran_layar": "21,5",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Backup",
            "catatan": "Unit cadangan siap pakai di rak gudang IT Blok 12.",
        },
        {
            "id_aset": "MON-0007",
            "merk": "Dell",
            "tipe_model": "P2422H",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "DisplayPort", "VGA"],
            "status": "Backup",
            "catatan": "Cadangan pengganti monitor operasional utama.",
        },
        {
            "id_aset": "MON-0008",
            "merk": "HP",
            "tipe_model": "M24f",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja Finance Kantor Blok 13.",
        },
        # Baris 9 - 24 (13 Digunakan + 3 Backup -> Total: 19 Digunakan, 5 Backup)
        {
            "id_aset": "MON-0009",
            "merk": "LG",
            "tipe_model": "24MP400-B",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Customer Service shift pagi/sore Blok 14.",
        },
        {
            "id_aset": "MON-0010",
            "merk": "Samsung",
            "tipe_model": "S24R350",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Divisi Akuntansi Kantor Blok 13.",
        },
        {
            "id_aset": "MON-0011",
            "merk": "Dell",
            "tipe_model": "SE2422H",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja rekonsiliasi transaksi XML.",
        },
        {
            "id_aset": "MON-0012",
            "merk": "AOC",
            "tipe_model": "24B2XH",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Operasional Mess Blok 12 Office.",
        },
        {
            "id_aset": "MON-0013",
            "merk": "HP",
            "tipe_model": "P22v G4",
            "ukuran_layar": "21,5",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja administrasi gudang.",
        },
        {
            "id_aset": "MON-0014",
            "merk": "LG",
            "tipe_model": "19M38A-B",
            "ukuran_layar": "18,5",
            "resolusi_layar": "1366 × 768",
            "konektivitas": ["VGA"],
            "status": "Digunakan",
            "catatan": "Terhubung ke KVM Switch rak server Blok 14.",
        },
        {
            "id_aset": "MON-0015",
            "merk": "Samsung",
            "tipe_model": "S22F350FHE",
            "ukuran_layar": "21,5",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Backup",
            "catatan": "Cadangan di Kantor Blok 13.",
        },
        {
            "id_aset": "MON-0016",
            "merk": "Dell",
            "tipe_model": "UltraSharp U2722DE",
            "ukuran_layar": "27",
            "resolusi_layar": "2560 × 1440",
            "konektivitas": ["HDMI", "DisplayPort", "USB-C"],
            "status": "Digunakan",
            "catatan": "Monitor ruang server & network monitoring.",
        },
        {
            "id_aset": "MON-0017",
            "merk": "LG",
            "tipe_model": "24MK600M",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja tim komplain CS Blok 14.",
        },
        {
            "id_aset": "MON-0018",
            "merk": "AOC",
            "tipe_model": "E970SWNL",
            "ukuran_layar": "18,5",
            "resolusi_layar": "1366 × 768",
            "konektivitas": ["VGA"],
            "status": "Digunakan",
            "catatan": "Monitor lokal Server Transaksi MBL.",
        },
        {
            "id_aset": "MON-0019",
            "merk": "HP",
            "tipe_model": "V22v G5",
            "ukuran_layar": "21,5",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Backup",
            "catatan": "Cadangan operasional Ruko.",
        },
        {
            "id_aset": "MON-0020",
            "merk": "Samsung",
            "tipe_model": "LF24T350",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja kerja supervisor operasional.",
        },
        {
            "id_aset": "MON-0021",
            "merk": "Dell",
            "tipe_model": "E2016HV",
            "ukuran_layar": "19",
            "resolusi_layar": "1600 × 900",
            "konektivitas": ["VGA", "DVI"],
            "status": "Backup",
            "catatan": "Unit cadangan tes konsol server.",
        },
        {
            "id_aset": "MON-0022",
            "merk": "LG",
            "tipe_model": "24MP400-B",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja kasir & pembelian Blok 13.",
        },
        {
            "id_aset": "MON-0023",
            "merk": "HP",
            "tipe_model": "M24f",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
            "status": "Digunakan",
            "catatan": "Meja staf HR & GA Blok 14.",
        },
        {
            "id_aset": "MON-0024",
            "merk": "AOC",
            "tipe_model": "24G2E",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "DisplayPort"],
            "status": "Digunakan",
            "catatan": "Display CCTV multi-channel ruang sekuriti.",
        },
    ]

    return [_format_monitor_record(row) for row in seed_rows]


MOCK_MONITORS_DB: list[dict[str, Any]] = _seed_initial_monitors()


def _count_by_status() -> dict[str, int]:
    total_all = len(MOCK_MONITORS_DB)
    digunakan = sum(1 for m in MOCK_MONITORS_DB if m["status"] == "Digunakan")
    backup = sum(1 for m in MOCK_MONITORS_DB if m["status"] == "Backup")
    return {
        "Semua": total_all,
        "Digunakan": digunakan,
        "Backup": backup,
    }


def is_monitor_id_taken(id_aset: str, exclude_id: str = "") -> bool:
    """Periksa apakah ID Aset sudah dipakai oleh unit monitor lain."""
    norm_id = id_aset.strip().upper()
    norm_ex = exclude_id.strip().upper()
    for item in MOCK_MONITORS_DB:
        if item["id_aset"].upper() == norm_id and item["id_aset"].upper() != norm_ex:
            return True
    return False


def get_next_monitor_id() -> str:
    """Hasilkan saran ID Aset berikutnya (mis. MON-0025)."""
    max_num = 0
    for item in MOCK_MONITORS_DB:
        code = str(item["id_aset"])
        if code.startswith("MON-") and code[4:].isdigit():
            max_num = max(max_num, int(code[4:]))
    return f"MON-{max_num + 1:04d}"


def query_mock_monitors(
    status: str,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 8,
) -> dict[str, Any]:
    """Filter, urutkan, dan paginasi data monitor ({items, total, page, page_size})."""
    search = str(filters.get("search", "")).strip().lower()
    merk = str(filters.get("merk", "Semua"))
    ukuran = str(filters.get("ukuran_layar", "Semua"))
    resolusi = str(filters.get("resolusi_layar", "Semua"))
    konektivitas = str(filters.get("konektivitas", "Semua"))
    sort_by = str(filters.get("sort_by", "id_aset"))
    sort_dir = str(filters.get("sort_dir", "asc"))

    filtered: list[dict[str, Any]] = []
    for item in MOCK_MONITORS_DB:
        if status not in ("Semua", "") and item["status"] != status:
            continue
        if merk != "Semua" and item["merk"] != merk:
            continue
        if ukuran != "Semua" and item["ukuran_layar"] != ukuran:
            continue
        if resolusi != "Semua" and item["resolusi_layar"] != resolusi:
            continue
        if konektivitas != "Semua" and konektivitas not in item["konektivitas"]:
            continue
        if search:
            haystack = (
                f"{item['id_aset']} {item['merk']} {item['tipe_model']} "
                f"{item['ukuran_layar']} {item['resolusi_layar']}"
            ).lower()
            if search not in haystack:
                continue
        filtered.append(item)

    reverse = sort_dir == "desc"
    if sort_by == "ukuran_layar":
        filtered.sort(key=lambda x: float(x.get("ukuran_num", 0.0)), reverse=reverse)
    elif sort_by == "merk":
        filtered.sort(
            key=lambda x: (str(x.get("merk", "")).lower(), str(x.get("id_aset", ""))),
            reverse=reverse,
        )
    else:
        filtered.sort(key=lambda x: str(x.get("id_aset", "")), reverse=reverse)

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {
        "items": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "counts_by_status": _count_by_status(),
    }


def create_mock_monitor(payload: dict[str, Any]) -> dict[str, Any]:
    """Tambah satu unit monitor baru."""
    record = _format_monitor_record(payload)
    MOCK_MONITORS_DB.insert(0, record)
    return record


def update_mock_monitor(original_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Perbarui satu unit monitor berdasarkan ID aset awal."""
    norm_orig = original_id.strip().upper()
    for idx, existing in enumerate(MOCK_MONITORS_DB):
        if existing["id_aset"].upper() == norm_orig:
            raw = {
                **payload,
                "history_info": [
                    {
                        "event": "Pembaruan Data Monitor",
                        "date": "19 Okt 2026",
                        "note": (
                            f"Spesifikasi monitor {payload.get('id_aset', original_id)} "
                            "diperbarui oleh Admin IT."
                        ),
                    },
                    *existing.get("history_info", []),
                ],
            }
            updated = _format_monitor_record(raw)
            MOCK_MONITORS_DB[idx] = updated
            return updated
    return None


def delete_mock_monitor(id_aset: str) -> bool:
    """Hapus satu unit monitor dari daftar mock."""
    global MOCK_MONITORS_DB
    before = len(MOCK_MONITORS_DB)
    norm_id = id_aset.strip().upper()
    MOCK_MONITORS_DB = [m for m in MOCK_MONITORS_DB if m["id_aset"].upper() != norm_id]
    return len(MOCK_MONITORS_DB) < before


__all__ = [
    "MOCK_MONITORS_DB",
    "create_mock_monitor",
    "delete_mock_monitor",
    "format_inch_label",
    "get_next_monitor_id",
    "is_monitor_id_taken",
    "parse_inch_number",
    "query_mock_monitors",
    "update_mock_monitor",
]
