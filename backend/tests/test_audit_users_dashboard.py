from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def _create_user_and_headers(
    session: Session,
    username: str,
    role: UserRole,
    password: str = "password123",
) -> dict[str, str]:
    user = User(
        username=username,
        full_name=f"User {username.capitalize()}",
        password_hash=hash_password(password),
        role=role.value,
        is_active=True,
    )
    session.add(user)
    session.commit()
    token = create_access_token(user.username, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_user_management_crud_and_last_admin_protection(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _create_user_and_headers(session, "admin_main", UserRole.ADMINISTRATOR)

    # 1. Buat user Member baru
    r_create = client.post(
        "/api/v1/users",
        headers=admin_h,
        json={
            "username": "staf_it",
            "full_name": "Staf IT Support",
            "password": "password123",
            "role": "Member",
        },
    )
    assert r_create.status_code == 201
    u_data = r_create.json()
    assert u_data["username"] == "staf_it"
    assert u_data["role"] == "Member"
    assert u_data["status"] == "Aktif"

    # 2. Duplikat username ditolak 409
    r_dup = client.post(
        "/api/v1/users",
        headers=admin_h,
        json={
            "username": "STAF_IT",
            "full_name": "Duplikat",
            "password": "password123",
            "role": "Viewer",
        },
    )
    assert r_dup.status_code == 409

    # 3. Satu-satunya Administrator aktif tidak boleh menghapus atau menonaktifkan dirinya sendiri
    assert client.delete("/api/v1/users/admin_main", headers=admin_h).status_code == 400
    assert (
        client.patch(
            "/api/v1/users/admin_main",
            headers=admin_h,
            json={"is_active": False},
        ).status_code
        == 400
    )

    # 4. Reset password user oleh Admin & uji login dengan password baru
    r_reset = client.post(
        "/api/v1/users/staf_it/reset-password",
        headers=admin_h,
        json={"new_password": "PasswordBaru2026!"},
    )
    assert r_reset.status_code == 200

    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "staf_it", "password": "PasswordBaru2026!"},
    )
    assert login_res.status_code == 200


def test_audit_log_auto_recorded_and_sanitized(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _create_user_and_headers(session, "admin_aud", UserRole.ADMINISTRATOR)

    # Buat kredensial lalu lakukan reveal -> harus otomatis tercatat di Audit Log
    crd = client.post(
        "/api/v1/credentials",
        headers=admin_h,
        json={
            "nama_layanan": "Router MikroTik Utama",
            "jenis_kredensial": "MikroTik",
            "username": "admin",
            "password": "RahasiaRouterJanganBocor",
        },
    )
    crd_code = crd.json()["kode_kredensial"]
    client.post(f"/api/v1/credentials/{crd_code}/reveal", headers=admin_h)

    # Cek daftar Audit Log
    aud_res = client.get("/api/v1/audit-logs", headers=admin_h)
    assert aud_res.status_code == 200
    aud_body = aud_res.json()
    assert aud_body["total"] >= 1
    assert aud_body["summary"]["akses_kredensial"] >= 1
    assert "RahasiaRouterJanganBocor" not in aud_res.text


def test_dashboard_real_aggregation(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _create_user_and_headers(session, "admin_dash", UserRole.ADMINISTRATOR)

    # Tambahkan sampel aset, IP, dan pembelian
    client.post(
        "/api/v1/assets",
        headers=admin_h,
        json={
            "nama_aset": "Server Utama",
            "kategori": "Server",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Aktif",
            "watt": 350,
        },
    )
    client.post(
        "/api/v1/ip-allocations",
        headers=admin_h,
        json={
            "ip_address": "192.168.1.10",
            "nama_perangkat": "Server Utama",
            "tipe": "Fisik",
            "status": "Aktif",
        },
    )
    client.post(
        "/api/v1/purchases",
        headers=admin_h,
        json={
            "nama_item": "SSD NVMe 1TB",
            "kategori": "Server",
            "jumlah": 2,
            "harga_satuan": 1500000,
            "status": "Lunas",
        },
    )

    dash_res = client.get("/api/v1/dashboard", headers=admin_h)
    assert dash_res.status_code == 200
    dash = dash_res.json()

    assert dash["kpi"]["total_aset"] == 1
    assert dash["kpi"]["total_ip"] == 1
    assert dash["kpi"]["total_watt"] == 350
    assert dash["kpi"]["total_pengeluaran"] == 3000000
    assert len(dash["asset_by_location"]) >= 5
