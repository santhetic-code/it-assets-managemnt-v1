from datetime import date, timedelta

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


def test_maintenance_schedule_complete_and_recurring_regeneration(
    client: TestClient,
    session: Session,
) -> None:
    headers = _auth_headers(session, "admin_mnt", UserRole.ADMINISTRATOR)

    # 1. Buat aset UPS yang kondisinya Perlu Pengecekan -> UPS-001
    ups_res = client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "nama_aset": "UPS ICA Server Room",
            "kategori": "UPS",
            "merek": "ICA",
            "model": "CP1400",
            "lokasi": "Head Office (Office Blok 14)",
            "status": "Perbaikan",
            "kondisi": "Perlu Pengecekan",
            "kapasitas_va": 1400,
        },
    )
    assert ups_res.status_code == 201
    ups_code = ups_res.json()["id_aset"]

    # 2. Buat jadwal maintenance rutin bulanan yang sudah lewat 2 hari (overdue)
    past_date = (date.today() - timedelta(days=2)).isoformat()
    mnt_res = client.post(
        "/api/v1/maintenance",
        headers=headers,
        json={
            "id_aset": ups_code,
            "jenis_maintenance": "Penggantian Baterai",
            "prioritas": "Tinggi",
            "deskripsi": "Cek tegangan dan ganti baterai YUASA",
            "teknisi": "Tio",
            "tanggal_jadwal": past_date,
            "is_recurring": True,
            "siklus": "Bulanan",
        },
    )
    assert mnt_res.status_code == 201
    mnt = mnt_res.json()
    assert mnt["kode_maintenance"] == "MNT-001"
    assert mnt["nama_aset"] == "UPS ICA Server Room"
    assert mnt["is_overdue"] is True
    assert mnt["status_efektif"] == "Terlambat"

    # 3. Selesaikan MNT-001 -> masuk riwayat, aset jadi Baik/Aktif, & otomatis buat MNT-002
    comp_res = client.post(
        "/api/v1/maintenance/MNT-001/complete",
        headers=headers,
        json={
            "tindakan": "Ganti 2 unit baterai YUASA 12V 7Ah baru",
            "biaya": 550000,
            "kondisi_setelah": "Baik",
            "status_aset_setelah": "Aktif",
        },
    )
    assert comp_res.status_code == 200
    done = comp_res.json()
    assert done["status"] == "Selesai"
    assert done["is_history"] is True
    assert done["biaya"] == 550000

    # Pastikan kondisi & status aset di /api/v1/assets ikut terbarui
    asset_after = client.get(f"/api/v1/assets/{ups_code}", headers=headers).json()
    assert asset_after["kondisi"] == "Baik"
    assert asset_after["status"] == "Aktif"

    # Pastikan MNT-002 otomatis terbuat untuk bulan berikutnya
    list_all = client.get("/api/v1/maintenance", headers=headers).json()
    assert list_all["total"] == 2
    assert list_all["tab_counts"]["Riwayat"] == 1
    assert list_all["tab_counts"]["Jadwal"] == 1
    codes = [item["kode_maintenance"] for item in list_all["items"]]
    assert "MNT-001" in codes
    assert "MNT-002" in codes


def test_bulk_maintenance_schedule_by_category_and_location(
    client: TestClient,
    session: Session,
) -> None:
    headers = _auth_headers(session, "member_mnt", UserRole.MEMBER)

    # Buat 2 PC di Head Office dan 1 PC di Mess
    for nama, lokasi in [
        ("PC Admin 1", "Head Office (Office Blok 14)"),
        ("PC Admin 2", "Head Office (Office Blok 14)"),
        ("PC Mess 1", "Mess (Mess Blok 12)"),
    ]:
        client.post(
            "/api/v1/assets",
            headers=headers,
            json={"nama_aset": nama, "kategori": "PC", "lokasi": lokasi},
        )

    # Buat jadwal massal khusus untuk semua PC di Head Office (harus membuat 2 jadwal)
    bulk_res = client.post(
        "/api/v1/maintenance/bulk",
        headers=headers,
        json={
            "kategori": "PC",
            "lokasi": "Head Office (Office Blok 14)",
            "jenis_maintenance": "Pembersihan",
            "prioritas": "Normal",
            "deskripsi": "Pembersihan debu rutin & ganti thermal paste",
            "teknisi": "Tim IT Support",
            "tanggal_jadwal": "2026-11-15",
        },
    )
    assert bulk_res.status_code == 201
    bulk_data = bulk_res.json()
    assert bulk_data["created_count"] == 2
    assert len(bulk_data["items"]) == 2
    assert {i["nama_aset"] for i in bulk_data["items"]} == {"PC Admin 1", "PC Admin 2"}


def test_maintenance_validation_and_rbac(
    client: TestClient,
    session: Session,
) -> None:
    admin_h = _auth_headers(session, "adm_m", UserRole.ADMINISTRATOR)
    member_h = _auth_headers(session, "mem_m", UserRole.MEMBER)
    viewer_h = _auth_headers(session, "vw_m", UserRole.VIEWER)

    # Buat 1 aset PC
    a_res = client.post(
        "/api/v1/assets",
        headers=member_h,
        json={
            "nama_aset": "PC Kasir Rinjani",
            "kategori": "PC",
            "lokasi": "Konter (Ruko Rinjani)",
        },
    )
    code = a_res.json()["id_aset"]

    # Viewer ditolak membuat jadwal (403)
    denied = client.post(
        "/api/v1/maintenance",
        headers=viewer_h,
        json={"id_aset": code, "deskripsi": "Cek PC"},
    )
    assert denied.status_code == 403

    # Jadwal untuk kode aset yang tidak ada -> 404
    not_found = client.post(
        "/api/v1/maintenance",
        headers=member_h,
        json={"id_aset": "PC-999", "deskripsi": "Aset tidak ada"},
    )
    assert not_found.status_code == 404

    # Member membuat jadwal lalu Administrator menghapusnya
    ok_res = client.post(
        "/api/v1/maintenance",
        headers=member_h,
        json={"id_aset": code, "deskripsi": "Instal ulang driver printer VSC"},
    )
    assert ok_res.status_code == 201
    mnt_code = ok_res.json()["kode_maintenance"]

    assert client.delete(f"/api/v1/maintenance/{mnt_code}", headers=member_h).status_code == 403
    assert client.delete(f"/api/v1/maintenance/{mnt_code}", headers=admin_h).status_code == 200
