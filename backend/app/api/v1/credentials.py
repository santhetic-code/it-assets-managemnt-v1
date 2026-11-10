"""Endpoint Credential Manager: AES-256-GCM, 8 Jenis Dinamis, & Akses 2 Lapis di SQL WHERE."""

import re
import time
from datetime import UTC, timedelta
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Request, status
from sqlalchemy import and_, func, or_
from sqlmodel import Session, col, select

from app.core.security import (
    CURRENT_KEY_VERSION,
    MASKED_SECRET_DISPLAY,
    decrypt_secret,
    decrypt_secret_dict,
    encrypt_secret,
    encrypt_secret_dict,
    verify_password,
)
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.audit import AuditLog
from app.models.base import utcnow
from app.models.credential import (
    Credential,
    CredentialACL,
    CredentialType,
    Division,
    DivisionGrant,
    RoleTypePermission,
)
from app.models.ip_allocation import IPAllocation
from app.models.user import UserRole
from app.schemas.audit import record_audit_log
from app.schemas.credential import (
    CREDENTIAL_TYPE_PERMISSIONS,
    INITIAL_CREDENTIAL_TYPES,
    INITIAL_DIVISIONS,
    INITIAL_ROLE_MATRIX,
    ROLE_RANKS,
    CredentialCreate,
    CredentialPageResponse,
    CredentialPublic,
    CredentialRevealResponse,
    CredentialUpdate,
    can_user_access_credential_type,
    compute_nearest_expiry,
    default_roles_for_type,
    is_admin_only_type,
    map_legacy_type_to_code,
    normalize_legacy_division_and_rank,
    resolve_canonical_type,
)

router = APIRouter()
HTTP_422_STATUS = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
CRD_CODE_PATTERN = re.compile(r"^CRD-(\d+)$")

# B: Sesi Re-Autentikasi (TTL 5 menit = 300 detik) & Rate Limit Reveal (maks 20/menit/user)
_REAUTH_SESSIONS: dict[str, float] = {}
_REVEAL_RATE_BUCKETS: dict[str, list[float]] = {}
REAUTH_TTL_SECONDS = 300.0
REVEAL_RATE_LIMIT_PER_MIN = 20


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


def _ensure_credential_types_and_rules(
    session: Session,
) -> tuple[
    dict[str, CredentialType],
    dict[int, CredentialType],
    dict[str, Division],
    dict[int, Division],
]:
    """A & C: Pastikan 8 credential_types, divisions, role_type_permissions, & grants terisi."""
    types_list = list(
        session.exec(select(CredentialType).order_by(col(CredentialType.urutan).asc())).all()
    )
    if not types_list:
        for t_def in INITIAL_CREDENTIAL_TYPES:
            ct = CredentialType(
                kode=t_def["kode"],
                nama=t_def["nama"],
                ikon=t_def["ikon"],
                urutan=t_def["urutan"],
                schema_fields=t_def["schema"],
            )
            session.add(ct)
        session.commit()
        types_list = list(
            session.exec(select(CredentialType).order_by(col(CredentialType.urutan).asc())).all()
        )

    divs_list = list(session.exec(select(Division).order_by(col(Division.id).asc())).all())
    if not divs_list:
        for d_def in INITIAL_DIVISIONS:
            session.add(
                Division(
                    nama=d_def["nama"],
                    peer_access=d_def["peer_access"],
                    upward_min_rank=d_def["upward_min_rank"],
                )
            )
        session.commit()
        divs_list = list(session.exec(select(Division).order_by(col(Division.id).asc())).all())

    by_code = {t.kode: t for t in types_list}
    by_id = {t.id: t for t in types_list if t.id is not None}
    div_by_name = {d.nama: d for d in divs_list}
    div_by_id = {d.id: d for d in divs_list if d.id is not None}

    if session.exec(select(RoleTypePermission.id).limit(1)).first() is None:
        can_edit_roles = {
            "Owner",
            "Direktur",
            "General Manager",
            "SPV Operasional",
            "Lead IT",
            "IT Support",
            "Administrator",
            "Member",
        }
        can_del_roles = {"Owner", "Lead IT", "IT Support", "Administrator"}
        for role_name, type_map in INITIAL_ROLE_MATRIX.items():
            for t_code, level in type_map.items():
                ct_obj = by_code.get(t_code)
                if not ct_obj or ct_obj.id is None:
                    continue
                session.add(
                    RoleTypePermission(
                        role_id=role_name,
                        type_id=ct_obj.id,
                        can_view=level in ("full", "view"),
                        can_reveal=(level == "full"),
                        can_edit=(level == "full" and role_name in can_edit_roles),
                        can_delete=(level == "full" and role_name in can_del_roles),
                    )
                )
        session.commit()

    if session.exec(select(DivisionGrant.id).limit(1)).first() is None:
        opr_div = div_by_name.get("Operator & CS")
        kreatif_div = div_by_name.get("Kreatif")
        if opr_div and opr_div.id is not None:
            session.add(DivisionGrant(viewer_role_id="HRD", target_division_id=opr_div.id))
        if kreatif_div and kreatif_div.id is not None:
            session.add(
                DivisionGrant(viewer_role_id="Head Marketing", target_division_id=kreatif_div.id)
            )
        session.commit()

    # Sinkronkan baris Credential yang belum memiliki type_id / divisi_pemilik_id
    unsynced = session.exec(select(Credential).where(col(Credential.type_id).is_(None))).all()
    if unsynced:
        for r in unsynced:
            t_code = map_legacy_type_to_code(r.jenis_kredensial)
            ct_obj = by_code.get(t_code)
            if ct_obj:
                r.type_id = ct_obj.id
            if not r.nama:
                r.nama = r.nama_layanan
            if r.divisi_pemilik_id is None:
                div_name, s_rank, _ = normalize_legacy_division_and_rank(r.nama_layanan)
                if is_admin_only_type(r.jenis_kredensial):
                    div_name = "IT"
                    s_rank = 15
                d_obj = div_by_name.get(div_name) or div_by_name.get("Umum")
                if d_obj:
                    r.divisi_pemilik_id = d_obj.id
                r.subject_rank = s_rank
            session.add(r)
        session.commit()

    return by_code, by_id, div_by_name, div_by_id


