from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def _auth_headers(session: Session, username: str, role: UserRole) -> dict[str, str]:
    user = User(
        username=username,
        full_name=f"Test {username}",
        password_hash=hash_password("password123"),
        role=role.value,
        is_active=True,
    )
    session.add(user)
    session.commit()
    token = create_access_token(user.username, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_get_master_data(client: TestClient, session: Session) -> None:
    headers = _auth_headers(session, "viewer1", UserRole.VIEWER)
    res = client.get("/api/v1/master", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "Head Office (Office Blok 14)" in data["locations"]
    assert "PC" in data["categories"]
    assert "UPS" in data["categories"]
    assert "power_supply" not in data["category_fields"]["PC"]
    assert "casing" not in data["category_fields"]["PC"]


def test_auto_generate_asset_id_and_crud(client: TestClient, session: Session) -> None:
    admin_headers = _auth_headers(session, "admin1", UserRole.ADMINISTRATOR)

    # Buat PC pertama -> PC-001
    r1 = client.post(
        "/api/v1/assets",
        headers=admin_headers,
        json={
            "nama_aset": "PC Kasir Utama",
            "kategori": "PC",
            "merek": "Rakitan",
            "serial_number": "SN-PC-1001",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Aktif",
            "processor": "Intel Core i5-12400",
            "ram": "16GB DDR4",
            "storage": "SSD NVMe 512GB",
            "watt": 250,
        },
    )
    assert r1.status_code == 201
    a1 = r1.json()
    assert a1["id_aset"] == "PC-001"
    assert a1["serial_number"] == "SN-PC-1001"
    assert "power_supply" not in a1
    assert "casing" not in a1

    # Buat PC kedua tanpa id_aset -> otomatis PC-002
    r2 = client.post(
        "/api/v1/assets",
        headers=admin_headers,
        json={
            "nama_aset": "PC Admin Gudang",
            "kategori": "PC",
            "serial_number": "-",
            "lokasi": "Office 437 (Office Blok 12)",
            "status": "Cadangan",
            "tanggal_masuk": "2026-10-15",
        },
    )
    assert r2.status_code == 201
    assert r2.json()["id_aset"] == "PC-002"
    assert r2.json()["serial_number"] == "-"
    assert r2.json()["tanggal_masuk"] == "2026-10-15"

    # Buat UPS pertama -> otomatis UPS-001
    r3 = client.post(
        "/api/v1/assets",
        headers=admin_headers,
        json={
            "nama_aset": "UPS Server Prolink",
            "kategori": "UPS",
            "merek": "Prolink",
            "model": "PRO1201SFCU",
            "serial_number": "-",
            "lokasi": "Head Office (Office Blok 14)",
            "kapasitas_va": 1200,
            "baterai": "YUASA 12V 7Ah",
            "jumlah_baterai": 2,
        },
    )
    assert r3.status_code == 201
    assert r3.json()["id_aset"] == "UPS-001"

    # Cek daftar berhalaman, tab_counts, dan summary
    list_res = client.get("/api/v1/assets", headers=admin_headers)
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["total"] == 3
    assert body["tab_counts"]["PC"] == 2
    assert body["tab_counts"]["UPS"] == 1
    assert body["summary"]["total"] == 3
    assert body["summary"]["aktif"] == 2
    assert body["summary"]["gudang"] == 1


def test_duplicate_serial_number_rejected_409(client: TestClient, session: Session) -> None:
    headers = _auth_headers(session, "member1", UserRole.MEMBER)

    res1 = client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "Monitor Dell 24",
            "kategori": "Monitor",
            "serial_number": "DL-998877",
            "lokasi": "White House (Office Blok 13)",
        },
    )
    assert res1.status_code == 201

    # Duplikat SN dengan huruf kecil harus tetap ditolak 409
    res_dup = client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "Monitor Kedua",
            "kategori": "Monitor",
            "serial_number": "dl-998877",
            "lokasi": "Mess (Mess Blok 12)",
        },
    )
    assert res_dup.status_code == 409
    assert "MON-001" in res_dup.json()["detail"]


def test_validation_rejects_invalid_category_and_location(
    client: TestClient,
    session: Session,
) -> None:
    headers = _auth_headers(session, "member2", UserRole.MEMBER)

    bad_cat = client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "Aset Aneh",
            "kategori": "Kendaraan",
            "lokasi": "Head Office (Office Blok 14)",
        },
    )
    assert bad_cat.status_code == 422

    bad_loc = client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "PC Cabang Palsu",
            "kategori": "PC",
            "lokasi": "Cabang Bandung",
        },
    )
    assert bad_loc.status_code == 422


def test_rbac_permissions_on_assets(client: TestClient, session: Session) -> None:
    admin_h = _auth_headers(session, "adm", UserRole.ADMINISTRATOR)
    member_h = _auth_headers(session, "mem", UserRole.MEMBER)
    viewer_h = _auth_headers(session, "vw", UserRole.VIEWER)

    payload = {
        "nama_aset": "Server Otomax",
        "kategori": "Server",
        "lokasi": "Head Office (Office Blok 14)",
    }

    # Viewer tidak boleh POST (403)
    assert client.post("/api/v1/assets", headers=viewer_h, json=payload).status_code == 403

    # Member boleh POST (201) dan PUT (200), tapi tidak boleh DELETE (403)
    created = client.post("/api/v1/assets", headers=member_h, json=payload)
    assert created.status_code == 201
    code = created.json()["id_aset"]

    updated = client.put(
        f"/api/v1/assets/{code}",
        headers=member_h,
        json={"nama_aset": "Server Otomax Utama"},
    )
    assert updated.status_code == 200
    assert updated.json()["nama_aset"] == "Server Otomax Utama"

    assert client.delete(f"/api/v1/assets/{code}", headers=member_h).status_code == 403

    # Administrator boleh DELETE (200)
    assert client.delete(f"/api/v1/assets/{code}", headers=admin_h).status_code == 200
    assert client.get(f"/api/v1/assets/{code}", headers=viewer_h).status_code == 404

