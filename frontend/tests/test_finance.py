"""
Unit tests (pytest) untuk Modul Finansial (Pembelian, Invoice, Tagihan Berulang) ITAM Pro.
"""
import datetime
from copy import deepcopy

import pytest

from itam_pro.services.mock import finance_mock
from itam_pro.services.mock.dashboard_mock import (
    build_bill_alerts,
    get_mock_dashboard_summary,
)
from itam_pro.services.mock.finance_mock import (
    MOCK_BILL_PAYMENTS,
    MOCK_BILLS,
    MOCK_PURCHASES,
    action_jadikan_aset,
    action_pay_bill,
    parse_marketplace_domain,
    query_bills,
    query_invoices,
    query_purchases,
)
from itam_pro.services.mock.seed import MOCK_ASSETS
from itam_pro.services.recurrence import add_months, calculate_bill_status, next_due


def test_parse_marketplace_domain() -> None:
    """1. Uji ekstraksi domain marketplace dan validasi skema HTTP/HTTPS."""
    assert parse_marketplace_domain("https://tokopedia.com/samsung/ssd") == "Tokopedia"
    assert parse_marketplace_domain("http://shopee.co.id/flashdisk") == "Shopee"
    assert parse_marketplace_domain("https://microsoft.com/en-us") == "microsoft.com"
    assert parse_marketplace_domain("") is None
    assert parse_marketplace_domain("   ") is None

    with pytest.raises(ValueError, match="URL wajib diawali dengan http:// atau https://"):
        parse_marketplace_domain("ftp://tokopedia.com")

    with pytest.raises(ValueError, match="URL wajib diawali dengan http:// atau https://"):
        parse_marketplace_domain("tokopedia.com/item")


def test_query_purchases_and_summary_calculation() -> None:
    """2. Uji filter, pagination, dan kalkulasi ringkasan finansial pada query_purchases."""
    res = query_purchases(filters={}, page=1, page_size=10)
    assert res["total"] >= 2
    assert len(res["items"]) >= 2
    assert "summary" in res

    summary = res["summary"]
    assert summary["total_belanja"] > 0
    assert summary["belanja_terbesar"] >= 2100000
    assert summary["belum_dicatat"] >= 1

    # Uji filter pencarian
    search_res = query_purchases(filters={"search": "Samsung"}, page=1, page_size=10)
    assert any("Samsung" in item["produk"] for item in search_res["items"])

    # Uji filter status aset
    status_res = query_purchases(filters={"aset_status": "Bukan aset"}, page=1, page_size=10)
    for item in status_res["items"]:
        assert item["aset_status"] == "Bukan aset"


def test_action_jadikan_aset_generates_n_physical_assets() -> None:
    """3. Uji otomatisasi konversi data pembelian menjadi N aset fisik di seed.py."""
    initial_asset_count = len(MOCK_ASSETS)

    # Cari item pembelian dengan pcs = 2 (SSD NVMe Samsung 980 1TB)
    target_id = "PRC-2026-001"
    target_purchase = next(p for p in MOCK_PURCHASES if p["id_pembelian"] == target_id)
    pcs = target_purchase["pcs"]
    assert pcs == 2

    action_jadikan_aset(
        id_pembelian=target_id,
        kategori="Storage",
        kepemilikan="XML",
        lokasi="Gudang IT",
    )

    # Status pembelian terupdate
    assert target_purchase["aset_status"] == f"{pcs} aset dibuat"

    # N unit aset fisik baru ditambahkan ke MOCK_ASSETS
    assert len(MOCK_ASSETS) == initial_asset_count + pcs
    created_assets = MOCK_ASSETS[:pcs]
    for asset in created_assets:
        assert asset["nama_aset"] == target_purchase["produk"]
        assert asset["kategori"] == "Storage"
        assert asset["kepemilikan"] == "XML"
        assert asset["lokasi"] == "Gudang IT"
        assert asset["kondisi"] == "Baru"
        assert asset["status"] == "Tidak Digunakan"


def _bill(due: datetime.date, **kw: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "BILL-T", "nama": "Tagihan Uji", "vendor": "V", "kategori": "Lainnya",
        "periode": "Bulanan", "nominal": 100000, "jatuh_tempo": due.isoformat(),
        "pengingat_hari": 7, "pembayar": "X", "aktif": True, "anchor_day": due.day,
    }
    base.update(kw)
    return base


def test_dashboard_dynamic_sync_with_finance(monkeypatch: pytest.MonkeyPatch) -> None:
    """4. Dashboard memuat alert tagihan Terlambat/Segera dan grafik pembelian bulanan."""
    today = datetime.date.today()
    monkeypatch.setattr(
        "itam_pro.services.mock.dashboard_mock.MOCK_BILLS",
        [
            _bill(today - datetime.timedelta(days=3), nama="Telat"),
            _bill(today + datetime.timedelta(days=2), nama="Dekat"),
            _bill(today + datetime.timedelta(days=60), nama="Jauh"),
            _bill(today - datetime.timedelta(days=9), nama="Mati", aktif=False),
        ],
    )
    alerts = build_bill_alerts()
    assert [a["title"] for a in alerts] == ["Tagihan: Telat", "Tagihan: Dekat"]
    assert alerts[0]["badge_variant"] == "danger"
    assert alerts[0]["description"] == "Jatuh tempo terlewat 3 hari"
    assert alerts[1]["badge_variant"] == "warning"

    summary = get_mock_dashboard_summary()
    titles = [item["title"] for item in summary["attention_items"]]
    assert "Tagihan: Telat" in titles
    assert len(summary["monthly_purchases"]) > 0


