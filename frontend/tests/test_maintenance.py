"""
Unit tests untuk Modul Jadwal Maintenance ITAM Pro (Tahap 10).
"""
from copy import deepcopy
from datetime import date

from itam_pro.services.category_config import CATEGORY_PREFIX_MAP, get_config_by_slug
from itam_pro.services.mock.dashboard_mock import build_maintenance_alerts
from itam_pro.services.mock.maintenance_mock import (
    MOCK_MAINTENANCE_LOGS,
    MOCK_MAINTENANCE_PLANS,
    action_buat_jadwal_massal,
    action_tandai_selesai,
    calculate_plan_status,
    query_maintenance_logs,
    query_maintenance_plans,
)
from itam_pro.services.recurrence import next_due


def test_printer_category_config() -> None:
    """1. Uji konfigurasi kategori Printer & Scanner."""
    cfg = get_config_by_slug("printer")
    assert cfg is not None
    assert cfg["name"] == "Printer"
    assert cfg["code"] == "PRN"
    assert cfg["tab_field"] == "jenis"
    assert "LaserJet" in cfg["tab_options"]
    assert "Printer" in cfg["included_categories"]
    assert "Scanner" in cfg["included_categories"]
    assert CATEGORY_PREFIX_MAP.get("Printer") == "PRN"
    assert CATEGORY_PREFIX_MAP.get("Scanner") == "SCN"


def test_calculate_plan_status() -> None:
    """2. Uji status relatif jatuh tempo maintenance."""
    assert calculate_plan_status("")["status"] == "Selesai"
    assert calculate_plan_status("2020-01-01")["status"] == "Terlambat"
    today_str = date.today().strftime("%Y-%m-%d")
    assert calculate_plan_status(today_str)["status"] == "Segera"
    assert calculate_plan_status("2099-12-31")["status"] == "Terjadwal"


def test_query_maintenance_plans_and_summary() -> None:
    """3. Uji query jadwal maintenance, resolusi display, dan rangkuman KPI."""
    res = query_maintenance_plans({})
    assert res["total"] >= 12
    summary = res["summary"]
    assert summary["aktif"] >= 12
    assert summary["tindak_lanjut"] >= 1
    # Uji objek_display terisi (baik tautan aset maupun teks bebas)
    for item in res["items"]:
        assert len(item["objek_display"]) > 0

    # Uji pencarian
    filtered = query_maintenance_plans({"search": "Database"})
    assert filtered["total"] >= 1
    assert "Database Produksi" in [x["objek_display"] for x in filtered["items"]]


def test_action_tandai_selesai_records_log_and_shifts_due() -> None:
    """4. Uji eksekusi 'Tandai Selesai' mencatat log dan menggeser tanggal berikutnya."""
    plans_backup = deepcopy(MOCK_MAINTENANCE_PLANS)
    logs_backup = deepcopy(MOCK_MAINTENANCE_LOGS)
    try:
        initial_log_count = len(MOCK_MAINTENANCE_LOGS)
        action_tandai_selesai(
            plan_id="MP-001",
            tgl_selesai="2026-10-24",
            hasil="Normal",
            catatan="Cek tegangan baterai ok",
            pic="Ridho",
        )
        assert len(MOCK_MAINTENANCE_LOGS) == initial_log_count + 1
        new_log = MOCK_MAINTENANCE_LOGS[0]
        assert new_log["plan_id"] == "MP-001"
        assert new_log["hasil"] == "Normal"
        assert new_log["dikerjakan_oleh"] == "Ridho"

        # Cek jadwal berikutnya digeser (3 bulan dari 2026-10-12 -> 2027-01-12)
        p1 = next(p for p in MOCK_MAINTENANCE_PLANS if p["id"] == "MP-001")
        assert p1["terakhir_dilakukan"] == "2026-10-24"
        assert p1["terakhir_hasil"] == "Normal"
        assert p1["jadwal_berikutnya"] == "2027-01-12"

        # Uji jika frekuensi 'Sekali' menjadi nonaktif (jadwal_berikutnya="")
        action_tandai_selesai(
            plan_id="MP-002",
            tgl_selesai="2026-10-24",
            hasil="Normal",
            catatan="Baterai UPS diganti baru",
            pic="Surya",
        )
        p2 = next(p for p in MOCK_MAINTENANCE_PLANS if p["id"] == "MP-002")
        assert p2["jadwal_berikutnya"] == ""
    finally:
        MOCK_MAINTENANCE_PLANS[:] = plans_backup
        MOCK_MAINTENANCE_LOGS[:] = logs_backup


def test_action_buat_jadwal_massal() -> None:
    """5. Uji pembuatan jadwal serentak per kategori aset."""
    plans_backup = deepcopy(MOCK_MAINTENANCE_PLANS)
    try:
        count_before = len(MOCK_MAINTENANCE_PLANS)
        action_buat_jadwal_massal(
            kategori="UPS",
            kegiatan="Pengecekan fisik baterai & grounding",
            jenis="Pengecekan rutin",
            frekuensi="6 bulan",
            tgl_mulai="2026-11-01",
            pic="Ridho",
        )
        assert len(MOCK_MAINTENANCE_PLANS) > count_before
        created = [p for p in MOCK_MAINTENANCE_PLANS if p["kegiatan"] == "Pengecekan fisik baterai & grounding"]
        assert len(created) > 0
        assert all(p["frekuensi"] == "6 bulan" for p in created)
        assert all(p["jadwal_berikutnya"] == "2026-11-01" for p in created)
    finally:
        MOCK_MAINTENANCE_PLANS[:] = plans_backup


def test_dashboard_maintenance_alerts() -> None:
    """6. Uji deteksi 'Perlu tindak lanjut' dan status 'Terlambat' di dashboard."""
    alerts = build_maintenance_alerts()
    # Harus ada alert 'Perlu tindak lanjut' dari Printer Blok 14
    assert any("Tindak Lanjut" in a["title"] for a in alerts)
    assert any(a["badge_variant"] == "warning" for a in alerts)
    # Harus ada alert status Terlambat
    assert any(a["badge_variant"] == "danger" for a in alerts)
