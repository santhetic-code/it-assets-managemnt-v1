"""Pengujian unit untuk modul Rekap Watt Server & UPS (Tahap B4)."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def _auth_headers(session: Session, username: str, role: UserRole) -> dict[str, str]:
    user = User(
        username=username,
        full_name=f"User {username}",
        password_hash=hash_password("password123"),
        role=role.value,
        is_active=True,
    )
    session.add(user)
    session.commit()
    token = create_access_token(user.username, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_watt_server_derived_from_assets_and_calculations(
    client: TestClient,
    session: Session,
) -> None:
    headers = _auth_headers(session, "admin_pwr", UserRole.ADMINISTRATOR)

    # 1. Buat 2 Server Aktif (400W dan 200W) dan 1 Server Cadangan (350W)
    client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "Server Otomax Utama",
            "kategori": "Server",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Aktif",
            "processor": "Intel Xeon E-2388G",
            "ram": "32GB ECC",
            "storage": "NVMe 1TB",
            "watt": 400,
        },
    )
    client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "Server Accurate DB",
            "kategori": "Server",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Aktif",
            "processor": "Intel Core i7-12700",
            "ram": "16GB",
            "storage": "SSD 512GB",
            "watt": 200,
        },
    )
    client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "Server Backup Lama",
            "kategori": "Server",
            "lokasi": "White House (Office Blok 13)",
            "status": "Cadangan",
            "watt": 350,
        },
    )

    # 2. Buat 1 unit UPS Prolink 1200VA (kapasitas_watt otomatis = 1200 * 0.6 = 720W)
    client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "UPS Prolink Server",
            "kategori": "UPS",
            "merek": "Prolink",
            "model": "PRO1201SFCU",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Aktif",
            "kapasitas_va": 1200,
            "baterai": "YUASA 12V 7Ah",
            "jumlah_baterai": 2,
            "beban_perangkat": "SRV-001, SRV-002",
        },
    )

    # 3. Ambil Rekap Watt Server
    res = client.get("/api/v1/watt-server", headers=headers)
    assert res.status_code == 200
    body = res.json()

    assert body["total"] == 3
    summary = body["summary"]
    assert summary["total_server"] == 3
    assert summary["server_aktif"] == 2
    # Hanya server aktif yang dihitung ke total_watt aktif (400 + 200 = 600W)
    assert summary["total_watt"] == 600
    assert summary["rata_rata_watt"] == 300
    # kWh per hari = (600 * 24) / 1000 = 14.4 kWh
    assert summary["estimasi_kwh_hari"] == 14.4
    # kWh per bulan = 14.4 * 30 = 432.0 kWh
    assert summary["estimasi_kwh_bulan"] == 432.0

    # Kapasitas UPS = 1200 VA -> 720 W efektif -> Beban = 600 / 720 = 83.3% (Waspada)
    assert summary["total_ups"] == 1
    assert summary["total_va_ups"] == 1200
    assert summary["total_kapasitas_watt_ups"] == 720
    assert summary["persentase_beban_ups"] == 83.3
    assert summary["status_beban_ups"] == "Waspada"


def test_patch_power_updates_underlying_asset_and_rbac(
    client: TestClient,
    session: Session,
) -> None:
    member_h = _auth_headers(session, "mem_pwr", UserRole.MEMBER)
    viewer_h = _auth_headers(session, "vw_pwr", UserRole.VIEWER)

    create_res = client.post(
        "/api/v1/assets",
        headers=member_h,
        json={
            "nama_aset": "Server Zabbix",
            "kategori": "Server",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Aktif",
            "watt": 150,
        },
    )
    code = create_res.json()["id_aset"]

    # Viewer ditolak saat mengubah watt (403)
    denied = client.patch(
        f"/api/v1/watt-server/{code}",
        headers=viewer_h,
        json={"watt": 250},
    )
    assert denied.status_code == 403

    # Member berhasil mengubah watt melalui endpoint watt-server
    patched = client.patch(
        f"/api/v1/watt-server/{code}",
        headers=member_h,
        json={"watt": 250, "beban_perangkat": "UPS-001"},
    )
    assert patched.status_code == 200
    assert patched.json()["watt"] == 250

    # Pastikan data di /api/v1/assets/{code} ikut berubah (single source of truth)
    asset_res = client.get(f"/api/v1/assets/{code}", headers=viewer_h)
    assert asset_res.status_code == 200
    assert asset_res.json()["watt"] == 250
    assert asset_res.json()["beban_perangkat"] == "UPS-001"
