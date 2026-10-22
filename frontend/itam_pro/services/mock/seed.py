"""
Unified Mock Database ITAM Pro.
Menyimpan tabel `assets`, `pc_specs`, dan `monitor_specs` dalam memori
dan melakukan relasional join secara langsung layaknya database SQL.
"""
from typing import Any

BULAN_ID: list[str] = [
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


def format_date_id(iso_date: str | None) -> str:
    """Ubah YYYY-MM-DD menjadi format Indonesia '12 Mar 2027' atau '—' jika kosong."""
    if not iso_date:
        return "—"
    val = iso_date.strip()
    if not val or val in ("—", "-"):
        return "—"
    parts = val.split("-")
    if len(parts) != 3:
        return val
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{day:02d} {BULAN_ID[month]} {year}"
    except (ValueError, IndexError):
        return val


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


# ==============================================================================
# 1. TABEL UTAMA: ASSETS (Fisik)
# ==============================================================================
mock_assets_db: list[dict[str, Any]] = [
    # --- 24 UNIT MONITOR (19 Digunakan, 5 Backup) ---
    {
        "id_aset": "MON-0001",
        "nama_aset": "LG 24MK600M 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-LG-24MK-001",
        "tanggal_masuk_gudang": "2024-01-10",
        "tanggal_keluar_gudang": "2024-01-12",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Tio (QA)",
        "catatan": "Monitor utama meja operasional Kantor Blok 14.",
    },
    {
        "id_aset": "MON-0002",
        "nama_aset": "LG 24MK600M 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-LG-24MK-002",
        "tanggal_masuk_gudang": "2024-01-10",
        "tanggal_keluar_gudang": "2024-01-12",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Tio (QA)",
        "catatan": "Monitor kedua (dual setup) operasional Blok 14.",
    },
    {
        "id_aset": "MON-0003",
        "nama_aset": "Dell UltraSharp U2422H 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-DELL-U24-003",
        "tanggal_masuk_gudang": "2024-02-01",
        "tanggal_keluar_gudang": "2024-02-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Rian (Lead Dev)",
        "catatan": "Digunakan di workstation tim IT Support & QA.",
    },
    {
        "id_aset": "MON-0004",
        "nama_aset": "Samsung S27R350 27 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-SAM-S27-004",
        "tanggal_masuk_gudang": "2024-02-15",
        "tanggal_keluar_gudang": "2024-02-20",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "NOC Team",
        "catatan": "Monitor dashboard monitoring Zabbix & Grafana.",
    },
    {
        "id_aset": "MON-0005",
        "nama_aset": "AOC 22B1HS 21,5 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-AOC-22B-005",
        "tanggal_masuk_gudang": "2024-03-01",
        "tanggal_keluar_gudang": "2024-03-02",
        "kepemilikan": "XML",
        "lokasi": "Ruko",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Siti (Admin)",
        "catatan": "Meja kerja admin Ruko.",
    },
    {
        "id_aset": "MON-0006",
        "nama_aset": "LG 22MK430H 21,5 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-LG-22MK-006",
        "tanggal_masuk_gudang": "2024-03-10",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Unit cadangan siap pakai di rak gudang IT Blok 12.",
    },
    {
        "id_aset": "MON-0007",
        "nama_aset": "Dell P2422H 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-DELL-P24-007",
        "tanggal_masuk_gudang": "2024-03-15",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Cadangan pengganti monitor operasional utama.",
    },
    {
        "id_aset": "MON-0008",
        "nama_aset": "HP P24v G4 23,8 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-HP-P24-008",
        "tanggal_masuk_gudang": "2024-04-01",
        "tanggal_keluar_gudang": "2024-04-05",
        "kepemilikan": "MBL",
        "lokasi": "Mess Blok 12 Office",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Budi (Support)",
        "catatan": "Monitor meja operasional Mess Blok 12 Office.",
    },
    {
        "id_aset": "MON-0009",
        "nama_aset": "Samsung Odyssey G5 27 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-SAM-G5-009",
        "tanggal_masuk_gudang": "2024-04-10",
        "tanggal_keluar_gudang": "2024-04-12",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Desain Grafis",
        "catatan": "Dipakai editor multimedia dan grafis.",
    },
    {
        "id_aset": "MON-0010",
        "nama_aset": "AOC 24G2SP 23,8 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-AOC-24G-010",
        "tanggal_masuk_gudang": "2024-04-15",
        "tanggal_keluar_gudang": "2024-04-18",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Andi (DevOps)",
        "catatan": "Setup workstation DevOps Blok 14.",
    },
    {
        "id_aset": "MON-0011",
        "nama_aset": "LG 24MP400 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-LG-24MP-011",
        "tanggal_masuk_gudang": "2024-05-01",
        "tanggal_keluar_gudang": "2024-05-03",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Finance",
        "catatan": "Layar staff finance Blok 13.",
    },
    {
        "id_aset": "MON-0012",
        "nama_aset": "Dell E1916HV 18,5 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-DELL-E19-012",
        "tanggal_masuk_gudang": "2024-05-10",
        "tanggal_keluar_gudang": "2024-05-12",
        "kepemilikan": "MBL",
        "lokasi": "Ruko",
        "kondisi": "Bekas",
        "status": "Digunakan",
        "digunakan_oleh": "Kasir / Gudang",
        "catatan": "Monitor display POS kasir gudang logistik.",
    },
    {
        "id_aset": "MON-0013",
        "nama_aset": "HP V214a 20,7 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-HP-V21-013",
        "tanggal_masuk_gudang": "2024-05-20",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Unit cadangan di gudang IT Blok 12.",
    },
    {
        "id_aset": "MON-0014",
        "nama_aset": "Samsung S24R350 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-SAM-S24-014",
        "tanggal_masuk_gudang": "2024-06-01",
        "tanggal_keluar_gudang": "2024-06-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "HRD",
        "catatan": "Meja HRD Kantor Blok 14.",
    },
    {
        "id_aset": "MON-0015",
        "nama_aset": "AOC 27V2Q 27 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-AOC-27V-015",
        "tanggal_masuk_gudang": "2024-06-10",
        "tanggal_keluar_gudang": "2024-06-15",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Ruang Meeting",
        "catatan": "Meja rapat kecil Blok 14.",
    },
    {
        "id_aset": "MON-0016",
        "nama_aset": "LG 27UP650 27 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-LG-27UP-016",
        "tanggal_masuk_gudang": "2024-06-20",
        "tanggal_keluar_gudang": "2024-06-22",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "CTO Office",
        "catatan": "Monitor 4K ruang direksi.",
    },
    {
        "id_aset": "MON-0017",
        "nama_aset": "Dell UltraSharp U2723QE 27 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-DELL-U27-017",
        "tanggal_masuk_gudang": "2024-07-01",
        "tanggal_keluar_gudang": "2024-07-03",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Senior Architect",
        "catatan": "Workstation software architect Blok 14.",
    },
    {
        "id_aset": "MON-0018",
        "nama_aset": "HP EliteDisplay E243 23,8 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-HP-E24-018",
        "tanggal_masuk_gudang": "2024-07-10",
        "tanggal_keluar_gudang": "2024-07-15",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Marketing",
        "catatan": "Meja kerja tim pemasaran Blok 13.",
    },
    {
        "id_aset": "MON-0019",
        "nama_aset": "Samsung S19A330 18,5 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-SAM-S19-019",
        "tanggal_masuk_gudang": "2024-07-20",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Bekas",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Unit darurat port VGA di rak Blok 12.",
    },
    {
        "id_aset": "MON-0020",
        "nama_aset": "AOC 24B2XH 23,8 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-AOC-24B-020",
        "tanggal_masuk_gudang": "2024-08-01",
        "tanggal_keluar_gudang": "2024-08-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Customer Care",
        "catatan": "Operasional CS Blok 14.",
    },
    {
        "id_aset": "MON-0021",
        "nama_aset": "LG 24GN60R 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-LG-24GN-021",
        "tanggal_masuk_gudang": "2024-08-10",
        "tanggal_keluar_gudang": "2024-08-12",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "QA Automation",
        "catatan": "Testing lab QA Blok 14.",
    },
    {
        "id_aset": "MON-0022",
        "nama_aset": "Dell SE2422H 24 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-DELL-SE24-022",
        "tanggal_masuk_gudang": "2024-08-15",
        "tanggal_keluar_gudang": "2024-08-18",
        "kepemilikan": "MBL",
        "lokasi": "Mess Blok 12 Office",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Staff Operasional",
        "catatan": "Workstation Mess Blok 12 Office.",
    },
    {
        "id_aset": "MON-0023",
        "nama_aset": "HP M24f 23,8 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-HP-M24-023",
        "tanggal_masuk_gudang": "2024-09-01",
        "tanggal_keluar_gudang": "2024-09-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Legal & Audit",
        "catatan": "Meja legal & compliance Blok 13.",
    },
    {
        "id_aset": "MON-0024",
        "nama_aset": "AOC Q27V4 27 inci",
        "kategori": "Monitor",
        "sn_pid": "SN-AOC-Q27-024",
        "tanggal_masuk_gudang": "2024-09-10",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Monitor 2K QHD cadangan tim riset.",
    },

    # --- 24 UNIT PC (8 Operasional, 8 Server, 8 Backup) ---
    {
        "id_aset": "PC-0001",
        "nama_aset": "PC-OPS-B14-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-001",
        "tanggal_masuk_gudang": "2024-01-05",
        "tanggal_keluar_gudang": "2024-01-10",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Ahmad Fauzi",
        "catatan": "Workstation staf operasional lantai 2.",
    },
    {
        "id_aset": "PC-0002",
        "nama_aset": "PC-OPS-B14-02",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-002",
        "tanggal_masuk_gudang": "2024-01-05",
        "tanggal_keluar_gudang": "2024-01-10",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Budi Santoso",
        "catatan": "Dual monitor setup untuk data entry.",
    },
    {
        "id_aset": "PC-0003",
        "nama_aset": "PC-OPS-B13-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-003",
        "tanggal_masuk_gudang": "2024-02-01",
        "tanggal_keluar_gudang": "2024-02-05",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Citra Lestari",
        "catatan": "Operasional finance & billing.",
    },
    {
        "id_aset": "PC-0004",
        "nama_aset": "PC-OPS-B13-02",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-004",
        "tanggal_masuk_gudang": "2024-02-01",
        "tanggal_keluar_gudang": "2024-02-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Dimas Pratama",
        "catatan": "Meja CS ticketing.",
    },
    {
        "id_aset": "PC-0005",
        "nama_aset": "PC-OPS-RUKO-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-005",
        "tanggal_masuk_gudang": "2024-02-15",
        "tanggal_keluar_gudang": "2024-02-20",
        "kepemilikan": "MBL",
        "lokasi": "Ruko",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Eka Saputra",
        "catatan": "Operasional administrasi ruko.",
    },
    {
        "id_aset": "PC-0006",
        "nama_aset": "PC-OPS-RUKO-02",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-006",
        "tanggal_masuk_gudang": "2024-02-15",
        "tanggal_keluar_gudang": "2024-02-20",
        "kepemilikan": "XML",
        "lokasi": "Ruko",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Farhan Hakim",
        "catatan": "Terminal kasir dan stok barang.",
    },
    {
        "id_aset": "PC-0007",
        "nama_aset": "PC-OPS-B12-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-007",
        "tanggal_masuk_gudang": "2024-03-01",
        "tanggal_keluar_gudang": "2024-03-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Gita Permata",
        "catatan": "Operasional purchasing.",
    },
    {
        "id_aset": "PC-0008",
        "nama_aset": "PC-OPS-B12-02",
        "kategori": "PC",
        "sn_pid": "SN-PC-OPS-008",
        "tanggal_masuk_gudang": "2024-03-01",
        "tanggal_keluar_gudang": "2024-03-05",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Hadi Subagyo",
        "catatan": "Operasional IT support internal.",
    },
    # 8 Server
    {
        "id_aset": "PC-0009",
        "nama_aset": "SRV-DB-PRIMARY",
        "kategori": "Server",
        "sn_pid": "SN-SRV-001",
        "tanggal_masuk_gudang": "2024-01-01",
        "tanggal_keluar_gudang": "2024-01-02",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Database Production",
        "catatan": "Server database utama PostgreSQL & Redis.",
    },
    {
        "id_aset": "PC-0010",
        "nama_aset": "SRV-APP-PROD-01",
        "kategori": "Server",
        "sn_pid": "SN-SRV-002",
        "tanggal_masuk_gudang": "2024-01-01",
        "tanggal_keluar_gudang": "2024-01-02",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "App Backend",
        "catatan": "Node aplikasi web & API gateway.",
    },
    {
        "id_aset": "PC-0011",
        "nama_aset": "SRV-MONITORING",
        "kategori": "Server",
        "sn_pid": "SN-SRV-003",
        "tanggal_masuk_gudang": "2024-01-15",
        "tanggal_keluar_gudang": "2024-01-16",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Zabbix & Grafana",
        "catatan": "Host monitoring server dan alerting.",
    },
    {
        "id_aset": "PC-0012",
        "nama_aset": "SRV-FILE-STORAGE",
        "kategori": "Server",
        "sn_pid": "SN-SRV-004",
        "tanggal_masuk_gudang": "2024-02-01",
        "tanggal_keluar_gudang": "2024-02-02",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "NAS Samba",
        "catatan": "File server internal seluruh divisi.",
    },
    {
        "id_aset": "PC-0013",
        "nama_aset": "SRV-BACKUP-AUTO",
        "kategori": "Server",
        "sn_pid": "SN-SRV-005",
        "tanggal_masuk_gudang": "2024-02-10",
        "tanggal_keluar_gudang": "2024-02-11",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Borg & Restic",
        "catatan": "Server snapshot dan replikasi harian.",
    },
    {
        "id_aset": "PC-0014",
        "nama_aset": "SRV-DEV-STAGING",
        "kategori": "Server",
        "sn_pid": "SN-SRV-006",
        "tanggal_masuk_gudang": "2024-03-01",
        "tanggal_keluar_gudang": "2024-03-02",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Staging QA",
        "catatan": "Lingkungan uji coba fitur baru.",
    },
    {
        "id_aset": "PC-0015",
        "nama_aset": "SRV-MAIL-GATEWAY",
        "kategori": "Server",
        "sn_pid": "SN-SRV-007",
        "tanggal_masuk_gudang": "2024-03-15",
        "tanggal_keluar_gudang": "2024-03-16",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Postfix & SpamAssassin",
        "catatan": "Relay email internal dan filter spam.",
    },
    {
        "id_aset": "PC-0016",
        "nama_aset": "SRV-DNS-LOCAL",
        "kategori": "Server",
        "sn_pid": "SN-SRV-008",
        "tanggal_masuk_gudang": "2024-04-01",
        "tanggal_keluar_gudang": "2024-04-02",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Pi-hole & CoreDNS",
        "catatan": "DNS resolver internal dan ad-blocking.",
    },
    # 8 Backup PC
    {
        "id_aset": "PC-0017",
        "nama_aset": "PC-BKP-B14-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-001",
        "tanggal_masuk_gudang": "2024-04-10",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "Cadangan Unit Operasional",
        "catatan": "Standby di rak IT Blok 14.",
    },
    {
        "id_aset": "PC-0018",
        "nama_aset": "PC-BKP-B14-02",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-002",
        "tanggal_masuk_gudang": "2024-04-10",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "Cadangan Dev Workstation",
        "catatan": "Spec mumpuni untuk dev pengganti.",
    },
    {
        "id_aset": "PC-0019",
        "nama_aset": "PC-BKP-B13-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-003",
        "tanggal_masuk_gudang": "2024-05-01",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "MBL",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "Cadangan CS & Admin",
        "catatan": "Siap jalan saat PC staf rusak.",
    },
    {
        "id_aset": "PC-0020",
        "nama_aset": "PC-BKP-B13-02",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-004",
        "tanggal_masuk_gudang": "2024-05-01",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "Cadangan Umum",
        "catatan": "Tersimpan di ruang server Blok 13.",
    },
    {
        "id_aset": "PC-0021",
        "nama_aset": "PC-BKP-RUKO-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-005",
        "tanggal_masuk_gudang": "2024-05-15",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "MBL",
        "lokasi": "Ruko",
        "kondisi": "Bekas",
        "status": "Backup",
        "digunakan_oleh": "Cadangan Terminal POS",
        "catatan": "Unit cadangan ruko siap pasang.",
    },
    {
        "id_aset": "PC-0022",
        "nama_aset": "PC-BKP-B12-01",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-006",
        "tanggal_masuk_gudang": "2024-06-01",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "Cadangan Ruang Meeting",
        "catatan": "Mini PC cadangan presentasi.",
    },
    {
        "id_aset": "PC-0023",
        "nama_aset": "PC-BKP-B12-02",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-007",
        "tanggal_masuk_gudang": "2024-06-01",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 12",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "Unit Pengganti Maintenance",
        "catatan": "Tersedia jika ada servis berkala.",
    },
    {
        "id_aset": "PC-0024",
        "nama_aset": "PC-BKP-HOTSPARE",
        "kategori": "PC",
        "sn_pid": "SN-PC-BKP-008",
        "tanggal_masuk_gudang": "2024-06-15",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "Hot-Spare Node",
        "catatan": "Dikonfigurasi identik dengan node server.",
    },

    # --- ASET HARDWARE UMUM LAINNYA (Laptop, SSD, RAM, Keyboard, Router) ---
    {
        "id_aset": "AST-0001",
        "nama_aset": "MacBook Pro M2 14-inch",
        "kategori": "Laptop",
        "sn_pid": "C02XYZ12345",
        "tanggal_masuk_gudang": "2024-01-10",
        "tanggal_keluar_gudang": "2024-01-15",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Bambang (Dev)",
        "catatan": "Laptop pengembangan produk.",
    },
    {
        "id_aset": "AST-0002",
        "nama_aset": "Lenovo ThinkPad T14 Gen 3",
        "kategori": "Laptop",
        "sn_pid": "PF456789",
        "tanggal_masuk_gudang": "2024-01-15",
        "tanggal_keluar_gudang": "2024-01-20",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 13",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Dewi (PM)",
        "catatan": "Laptop Project Manager.",
    },
    {
        "id_aset": "AST-0003",
        "nama_aset": "SSD Samsung 970 EVO Plus 1TB",
        "kategori": "SSD",
        "sn_pid": "S4EVNF012345",
        "tanggal_masuk_gudang": "2024-02-01",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Stok upgrade SSD tim backend.",
    },
    {
        "id_aset": "AST-0004",
        "nama_aset": "RAM Corsair Vengeance 32GB DDR4",
        "kategori": "RAM",
        "sn_pid": "CMK32GX4M2E",
        "tanggal_masuk_gudang": "2024-02-10",
        "tanggal_keluar_gudang": "",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Backup",
        "digunakan_oleh": "",
        "catatan": "Spare RAM workstation.",
    },
    {
        "id_aset": "AST-0005",
        "nama_aset": "MikroTik Cloud Core Router CCR1009",
        "kategori": "Router",
        "sn_pid": "CCR-987654321",
        "tanggal_masuk_gudang": "2024-01-02",
        "tanggal_keluar_gudang": "2024-01-03",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Infrastruktur Jaringan",
        "catatan": "Router core gateway utama.",
    },
    {
        "id_aset": "AST-0006",
        "nama_aset": "Keyboard Logitech MX Keys",
        "kategori": "Keyboard",
        "sn_pid": "SN-KB-LOGI-001",
        "tanggal_masuk_gudang": "2024-02-20",
        "tanggal_keluar_gudang": "2024-02-22",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Tio (QA)",
        "catatan": "Keyboard meja QA.",
    },
    {
        "id_aset": "AST-0007",
        "nama_aset": "Mouse Logitech MX Master 3S",
        "kategori": "Mouse",
        "sn_pid": "SN-MS-LOGI-001",
        "tanggal_masuk_gudang": "2024-02-20",
        "tanggal_keluar_gudang": "2024-02-22",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "Tio (QA)",
        "catatan": "Mouse ergonomis tim QA.",
    },
    {
        "id_aset": "AST-0008",
        "nama_aset": "HDD Seagate IronWolf 4TB",
        "kategori": "HDD",
        "sn_pid": "W12345678",
        "tanggal_masuk_gudang": "2024-03-01",
        "tanggal_keluar_gudang": "2024-03-02",
        "kepemilikan": "XML",
        "lokasi": "Kantor Blok 14",
        "kondisi": "Baru",
        "status": "Digunakan",
        "digunakan_oleh": "NAS Samba",
        "catatan": "Drive penyimpanan data harian.",
    },
]

# Tambahkan alias "id" ke setiap record agar kompatibel dengan state/tabel mana pun
for _item in mock_assets_db:
    _item["id"] = _item["id_aset"]


# ==============================================================================
# 2. TABEL SPESIFIKASI MONITOR (1:1 ke assets)
# ==============================================================================
mock_monitor_specs_db: list[dict[str, Any]] = [
    {
        "asset_id": "MON-0001",
        "merk": "LG",
        "tipe_model": "24MK600M",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0002",
        "merk": "LG",
        "tipe_model": "24MK600M",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0003",
        "merk": "Dell",
        "tipe_model": "UltraSharp U2422H",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "DisplayPort"],
    },
    {
        "asset_id": "MON-0004",
        "merk": "Samsung",
        "tipe_model": "S27R350",
        "ukuran_layar": "27",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0005",
        "merk": "AOC",
        "tipe_model": "22B1HS",
        "ukuran_layar": "21,5",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0006",
        "merk": "LG",
        "tipe_model": "22MK430H",
        "ukuran_layar": "21,5",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0007",
        "merk": "Dell",
        "tipe_model": "P2422H",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "DisplayPort", "VGA"],
    },
    {
        "asset_id": "MON-0008",
        "merk": "HP",
        "tipe_model": "P24v G4",
        "ukuran_layar": "23,8",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0009",
        "merk": "Samsung",
        "tipe_model": "Odyssey G5",
        "ukuran_layar": "27",
        "resolusi_layar": "2560 × 1440",
        "konektivitas": ["HDMI", "DisplayPort"],
    },
    {
        "asset_id": "MON-0010",
        "merk": "AOC",
        "tipe_model": "24G2SP",
        "ukuran_layar": "23,8",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "DisplayPort", "VGA"],
    },
    {
        "asset_id": "MON-0011",
        "merk": "LG",
        "tipe_model": "24MP400",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0012",
        "merk": "Dell",
        "tipe_model": "E1916HV",
        "ukuran_layar": "18,5",
        "resolusi_layar": "1366 × 768",
        "konektivitas": ["VGA"],
    },
    {
        "asset_id": "MON-0013",
        "merk": "HP",
        "tipe_model": "V214a",
        "ukuran_layar": "20,7",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0014",
        "merk": "Samsung",
        "tipe_model": "S24R350",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0015",
        "merk": "AOC",
        "tipe_model": "27V2Q",
        "ukuran_layar": "27",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "DisplayPort"],
    },
    {
        "asset_id": "MON-0016",
        "merk": "LG",
        "tipe_model": "27UP650",
        "ukuran_layar": "27",
        "resolusi_layar": "3840 × 2160",
        "konektivitas": ["HDMI", "DisplayPort"],
    },
    {
        "asset_id": "MON-0017",
        "merk": "Dell",
        "tipe_model": "UltraSharp U2723QE",
        "ukuran_layar": "27",
        "resolusi_layar": "3840 × 2160",
        "konektivitas": ["HDMI", "DisplayPort", "USB-C"],
    },
    {
        "asset_id": "MON-0018",
        "merk": "HP",
        "tipe_model": "EliteDisplay E243",
        "ukuran_layar": "23,8",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "DisplayPort", "VGA"],
    },
    {
        "asset_id": "MON-0019",
        "merk": "Samsung",
        "tipe_model": "S19A330",
        "ukuran_layar": "18,5",
        "resolusi_layar": "1366 × 768",
        "konektivitas": ["VGA", "HDMI"],
    },
    {
        "asset_id": "MON-0020",
        "merk": "AOC",
        "tipe_model": "24B2XH",
        "ukuran_layar": "23,8",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0021",
        "merk": "LG",
        "tipe_model": "24GN60R",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "DisplayPort"],
    },
    {
        "asset_id": "MON-0022",
        "merk": "Dell",
        "tipe_model": "SE2422H",
        "ukuran_layar": "24",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0023",
        "merk": "HP",
        "tipe_model": "M24f",
        "ukuran_layar": "23,8",
        "resolusi_layar": "1920 × 1080",
        "konektivitas": ["HDMI", "VGA"],
    },
    {
        "asset_id": "MON-0024",
        "merk": "AOC",
        "tipe_model": "Q27V4",
        "ukuran_layar": "27",
        "resolusi_layar": "2560 × 1440",
        "konektivitas": ["HDMI", "DisplayPort"],
    },
]


