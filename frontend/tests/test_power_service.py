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
    """2. Uji parsing spesifikasi, klasifikasi beban Artboard 15, dan pengelompokan server."""
    dummy_server = {
        "id_aset": "SRV-TEST",
        "nama_aset": "SERVER UTAMA OTO",
        "status": "Digunakan",
        "attributes": {
            "cpu": "Intel Xeon E5-2680",
            "vga": "NVIDIA T400",
            "ram": "4x DDR4",
            "hdd_ssd": "2x SSD SATA, 1x SSD M.2",
            "tdp_total_w": "240",
            "psu_min_w": "325",
            "psu_rekomendasi_w": "400",
        },
    }
    enriched = enrich_server_power_row(dummy_server)
    assert enriched["grup_server"] == "Operasional"
    assert enriched["cpu_brand"] == "Intel"
    assert enriched["tdp_total_w"] == 240
    assert enriched["beban_efektif_w"] == 240
    assert enriched["beban_badge"] == "Sedang"
    assert enriched["beban_variant"] == "warning"
    assert "kWh" in enriched["kwh_display"]
    assert enriched["biaya_display"] == ""  # Default tarif kosong = sembunyikan rupiah

    # Test server backup (< 220 W = Rendah)
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
    assert enriched_bk["beban_badge"] == "Rendah"
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


def test_psu_formula_and_optional_tarif_and_ups_datasheet() -> None:
    """7. Uji konsistensi rumus PSU, tarif listrik opsional, dan kapasitas watt UPS manual."""
    from itam_pro.services.power_service import (
        calculate_psu_specs,
        update_mock_power_assumptions,
        update_mock_ups_capacity_watt,
    )

    # Konsistensi rumus PSU: 142 W -> 250 / 350 W, 211 W -> 300 / 400 W
    psu_142 = calculate_psu_specs(142)
    assert psu_142["psu_min_w"] == 250
    assert psu_142["psu_rekomendasi_w"] == 350

    psu_211 = calculate_psu_specs(211)
    assert psu_211["psu_min_w"] == 300
    assert psu_211["psu_rekomendasi_w"] == 400

    # Deteksi inkonsistensi override SRV-003 (198 W dengan override 400/500 W)
    psu_198_ov = calculate_psu_specs(198, override_min_w=400, override_rek_w=500)
    assert psu_198_ov["psu_min_w"] == 400
    assert psu_198_ov["formula_psu_min_w"] == 300
    assert psu_198_ov["psu_inconsistent"] is True

    # Uji perubahan tarif opsional & kapasitas UPS manual (Datasheet vs Perkiraan)
    update_mock_power_assumptions({"tarif_listrik_per_kwh": 1500})
    update_mock_ups_capacity_watt("UPS-009", 420)
    res = query_server_power(filters={})
    assert res["summary"]["estimasi_biaya_bulan"] is not None
    ups_009 = next((u for u in res["ups_items"] if u["id_aset"] == "UPS-009"), None)
    if ups_009:
        assert ups_009["sumber_kapasitas"] == "Datasheet"
        assert ups_009["kapasitas_watt"] == 420

    # Kembalikan ke default tarif kosong
    update_mock_power_assumptions({"tarif_listrik_per_kwh": None})


def test_ups_load_ratio_and_tdp_psu_status_thresholds() -> None:
    """8. Uji rumus beban UPS (TDP / kapasitas Watt) & ambang status TDP/PSU min."""
    from itam_pro.services.power_service import (
        calculate_ups_load_pct,
        classify_tdp_psu_status,
    )

    # Beban UPS = TDP / kapasitas Watt UPS
    assert calculate_ups_load_pct(211, 390) == pytest.approx(54.1)
    assert calculate_ups_load_pct(162, 390) == pytest.approx(41.5)
    assert calculate_ups_load_pct(200, 0) == 0.0

    # Ambang status TDP / PSU Min: Aman <70%, Waspada >=70%, Kritis >=90%
    assert classify_tdp_psu_status(159, 250)["status"] == "Aman"
    assert classify_tdp_psu_status(159, 250)["variant"] == "success"

    waspada = classify_tdp_psu_status(211, 300)
    assert waspada["status"] == "Waspada"
    assert waspada["variant"] == "warning"
    assert waspada["ratio_pct"] == 70

    kritis = classify_tdp_psu_status(275, 300)
    assert kritis["status"] == "Kritis"
    assert kritis["variant"] == "danger"
    assert kritis["ratio_pct"] == 92

    # Filter power_status & UPS Belum ditautkan di query_server_power
    res_waspada = query_server_power(filters={"power_status": "Waspada"})
    assert all(item["power_status"] == "Waspada" for item in res_waspada["items"])

    res_unlinked = query_server_power(filters={"ups_id": "Belum ditautkan"})
    assert all(item["ups_chip_label"] == "Belum ditautkan" for item in res_unlinked["items"])


def test_power_state_normalizes_backend_payload_and_ups_fallback() -> None:
    """9. Uji normalisasi payload backend: bar TDP/PSU terisi, UPS tertaut, TDP max akurat."""
    from itam_pro.states.power_state import _build_ups_fallback_lookup, _normalize_power_row

    raw_servers = [
        {
            "id_aset": "SRV-002",
            "nama_aset": "SERVER OTO RETAIL",
            "cpu": "Intel Core i7-12700 2,10 GHz Desktop",
            "vga": "Intel UHD Graphics 620 Desktop",
            "ram": "4x DDR4",
            "hdd_ssd": "3x SSD SATA, 1x SSD M.2",
            "tdp_total_w": 162,
            "psu_min_w": 250,
            "psu_rekomendasi_w": 350,
            "ups_id_aset": "",
            "ups_utilisasi_pct": 0.0,
        },
        {
            "id_aset": "SRV-004",
            "nama_aset": "SERVER OTO SDP",
            "cpu": "Intel Core i5-10600K",
            "vga": "NVIDIA GeForce GT 1030 2GB",
            "ram": "2x DDR4",
            "hdd_ssd": "3x SSD SATA",
            "tdp_total_w": 211,
            "psu_min_w": 300,
            "psu_rekomendasi_w": 400,
            "ups_id_aset": "UPS-006",
            "ups_utilisasi_pct": 54.1,
        },
    ]
    ups_items = [
        {
            "id_aset": "UPS-002",
            "kapasitas_va": 650,
            "kapasitas_watt": 390,
            "beban_perangkat": "OTOMAX RETAIL",
            "linked_server_ids": [],
            "linked_servers": [],
            "utilisasi_pct": 0.0,
        }
    ]
    fallback = _build_ups_fallback_lookup(raw_servers, ups_items)
    row_retail = _normalize_power_row(raw_servers[0], 1, fallback)
    row_sdp = _normalize_power_row(raw_servers[1], 2, fallback)

    assert row_retail["tdp_psu_ratio_pct"] == 65
    assert row_retail["tdp_psu_bar_width"] == "65%"
    assert row_retail["has_ups"] is True
    assert row_retail["ups_chip_label"] == "UPS-002 · 42%"

    assert row_sdp["power_status"] == "Waspada"
    assert row_sdp["power_status_label"] == "Waspada 70%"
    assert row_sdp["tdp_psu_bar_width"] == "70%"
    assert row_sdp["ups_chip_label"] == "UPS-006 · 54%"
