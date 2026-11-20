from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlmodel import Session, col

from app.core.security import create_access_token, hash_password
from app.models.audit import AuditLog, AuditLogImmutableError
from app.models.user import User, UserRole
from app.schemas.audit import (
    compute_audit_severity,
    delete_audit_log,
    format_audit_timestamps,
    record_audit_log,
    update_audit_log,
)


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


def test_audit_severity_mapping_and_wib_timezone() -> None:
    assert compute_audit_severity("login_gagal") == "Peringatan"
    assert compute_audit_severity("akun_terkunci") == "Peringatan"
    assert compute_audit_severity("reveal_ditolak") == "Peringatan"
    assert compute_audit_severity("hak_ditolak") == "Peringatan"

    assert compute_audit_severity("reveal") == "Penting"
    assert compute_audit_severity("password_direset") == "Penting"
    assert compute_audit_severity("password_diubah") == "Penting"
    assert compute_audit_severity("peran_diubah") == "Penting"
    assert compute_audit_severity("pengguna_dibuat") == "Penting"
    assert compute_audit_severity("pengguna_dinonaktifkan") == "Penting"
    assert compute_audit_severity("pengguna_diaktifkan") == "Penting"
    assert compute_audit_severity("aset_dihapus") == "Penting"
    assert compute_audit_severity("kredensial_diarsipkan") == "Penting"
    assert compute_audit_severity("audit_diekspor") == "Penting"

    assert compute_audit_severity("Login") == "Info"
    assert compute_audit_severity("Aset diubah") == "Info"

    # UTC 2026-11-18 21:29 -> WIB 19 Nov 2026 04:29 WIB
    ts = format_audit_timestamps(datetime(2026, 11, 18, 21, 29, tzinfo=UTC))
    assert ts["tanggal_wib"] == "19 Nov 2026"
    assert ts["jam_wib"] == "04:29 WIB"


def test_audit_admin_only_access_control(client: TestClient, session: Session) -> None:
    _create_user_and_headers(session, "admin_acl", UserRole.ADMINISTRATOR)
    member_h = _create_user_and_headers(session, "member_acl", UserRole.MEMBER)
    viewer_h = _create_user_and_headers(session, "viewer_acl", UserRole.VIEWER)

    assert client.get("/api/v1/audit-logs").status_code == 401
    assert client.get("/api/v1/audit-logs", headers=member_h).status_code == 403
    assert client.get("/api/v1/audit-logs", headers=viewer_h).status_code == 403
    assert client.get("/api/v1/audit-logs/export", headers=member_h).status_code == 403
    assert client.get("/api/v1/audit-logs/export", headers=viewer_h).status_code == 403


