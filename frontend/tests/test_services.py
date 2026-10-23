"""
Unit Tests (pytest) untuk logika bisnis murni di lapisan services/ ITAM Pro (Tahap 6d).
Jalankan dari direktori frontend/: `pytest`
"""
from itam_pro.services.mock.ip_mock import (
    find_ip_duplicate_owner,
    get_conflict_ip_map,
    ipv4_sort_tuple,
    is_valid_ipv4,
    query_mock_ip_entries,
)
from itam_pro.services.mock.seed import (
    SEED_IDS,
    allocate_next_asset_id,
    create_mock_assets,
    delete_mock_asset,
)
from itam_pro.services.validators import validate_asset_business_rules


def test_ipv4_validation() -> None:
    """1. Uji validasi format alamat IPv4."""
    assert is_valid_ipv4("192.168.10.1") is True
    assert is_valid_ipv4("10.0.0.255") is True
    assert is_valid_ipv4("192.168.10.256") is False
    assert is_valid_ipv4("192.168.10") is False
    assert is_valid_ipv4("192.168.01.1") is False
    assert is_valid_ipv4("abc.def.ghi.jkl") is False


def test_numeric_ip_sorting() -> None:
    """2. Uji pengurutan IP secara numerik (bukan alfabetis string)."""
    ips = ["192.168.10.100", "192.168.10.2", "192.168.10.11", "192.168.2.5"]
    sorted_ips = sorted(ips, key=ipv4_sort_tuple)
    assert sorted_ips == [
        "192.168.2.5",
        "192.168.10.2",
        "192.168.10.11",
        "192.168.10.100",
    ]

    res = query_mock_ip_entries(grup="Semua", filters={}, page=1, page_size=50)
    returned_ips = [item["ip_address"] for item in res["items"]]
    assert returned_ips == sorted(returned_ips, key=ipv4_sort_tuple)


def test_ip_conflict_detection_and_distinct_physical_assets() -> None:
    """3. Uji deteksi IP bentrok dan keunikan tautan aset fisik pada ip_mock."""
    conflicts = get_conflict_ip_map()
    assert "192.168.10.25" in conflicts
    assert len(conflicts["192.168.10.25"]) == 2
    assert find_ip_duplicate_owner("192.168.10.1") == "GW-CORE-BLOK14"
    assert find_ip_duplicate_owner("192.168.10.1", exclude_id="IP-0001") is None

    # Pastikan entri Fisik menaut ke asset_id yang berbeda-beda dan GW ke Router
    res = query_mock_ip_entries(
        grup="Semua",
        filters={"jenis": "Fisik"},
        page=1,
        page_size=50,
    )
    phys_assets = [x["asset_id"] for x in res["items"] if x.get("asset_id")]
    assert len(phys_assets) == len(set(phys_assets))
    gw_entry = next(x for x in res["items"] if x["nama"] == "GW-CORE-BLOK14")
    assert gw_entry["asset_id"] == SEED_IDS["RTR_CORE_01"]


def test_asset_id_never_reused_after_delete() -> None:
    """4. Uji pembuatan id_aset otomatis dan jaminan ID tidak dipakai ulang setelah dihapus."""
    created = create_mock_assets(
        payload={
            "nama_aset": "UPS-TEST-UNIT",
            "kategori": "UPS",
            "status": "Backup",
            "digunakan_oleh": "",
        },
        count=1,
    )
    first_id = created[0]["id_aset"]
    assert delete_mock_asset(first_id) is True

    next_id = allocate_next_asset_id("UPS")
    assert next_id != first_id
    assert int(next_id.split("-")[1]) > int(first_id.split("-")[1])


def test_status_digunakan_requires_digunakan_oleh() -> None:
    """5. Uji aturan Status == 'Digunakan' mewajibkan 'Digunakan Oleh' diisi."""
    err = validate_asset_business_rules(
        {
            "nama_aset": "PC-ADMIN-01",
            "kategori": "PC",
            "status": "Digunakan",
            "digunakan_oleh": "",
        }
    )
    assert err is not None
    assert "Digunakan Oleh" in err

    ok = validate_asset_business_rules(
        {
            "nama_aset": "PC-ADMIN-01",
            "kategori": "PC",
            "status": "Digunakan",
            "digunakan_oleh": "Budi (Admin)",
        }
    )
    assert ok is None


def test_tanggal_keluar_must_be_on_or_after_tanggal_masuk() -> None:
    """6. Uji aturan Tanggal Keluar Gudang >= Tanggal Masuk Gudang."""
    err = validate_asset_business_rules(
        {
            "nama_aset": "PC-ADMIN-02",
            "kategori": "PC",
            "status": "Backup",
            "digunakan_oleh": "",
            "tanggal_masuk_gudang": "2026-10-15",
            "tanggal_keluar_gudang": "2026-10-10",
        }
    )
    assert err is not None
    assert "Tanggal Keluar" in err

    ok = validate_asset_business_rules(
        {
            "nama_aset": "PC-ADMIN-02",
            "kategori": "PC",
            "status": "Backup",
            "digunakan_oleh": "",
            "tanggal_masuk_gudang": "2026-10-15",
            "tanggal_keluar_gudang": "2026-10-15",
        }
    )
    assert ok is None
