"""
Unit tests (pytest) untuk Modul Finansial (Pembelian & Invoice) ITAM Pro (Tahap 9).
"""
import pytest

from itam_pro.services.mock.dashboard_mock import (
    build_invoice_alert,
    get_mock_dashboard_summary,
)
from itam_pro.services.mock.finance_mock import (
    MOCK_INVOICES,
    MOCK_PURCHASES,
    action_jadikan_aset,
    parse_marketplace_domain,
    query_purchases,
)
from itam_pro.services.mock.seed import MOCK_ASSETS


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


def test_dashboard_dynamic_sync_with_finance() -> None:
    """4. Uji sinkronisasi dinamis dashboard dengan data pembelian dan peringatan invoice."""
    # Bersihkan / isi invoice mock untuk pengujian alert
    MOCK_INVOICES.clear()
    assert build_invoice_alert() is None

    MOCK_INVOICES.append(
        {
            "id_invoice": "INV-TEST-001",
            "vendor": "PT Vendor Test",
            "jumlah": 5000000,
            "status": "Belum Dibayar",
        }
    )
    alert = build_invoice_alert()
    assert alert is not None
    assert alert["badge_label"] == "Finance"
    assert "1 invoice mendekati jatuh tempo" in alert["description"]

    # Dashboard summary mencakup perhatian invoice dan grafik pembelian bulanan
    summary = get_mock_dashboard_summary()
    assert any(item["title"] == "Invoice Belum Dibayar" for item in summary["attention_items"])
    assert len(summary["monthly_purchases"]) > 0