# ==============================================================================
# 3. TABEL SPESIFIKASI PC (1:1 ke assets)
# ==============================================================================
mock_pc_specs_db: list[dict[str, Any]] = [
    # 8 Operasional
    {
        "asset_id": "PC-0001",
        "jenis": "Operasional",
        "os": "Windows 11 Pro 64-bit",
        "ram": "16 GB DDR4 3200MHz",
        "vga": "NVIDIA GTX 1650 4GB",
        "cpu": "Intel Core i5-12400F",
        "mainboard": "ASUS PRIME B660M-A",
        "hdd_ssd": "SSD NVMe 512GB + HDD 1TB",
        "monitor": "LG 24MK600M 24 inci",
        "keyboard": "Logitech K120",
        "mouse": "Logitech B100",
    },
    {
        "asset_id": "PC-0002",
        "jenis": "Operasional",
        "os": "Windows 11 Pro 64-bit",
        "ram": "16 GB DDR4 3200MHz",
        "vga": "Integrated Intel UHD 730",
        "cpu": "Intel Core i3-12100",
        "mainboard": "MSI PRO H610M-E",
        "hdd_ssd": "SSD NVMe 256GB",
        "monitor": "Dell P2422H 24 inci",
        "keyboard": "Logitech MK120",
        "mouse": "Logitech MK120",
    },
    {
        "asset_id": "PC-0003",
        "jenis": "Operasional",
        "os": "Windows 10 Pro 64-bit",
        "ram": "8 GB DDR4 2666MHz",
        "vga": "Integrated Intel UHD 630",
        "cpu": "Intel Core i3-10100",
        "mainboard": "Gigabyte H410M H",
        "hdd_ssd": "SSD SATA 256GB",
        "monitor": "AOC 22B1HS 21.5 inci",
        "keyboard": "Genius KB-110",
        "mouse": "Genius DX-110",
    },
    {
        "asset_id": "PC-0004",
        "jenis": "Operasional",
        "os": "Windows 11 Pro 64-bit",
        "ram": "16 GB DDR4 3200MHz",
        "vga": "Integrated Intel UHD 730",
        "cpu": "Intel Core i5-12400",
        "mainboard": "ASUS PRIME H610M-K",
        "hdd_ssd": "SSD NVMe 512GB",
        "monitor": "HP P24v G4 23.8 inci",
        "keyboard": "Logitech K120",
        "mouse": "Logitech M90",
    },
    {
        "asset_id": "PC-0005",
        "jenis": "Operasional",
        "os": "Windows 10 Home 64-bit",
        "ram": "8 GB DDR4 2666MHz",
        "vga": "Integrated Intel HD",
        "cpu": "Intel Core i3-9100",
        "mainboard": "ASRock H310CM-HDV",
        "hdd_ssd": "SSD SATA 128GB + HDD 500GB",
        "monitor": "LG 20MK400H 19.5 inci",
        "keyboard": "Standard USB",
        "mouse": "Standard USB",
    },
    {
        "asset_id": "PC-0006",
        "jenis": "Operasional",
        "os": "Windows 10 Pro 64-bit",
        "ram": "8 GB DDR4 2666MHz",
        "vga": "Integrated Radeon Graphics",
        "cpu": "AMD Ryzen 3 3200G",
        "mainboard": "ASUS PRIME A320M-K",
        "hdd_ssd": "SSD SATA 240GB",
        "monitor": "Samsung S19A330 18.5 inci",
        "keyboard": "Logitech K120",
        "mouse": "Logitech B100",
    },
    {
        "asset_id": "PC-0007",
        "jenis": "Operasional",
        "os": "Windows 11 Pro 64-bit",
        "ram": "16 GB DDR4 3200MHz",
        "vga": "NVIDIA GTX 1050 Ti 4GB",
        "cpu": "Intel Core i5-10400F",
        "mainboard": "MSI B460M PRO-VDH",
        "hdd_ssd": "SSD NVMe 500GB",
        "monitor": "LG 24MP400 24 inci",
        "keyboard": "HP USB Keyboard",
        "mouse": "HP USB Optical",
    },
    {
        "asset_id": "PC-0008",
        "jenis": "Operasional",
        "os": "Ubuntu 22.04 LTS",
        "ram": "32 GB DDR4 3200MHz",
        "vga": "NVIDIA RTX 3060 12GB",
        "cpu": "AMD Ryzen 7 5700X",
        "mainboard": "Gigabyte B550 AORUS ELITE",
        "hdd_ssd": "SSD NVMe 1TB Gen4",
        "monitor": "Dell UltraSharp U2422H",
        "keyboard": "Keychron K2",
        "mouse": "Logitech MX Master 3",
    },
    # 8 Server
    {
        "asset_id": "PC-0009",
        "jenis": "Server",
        "os": "Ubuntu Server 22.04 LTS",
        "ram": "64 GB DDR4 ECC",
        "vga": "Matrox G200eR2",
        "cpu": "Intel Xeon E-2388G 8C/16T",
        "mainboard": "Supermicro X12STL-F",
        "hdd_ssd": "2x SSD NVMe 1TB Enterprise RAID 1",
        "monitor": "Rack KVM Switch 17 inci",
        "keyboard": "KVM Console",
        "mouse": "KVM Touchpad",
    },
    {
        "asset_id": "PC-0010",
        "jenis": "Server",
        "os": "Debian 12 Bookworm",
        "ram": "32 GB DDR4 ECC",
        "vga": "ASPEED AST2500",
        "cpu": "AMD EPYC 7302P 16C/32T",
        "mainboard": "ASRock Rack EPYCD8",
        "hdd_ssd": "2x SSD SATA Enterprise 960GB",
        "monitor": "Headless (SSH / Web GUI)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0011",
        "jenis": "Server",
        "os": "Ubuntu Server 22.04 LTS",
        "ram": "16 GB DDR4 3200MHz",
        "vga": "Integrated Intel UHD 730",
        "cpu": "Intel Core i5-12500",
        "mainboard": "ASUS Pro B660M-C",
        "hdd_ssd": "SSD NVMe 500GB",
        "monitor": "Shared KVM",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0012",
        "jenis": "Server",
        "os": "TrueNAS SCALE 23.10",
        "ram": "32 GB DDR4 ECC",
        "vga": "ASPEED AST2400",
        "cpu": "Intel Xeon E-2224",
        "mainboard": "Supermicro X11SCL-F",
        "hdd_ssd": "4x HDD Seagate IronWolf 4TB RAID Z2",
        "monitor": "Headless (Web UI)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0013",
        "jenis": "Server",
        "os": "Proxmox VE 8.1",
        "ram": "64 GB DDR4 3200MHz",
        "vga": "Integrated Radeon Graphics",
        "cpu": "AMD Ryzen 9 5900X 12C/24T",
        "mainboard": "ASUS ProArt B550-CREATOR",
        "hdd_ssd": "2x SSD NVMe 2TB ZFS Mirror",
        "monitor": "Headless (Proxmox GUI)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0014",
        "jenis": "Server",
        "os": "Ubuntu Server 20.04 LTS",
        "ram": "16 GB DDR4 2666MHz",
        "vga": "Integrated Intel HD",
        "cpu": "Intel Core i7-8700",
        "mainboard": "Gigabyte B360M D3H",
        "hdd_ssd": "SSD SATA 512GB",
        "monitor": "Headless (Portainer / Docker)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0015",
        "jenis": "Server",
        "os": "Debian 12 Minimal",
        "ram": "8 GB DDR4 2666MHz",
        "vga": "Integrated Intel HD",
        "cpu": "Intel Core i3-8100",
        "mainboard": "MSI H310M PRO-VD",
        "hdd_ssd": "SSD SATA 240GB",
        "monitor": "Headless (SSH)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0016",
        "jenis": "Server",
        "os": "Alpine Linux 3.19",
        "ram": "4 GB DDR4 2400MHz",
        "vga": "Integrated",
        "cpu": "Intel Celeron J4125",
        "mainboard": "Mini ITX Embedded",
        "hdd_ssd": "eMMC 64GB + SSD 120GB",
        "monitor": "Headless",
        "keyboard": "—",
        "mouse": "—",
    },
    # 8 Backup PC
    {
        "asset_id": "PC-0017",
        "jenis": "Backup",
        "os": "Windows 11 Pro (Sysprep Ready)",
        "ram": "16 GB DDR4 3200MHz",
        "vga": "Integrated Intel UHD 730",
        "cpu": "Intel Core i5-12400",
        "mainboard": "ASUS PRIME H610M-K",
        "hdd_ssd": "SSD NVMe 512GB",
        "monitor": "— (Di Rak)",
        "keyboard": "Logitech K120 (Box)",
        "mouse": "Logitech B100 (Box)",
    },
    {
        "asset_id": "PC-0018",
        "jenis": "Backup",
        "os": "Windows 11 Pro 64-bit",
        "ram": "32 GB DDR4 3200MHz",
        "vga": "NVIDIA GTX 1660 Super 6GB",
        "cpu": "AMD Ryzen 5 5600X",
        "mainboard": "MSI B550M PRO-VDH",
        "hdd_ssd": "SSD NVMe 1TB",
        "monitor": "— (Di Rak)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0019",
        "jenis": "Backup",
        "os": "Windows 10 Pro 64-bit",
        "ram": "8 GB DDR4 2666MHz",
        "vga": "Integrated Intel UHD 630",
        "cpu": "Intel Core i3-10100",
        "mainboard": "ASRock H410M-HDV",
        "hdd_ssd": "SSD SATA 256GB",
        "monitor": "— (Di Rak)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0020",
        "jenis": "Backup",
        "os": "Windows 10 Pro 64-bit",
        "ram": "8 GB DDR4 2666MHz",
        "vga": "Integrated Intel UHD 630",
        "cpu": "Intel Core i3-10100",
        "mainboard": "ASUS PRIME H410M-E",
        "hdd_ssd": "SSD SATA 240GB",
        "monitor": "— (Di Rak)",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0021",
        "jenis": "Backup",
        "os": "Windows 10 IoT Enterprise",
        "ram": "4 GB DDR3L",
        "vga": "Integrated Intel HD",
        "cpu": "Intel Celeron J1900",
        "mainboard": "POS Embedded Motherboard",
        "hdd_ssd": "SSD SATA 64GB",
        "monitor": "Touchscreen 15 inci (Cadangan)",
        "keyboard": "Mini USB POS",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0022",
        "jenis": "Backup",
        "os": "Windows 11 Home 64-bit",
        "ram": "8 GB DDR4 3200MHz",
        "vga": "Integrated Intel Iris Xe",
        "cpu": "Intel Core i5-1135G7 Mini PC",
        "mainboard": "NUC Mainboard",
        "hdd_ssd": "SSD NVMe 256GB",
        "monitor": "—",
        "keyboard": "Wireless Mini",
        "mouse": "Wireless Mini",
    },
    {
        "asset_id": "PC-0023",
        "jenis": "Backup",
        "os": "Windows 10 Pro 64-bit",
        "ram": "8 GB DDR4 2400MHz",
        "vga": "Integrated Intel HD 610",
        "cpu": "Intel Pentium Gold G5400",
        "mainboard": "Gigabyte H310M DS2",
        "hdd_ssd": "HDD 500GB",
        "monitor": "—",
        "keyboard": "—",
        "mouse": "—",
    },
    {
        "asset_id": "PC-0024",
        "jenis": "Backup",
        "os": "Proxmox VE 8 Ready",
        "ram": "32 GB DDR4 ECC",
        "vga": "ASPEED AST2500",
        "cpu": "AMD EPYC 7282 16C/32T",
        "mainboard": "Supermicro H11SSL-i",
        "hdd_ssd": "2x SSD NVMe 1TB Enterprise",
        "monitor": "Headless",
        "keyboard": "—",
        "mouse": "—",
    },
]


