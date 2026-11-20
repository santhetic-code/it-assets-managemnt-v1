"""Endpoint Audit Log: khusus Administrator, filter, penggabungan xN, banner 24j, & export CSV."""

import csv
import io
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from sqlalchemy import func
from sqlmodel import col, select

from app.deps import AdminUserDep, PageParamsDep, SessionDep
from app.models.audit import AuditLog
from app.models.base import utcnow
from app.schemas.audit import (
    WIB_TZ,
    AuditLogCreate,
    AuditLogPageResponse,
    AuditLogPublic,
    compute_audit_severity,
    format_action_label,
    normalize_action_key,
    record_audit_log,
)

router = APIRouter()

_CSV_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_cell(value: Any) -> str:
    """Anti CSV-injection: awali tanda petik tunggal bila sel diawali =, +, -, @, tab, atau CR."""
    text = "" if value is None else str(value)
    stripped = text.lstrip(" ")
    if stripped and stripped[0] in _CSV_INJECTION_PREFIXES:
        return "'" + text
    return text


def _ensure_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _is_login_success(row: AuditLog) -> bool:
    key = normalize_action_key(row.aksi)
    return key in ("login", "login_berhasil") and row.status.strip().lower() in (
        "sukses",
        "berhasil",
    )


def _resolve_period_bounds_utc(
    periode: str | None,
    date_from: str | None,
    date_to: str | None,
    now_utc: datetime | None = None,
) -> tuple[datetime | None, datetime | None]:
    """Menghitung rentang waktu UTC berdasarkan periode kalender Asia/Jakarta (WIB)."""
    now = _ensure_utc(now_utc or utcnow())
    now_wib = now.astimezone(WIB_TZ)
    p = (periode or "").strip().lower()

    if p in ("hari_ini", "hari ini", "today"):
        start_wib = datetime.combine(now_wib.date(), time.min, tzinfo=WIB_TZ)
        return start_wib.astimezone(UTC), None
    if p in ("7_hari", "7 hari", "7d"):
        start_wib = datetime.combine(
            now_wib.date() - timedelta(days=6), time.min, tzinfo=WIB_TZ
        )
        return start_wib.astimezone(UTC), None
    if p in ("30_hari", "30 hari", "30d"):
        start_wib = datetime.combine(
            now_wib.date() - timedelta(days=29), time.min, tzinfo=WIB_TZ
        )
        return start_wib.astimezone(UTC), None

    start_utc: datetime | None = None
    end_utc: datetime | None = None
    if date_from and date_from.strip():
        try:
            d_from = date.fromisoformat(date_from.strip()[:10])
            start_utc = datetime.combine(d_from, time.min, tzinfo=WIB_TZ).astimezone(UTC)
        except ValueError:
            pass
    if date_to and date_to.strip():
        try:
            d_to = date.fromisoformat(date_to.strip()[:10])
            end_utc = datetime.combine(d_to, time.max, tzinfo=WIB_TZ).astimezone(UTC)
        except ValueError:
            pass
    return start_utc, end_utc


def group_audit_events(
    items: list[AuditLogPublic], window_seconds: int = 60
) -> list[AuditLogPublic]:
    """Gabungkan kejadian berurutan dengan pelaku + aksi + target sama dalam 60 detik."""
    if not items:
        return []

    grouped: list[AuditLogPublic] = []
    # items sudah urut terbaru -> terlama
    for item in items:
        item_dt = _ensure_utc(datetime.fromisoformat(item.timestamp))
        item_key = (
            item.username.strip().lower(),
            normalize_action_key(item.aksi),
            item.target_id.strip().lower(),
        )
        merged = False
        for prev in reversed(grouped):
            prev_dt = _ensure_utc(datetime.fromisoformat(prev.timestamp))
            if abs((prev_dt - item_dt).total_seconds()) > window_seconds:
                # Karena terurut menurun, item lebih awal di grouped pasti lebih jauh lagi
                break
            prev_key = (
                prev.username.strip().lower(),
                normalize_action_key(prev.aksi),
                prev.target_id.strip().lower(),
            )
            if prev_key == item_key:
                prev.group_count += 1
                prev.grouped_ids.append(item.kode_audit)
                prev.grouped_timestamps.extend(item.grouped_timestamps)
                merged = True
                break
        if not merged:
            grouped.append(item.model_copy(deep=True))
    return grouped


