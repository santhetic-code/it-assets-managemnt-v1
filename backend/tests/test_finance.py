"""Pengujian unit untuk modul Keuangan (Pembelian, Invoice, Tagihan Berulang) Tahap B5."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.schemas.finance import advance_due_date


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


def test_advance_due_date_edge_cases() -> None:
    # 31 Januari + 1 bulan -> 28 Februari (tahun non-kabisat 2026)
    assert advance_due_date(date(2026, 1, 31), "Bulanan") == date(2026, 2, 28)
    # Siklus Triwulan & Tahunan
    assert advance_due_date(date(2026, 3, 15), "Triwulan") == date(2026, 6, 15)
    assert advance_due_date(date(2026, 11, 3), "Tahunan") == date(2027, 11, 3)


def test_purchase_invoice_and_recurring_lifecycle(
    client: TestClient,
    session: Session,
) -> None:
    headers = _auth_headers(session, "admin_fin", UserRole.ADMINISTRATOR)

    # 1. Buat Pembelian Perangkat Keras (otomatis PO-001 & hitung total_harga = 2 * 1.850.000)
    r_po = client.post(
        "/api/v1/purchases",
        headers=headers,
        json={
            "nama_item": "Monitor LG 24MK600",
            "kategori": "Monitor",
            "vendor": "Toko Komputer Jaya",
            "lokasi": "Head Office (Office Blok 14)",
            "jumlah": 2,
            "harga_satuan": 1850000,
            "tanggal_beli": "2026-10-20",
            "nomor_invoice": "INV/2026/10/088",
            "status": "Lunas",
        },
    )
    assert r_po.status_code == 201
    po_data = r_po.json()
    assert po_data["kode_pembelian"] == "PO-001"
    assert po_data["total_harga"] == 3700000
    assert po_data["is_recurring"] is False

    # 2. Buat Tagihan Berulang Internet Bulanan yang sudah melewati jatuh tempo (overdue)
    past_due = (date.today() - timedelta(days=3)).isoformat()
    r_bill = client.post(
        "/api/v1/purchases",
        headers=headers,
        json={
            "nama_item": "Dedicated Internet Biznet 100Mbps",
            "kategori": "Jaringan",
            "vendor": "Biznet Networks",
            "lokasi": "Head Office (Office Blok 14)",
            "jumlah": 1,
            "harga_satuan": 2500000,
            "tanggal_beli": "2026-09-01",
            "tanggal_jatuh_tempo": past_due,
            "status": "Belum Lunas",
            "is_recurring": True,
            "siklus_tagihan": "Bulanan",
        },
    )
    assert r_bill.status_code == 201
    bill = r_bill.json()
    assert bill["kode_pembelian"] == "BIL-001"
    assert bill["is_overdue"] is True
    assert bill["status_efektif"] == "Jatuh Tempo"

    # 3. Cek ringkasan KPI dan tab_counts
    list_res = client.get("/api/v1/purchases", headers=headers)
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["total"] == 2
    assert body["tab_counts"]["Pembelian"] == 1
    assert body["tab_counts"]["Tagihan Berulang"] == 1
    assert body["tab_counts"]["Jatuh Tempo"] == 1
    assert body["summary"]["total_pengeluaran"] == 6200000
    assert body["summary"]["total_lunas"] == 3700000
    assert body["summary"]["total_belum_lunas"] == 2500000
    assert body["summary"]["estimasi_tagihan_bulanan"] == 2500000

    # 4. Bayar tagihan berulang BIL-001 -> jatuh tempo otomatis maju 1 bulan & tidak lagi overdue
    pay_res = client.post(
        f"/api/v1/purchases/{bill['kode_pembelian']}/pay",
        headers=headers,
        json={"metode_pembayaran": "Transfer BCA"},
    )
    assert pay_res.status_code == 200
    paid_bill = pay_res.json()
    expected_next_due = advance_due_date(
        date.fromisoformat(past_due),
        "Bulanan",
    ).isoformat()
    assert paid_bill["tanggal_jatuh_tempo"] == expected_next_due
    assert paid_bill["is_overdue"] is False


def test_finance_rbac_and_one_time_invoice_payment(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _auth_headers(session, "adm_f", UserRole.ADMINISTRATOR)
    member_h = _auth_headers(session, "mem_f", UserRole.MEMBER)
    viewer_h = _auth_headers(session, "vw_f", UserRole.VIEWER)

    # Viewer ditolak membuat transaksi baru (403)
    denied = client.post(
        "/api/v1/purchases",
        headers=viewer_h,
        json={"nama_item": "Baterai YUASA 12V 7Ah", "harga_satuan": 280000},
    )
    assert denied.status_code == 403

    # Member membuat Invoice sekali bayar yang Belum Lunas
    inv_res = client.post(
        "/api/v1/purchases",
        headers=member_h,
        json={
            "nama_item": "Baterai UPS YUASA 12V 7Ah",
            "kategori": "UPS",
            "jenis_transaksi": "Invoice",
            "nomor_invoice": "INV-YUASA-01",
            "jumlah": 4,
            "harga_satuan": 275000,
            "status": "Belum Lunas",
        },
    )
    assert inv_res.status_code == 201
    code = inv_res.json()["kode_pembelian"]
    assert code == "INV-001"
    assert inv_res.json()["total_harga"] == 1100000

    # Tandai lunas invoice sekali bayar -> status menjadi Lunas
    paid = client.post(f"/api/v1/purchases/{code}/pay", headers=member_h)
    assert paid.status_code == 200
    assert paid.json()["status"] == "Lunas"
    assert paid.json()["tanggal_bayar"] == date.today().isoformat()

    # Member tidak boleh DELETE (403), Administrator boleh DELETE (200)
    assert client.delete(f"/api/v1/purchases/{code}", headers=member_h).status_code == 403
    assert client.delete(f"/api/v1/purchases/{code}", headers=admin_h).status_code == 200
