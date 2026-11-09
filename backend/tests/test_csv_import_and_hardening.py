"""Unit test untuk modul Tahap B9: Integrasi Data Nyata CSV, Security Hardening, & Deploy."""

from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from app.core.csv_importer import _normalize_loc, import_all_csv_data, resolve_data_dir
from app.core.rate_limit import reset_login_rate_limiter
from app.core.security import create_access_token, hash_password
from app.models.asset import Asset
from app.models.audit import AuditLog
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation
from app.models.user import User, UserRole
from scripts.generate_secrets import generate_production_secrets


def test_import_real_csv_files_is_idempotent(session: Session) -> None:
    """Menguji bahwa impor 4 file CSV nyata di docs/data/ berhasil dan strictly idempoten."""
    data_dir = resolve_data_dir()
    assert (data_dir / "rekap_ups_xml.csv").exists(), f"File UPS tidak ada di {data_dir}"
    assert (data_dir / "rekap_watt_server.csv").exists()
    assert (data_dir / "ip_list_xml.csv").exists()
    assert (data_dir / "rekap_pembelian.csv").exists()

    # Eksekusi Impor Pertama
    res1 = import_all_csv_data(session, data_dir=data_dir, username="test_admin")
    assert res1["success"] is True
    data1 = res1["data"]

    # Verifikasi jumlah impor pertama
    assert data1["ups_imported"] == 24
    assert data1["servers_imported"] == 16
    assert data1["ips_imported"] >= 30
    assert data1["purchases_imported"] == 41
    total1 = data1["total_imported"]
    assert total1 >= 110

    # Verifikasi database assets (UPS & Server)
    ups_assets = session.exec(select(Asset).where(col(Asset.kategori) == "UPS")).all()
    assert len(ups_assets) == 24
    server_assets = session.exec(select(Asset).where(col(Asset.kategori) == "Server")).all()
    assert len(server_assets) == 16

    # Verifikasi database IP Allocation
    ip_records = session.exec(select(IPAllocation)).all()
    assert len(ip_records) >= 30
    # Pastikan ip_int terisi dengan benar (bukan 0)
    assert all(rec.ip_int > 0 for rec in ip_records)

    # Verifikasi database Purchases
    purchases = session.exec(select(Purchase)).all()
    assert len(purchases) == 41
    po_001 = session.exec(select(Purchase).where(col(Purchase.kode_pembelian) == "PO-001")).first()
    assert po_001 is not None
    assert po_001.harga_satuan == 77500
    assert po_001.jumlah == 2
    assert po_001.total_harga == 155000

    # Verifikasi audit log tercatat
    audit = session.exec(select(AuditLog).where(col(AuditLog.aksi) == "Impor CSV")).first()
    assert audit is not None
    assert "Berhasil mengimpor" in audit.detail

    # Eksekusi Impor Kedua (Uji Idempotensi)
    res2 = import_all_csv_data(session, data_dir=data_dir, username="test_admin")
    assert res2["success"] is True
    data2 = res2["data"]
    assert data2["total_imported"] == 0
    assert data2["ups_imported"] == 0
    assert data2["servers_imported"] == 0
    assert data2["ips_imported"] == 0
    assert data2["purchases_imported"] == 0

    # Pastikan jumlah entri di tabel tidak bertambah sama sekali
    assert len(session.exec(select(Asset).where(col(Asset.kategori) == "UPS")).all()) == 24
    assert len(session.exec(select(Asset).where(col(Asset.kategori) == "Server")).all()) == 16
    assert len(session.exec(select(Purchase)).all()) == 41