def _build_warning_banner(
    all_rows: list[AuditLog], now_utc: datetime | None = None
) -> dict[str, Any]:
    """Menyusun data banner merah bila ada kejadian Peringatan dalam 24 jam terakhir."""
    cutoff = _ensure_utc(now_utc or utcnow()) - timedelta(hours=24)
    recent_warnings = [
        r
        for r in all_rows
        if compute_audit_severity(r.aksi) == "Peringatan"
        and _ensure_utc(r.created_at) >= cutoff
    ]
    if not recent_warnings:
        return {"visible": False, "count": 0, "summary": ""}

    action_counts: dict[str, int] = {}
    for r in recent_warnings:
        lbl = format_action_label(r.aksi).lower()
        action_counts[lbl] = action_counts.get(lbl, 0) + 1

    parts = [f"{lbl} ({cnt}×)" if cnt > 1 else lbl for lbl, cnt in action_counts.items()]
    summary_text = (
        f"{len(recent_warnings)} peringatan dalam 24 jam terakhir: "
        + ", ".join(parts[:3])
    )
    return {
        "visible": True,
        "count": len(recent_warnings),
        "summary": summary_text,
    }


def _compute_audit_summary(
    all_rows: list[AuditLog],
) -> tuple[dict[str, int], dict[str, Any]]:
    total = len(all_rows)
    peringatan_count = sum(
        1 for r in all_rows if compute_audit_severity(r.aksi) == "Peringatan"
    )
    penting_count = sum(
        1 for r in all_rows if compute_audit_severity(r.aksi) == "Penting"
    )
    info_count = total - peringatan_count - penting_count
    gagal_count = sum(1 for r in all_rows if r.status.lower() in ("gagal", "ditolak"))
    reveal_count = sum(1 for r in all_rows if "reveal" in r.aksi.lower())

    tab_counts: dict[str, int] = {
        "Semua": total,
        "all": total,
        "Peringatan": peringatan_count,
        "Penting": penting_count,
        "Info": info_count,
        "Risiko Tinggi": peringatan_count,
        "Reveal": reveal_count,
        "Gagal": gagal_count,
    }
    for r in all_rows:
        tab_counts[r.modul] = tab_counts.get(r.modul, 0) + 1

    summary: dict[str, Any] = {
        "total": total,
        "total_log": total,
        "peringatan": peringatan_count,
        "penting": penting_count,
        "info": info_count,
        "risiko_tinggi": peringatan_count,
        "risiko_sedang": penting_count,
        "risiko_rendah": info_count,
        "akses_kredensial": reveal_count,
        "aktivitas_gagal": gagal_count,
    }
    return tab_counts, summary


