"""Endpoint Credential Manager: CRUD Terenkripsi Fernet, Reveal, & Izin per Jenis (B7)."""

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.security import (
    MASKED_SECRET_DISPLAY,
    decrypt_secret,
    encrypt_secret,
)
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.base import utcnow
from app.models.credential import Credential
from app.schemas.audit import record_audit_log
from app.schemas.credential import (
    CREDENTIAL_TYPE_PERMISSIONS,
    CredentialCreate,
    CredentialPageResponse,
    CredentialPublic,
    CredentialRevealResponse,
    CredentialUpdate,
    can_user_access_credential_type,
    default_roles_for_type,
    is_admin_only_type,
    resolve_canonical_type,
)

router = APIRouter()

CRD_CODE_PATTERN = re.compile(r"^CRD-(\d+)$")


def generate_next_credential_code(session: Session) -> str:
    """Menghasilkan kode otomatis CRD-001, CRD-002, dst."""
    existing = session.exec(
        select(Credential.kode_kredensial).where(col(Credential.kode_kredensial).like("CRD-%"))
    ).all()
    max_num = 0
    for code in existing:
        match = CRD_CODE_PATTERN.match(code.strip().upper())
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"CRD-{max_num + 1:03d}"


def _find_credential(session: Session, identifier: str) -> Credential:
    cleaned = identifier.strip()
    row: Credential | None = None
    if cleaned.isdigit():
        row = session.get(Credential, int(cleaned))
    if row is None:
        row = session.exec(
            select(Credential).where(func.lower(Credential.kode_kredensial) == cleaned.lower())
        ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kredensial tidak ditemukan",
        )
    return row


def _enforce_type_permission(
    user_role: str,
    jenis_kredensial: str,
    allowed_roles: list[str] | None = None,
    action_label: str = "mengakses",
) -> None:
    """Menolak akses dengan HTTP 403 bila peran tidak diizinkan untuk jenis kredensial tersebut."""
    if not can_user_access_credential_type(user_role, jenis_kredensial, allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Peran '{user_role}' tidak memiliki izin untuk {action_label} "
                f"kredensial jenis '{jenis_kredensial}'"
            ),
        )


def _compute_credential_summary(
    all_rows: list[Credential],
    viewer_role: str,
) -> tuple[dict[str, int], dict[str, Any]]:
    total_all = len(all_rows)
    admin_only_count = sum(
        1
        for r in all_rows
        if is_admin_only_type(r.jenis_kredensial) or r.allowed_roles == ["Administrator"]
    )
    operational_count = total_all - admin_only_count
    revealable_count = sum(
        1
        for r in all_rows
        if can_user_access_credential_type(
            viewer_role,
            r.jenis_kredensial,
            r.allowed_roles,
        )
    )

    tab_counts: dict[str, int] = {
        "Semua": total_all,
        "all": total_all,
        "Khusus Admin": admin_only_count,
        "Operasional": operational_count,
        "Website & Aplikasi": 0,
        "Perangkat": 0,
        "Akun Online": 0,
    }
    for r in all_rows:
        tab_counts[r.jenis_kredensial] = tab_counts.get(r.jenis_kredensial, 0) + 1
        j_low = (r.jenis_kredensial or "").lower()
        if j_low in ("aplikasi", "domain / dns", "cloud / vps"):
            tab_counts["Website & Aplikasi"] += 1
        elif j_low in ("email", "lainnya"):
            tab_counts["Akun Online"] += 1
        else:
            tab_counts["Perangkat"] += 1

    summary: dict[str, Any] = {
        "total": total_all,
        "total_kredensial": total_all,
        "khusus_admin": admin_only_count,
        "operasional": operational_count,
        "dapat_dibuka": revealable_count,
        "terenkripsi": total_all,
    }
    return tab_counts, summary


@router.get("/config", response_model=dict[str, Any])
def get_credential_config(_: CurrentUserDep) -> dict[str, Any]:
    """Mengembalikan konfigurasi jenis kredensial dan matriks izin peran."""
    return {
        "types": list(CREDENTIAL_TYPE_PERMISSIONS.keys()),
        "permissions": CREDENTIAL_TYPE_PERMISSIONS,
        "admin_only_types": [
            k for k, roles in CREDENTIAL_TYPE_PERMISSIONS.items() if roles == ["Administrator"]
        ],
    }