def test_recurrence_add_months_and_leap_year() -> None:
    """5. Kalkulasi bulan: akhir bulan, kabisat, dan anchor_day."""
    d = datetime.date
    assert add_months(d(2026, 1, 31), 1) == d(2026, 2, 28)
    assert add_months(d(2028, 1, 31), 1) == d(2028, 2, 29)  # kabisat
    assert add_months(d(2026, 11, 15), 3) == d(2027, 2, 15)  # lintas tahun
    assert add_months(d(2028, 2, 29), 12) == d(2029, 2, 28)
    # Tanpa anchor tanggal melorot; dengan anchor kembali ke 31.
    feb = add_months(d(2026, 1, 31), 1)
    assert add_months(feb, 1) == d(2026, 3, 28)
    assert add_months(feb, 1, anchor_day=31) == d(2026, 3, 31)


def test_recurrence_next_due_periods() -> None:
    """6. next_due per periode, input str, 'Sekali' = None."""
    assert next_due("2026-10-19", "Bulanan") == datetime.date(2026, 11, 19)
    assert next_due("2026-10-19", "3 bulan") == datetime.date(2027, 1, 19)
    assert next_due("2026-10-19", "6 bulan") == datetime.date(2027, 4, 19)
    assert next_due("2026-10-19", "Tahunan") == datetime.date(2027, 10, 19)
    assert next_due("2026-10-19", "Sekali") is None


def test_calculate_bill_status_boundaries() -> None:
    """7. Status: Terlambat / Segera (<= pengingat) / Terjadwal."""
    today = datetime.date(2026, 10, 24)
    assert calculate_bill_status("2026-10-19", 14, today) == {
        "status": "Terlambat", "label": "Terlambat 5 hari",
    }
    assert calculate_bill_status("2026-10-24", 7, today)["status"] == "Segera"
    assert calculate_bill_status("2026-10-31", 7, today)["status"] == "Segera"
    assert calculate_bill_status("2026-11-01", 7, today)["status"] == "Terjadwal"


def test_query_bills_kpi_and_filters() -> None:
    """8. KPI & filter query_bills dengan tanggal acuan tetap."""
    ref = datetime.date(2026, 10, 24)
    res = query_bills({}, today=ref)
    s = res["summary"]
    assert s["terlambat"] == 1  # BILL-001 (19 Okt)
    assert s["segera"] == 1  # hanya BILL-002 (28 Okt); BILL-003 (1 Nov) = 8 hari > 7
    assert s["tagihan_aktif"] == 6
    # <= 30 hari (termasuk terlambat): BILL-001..004
    assert s["perlu_dibayar_30d"] == 185000 + 1450000 + 450000 + 1250000
    assert res["items"][0]["id"] == "BILL-001"
    assert res["items"][0]["status_variant"] == "danger"
    assert res["items"][0]["nominal_display"] == "Rp185.000"

    late = query_bills({"status": "Terlambat"}, today=ref)
    assert late["total"] == 1
    assert late["summary"]["tagihan_aktif"] == 6  # KPI tidak ikut terfilter
    assert query_bills({"search": "hosting"}, today=ref)["total"] == 2


def test_action_pay_bill_records_history_and_shifts_due() -> None:
    """9. Bayar tagihan: riwayat tersimpan, jatuh tempo geser dari periode lama."""
    snapshot_bills = deepcopy(MOCK_BILLS)
    snapshot_pay = deepcopy(MOCK_BILL_PAYMENTS)
    try:
        action_pay_bill("BILL-001", "2026-10-24", 185000)  # Tahunan
        b1 = next(b for b in MOCK_BILLS if b["id"] == "BILL-001")
        assert b1["jatuh_tempo"] == "2027-10-19"
        assert MOCK_BILL_PAYMENTS[-1]["bill_id"] == "BILL-001"

        action_pay_bill("BILL-002", "2026-10-24", 1450000)  # Bulanan
        b2 = next(b for b in MOCK_BILLS if b["id"] == "BILL-002")
        assert b2["jatuh_tempo"] == "2026-11-28"

        # Tagihan sekali bayar menjadi nonaktif
        MOCK_BILLS.append(_bill(datetime.date(2026, 10, 30), id="BILL-ONCE", periode="Sekali"))
        action_pay_bill("BILL-ONCE", "2026-10-24", 100000)
        assert MOCK_BILLS[-1]["aktif"] is False
    finally:
        MOCK_BILLS[:] = snapshot_bills
        MOCK_BILL_PAYMENTS[:] = snapshot_pay


def test_query_invoices_summary_and_filters() -> None:
    """10. Invoice = arsip bukti; KPI tautan & pembelian tanpa bukti dihitung dinamis."""
    res = query_invoices({})
    s = res["summary"]
    assert s["total_invoice"] == 3
    assert s["sudah_ditautkan"] == 2
    assert s["belum_ditautkan"] == 1
    linked = {
        i["terkait_id"]
        for i in finance_mock.MOCK_INVOICES
        if i["terkait_tipe"] == "pembelian"
    }
    assert s["tanpa_bukti"] == len([p for p in MOCK_PURCHASES if p["id_pembelian"] not in linked])
    assert res["items"][0]["total_display"] == "Rp1.250.000"  # terbaru: NOTA-0187
    assert query_invoices({"tautan": "Belum ditautkan"})["total"] == 1
    assert query_invoices({"search": "hosting"})["total"] == 1
