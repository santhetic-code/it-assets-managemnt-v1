"""Endpoint CRUD Maintenance: Jadwal, Riwayat, Penyelesaian, & Jadwal Massal (B6)."""

import calendar as py_calendar
import csv
import io
import re
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.base import utcnow
from app.models.maintenance import (
    Location,
    Maintenance,
    MaintenanceTemplate,
    Vendor,
)
from app.schemas.finance import VALID_BILLING_CYCLES, advance_due_date
from app.schemas.maintenance import (
    VALID_MAINTENANCE_STATUSES,
    VALID_MAINTENANCE_TYPES,
    VALID_PRIORITIES,
    BulkMaintenanceRequest,
    BulkMaintenanceResponse,
    MaintenanceCompleteRequest,
    MaintenanceCreate,
    MaintenancePageResponse,
    MaintenancePublic,
    MaintenanceUpdate,
)

router = APIRouter()

MNT_CODE_PATTERN = re.compile(r"^MNT-(\d+)$")


def generate_next_maintenance_code(session: Session) -> str:
    """Menghasilkan kode otomatis MNT-001, MNT-002, dst."""
    existing = session.exec(
        select(Maintenance.kode_maintenance).where(col(Maintenance.kode_maintenance).like("MNT-%"))
    ).all()
    max_num = 0
    for code in existing:
        match = MNT_CODE_PATTERN.match(code.strip().upper())
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"MNT-{max_num + 1:03d}"


def _resolve_asset(session: Session, id_aset: str) -> Asset:
    asset = session.exec(
        select(Asset).where(func.lower(Asset.id_aset) == id_aset.strip().lower())
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aset dengan kode '{id_aset}' tidak ditemukan",
        )
    return asset


def _find_maintenance(session: Session, identifier: str) -> Maintenance:
    cleaned = identifier.strip()
    row: Maintenance | None = None
    if cleaned.isdigit():
        row = session.get(Maintenance, int(cleaned))
    if row is None:
        row = session.exec(
            select(Maintenance).where(func.lower(Maintenance.kode_maintenance) == cleaned.lower())
        ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data maintenance tidak ditemukan",
        )
    return row


def _compute_maintenance_summary(
    all_rows: list[Maintenance],
    today: date | None = None,
) -> tuple[dict[str, int], dict[str, Any]]:
    ref_today = today or date.today()
    public_items = [MaintenancePublic.from_model(r, today=ref_today) for r in all_rows]

    total_all = len(public_items)
    jadwal_aktif = sum(1 for i in public_items if not i.is_history)
    terjadwal_count = sum(
        1 for i in public_items if i.status.lower() == "terjadwal" and not i.is_overdue
    )
    proses_count = sum(
        1 for i in public_items if i.status.lower() in ("dalam proses", "sedang dikerjakan")
    )
    overdue_count = sum(1 for i in public_items if i.is_overdue)
    selesai_count = sum(1 for i in public_items if i.status.lower() == "selesai")
    batal_count = sum(1 for i in public_items if i.status.lower() == "dibatalkan")
    riwayat_count = selesai_count + batal_count
    rutin_count = sum(1 for i in public_items if i.is_recurring and not i.is_history)
    total_biaya = sum(i.biaya for i in public_items if i.status.lower() != "dibatalkan")

    tab_counts = {
        "Semua": total_all,
        "all": total_all,
        "Jadwal": jadwal_aktif,
        "Terjadwal": terjadwal_count,
        "Dalam Proses": proses_count,
        "Terlambat": overdue_count,
        "Riwayat": riwayat_count,
        "Selesai": selesai_count,
        "Rutin": rutin_count,
    }

    segera_count = sum(
        1 for i in public_items if (not i.is_history) and (0 <= i.hari_menuju_jadwal <= 7)
    )
    tindak_lanjut_count = sum(1 for i in public_items if i.hasil == "Perlu Tindak Lanjut")

    summary: dict[str, Any] = {
        "total": total_all,
        "total_jadwal": jadwal_aktif,
        "aktif": jadwal_aktif,
        "terjadwal": terjadwal_count,
        "segera": segera_count,
        "dalam_proses": proses_count,
        "terlambat": overdue_count,
        "overdue": overdue_count,
        "tindak_lanjut": tindak_lanjut_count,
        "total_riwayat": riwayat_count,
        "selesai": selesai_count,
        "dibatalkan": batal_count,
        "jadwal_rutin": rutin_count,
        "total_biaya": total_biaya,
    }
    return tab_counts, summary


