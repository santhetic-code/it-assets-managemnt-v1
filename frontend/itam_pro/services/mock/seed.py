"""
Unified Mock Database ITAM Pro (Tahap 6c-1).
Seluruh aset disimpan dalam satu tabel `MOCK_ASSETS` dengan field `attributes` (dict JSON)
dan `parent_asset_id`.
"""
import csv
import os
from copy import deepcopy
from datetime import datetime
from typing import Any

from itam_pro.services.category_config import (
    get_config_by_slug,
    get_prefix_for_category,
)

_BULAN_ID = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
]


def format_tanggal_id(iso_date: str) -> str:
    """Ubah YYYY-MM-DD menjadi '10 Nov 2025' atau '—' jika kosong."""
    if not iso_date or iso_date == "—":
        return "—"
    if any(b in iso_date for b in _BULAN_ID[1:]):
        return iso_date
    try:
        dt = datetime.strptime(iso_date.strip(), "%Y-%m-%d")
        return f"{dt.day:02d} {_BULAN_ID[dt.month]} {dt.year}"
    except ValueError:
        return iso_date


def format_ukuran_layar(val: Any) -> str:
    """Format angka ukuran layar menjadi berakhiran tanda kutip inci (mis. 24\")."""
    s = str(val or "").strip().replace('"', "")
    if not s or s == "—":
        return "—"
    return f'{s}"'
SEED_IDS: dict[str, str] = {
    "PC_IT_TIO": "PC-0001",
    "PC_FIN_01": "PC-0002",
    "PC_CS_TRX": "PC-0003",
    "PC_BACKUP_01": "PC-0004",
    "SRV_PROXMOX_01": "SRV-0001",
    "SRV_ZABBIX_02": "SRV-0002",
    "MON_LG_01": "MON-0001",
    "MON_DELL_02": "MON-0002",
    "MON_SAM_03": "MON-0003",
    "MON_AOC_04": "MON-0004",
    "MON_HP_05": "MON-0005",
    "UPS_APC_01": "UPS-0001",
    "UPS_ICA_02": "UPS-0002",
    "RTR_CORE_01": "RTR-0001",
    "SSD_SAM_01": "SSD-0001",
}


