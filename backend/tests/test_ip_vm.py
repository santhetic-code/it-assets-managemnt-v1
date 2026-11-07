import io

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import create_access_token, hash_password
from app.models.asset import Asset
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

    # Masukkan IP secara acak di subnet terdaftar 192.168.1.0/24
    for ip, name in [
        ("192.168.1.100", "PC-Seratus"),
        ("192.168.1.2", "Router-Gateway"),
        ("192.168.1.10", "Server-Sepuluh"),
        ("192.168.1.20", "Switch-DuaPuluh"),
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

    # B4: IP di luar subnet terdaftar (192.168.1.0/24) harus ditolak
    out_of_subnet = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "10.0.0.5",
            "nama_perangkat": "MikroTik-Luar-Subnet",
            "tipe": "Fisik",
            "lokasi": "Head Office (Office Blok 14)",
        },
    )
    assert out_of_subnet.status_code == 422
    assert "di luar subnet terdaftar" in out_of_subnet.json()["detail"]

    list_res = client.get("/api/v1/ip-allocations", headers=headers)
    assert list_res.status_code == 200
    returned_ips = [item["ip_address"] for item in list_res.json()["items"]]
    assert returned_ips == [
        "192.168.1.2",
        "192.168.1.10",
        "192.168.1.20",
        "192.168.1.100",
    ]


def test_ip_conflict_rejected_409_unless_bebas(client: TestClient, session: Session) -> None:
    headers = _auth_headers(session, "editor_ip", UserRole.MEMBER)

    first = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.1.25",
            "nama_perangkat": "Server-Alpha",
            "status": "Aktif",
            "lokasi": "Head Office (Office Blok 14)",
        },
    )
    assert first.status_code == 201

    # Percobaan kedua dengan IP yang sama harus ditolak (409 Conflict)
    duplicate = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.1.25",
            "nama_perangkat": "Server-Beta",
            "status": "Aktif",
            "lokasi": "Head Office (Office Blok 14)",
        },
    )
    assert duplicate.status_code == 409
    assert "sudah digunakan" in duplicate.json()["detail"]


def test_vm_without_host_rejected_and_orphan_detection(
    client: TestClient, session: Session
) -> None:
    headers = _auth_headers(session, "admin_vm", UserRole.ADMINISTRATOR)

    # 1. Buat Server Fisik Host terlebih dahulu
    host_server = Asset(
        id_aset="SRV-0001",
        nama_aset="Host Utama Proxmox",
        kategori="Server",
        status="Digunakan",
        lokasi="Server Room HO",
    )
    session.add(host_server)
    session.commit()

    # 2. Buat VM dengan host valid -> Berhasil
    vm_ok = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.1.200",
            "nama_perangkat": "VM-Postgres-Primary",
            "is_vm": True,
            "id_aset_host": "SRV-0001",
            "lokasi": "Head Office (Office Blok 14)",
        },
    )
    assert vm_ok.status_code == 201
    vm_data = vm_ok.json()
    assert vm_data["is_vm"] is True
    assert vm_data["id_aset_host"] == "SRV-0001"
    assert vm_data["host_name"] == "Host Utama Proxmox"

    # 3. Buat VM tanpa host -> Ditolak
    vm_no_host = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.1.201",
            "nama_perangkat": "VM-Tanpa-Induk",
            "is_vm": True,
            "lokasi": "Head Office (Office Blok 14)",
        },
    )
    assert vm_no_host.status_code == 422

    # 4. Deteksi orphan jika server host dinonaktifkan
    host_server.status = "Nonaktif"
    session.add(host_server)
    session.commit()

    list_res = client.get("/api/v1/ip-allocations", headers=headers)
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["summary"]["vm_tanpa_host"] == 1

    # 5. Filter tab/query only_orphan_vm
    orphan_res = client.get("/api/v1/ip-allocations?only_orphan_vm=true", headers=headers)
    assert orphan_res.status_code == 200
    orphan_items = orphan_res.json()["items"]
    assert len(orphan_items) == 1
    assert orphan_items[0]["id_aset_host"] == "SRV-0001"


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