def resolve_viewer_context(
    session: Session,
    user: Any,
    as_role: str | None = None,
    as_division: str | None = None,
) -> dict[str, Any]:
    """Menentukan konteks akses pengguna (mendukung fitur 'Lihat sebagai pengguna' Admin/Owner)."""
    _, _, div_by_name, div_by_id = _ensure_credential_types_and_rules(session)
    base_role = getattr(user, "jabatan", "") or getattr(user, "role", UserRole.VIEWER.value)
    is_real_admin = (
        getattr(user, "role", "") == UserRole.ADMINISTRATOR.value
        or getattr(user, "is_it_admin", False)
        or base_role in ("Owner", "Lead IT", "IT Support", "Administrator")
    )

    eff_role = (as_role or "").strip() if (as_role and is_real_admin) else base_role
    eff_rank = int(getattr(user, "rank", 0))
    if as_role and is_real_admin:
        eff_rank = ROLE_RANKS.get(eff_role, 0)
    elif eff_rank == 0 and eff_role in ROLE_RANKS:
        eff_rank = ROLE_RANKS[eff_role]

    eff_it_admin = eff_role in ("Lead IT", "IT Support", "Administrator") or (
        not as_role and bool(getattr(user, "is_it_admin", False))
    )

    eff_div_id: int | None = getattr(user, "division_id", None)
    if as_division and is_real_admin and as_division in div_by_name:
        eff_div_id = div_by_name[as_division].id
    elif eff_div_id is None or (as_role and is_real_admin):
        role_div_map = {
            "Owner": "Manajemen",
            "Direktur": "Manajemen",
            "General Manager": "Manajemen",
            "SPV Operasional": "Manajemen",
            "Lead IT": "IT",
            "IT Support": "IT",
            "Administrator": "IT",
            "HRD": "Senior & Cabang",
            "Staff Legal": "Senior & Cabang",
            "Head Marketing": "Senior & Cabang",
            "SPV Cilacap": "Senior & Cabang",
            "Staff Accounting": "Accounting",
            "Staff Operator & CS": "Operator & CS",
            "Staff Voucher": "Voucher",
            "Staff Kreatif": "Kreatif",
            "Programmer / QA": "Programmer / QA",
        }
        mapped_div = div_by_name.get(role_div_map.get(eff_role, "Umum"))
        eff_div_id = mapped_div.id if mapped_div else None

    div_obj = div_by_id.get(eff_div_id) if eff_div_id else None
    return {
        "username": getattr(user, "username", "anonymous"),
        "base_role": getattr(user, "role", UserRole.VIEWER.value),
        "role_id": eff_role,
        "rank": eff_rank,
        "division_id": eff_div_id,
        "division_name": div_obj.nama if div_obj else "Umum",
        "is_it_admin": eff_it_admin,
        "is_owner_or_it": eff_it_admin or eff_role == "Owner" or is_real_admin,
    }


def can_access_credential(
    session: Session,
    viewer_ctx: dict[str, Any],
    cred: Credential,
    action: str = "view",
) -> bool:
    """C: Algoritma 7 langkah canAccess(user, cred, action) (urutan ketat, deny menang)."""
    # 1. cred sudah dihapus -> tolak
    if cred.deleted_at is not None:
        return False

    role_id = viewer_ctx["role_id"]
    base_role = viewer_ctx["base_role"]
    user_rank = int(viewer_ctx["rank"])
    user_div_id = viewer_ctx["division_id"]
    is_it_admin = bool(viewer_ctx["is_it_admin"])
    username = str(viewer_ctx["username"])

    # 2. LAPIS 1: role_type_permissions[user.role][cred.type][action]
    rtp = session.exec(
        select(RoleTypePermission).where(
            and_(
                col(RoleTypePermission.type_id) == (cred.type_id or 0),
                col(RoleTypePermission.role_id).in_([role_id, base_role]),
            )
        )
    ).all()
    action_col_map = {
        "view": "can_view",
        "reveal": "can_reveal",
        "copy": "can_reveal",
        "edit": "can_edit",
        "delete": "can_delete",
    }
    perm_attr = action_col_map.get(action, "can_view")
    matched_rtp = next((p for p in rtp if p.role_id == role_id), rtp[0] if rtp else None)

    # Cek ACL entri untuk user/role/division
    acls = session.exec(
        select(CredentialACL).where(col(CredentialACL.credential_id) == (cred.id or 0))
    ).all()
    relevant_acls = [
        a
        for a in acls
        if action in (a.actions or [])
        and (
            (a.principal == "user" and a.principal_id == username)
            or (a.principal == "role" and a.principal_id in (role_id, base_role))
            or (a.principal == "division" and str(user_div_id) == a.principal_id)
        )
    ]

    # 3. credential_acl ada deny -> tolak (deny selalu menang)
    if any(a.effect == "deny" for a in relevant_acls):
        return False

    has_acl_allow = any(a.effect == "allow" for a in relevant_acls)
    lapis1_ok = (
        bool(getattr(matched_rtp, perm_attr, False))
        if matched_rtp
        else can_user_access_credential_type(base_role, cred.jenis_kredensial, cred.allowed_roles)
    )
    # Kompatibilitas per-entri allowed_roles khusus Admin
    if (
        not is_it_admin
        and role_id not in ("Owner", "Direktur", "General Manager")
        and (
            is_admin_only_type(cred.jenis_kredensial)
            or cred.allowed_roles == [UserRole.ADMINISTRATOR.value]
        )
    ):
        if role_id == UserRole.MEMBER.value:
            return False

    if not lapis1_ok and not has_acl_allow:
        return False

    # 4. user.is_it_admin -> izinkan
    if is_it_admin:
        return True

    # 5. credential_acl ada allow -> izinkan
    if has_acl_allow:
        return True

    # 6. user.rank < cred.min_view_rank -> tolak
    if user_rank < (cred.min_view_rank or 0):
        return False

    # 7. LAPIS 2: Lingkup Divisi & Tingkat
    div_obj = session.get(Division, cred.divisi_pemilik_id) if cred.divisi_pemilik_id else None
    peer_access = div_obj.peer_access if div_obj is not None else True
    upward_min_rank = div_obj.upward_min_rank if div_obj is not None else 20

    # 7a. Satu divisi & peer_access & user.rank >= cred.subject_rank
    if (
        user_div_id is not None
        and cred.divisi_pemilik_id == user_div_id
        and peer_access
        and user_rank >= (cred.subject_rank or 0)
    ):
        return True

    # 7b. Ada division_grants dari user (role atau divisi) ke divisi pemilik
    if cred.divisi_pemilik_id is not None:
        grants = session.exec(
            select(DivisionGrant).where(
                col(DivisionGrant.target_division_id) == cred.divisi_pemilik_id,
                or_(
                    col(DivisionGrant.type_id).is_(None),
                    col(DivisionGrant.type_id) == cred.type_id,
                ),
            )
        ).all()
        for g in grants:
            if g.viewer_role_id and g.viewer_role_id in (role_id, base_role):
                return True
            if g.viewer_division_id and g.viewer_division_id == user_div_id:
                return True

    # 7c. Atasan -> bawahan: user.rank > cred.subject_rank DAN user.rank >= divisi.upward_min_rank
    if user_rank > (cred.subject_rank or 0) and user_rank >= upward_min_rank:
        return True

    # Khusus divisi Umum (upward_min_rank == 0 & subject_rank == 0)
    if div_obj and div_obj.nama == "Umum" and user_rank >= (cred.subject_rank or 0):
        return True

    # 7d. Selain itu -> tolak
    return False


