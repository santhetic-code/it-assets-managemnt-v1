from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.security import (
    MASKED_SECRET_DISPLAY,
    create_access_token,
    decrypt_secret,
    encrypt_secret,
    hash_password,
)
from app.models.credential import Credential
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


def test_fernet_encryption_roundtrip_and_db_storage(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _auth_headers(session, "admin_crd", UserRole.ADMINISTRATOR)

    # Uji langsung helper Fernet
    cipher = encrypt_secret("SuperSecret#2026")
    assert cipher != "SuperSecret#2026"
    assert cipher.startswith("gAAAAA")
    assert decrypt_secret(cipher) == "SuperSecret#2026"

    # Buat kredensial melalui API
    res = client.post(
        "/api/v1/credentials",
        headers=admin_h,
        json={
            "nama_layanan": "MikroTik Core Router RB4011",
            "jenis_kredensial": "MikroTik",
            "lokasi": "Head Office (Office Blok 14)",
            "ip_address": "192.168.1.1",
            "port": 8291,
            "username": "admin_net",
            "password": "WinBoxPassword!99",
            "secret_extra": "SSH-Passphrase-77",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["kode_kredensial"] == "CRD-001"
    # Respons pembuatan/daftar tidak boleh menampilkan plaintext password
    assert body["password"] == MASKED_SECRET_DISPLAY
    assert "WinBoxPassword!99" not in res.text
    assert "SSH-Passphrase-77" not in res.text

    # Pastikan di dalam tabel database tersimpan sebagai ciphertext Fernet
    db_row = session.exec(
        select(Credential).where(Credential.kode_kredensial == "CRD-001")
    ).one()
    assert db_row.password_encrypted != "WinBoxPassword!99"
    assert db_row.password_encrypted.startswith("gAAAAA")
    assert decrypt_secret(db_row.password_encrypted) == "WinBoxPassword!99"


def test_credential_reveal_and_per_type_permissions(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _auth_headers(session, "adm_c", UserRole.ADMINISTRATOR)
    member_h = _auth_headers(session, "mem_c", UserRole.MEMBER)
    viewer_h = _auth_headers(session, "vw_c", UserRole.VIEWER)

    # 1. Administrator membuat kredensial Server (khusus Admin) -> CRD-001
    r_srv = client.post(
        "/api/v1/credentials",
        headers=admin_h,
        json={
            "nama_layanan": "Server Proxmox Utama",
            "jenis_kredensial": "Server",
            "ip_address": "192.168.20.1",
            "username": "root",
            "password": "RootServerPassword#1",
        },
    )
    assert r_srv.status_code == 201
    srv_code = r_srv.json()["kode_kredensial"]

    # 2. Member mencoba membuat kredensial Database (khusus Admin) -> ditolak 403
    r_denied_create = client.post(
        "/api/v1/credentials",
        headers=member_h,
        json={
            "nama_layanan": "PostgreSQL Production",
            "jenis_kredensial": "Database",
            "username": "postgres",
            "password": "DbSecretPassword",
        },
    )
    assert r_denied_create.status_code == 403

    # 3. Member membuat kredensial operasional CCTV -> diizinkan (201) -> CRD-002
    r_cctv = client.post(
        "/api/v1/credentials",
        headers=member_h,
        json={
            "nama_layanan": "CCTV Dahua Lobby Head Office",
            "jenis_kredensial": "CCTV",
            "ip_address": "192.168.30.15",
            "username": "admin",
            "password": "CctvStreamPassword#25",
        },
    )
    assert r_cctv.status_code == 201
    cctv_code = r_cctv.json()["kode_kredensial"]

    # 4. Uji Reveal oleh Administrator: boleh reveal Server (200) maupun CCTV (200)
    rev_admin_srv = client.post(
        f"/api/v1/credentials/{srv_code}/reveal",
        headers=admin_h,
    )
    assert rev_admin_srv.status_code == 200
    assert rev_admin_srv.json()["password"] == "RootServerPassword#1"

    rev_admin_cctv = client.post(
        f"/api/v1/credentials/{cctv_code}/reveal",
        headers=admin_h,
    )
    assert rev_admin_cctv.status_code == 200
    assert rev_admin_cctv.json()["password"] == "CctvStreamPassword#25"

    # 5. Uji Reveal oleh Member: boleh reveal CCTV (200), tetapi ditolak reveal Server (403)
    rev_mem_cctv = client.post(
        f"/api/v1/credentials/{cctv_code}/reveal",
        headers=member_h,
    )
    assert rev_mem_cctv.status_code == 200
    assert rev_mem_cctv.json()["password"] == "CctvStreamPassword#25"

    rev_mem_srv = client.post(
        f"/api/v1/credentials/{srv_code}/reveal",
        headers=member_h,
    )
    assert rev_mem_srv.status_code == 403

    # 6. Uji Reveal oleh Viewer: ditolak (403) baik untuk CCTV maupun Server
    assert (
        client.post(f"/api/v1/credentials/{cctv_code}/reveal", headers=viewer_h).status_code
        == 403
    )
    assert (
        client.post(f"/api/v1/credentials/{srv_code}/reveal", headers=viewer_h).status_code
        == 403
    )


def test_credential_update_preserves_or_rotates_secret_and_delete_rbac(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _auth_headers(session, "adm_u", UserRole.ADMINISTRATOR)
    member_h = _auth_headers(session, "mem_u", UserRole.MEMBER)

    res = client.post(
        "/api/v1/credentials",
        headers=member_h,
        json={
            "nama_layanan": "WiFi Tamu Office 437",
            "jenis_kredensial": "WiFi",
            "lokasi": "Office 437 (Office Blok 12)",
            "username": "SSID-XML-Guest",
            "password": "WifiPasswordLama",
        },
    )
    code = res.json()["kode_kredensial"]

    # Update nama_layanan tanpa mengirim password baru -> password lama tetap utuh
    client.patch(
        f"/api/v1/credentials/{code}",
        headers=member_h,
        json={"nama_layanan": "WiFi Utama Office 437"},
    )
    rev1 = client.post(f"/api/v1/credentials/{code}/reveal", headers=member_h)
    assert rev1.json()["password"] == "WifiPasswordLama"

    # Update password baru -> terenkripsi ulang dan hasil reveal berubah
    client.patch(
        f"/api/v1/credentials/{code}",
        headers=member_h,
        json={"password": "WifiPasswordBaru2026!"},
    )
    rev2 = client.post(f"/api/v1/credentials/{code}/reveal", headers=member_h)
    assert rev2.json()["password"] == "WifiPasswordBaru2026!"

    # Member tidak boleh DELETE (403), Administrator boleh DELETE (200)
    assert client.delete(f"/api/v1/credentials/{code}", headers=member_h).status_code == 403
    assert client.delete(f"/api/v1/credentials/{code}", headers=admin_h).status_code == 200