# ==============================================================================
# HELPER FORMATTING & ID SEQUENCING
# ==============================================================================

def is_monitor_id_taken(id_aset: str, exclude_id: str = "") -> bool:
    norm = id_aset.strip().upper()
    exclude_norm = exclude_id.strip().upper()
    for item in mock_assets_db:
        curr = str(item.get("id_aset", "")).strip().upper()
        if curr == norm and curr != exclude_norm:
            return True
    return False


def get_next_monitor_id() -> str:
    max_num = 0
    for item in mock_assets_db:
        code = str(item.get("id_aset", "")).strip().upper()
        if code.startswith("MON-") and code[4:].isdigit():
            max_num = max(max_num, int(code[4:]))
    return f"MON-{max_num + 1:04d}"


def get_next_pc_id() -> str:
    max_num = 0
    for item in mock_assets_db:
        code = str(item.get("id_aset", "")).strip().upper()
        if code.startswith("PC-") and code[3:].isdigit():
            max_num = max(max_num, int(code[3:]))
        elif code.startswith("PC-") and code[4:].isdigit():
            max_num = max(max_num, int(code[4:]))
    return f"PC-{max_num + 1:04d}"


def get_next_asset_id() -> str:
    max_num = 0
    for item in mock_assets_db:
        code = str(item.get("id_aset", "")).strip().upper()
        if code.startswith("AST-") and code[4:].isdigit():
            max_num = max(max_num, int(code[4:]))
    return f"AST-{max_num + 1:04d}"