def test_security_headers_and_login_rate_limiting(client: TestClient, session: Session) -> None:
    """Menguji security headers, global unhandled exception handler, dan brute-force limiter."""
    reset_login_rate_limiter()

    # 1. Uji HTTP Security Headers
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "same-origin"

    # Untuk endpoint /api/v1/..., harus ada header Cache-Control: no-store
    admin_user = User(
        username="admin_sec",
        full_name="Admin Sec",
        password_hash=hash_password("adminpass"),
        role=UserRole.ADMINISTRATOR.value,
        is_active=True,
    )
    session.add(admin_user)
    session.commit()

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_sec", "password": "adminpass"},
    )
    assert login_resp.status_code == 200
    assert login_resp.headers.get("Cache-Control") == "no-store"
    assert login_resp.headers.get("X-Content-Type-Options") == "nosniff"

    # 2. Uji Brute-Force Rate Limiting pada Login
    # Lakukan 10 kali percobaan gagal
    for i in range(10):
        fail_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin_sec", "password": "wrongpassword"},
        )
        assert fail_resp.status_code == 401, f"Percobaan ke-{i + 1} harusnya 401"

    # Percobaan ke-11 harus diblokir dengan HTTP 429 Too Many Requests
    blocked_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_sec", "password": "wrongpassword"},
    )
    assert blocked_resp.status_code == 429
    assert "Terlalu banyak percobaan login gagal" in blocked_resp.json()["detail"]

    # Sekalipun memasukkan password benar saat terblokir, tetap ditolak 429
    blocked_correct_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_sec", "password": "adminpass"},
    )
    assert blocked_correct_resp.status_code == 429

    # Reset limiter dan pastikan bisa login kembali
    reset_login_rate_limiter()
    login_again = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_sec", "password": "adminpass"},
    )
    assert login_again.status_code == 200

    # 3. Uji Global Unhandled Exception Handler (500 tanpa leak info teknis)
    token = login_resp.json()["access_token"]
    err_client = TestClient(client.app, raise_server_exceptions=False)
    with patch(
        "app.api.v1.master.get_master_data_payload",
        side_effect=RuntimeError("Kesalahan fatal tak terduga"),
    ):
        err_resp = err_client.get(
            "/api/v1/master",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert err_resp.status_code == 500
        data = err_resp.json()
        assert data == {"detail": "Terjadi kesalahan internal pada server"}


def test_generated_production_secrets_pass_strict_validation() -> None:
    """Menguji bahwa script generator rahasia produksi menghasilkan kunci yang valid & kuat."""
    secrets_dict = generate_production_secrets()

    assert "JWT_SECRET_KEY" in secrets_dict
    assert "FERNET_MASTER_KEY" in secrets_dict
    assert "POSTGRES_PASSWORD" in secrets_dict

    # JWT Key minimal 32 karakter
    jwt_key = secrets_dict["JWT_SECRET_KEY"]
    assert len(jwt_key) >= 32

    # Fernet key harus valid dan bisa digunakan untuk enkripsi/dekripsi
    fernet_key = secrets_dict["FERNET_MASTER_KEY"]
    f = Fernet(fernet_key.encode())
    encrypted = f.encrypt(b"test-secret-payload")
    decrypted = f.decrypt(encrypted)
    assert decrypted == b"test-secret-payload"

    # DB Password minimal 16 karakter
    db_pass = secrets_dict["POSTGRES_PASSWORD"]
    assert len(db_pass) >= 16


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
    token = create_access_token(subject=user.username, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_location_disambiguation_and_full_contract_after_csv_import(
    client: TestClient,
    session: Session,
) -> None:
    # 1. Pastikan Blok 12 untuk Office 437 dan Mess tidak tertukar
    assert _normalize_loc("Office 437") == "Office 437 (Office Blok 12)"
    assert _normalize_loc("Office Blok 12") == "Office 437 (Office Blok 12)"
    assert _normalize_loc("Mess Blok 12") == "Mess (Mess Blok 12)"
    assert _normalize_loc("Ruko Rinjani") == "Konter (Ruko Rinjani)"
    assert _normalize_loc("White House") == "White House (Office Blok 13)"
    assert _normalize_loc("Head Office") == "Head Office (Office Blok 14)"

    # 2. Jalankan impor CSV dan pastikan semua endpoint utama merespons kontrak frontend
    admin_h = _auth_headers(session, "admin_e2e", UserRole.ADMINISTRATOR)
    client.post("/api/v1/master/import-csv", headers=admin_h)

    for path in (
        "/api/v1/assets",
        "/api/v1/watt-server",
        "/api/v1/ip-allocations",
        "/api/v1/ip-entries",
        "/api/v1/purchases",
        "/api/v1/maintenance",
        "/api/v1/credentials",
        "/api/v1/audit-logs",
    ):
        res = client.get(path, headers=admin_h)
        assert res.status_code == 200
        payload = res.json()
        assert "items" in payload
        assert "total" in payload
        assert "tab_counts" in payload
        assert "summary" in payload

    # 3. Verifikasi kontrak Inventory (Semua Aset, PC, Server, Monitor, UPS) & category_counts
    assets_all = client.get("/api/v1/assets", headers=admin_h).json()
    assert "category_counts" in assets_all
    assert assets_all["category_counts"]["all"] == 77
    assert assets_all["category_counts"]["pc"] == 33
    assert assets_all["category_counts"]["server"] == 16
    assert assets_all["category_counts"]["monitor"] == 4
    assert assets_all["category_counts"]["ups"] == 24

    pc_op = client.get("/api/v1/assets?slug=pc&tab=Operasional", headers=admin_h).json()
    assert pc_op["total"] == 33
    assert pc_op["tab_counts"]["Operasional"] == 33
    assert pc_op["tab_counts"]["Server"] == 16
    assert pc_op["tab_counts"]["Backup"] == 5
    assert "attributes" in pc_op["items"][0]
    assert "sn_pid" in pc_op["items"][0]

    # 4. Verifikasi kontrak Dashboard (/api/v1/dashboard/summary)
    dash = client.get("/api/v1/dashboard/summary", headers=admin_h)
    assert dash.status_code == 200
    dash_data = dash.json()
    assert "kpis" in dash_data
    assert dash_data["kpis"]["total_assets"] == 77
    assert len(dash_data["monthly_purchases"]) == 6
    assert len(dash_data["assets_by_category"]) == 4
    assert len(dash_data["ups_loads"]) > 0

    # 5. Verifikasi kontrak IP & Server (VM) (/api/v1/ip-entries)
    ip_res = client.get("/api/v1/ip-entries?grup=Semua", headers=admin_h).json()
    assert ip_res["kpi"]["total_ip"] == 59
    assert ip_res["kpi"]["operasional"] == 47
    assert ip_res["kpi"]["addon"] == 12
    assert ip_res["kpi"]["vm_tanpa_host"] == 0
    assert "192.168.1.0/24" in ip_res["subnet_options"]
    first_ip = ip_res["items"][0]
    for k in ("nama", "jenis", "asset_id", "host_asset_id", "grup", "fungsi", "host_label"):
        assert k in first_ip

    # 6. Verifikasi kontrak Rekap Watt Server (/api/v1/watt-server)
    watt_res = client.get("/api/v1/watt-server?tab=Semua", headers=admin_h).json()
    assert watt_res["summary"]["total_servers"] == 16
    assert watt_res["tab_counts"]["Operasional"] == 11
    assert watt_res["tab_counts"]["Backup"] == 5
    first_watt = watt_res["items"][0]
    watt_keys = (
        "cpu",
        "cpu_brand",
        "vga",
        "hdd_ssd",
        "tdp_display",
        "psu_min_display",
        "beban_badge",
    )
    for k in watt_keys:
        assert k in first_watt

    # 7. Verifikasi kontrak Pembelian, Maintenance, & Credentials
    po_res = client.get("/api/v1/purchases?tab=pembelian", headers=admin_h).json()
    assert po_res["total"] == 41
    assert "total_belanja" in po_res["summary"]
    first_po = po_res["items"][0]
    for k in ("produk", "harga", "pcs", "total", "nama_toko", "domain_chip", "aset_status"):
        assert k in first_po

    mnt_res = client.get("/api/v1/maintenance?tab=jadwal", headers=admin_h).json()
    assert mnt_res["total"] >= 3
    assert "objek_display" in mnt_res["items"][0]
    assert "jadwal_berikutnya" in mnt_res["items"][0]

    crd_res = client.get("/api/v1/credentials", headers=admin_h).json()
    assert crd_res["total"] >= 6
    assert "jenis_label" in crd_res["items"][0]
    assert "induk" in crd_res["items"][0]
    rev_res = client.post("/api/v1/credentials/CRD-001/reveal", headers=admin_h).json()
    assert rev_res["value"] != ""