def _build_sql_access_where(
    session: Session,
    viewer_ctx: dict[str, Any],
) -> Any:
    """C & I: Membangun klausa SQL WHERE untuk filter akses 2 lapis langsung di database."""
    role_id = viewer_ctx["role_id"]
    base_role = viewer_ctx["base_role"]
    user_rank = int(viewer_ctx["rank"])
    user_div_id = viewer_ctx["division_id"]
    is_it_admin = bool(viewer_ctx["is_it_admin"])
    username = str(viewer_ctx["username"])

    not_deleted = col(Credential.deleted_at).is_(None)

    # Lapis 1: type_id yang memiliki can_view == True untuk role_id pengguna
    allowed_type_ids = list(
        session.exec(
            select(RoleTypePermission.type_id).where(
                col(RoleTypePermission.role_id) == role_id,
                col(RoleTypePermission.can_view).is_(True),
            )
        ).all()
    )
    if not allowed_type_ids and role_id != base_role:
        allowed_type_ids = list(
            session.exec(
                select(RoleTypePermission.type_id).where(
                    col(RoleTypePermission.role_id) == base_role,
                    col(RoleTypePermission.can_view).is_(True),
                )
            ).all()
        )

    # Cek ACL allow/deny di DB
    all_acls = session.exec(select(CredentialACL)).all()
    deny_cred_ids = {
        a.credential_id
        for a in all_acls
        if a.effect == "deny"
        and "view" in (a.actions or [])
        and (
            (a.principal == "user" and a.principal_id == username)
            or (a.principal == "role" and a.principal_id in (role_id, base_role))
            or (a.principal == "division" and str(user_div_id) == a.principal_id)
        )
    }
    allow_cred_ids = {
        a.credential_id
        for a in all_acls
        if a.effect == "allow"
        and "view" in (a.actions or [])
        and a.credential_id not in deny_cred_ids
        and (
            (a.principal == "user" and a.principal_id == username)
            or (a.principal == "role" and a.principal_id in (role_id, base_role))
            or (a.principal == "division" and str(user_div_id) == a.principal_id)
        )
    }

    conds: list[Any] = [not_deleted]
    if deny_cred_ids:
        conds.append(~col(Credential.id).in_(deny_cred_ids))

    lapis1_clause = (
        col(Credential.type_id).in_(allowed_type_ids)
        if allowed_type_ids
        else (col(Credential.id) == -1)
    )
    if allow_cred_ids:
        lapis1_clause = or_(lapis1_clause, col(Credential.id).in_(allow_cred_ids))
    conds.append(lapis1_clause)

    # Langkah 4: IT Admin lolos Lapis 2
    if is_it_admin:
        return and_(*conds)

    # Langkah 6 & 7: Lapis 2 di SQL
    divs = session.exec(select(Division)).all()
    grants = session.exec(select(DivisionGrant)).all()
    granted_div_ids = {
        g.target_division_id
        for g in grants
        if (g.viewer_role_id and g.viewer_role_id in (role_id, base_role))
        or (g.viewer_division_id and g.viewer_division_id == user_div_id)
    }

    div_clauses: list[Any] = []
    if allow_cred_ids:
        div_clauses.append(col(Credential.id).in_(allow_cred_ids))

    for d in divs:
        if d.id is None:
            continue
        d_sub: list[Any] = []
        # 7a: Peer access satu divisi
        if user_div_id == d.id and d.peer_access:
            d_sub.append(col(Credential.subject_rank) <= user_rank)
        # 7b: Division grant
        if d.id in granted_div_ids:
            d_sub.append(col(Credential.id).is_not(None))
        # 7c: Atasan -> bawahan
        if user_rank >= d.upward_min_rank:
            d_sub.append(col(Credential.subject_rank) < user_rank)
        # Divisi Umum
        if d.nama == "Umum":
            d_sub.append(col(Credential.subject_rank) <= user_rank)

        if d_sub:
            div_clauses.append(
                and_(
                    col(Credential.divisi_pemilik_id) == d.id,
                    col(Credential.min_view_rank) <= user_rank,
                    or_(*d_sub),
                )
            )

    # Entri tanpa divisi_pemilik_id (fallback kompatibilitas)
    div_clauses.append(
        and_(
            col(Credential.divisi_pemilik_id).is_(None),
            col(Credential.min_view_rank) <= user_rank,
            col(Credential.subject_rank) <= user_rank,
        )
    )

    conds.append(or_(*div_clauses))
    return and_(*conds)