MOCK_ASSETS: list[dict[str, Any]] = [
    # --- KATEGORI PC & SERVER ---
    {
        "id_aset": "PC-0001",
        "nama_aset": "PC-IT-TIO",
        "kategori": "PC",
        "sn_pid": "SN-PC-2025-001",
        "tanggal_masuk_gudang": "2025-01-10",
        "tanggal_keluar_gudang": "2025-01-12",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Suryo Adji (IT & QA)",
        "catatan": "Workstation utama pengembangan & monitoring",
        "parent_asset_id": None,
        "attributes": {
            "jenis": "Operasional",
            "os": "Windows 11 Pro",
            "ram": "16 GB DDR4",
            "vga": "NVIDIA GTX 1650 4GB",
            "cpu": "Intel Core i5-12400F",
            "mainboard": "MSI PRO H610M-E",
            "hdd_ssd": "SSD NVMe 512 GB",
            "monitor": 'LG 24" (MON-0001)',
            "keyboard": "Logitech K120",
            "mouse": "Logitech B100",
        },
    },
    {
        "id_aset": "PC-0002",
        "nama_aset": "PC-FIN-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-2025-002",
        "tanggal_masuk_gudang": "2025-02-03",
        "tanggal_keluar_gudang": "2025-02-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Rina (Finance)",
        "catatan": "PC rekapitulasi invoice dan pajak",
        "parent_asset_id": None,
        "attributes": {
            "jenis": "Operasional",
            "os": "Windows 11 Pro",
            "ram": "16 GB DDR4",
            "vga": "Intel UHD 730",
            "cpu": "Intel Core i5-12400",
            "mainboard": "ASUS Prime H610M-K",
            "hdd_ssd": "SSD NVMe 512 GB",
            "monitor": 'Dell 24" (MON-0002)',
            "keyboard": "Logitech K120",
            "mouse": "Logitech B100",
        },
    },
    {
        "id_aset": "PC-0003",
        "nama_aset": "PC-CS-TRANSAKSI",
        "kategori": "PC",
        "sn_pid": "SN-PC-2024-019",
        "tanggal_masuk_gudang": "2024-08-14",
        "tanggal_keluar_gudang": "2024-08-15",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Bekas",
        "status": "Digunakan",
        "digunakan_oleh": "CS Shift Pagi/Malam",
        "catatan": "PC pemantauan transaksi pulsa",
        "parent_asset_id": None,
        "attributes": {
            "jenis": "Operasional",
            "os": "Windows 10 Pro",
            "ram": "8 GB DDR4",
            "vga": "Intel UHD 630",
            "cpu": "Intel Core i3-10105",
            "mainboard": "Gigabyte H410M",
            "hdd_ssd": "SSD SATA 256 GB",
            "monitor": 'Samsung 21,5" (MON-0003)',
            "keyboard": "Logitech K120",
            "mouse": "Logitech B100",
        },
    },
    {
        "id_aset": "PC-0004",
        "nama_aset": "PC-BACKUP-IT-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-004",
        "tanggal_masuk_gudang": "2024-11-20",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Bekas",
        "status": "Backup",
        "digunakan_oleh": "Cadangan Operasional Blok 14",
        "catatan": "Siap pakai bila ada PC operasional bermasalah",
        "parent_asset_id": None,
        "attributes": {
            "jenis": "Backup",
            "os": "Windows 11 Pro",
            "ram": "8 GB DDR4",
            "vga": "Intel UHD 630",
            "cpu": "Intel Core i3-10100",
            "mainboard": "ASRock H510M-HDV",
            "hdd_ssd": "SSD SATA 256 GB",
            "monitor": "—",
            "keyboard": "Logitech K120",
            "mouse": "Logitech B100",
        },
    },
    # --- KATEGORI MONITOR ---
    {
        "id_aset": "MON-0001",
        "nama_aset": 'LG 24MK600M 24"',
        "kategori": "Monitor",
        "sn_pid": "SN-LG-24MK-001",
        "tanggal_masuk_gudang": "2025-01-10",
        "tanggal_keluar_gudang": "2025-01-12",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Suryo Adji (IT & QA)",
        "catatan": "Monitor utama meja IT Support",
        "parent_asset_id": "PC-0001",
        "attributes": {
            "merk": "LG",
            "tipe_model": "24MK600M",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
        },
    },
    {
        "id_aset": "MON-0002",
        "nama_aset": 'Dell UltraSharp U2422H 24"',
        "kategori": "Monitor",
        "sn_pid": "SN-DELL-U24-002",
        "tanggal_masuk_gudang": "2025-02-01",
        "tanggal_keluar_gudang": "2025-02-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Rina (Finance)",
        "catatan": "Layar IPS kalibrasi warna",
        "parent_asset_id": "PC-0002",
        "attributes": {
            "merk": "Dell",
            "tipe_model": "UltraSharp U2422H",
            "ukuran_layar": "24",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "DisplayPort", "USB-C"],
        },
    },
    {
        "id_aset": "MON-0003",
        "nama_aset": 'Samsung S22F350 21,5"',
        "kategori": "Monitor",
        "sn_pid": "SN-SAM-22F-003",
        "tanggal_masuk_gudang": "2024-08-10",
        "tanggal_keluar_gudang": "2024-08-15",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Bekas",
        "status": "Digunakan",
        "digunakan_oleh": "CS Shift Pagi/Malam",
        "catatan": "Kondisi normal",
        "parent_asset_id": "PC-0003",
        "attributes": {
            "merk": "Samsung",
            "tipe_model": "S22F350",
            "ukuran_layar": "21,5",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
        },
    },
    {
        "id_aset": "MON-0004",
        "nama_aset": 'AOC 24G2SP 23,8"',
        "kategori": "Monitor",
        "sn_pid": "SN-AOC-24G-004",
        "tanggal_masuk_gudang": "2025-03-12",
        "tanggal_keluar_gudang": "2025-03-14",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "NOC Monitoring Wall",
        "catatan": "Display dashboard Grafana NOC",
        "parent_asset_id": None,
        "attributes": {
            "merk": "AOC",
            "tipe_model": "24G2SP",
            "ukuran_layar": "23,8",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "DisplayPort", "VGA"],
        },
    },
    {
        "id_aset": "MON-0005",
        "nama_aset": 'HP P22v G4 21,5"',
        "kategori": "Monitor",
        "sn_pid": "SN-HP-P22V-005",
        "tanggal_masuk_gudang": "2024-10-05",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Bekas",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Unit cadangan di rak gudang IT Blok 12",
        "parent_asset_id": None,
        "attributes": {
            "merk": "HP",
            "tipe_model": "P22v G4",
            "ukuran_layar": "21,5",
            "resolusi_layar": "1920 × 1080",
            "konektivitas": ["HDMI", "VGA"],
        },
    },
    # --- KATEGORI UPS & PERIFERAL LAINNYA ---
    {
        "id_aset": "UPS-0001",
        "nama_aset": "APC Smart-UPS 1500VA",
        "kategori": "UPS",
        "sn_pid": "SN-APC-1500-01",
        "tanggal_masuk_gudang": "2024-06-15",
        "tanggal_keluar_gudang": "2024-06-16",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Rak Server Utama Blok 14",
        "catatan": "Backup daya untuk Proxmox & Router Utama",
        "parent_asset_id": None,
        "attributes": {},
    },
    {
        "id_aset": "UPS-0002",
        "nama_aset": "ICA CE1200 1200VA",
        "kategori": "UPS",
        "sn_pid": "SN-ICA-1200-02",
        "tanggal_masuk_gudang": "2024-07-20",
        "tanggal_keluar_gudang": "2024-07-22",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Meja Transaksi CS Blok 13",
        "catatan": "Kondisi baterai sehat",
        "parent_asset_id": None,
        "attributes": {},
    },
    {
        "id_aset": "RTR-0001",
        "nama_aset": "MikroTik CCR2004-16G-2S+",
        "kategori": "Router",
        "sn_pid": "SN-MTK-CCR2004",
        "tanggal_masuk_gudang": "2024-04-01",
        "tanggal_keluar_gudang": "2024-04-02",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Core Gateway Antar Subnet",
        "catatan": "Dikelola via Winbox",
        "parent_asset_id": None,
        "attributes": {},
    },
    {
        "id_aset": "SSD-0001",
        "nama_aset": "Samsung 980 PRO NVMe 1TB",
        "kategori": "SSD",
        "sn_pid": "SN-SAM-980PRO-01",
        "tanggal_masuk_gudang": "2025-03-01",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Stok cadangan pengganti disk server",
        "parent_asset_id": None,
        "attributes": {},
    },
]