def _filter_audit_rows(
    all_rows: list[AuditLog],
    *,
    search: str | None = None,
    tingkat: str | None = None,
    modul: str | None = None,
    aksi: str | None = None,
    pelaku: str | None = None,
    periode: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    hide_login_success: bool = False,
    status_filter: str | None = None,
) -> list[AuditLog]:
    filtered = all_rows

    if hide_login_success:
        filtered = [r for r in filtered if not _is_login_success(r)]

    start_utc, end_utc = _resolve_period_bounds_utc(periode, date_from, date_to)
    if start_utc is not None:
        filtered = [r for r in filtered if _ensure_utc(r.created_at) >= start_utc]
    if end_utc is not None:
        filtered = [r for r in filtered if _ensure_utc(r.created_at) <= end_utc]

    if modul and modul.strip().lower() not in ("semua", "semua modul", "all", ""):
        m_clean = modul.strip().lower()
        if m_clean == "risiko tinggi":
            filtered = [
                r for r in filtered if compute_audit_severity(r.aksi) == "Peringatan"
            ]
        elif m_clean == "reveal":
            filtered = [r for r in filtered if "reveal" in r.aksi.lower()]
        elif m_clean == "gagal":
            filtered = [
                r for r in filtered if r.status.lower() in ("gagal", "ditolak")
            ]
        else:
            filtered = [r for r in filtered if r.modul.strip().lower() == m_clean]

    if pelaku and pelaku.strip().lower() not in ("semua", "semua pelaku", "all", ""):
        p_clean = pelaku.strip().lower()
        filtered = [
            r
            for r in filtered
            if r.username.strip().lower() == p_clean
            or r.nama_pengguna.strip().lower() == p_clean
        ]

    if aksi and aksi.strip().lower() not in ("semua", "all", ""):
        a_clean = aksi.strip().lower()
        filtered = [
            r
            for r in filtered
            if a_clean in r.aksi.lower()
            or a_clean in format_action_label(r.aksi).lower()
        ]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        s_clean = status_filter.strip().lower()
        filtered = [r for r in filtered if r.status.strip().lower() == s_clean]

    if search and search.strip():
        kw = search.strip().lower()
        filtered = [
            r
            for r in filtered
            if kw in r.kode_audit.lower()
            or kw in r.username.lower()
            or kw in r.nama_pengguna.lower()
            or kw in r.aksi.lower()
            or kw in format_action_label(r.aksi).lower()
            or kw in r.modul.lower()
            or kw in r.target_id.lower()
            or kw in r.detail.lower()
        ]

    if tingkat and tingkat.strip().lower() not in ("semua", "all", ""):
        t_clean = tingkat.strip().lower()
        filtered = [
            r for r in filtered if compute_audit_severity(r.aksi).lower() == t_clean
        ]

    return filtered


@router.get("", response_model=AuditLogPageResponse)
def list_audit_logs(
    session: SessionDep,
    _: AdminUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tingkat: str | None = Query(default=None),
    level: str | None = Query(default=None),
    tab: str | None = Query(default=None),
    modul: str | None = Query(default=None),
    aksi: str | None = Query(default=None),
    pelaku: str | None = Query(default=None),
    username: str | None = Query(default=None),
    periode: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    hide_login_success: bool = Query(default=False),
    level_risiko: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    group: bool = Query(default=True),
) -> AuditLogPageResponse:
    """Mengambil daftar Audit Log khusus Administrator dengan filter, tab tingkat, & grup xN."""
    all_rows = list(
        session.exec(
            select(AuditLog).order_by(
                col(AuditLog.created_at).desc(),
                col(AuditLog.id).desc(),
            )
        ).all()
    )

    _all_tab_counts, summary = _compute_audit_summary(all_rows)
    warning_banner = _build_warning_banner(all_rows)
    modules_opts = sorted({r.modul.strip() for r in all_rows if r.modul.strip()})
    actors_opts = sorted({r.username.strip() for r in all_rows if r.username.strip()})

    eff_search = search or q
    eff_pelaku = pelaku or username
    eff_tingkat = tingkat or level or tab
    if not eff_tingkat and level_risiko:
        legacy_map = {
            "tinggi": "Peringatan",
            "kritis": "Peringatan",
            "sedang": "Penting",
            "rendah": "Info",
        }
        eff_tingkat = legacy_map.get(level_risiko.strip().lower())

    # Hitung tab_counts pada hasil filter non-tingkat agar angka tab akurat terhadap filter aktif
    base_filtered = _filter_audit_rows(
        all_rows,
        search=eff_search,
        tingkat=None,
        modul=modul,
        aksi=aksi,
        pelaku=eff_pelaku,
        periode=periode,
        date_from=date_from,
        date_to=date_to,
        hide_login_success=hide_login_success,
        status_filter=status_filter,
    )
    tab_counts, _filtered_summary = _compute_audit_summary(base_filtered)

    filtered_rows = (
        [
            r
            for r in base_filtered
            if compute_audit_severity(r.aksi).lower() == eff_tingkat.strip().lower()
        ]
        if eff_tingkat and eff_tingkat.strip().lower() not in ("semua", "all", "")
        else base_filtered
    )

    public_items = [AuditLogPublic.from_model(r) for r in filtered_rows]
    display_items = (
        group_audit_events(public_items, window_seconds=60) if group else public_items
    )

    total = len(display_items)
    paged = display_items[
        page_params.offset : page_params.offset + page_params.page_size
    ]

    return AuditLogPageResponse(
        items=paged,
        total=total,
        raw_total=len(filtered_rows),
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=summary,
        warning_banner=warning_banner,
        filter_options={"modules": modules_opts, "actors": actors_opts},
    )


