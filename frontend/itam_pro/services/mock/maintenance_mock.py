"""
Data Mock Modul Jadwal Maintenance ITAM Pro (Tahap 10).
Melebur jadwal fisik (PC/Printer/Server) dan perangkat lunak (Backup Database)
ke dalam satu ekosistem terpadu menggunakan recurrence engine.
"""
from copy import deepcopy
from datetime import date, datetime
from typing import Any

from itam_pro.services.mock.seed import MOCK_ASSETS
from itam_pro.services.recurrence import next_due

# 12 Mock Jadwal Sesuai Referensi UI
MOCK_MAINTENANCE_PLANS: list[dict[str, Any]] = [
    {
        "id": "MP-001",
        "objek_asset_id": "UPS-0004",
        "objek_teks": "",
        "kegiatan": "Cek kondisi baterai & beban",
        "jenis": "Pengecekan rutin",
        "frekuensi": "3 bulan",
        "terakhir_dilakukan": "2026-07-12",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-10-12",
        "pic": "Ridho",
        "catatan": "",
    },
    {
        "id": "MP-002",
        "objek_asset_id": "UPS-0011",
        "objek_teks": "",
        "kegiatan": "Ganti baterai (usia > 3 tahun)",
        "jenis": "Ganti baterai",
        "frekuensi": "Sekali",
        "terakhir_dilakukan": "",
        "terakhir_hasil": "",
        "jadwal_berikutnya": "2026-10-26",
        "pic": "Surya",
        "catatan": "",
    },
    {
        "id": "MP-003",
        "objek_asset_id": "",
        "objek_teks": "Database Produksi",
        "kegiatan": "Backup & uji restore",
        "jenis": "Backup",
        "frekuensi": "Mingguan",
        "terakhir_dilakukan": "2026-10-18",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-10-25",
        "pic": "Surya",
        "catatan": "",
    },
    {
        "id": "MP-004",
        "objek_asset_id": "PC-0003",
        "objek_teks": "",
        "kegiatan": "Cek & bersihkan debu",
        "jenis": "Pengecekan rutin",
        "frekuensi": "6 bulan",
        "terakhir_dilakukan": "2026-05-03",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-11-03",
        "pic": "Ridho",
        "catatan": "",
    },
    {
        "id": "MP-005",
        "objek_asset_id": "",
        "objek_teks": "Printer Blok 14",
        "kegiatan": "Cek toner & head",
        "jenis": "Pengecekan rutin",
        "frekuensi": "Bulanan",
        "terakhir_dilakukan": "2026-10-05",
        "terakhir_hasil": "Perlu tindak lanjut",
        "jadwal_berikutnya": "2026-11-05",
        "pic": "Ridho",
        "catatan": "",
    },
    {
        "id": "MP-006",
        "objek_asset_id": "SRV-0001",
        "objek_teks": "",
        "kegiatan": "Update OS & patch keamanan",
        "jenis": "Servis",
        "frekuensi": "3 bulan",
        "terakhir_dilakukan": "2026-08-20",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-11-20",
        "pic": "Surya",
        "catatan": "",
    },
    {
        "id": "MP-007",
        "objek_asset_id": "SRV-0002",
        "objek_teks": "",
        "kegiatan": "Cek disk & log monitoring",
        "jenis": "Pengecekan rutin",
        "frekuensi": "Bulanan",
        "terakhir_dilakukan": "2026-10-01",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-11-01",
        "pic": "Surya",
        "catatan": "",
    },
    {
        "id": "MP-008",
        "objek_asset_id": "PC-0002",
        "objek_teks": "",
        "kegiatan": "Cek thermal pasta & fan cooler",
        "jenis": "Pengecekan rutin",
        "frekuensi": "6 bulan",
        "terakhir_dilakukan": "2026-05-15",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-11-15",
        "pic": "Ridho",
        "catatan": "",
    },
    {
        "id": "MP-009",
        "objek_asset_id": "",
        "objek_teks": "Server Backup Synology NAS",
        "kegiatan": "Uji integritas RAID & disk scrub",
        "jenis": "Pengecekan rutin",
        "frekuensi": "Bulanan",
        "terakhir_dilakukan": "2026-10-02",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-11-02",
        "pic": "Surya",
        "catatan": "",
    },
    {
        "id": "MP-010",
        "objek_asset_id": "RTR-0001",
        "objek_teks": "",
        "kegiatan": "Backup konfigurasi MikroTik & cek firmware",
        "jenis": "Backup",
        "frekuensi": "Bulanan",
        "terakhir_dilakukan": "2026-09-28",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-10-28",
        "pic": "Surya",
        "catatan": "",
    },
    {
        "id": "MP-011",
        "objek_asset_id": "UPS-0001",
        "objek_teks": "",
        "kegiatan": "Kalibrasi sensor & uji discharge baterai",
        "jenis": "Servis",
        "frekuensi": "Tahunan",
        "terakhir_dilakukan": "2025-11-10",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-11-10",
        "pic": "Ridho",
        "catatan": "",
    },
    {
        "id": "MP-012",
        "objek_asset_id": "",
        "objek_teks": "Printer EPSON L3110 HRD",
        "kegiatan": "Pembersihan waste ink pad & printhead",
        "jenis": "Servis",
        "frekuensi": "6 bulan",
        "terakhir_dilakukan": "2026-04-14",
        "terakhir_hasil": "Normal",
        "jadwal_berikutnya": "2026-10-14",
        "pic": "Ridho",
        "catatan": "",
    },
]