@router.get("", response_model=MaintenancePageResponse)
def list_maintenances(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tab: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    id_aset: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    jenis: str | None = Query(default=None),
    frekuensi: str | None = Query(default=None),
    pic: str | None = Query(default=None),
    hasil: str | None = Query(default=None),
    month: str | None = Query(default=None),
    prioritas: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    overdue_only: bool = Query(default=False),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="asc"),
) -> MaintenancePageResponse:
    """Mengambil daftar jadwal dan riwayat maintenance berhalaman."""
    all_rows = list(
        session.exec(
            select(Maintenance).order_by(
                col(Maintenance.tanggal_jadwal).asc(),
                col(Maintenance.id).desc(),
            )
        ).all()
    )
    today = date.today()
    tab_counts, summary = _compute_maintenance_summary(all_rows, today=today)
    all_public = [MaintenancePublic.from_model(r, today=today) for r in all_rows]

    filtered = all_public

    keyword = (search or q or "").strip().lower()
    if keyword:
        filtered = [
            i
            for i in filtered
            if keyword in i.kode_maintenance.lower()
            or keyword in i.id_aset.lower()
            or keyword in i.nama_aset.lower()
            or keyword in i.judul.lower()
            or keyword in i.deskripsi.lower()
            or keyword in i.teknisi.lower()
            or keyword in i.tindakan.lower()
        ]

    active_tab = (tab or mode or "").strip().lower()
    if active_tab and active_tab not in ("semua", "all"):
        if active_tab in ("jadwal", "aktif", "schedule", "upcoming"):
            filtered = [i for i in filtered if not i.is_history]
        elif active_tab in ("riwayat", "history", "selesai"):
            filtered = [i for i in filtered if i.is_history]
        elif active_tab in ("terlambat", "overdue"):
            filtered = [i for i in filtered if i.is_overdue]
        elif active_tab in ("dalam proses", "proses"):
            filtered = [
                i for i in filtered if i.status.lower() in ("dalam proses", "sedang dikerjakan")
            ]
        elif active_tab in ("rutin", "recurring"):
            filtered = [i for i in filtered if i.is_recurring]

    if overdue_only:
        filtered = [i for i in filtered if i.is_overdue]

    if id_aset and id_aset.strip():
        code_clean = id_aset.strip().lower()
        filtered = [i for i in filtered if i.id_aset.lower() == code_clean]

    if kategori and kategori.strip().lower() not in ("semua", "all", ""):
        kat_clean = kategori.strip().lower()
        filtered = [i for i in filtered if i.kategori.lower() == kat_clean]

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        loc_clean = lokasi.strip().lower()
        filtered = [i for i in filtered if i.lokasi.lower() == loc_clean]

    if jenis and jenis.strip().lower() not in ("semua", "all", ""):
        j_clean = jenis.strip().lower()
        filtered = [i for i in filtered if i.jenis_maintenance.lower() == j_clean]

    if prioritas and prioritas.strip().lower() not in ("semua", "all", ""):
        p_clean = prioritas.strip().lower()
        filtered = [i for i in filtered if i.prioritas.lower() == p_clean]

    if frekuensi and frekuensi.strip().lower() not in ("semua", "all", ""):
        f_clean = VALID_BILLING_CYCLES.get(frekuensi.strip(), frekuensi.strip()).lower()
        filtered = [i for i in filtered if i.siklus.lower() == f_clean]

    if pic and pic.strip().lower() not in ("semua", "all", ""):
        pic_clean = pic.strip().lower()
        filtered = [i for i in filtered if pic_clean in i.teknisi.lower()]

    if hasil and hasil.strip().lower() not in ("semua", "all", ""):
        h_clean = hasil.strip().lower()
        filtered = [i for i in filtered if i.hasil.lower() == h_clean]

    if month and month.strip().lower() not in ("semua", "all", ""):
        m_map = {
            "januari": "-01-",
            "februari": "-02-",
            "maret": "-03-",
            "april": "-04-",
            "mei": "-05-",
            "juni": "-06-",
            "juli": "-07-",
            "agustus": "-08-",
            "september": "-09-",
            "oktober": "-10-",
            "november": "-11-",
            "desember": "-12-",
        }
        m_sub = m_map.get(month.strip().lower(), month.strip())
        filtered = [i for i in filtered if m_sub in (i.tanggal_selesai or i.tanggal_jadwal)]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        if st_clean in ("terlambat", "overdue"):
            filtered = [i for i in filtered if i.is_overdue]
        elif st_clean == "segera":
            filtered = [
                i for i in filtered if (not i.is_history) and (0 <= i.hari_menuju_jadwal <= 7)
            ]
        else:
            filtered = [
                i
                for i in filtered
                if i.status.lower() == st_clean or i.status_efektif.lower() == st_clean
            ]

    if sort_by and sort_by.strip():
        s_key = sort_by.strip()
        rev = (sort_dir or "asc").strip().lower() == "desc"
        filtered.sort(
            key=lambda i: str(getattr(i, s_key, "") or "").lower(),
            reverse=rev,
        )

    total = len(filtered)
    paged = filtered[page_params.offset : page_params.offset + page_params.page_size]

    return MaintenancePageResponse(
        items=paged,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=summary,
    )


