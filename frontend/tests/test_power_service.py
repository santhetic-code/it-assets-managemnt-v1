"""
Unit tests untuk Layanan Rekap Watt Server ITAM Pro.
"""
import pytest

from itam_pro.pages.infrastructure.watt_server import watt_server_page
from itam_pro.services.api_client import api_client
from itam_pro.services.power_service import (
    energi_kwh_bulan,
    enrich_server_power_row,
    query_server_power,
    remove_server_power_entry,
    save_server_power_entry,
    total_tdp,
)


def test_energi_kwh_and_total_tdp_calculation() -> None:
    """1. Uji rumus kalkulasi total TDP dan estimasi kWh bulanan."""
    assert energi_kwh_bulan(1000.0, jam=720) == 720.0
    assert energi_kwh_bulan(500.0, jam=720) == 360.0

    sample_assets = [
        {"attributes": {"tdp_total_w": "150"}},
        {"attributes": {"tdp_total_w": "250"}},
        {"attributes": {"tdp_total_w": "invalid"}},
    ]
    assert total_tdp(sample_assets) == 400.0


def test_enrich_server_power_row() -> None:
    """2. Uji parsing spesifikasi, klasifikasi beban, dan pengelompokan server."""
    dummy_server = {
        "id_aset": "SRV-TEST",
        "nama_aset": "SERVER UTAMA OTO",
        "status": "Digunakan",
        "attributes": {
            "cpu": "Intel Xeon E5-2680",
            "vga": "NVIDIA T400",
            "ram": "64GB DDR4",
            "hdd_ssd": "2x 1TB NVMe",
            "tdp_total_w": "240",
            "psu_min_w": "350",
            "psu_rekomendasi_w": "500",
        },
    }
    enriched = enrich_server_power_row(dummy_server)
    assert enriched["grup_server"] == "Operasional"
    assert enriched["cpu_brand"] == "Intel"
    assert enriched["tdp_total_w"] == 240
    assert enriched["beban_badge"] == "Tinggi"
    assert enriched["beban_variant"] == "warning"
    assert "kWh/bln" in enriched["kwh_display"]

    # Test server backup
    dummy_backup = {
        "id_aset": "SRV-BK",
        "nama_aset": "SERVER BACKUP REALTIME",
        "status": "Backup",
        "attributes": {
            "cpu": "AMD EPYC 7302P",
            "tdp_total_w": "160",
        },
    }
    enriched_bk = enrich_server_power_row(dummy_backup)
    assert enriched_bk["grup_server"] == "Backup"
    assert enriched_bk["cpu_brand"] == "AMD"
    assert enriched_bk["beban_badge"] == "Efisien"
    assert enriched_bk["beban_variant"] == "success"


def test_query_server_power_filter_and_aggregation() -> None:
    """3. Uji filter tab, CPU, pencarian, dan kalkulasi ringkasan ESTIMASI."""
    res_all = query_server_power(filters={})
    assert res_all["total"] >= 16
    assert res_all["tab_counts"]["Semua"] >= 16
    assert res_all["tab_counts"]["Operasional"] >= 1
    assert res_all["tab_counts"]["Backup"] >= 1

    summary = res_all["summary"]
    assert summary["total_tdp_w"] > 0
    assert summary["total_tdp_kw"] > 0
    assert summary["est_kwh_month"] > 0
    assert summary["avg_tdp_w"] > 0
    assert summary["max_tdp_w"] > 0

    # Filter tab Operasional
    res_ops = query_server_power(filters={"tab": "Operasional"})
    assert res_ops["total"] == res_all["tab_counts"]["Operasional"]
    for s in res_ops["items"]:
        assert s["grup_server"] == "Operasional"

    # Filter CPU Brand Intel
    res_intel = query_server_power(filters={"cpu_brand": "Intel"})
    for s in res_intel["items"]:
        assert s["cpu_brand"] == "Intel"

    # Filter Pencarian
    res_search = query_server_power(filters={"search": "OTO"})
    assert res_search["total"] >= 1


def test_server_power_crud_operations() -> None:
    """4. Uji penambahan, pembaruan, dan penghapusan entri server."""
    payload = {
        "nama_aset": "SRV PENGUJIAN BARU",
        "cpu": "Intel Core i5-12400",
        "vga": "Integrated",
        "ram": "32GB",
        "hdd_ssd": "1TB SSD",
        "tdp_total_w": 130,
        "psu_min_w": 200,
        "psu_rekomendasi_w": 300,
        "lokasi": "Kantor Pusat",
        "status": "Digunakan",
        "catatan": "Unit testing",
    }
    saved = save_server_power_entry(payload)
    new_id = saved["id_aset"]
    assert new_id.startswith("SRV-")
    assert saved["nama_aset"] == "SRV PENGUJIAN BARU"
    assert saved["tdp_total_w"] == 130

    # Edit
    payload["nama_aset"] = "SRV PENGUJIAN DIUBAH"
    payload["tdp_total_w"] = 145
    updated = save_server_power_entry(payload, asset_id=new_id)
    assert updated["id_aset"] == new_id
    assert updated["nama_aset"] == "SRV PENGUJIAN DIUBAH"
    assert updated["tdp_total_w"] == 145

    # Hapus
    removed = remove_server_power_entry(new_id)
    assert removed is True


@pytest.mark.anyio
async def test_api_client_server_power() -> None:
    """5. Uji pemanggilan APIClient untuk get_server_power."""
    res = await api_client.get_server_power(filters={})
    assert "items" in res
    assert "total" in res
    assert "summary" in res
    assert res["total"] >= 16


def test_watt_server_page_ui_compilation() -> None:
    """6. Uji kompilasi komponen antarmuka halaman /watt-server."""
    page = watt_server_page()
    assert page is not None