def _load_server_csv() -> list[dict[str, Any]]:
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "docs", "data", "rekap_watt_server.csv"
    )
    if not os.path.exists(csv_path):
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "docs", "data", "rekap_watt_server.csv"
        )
    servers: list[dict[str, Any]] = []
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            for row in reader:
                if row.get("ID SERVER", "").upper().startswith("ESTIMASI"):
                    continue

                nama_aset = row.get("ID SERVER", "").strip()
                if not nama_aset:
                    continue

                # Atribut inti sementara (DATA SEMENTARA - lengkapi)
                servers.append(
                    {
                        "id_aset": f"SRV-{len(servers) + 1:04d}",
                        "nama_aset": nama_aset,
                        "kategori": "Server",
                        "sn_pid": "-",
                        "tanggal_masuk_gudang": "2024-01-01",
                        "tanggal_keluar_gudang": "2024-01-02",
                        "kepemilikan": "XML",
                        "lokasi": "Kantor Pusat",
                        "kondisi": "Baru",
                        "status": "Digunakan",
                        "digunakan_oleh": "Operasional IT",
                        "catatan": "Diimpor dari rekap_watt_server.csv",
                        "parent_asset_id": None,
                        "attributes": {
                            "jenis": "Server",
                            "cpu": row.get("CPU", "") or row.get("MODEL PROSESOR (CPU)", ""),
                            "vga": row.get("GPU", "") or row.get("KARTU GRAFIS (GPU)", ""),
                            "ram": row.get("RAM", "") or row.get("KONFIGURASI RAM", ""),
                            "hdd_ssd": (
                                row.get("Penyimpanan", "")
                                or row.get("KONFIGURASI PENYIMPANAN", "")
                            ),
                            "tdp_total_w": (
                                row.get("TOTAL (W)")
                                or row.get("TOTAL TDP (W)")
                                or "0"
                            ).replace(",", "."),
                            "psu_min_w": (
                                row.get("PSU (Min)")
                                or row.get("PSU MINIMUM (W)")
                                or "0"
                            ).replace(",", "."),
                            "psu_rekomendasi_w": (
                                row.get("PSU (Rekomendasi)")
                                or row.get("PSU REKOMENDASI (W)")
                                or "0"
                            ).replace(",", "."),
                        },
                    }
                )
    return servers