def _format_monitor_record(asset: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Gabungkan atribut fisik aset dan spesifikasi monitor (1:1 join) untuk tampilan UI."""
    id_aset = str(asset.get("id_aset", spec.get("asset_id", ""))).strip().upper()
    merk = str(spec.get("merk", "")).strip()
    tipe_model = str(spec.get("tipe_model", "")).strip()
    ukuran_raw = spec.get("ukuran_layar", "24")
    ukuran_num = parse_inch_number(ukuran_raw)
    ukuran_display = format_inch_label(ukuran_raw)
    resolusi = (
        str(spec.get("resolusi_layar", "1920 × 1080"))
        .strip()
        .replace("x", "×")
        .replace("X", "×")
    )
    konektivitas = list(spec.get("konektivitas", ["HDMI"]))
    status = str(asset.get("status", "Digunakan")).strip()
    kepemilikan = str(asset.get("kepemilikan", "XML")).strip()
    lokasi = str(asset.get("lokasi", "Kantor Blok 14")).strip()
    kondisi = str(asset.get("kondisi", "Baru")).strip()
    catatan_raw = str(asset.get("catatan", "")).strip()
    catatan_display = catatan_raw or "—"
    digunakan_oleh = str(asset.get("digunakan_oleh", "")).strip()

    return {
        "id": id_aset,
        "id_aset": id_aset,
        "nama_aset": asset.get("nama_aset", f"{merk} {tipe_model} {ukuran_display}"),
        "kategori": "Monitor",
        "merk": merk,
        "tipe_model": tipe_model,
        "ukuran_layar": ukuran_display,
        "ukuran_num": ukuran_num,
        "ukuran_raw": str(
            ukuran_num if not ukuran_num.is_integer() else int(ukuran_num)
        ).replace(".", ","),
        "resolusi_layar": resolusi,
        "konektivitas": konektivitas,
        "status": status,
        "kepemilikan": kepemilikan,
        "lokasi": lokasi,
        "kondisi": kondisi,
        "digunakan_oleh": digunakan_oleh,
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
            {"label": "Kepemilikan", "value": kepemilikan},
            {"label": "Lokasi", "value": lokasi},
            {"label": "Kondisi Fisik", "value": kondisi},
            {"label": "Aksi", "value": "Buka di Assets Inventory ↗"},
            {"label": "Catatan", "value": catatan_display},
        ],
        "history_info": asset.get(
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


def _format_pc_record(asset: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Gabungkan atribut fisik aset dan spesifikasi PC (1:1 join) untuk tampilan UI."""
    asset_id = str(asset.get("id_aset", spec.get("asset_id", ""))).strip().upper()
    jenis = str(spec.get("jenis", "Operasional")).strip()
    nama_pc = str(asset.get("nama_aset", asset_id)).strip()
    user_raw = str(asset.get("digunakan_oleh", "")).strip()
    os_raw = str(spec.get("os", spec.get("operasi_system", ""))).strip()
    ram_raw = str(spec.get("ram", "")).strip()
    vga_raw = str(spec.get("vga", "")).strip()
    cpu_raw = str(spec.get("cpu", "")).strip()
    mb_raw = str(spec.get("mainboard", "")).strip()
    storage_raw = str(spec.get("hdd_ssd", "")).strip()
    mon_raw = str(spec.get("monitor", "")).strip()
    kb_raw = str(spec.get("keyboard", "")).strip()
    mouse_raw = str(spec.get("mouse", "")).strip()
    catatan_raw = str(asset.get("catatan", "")).strip()

    user_label = "User / Fungsi" if jenis in ("Server", "Backup") else "User"

    return {
        "id": asset_id,
        "asset_id": asset_id,
        "id_aset": asset_id,
        "jenis": jenis,
        "nama_pc": nama_pc,
        "user": user_raw or "—",
        "user_raw": user_raw,
        "operasi_system": os_raw or "—",
        "operasi_system_raw": os_raw,
        "ram": ram_raw or "—",
        "ram_raw": ram_raw,
        "vga": vga_raw or "—",
        "vga_raw": vga_raw,
        "cpu": cpu_raw or "—",
        "cpu_raw": cpu_raw,
        "mainboard": mb_raw or "—",
        "mainboard_raw": mb_raw,
        "hdd_ssd": storage_raw or "—",
        "hdd_ssd_raw": storage_raw,
        "monitor": mon_raw or "—",
        "monitor_raw": mon_raw,
        "keyboard": kb_raw or "—",
        "keyboard_raw": kb_raw,
        "mouse": mouse_raw or "—",
        "mouse_raw": mouse_raw,
        "catatan": catatan_raw or "—",
        "catatan_raw": catatan_raw,
        "identity_info": [
            {"label": "ID Aset", "value": asset_id},
            {"label": "Nama PC / Hostname", "value": nama_pc},
            {"label": "Jenis PC", "value": jenis},
            {"label": user_label, "value": user_raw or "—"},
            {"label": "Lokasi", "value": asset.get("lokasi", "Kantor Blok 14")},
            {"label": "Kepemilikan", "value": asset.get("kepemilikan", "XML")},
            {"label": "Aksi", "value": "Buka di Assets Inventory ↗"},
            {"label": "Catatan", "value": catatan_raw or "—"},
        ],
        "hardware_info": [
            {"label": "Operasi System", "value": os_raw or "—"},
            {"label": "CPU / Prosesor", "value": cpu_raw or "—"},
            {"label": "Mainboard", "value": mb_raw or "—"},
            {"label": "RAM", "value": ram_raw or "—"},
            {"label": "VGA / Grafis", "value": vga_raw or "—"},
            {"label": "HDD / SSD", "value": storage_raw or "—"},
        ],
        "peripheral_info": [
            {"label": "Monitor", "value": mon_raw or "—"},
            {"label": "Keyboard", "value": kb_raw or "—"},
            {"label": "Mouse", "value": mouse_raw or "—"},
        ],
        "history_info": asset.get(
            "history_info",
            [
                {
                    "event": "Pencatatan Spesifikasi PC",
                    "date": "12 Okt 2026",
                    "note": f"Spesifikasi unit {nama_pc} ({jenis}) telah diverifikasi.",
                }
            ],
        ),
    }


def _format_asset_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Lengkapi tampilan tabel dan drawer untuk item aset umum."""
    id_aset = str(raw.get("id_aset", raw.get("id", ""))).strip().upper()
    sn_display = raw.get("sn_pid", "").strip() or "—"
    masuk_iso = raw.get("tanggal_masuk_gudang", "").strip()
    keluar_iso = raw.get("tanggal_keluar_gudang", "").strip()
    masuk_display = format_date_id(masuk_iso)
    keluar_display = format_date_id(keluar_iso)
    digunakan_display = (
        raw.get("digunakan_oleh", "").strip() or "—"
        if raw.get("status") == "Digunakan"
        else "—"
    )
    catatan_display = raw.get("catatan", "").strip() or "—"

    return {
        "id": id_aset,
        "id_aset": id_aset,
        "nama_aset": raw["nama_aset"],
        "kategori": raw["kategori"],
        "sn_pid": sn_display,
        "sn_pid_raw": raw.get("sn_pid", "").strip(),
        "tanggal_masuk_gudang": masuk_display,
        "tanggal_masuk_iso": masuk_iso,
        "tanggal_keluar_gudang": keluar_display,
        "tanggal_keluar_iso": keluar_iso,
        "kepemilikan": raw["kepemilikan"],
        "lokasi": raw["lokasi"],
        "kondisi": raw["kondisi"],
        "status": raw["status"],
        "digunakan_oleh": digunakan_display,
        "digunakan_oleh_raw": raw.get("digunakan_oleh", "").strip(),
        "catatan": catatan_display,
        "catatan_raw": raw.get("catatan", "").strip(),
        "general_info": [
            {"label": "ID Aset", "value": id_aset},
            {"label": "Nama Aset", "value": raw["nama_aset"]},
            {"label": "Kategori", "value": raw["kategori"]},
            {"label": "SN / PID", "value": sn_display},
            {"label": "Kepemilikan", "value": raw["kepemilikan"]},
            {"label": "Kondisi", "value": raw["kondisi"]},
            {"label": "Catatan", "value": catatan_display},
        ],
        "usage_info": [
            {"label": "Status", "value": raw["status"]},
            {"label": "Digunakan Oleh", "value": digunakan_display},
            {"label": "Lokasi", "value": raw["lokasi"]},
            {"label": "Tgl Masuk Gudang", "value": masuk_display},
            {"label": "Tgl Keluar Gudang", "value": keluar_display},
        ],
        "history_info": raw.get(
            "history_info",
            [
                {
                    "event": "Pencatatan Inventaris",
                    "date": masuk_display if masuk_display != "—" else "10 Jan 2026",
                    "note": (
                        f"Unit {raw['nama_aset']} ({raw['kepemilikan']}) "
                        f"tercatat di {raw['lokasi']}."
                    ),
                }
            ],
        ),
    }


# ==============================================================================
# LOGIKA RELASIONAL JOIN MOCK API (MONITOR)
# ==============================================================================

def query_joined_monitors(
    status: str,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 8,
) -> dict[str, Any]:
    """Join `assets` dan `monitor_specs` khusus untuk kategori Monitor."""
    search = str(filters.get("search", "")).strip().lower()
    merk = str(filters.get("merk", "Semua"))
    ukuran = str(filters.get("ukuran_layar", "Semua"))
    resolusi = str(filters.get("resolusi_layar", "Semua"))
    konektivitas = str(filters.get("konektivitas", "Semua"))
    lokasi = str(filters.get("lokasi", "Semua"))
    kepemilikan = str(filters.get("kepemilikan", "Semua"))
    sort_by = str(filters.get("sort_by", "id_aset"))
    sort_dir = str(filters.get("sort_dir", "asc"))

    results: list[dict[str, Any]] = []

    # Hitung counter status untuk tabs
    count_semua = 0
    count_digunakan = 0
    count_backup = 0

    for spec in mock_monitor_specs_db:
        asset = next(
            (a for a in mock_assets_db if a.get("id_aset") == spec.get("asset_id")),
            None,
        )
        if not asset:
            continue

        count_semua += 1
        st = asset.get("status", "")
        if st == "Digunakan":
            count_digunakan += 1
        elif st == "Backup":
            count_backup += 1

        # Filter berdasarkan tab status
        if status not in ("Semua", "") and asset["status"] != status:
            continue

        # Filter spesifikasi monitor
        if merk != "Semua" and spec.get("merk") != merk:
            continue
        if ukuran != "Semua" and spec.get("ukuran_layar") != ukuran:
            continue
        if resolusi != "Semua" and spec.get("resolusi_layar") != resolusi:
            continue
        if konektivitas != "Semua" and konektivitas not in spec.get("konektivitas", []):
            continue

        # Filter master aset
        if lokasi != "Semua" and asset.get("lokasi") != lokasi:
            continue
        if kepemilikan != "Semua" and asset.get("kepemilikan") != kepemilikan:
            continue

        # Filter pencarian
        if search:
            haystack = (
                f"{asset.get('id_aset', '')} {spec.get('merk', '')} {spec.get('tipe_model', '')} "
                f"{spec.get('ukuran_layar', '')} {spec.get('resolusi_layar', '')} "
                f"{asset.get('lokasi', '')} {asset.get('kepemilikan', '')} "
                f"{asset.get('digunakan_oleh', '')}"
            ).lower()
            if search not in haystack:
                continue

        joined_record = _format_monitor_record(asset, spec)
        results.append(joined_record)

    reverse = sort_dir == "desc"
    if sort_by == "ukuran_layar":
        results.sort(key=lambda x: float(x.get("ukuran_num", 0.0)), reverse=reverse)
    elif sort_by == "merk":
        results.sort(
            key=lambda x: (str(x.get("merk", "")).lower(), str(x.get("id_aset", ""))),
            reverse=reverse,
        )
    else:
        results.sort(key=lambda x: str(x.get("id_aset", "")), reverse=reverse)

    total = len(results)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {
        "items": results[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "counts_by_status": {
            "semua": count_semua,
            "digunakan": count_digunakan,
            "backup": count_backup,
            "Semua": count_semua,
            "Digunakan": count_digunakan,
            "Backup": count_backup,
        },
    }


def create_joined_monitor(payload: dict[str, Any]) -> dict[str, Any]:
    """Simpan data menjadi 1 record assets dan 1 record monitor_specs."""
    id_aset = payload.get("id_aset") or get_next_monitor_id()
    ukuran_clean = (
        str(payload.get("ukuran_layar", "24"))
        .replace('"', "")
        .replace("inci", "")
        .strip()
    )

    asset_data = {
        "id_aset": id_aset,
        "id": id_aset,
        "nama_aset": (
            f"{payload.get('merk', 'Monitor')} {payload.get('tipe_model', '')} "
            f"{ukuran_clean} inci"
        ),
        "kategori": "Monitor",
        "sn_pid": payload.get("sn_pid", "-"),
        "tanggal_masuk_gudang": payload.get("tanggal_masuk_gudang", ""),
        "tanggal_keluar_gudang": payload.get("tanggal_keluar_gudang", ""),
        "kepemilikan": payload.get("kepemilikan", "XML"),
        "lokasi": payload.get("lokasi", "Kantor Blok 14"),
        "kondisi": payload.get("kondisi", "Baru"),
        "status": payload.get("status", "Digunakan"),
        "digunakan_oleh": payload.get("digunakan_oleh", ""),
        "catatan": payload.get("catatan", ""),
    }
    mock_assets_db.insert(0, asset_data)

    spec_data = {
        "asset_id": id_aset,
        "merk": payload.get("merk", "LG"),
        "tipe_model": payload.get("tipe_model", ""),
        "ukuran_layar": ukuran_clean,
        "resolusi_layar": payload.get("resolusi_layar", "1920 × 1080"),
        "konektivitas": payload.get("konektivitas", ["HDMI"]),
    }
    mock_monitor_specs_db.insert(0, spec_data)

    return _format_monitor_record(asset_data, spec_data)


def update_joined_monitor(original_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Perbarui 1 record assets dan 1 record monitor_specs."""
    norm_orig = original_id.strip().upper()
    asset = next(
        (a for a in mock_assets_db if a.get("id_aset", "").upper() == norm_orig),
        None,
    )
    spec = next(
        (s for s in mock_monitor_specs_db if s.get("asset_id", "").upper() == norm_orig),
        None,
    )
    if not asset or not spec:
        return None

    new_id = payload.get("id_aset", original_id).strip().upper()
    ukuran_clean = (
        str(payload.get("ukuran_layar", spec.get("ukuran_layar", "24")))
        .replace('"', "")
        .replace("inci", "")
        .strip()
    )

    asset["id_aset"] = new_id
    asset["id"] = new_id
    asset["nama_aset"] = (
        f"{payload.get('merk', spec.get('merk'))} "
        f"{payload.get('tipe_model', spec.get('tipe_model'))} "
        f"{ukuran_clean} inci"
    )
    asset["sn_pid"] = payload.get("sn_pid", asset.get("sn_pid", "-"))
    asset["kepemilikan"] = payload.get("kepemilikan", asset.get("kepemilikan", "XML"))
    asset["lokasi"] = payload.get("lokasi", asset.get("lokasi", "Kantor Blok 14"))
    asset["kondisi"] = payload.get("kondisi", asset.get("kondisi", "Baru"))
    asset["status"] = payload.get("status", asset.get("status", "Digunakan"))
    asset["digunakan_oleh"] = payload.get("digunakan_oleh", asset.get("digunakan_oleh", ""))
    asset["catatan"] = payload.get("catatan", asset.get("catatan", ""))

    spec["asset_id"] = new_id
    spec["merk"] = payload.get("merk", spec.get("merk"))
    spec["tipe_model"] = payload.get("tipe_model", spec.get("tipe_model"))
    spec["ukuran_layar"] = ukuran_clean
    spec["resolusi_layar"] = payload.get("resolusi_layar", spec.get("resolusi_layar"))
    spec["konektivitas"] = payload.get("konektivitas", spec.get("konektivitas"))

    return _format_monitor_record(asset, spec)


def delete_joined_monitor(id_aset: str) -> bool:
    """Hapus dari kedua tabel."""
    global mock_assets_db, mock_monitor_specs_db
    norm_id = id_aset.strip().upper()
    before = len(mock_assets_db)
    mock_assets_db = [a for a in mock_assets_db if a.get("id_aset", "").upper() != norm_id]
    mock_monitor_specs_db = [
        s for s in mock_monitor_specs_db if s.get("asset_id", "").upper() != norm_id
    ]
    return len(mock_assets_db) < before


# ==============================================================================
# LOGIKA RELASIONAL JOIN MOCK API (PC / SERVER)
# ==============================================================================

def query_joined_pcs(
    jenis: str,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Join `assets` dan `pc_specs` khusus untuk kategori PC/Server."""
    search = str(filters.get("search", "")).strip().lower()

    count_op = 0
    count_srv = 0
    count_bkp = 0
    results: list[dict[str, Any]] = []

    for spec in mock_pc_specs_db:
        asset = next(
            (a for a in mock_assets_db if a.get("id_aset") == spec.get("asset_id")),
            None,
        )
        if not asset:
            continue

        j = spec.get("jenis", "Operasional")
        if j == "Operasional":
            count_op += 1
        elif j == "Server":
            count_srv += 1
        elif j == "Backup":
            count_bkp += 1

        if jenis not in ("Semua", "") and j != jenis:
            continue

        if search:
            haystack = (
                f"{asset.get('nama_aset', '')} {asset.get('id_aset', '')} "
                f"{asset.get('digunakan_oleh', '')} {spec.get('cpu', '')} "
                f"{spec.get('mainboard', '')} {spec.get('os', '')}"
            ).lower()
            if search not in haystack:
                continue

        results.append(_format_pc_record(asset, spec))

    total = len(results)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {
        "items": results[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "counts_by_jenis": {
            "Operasional": count_op,
            "Server": count_srv,
            "Backup": count_bkp,
            "operasional": count_op,
            "server": count_srv,
            "backup": count_bkp,
        },
    }


def create_joined_pc(payload: dict[str, Any]) -> dict[str, Any]:
    """Simpan 1 record assets dan 1 record pc_specs."""
    id_aset = payload.get("id_aset") or payload.get("id") or get_next_pc_id()
    jenis = payload.get("jenis", "Operasional")

    asset_data = {
        "id_aset": id_aset,
        "id": id_aset,
        "nama_aset": payload.get("nama_pc", id_aset),
        "kategori": "Server" if jenis == "Server" else "PC",
        "sn_pid": payload.get("sn_pid", "-"),
        "tanggal_masuk_gudang": payload.get("tanggal_masuk_gudang", ""),
        "tanggal_keluar_gudang": payload.get("tanggal_keluar_gudang", ""),
        "kepemilikan": payload.get("kepemilikan", "XML"),
        "lokasi": payload.get("lokasi", "Kantor Blok 14"),
        "kondisi": payload.get("kondisi", "Baru"),
        "status": "Backup" if jenis == "Backup" else "Digunakan",
        "digunakan_oleh": payload.get("user", payload.get("digunakan_oleh", "")),
        "catatan": payload.get("catatan", ""),
    }
    mock_assets_db.insert(0, asset_data)

    spec_data = {
        "asset_id": id_aset,
        "jenis": jenis,
        "os": payload.get("os", payload.get("operasi_system", "Windows 11 Pro")),
        "ram": payload.get("ram", "16 GB DDR4"),
        "vga": payload.get("vga", "Integrated"),
        "cpu": payload.get("cpu", "Intel Core i5"),
        "mainboard": payload.get("mainboard", "Standard MB"),
        "hdd_ssd": payload.get("hdd_ssd", "SSD 512GB"),
        "monitor": payload.get("monitor", "—"),
        "keyboard": payload.get("keyboard", "—"),
        "mouse": payload.get("mouse", "—"),
    }
    mock_pc_specs_db.insert(0, spec_data)

    return _format_pc_record(asset_data, spec_data)


def update_joined_pc(pc_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    norm_id = pc_id.strip().upper()
    asset = next((a for a in mock_assets_db if a.get("id_aset", "").upper() == norm_id), None)
    spec = next((s for s in mock_pc_specs_db if s.get("asset_id", "").upper() == norm_id), None)
    if not asset or not spec:
        return None

    if "nama_pc" in payload:
        asset["nama_aset"] = payload["nama_pc"]
    if "user" in payload:
        asset["digunakan_oleh"] = payload["user"]
    if "catatan" in payload:
        asset["catatan"] = payload["catatan"]

    spec["jenis"] = payload.get("jenis", spec.get("jenis"))
    spec["os"] = payload.get("os", payload.get("operasi_system", spec.get("os")))
    spec["ram"] = payload.get("ram", spec.get("ram"))
    spec["vga"] = payload.get("vga", spec.get("vga"))
    spec["cpu"] = payload.get("cpu", spec.get("cpu"))
    spec["mainboard"] = payload.get("mainboard", spec.get("mainboard"))
    spec["hdd_ssd"] = payload.get("hdd_ssd", spec.get("hdd_ssd"))
    spec["monitor"] = payload.get("monitor", spec.get("monitor"))
    spec["keyboard"] = payload.get("keyboard", spec.get("keyboard"))
    spec["mouse"] = payload.get("mouse", spec.get("mouse"))

    return _format_pc_record(asset, spec)


def delete_joined_pc(pc_id: str) -> bool:
    global mock_assets_db, mock_pc_specs_db
    norm_id = pc_id.strip().upper()
    before = len(mock_assets_db)
    mock_assets_db = [a for a in mock_assets_db if a.get("id_aset", "").upper() != norm_id]
    mock_pc_specs_db = [s for s in mock_pc_specs_db if s.get("asset_id", "").upper() != norm_id]
    return len(mock_assets_db) < before


# ==============================================================================
# LOGIKA TABEL UTAMA ASSETS
# ==============================================================================

def query_mock_assets(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    search = str(filters.get("search", "")).strip().lower()
    kategori = str(filters.get("kategori", "Semua"))
    kepemilikan = str(filters.get("kepemilikan", "Semua"))
    lokasi = str(filters.get("lokasi", "Semua"))
    kondisi = str(filters.get("kondisi", "Semua"))
    status = str(filters.get("status", "Semua"))

    filtered: list[dict[str, Any]] = []
    for item in mock_assets_db:
        if kategori != "Semua" and item["kategori"] != kategori:
            continue
        if kepemilikan != "Semua" and item["kepemilikan"] != kepemilikan:
            continue
        if lokasi != "Semua" and item["lokasi"] != lokasi:
            continue
        if kondisi != "Semua" and item["kondisi"] != kondisi:
            continue
        if status != "Semua" and item["status"] != status:
            continue
        if search:
            haystack = (
                f"{item.get('id_aset', '')} {item.get('nama_aset', '')} "
                f"{item.get('sn_pid', '')} {item.get('digunakan_oleh', '')} "
                f"{item.get('lokasi', '')} {item.get('kategori', '')}"
            ).lower()
            if search not in haystack:
                continue
        filtered.append(_format_asset_record(item))

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {
        "items": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def create_mock_assets(payload: dict[str, Any], count: int = 1) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    qty = max(1, min(50, count))
    kategori = payload.get("kategori", "Monitor")

    for _ in range(qty):
        if kategori == "Monitor":
            new_id = get_next_monitor_id()
        elif kategori in ("PC", "Server"):
            new_id = get_next_pc_id()
        else:
            new_id = get_next_asset_id()

        asset_record = {
            "id_aset": new_id,
            "id": new_id,
            "nama_aset": str(payload.get("nama_aset", "")).strip() or f"{kategori} {new_id}",
            "kategori": kategori,
            "sn_pid": str(payload.get("sn_pid", "-")).strip(),
            "tanggal_masuk_gudang": str(payload.get("tanggal_masuk_gudang", "")).strip(),
            "tanggal_keluar_gudang": str(payload.get("tanggal_keluar_gudang", "")).strip(),
            "kepemilikan": str(payload.get("kepemilikan", "XML")),
            "lokasi": str(payload.get("lokasi", "Kantor Blok 14")),
            "kondisi": str(payload.get("kondisi", "Baru")),
            "status": str(payload.get("status", "Digunakan")),
            "digunakan_oleh": str(payload.get("digunakan_oleh", "")).strip(),
            "catatan": str(payload.get("catatan", "")).strip(),
        }
        mock_assets_db.insert(0, asset_record)

        # Jika kategori Monitor, simpan spesifikasi monitor jika ada
        if kategori == "Monitor":
            spec_data = {
                "asset_id": new_id,
                "merk": payload.get("merk", "LG"),
                "tipe_model": payload.get("tipe_model", "Standard"),
                "ukuran_layar": str(payload.get("ukuran_layar", "24")).replace('"', "").strip(),
                "resolusi_layar": payload.get("resolusi_layar", "1920 × 1080"),
                "konektivitas": payload.get("konektivitas", ["HDMI"]),
            }
            mock_monitor_specs_db.insert(0, spec_data)

        # Jika kategori PC atau Server, simpan spesifikasi PC jika ada
        elif kategori in ("PC", "Server"):
            spec_data = {
                "asset_id": new_id,
                "jenis": payload.get(
                    "jenis_pc", "Server" if kategori == "Server" else "Operasional"
                ),
                "os": payload.get("os", payload.get("operasi_system", "Windows 11 Pro")),
                "ram": payload.get("ram", "16 GB DDR4"),
                "vga": payload.get("vga", "Integrated"),
                "cpu": payload.get("cpu", "Intel Core i5"),
                "mainboard": payload.get("mainboard", "Standard MB"),
                "hdd_ssd": payload.get("hdd_ssd", "SSD 512GB"),
                "monitor": payload.get("monitor", "—"),
                "keyboard": payload.get("keyboard", "—"),
                "mouse": payload.get("mouse", "—"),
            }
            mock_pc_specs_db.insert(0, spec_data)

        formatted = _format_asset_record(asset_record)
        created.append(formatted)

    return created


def update_mock_asset(asset_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    norm_id = asset_id.strip().upper()
    for idx, existing in enumerate(mock_assets_db):
        if existing.get("id_aset", "").upper() == norm_id:
            existing["nama_aset"] = str(payload.get("nama_aset", existing["nama_aset"])).strip()
            existing["kategori"] = str(payload.get("kategori", existing["kategori"]))
            existing["sn_pid"] = str(payload.get("sn_pid", existing.get("sn_pid", "-"))).strip()
            existing["tanggal_masuk_gudang"] = str(
                payload.get("tanggal_masuk_gudang", existing.get("tanggal_masuk_gudang", ""))
            ).strip()
            existing["tanggal_keluar_gudang"] = str(
                payload.get("tanggal_keluar_gudang", existing.get("tanggal_keluar_gudang", ""))
            ).strip()
            existing["kepemilikan"] = str(payload.get("kepemilikan", existing["kepemilikan"]))
            existing["lokasi"] = str(payload.get("lokasi", existing["lokasi"]))
            existing["kondisi"] = str(payload.get("kondisi", existing["kondisi"]))
            existing["status"] = str(payload.get("status", existing["status"]))
            existing["digunakan_oleh"] = str(
                payload.get("digunakan_oleh", existing.get("digunakan_oleh", ""))
            ).strip()
            existing["catatan"] = str(payload.get("catatan", existing.get("catatan", ""))).strip()

            # Perbarui spec monitor jika ada
            for s in mock_monitor_specs_db:
                if s.get("asset_id", "").upper() == norm_id:
                    if "merk" in payload:
                        s["merk"] = payload["merk"]
                    if "tipe_model" in payload:
                        s["tipe_model"] = payload["tipe_model"]
                    if "ukuran_layar" in payload:
                        s["ukuran_layar"] = str(payload["ukuran_layar"]).replace('"', "").strip()
                    if "resolusi_layar" in payload:
                        s["resolusi_layar"] = payload["resolusi_layar"]
                    if "konektivitas" in payload:
                        s["konektivitas"] = payload["konektivitas"]

            # Perbarui spec PC jika ada
            for p in mock_pc_specs_db:
                if p.get("asset_id", "").upper() == norm_id:
                    if "jenis_pc" in payload:
                        p["jenis"] = payload["jenis_pc"]
                    if "cpu" in payload:
                        p["cpu"] = payload["cpu"]
                    if "ram" in payload:
                        p["ram"] = payload["ram"]
                    if "vga" in payload:
                        p["vga"] = payload["vga"]

            formatted = _format_asset_record(existing)
            mock_assets_db[idx] = existing
            return formatted
    return None


def delete_mock_asset(asset_id: str) -> bool:
    global mock_assets_db, mock_monitor_specs_db, mock_pc_specs_db
    norm_id = asset_id.strip().upper()
    before = len(mock_assets_db)
    mock_assets_db = [item for item in mock_assets_db if item.get("id_aset", "").upper() != norm_id]
    mock_monitor_specs_db = [
        s for s in mock_monitor_specs_db if s.get("asset_id", "").upper() != norm_id
    ]
    mock_pc_specs_db = [p for p in mock_pc_specs_db if p.get("asset_id", "").upper() != norm_id]
    return len(mock_assets_db) < before


# ==============================================================================
# ALIASES UNTUK KOMPATIBILITAS KODE
# ==============================================================================
MOCK_ASSETS_DB = mock_assets_db
MOCK_MONITORS_DB = mock_monitor_specs_db
MOCK_PCS_DB = mock_pc_specs_db

create_mock_monitor = create_joined_monitor
delete_mock_monitor = delete_joined_monitor
query_mock_monitors = query_joined_monitors
update_mock_monitor = update_joined_monitor

create_mock_pc = create_joined_pc
delete_mock_pc = delete_joined_pc
query_mock_pcs = query_joined_pcs
update_mock_pc = update_joined_pc


__all__ = [
    "BULAN_ID",
    "MOCK_ASSETS_DB",
    "MOCK_MONITORS_DB",
    "MOCK_PCS_DB",
    "create_joined_monitor",
    "create_joined_pc",
    "create_mock_assets",
    "create_mock_monitor",
    "create_mock_pc",
    "delete_joined_monitor",
    "delete_joined_pc",
    "delete_mock_asset",
    "delete_mock_monitor",
    "delete_mock_pc",
    "format_date_id",
    "format_inch_label",
    "get_next_asset_id",
    "get_next_monitor_id",
    "get_next_pc_id",
    "is_monitor_id_taken",
    "mock_assets_db",
    "mock_monitor_specs_db",
    "mock_pc_specs_db",
    "parse_inch_number",
    "query_joined_monitors",
    "query_joined_pcs",
    "query_mock_assets",
    "query_mock_monitors",
    "query_mock_pcs",
    "update_joined_monitor",
    "update_joined_pc",
    "update_mock_asset",
    "update_mock_monitor",
    "update_mock_pc",
]