def test_ip_import_template_and_export_xlsx_and_pdf(client: TestClient, session: Session) -> None:
    headers = _auth_headers(session, "admin_exp", UserRole.ADMINISTRATOR)

    # 1. Download template
    tpl_res = client.get("/api/v1/ip-allocations/import-template", headers=headers)
    assert tpl_res.status_code == 200
    assert "spreadsheetml" in tpl_res.headers["Content-Type"]
    assert len(tpl_res.content) > 100

    # 2. Export Excel (.xlsx)
    exp_xlsx = client.get("/api/v1/ip-allocations/export?format=xlsx", headers=headers)
    assert exp_xlsx.status_code == 200
    assert "spreadsheetml" in exp_xlsx.headers["Content-Type"]
    assert len(exp_xlsx.content) > 100

    # 3. Export PDF
    exp_pdf = client.get("/api/v1/ip-allocations/export?format=pdf", headers=headers)
    assert exp_pdf.status_code == 200
    assert exp_pdf.headers["Content-Type"] == "application/pdf"
    assert exp_pdf.content.startswith(b"%PDF-1.4")


def test_ip_import_preview_and_commit(client: TestClient, session: Session) -> None:
    headers = _auth_headers(session, "admin_imp", UserRole.ADMINISTRATOR)

    # Buat server fisik aktif untuk host VM
    srv = Asset(
        id_aset="SRV-0002",
        nama_aset="Host Backup Proxmox",
        kategori="Server",
        status="Digunakan",
        lokasi="Server Room HO",
    )
    session.add(srv)
    session.commit()

    csv_data = (
        "IP Address,Nama Server/VM,Jenis,Host Server,Status,Fungsi,OS,Keterangan\n"
        "192.168.1.55,PC Kasir 1,Fisik,,Aktif,Kasir Toko,Windows 11,\n"
        "192.168.1.56,VM Backup Node,VM,SRV-0002,Aktif,Node Proxmox,Ubuntu 24.04,Test ket\n"
    )

    # 1. Preview
    files = {"file": ("data.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    prev_res = client.post("/api/v1/ip-allocations/import-preview", headers=headers, files=files)
    assert prev_res.status_code == 200
    prev_body = prev_res.json()
    assert prev_body["valid_count"] == 2
    assert prev_body["error_count"] == 0

    # 2. Commit
    commit_res = client.post(
        "/api/v1/ip-allocations/import-commit",
        headers=headers,
        json={"valid_rows": prev_body["valid_rows"]},
    )
    assert commit_res.status_code == 200
    assert commit_res.json()["imported_count"] == 2

    # 3. Verify in database
    list_res = client.get("/api/v1/ip-allocations", headers=headers)
    ips = [it["ip_address"] for it in list_res.json()["items"]]
    assert "192.168.1.55" in ips
    assert "192.168.1.56" in ips


def test_ip_import_skip_update_and_rollback_on_failure(
    client: TestClient, session: Session
) -> None:
    """A1.6: Uji 2 baris valid (mode skip & update tanpa ip_int) dan rollback saat gagal."""
    headers = _auth_headers(session, "admin_a1", UserRole.ADMINISTRATOR)

    csv_data = (
        "IP Address,Nama Server/VM,Jenis,Host Server,Status,Fungsi,OS,Keterangan\n"
        "192.168.1.61,PC Finance 1,Fisik,,Aktif,Operasional Akuntansi,Windows 11,\n"
        "192.168.1.62,PC Finance 2,Fisik,,Aktif,Operasional Pajak,Windows 11,NIC sering putus\n"
    )
    files = {"file": ("import_a1.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    prev_res = client.post("/api/v1/ip-allocations/import-preview", headers=headers, files=files)
    assert prev_res.status_code == 200
    valid_rows = prev_res.json()["valid_rows"]
    assert len(valid_rows) == 2

    # Hapus ip_int dari payload client untuk memastikan server menghitung ulang ip_int sendiri
    client_rows = [{k: v for k, v in r.items() if k != "ip_int"} for r in valid_rows]

    # 1. Commit mode "skip" (Lewati)
    commit_skip = client.post(
        "/api/v1/ip-allocations/import-commit",
        headers=headers,
        json={"valid_rows": client_rows, "duplicate_mode": "skip"},
    )
    assert commit_skip.status_code == 200
    assert commit_skip.json()["imported_count"] == 2

    # Ulangi commit mode "skip" -> keduanya dilewati
    commit_skip_again = client.post(
        "/api/v1/ip-allocations/import-commit",
        headers=headers,
        json={"valid_rows": client_rows, "duplicate_mode": "skip"},
    )
    assert commit_skip_again.status_code == 200
    assert commit_skip_again.json()["skipped_count"] == 2

    # 2. Commit mode "update" (Perbarui)
    updated_payload = [
        {**client_rows[0], "nama_perangkat": "PC Finance 1 Updated", "os": "Ubuntu 24.04"},
        {**client_rows[1], "keterangan": ""},
    ]
    commit_upd = client.post(
        "/api/v1/ip-allocations/import-commit",
        headers=headers,
        json={"valid_rows": updated_payload, "duplicate_mode": "update"},
    )
    assert commit_upd.status_code == 200
    assert commit_upd.json()["updated_count"] == 2

    # 3. Semua gagal -> Rollback, tabel tidak berubah, kode error ERR-xxxx
    bad_rows = [
        {"ip_address": "192.168.1.63", "nama_perangkat": "PC Baru Valid", "tipe": "Fisik"},
        {"ip_address": "999.999.999.999", "nama_perangkat": "PC Rusak", "tipe": "Fisik"},
    ]
    fail_res = client.post(
        "/api/v1/ip-allocations/import-commit",
        headers=headers,
        json={"valid_rows": bad_rows, "duplicate_mode": "skip"},
    )
    assert fail_res.status_code == 400
    assert fail_res.json()["detail"].startswith("Import gagal. Kode: ERR-")

    list_res = client.get("/api/v1/ip-allocations", headers=headers)
    ips = {it["ip_address"]: it for it in list_res.json()["items"]}
    assert "192.168.1.63" not in ips  # Rollback berhasil, baris pertama batal disimpan
    assert ips["192.168.1.61"]["nama_perangkat"] == "PC Finance 1 Updated"
    assert ips["192.168.1.61"]["has_kendala"] is False
    assert ips["192.168.1.61"]["keterangan"] is None


def test_kendala_helper_host_options_map_and_print(client: TestClient, session: Session) -> None:
    """A2, A3, A4, B2, B4: Uji has_kendala, host_options VM count, /map bentrok=0, & /print-data."""
    headers = _auth_headers(session, "admin_all", UserRole.ADMINISTRATOR)

    srv = Asset(
        id_aset="SRV-002",
        nama_aset="SERVER OTO RETAIL",
        kategori="Server",
        status="Digunakan",
        lokasi="Head Office (Office Blok 14)",
    )
    session.add(srv)
    session.commit()

    # Buat VM dengan fungsi terisi & keterangan kosong -> has_kendala False & keterangan None
    vm_res = client.post(
        "/api/v1/ip-allocations",
        headers=headers,
        json={
            "ip_address": "192.168.1.70",
            "pengguna": "ADDON RETAIL 1",
            "jenis": "VM",
            "id_aset_host": "SRV-002",
            "fungsi": "Worker Transaksi Retail",
            "keterangan": "   ",
        },
    )
    assert vm_res.status_code == 201
    vm_body = vm_res.json()
    assert vm_body["keterangan"] is None
    assert vm_body["has_kendala"] is False
    assert "Ada kendala" not in vm_body["sub_label"]

    # Cek host_options di GET /api/v1/ip-allocations (A3)
    list_res = client.get("/api/v1/ip-allocations", headers=headers)
    assert list_res.status_code == 200
    host_opts = list_res.json()["host_options"]
    assert host_opts == ["Semua host", "SRV-002 (SERVER OTO RETAIL) · 1 VM"]

    # Cek Peta IP (A4 & B4): bentrok tidak boleh undefined, subnet tidak terdaftar ditolak
    map_res = client.get("/api/v1/ip-allocations/map?subnet=1", headers=headers)
    assert map_res.status_code == 200
    assert map_res.json()["stats"]["bentrok"] == 0

    bad_map = client.get("/api/v1/ip-allocations/map?subnet=10.0.0.0/24", headers=headers)
    assert bad_map.status_code == 422

    # Cek Print Data & Audit Log (B2)
    print_res = client.get("/api/v1/ip-allocations/print-data", headers=headers)
    assert print_res.status_code == 200
    assert print_res.json()["total"] == 1