MOCK_ASSETS.extend(_load_server_csv())


# Counter sekuensial per prefix agar ID Aset tidak pernah dipakai ulang
_PREFIX_COUNTERS: dict[str, int] = {
    "PC": 4,
    "SRV": 2,
    "MON": 5,
    "UPS": 2,
    "RTR": 1,
    "SSD": 1,
    "KBD": 0,
    "MSE": 0,
    "RAM": 0,
    "LPT": 0,
    "HDD": 0,
    "CMP": 0,
    "AST": 0,
}


def peek_next_asset_id(kategori: str) -> str:
    """Lihat kandidat ID Aset berikutnya untuk ditampilkan pada preview form."""
    prefix = get_prefix_for_category(kategori)
    current = _PREFIX_COUNTERS.get(prefix, 0)
    for item in MOCK_ASSETS:
        code = str(item.get("id_aset", ""))
        if code.startswith(f"{prefix}-"):
            num_part = code.split("-", 1)[1]
            if num_part.isdigit():
                current = max(current, int(num_part))
    _PREFIX_COUNTERS[prefix] = current
    return f"{prefix}-{current + 1:04d}"


def allocate_next_asset_id(kategori: str) -> str:
    """Alokasikan ID Aset baru secara permanen (tidak akan dipakai ulang)."""
    next_id = peek_next_asset_id(kategori)
    prefix = get_prefix_for_category(kategori)
    _PREFIX_COUNTERS[prefix] = _PREFIX_COUNTERS.get(prefix, 0) + 1
    return next_id


def flatten_asset_row(asset: dict[str, Any]) -> dict[str, Any]:
    """Ratakan dict `attributes` ke level atas untuk konsumsi `reusable_data_table`."""
    row = deepcopy(asset)
    attrs: dict[str, Any] = row.get("attributes") or {}
    for k, v in attrs.items():
        if k == "konektivitas":
            row[k] = list(v) if isinstance(v, list) else []
        else:
            row[k] = v if (v is not None and str(v).strip() != "") else "—"

    row["sn_pid"] = row.get("sn_pid") or "—"
    row["digunakan_oleh"] = row.get("digunakan_oleh") or "—"
    row["catatan"] = row.get("catatan") or "—"
    row["tanggal_masuk_display"] = format_tanggal_id(
        str(row.get("tanggal_masuk_gudang", ""))
    )
    row["tanggal_keluar_display"] = format_tanggal_id(
        str(row.get("tanggal_keluar_gudang", ""))
    )
    if "ukuran_layar" in attrs:
        row["ukuran_layar_display"] = format_ukuran_layar(attrs.get("ukuran_layar"))
    else:
        row["ukuran_layar_display"] = "—"
    return row


def find_sn_duplicate(sn_pid: str, exclude_id: str = "") -> str | None:
    """Kembalikan id_aset yang sudah memakai sn_pid serupa, atau None jika belum ada."""
    cleaned = sn_pid.strip()
    if not cleaned or cleaned in ("-", "—"):
        return None
    for item in MOCK_ASSETS:
        if item["id_aset"] == exclude_id:
            continue
        existing = str(item.get("sn_pid", "")).strip()
        if existing and existing not in ("-", "—") and existing.lower() == cleaned.lower():
            return str(item["id_aset"])
    return None


def get_mock_category_counts() -> dict[str, int]:
    """Hitung jumlah unit untuk Semua Aset dan setiap kategori pinned di Sidebar."""
    counts: dict[str, int] = {"all": len(MOCK_ASSETS)}
    for slug in ("pc", "monitor", "ups"):
        cfg = get_config_by_slug(slug)
        if cfg:
            inc = cfg["included_categories"]
            counts[slug] = sum(1 for a in MOCK_ASSETS if a.get("kategori") in inc)
    return counts


