"""Endpoint Audit Log: daftar berhalaman, filter, ringkasan, dan pencatatan (B8)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import col, select

from app.deps import CurrentUserDep, PageParamsDep, SessionDep
from app.models.audit import AuditLog
from app.schemas.audit import (
    AuditLogCreate,
    AuditLogPageResponse,
    AuditLogPublic,
    record_audit_log,
)

router = APIRouter()


def _compute_audit_summary(
    all_rows: list[AuditLog],
) -> tuple[dict[str, int], dict[str, Any]]:
    total = len(all_rows)
    tinggi_count = sum(
        1 for r in all_rows if r.level_risiko.lower() in ("tinggi", "kritis")
    )
    sedang_count = sum(1 for r in all_rows if r.level_risiko.lower() == "sedang")
    rendah_count = sum(1 for r in all_rows if r.level_risiko.lower() == "rendah")
    gagal_count = sum(
        1 for r in all_rows if r.status.lower() in ("gagal", "ditolak")
    )
    reveal_count = sum(1 for r in all_rows if "reveal" in r.aksi.lower())

    tab_counts: dict[str, int] = {
        "Semua": total,
        "all": total,
        "Risiko Tinggi": tinggi_count,
        "Reveal": reveal_count,
        "Gagal": gagal_count,
    }
    for r in all_rows:
        tab_counts[r.modul] = tab_counts.get(r.modul, 0) + 1

    summary: dict[str, Any] = {
        "total": total,
        "total_log": total,
        "risiko_tinggi": tinggi_count,
        "risiko_sedang": sedang_count,
        "risiko_rendah": rendah_count,
        "akses_kredensial": reveal_count,
        "aktivitas_gagal": gagal_count,
    }
    return tab_counts, summary


@router.get("", response_model=AuditLogPageResponse)
def list_audit_logs(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    modul: str | None = Query(default=None),
    aksi: str | None = Query(default=None),
    username: str | None = Query(default=None),
    level_risiko: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
) -> AuditLogPageResponse:
    """Mengambil daftar Audit Log berhalaman (diurutkan dari yang terbaru)."""
    all_rows = list(
        session.exec(
            select(AuditLog).order_by(
                col(AuditLog.created_at).desc(),
                col(AuditLog.id).desc(),
            )
        ).all()
    )
    tab_counts, summary = _compute_audit_summary(all_rows)
    all_public = [AuditLogPublic.from_model(r) for r in all_rows]

    filtered = all_public

    keyword = (search or q or "").strip().lower()
    if keyword:
        filtered = [
            i
            for i in filtered
            if keyword in i.kode_audit.lower()
            or keyword in i.username.lower()
            or keyword in i.nama_pengguna.lower()
            or keyword in i.aksi.lower()
            or keyword in i.modul.lower()
            or keyword in i.target_id.lower()
            or keyword in i.detail.lower()
        ]

    if modul and modul.strip().lower() not in ("semua", "all", ""):
        m_clean = modul.strip().lower()
        if m_clean == "risiko tinggi":
            filtered = [
                i for i in filtered if i.level_risiko.lower() in ("tinggi", "kritis")
            ]
        elif m_clean == "reveal":
            filtered = [i for i in filtered if "reveal" in i.aksi.lower()]
        elif m_clean == "gagal":
            filtered = [
                i for i in filtered if i.status.lower() in ("gagal", "ditolak")
            ]
        else:
            filtered = [i for i in filtered if i.modul.lower() == m_clean]

    if aksi and aksi.strip().lower() not in ("semua", "all", ""):
        a_clean = aksi.strip().lower()
        filtered = [i for i in filtered if a_clean in i.aksi.lower()]

    if username and username.strip().lower() not in ("semua", "all", ""):
        u_clean = username.strip().lower()
        filtered = [i for i in filtered if i.username.lower() == u_clean]

    if level_risiko and level_risiko.strip().lower() not in ("semua", "all", ""):
        r_clean = level_risiko.strip().lower()
        filtered = [i for i in filtered if i.level_risiko.lower() == r_clean]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        s_clean = status_filter.strip().lower()
        filtered = [i for i in filtered if i.status.lower() == s_clean]

    total = len(filtered)
    paged = filtered[page_params.offset : page_params.offset + page_params.page_size]

    return AuditLogPageResponse(
        items=paged,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=summary,
    )


@router.get("/{identifier}", response_model=AuditLogPublic)
def get_audit_log_detail(
    identifier: str,
    session: SessionDep,
    _: CurrentUserDep,
) -> AuditLogPublic:
    """Mengambil detail satu log audit berdasarkan ID atau kode_audit."""
    cleaned = identifier.strip()
    row: AuditLog | None = None
    if cleaned.isdigit():
        row = session.get(AuditLog, int(cleaned))
    if row is None:
        row = session.exec(
            select(AuditLog).where(
                func.lower(AuditLog.kode_audit) == cleaned.lower()
            )
        ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log audit tidak ditemukan",
        )
    return AuditLogPublic.from_model(row)


@router.post("", response_model=AuditLogPublic, status_code=status.HTTP_201_CREATED)
def create_audit_log_entry(
    payload: AuditLogCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> AuditLogPublic:
    """Mencatat aktivitas baru ke tabel audit_logs."""
    row = record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=current_user.full_name,
        role=current_user.role,
        aksi=payload.aksi,
        modul=payload.modul,
        target_id=payload.target_id,
        detail=payload.detail,
        level_risiko=payload.level_risiko,
        status=payload.status,
        ip_address=payload.ip_address,
    )
    return AuditLogPublic.from_model(row)