@router.get("/config", response_model=dict[str, Any])
def get_credential_config(
    session: SessionDep,
    current_user: CurrentUserDep,
    as_role: str | None = Query(default=None),
) -> dict[str, Any]:
    """A, C, D: Mengembalikan 8 credential_types (schema JSON), divisi, matriks, & opsi PC/IP."""
    by_code, _, div_by_name, _ = _ensure_credential_types_and_rules(session)
    v_ctx = resolve_viewer_context(session, current_user, as_role=as_role)

    rtps = session.exec(
        select(RoleTypePermission).where(col(RoleTypePermission.role_id) == v_ctx["role_id"])
    ).all()
    perm_by_type_id = {p.type_id: p for p in rtps}

    types_payload: list[dict[str, Any]] = []
    for ct in sorted(by_code.values(), key=lambda x: x.urutan):
        p = perm_by_type_id.get(ct.id or 0)
        can_v = p.can_view if p else bool(v_ctx["is_it_admin"])
        can_r = p.can_reveal if p else bool(v_ctx["is_it_admin"])
        can_e = p.can_edit if p else bool(v_ctx["is_it_admin"])
        types_payload.append(
            {
                "id": ct.id,
                "kode": ct.kode,
                "nama": ct.nama,
                "ikon": ct.ikon,
                "urutan": ct.urutan,
                "schema": ct.schema_fields,
                "can_view": can_v,
                "can_reveal": can_r,
                "can_edit": can_e,
                "locked": not can_v,
            }
        )

    active_pc_assets = session.exec(
        select(Asset)
        .where(
            col(Asset.kategori).in_(["PC", "Laptop", "Server"]),
            col(Asset.deleted_at).is_(None),
        )
        .order_by(col(Asset.id_aset).asc())
    ).all()
    ip_by_asset = {
        r.id_aset: r.ip_address
        for r in session.exec(
            select(IPAllocation).where(col(IPAllocation.id_aset).is_not(None))
        ).all()
        if r.id_aset
    }
    pc_options: list[dict[str, Any]] = []
    for a_row in active_pc_assets:
        pemakai = a_row.pemakai_text or a_row.penanggung_jawab or a_row.nama_aset
        ip_val = ip_by_asset.get(a_row.id_aset) or a_row.ip_address or "—"
        div_n, s_rank, _ = normalize_legacy_division_and_rank(pemakai)
        if a_row.kategori.lower() == "server":
            div_n = "IT"
            s_rank = 15
        pc_options.append(
            {
                "id": a_row.id_aset,
                "asset_id": a_row.id_aset,
                "label": f"{a_row.id_aset} · {a_row.nama_aset} ({ip_val})",
                "ip_address": ip_val if ip_val != "—" else "",
                "pengguna": pemakai,
                "lokasi": a_row.lokasi,
                "divisi": div_n,
                "subject_rank": s_rank,
            }
        )

    return {
        "types": list(CREDENTIAL_TYPE_PERMISSIONS.keys()),
        "credential_types": types_payload,
        "divisions": [
            {
                "id": d.id,
                "nama": d.nama,
                "peer_access": d.peer_access,
                "upward_min_rank": d.upward_min_rank,
            }
            for d in div_by_name.values()
        ],
        "pc_ip_options": pc_options,
        "viewer_context": v_ctx,
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
    type_code: str | None = Query(default=None, alias="type"),
    jenis: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    divisi: str | None = Query(default=None),
    only_my_division: bool = Query(default=False),
    masa_berlaku: str | None = Query(default=None),
    card_filter: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    level_akses: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    as_role: str | None = Query(default=None),
    as_division: str | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="asc"),
) -> CredentialPageResponse:
    """E & I: Daftar kredensial berhalaman dengan filter akses 2 lapis di SQL WHERE."""
    by_code, by_id, div_by_name, div_by_id = _ensure_credential_types_and_rules(session)
    v_ctx = resolve_viewer_context(session, current_user, as_role=as_role, as_division=as_division)
    access_where = _build_sql_access_where(session, v_ctx)

    # I: Satu query terindeks GROUP BY type_id untuk menghitung jumlah per tile jenis
    type_counts_rows = (
        session.connection()
        .execute(
            select(col(Credential.type_id), func.count(col(Credential.id)))
            .where(access_where)
            .group_by(col(Credential.type_id))
        )
        .all()
    )
    counts_by_type_id = {int(tid or 0): int(cnt or 0) for tid, cnt in type_counts_rows if tid}
    total_accessible = sum(counts_by_type_id.values())

    now_utc = utcnow()
    soon_cutoff = now_utc + timedelta(days=30)
    old_pwd_cutoff = now_utc - timedelta(days=90)

    expiring_soon_count = (
        session.exec(
            select(func.count(col(Credential.id))).where(
                access_where,
                col(Credential.expired_at).is_not(None),
                col(Credential.expired_at) <= soon_cutoff,
            )
        ).one()
        or 0
    )
    old_password_count = (
        session.exec(
            select(func.count(col(Credential.id))).where(
                access_where,
                col(Credential.last_rotated_at) < old_pwd_cutoff,
            )
        ).one()
        or 0
    )

    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    revealed_today_count = (
        session.exec(
            select(func.count(col(AuditLog.id))).where(
                col(AuditLog.modul).in_(["Kredensial", "Credential Manager", "Security"]),
                col(AuditLog.aksi).ilike("%reveal%"),
                col(AuditLog.created_at) >= today_start,
            )
        ).one()
        or 0
        if v_ctx["is_owner_or_it"]
        else 0
    )

    rtps = session.exec(
        select(RoleTypePermission).where(col(RoleTypePermission.role_id) == v_ctx["role_id"])
    ).all()
    perm_by_type_id = {p.type_id: p for p in rtps}

    type_tiles: list[dict[str, Any]] = []
    tab_counts: dict[str, int] = {"Semua": total_accessible, "all": total_accessible}
    unlocked_types_count = 0

    for ct in sorted(by_code.values(), key=lambda x: x.urutan):
        p = perm_by_type_id.get(ct.id or 0)
        can_v = p.can_view if p else bool(v_ctx["is_it_admin"])
        cnt = counts_by_type_id.get(ct.id or 0, 0) if can_v else 0
        if can_v:
            unlocked_types_count += 1
        tab_counts[ct.kode] = cnt
        tab_counts[ct.nama] = cnt
        type_tiles.append(
            {
                "id": ct.id,
                "kode": ct.kode,
                "nama": ct.nama,
                "ikon": ct.ikon,
                "count": cnt,
                "locked": not can_v,
            }
        )

    # Query utama dengan filter di SQL WHERE (E: JANGAN mencari di data_rahasia/password_encrypted)
    stmt = select(Credential).where(access_where)

    keyword = (search or q or "").strip()
    if keyword:
        pat = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                col(Credential.kode_kredensial).ilike(pat),
                col(Credential.nama).ilike(pat),
                col(Credential.nama_layanan).ilike(pat),
                col(Credential.username).ilike(pat),
                col(Credential.ip_address).ilike(pat),
                col(Credential.url_akses).ilike(pat),
                col(Credential.lokasi).ilike(pat),
                col(Credential.catatan).ilike(pat),
            )
        )

    active_type = (type_code or tab or jenis or kategori or "").strip().lower()
    if active_type and active_type not in ("semua", "all"):
        mapped_code = map_legacy_type_to_code(active_type)
        if mapped_code in by_code and by_code[mapped_code].id is not None:
            stmt = stmt.where(col(Credential.type_id) == by_code[mapped_code].id)
        else:
            stmt = stmt.where(func.lower(Credential.jenis_kredensial) == active_type)

    if only_my_division and v_ctx["division_id"] is not None:
        stmt = stmt.where(col(Credential.divisi_pemilik_id) == v_ctx["division_id"])
    elif divisi and divisi.strip().lower() not in ("semua", "semua divisi", "all", ""):
        d_obj = next(
            (d for d in div_by_name.values() if d.nama.lower() == divisi.strip().lower()),
            None,
        )
        if d_obj and d_obj.id is not None:
            stmt = stmt.where(col(Credential.divisi_pemilik_id) == d_obj.id)

    if status_filter and status_filter.strip().lower() not in ("semua", "semua status", "all", ""):
        st_low = status_filter.strip().lower()
        if st_low == "kedaluwarsa":
            stmt = stmt.where(
                col(Credential.expired_at).is_not(None),
                col(Credential.expired_at) < now_utc,
            )
        else:
            stmt = stmt.where(func.lower(Credential.status) == st_low)

    eff_card = (card_filter or masa_berlaku or "").strip().lower()
    if eff_card in ("expiring", "segera kedaluwarsa", "<= 30 hari", "30_hari"):
        stmt = stmt.where(
            col(Credential.expired_at).is_not(None),
            col(Credential.expired_at) <= soon_cutoff,
        )
    elif eff_card in ("old_password", "password lama", "> 90 hari"):
        stmt = stmt.where(col(Credential.last_rotated_at) < old_pwd_cutoff)

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(Credential.lokasi) == lokasi.strip().lower())

    if level_akses and level_akses.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(Credential.level_akses) == level_akses.strip().lower())

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one() or 0

    is_desc = (sort_dir or "asc").strip().lower() == "desc"
    sort_col = col(Credential.nama) if sort_by == "nama" else col(Credential.kode_kredensial)
    stmt = stmt.order_by(
        sort_col.desc() if is_desc else sort_col.asc(),
        col(Credential.id).asc(),
    )

    rows = session.exec(stmt.offset(page_params.offset).limit(page_params.page_size)).all()

    items: list[CredentialPublic] = []
    for r in rows:
        t_obj = by_id.get(r.type_id or 0)
        d_obj = div_by_id.get(r.divisi_pemilik_id or 0)
        p_obj = perm_by_type_id.get(r.type_id or 0)
        can_rev = can_access_credential(session, v_ctx, r, action="reveal")
        can_ed = p_obj.can_edit if p_obj else bool(v_ctx["is_it_admin"])
        can_del = p_obj.can_delete if p_obj else bool(v_ctx["is_it_admin"])
        items.append(
            CredentialPublic.from_model(
                r,
                viewer_role=current_user.role,
                type_obj=t_obj,
                division_name=d_obj.nama if d_obj else "Umum",
                can_reveal_override=can_rev,
                can_edit_override=can_ed,
                can_delete_override=can_del,
            )
        )

    summary = {
        "total": total_accessible,
        "total_kredensial": total_accessible,
        "bisa_diakses": total_accessible,
        "segera_kedaluwarsa": expiring_soon_count,
        "password_lama": old_password_count,
        "dibuka_hari_ini": revealed_today_count,
        "unlocked_types_count": unlocked_types_count,
        "total_types_count": len(by_code),
        "dapat_dibuka": total_accessible,
        "terenkripsi": total_accessible,
    }

    return CredentialPageResponse(
        items=items,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        type_tiles=type_tiles,
        summary=summary,
        kpi=summary,
        viewer_context={
            **v_ctx,
            "unlocked_types_count": unlocked_types_count,
            "total_types_count": len(by_code),
            "badge_text": (
                f"Akses Anda: {v_ctx['role_id']} · {unlocked_types_count} dari {len(by_code)} jenis"
            ),
        },
    )