@router.get("", response_model=CredentialPageResponse)
def list_credentials(
    session: SessionDep,
    current_user: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tab: str | None = Query(default=None),
    jenis: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    level_akses: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="asc"),
) -> CredentialPageResponse:
    """Mengambil daftar kredensial berhalaman (password selalu disamarkan)."""
    all_rows = list(
        session.exec(select(Credential).order_by(col(Credential.kode_kredensial).asc())).all()
    )
    tab_counts, summary = _compute_credential_summary(all_rows, current_user.role)

    all_public = [CredentialPublic.from_model(r, viewer_role=current_user.role) for r in all_rows]
    filtered = all_public

    keyword = (search or q or "").strip().lower()
    if keyword:
        filtered = [
            i
            for i in filtered
            if keyword in i.kode_kredensial.lower()
            or keyword in i.nama_layanan.lower()
            or keyword in i.jenis_kredensial.lower()
            or keyword in i.jenis_label.lower()
            or keyword in i.username.lower()
            or keyword in i.ip_address.lower()
            or keyword in i.target.lower()
            or keyword in i.lokasi.lower()
            or keyword in i.catatan.lower()
        ]

    active_tab = (tab or jenis or kategori or "").strip().lower()
    if active_tab and active_tab not in ("semua", "all"):
        if active_tab in ("khusus admin", "admin"):
            filtered = [i for i in filtered if i.is_admin_only]
        elif active_tab == "operasional":
            filtered = [i for i in filtered if not i.is_admin_only]
        elif active_tab in ("website & aplikasi", "website"):
            filtered = [i for i in filtered if i.jenis_key == "website"]
        elif active_tab == "perangkat":
            filtered = [i for i in filtered if i.jenis_key == "perangkat"]
        elif active_tab in ("akun online", "akun"):
            filtered = [i for i in filtered if i.jenis_key == "akun"]
        else:
            filtered = [i for i in filtered if i.jenis_kredensial.lower() == active_tab]

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        loc_clean = lokasi.strip().lower()
        filtered = [i for i in filtered if i.lokasi.lower() == loc_clean]

    if level_akses and level_akses.strip().lower() not in ("semua", "all", ""):
        lvl_clean = level_akses.strip().lower()
        filtered = [i for i in filtered if i.level_akses.lower() == lvl_clean]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        filtered = [i for i in filtered if i.status.lower() == st_clean]

    if sort_by and sort_by.strip():
        s_key = sort_by.strip()
        rev = (sort_dir or "asc").strip().lower() == "desc"
        filtered.sort(
            key=lambda i: str(getattr(i, s_key, "") or "").lower(),
            reverse=rev,
        )

    total = len(filtered)
    paged = filtered[page_params.offset : page_params.offset + page_params.page_size]

    return CredentialPageResponse(
        items=paged,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=summary,
    )


@router.get("/{identifier}", response_model=CredentialPublic)
def get_credential_detail(
    identifier: str,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CredentialPublic:
    """Mengambil detail satu kredensial (password tetap disamarkan)."""
    row = _find_credential(session, identifier)
    return CredentialPublic.from_model(row, viewer_role=current_user.role)


def _perform_reveal(
    identifier: str,
    session: Session,
    current_user: Any,
) -> CredentialRevealResponse:
    row = _find_credential(session, identifier)
    _enforce_type_permission(
        current_user.role,
        row.jenis_kredensial,
        row.allowed_roles,
        action_label="membuka (reveal)",
    )
    try:
        plain_pwd = decrypt_secret(row.password_encrypted)
        plain_extra = (
            decrypt_secret(row.secret_extra_encrypted) if row.secret_extra_encrypted else ""
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kredensial tidak dapat didekripsi",
        ) from exc

    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=getattr(current_user, "full_name", current_user.username),
        role=current_user.role,
        aksi="Reveal Kredensial",
        modul="Kredensial",
        target_id=row.kode_kredensial,
        detail=f"Membuka password kredensial '{row.nama_layanan}' ({row.jenis_kredensial})",
        level_risiko="Tinggi",
    )

    return CredentialRevealResponse(
        id=row.id or 0,
        kode_kredensial=row.kode_kredensial,
        nama_layanan=row.nama_layanan,
        jenis_kredensial=row.jenis_kredensial,
        username=row.username,
        password=plain_pwd,
        secret=plain_pwd,
        value=plain_pwd,
        secret_extra=plain_extra,
        revealed_by=current_user.username,
    )