@router.post("/bulk", response_model=BulkMaintenanceResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "/bulk-schedule",
    response_model=BulkMaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_bulk_maintenance(
    payload: BulkMaintenanceRequest,
    session: SessionDep,
    _: EditorUserDep,
) -> BulkMaintenanceResponse:
    """Membuat jadwal maintenance massal untuk banyak aset sekaligus."""
    stmt = select(Asset)

    if payload.id_assets:
        upper_codes = [c.upper() for c in payload.id_assets]
        stmt = stmt.where(func.upper(Asset.id_aset).in_(upper_codes))
    else:
        if payload.only_active_assets:
            stmt = stmt.where(func.lower(Asset.status).notin_(["rusak", "nonaktif"]))
        if payload.kategori:
            stmt = stmt.where(func.lower(Asset.kategori) == payload.kategori.strip().lower())
        if payload.lokasi:
            stmt = stmt.where(func.lower(Asset.lokasi) == payload.lokasi.strip().lower())

    target_assets = list(session.exec(stmt.order_by(col(Asset.id_aset).asc())).all())
    if not target_assets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tidak ada aset yang cocok dengan kriteria jadwal massal",
        )

    created_rows: list[Maintenance] = []
    for asset in target_assets:
        code = generate_next_maintenance_code(session)
        row = Maintenance(
            kode_maintenance=code,
            id_aset=asset.id_aset,
            nama_aset=asset.nama_aset,
            kategori=asset.kategori,
            lokasi=asset.lokasi,
            jenis_maintenance=payload.jenis_maintenance,
            prioritas=payload.prioritas,
            judul=payload.judul,
            deskripsi=payload.deskripsi.strip(),
            tindakan="",
            teknisi=payload.teknisi.strip(),
            vendor_servis="",
            biaya=0,
            tanggal_jadwal=payload.tanggal_jadwal or date.today(),
            tanggal_selesai=None,
            status="Terjadwal",
            kondisi_setelah=asset.kondisi,
            is_recurring=payload.is_recurring,
            siklus=payload.siklus,
            catatan=payload.catatan.strip(),
        )
        session.add(row)
        session.flush()
        created_rows.append(row)

    session.commit()
    for r in created_rows:
        session.refresh(r)

    return BulkMaintenanceResponse(
        created_count=len(created_rows),
        items=[MaintenancePublic.from_model(r) for r in created_rows],
    )