@router.get("/export")
def export_audit_logs_csv(
    request: Request,
    session: SessionDep,
    admin_user: AdminUserDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tingkat: str | None = Query(default=None),
    level: str | None = Query(default=None),
    tab: str | None = Query(default=None),
    modul: str | None = Query(default=None),
    aksi: str | None = Query(default=None),
    pelaku: str | None = Query(default=None),
    username: str | None = Query(default=None),
    periode: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    hide_login_success: bool = Query(default=False),
    status_filter: str | None = Query(default=None, alias="status"),
) -> Response:
    """Export Audit Log ke CSV mengikuti filter aktif, anti CSV-injection, & audit_diekspor."""
    all_rows = list(
        session.exec(
            select(AuditLog).order_by(
                col(AuditLog.created_at).desc(),
                col(AuditLog.id).desc(),
            )
        ).all()
    )
    filtered_rows = _filter_audit_rows(
        all_rows,
        search=search or q,
        tingkat=tingkat or level or tab,
        modul=modul,
        aksi=aksi,
        pelaku=pelaku or username,
        periode=periode,
        date_from=date_from,
        date_to=date_to,
        hide_login_success=hide_login_success,
        status_filter=status_filter,
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "ID Kejadian",
            "Waktu (WIB)",
            "Waktu (UTC)",
            "Pelaku",
            "Peran",
            "Modul",
            "Aksi",
            "Tingkat",
            "Target",
            "Hasil",
            "Alamat IP",
            "Perangkat",
            "Ringkasan",
        ]
    )
    for row in filtered_rows:
        pub = AuditLogPublic.from_model(row)
        writer.writerow(
            [
                sanitize_csv_cell(pub.kode_audit),
                sanitize_csv_cell(pub.waktu_wib),
                sanitize_csv_cell(pub.waktu_utc),
                sanitize_csv_cell(f"{pub.nama_pengguna} ({pub.username})"),
                sanitize_csv_cell(pub.role),
                sanitize_csv_cell(pub.modul),
                sanitize_csv_cell(pub.aksi_label),
                sanitize_csv_cell(pub.tingkat),
                sanitize_csv_cell(pub.target_id),
                sanitize_csv_cell(pub.hasil),
                sanitize_csv_cell(pub.ip_address),
                sanitize_csv_cell(pub.perangkat),
                sanitize_csv_cell(pub.detail),
            ]
        )

    # Catat event audit_diekspor (tingkat Penting)
    record_audit_log(
        session,
        username=admin_user.username,
        nama_pengguna=admin_user.full_name,
        role=admin_user.role,
        aksi="audit_diekspor",
        modul="Audit Log",
        target_id="audit_logs.csv",
        detail=f"Export CSV Audit Log ({len(filtered_rows)} kejadian)",
        status="Berhasil",
        request=request,
    )

    stamp = utcnow().astimezone(WIB_TZ).strftime("%Y%m%d_%H%M")
    return Response(
        content=buf.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="audit_log_{stamp}.csv"'},
    )


@router.get("/{identifier}", response_model=AuditLogPublic)
def get_audit_log_detail(
    identifier: str,
    session: SessionDep,
    _: AdminUserDep,
) -> AuditLogPublic:
    """Mengambil detail satu log audit (khusus Administrator)."""
    cleaned = identifier.strip()
    row: AuditLog | None = None
    if cleaned.isdigit():
        row = session.get(AuditLog, int(cleaned))
    if row is None:
        row = session.exec(
            select(AuditLog).where(func.lower(AuditLog.kode_audit) == cleaned.lower())
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
    request: Request,
    session: SessionDep,
    current_user: AdminUserDep,
) -> AuditLogPublic:
    """Mencatat aktivitas baru ke tabel audit_logs (append-only, khusus Administrator)."""
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
        user_agent=payload.user_agent,
        changes=payload.changes,
        request=request,
    )
    return AuditLogPublic.from_model(row)
