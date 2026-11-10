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


def _load_real_77_assets_from_csv() -> list[dict[str, Any]]:
    """Memuat 77 aset nyata (33 PC + 16 Server + 4 Monitor + 24 UPS) dari docs/data/."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "docs", "data")
    if not os.path.exists(base_dir):
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "data")

    loaded: list[dict[str, Any]] = []
    srv_path = os.path.join(base_dir, "rekap_watt_server.csv")
    ups_path = os.path.join(base_dir, "rekap_ups_xml.csv")
    ip_path = os.path.join(base_dir, "ip_list_xml.csv")

    if not (os.path.exists(srv_path) and os.path.exists(ups_path) and os.path.exists(ip_path)):
        return []

    # 1. 16 Server dari rekap_watt_server.csv
    with open(srv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            nama_srv = (row.get("ID SERVER") or "").strip()
            if not nama_srv or nama_srv.upper().startswith("ESTIMASI"):
                continue
            idx_srv = sum(1 for x in loaded if x["kategori"] == "Server") + 1
            is_bkp = "BACKUP" in nama_srv.upper()
            loaded.append(
                {
                    "id_aset": f"SRV-{idx_srv:03d}",
                    "nama_aset": nama_srv,
                    "kategori": "Server",
                    "sn_pid": "—",
                    "tanggal_masuk_gudang": "2025-01-10",
                    "tanggal_keluar_gudang": "" if is_bkp else "2025-01-12",
                    "kepemilikan": "XML",
                    "lokasi": "Head Office (Blok 14)",
                    "kondisi": "Baik",
                    "status": "Cadangan" if is_bkp else "Digunakan",
                    "digunakan_oleh": "—",
                    "catatan": "Server Fisik",
                    "parent_asset_id": None,
                    "purchase_item_id": 1 if idx_srv <= 8 else None,
                    "terkait_chips": (
                        ["UPS 1", "IP 1", "VM 3"] if not is_bkp else ["UPS 1", "IP 1"]
                    ),
                    "attributes": {
                        "jenis": "Backup" if is_bkp else "Server",
                        "os": (
                            "Proxmox VE 8.2" if "VM" in nama_srv.upper() else "Windows Server 2022"
                        ),
                        "cpu": (row.get("MODEL PROSESOR (CPU)") or "").strip(),
                        "vga": (row.get("KARTU GRAFIS (GPU)") or "").strip(),
                        "ram": (row.get("KONFIGURASI RAM") or "").strip(),
                        "hdd_ssd": (row.get("KONFIGURASI PENYIMPANAN") or "").strip(),
                        "tdp_total_w": (row.get("TOTAL TDP (W)") or "0").strip(),
                        "psu_min_w": (row.get("PSU MINIMUM (W)") or "0").strip(),
                        "psu_rekomendasi_w": (row.get("PSU REKOMENDASI (W)") or "0").strip(),
                    },
                }
            )

    # 2. 33 PC Operasional dari ip_list_xml.csv
    with open(ip_path, encoding="utf-8-sig") as f:
        raw_rows = list(csv.reader(f))
        pc_num = 0
        for r in raw_rows[2:]:
            if len(r) > 8 and r[8].strip():
                user_name = r[7].strip()
                pc_num += 1
                code = f"PC-{pc_num:03d}"
                has_mon = code in ("PC-003", "PC-016", "PC-001")
                chips = ["Monitor 1", "IP 1"]
                if code == "PC-003":
                    chips.append("Kredensial 2")
                loaded.append(
                    {
                        "id_aset": code,
                        "nama_aset": f"PC {user_name}".strip(),
                        "kategori": "PC",
                        "sn_pid": f"SN-PC-{pc_num:03d}",
                        "tanggal_masuk_gudang": "2025-03-10",
                        "tanggal_keluar_gudang": "2025-03-12",
                        "kepemilikan": "XML",
                        "lokasi": "Head Office",
                        "kondisi": "Baik",
                        "status": "Digunakan",
                        "digunakan_oleh": user_name,
                        "catatan": f"Workstation {user_name}",
                        "parent_asset_id": None,
                        "purchase_item_id": 1 if pc_num <= 16 else None,
                        "terkait_chips": chips if has_mon else ["IP 1"],
                        "attributes": {
                            "jenis": "Operasional",
                            "os": "Windows 11 Pro",
                            "cpu": "Intel Core i5-12400",
                            "ram": "16GB DDR4",
                            "vga": "Intel UHD Graphics 730",
                            "hdd_ssd": "SSD NVMe 512GB",
                            "mainboard": "ASUS Prime H610M",
                            "monitor": (
                                '24" FHD (MON-001)'
                                if code == "PC-003"
                                else ('24" FHD' if has_mon else "—")
                            ),
                        },
                    }
                )

    # 3. 4 Monitor (3 terpasang di PC, 1 Cadangan di Gudang sesuai Artboard 10)
    mon_defs = [
        (
            "MON-001",
            'Samsung S24D330 24"',
            "Samsung",
            "S24D330",
            "Terpasang di PC-003",
            "Head Office",
            "Digunakan",
            "PC-003",
            ["PC 1"],
        ),
        (
            "MON-002",
            'Samsung S24D330 24"',
            "Samsung",
            "S24D330",
            "Terpasang di PC-016",
            "Head Office",
            "Digunakan",
            "PC-016",
            ["PC 1"],
        ),
        (
            "MON-003",
            'Samsung S24D330 24"',
            "Samsung",
            "S24D330",
            "Terpasang di PC-001",
            "Head Office",
            "Digunakan",
            "PC-001",
            ["PC 1"],
        ),
        ("MON-004", 'LG 24MR400-B 24"', "LG", "24MR400-B", "—", "Gudang", "Cadangan", None, []),
    ]
    for m_id, m_nama, m_merk, m_tipe, m_user, m_lok, m_st, m_parent, m_chips in mon_defs:
        loaded.append(
            {
                "id_aset": m_id,
                "nama_aset": m_nama,
                "kategori": "Monitor",
                "sn_pid": f"SN-{m_id}",
                "tanggal_masuk_gudang": "2025-04-01",
                "tanggal_keluar_gudang": "2025-04-02" if m_st == "Digunakan" else "",
                "kepemilikan": "XML",
                "lokasi": m_lok,
                "kondisi": "Baik",
                "status": m_st,
                "digunakan_oleh": m_user,
                "catatan": "Monitor 24 inch FHD",
                "parent_asset_id": m_parent,
                "purchase_item_id": 1,
                "terkait_chips": m_chips,
                "attributes": {
                    "merk": m_merk,
                    "tipe_model": m_tipe,
                    "ukuran_layar": "24",
                    "resolusi_layar": "1920 × 1080",
                    "konektivitas": ["HDMI", "VGA"],
                },
            }
        )

    # 4. 24 UPS dari rekap_ups_xml.csv
    with open(ups_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            raw_id = (row.get("ID UPS") or "").strip().replace(" ", "")
            if not raw_id:
                continue
            merk = (row.get("MERK UPS") or "").strip()
            aki = (row.get("KATEGORI AKI") or "").strip()
            va_raw = (
                "".join(ch for ch in (row.get("KAPASITAS (VA/WATT)") or "") if ch.isdigit())
                or "650"
            )
            st_ops = (row.get("STATUS OPERASIONAL") or "").strip().upper()
            id_srv = (row.get("ID SERVER") or "").strip()
            is_used = st_ops == "DIGUNAKAN"
            penempatan = (
                f"Menyuplai SERVER {id_srv}" if (is_used and id_srv and id_srv != "BACKUP") else "—"
            )
            loaded.append(
                {
                    "id_aset": raw_id,
                    "nama_aset": f"UPS {merk} {va_raw}VA ({aki.title()})",
                    "kategori": "UPS",
                    "sn_pid": f"SN-{raw_id}",
                    "tanggal_masuk_gudang": "2025-06-15",
                    "tanggal_keluar_gudang": "2025-06-16" if is_used else "",
                    "kepemilikan": "XML",
                    "lokasi": "Head Office (Blok 14)" if is_used else "Gudang",
                    "kondisi": "Baru",
                    "status": "Digunakan" if is_used else "Cadangan",
                    "digunakan_oleh": penempatan,
                    "catatan": f"Kapasitas {va_raw}VA",
                    "parent_asset_id": None,
                    "purchase_item_id": 1 if len(loaded) % 2 == 0 else None,
                    "terkait_chips": ["Server 1"] if is_used and id_srv else [],
                    "attributes": {
                        "kapasitas_va": va_raw,
                        "jenis_aki": aki.title(),
                    },
                }
            )
    return loaded


def _load_server_csv() -> list[dict[str, Any]]:
    """Kompatibilitas pemuat CSV server untuk unit test."""
    return [a for a in _load_real_77_assets_from_csv() if a.get("kategori") == "Server"]


_CSV_77_ASSETS = _load_real_77_assets_from_csv()
if _CSV_77_ASSETS:
    MOCK_ASSETS.clear()
    MOCK_ASSETS.extend(_CSV_77_ASSETS)

_ARTBOARD_12_COMPONENTS: list[dict[str, Any]] = [
    {
        "id_aset": "RAM-014",
        "nama_aset": "RAM DDR4 8 GB",
        "kategori": "RAM",
        "sn_pid": "SN-RAM-014",
        "tanggal_masuk_gudang": "2025-06-01",
        "tanggal_keluar_gudang": "2025-06-02",
        "kepemilikan": "XML",
        "lokasi": "Head Office",
        "kondisi": "Baik",
        "status": "Digunakan",
        "digunakan_oleh": "Terpasang di PC-003",
        "catatan": "Modul RAM Slot 1",
        "parent_asset_id": "PC-003",
        "purchase_item_id": 1,
        "terkait_chips": ["PC 1"],
        "attributes": {
            "tipe": "DDR4",
            "kapasitas_gb": 8,
            "slot": "DIMM 1",
            "dipasang_sejak": "Jun 2025",
            "data_status": "Kosong",
        },
    },
    {
        "id_aset": "RAM-015",
        "nama_aset": "RAM DDR4 8 GB",
        "kategori": "RAM",
        "sn_pid": "SN-RAM-015",
        "tanggal_masuk_gudang": "2025-06-01",
        "tanggal_keluar_gudang": "2025-06-02",
        "kepemilikan": "XML",
        "lokasi": "Head Office",
        "kondisi": "Baik",
        "status": "Digunakan",
        "digunakan_oleh": "Terpasang di PC-003",
        "catatan": "Modul RAM Slot 2",
        "parent_asset_id": "PC-003",
        "purchase_item_id": 1,
        "terkait_chips": ["PC 1"],
        "attributes": {
            "tipe": "DDR4",
            "kapasitas_gb": 8,
            "slot": "DIMM 2",
            "dipasang_sejak": "Jun 2025",
            "data_status": "Kosong",
        },
    },
    {
        "id_aset": "SSD-009",
        "nama_aset": "SSD NVMe 512 GB",
        "kategori": "SSD",
        "sn_pid": "SN-SSD-009",
        "tanggal_masuk_gudang": "2025-06-01",
        "tanggal_keluar_gudang": "2025-06-02",
        "kepemilikan": "XML",
        "lokasi": "Head Office",
        "kondisi": "Baik",
        "status": "Digunakan",
        "digunakan_oleh": "Terpasang di PC-003",
        "catatan": "NVMe OS Boot Drive",
        "parent_asset_id": "PC-003",
        "purchase_item_id": 1,
        "terkait_chips": ["PC 1"],
        "attributes": {
            "tipe": "NVMe",
            "kapasitas_gb": 512,
            "slot": "M.2",
            "dipasang_sejak": "Jun 2025",
            "data_status": "Berisi data",
        },
    },
    {
        "id_aset": "RAM-021",
        "nama_aset": "RAM DDR4 - 8 GB",
        "kategori": "RAM",
        "sn_pid": "SN-RAM-021",
        "tanggal_masuk_gudang": "2025-07-10",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Gudang",
        "kondisi": "Baru",
        "status": "Cadangan",
        "digunakan_oleh": "Cadangan - Gudang",
        "catatan": "Siap pakai",
        "parent_asset_id": None,
        "purchase_item_id": 1,
        "terkait_chips": [],
        "attributes": {
            "tipe": "DDR4",
            "kapasitas_gb": 8,
            "slot": "DIMM 1",
            "dipasang_sejak": "-",
            "data_status": "Kosong",
        },
    },
    {
        "id_aset": "SSD-012",
        "nama_aset": "SSD SATA - 480 GB",
        "kategori": "SSD",
        "sn_pid": "SN-SSD-012",
        "tanggal_masuk_gudang": "2025-07-12",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Gudang",
        "kondisi": "Baik",
        "status": "Cadangan",
        "digunakan_oleh": "Cadangan - Gudang",
        "catatan": "Berisi data, belum di-wipe",
        "parent_asset_id": None,
        "purchase_item_id": 1,
        "terkait_chips": [],
        "attributes": {
            "tipe": "SATA",
            "kapasitas_gb": 480,
            "slot": "SATA 1",
            "dipasang_sejak": "-",
            "data_status": "Berisi data",
        },
    },
]
MOCK_ASSETS.extend(_ARTBOARD_12_COMPONENTS)


# Counter sekuensial per prefix agar ID Aset tidak pernah dipakai ulang
_PREFIX_COUNTERS: dict[str, int] = {
    "PC": 33,
    "SRV": 16,
    "MON": 4,
    "UPS": 24,
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
    row["terkait_chips"] = list(row.get("terkait_chips") or [])
    row["tanggal_masuk_display"] = format_tanggal_id(str(row.get("tanggal_masuk_gudang", "")))
    row["tanggal_keluar_display"] = format_tanggal_id(str(row.get("tanggal_keluar_gudang", "")))
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
    """Hitung jumlah unit untuk Semua Aset, PC & Laptop (33), Server (16), Monitor (4), UPS (24)."""
    counts: dict[str, int] = {
        "all": len(MOCK_ASSETS),
        "pc": sum(1 for a in MOCK_ASSETS if a.get("kategori") in ("PC", "Laptop")),
        "server": sum(1 for a in MOCK_ASSETS if a.get("kategori") == "Server"),
        "monitor": sum(1 for a in MOCK_ASSETS if a.get("kategori") == "Monitor"),
        "ups": sum(1 for a in MOCK_ASSETS if a.get("kategori") == "UPS"),
        "perangkat-it": sum(
            1
            for a in MOCK_ASSETS
            if a.get("kategori") in ("PC", "Laptop", "Server", "Monitor", "UPS")
        ),
        "komponen-periferal": sum(
            1
            for a in MOCK_ASSETS
            if a.get("kategori")
            in ("RAM", "SSD", "HDD", "SSD/HDD", "VGA", "PSU", "Keyboard", "Mouse")
        ),
        "jaringan": sum(
            1
            for a in MOCK_ASSETS
            if a.get("kategori") in ("Router", "Router/Switch", "Access Point", "CCTV", "Jaringan")
        ),
        "kendaraan": sum(
            1 for a in MOCK_ASSETS if a.get("kategori") in ("Mobil", "Motor", "Kendaraan")
        ),
        "peralatan-kantor": sum(1 for a in MOCK_ASSETS if a.get("kategori") == "AC"),
        "furnitur": sum(
            1 for a in MOCK_ASSETS if a.get("kategori") in ("Meja", "Kursi", "Lemari", "Furnitur")
        ),
        "lainnya": sum(1 for a in MOCK_ASSETS if a.get("kategori") in ("Lainnya", "Aset lain")),
    }
    return counts


_GROUP_CATEGORY_MAP: dict[str, tuple[str, ...]] = {
    "perangkat-it": ("PC", "Laptop", "Server", "Monitor", "UPS"),
    "komponen-periferal": ("RAM", "SSD", "HDD", "SSD/HDD", "VGA", "PSU", "Keyboard", "Mouse"),
    "jaringan": ("Router", "Router/Switch", "Access Point", "CCTV", "Jaringan"),
    "kendaraan": ("Mobil", "Motor", "Kendaraan"),
    "peralatan-kantor": ("AC",),
    "furnitur": ("Meja", "Kursi", "Lemari", "Furnitur"),
    "lainnya": ("Lainnya", "Aset lain"),
}


def query_mock_assets(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Query terpusat untuk `/assets` dan `/assets?category=[slug]`."""
    slug = str(filters.get("category") or filters.get("slug") or "").strip().lower()
    group_key = str(filters.get("group", "")).strip().lower()
    search = str(filters.get("search", "")).strip().lower()
    tab_value = str(filters.get("tab", "")).strip()
    pengguna = str(filters.get("pengguna", "")).strip().lower()
    warranty = str(filters.get("warranty", "")).strip().lower()
    no_purchase = int(filters.get("no_purchase") or 0)
    sort_by = str(filters.get("sort_by", "")).strip()
    sort_dir = str(filters.get("sort_dir", "asc")).strip().lower()

    cfg = get_config_by_slug(slug) if slug else None
    allowed_group_cats = _GROUP_CATEGORY_MAP.get(group_key) if group_key else None

    base_items: list[dict[str, Any]] = []
    for raw in MOCK_ASSETS:
        if cfg and raw.get("kategori") not in cfg["included_categories"]:
            continue
        if allowed_group_cats is not None and raw.get("kategori") not in allowed_group_cats:
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
                tab_counts[opt] = sum(1 for item in base_items if str(item.get(t_field, "")) == opt)

    filtered: list[dict[str, Any]] = []
    for item in base_items:
        if cfg and cfg.get("tab_field") and tab_value and tab_value != "Semua":
            t_field = cfg["tab_field"]
            if str(item.get(t_field, "")) != tab_value:
                continue

        if pengguna and pengguna not in str(item.get("digunakan_oleh", "")).lower():
            continue

        if no_purchase == 1 and item.get("purchase_item_id"):
            continue

        if warranty == "expiring" and not str(item.get("id_aset", "")).endswith(("001", "002")):
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
        status_f = str(filters.get("status", "")).strip()
        if status_f.lower() in ("attention", "perlu_perhatian"):
            if item.get("status") not in (
                "Dalam Perbaikan",
                "Rusak",
                "Perbaikan",
            ) and item.get("kondisi") not in ("Perlu Servis", "Rusak"):
                continue

        core_ok = True
        for core_key in ("kategori", "kepemilikan", "lokasi", "kondisi", "status"):
            if core_key == "status" and status_f.lower() in ("attention", "perlu_perhatian"):
                continue
            f_val = str(filters.get(core_key, "")).strip()
            if f_val and str(item.get(core_key, "")) != f_val:
                core_ok = False
                break

        if core_ok:
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

    cat_counts = get_mock_category_counts()
    unlinked_cnt = sum(1 for a in MOCK_ASSETS if not a.get("purchase_item_id"))
    attention_cnt = sum(
        1
        for a in MOCK_ASSETS
        if a.get("status") in ("Dalam Perbaikan", "Rusak", "Perbaikan")
        or a.get("kondisi") in ("Perlu Servis", "Rusak")
    )
    return {
        "items": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "tab_counts": tab_counts,
        "category_counts": cat_counts,
        "group_counts": cat_counts,
        "subcategory_counts": {
            "pc": cat_counts["pc"],
            "server": cat_counts["server"],
            "monitor": cat_counts["monitor"],
            "ups": cat_counts["ups"],
        },
        "summary": {
            "total": len(MOCK_ASSETS),
            "perlu_perhatian": attention_cnt,
            "garansi_segera_habis": 5,
            "belum_terhubung_pembelian": unlinked_cnt,
        },
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
                    payload.get("tanggal_keluar_gudang", item.get("tanggal_keluar_gudang", ""))
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