@router.post("/reauth")
def verify_credential_reauth(
    payload: dict[str, Any],
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    """B: Verifikasi ulang password akun yang sedang login (berlaku 5 menit)."""
    pwd = str(payload.get("password") or "").strip()
    if not pwd or not verify_password(pwd, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password akun tidak sesuai untuk membuka rahasia kredensial",
        )
    expires_at = time.time() + REAUTH_TTL_SECONDS
    _REAUTH_SESSIONS[current_user.username] = expires_at
    return {
        "verified": True,
        "expires_in_seconds": int(REAUTH_TTL_SECONDS),
    }


@router.get("/access-rules")
def get_access_rules_matrix(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    """D: Mengambil matriks peran x jenis (Lapis 1), aturan divisi (Lapis 2), dan daftar grants."""
    by_code, by_id, div_by_name, div_by_id = _ensure_credential_types_and_rules(session)
    v_ctx = resolve_viewer_context(session, current_user)
    if not v_ctx["is_owner_or_it"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya Owner dan IT Admin yang dapat membuka pengaturan Aturan Akses",
        )

    rtps = session.exec(select(RoleTypePermission)).all()
    matrix: dict[str, dict[str, str]] = {}
    for p in rtps:
        ct = by_id.get(p.type_id)
        if not ct:
            continue
        cell = "full" if (p.can_view and p.can_reveal) else ("view" if p.can_view else "none")
        matrix.setdefault(p.role_id, {})[ct.kode] = cell

    grants = session.exec(select(DivisionGrant)).all()
    grants_list = [
        {
            "id": g.id,
            "viewer_role_id": g.viewer_role_id or "",
            "viewer_division": div_by_id[g.viewer_division_id].nama
            if (g.viewer_division_id and g.viewer_division_id in div_by_id)
            else "",
            "target_division": div_by_id[g.target_division_id].nama
            if g.target_division_id in div_by_id
            else "",
        }
        for g in grants
    ]

    return {
        "roles": [
            "Owner",
            "Direktur",
            "General Manager",
            "SPV Operasional",
            "Lead IT",
            "IT Support",
            "HRD",
            "Head Marketing",
            "Staff Operator & CS",
            "Staff Accounting",
            "Staff Voucher",
            "Staff Kreatif",
            "Programmer / QA",
        ],
        "types": [
            {"id": t.id, "kode": t.kode, "nama": t.nama}
            for t in sorted(by_code.values(), key=lambda x: x.urutan)
        ],
        "matrix": matrix,
        "divisions": [
            {
                "id": d.id,
                "nama": d.nama,
                "peer_access": d.peer_access,
                "upward_min_rank": d.upward_min_rank,
                "is_sensitive": d.upward_min_rank >= 40,
            }
            for d in div_by_name.values()
        ],
        "grants": grants_list,
    }


@router.put("/access-rules")
def update_access_rules_matrix(
    payload: dict[str, Any],
    session: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    """D: Menyimpan perubahan matriks Lapis 1 atau divisi Lapis 2 & mencatat ke Audit Log."""
    by_code, _, div_by_name, _ = _ensure_credential_types_and_rules(session)
    v_ctx = resolve_viewer_context(session, current_user)
    if not v_ctx["is_owner_or_it"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya Owner dan IT Admin yang dapat mengubah Aturan Akses",
        )

    changes_log: list[str] = []
    if "matrix" in payload and isinstance(payload["matrix"], dict):
        for role_id, type_map in payload["matrix"].items():
            if not isinstance(type_map, dict):
                continue
            for t_code, new_mode in type_map.items():
                ct = by_code.get(t_code)
                if not ct or ct.id is None:
                    continue
                rtp = session.exec(
                    select(RoleTypePermission).where(
                        col(RoleTypePermission.role_id) == role_id,
                        col(RoleTypePermission.type_id) == ct.id,
                    )
                ).first()
                old_mode = (
                    "full"
                    if (rtp and rtp.can_view and rtp.can_reveal)
                    else ("view" if (rtp and rtp.can_view) else "none")
                )
                if old_mode != new_mode:
                    changes_log.append(f"{role_id}.{t_code}: {old_mode} -> {new_mode}")
                    if rtp is None:
                        rtp = RoleTypePermission(role_id=role_id, type_id=ct.id)
                    rtp.can_view = new_mode in ("full", "view")
                    rtp.can_reveal = new_mode == "full"
                    session.add(rtp)

    if "divisions" in payload and isinstance(payload["divisions"], list):
        for d_item in payload["divisions"]:
            d_obj = div_by_name.get(str(d_item.get("nama", "")))
            if not d_obj:
                continue
            new_peer = bool(d_item.get("peer_access", d_obj.peer_access))
            new_upward = int(d_item.get("upward_min_rank", d_obj.upward_min_rank))
            if d_obj.peer_access != new_peer or d_obj.upward_min_rank != new_upward:
                changes_log.append(
                    f"Divisi {d_obj.nama}: peer={d_obj.peer_access}->{new_peer}, "
                    f"upward_rank={d_obj.upward_min_rank}->{new_upward}"
                )
                d_obj.peer_access = new_peer
                d_obj.upward_min_rank = new_upward
                session.add(d_obj)

    if changes_log:
        record_audit_log(
            session,
            username=current_user.username,
            nama_pengguna=getattr(current_user, "full_name", current_user.username),
            role=current_user.role,
            aksi="Ubah Aturan Akses",
            modul="Kredensial",
            target_id="ACCESS-MATRIX",
            detail="; ".join(changes_log)[:500],
            level_risiko="Tinggi",
        )
        session.commit()

    return {"status": "ok", "updated_changes": changes_log}


@router.get("/visibility-preview")
def preview_credential_visibility(
    session: SessionDep,
    current_user: CurrentUserDep,
    type_code: str = Query(default="radmin"),
    divisi: str = Query(default="Operator & CS"),
    subject_rank: int = Query(default=0),
    min_view_rank: int = Query(default=0),
) -> dict[str, Any]:
    """F: Simulasi 'Terlihat oleh: ...' berdasarkan aturan Lapis 1 + Lapis 2."""
    del current_user  # Dependency authorization check
    by_code, _unused_id, div_by_name, _unused_div_id = _ensure_credential_types_and_rules(session)
    ct = by_code.get(map_legacy_type_to_code(type_code)) or by_code["radmin"]
    d_obj = div_by_name.get(divisi) or div_by_name.get("Umum")

    dummy_cred = Credential(
        id=-999,
        kode_kredensial="PREVIEW",
        nama_layanan="Preview",
        nama="Preview",
        jenis_kredensial=ct.nama,
        type_id=ct.id,
        divisi_pemilik_id=d_obj.id if d_obj else None,
        subject_rank=subject_rank,
        min_view_rank=min_view_rank,
        username="preview",
        password_encrypted="preview",
        allowed_roles=["Administrator", "Member"],
    )

    test_personas = [
        ("Owner", "Manajemen", 50, False),
        ("Direktur", "Manajemen", 40, False),
        ("General Manager", "Manajemen", 30, False),
        ("SPV Operasional", "Manajemen", 20, False),
        ("Lead IT", "IT", 15, True),
        ("IT Support", "IT", 15, True),
        ("HRD", "Senior & Cabang", 10, False),
        ("Staff Legal", "Senior & Cabang", 10, False),
        ("Head Marketing", "Senior & Cabang", 10, False),
        ("SPV Cilacap", "Senior & Cabang", 10, False),
        ("Staff Accounting", "Accounting", 0, False),
        ("Staff Operator & CS", "Operator & CS", 0, False),
        ("Staff Voucher", "Voucher", 0, False),
        ("Staff Kreatif", "Kreatif", 0, False),
        ("Programmer / QA", "Programmer / QA", 0, False),
    ]
    visible_to: list[str] = []
    for role_lbl, div_lbl, rnk, it_adm in test_personas:
        div_target = div_by_name.get(div_lbl)
        ctx = {
            "username": f"sim_{role_lbl}",
            "base_role": "Administrator" if it_adm else "Member",
            "role_id": role_lbl,
            "rank": rnk,
            "division_id": div_target.id if div_target else None,
            "is_it_admin": it_adm,
        }
        if can_access_credential(session, ctx, dummy_cred, action="view"):
            visible_to.append(role_lbl)

    return {
        "visible_to": visible_to,
        "summary_text": ", ".join(visible_to) if visible_to else "Hanya IT Admin & Owner",
    }


@router.get("/expiry-reminders")
def get_credential_expiry_reminders(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    """G: Pengingat kedaluwarsa domain/hosting pada H-30, H-7, H-1 untuk Lead IT & IT Support."""
    v_ctx = resolve_viewer_context(session, current_user)
    now_utc = utcnow()
    cutoff = now_utc + timedelta(days=30)
    rows = session.exec(
        select(Credential).where(
            col(Credential.deleted_at).is_(None),
            col(Credential.expired_at).is_not(None),
            col(Credential.expired_at) <= cutoff,
        )
    ).all()

    reminders: list[dict[str, Any]] = []
    for r in rows:
        if not v_ctx["is_owner_or_it"] and not can_access_credential(session, v_ctx, r, "view"):
            continue
        exp_dt = (
            r.expired_at
            if r.expired_at and r.expired_at.tzinfo is not None
            else (r.expired_at.replace(tzinfo=UTC) if r.expired_at else now_utc)
        )
        days_left = (exp_dt.date() - now_utc.date()).days
        stage = (
            "Expired"
            if days_left < 0
            else ("H-1" if days_left <= 1 else ("H-7" if days_left <= 7 else "H-30"))
        )
        reminders.append(
            {
                "kode_kredensial": r.kode_kredensial,
                "nama": r.nama or r.nama_layanan,
                "days_left": days_left,
                "stage": stage,
                "expired_at": exp_dt.date().isoformat(),
            }
        )
    return {"count": len(reminders), "items": reminders}


@router.get("/{identifier}", response_model=CredentialPublic)
def get_credential_detail(
    identifier: str,
    session: SessionDep,
    current_user: CurrentUserDep,
    as_role: str | None = Query(default=None),
) -> CredentialPublic:
    """Mengambil detail satu kredensial (rahasia TIDAK PERNAH dikirim, hanya hasValue: true)."""
    _, by_id, _, div_by_id = _ensure_credential_types_and_rules(session)
    row = _find_credential(session, identifier)
    v_ctx = resolve_viewer_context(session, current_user, as_role=as_role)
    if not can_access_credential(session, v_ctx, row, action="view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke entri kredensial ini",
        )
    t_obj = by_id.get(row.type_id or 0)
    d_obj = div_by_id.get(row.divisi_pemilik_id or 0)
    can_rev = can_access_credential(session, v_ctx, row, action="reveal")
    return CredentialPublic.from_model(
        row,
        viewer_role=current_user.role,
        type_obj=t_obj,
        division_name=d_obj.nama if d_obj else "Umum",
        can_reveal_override=can_rev,
    )


def _perform_reveal(
    identifier: str,
    session: Session,
    current_user: Any,
    payload: dict[str, Any] | None = None,
    request: Request | None = None,
) -> CredentialRevealResponse:
    """B & C: Cek izin Lapis 1+2 + reveal, re-auth 5 menit, rate limit 20/menit, & Audit Log."""
    _ensure_credential_types_and_rules(session)
    row = _find_credential(session, identifier)
    body = payload or {}
    as_role = body.get("as_role")
    v_ctx = resolve_viewer_context(session, current_user, as_role=as_role)

    # 1. Cek izin Lapis 1 + Lapis 2 + tindakan "reveal"
    if not can_access_credential(session, v_ctx, row, action="reveal"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Peran '{v_ctx['role_id']}' tidak memiliki izin "
                "untuk membuka password kredensial ini"
            ),
        )

    # 2. Cek Re-Autentikasi (5 menit) bila reauth_password dikirim atau require_reauth aktif
    now_ts = time.time()
    reauth_pwd = body.get("reauth_password") or body.get("account_password")
    require_reauth = bool(body.get("require_reauth", False))
    if reauth_pwd is not None:
        if not verify_password(str(reauth_pwd), current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password akun tidak sesuai untuk verifikasi buka kredensial",
            )
        _REAUTH_SESSIONS[current_user.username] = now_ts + REAUTH_TTL_SECONDS
    elif require_reauth:
        valid_until = _REAUTH_SESSIONS.get(current_user.username, 0.0)
        if now_ts > valid_until:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Sesi verifikasi password telah habis (5 menit). "
                    "Masukkan kembali password akun Anda."
                ),
            )

    # 3. Rate limit: maksimal 20 reveal / menit / pengguna
    bucket = [t for t in _REVEAL_RATE_BUCKETS.get(current_user.username, []) if now_ts - t < 60.0]
    if len(bucket) >= REVEAL_RATE_LIMIT_PER_MIN:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Batas pembukaan password tercapai (maks. 20 kali/menit). Silakan tunggu sesaat."
            ),
        )
    bucket.append(now_ts)
    _REVEAL_RATE_BUCKETS[current_user.username] = bucket

    field_key = str(body.get("field") or "password").strip()
    action_type = str(body.get("action") or "reveal").strip().lower()

    try:
        secrets_map = decrypt_secret_dict(row.data_rahasia) if row.data_rahasia else {}
        plain_pwd = (
            secrets_map.get(field_key)
            or secrets_map.get("password")
            or decrypt_secret(row.password_encrypted)
        )
        plain_extra = secrets_map.get("secret_extra") or (
            decrypt_secret(row.secret_extra_encrypted) if row.secret_extra_encrypted else ""
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kredensial tidak dapat didekripsi",
        ) from exc

    client_ip = request.client.host if (request and request.client) else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")[:120] if request else "testclient"
    aksi_label = "Copy Kredensial" if action_type == "copy" else "Reveal Kredensial"

    # G: Catat di Audit Log tanpa pernah menulis nilai rahasia
    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=getattr(current_user, "full_name", current_user.username),
        role=current_user.role,
        aksi=aksi_label,
        modul="Kredensial",
        target_id=row.kode_kredensial,
        detail=(
            f"{aksi_label} '{row.nama or row.nama_layanan}' "
            f"(field={field_key}, ip={client_ip}, ua={user_agent})"
        )[:500],
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
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    payload: dict[str, Any] | None = Body(default=None),
) -> CredentialRevealResponse:
    """Mendekripsi dan menampilkan field rahasia kredensial bila izin Lapis 1 & 2 terpenuhi."""
    return _perform_reveal(identifier, session, current_user, payload=payload, request=request)