@router.post("/{identifier}/reveal", response_model=CredentialRevealResponse)
def reveal_credential_post(
    identifier: str,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CredentialRevealResponse:
    """Mendekripsi dan menampilkan password kredensial bila peran diizinkan (POST)."""
    return _perform_reveal(identifier, session, current_user)


@router.get(
    "/{identifier}/reveal",
    response_model=CredentialRevealResponse,
    include_in_schema=False,
)
def reveal_credential_get(
    identifier: str,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CredentialRevealResponse:
    """Mendekripsi dan menampilkan password kredensial bila peran diizinkan (GET alias)."""
    return _perform_reveal(identifier, session, current_user)


@router.post("", response_model=CredentialPublic, status_code=status.HTTP_201_CREATED)
def create_credential(
    payload: CredentialCreate,
    session: SessionDep,
    current_user: EditorUserDep,
) -> CredentialPublic:
    """Membuat kredensial baru dengan mengenkripsi password menggunakan Fernet."""
    _enforce_type_permission(
        current_user.role,
        payload.jenis_kredensial,
        payload.allowed_roles,
        action_label="membuat",
    )

    if payload.kode_kredensial and payload.kode_kredensial.strip():
        final_code = payload.kode_kredensial.strip().upper()
        dup = session.exec(
            select(Credential).where(func.lower(Credential.kode_kredensial) == final_code.lower())
        ).first()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Kode kredensial '{final_code}' sudah terdaftar",
            )
    else:
        final_code = generate_next_credential_code(session)

    encrypted_pwd = encrypt_secret(payload.password)
    encrypted_extra = encrypt_secret(payload.secret_extra) if payload.secret_extra else ""

    row = Credential(
        kode_kredensial=final_code,
        nama_layanan=payload.nama_layanan,
        jenis_kredensial=payload.jenis_kredensial,
        lokasi=payload.lokasi,
        id_aset=payload.id_aset,
        ip_address=payload.ip_address.strip(),
        port=str(payload.port).strip(),
        url_akses=payload.url_akses.strip(),
        username=payload.username.strip(),
        password_encrypted=encrypted_pwd,
        secret_extra_encrypted=encrypted_extra,
        level_akses=payload.level_akses or "Administrator",
        allowed_roles=payload.allowed_roles or default_roles_for_type(payload.jenis_kredensial),
        status=payload.status.strip(),
        terakhir_diubah_oleh=current_user.username,
        catatan=payload.catatan.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return CredentialPublic.from_model(row, viewer_role=current_user.role)


def _apply_credential_update(
    identifier: str,
    payload: CredentialUpdate,
    session: Session,
    current_user: Any,
) -> CredentialPublic:
    row = _find_credential(session, identifier)
    _enforce_type_permission(
        current_user.role,
        row.jenis_kredensial,
        row.allowed_roles,
        action_label="mengubah",
    )

    data = payload.model_dump(exclude_unset=True)
    for alias_name in ("nama_perangkat", "induk"):
        if alias_name in data and "nama_layanan" not in data:
            data["nama_layanan"] = data.pop(alias_name)
        else:
            data.pop(alias_name, None)

    for alias_type in ("kategori", "jenis_key", "jenis_label"):
        if alias_type in data and "jenis_kredensial" not in data:
            data["jenis_kredensial"] = data.pop(alias_type)
        else:
            data.pop(alias_type, None)

    if "peran" in data and "level_akses" not in data:
        data["level_akses"] = data.pop("peran")
    else:
        data.pop("peran", None)

    if "target" in data:
        t_val = (data.pop("target") or "").strip()
        if "http" in t_val.lower() or "/" in t_val:
            data["url_akses"] = t_val
        else:
            data["ip_address"] = t_val[:80]

    if "jenis_kredensial" in data and data["jenis_kredensial"] is not None:
        try:
            new_type = resolve_canonical_type(str(data["jenis_kredensial"]))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        _enforce_type_permission(
            current_user.role,
            new_type,
            action_label="mengubah ke",
        )
        row.jenis_kredensial = new_type
        if is_admin_only_type(new_type):
            row.allowed_roles = ["Administrator"]
            row.level_akses = "Administrator"
        elif "allowed_roles" not in data:
            row.allowed_roles = default_roles_for_type(new_type)
        data.pop("jenis_kredensial", None)

    new_plain_pwd = data.pop("password", None) or data.pop("secret", None)
    if (
        new_plain_pwd is not None
        and new_plain_pwd.strip()
        and new_plain_pwd.strip() != MASKED_SECRET_DISPLAY
    ):
        row.password_encrypted = encrypt_secret(new_plain_pwd)

    new_extra = data.pop("secret_extra", None)
    if new_extra is not None and new_extra.strip() != MASKED_SECRET_DISPLAY:
        row.secret_extra_encrypted = encrypt_secret(new_extra) if new_extra.strip() else ""

    if "port" in data and data["port"] is not None:
        row.port = str(data.pop("port")).strip()

    for key, val in data.items():
        if key in ("id", "kode_kredensial", "created_at") or val is None:
            continue
        if hasattr(row, key):
            setattr(row, key, val.strip() if isinstance(val, str) else val)

    row.terakhir_diubah_oleh = current_user.username
    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return CredentialPublic.from_model(row, viewer_role=current_user.role)


@router.put("/{identifier}", response_model=CredentialPublic)
def update_credential_put(
    identifier: str,
    payload: CredentialUpdate,
    session: SessionDep,
    current_user: EditorUserDep,
) -> CredentialPublic:
    """Memperbarui kredensial (PUT)."""
    return _apply_credential_update(identifier, payload, session, current_user)


@router.patch("/{identifier}", response_model=CredentialPublic)
def update_credential_patch(
    identifier: str,
    payload: CredentialUpdate,
    session: SessionDep,
    current_user: EditorUserDep,
) -> CredentialPublic:
    """Memperbarui sebagian data kredensial (PATCH)."""
    return _apply_credential_update(identifier, payload, session, current_user)


@router.delete("/{identifier}")
def delete_credential(
    identifier: str,
    session: SessionDep,
    _: AdminUserDep,
) -> dict[str, Any]:
    """Menghapus kredensial (hanya Administrator)."""
    row = _find_credential(session, identifier)
    deleted_code = row.kode_kredensial
    deleted_id = row.id
    session.delete(row)
    session.commit()
    return {"status": "ok", "id": deleted_id, "kode_kredensial": deleted_code}