MOCK_MAINTENANCE_LOGS: list[dict[str, Any]] = [
    {
        "id": "MLOG-001",
        "plan_id": "MP-001",
        "objek_asset_id": "UPS-0004",
        "objek_display": "UPS-0004 · UPS Server 1",
        "kegiatan": "Cek kondisi baterai & beban",
        "tanggal_selesai": "2026-07-12",
        "dikerjakan_oleh": "Ridho",
        "hasil": "Normal",
        "catatan": "Tegangan aki masih optimal 13.6V, load 64%.",
    },
    {
        "id": "MLOG-002",
        "plan_id": "MP-003",
        "objek_asset_id": "",
        "objek_display": "Database Produksi",
        "kegiatan": "Backup & uji restore",
        "tanggal_selesai": "2026-10-18",
        "dikerjakan_oleh": "Surya",
        "hasil": "Normal",
        "catatan": "Dump PostgreSQL 42 GB sukses, uji restore di staging berjalan lancar.",
    },
    {
        "id": "MLOG-003",
        "plan_id": "MP-005",
        "objek_asset_id": "",
        "objek_display": "Printer Blok 14",
        "kegiatan": "Cek toner & head",
        "tanggal_selesai": "2026-10-05",
        "dikerjakan_oleh": "Ridho",
        "hasil": "Perlu tindak lanjut",
        "catatan": "Roller penarik kertas agak aus, sering paper jam pada tray 1.",
    },
    {
        "id": "MLOG-004",
        "plan_id": "MP-006",
        "objek_asset_id": "SRV-0001",
        "objek_display": "SRV-0001 · Server Proxmox Node 1",
        "kegiatan": "Update OS & patch keamanan",
        "tanggal_selesai": "2026-08-20",
        "dikerjakan_oleh": "Surya",
        "hasil": "Normal",
        "catatan": "Kernel update berhasil, reboot terkendali tanpa downtime VM.",
    },
    {
        "id": "MLOG-005",
        "plan_id": "MP-007",
        "objek_asset_id": "SRV-0002",
        "objek_display": "SRV-0002 · Server Storage NAS",
        "kegiatan": "Cek disk & log monitoring",
        "tanggal_selesai": "2026-10-01",
        "dikerjakan_oleh": "Surya",
        "hasil": "Normal",
        "catatan": "Disk SMART status healthy, kapasitas terpakai 58%.",
    },
]


def _get_asset_name_map() -> dict[str, str]:
    """Peta id_aset ke nama_aset untuk visualisasi nama objek yang jelas."""
    return {a["id_aset"]: a.get("nama_aset", "") for a in MOCK_ASSETS if "id_aset" in a}


def calculate_plan_status(jadwal_berikutnya: str, pengingat_hari: int = 7) -> dict[str, str]:
    """Hitung status relatif jadwal berikutnya (Terlambat, Segera, Terjadwal, Selesai)."""
    if not jadwal_berikutnya:
        return {"status": "Selesai", "label": "Arsip", "variant": "neutral"}
    try:
        j_tempo = datetime.strptime(jadwal_berikutnya.strip(), "%Y-%m-%d").date()
    except ValueError:
        return {"status": "Terjadwal", "label": jadwal_berikutnya, "variant": "info"}

    today = date.today()
    diff = (j_tempo - today).days

    if diff < 0:
        return {"status": "Terlambat", "label": f"Terlambat {abs(diff)} hari", "variant": "danger"}
    elif diff == 0:
        return {"status": "Segera", "label": "Hari ini", "variant": "warning"}
    elif diff <= pengingat_hari:
        return {"status": "Segera", "label": f"{diff} hari lagi", "variant": "warning"}
    else:
        return {"status": "Terjadwal", "label": f"{diff} hari lagi", "variant": "info"}


