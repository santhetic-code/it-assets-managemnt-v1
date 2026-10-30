"""
Unit Tests (pytest) untuk Tahap 11B:
- Kalkulasi Power Service (total_tdp & energi_kwh_bulan)
- Seed Server dari CSV (rekap_watt_server.csv)
- Seed Pembelian dari CSV (rekap_pembelian.csv)
- Dashboard Metrics Calculation (dashboard_service.py)
- Sinkronisasi Dashboard Mock dan URL Parametrik AssetState
"""
from typing import Any
from unittest.mock import MagicMock

import pytest

from itam_pro.services.dashboard_service import calculate_dashboard_metrics
from itam_pro.services.mock.dashboard_mock import get_mock_dashboard_summary
from itam_pro.services.mock.finance_mock import MOCK_PURCHASES
from itam_pro.services.mock.seed import MOCK_ASSETS, _load_server_csv
from itam_pro.services.power_service import energi_kwh_bulan, total_tdp
from itam_pro.states.asset_state import AssetState


def test_power_service_calculations() -> None:
    """1. Uji fungsi kalkulasi TDP total dan estimasi energi kWh bulanan."""
    sample_assets: list[dict[str, Any]] = [
        {"attributes": {"tdp_total_w": "250.5"}},
        {"attributes": {"tdp_total_w": 149.5}},
        {"attributes": {"tdp_total_w": "invalid"}},
        {"attributes": {}},
        {},
    ]
    total_w = total_tdp(sample_assets)
    assert total_w == 400.0

    # Default jam = 720 (30 hari * 24 jam)
    # (400 / 1000) * 720 = 288.0 kWh
    assert energi_kwh_bulan(total_w) == 288.0
    # Custom jam = 24 jam
    assert energi_kwh_bulan(total_w, jam=24) == pytest.approx(9.6)

    # List kosong
    assert total_tdp([]) == 0.0
    assert energi_kwh_bulan(0.0) == 0.0


def test_rekap_watt_server_csv_loaded() -> None:
    """2. Uji hasil parsing rekap_watt_server.csv ke dalam format Server ITAM Pro."""
    loaded_servers = _load_server_csv()
    assert len(loaded_servers) > 0

    first_server = loaded_servers[0]
    assert first_server["kategori"] == "Server"
    assert first_server["id_aset"].startswith("SRV-")
    assert "tdp_total_w" in first_server["attributes"]
    assert "cpu" in first_server["attributes"]
    assert "ram" in first_server["attributes"]
    assert "hdd_ssd" in first_server["attributes"]

    # Pastikan server juga terdaftar di MOCK_ASSETS
    server_in_mock = [a for a in MOCK_ASSETS if a.get("kategori") == "Server"]
    assert len(server_in_mock) >= len(loaded_servers)


def test_rekap_pembelian_csv_loaded() -> None:
    """3. Uji hasil parsing rekap_pembelian.csv ke MOCK_PURCHASES."""
    assert len(MOCK_PURCHASES) > 0
    first_purchase = MOCK_PURCHASES[0]
    assert first_purchase["id_pembelian"].startswith("PRC-CSV-")
    assert "tanggal" in first_purchase
    assert "harga" in first_purchase
    assert isinstance(first_purchase["harga"], int)
    assert isinstance(first_purchase["pcs"], int)
    assert first_purchase["pcs"] >= 1
    assert first_purchase["dibeli_oleh"] == "Data CSV"


def test_calculate_dashboard_metrics() -> None:
    """4. Uji fungsi terpusat calculate_dashboard_metrics."""
    metrics = calculate_dashboard_metrics()

    assert "kpis" in metrics
    kpis = metrics["kpis"]
    assert kpis["total_assets"] == len(MOCK_ASSETS)
    assert kpis["in_use_assets"] <= kpis["total_assets"]
    assert 0 <= kpis["in_use_percent"] <= 100
    assert kpis["server_power_kw"] >= 0.0
    assert kpis["server_energy_kwh_month"] >= 0.0

    assert "monthly_purchases" in metrics
    purchases = metrics["monthly_purchases"]
    assert len(purchases) == 6
    assert purchases[-1]["is_latest"] is True
    for p in purchases:
        assert "month" in p
        assert "amount_million" in p

    assert "assets_by_category" in metrics
    categories = metrics["assets_by_category"]
    assert any(c["name"] == "Server" for c in categories)

    assert "ip_conflict_count" in metrics


def test_dashboard_mock_integration_with_service() -> None:
    """5. Uji get_mock_dashboard_summary menggunakan data dari calculate_dashboard_metrics."""
    summary = get_mock_dashboard_summary()
    assert "kpis" in summary
    assert "monthly_purchases" in summary
    assert "assets_by_category" in summary
    assert "ups_loads" in summary
    assert "attention_items" in summary
    assert "recent_activities" in summary

    # Total assets harus sama dengan panjang MOCK_ASSETS
    assert summary["kpis"]["total_assets"] == len(MOCK_ASSETS)
    assert len(summary["monthly_purchases"]) == 6


@pytest.mark.anyio
async def test_asset_state_url_parametric_query() -> None:
    """6. Uji penanganan argumen query URL ?status dan ?kategori pada AssetState."""
    state = AssetState()
    state.router = MagicMock()

    # Simulasi ?status=Digunakan
    state.router.page.params = {"status": "Digunakan"}
    state.router.page.path = "/assets"
    await state.load_view_data()

    assert state.status_filter == "Digunakan"
    assert state.kategori_filter == ""
    assert all(item.get("status") == "Digunakan" for item in state.items)

    # Simulasi ?kategori=Monitor
    state.router.page.params = {"kategori": "Monitor"}
    state.router.page.path = "/assets"
    await state.load_view_data()

    assert state.status_filter == ""
    assert state.kategori_filter == "Monitor"
    assert all(item.get("kategori") == "Monitor" for item in state.items)