@router.get("/{identifier}", response_model=MaintenancePublic)
def get_maintenance_detail(
    identifier: str,
    session: SessionDep,
    _: CurrentUserDep,
) -> MaintenancePublic:
    """Mengambil detail satu jadwal atau riwayat maintenance."""
    row = _find_maintenance(session, identifier)
    return MaintenancePublic.from_model(row)


@router.post("", response_model=MaintenancePublic, status_code=status.HTTP_201_CREATED)
def create_maintenance(
    payload: MaintenanceCreate,
    session: SessionDep,
    _: EditorUserDep,
) -> MaintenancePublic:
    """Membuat jadwal atau catatan riwayat maintenance tunggal."""
    asset = _resolve_asset(session, payload.id_aset)

    if payload.kode_maintenance and payload.kode_maintenance.strip():
        final_code = payload.kode_maintenance.strip().upper()
        dup = session.exec(
            select(Maintenance).where(
                func.lower(Maintenance.kode_maintenance) == final_code.lower()
            )
        ).first()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Kode maintenance '{final_code}' sudah terdaftar",
            )
    else:
        final_code = generate_next_maintenance_code(session)

    row = Maintenance(
        kode_maintenance=final_code,
        id_aset=asset.id_aset,
        nama_aset=payload.nama_aset.strip() or asset.nama_aset,
        kategori=payload.kategori.strip() or asset.kategori,
        lokasi=payload.lokasi.strip() or asset.lokasi,
        jenis_maintenance=payload.jenis_maintenance,
        prioritas=payload.prioritas,
        judul=payload.judul.strip(),
        deskripsi=payload.deskripsi.strip(),
        tindakan=payload.tindakan.strip(),
        teknisi=payload.teknisi,
        vendor_servis=payload.vendor_servis.strip(),
        biaya=payload.biaya,
        tanggal_jadwal=payload.tanggal_jadwal or date.today(),
        tanggal_selesai=payload.tanggal_selesai,
        status=payload.status,
        kondisi_setelah=payload.kondisi_setelah,
        is_recurring=bool(payload.is_recurring),
        siklus=payload.siklus,
        catatan=payload.catatan.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return MaintenancePublic.from_model(row)


def _apply_maintenance_update(
    identifier: str,
    payload: MaintenanceUpdate,
    session: Session,
) -> MaintenancePublic:
    row = _find_maintenance(session, identifier)
    data = payload.model_dump(exclude_unset=True)

    if "jenis_maintenance" in data and data["jenis_maintenance"] is not None:
        raw_t = str(data["jenis_maintenance"]).strip()
        matched_t = next(
            (t for t in VALID_MAINTENANCE_TYPES if t.lower() == raw_t.lower()),
            None,
        )
        if not matched_t:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Jenis maintenance '{raw_t}' tidak valid",
            )
        data["jenis_maintenance"] = matched_t

    if "prioritas" in data and data["prioritas"] is not None:
        raw_p = str(data["prioritas"]).strip()
        matched_p = next(
            (p for p in VALID_PRIORITIES if p.lower() == raw_p.lower()),
            None,
        )
        if not matched_p:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Prioritas '{raw_p}' tidak valid",
            )
        data["prioritas"] = matched_p

    if "status" in data and data["status"] is not None:
        raw_st = str(data["status"]).strip()
        matched_st = next(
            (s for s in VALID_MAINTENANCE_STATUSES if s.lower() == raw_st.lower()),
            None,
        )
        if not matched_st:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Status '{raw_st}' tidak valid",
            )
        data["status"] = "Terjadwal" if matched_st == "Dijadwalkan" else matched_st

    if "siklus" in data and data["siklus"] is not None:
        raw_c = str(data["siklus"]).strip()
        if raw_c not in VALID_BILLING_CYCLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Siklus '{raw_c}' tidak valid",
            )
        data["siklus"] = VALID_BILLING_CYCLES[raw_c]

    for key, val in data.items():
        if key in ("id", "kode_maintenance", "created_at") or val is None:
            continue
        if hasattr(row, key):
            setattr(row, key, val.strip() if isinstance(val, str) else val)

    if row.status == "Selesai" and row.tanggal_selesai is None:
        row.tanggal_selesai = date.today()

    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return MaintenancePublic.from_model(row)