def query_maintenance_plans(
    filters: dict[str, Any] | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Query dan filter jadwal maintenance dengan KPI rangkuman teragregasi."""
    filters = filters or {}
    asset_name_map = _get_asset_name_map()
    filtered: list[dict[str, Any]] = []
    stats = {"terlambat": 0, "segera": 0, "aktif": 0, "tindak_lanjut": 0}

    search = str(filters.get("search", "")).strip().lower()

    for plan in MOCK_MAINTENANCE_PLANS:
        row = deepcopy(plan)
        # 1. Resolusi Nama Objek (Taut Aset vs Teks Bebas)
        aid = row.get("objek_asset_id")
        if aid:
            nama_aset = asset_name_map.get(aid)
            row["objek_display"] = f"{aid} · {nama_aset}" if nama_aset else aid
        else:
            row["objek_display"] = row.get("objek_teks", "")

        # 2. Kalkulasi Status Relatif
        status_info = calculate_plan_status(row["jadwal_berikutnya"])
        row["status"] = status_info["status"]
        row["status_label"] = status_info["label"]
        row["status_variant"] = status_info.get("variant", "neutral")

        # 3. Hitung KPI
        if row["status"] != "Selesai":
            stats["aktif"] += 1
            if row["status"] == "Terlambat":
                stats["terlambat"] += 1
            if row["status"] == "Segera":
                stats["segera"] += 1
        if row["terakhir_hasil"] == "Perlu tindak lanjut":
            stats["tindak_lanjut"] += 1

        # 4. Filter Pencarian
        if search:
            match = (
                search in row["objek_display"].lower()
                or search in str(row.get("kegiatan", "")).lower()
                or search in str(row.get("pic", "")).lower()
                or search in str(row.get("jenis", "")).lower()
                or search in str(row.get("status", "")).lower()
            )
            if not match:
                continue

        filtered.append(row)

    filtered.sort(key=lambda x: (x["jadwal_berikutnya"] or "9999-12-31"))
    start = max(0, (page - 1) * page_size)

    return {
        "items": filtered[start : start + page_size],
        "total": len(filtered),
        "summary": stats,
        "page": page,
        "page_size": page_size,
    }


def query_maintenance_logs(
    filters: dict[str, Any] | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Query daftar riwayat/log eksekusi maintenance."""
    filters = filters or {}
    filtered = deepcopy(MOCK_MAINTENANCE_LOGS)
    search = str(filters.get("search", "")).strip().lower()

    if search:
        filtered = [
            log_entry
            for log_entry in filtered
            if search in str(log_entry.get("objek_display", "")).lower()
            or search in str(log_entry.get("kegiatan", "")).lower()
            or search in str(log_entry.get("catatan", "")).lower()
            or search in str(log_entry.get("dikerjakan_oleh", "")).lower()
            or search in str(log_entry.get("hasil", "")).lower()
        ]

    asset_id = filters.get("asset_id")
    if asset_id:
        filtered = [
            log_entry
            for log_entry in filtered
            if log_entry.get("objek_asset_id") == asset_id
        ]

    start = max(0, (page - 1) * page_size)
    return {
        "items": filtered[start : start + page_size],
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
    }


def action_tandai_selesai(
    plan_id: str,
    tgl_selesai: str,
    hasil: str,
    catatan: str,
    pic: str,
) -> None:
    """Tandai jadwal maintenance selesai, catat riwayat log, dan geser jadwal berikutnya."""
    asset_name_map = _get_asset_name_map()
    for plan in MOCK_MAINTENANCE_PLANS:
        if plan["id"] == plan_id:
            aid = plan.get("objek_asset_id", "")
            if aid:
                nama = asset_name_map.get(aid)
                objek_disp = f"{aid} · {nama}" if nama else aid
            else:
                objek_disp = plan.get("objek_teks", "")

            # Tulis riwayat ke logs (paling atas)
            MOCK_MAINTENANCE_LOGS.insert(
                0,
                {
                    "id": f"MLOG-{len(MOCK_MAINTENANCE_LOGS)+1:03d}",
                    "plan_id": plan_id,
                    "objek_asset_id": aid,
                    "objek_display": objek_disp,
                    "kegiatan": plan.get("kegiatan", ""),
                    "tanggal_selesai": tgl_selesai,
                    "dikerjakan_oleh": pic,
                    "hasil": hasil,
                    "catatan": catatan,
                },
            )

            # Geser jadwal plan
            plan["terakhir_dilakukan"] = tgl_selesai
            plan["terakhir_hasil"] = hasil

            if plan["frekuensi"] == "Sekali":
                plan["jadwal_berikutnya"] = ""  # Nonaktif
            else:
                baru = next_due(plan["jadwal_berikutnya"], plan["frekuensi"])
                if baru:
                    plan["jadwal_berikutnya"] = baru.strftime("%Y-%m-%d")
            break


def action_buat_jadwal_massal(
    kategori: str,
    kegiatan: str,
    jenis: str,
    frekuensi: str,
    tgl_mulai: str,
    pic: str,
) -> None:
    """Buat jadwal maintenance secara massal untuk seluruh aset pada kategori tertentu."""
    for asset in MOCK_ASSETS:
        if asset.get("kategori") == kategori or kategori == "Semua":
            MOCK_MAINTENANCE_PLANS.append(
                {
                    "id": f"MP-{len(MOCK_MAINTENANCE_PLANS)+1:03d}",
                    "objek_asset_id": asset.get("id_aset", ""),
                    "objek_teks": "",
                    "kegiatan": kegiatan,
                    "jenis": jenis,
                    "frekuensi": frekuensi,
                    "terakhir_dilakukan": "",
                    "terakhir_hasil": "",
                    "jadwal_berikutnya": tgl_mulai,
                    "pic": pic,
                    "catatan": "",
                }
            )


__all__ = [
    "MOCK_MAINTENANCE_LOGS",
    "MOCK_MAINTENANCE_PLANS",
    "action_buat_jadwal_massal",
    "action_tandai_selesai",
    "calculate_plan_status",
    "query_maintenance_logs",
    "query_maintenance_plans",
]