def test_audit_grouping_60s_not_across_actor_or_target(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _create_user_and_headers(session, "admin_grp", UserRole.ADMINISTRATOR)
    base_time = datetime(2026, 11, 19, 1, 0, 0, tzinfo=UTC)

    # 3 kejadian identik dalam 45 detik -> harus tergabung x3
    for offset in (0, 20, 45):
        r = record_audit_log(
            session,
            username="admin_grp",
            nama_pengguna="Admin",
            role="Administrator",
            aksi="reveal",
            modul="Kredensial",
            target_id="CRD-001",
            detail="Reveal password",
        )
        session.execute(
            update(AuditLog)
            .where(col(AuditLog.id) == r.id)
            .values(created_at=base_time + timedelta(seconds=offset))
        )
    # Pelaku berbeda dalam 60 detik -> TIDAK boleh digabung
    r_other_actor = record_audit_log(
        session,
        username="staf_lain",
        nama_pengguna="Staf Lain",
        role="Member",
        aksi="reveal",
        modul="Kredensial",
        target_id="CRD-001",
        detail="Reveal password",
    )
    session.execute(
        update(AuditLog)
        .where(col(AuditLog.id) == r_other_actor.id)
        .values(created_at=base_time + timedelta(seconds=10))
    )
    # Target berbeda dalam 60 detik -> TIDAK boleh digabung
    r_other_target = record_audit_log(
        session,
        username="admin_grp",
        nama_pengguna="Admin",
        role="Administrator",
        aksi="reveal",
        modul="Kredensial",
        target_id="CRD-002",
        detail="Reveal password",
    )
    session.execute(
        update(AuditLog)
        .where(col(AuditLog.id) == r_other_target.id)
        .values(created_at=base_time + timedelta(seconds=15))
    )
    session.commit()

    res = client.get("/api/v1/audit-logs", headers=admin_h)
    assert res.status_code == 200
    body = res.json()
    assert body["raw_total"] == 5
    assert body["total"] == 3
    grp_item = next(
        i
        for i in body["items"]
        if i["username"] == "admin_grp" and i["target_id"] == "CRD-001"
    )
    assert grp_item["group_count"] == 3
    assert len(grp_item["grouped_timestamps"]) == 3


def test_audit_sensitive_fields_masked_and_append_only(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _create_user_and_headers(session, "admin_imm", UserRole.ADMINISTRATOR)

    row = record_audit_log(
        session,
        username="admin_imm",
        role="Administrator",
        aksi="Aset diubah",
        modul="Aset",
        target_id="PC-0012",
        detail="password=RahasiaSuper123 token=TokXYZ999",
        changes=[
            {"field": "Lokasi", "before": "Kantor Blok 12", "after": "Kantor Blok 14"},
            {"field": "api_key", "before": "sk-lama-999", "after": "sk-baru-888"},
            {"field": "nilai_kredensial", "before": "PassLama!", "after": "PassBaru!"},
        ],
    )
    res = client.get(f"/api/v1/audit-logs/{row.kode_audit}", headers=admin_h)
    assert res.status_code == 200
    assert "RahasiaSuper123" not in res.text
    assert "TokXYZ999" not in res.text
    assert "sk-lama-999" not in res.text
    assert "PassBaru!" not in res.text
    changes_by_field = {c["field"]: c for c in res.json()["changes"]}
    assert changes_by_field["api_key"]["after"] == "(disembunyikan)"
    assert changes_by_field["Lokasi"]["after"] == "Kantor Blok 14"

    # Append-only di HTTP, service, dan ORM
    assert (
        client.delete(f"/api/v1/audit-logs/{row.kode_audit}", headers=admin_h).status_code
        == 405
    )
    assert (
        client.put(
            f"/api/v1/audit-logs/{row.kode_audit}", headers=admin_h, json={}
        ).status_code
        == 405
    )
    with pytest.raises(AuditLogImmutableError):
        update_audit_log(session, row.id)
    with pytest.raises(AuditLogImmutableError):
        delete_audit_log(session, row.id)

    row.detail = "diubah paksa"
    session.add(row)
    with pytest.raises(AuditLogImmutableError):
        session.commit()
    session.rollback()

    session.delete(row)
    with pytest.raises(AuditLogImmutableError):
        session.commit()
    session.rollback()


def test_audit_client_origin_headers_and_export_anti_csv_injection(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _create_user_and_headers(session, "admin_exp", UserRole.ADMINISTRATOR)

    # 1. Uji penerusan IP & UA klien (tidak menyimpan 172.x atau python-httpx)
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_exp", "password": "password123"},
        headers={
            "X-Client-IP": "10.20.5.41",
            "X-Client-UA": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36"
            ),
            "User-Agent": "python-httpx/0.28.1",
        },
    )
    assert login_res.status_code == 200

    # 2. Masukkan entri dengan formula berbahaya untuk uji anti CSV-injection
    record_audit_log(
        session,
        username="admin_exp",
        role="Administrator",
        aksi="Aset diubah",
        modul="Aset",
        target_id="=CMD|'/C calc'!A0",
        detail="+SUM(A1:A2)",
    )

    # 3. Filter hide_login_success=true harus menyembunyikan Login berhasil
    res_filtered = client.get(
        "/api/v1/audit-logs?hide_login_success=true&modul=Aset",
        headers=admin_h,
    )
    assert res_filtered.status_code == 200
    assert all(i["aksi"] != "Login" for i in res_filtered.json()["items"])

    # Cek IP & UA pada log login
    res_all = client.get("/api/v1/audit-logs", headers=admin_h)
    login_item = next(i for i in res_all.json()["items"] if i["aksi"] == "Login")
    assert login_item["ip_address"] == "10.20.5.41"
    assert "172." not in login_item["ip_address"]
    assert "python-httpx" not in login_item["user_agent"]
    assert login_item["perangkat"] == "Chrome 130 · Windows 11"

    # 4. Export CSV anti-injection + otomatis mencatat audit_diekspor
    exp_res = client.get("/api/v1/audit-logs/export?modul=Aset", headers=admin_h)
    assert exp_res.status_code == 200
    csv_text = exp_res.content.decode("utf-8-sig")
    assert "'=CMD|'/C calc'!A0" in csv_text
    assert "'+SUM(A1:A2)" in csv_text

    res_after = client.get("/api/v1/audit-logs?tingkat=Penting", headers=admin_h)
    assert any(i["aksi"] == "audit_diekspor" for i in res_after.json()["items"])