@router.put("/{identifier}", response_model=MaintenancePublic)
def update_maintenance_put(
    identifier: str,
    payload: MaintenanceUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> MaintenancePublic:
    """Memperbarui data jadwal/riwayat maintenance (PUT)."""
    return _apply_maintenance_update(identifier, payload, session)


@router.patch("/{identifier}", response_model=MaintenancePublic)
def update_maintenance_patch(
    identifier: str,
    payload: MaintenanceUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> MaintenancePublic:
    """Memperbarui sebagian data jadwal/riwayat maintenance (PATCH)."""
    return _apply_maintenance_update(identifier, payload, session)


@router.post("/{identifier}/complete", response_model=MaintenancePublic)
def complete_maintenance(
    identifier: str,
    session: SessionDep,
    _: EditorUserDep,
    payload: MaintenanceCompleteRequest | None = None,
) -> MaintenancePublic:
    """Menandai jadwal maintenance selesai, memperbarui aset, & membuat jadwal baru."""
    row = _find_maintenance(session, identifier)
    req = payload or MaintenanceCompleteRequest()
    done_date = req.tanggal_selesai or date.today()

    row.status = "Selesai"
    row.tanggal_selesai = done_date
    if req.tindakan is not None:
        row.tindakan = req.tindakan.strip()
    elif req.hasil is not None:
        row.tindakan = req.hasil.strip()

    if req.teknisi is not None:
        row.teknisi = req.teknisi.strip()
    elif req.pic is not None:
        row.teknisi = req.pic.strip()
    elif req.dikerjakan_oleh is not None:
        row.teknisi = req.dikerjakan_oleh.strip()

    if req.biaya is not None:
        row.biaya = req.biaya
    if req.catatan is not None:
        row.catatan = req.catatan.strip()
    if req.hasil and "tindak lanjut" in req.hasil.lower():
        row.kondisi_setelah = "Perlu Pengecekan"
    else:
        row.kondisi_setelah = req.kondisi_setelah
    row.updated_at = utcnow()
    session.add(row)

    # Sinkronkan kondisi & status aset terkait
    asset = session.exec(
        select(Asset).where(func.lower(Asset.id_aset) == row.id_aset.lower())
    ).first()
    if asset is not None:
        asset.kondisi = req.kondisi_setelah
        if req.status_aset_setelah:
            asset.status = req.status_aset_setelah
        asset.updated_at = utcnow()
        session.add(asset)

    session.flush()

    # Bila jadwal rutin berulang, buat jadwal periode berikutnya secara otomatis
    if row.is_recurring and req.create_next_schedule and row.siklus != "Sekali":
        next_date = advance_due_date(row.tanggal_jadwal, row.siklus)
        next_code = generate_next_maintenance_code(session)
        next_row = Maintenance(
            kode_maintenance=next_code,
            id_aset=row.id_aset,
            nama_aset=row.nama_aset,
            kategori=row.kategori,
            lokasi=row.lokasi,
            jenis_maintenance=row.jenis_maintenance,
            prioritas=row.prioritas,
            judul=row.judul,
            deskripsi=row.deskripsi,
            tindakan="",
            teknisi=row.teknisi,
            vendor_servis=row.vendor_servis,
            biaya=0,
            tanggal_jadwal=next_date,
            tanggal_selesai=None,
            status="Terjadwal",
            kondisi_setelah=req.kondisi_setelah,
            is_recurring=True,
            siklus=row.siklus,
            catatan=row.catatan,
        )
        session.add(next_row)

    session.commit()
    session.refresh(row)
    return MaintenancePublic.from_model(row)


@router.delete("/{identifier}")
def delete_maintenance(
    identifier: str,
    session: SessionDep,
    _: AdminUserDep,
) -> dict[str, Any]:
    """Menghapus jadwal/riwayat maintenance (hanya Administrator)."""
    row = _find_maintenance(session, identifier)
    deleted_code = row.kode_maintenance
    deleted_id = row.id
    session.delete(row)
    session.commit()
    return {"status": "ok", "id": deleted_id, "kode_maintenance": deleted_code}


INITIAL_TEMPLATES_SEED: list[dict[str, Any]] = [
    {
        "nama": "PC",
        "kategori_objek": "PC & Server",
        "kegiatan": "Pembersihan debu internal & ganti thermal paste",
        "jenis": "Preventif",
        "interval_nilai": 3,
        "interval_satuan": "bulan",
        "interval_pemakaian": None,
        "checklist": [
            "Bersihkan kipas & heatsink",
            "Cek suhu CPU",
            "Rapikan manajemen kabel",
        ],
        "pelaksana_default": "Internal",
    },
    {
        "nama": "Server",
        "kategori_objek": "PC & Server",
        "kegiatan": "Pembersihan debu heatsink & verifikasi snapshot VM",
        "jenis": "Preventif",
        "interval_nilai": 1,
        "interval_satuan": "bulan",
        "interval_pemakaian": None,
        "checklist": [
            "Bersihkan filter udara",
            "Cek kesehatan SMART disk",
            "Verifikasi backup VM",
        ],
        "pelaksana_default": "Internal",
    },
    {
        "nama": "UPS",
        "kategori_objek": "UPS",
        "kegiatan": "Cek voltase aki & kalibrasi beban",
        "jenis": "Preventif",
        "interval_nilai": 3,
        "interval_satuan": "bulan",
        "interval_pemakaian": None,
        "checklist": [
            "Ukur voltase baterai",
            "Uji backup saat beban penuh",
            "Cek terminal aki",
        ],
        "pelaksana_default": "Internal",
    },
    {
        "nama": "AC",
        "kategori_objek": "AC",
        "kegiatan": "Cuci AC (cleaning)",
        "jenis": "Preventif",
        "interval_nilai": 3,
        "interval_satuan": "bulan",
        "interval_pemakaian": None,
        "checklist": [
            "Cuci indoor",
            "Cuci outdoor",
            "Cek freon / tekanan",
            "Cek saluran pembuangan",
        ],
        "pelaksana_default": "Vendor",
    },
    {
        "nama": "Genset",
        "kategori_objek": "Genset",
        "kegiatan": "Pemanasan mesin, cek solar, oli & aki starter Krisbow KRPI80",
        "jenis": "Inspeksi",
        "interval_nilai": 1,
        "interval_satuan": "bulan",
        "interval_pemakaian": 250,
        "checklist": [
            "Cek level oli & solar",
            "Cek tegangan aki starter",
            "Pemanasan tanpa beban 15 menit",
        ],
        "pelaksana_default": "Internal",
    },
    {
        "nama": "Jaringan",
        "kategori_objek": "Jaringan",
        "kegiatan": "Backup konfigurasi MikroTik & cek redaman fiber optic",
        "jenis": "Preventif",
        "interval_nilai": 1,
        "interval_satuan": "bulan",
        "interval_pemakaian": None,
        "checklist": [
            "Export backup RouterOS",
            "Cek port switch & suhu",
            "Cek log trafik",
        ],
        "pelaksana_default": "Internal",
    },
    {
        "nama": "Kendaraan",
        "kategori_objek": "Kendaraan",
        "kegiatan": "Servis berkala & ganti oli mesin",
        "jenis": "Preventif",
        "interval_nilai": 3,
        "interval_satuan": "bulan",
        "interval_pemakaian": 5000,
        "checklist": [
            "Ganti oli mesin",
            "Cek rem & ban",
            "Cek lampu & kelistrikan",
        ],
        "pelaksana_default": "Vendor",
    },
    {
        "nama": "Fasilitas",
        "kategori_objek": "Fasilitas",
        "kegiatan": "Inspeksi instalasi listrik & APAR gedung",
        "jenis": "Inspeksi",
        "interval_nilai": 6,
        "interval_satuan": "bulan",
        "interval_pemakaian": None,
        "checklist": ["Cek tekanan tabung APAR", "Cek panel MCB utama"],
        "pelaksana_default": "Internal",
    },
]


def _add_interval_date(base: date, nilai: int, satuan: str) -> date:
    val = max(1, int(nilai or 1))
    u = (satuan or "bulan").strip().lower()
    if u in ("hari", "day", "harian"):
        return base + timedelta(days=val)
    if u in ("minggu", "week", "mingguan"):
        return base + timedelta(days=val * 7)
    months = val * 12 if u in ("tahun", "tahunan") else val
    m_idx = base.month - 1 + months
    yr = base.year + m_idx // 12
    mn = m_idx % 12 + 1
    max_d = py_calendar.monthrange(yr, mn)[1]
    return date(yr, mn, min(base.day, max_d))


def _ensure_templates_and_locations(session: Session) -> None:
    if session.exec(select(MaintenanceTemplate.id).limit(1)).first() is None:
        for t in INITIAL_TEMPLATES_SEED:
            session.add(
                MaintenanceTemplate(
                    nama=t["nama"],
                    kategori_objek=t["kategori_objek"],
                    kegiatan=t["kegiatan"],
                    jenis=t["jenis"],
                    interval_nilai=t["interval_nilai"],
                    interval_satuan=t["interval_satuan"],
                    interval_pemakaian=t["interval_pemakaian"],
                    checklist=t["checklist"],
                    pelaksana_default=t["pelaksana_default"],
                )
            )
        session.commit()

    if session.exec(select(Vendor.id).limit(1)).first() is None:
        for v_nama, v_layanan in [
            ("Teknisi AC", "Cuci & Servis AC"),
            ("Vendor Genset Krisbow", "Servis Genset & Panel ATS"),
            ("Bengkel Resmi", "Servis Kendaraan Operasional"),
        ]:
            session.add(Vendor(nama=v_nama, jenis_layanan=v_layanan))
        session.commit()

    if session.exec(select(Location.id).limit(1)).first() is None:
        for loc_parent in (
            "Kantor Blok 12",
            "Kantor Blok 13",
            "Kantor Blok 14",
            "Ruko Rinjani",
            "Mess Blok 12",
        ):
            p_row = Location(parent_id=None, nama=loc_parent)
            session.add(p_row)
            session.flush()
            for room in ("Ruang Kerja", "Ruang Server", "Ruang Meeting", "Lobby"):
                session.add(Location(parent_id=p_row.id, nama=room))
        session.commit()


@router.get("/templates/meta")
def get_maintenance_templates_and_meta(
    session: SessionDep,
    _: CurrentUserDep,
) -> dict[str, Any]:
    """Mengambil daftar template, vendor, dan lokasi 2 tingkat (Artboard 14)."""
    _ensure_templates_and_locations(session)
    templates = list(
        session.exec(
            select(MaintenanceTemplate).order_by(col(MaintenanceTemplate.id).asc())
        ).all()
    )
    vendors = list(
        session.exec(select(Vendor).order_by(col(Vendor.id).asc())).all()
    )
    locs = list(
        session.exec(select(Location).order_by(col(Location.id).asc())).all()
    )
    parents = [loc for loc in locs if loc.parent_id is None]
    rooms_by_parent = {
        p.nama: [r.nama for r in locs if r.parent_id == p.id] for p in parents
    }
    return {
        "templates": [
            {
                "id": t.id,
                "nama": t.nama,
                "kategori_objek": t.kategori_objek,
                "kegiatan": t.kegiatan,
                "jenis": t.jenis,
                "interval_nilai": t.interval_nilai,
                "interval_satuan": t.interval_satuan,
                "interval_pemakaian": t.interval_pemakaian,
                "checklist": t.checklist,
                "pelaksana_default": t.pelaksana_default,
            }
            for t in templates
        ],
        "vendors": [
            {"id": v.id, "nama": v.nama, "jenis_layanan": v.jenis_layanan}
            for v in vendors
        ],
        "locations": [p.nama for p in parents],
        "rooms_by_location": rooms_by_parent,
    }


@router.post("/import-ac-preview")
def preview_import_ac_sheet(
    payload: dict[str, Any],
    _: EditorUserDep,
) -> dict[str, Any]:
    """Pratinjau import Google Sheet AC."""
    csv_text = str(payload.get("csv_text") or "").strip()
    if not csv_text:
        return {
            "valid_count": 0,
            "error_count": 1,
            "valid_rows": [],
            "errors": [{"row": 1, "reason": "CSV kosong"}],
        }

    first_line = csv_text.split("\n", 1)[0]
    delim = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = list(csv.DictReader(io.StringIO(csv_text), delimiter=delim))

    valid_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, r in enumerate(reader, start=2):
        norm = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        lokasi = norm.get("lokasi") or norm.get("kantor") or ""
        ruangan = norm.get("jenis ruangan") or norm.get("ruangan") or ""
        jml_str = norm.get("jumlah ac") or norm.get("jumlah") or "1"
        tgl_raw = (
            norm.get("tanggal cuci terakhir")
            or norm.get("terakhir dikerjakan")
            or ""
        )
        int_str = norm.get("interval (bulan)") or norm.get("interval") or "3"

        if not lokasi or not ruangan:
            errors.append(
                {"row": idx, "reason": "Kolom Lokasi dan Jenis Ruangan wajib diisi"}
            )
            continue

        parsed_last: date | None = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                parsed_last = datetime.strptime(tgl_raw, fmt).date()
                break
            except ValueError:
                continue
        if parsed_last is None:
            errors.append(
                {
                    "row": idx,
                    "reason": (
                        f"Format Tanggal Cuci Terakhir '{tgl_raw}' tidak valid "
                        "(gunakan dd/mm/yyyy)"
                    ),
                }
            )
            continue

        digits_jml = re.sub(r"[^\d]", "", jml_str)
        digits_int = re.sub(r"[^\d]", "", int_str)
        jml_val = int(digits_jml) if digits_jml else 1
        int_val = int(digits_int) if digits_int else 3
        next_due = _add_interval_date(parsed_last, int_val, "bulan")

        valid_rows.append(
            {
                "row": idx,
                "lokasi": lokasi,
                "ruangan": ruangan,
                "jumlah_unit_manual": jml_val,
                "last_done_at": parsed_last.isoformat(),
                "interval_nilai": int_val,
                "interval_satuan": "bulan",
                "next_due_at": next_due.isoformat(),
                "kegiatan": "Cuci AC (cleaning)",
                "pelaksana_tipe": "Vendor",
                "pelaksana_nama": "Teknisi AC",
            }
        )

    return {
        "valid_count": len(valid_rows),
        "error_count": len(errors),
        "valid_rows": valid_rows,
        "errors": errors,
    }

