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


def test_ip_numeric_sorting(client: TestClient, session: Session) -> None:
    headers = _auth_headers(session, "admin_ip", UserRole.ADMINISTRATOR)

    # Masukkan IP secara acak (jika urut string, .100 dan .10 akan muncul sebelum .2)
    for ip, name in [
        ("192.168.1.100", "PC-Seratus"),
        ("192.168.1.2", "Router-Gateway"),
        ("192.168.1.10", "Server-Sepuluh"),
        ("10.0.0.5", "MikroTik-Core"),
    ]:
        res = client.post(
            "/api/v1/ip-allocations",
            headers=headers,
            json={
                "ip_address": ip,
                "nama_perangkat": name,
                "tipe": "Fisik",
                "lokasi": "Head Office (Office Blok 14)",
            },
        )
        assert res.status_code == 201

    list_res = client.get("/api/v1/ip-allocations", headers=headers)
    assert list_res.status_code == 200
    returned_ips = [item["ip_address"] for item in list_res.json()["items"]]
    assert returned_ips == [
        "10.0.0.5",
        "192.168.1.2",
        "192.168.1.10",
        "192.168.1.100",
    ]


def test_ip_conflict_rejected_409_unless_bebas(client: TestClient, session: Session) -> None:
    headers = _auth_headers(session, "member_ip", UserRole.MEMBER)

    r1 = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.10.25",
            "nama_perangkat": "Server Otomax Utama",
            "tipe": "Fisik",
            "status": "Aktif",
        },
    )
    assert r1.status_code == 201

    # Duplikat IP aktif harus ditolak 409 Conflict
    r_dup = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.10.25",
            "nama_perangkat": "PC Duplikat",
            "tipe": "Fisik",
            "status": "Aktif",
        },
    )
    assert r_dup.status_code == 409
    assert "192.168.10.25" in r_dup.json()["detail"]

    # Jika diubah menjadi Bebas, maka IP tersebut boleh dipakai perangkat baru
    item_id = r1.json()["id"]
    client.patch(
        f"/api/v1/ip-allocations/{item_id}",
        headers=headers,
        json={"status": "Bebas"},
    )
    r_reuse = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.10.25",
            "nama_perangkat": "Server Pengganti",
            "tipe": "Fisik",
            "status": "Aktif",
        },
    )
    assert r_reuse.status_code == 201


def test_vm_without_host_rejected_and_orphan_detection(
    client: TestClient,
    session: Session,
) -> None:
    headers = _auth_headers(session, "admin_vm", UserRole.ADMINISTRATOR)

    # 1. Buat VM tanpa host_name maupun id_aset_host -> ditolak 422
    no_host = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.20.11",
            "nama_perangkat": "VM-Tanpa-Induk",
            "tipe": "VM",
            "is_vm": True,
        },
    )
    assert no_host.status_code == 422

    # 2. Buat VM dengan id_aset_host yang tidak ada di tabel assets -> ditolak 422
    ghost_host = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.20.12",
            "nama_perangkat": "VM-Host-Palsu",
            "tipe": "VM",
            "id_aset_host": "SRV-999",
        },
    )
    assert ghost_host.status_code == 422

    # 3. Buat aset Server fisik terlebih dahulu -> SRV-001
    srv = client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "Server Proxmox Node 1",
            "kategori": "Server",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Aktif",
            "watt": 450,
        },
    )
    assert srv.status_code == 201
    srv_code = srv.json()["id_aset"]

    # 4. Buat VM yang menempel ke SRV-001 -> sukses (201) dan bukan orphan
    vm_ok = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.20.15",
            "nama_perangkat": "VM-Zabbix-Monitoring",
            "tipe": "VM",
            "id_aset_host": srv_code,
            "os": "Ubuntu 24.04",
            "vcpu": 4,
            "ram": "8GB",
        },
    )
    assert vm_ok.status_code == 201
    assert vm_ok.json()["vm_tanpa_host"] is False
    assert vm_ok.json()["host_name"] == "Server Proxmox Node 1"

    # 5. Jika aset SRV-001 diubah statusnya jadi Rusak,
    # maka VM otomatis terdeteksi sebagai VM Tanpa Host (orphan)
    client.patch(
        f"/api/v1/assets/{srv_code}",
        headers=headers,
        json={"status": "Rusak"},
    )
    list_res = client.get("/api/v1/ip-allocations?orphan_only=true", headers=headers)
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["total"] == 1
    assert body["items"][0]["nama_perangkat"] == "VM-Zabbix-Monitoring"
    assert body["items"][0]["vm_tanpa_host"] is True
    assert body["summary"]["vm_tanpa_host"] == 1


def test_invalid_ipv4_rejected_422_and_rbac(client: TestClient, session: Session) -> None:
    viewer_h = _auth_headers(session, "vw_ip", UserRole.VIEWER)
    member_h = _auth_headers(session, "mem_ip", UserRole.MEMBER)

    bad_ip = client.post(
        "/api/v1/ip-allocations",
        headers=member_h,
        json={
            "ip_address": "999.168.1.1",
            "nama_perangkat": "Perangkat Salah IP",
        },
    )
    assert bad_ip.status_code == 422

    # Viewer ditolak saat membuat atau menghapus IP
    denied = client.post(
        "/api/v1/ip-allocations",
        headers=viewer_h,
        json={
            "ip_address": "192.168.1.50",
            "nama_perangkat": "PC Viewer",
        },
    )
    assert denied.status_code == 403