def query_mock_assets(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Query terpusat untuk `/assets` dan `/assets/c/[slug]`."""
    slug = str(filters.get("slug", "")).strip().lower()
    search = str(filters.get("search", "")).strip().lower()
    tab_value = str(filters.get("tab", "")).strip()
    sort_by = str(filters.get("sort_by", "")).strip()
    sort_dir = str(filters.get("sort_dir", "asc")).strip().lower()

    cfg = get_config_by_slug(slug) if slug else None
    base_items: list[dict[str, Any]] = []
    for raw in MOCK_ASSETS:
        if cfg and raw.get("kategori") not in cfg["included_categories"]:
            continue
        base_items.append(flatten_asset_row(raw))

    # Hitung jumlah per tab sebelum filter tab diterapkan
    tab_counts: dict[str, int] = {}
    if cfg and cfg.get("tab_field"):
        t_field = cfg["tab_field"]
        for opt in cfg.get("tab_options", []):
            if opt == "Semua":
                tab_counts[opt] = len(base_items)
            else:
                tab_counts[opt] = sum(
                    1 for item in base_items if str(item.get(t_field, "")) == opt
                )

    filtered: list[dict[str, Any]] = []
    for item in base_items:
        if cfg and cfg.get("tab_field") and tab_value and tab_value != "Semua":
            t_field = cfg["tab_field"]
            if str(item.get(t_field, "")) != tab_value:
                continue

        if search:
            haystack = " ".join(
                [
                    str(item.get("id_aset", "")),
                    str(item.get("nama_aset", "")),
                    str(item.get("kategori", "")),
                    str(item.get("sn_pid", "")),
                    str(item.get("digunakan_oleh", "")),
                    str(item.get("lokasi", "")),
                    " ".join(str(v) for v in (item.get("attributes") or {}).values()),
                ]
            ).lower()
            if search not in haystack:
                continue

        # Filter atribut inti
        for core_key in ("kategori", "kepemilikan", "lokasi", "kondisi", "status"):
            f_val = str(filters.get(core_key, "")).strip()
            if f_val and str(item.get(core_key, "")) != f_val:
                break
        else:
            # Filter atribut dinamis per kategori
            attr_match = True
            attr_filters: dict[str, str] = filters.get("attr_filters") or {}
            for ak, aval in attr_filters.items():
                if not aval:
                    continue
                item_val = item.get(ak)
                if ak == "ukuran_layar":
                    if format_ukuran_layar(item_val) != aval and str(item_val) != aval:
                        attr_match = False
                        break
                elif isinstance(item_val, list):
                    if aval not in item_val:
                        attr_match = False
                        break
                elif str(item_val or "") != aval:
                    attr_match = False
                    break

            if attr_match:
                filtered.append(item)

    if sort_by:
        reverse = sort_dir == "desc"

        def _sort_key(x: dict[str, Any]) -> Any:
            val = x.get(sort_by, "")
            if sort_by == "ukuran_layar":
                try:
                    return float(str(val).replace('"', "").replace(",", "."))
                except ValueError:
                    return 0.0
            return str(val).lower()

        filtered.sort(key=_sort_key, reverse=reverse)

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    return {
        "items": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "tab_counts": tab_counts,
        "category_counts": get_mock_category_counts(),
    }


def create_mock_assets(
    payload: dict[str, Any],
    count: int = 1,
) -> list[dict[str, Any]]:
    """Buat 1 atau N aset baru beserta `attributes` spesifikasinya."""
    created: list[dict[str, Any]] = []
    kategori = str(payload.get("kategori", "Lainnya"))
    attrs = deepcopy(payload.get("attributes") or {})

    if kategori == "Server":
        attrs["jenis"] = "Server"

    nama_aset = str(payload.get("nama_aset", "")).strip()
    if kategori == "Monitor" and not nama_aset:
        merk = str(attrs.get("merk", "")).strip()
        tipe = str(attrs.get("tipe_model", "")).strip()
        ukuran = format_ukuran_layar(attrs.get("ukuran_layar", ""))
        nama_aset = f"{merk} {tipe} {ukuran}".strip()

    for _ in range(max(1, count)):
        new_id = allocate_next_asset_id(kategori)
        record: dict[str, Any] = {
            "id_aset": new_id,
            "nama_aset": nama_aset,
            "kategori": kategori,
            "sn_pid": str(payload.get("sn_pid", "")).strip(),
            "tanggal_masuk_gudang": str(payload.get("tanggal_masuk_gudang", "")).strip(),
            "tanggal_keluar_gudang": str(payload.get("tanggal_keluar_gudang", "")).strip(),
            "kepemilikan": str(payload.get("kepemilikan", "XML")).strip(),
            "lokasi": str(payload.get("lokasi", "Kantor Blok 14")).strip(),
            "kondisi": str(payload.get("kondisi", "Baru")).strip(),
            "status": str(payload.get("status", "Digunakan")).strip(),
            "digunakan_oleh": str(payload.get("digunakan_oleh", "")).strip(),
            "catatan": str(payload.get("catatan", "")).strip(),
            "parent_asset_id": payload.get("parent_asset_id"),
            "attributes": deepcopy(attrs),
        }
        MOCK_ASSETS.insert(0, record)
        created.append(flatten_asset_row(record))
    return created


def update_mock_asset(
    asset_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Perbarui satu record aset dan `attributes`-nya berdasarkan `id_aset`."""
    for idx, item in enumerate(MOCK_ASSETS):
        if item["id_aset"] == asset_id:
            kategori = str(payload.get("kategori", item["kategori"]))
            attrs = deepcopy(payload.get("attributes") or item.get("attributes") or {})
            if kategori == "Server":
                attrs["jenis"] = "Server"

            nama_aset = str(payload.get("nama_aset", item["nama_aset"])).strip()
            if kategori == "Monitor":
                merk = str(attrs.get("merk", "")).strip()
                tipe = str(attrs.get("tipe_model", "")).strip()
                ukuran = format_ukuran_layar(attrs.get("ukuran_layar", ""))
                if merk and tipe:
                    nama_aset = f"{merk} {tipe} {ukuran}".strip()

            updated: dict[str, Any] = {
                **item,
                "nama_aset": nama_aset,
                "kategori": kategori,
                "sn_pid": str(payload.get("sn_pid", item.get("sn_pid", ""))).strip(),
                "tanggal_masuk_gudang": str(
                    payload.get("tanggal_masuk_gudang", item.get("tanggal_masuk_gudang", ""))
                ).strip(),
                "tanggal_keluar_gudang": str(
                    payload.get(
                        "tanggal_keluar_gudang", item.get("tanggal_keluar_gudang", "")
                    )
                ).strip(),
                "kepemilikan": str(
                    payload.get("kepemilikan", item.get("kepemilikan", "XML"))
                ).strip(),
                "lokasi": str(payload.get("lokasi", item.get("lokasi", ""))).strip(),
                "kondisi": str(payload.get("kondisi", item.get("kondisi", "Baru"))).strip(),
                "status": str(payload.get("status", item.get("status", "Digunakan"))).strip(),
                "digunakan_oleh": str(
                    payload.get("digunakan_oleh", item.get("digunakan_oleh", ""))
                ).strip(),
                "catatan": str(payload.get("catatan", item.get("catatan", ""))).strip(),
                "attributes": attrs,
            }
            MOCK_ASSETS[idx] = updated
            return flatten_asset_row(updated)
    return None


def delete_mock_asset(asset_id: str) -> bool:
    """Hapus satu unit aset dari `MOCK_ASSETS` (ID Aset tidak dipakai ulang)."""
    for idx, item in enumerate(MOCK_ASSETS):
        if item["id_aset"] == asset_id:
            MOCK_ASSETS.pop(idx)
            return True
    return False


__all__ = [
    "MOCK_ASSETS",
    "SEED_IDS",
    "allocate_next_asset_id",
    "create_mock_assets",
    "delete_mock_asset",
    "find_sn_duplicate",
    "flatten_asset_row",
    "format_tanggal_id",
    "format_ukuran_layar",
    "get_mock_category_counts",
    "peek_next_asset_id",
    "query_mock_assets",
    "update_mock_asset",
]