@router.get(
    "/{identifier}/reveal",
    response_model=CredentialRevealResponse,
    include_in_schema=False,
)
def reveal_credential_get(
    identifier: str,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CredentialRevealResponse:
    """Mendekripsi dan menampilkan password kredensial bila peran diizinkan (GET alias)."""
    return _perform_reveal(identifier, session, current_user, request=request)


@router.post("", response_model=CredentialPublic, status_code=status.HTTP_201_CREATED)
def create_credential(
    payload: CredentialCreate,
    session: SessionDep,
    current_user: EditorUserDep,
) -> CredentialPublic:
    """Membuat kredensial baru dengan enkripsi Fernet & AES-256-GCM serta atribut Lapis 2."""
    by_code, _, div_by_name, _ = _ensure_credential_types_and_rules(session)
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

    extra = payload.model_extra or {}
    raw_type_code = str(
        extra.get("type_code")
        or payload.jenis_key
        or map_legacy_type_to_code(payload.jenis_kredensial)
    )
    ct_obj = by_code.get(map_legacy_type_to_code(raw_type_code)) or by_code["pc"]

    # Tentukan divisi & subject_rank otomatis dari Asset bila ditautkan (Seksi 12)
    raw_linked = str(extra.get("linked_asset_id") or payload.id_aset or "").strip()
    linked_id = raw_linked.split(" ")[0].strip().upper() if raw_linked else None
    matched_asset = (
        session.exec(
            select(Asset).where(
                func.upper(Asset.id_aset) == linked_id,
                col(Asset.deleted_at).is_(None),
            )
        ).first()
        if linked_id
        else None
    )

    div_name_req = str(extra.get("divisi") or extra.get("divisi_label") or "").strip()
    subj_rank_req = extra.get("subject_rank")

    if matched_asset is not None:
        if not payload.lokasi or payload.lokasi == "Head Office (Office Blok 14)":
            payload.lokasi = matched_asset.lokasi
        if not payload.ip_address and matched_asset.ip_address:
            payload.ip_address = matched_asset.ip_address
        if not div_name_req:
            source_label = (
                matched_asset.pemakai_text
                or matched_asset.penanggung_jawab
                or matched_asset.nama_aset
            )
            div_name_req, auto_rank, _ = normalize_legacy_division_and_rank(source_label)
            if matched_asset.kategori.lower() == "server":
                div_name_req = "IT"
                auto_rank = 15
        else:
            _, auto_rank, _ = normalize_legacy_division_and_rank(div_name_req)
    elif not div_name_req:
        div_name_req, auto_rank, _ = normalize_legacy_division_and_rank(payload.nama_layanan)
        if is_admin_only_type(payload.jenis_kredensial):
            div_name_req = "IT"
            auto_rank = 15
    else:
        _, auto_rank, _ = normalize_legacy_division_and_rank(div_name_req)

    d_obj = div_by_name.get(div_name_req) or div_by_name.get("Umum")
    final_subj_rank = int(subj_rank_req) if subj_rank_req is not None else auto_rank
    min_v_rank = int(extra.get("min_view_rank", 0) or 0)

    pub_data = dict(extra.get("data_publik") or {})
    pub_data["type_code"] = ct_obj.kode
    sec_dict = dict(extra.get("data_rahasia_dict") or {})
    sec_dict.setdefault("password", payload.password)
    if payload.secret_extra:
        sec_dict["secret_extra"] = payload.secret_extra

    encrypted_pwd = encrypt_secret(payload.password)
    encrypted_extra = encrypt_secret(payload.secret_extra) if payload.secret_extra else ""
    aes_blob = encrypt_secret_dict(sec_dict, key_version=CURRENT_KEY_VERSION)
    exp_dt = compute_nearest_expiry(pub_data)

    row = Credential(
        kode_kredensial=final_code,
        type_id=ct_obj.id,
        nama=payload.nama_layanan,
        nama_layanan=payload.nama_layanan,
        jenis_kredensial=payload.jenis_kredensial,
        divisi_pemilik_id=d_obj.id if d_obj else None,
        subject_rank=final_subj_rank,
        min_view_rank=min_v_rank,
        linked_asset_id=linked_id,
        lokasi=payload.lokasi,
        id_aset=payload.id_aset,
        ip_address=payload.ip_address.strip(),
        port=str(payload.port).strip(),
        url_akses=payload.url_akses.strip(),
        username=payload.username.strip(),
        password_encrypted=encrypted_pwd,
        secret_extra_encrypted=encrypted_extra,
        data_publik=pub_data,
        data_rahasia=aes_blob,
        key_version=CURRENT_KEY_VERSION,
        last_rotated_at=utcnow(),
        expired_at=exp_dt,
        created_by=current_user.username,
        level_akses=payload.level_akses or "Administrator",
        allowed_roles=payload.allowed_roles or default_roles_for_type(payload.jenis_kredensial),
        status=payload.status.strip(),
        terakhir_diubah_oleh=current_user.username,
        catatan=payload.catatan.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return CredentialPublic.from_model(
        row,
        viewer_role=current_user.role,
        type_obj=ct_obj,
        division_name=d_obj.nama if d_obj else "Umum",
    )


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
                status_code=HTTP_422_STATUS,
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
        row.data_rahasia = encrypt_secret_dict(
            {"password": new_plain_pwd},
            key_version=CURRENT_KEY_VERSION,
        )
        row.last_rotated_at = utcnow()

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
