"""Endpoint Manajemen Pengguna & Pengaturan Akun (/api/v1/users) (B8)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.csv_importer import import_all_csv_data
from app.core.security import hash_password, verify_password
from app.deps import AdminUserDep, CurrentUserDep, PageParamsDep, SessionDep
from app.models.base import utcnow
from app.models.user import User, UserRole
from app.schemas.audit import record_audit_log
from app.schemas.auth import UserPublic
from app.schemas.user import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    UserCreateRequest,
    UserPageResponse,
    UserUpdateRequest,
)

router = APIRouter()


def _find_user(session: Session, identifier: str) -> User:
    cleaned = identifier.strip()
    user: User | None = None
    if cleaned.isdigit():
        user = session.get(User, int(cleaned))
    if user is None:
        user = session.exec(
            select(User).where(func.lower(User.username) == cleaned.lower())
        ).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengguna tidak ditemukan",
        )
    return user


def _count_active_admins(session: Session) -> int:
    return len(
        session.exec(
            select(User).where(
                col(User.role) == UserRole.ADMINISTRATOR.value,
                col(User.is_active).is_(True),
            )
        ).all()
    )


@router.get("", response_model=UserPageResponse)
def list_users(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    role: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
) -> UserPageResponse:
    """Mengambil daftar pengguna beserta ringkasan peran dan status."""
    all_users = list(
        session.exec(select(User).order_by(col(User.id).asc())).all()
    )
    all_public = [UserPublic.from_user(u) for u in all_users]

    total_all = len(all_public)
    aktif_count = sum(1 for u in all_public if u.is_active)
    nonaktif_count = total_all - aktif_count
    admin_count = sum(
        1 for u in all_public if u.role == UserRole.ADMINISTRATOR
    )
    member_count = sum(1 for u in all_public if u.role == UserRole.MEMBER)
    viewer_count = sum(1 for u in all_public if u.role == UserRole.VIEWER)

    tab_counts = {
        "Semua": total_all,
        "all": total_all,
        "Administrator": admin_count,
        "Member": member_count,
        "Viewer": viewer_count,
        "Aktif": aktif_count,
        "Nonaktif": nonaktif_count,
    }
    summary: dict[str, Any] = {
        "total": total_all,
        "total_pengguna": total_all,
        "aktif": aktif_count,
        "nonaktif": nonaktif_count,
        "administrator": admin_count,
        "member": member_count,
        "viewer": viewer_count,
    }

    filtered = all_public
    keyword = (search or q or "").strip().lower()
    if keyword:
        filtered = [
            u
            for u in filtered
            if keyword in u.username.lower()
            or keyword in u.full_name.lower()
            or keyword in u.role.value.lower()
        ]

    if role and role.strip().lower() not in ("semua", "all", ""):
        r_clean = role.strip().lower()
        filtered = [u for u in filtered if u.role.value.lower() == r_clean]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        s_clean = status_filter.strip().lower()
        if s_clean == "aktif":
            filtered = [u for u in filtered if u.is_active]
        elif s_clean == "nonaktif":
            filtered = [u for u in filtered if not u.is_active]

    total = len(filtered)
    paged = filtered[page_params.offset : page_params.offset + page_params.page_size]

    return UserPageResponse(
        items=paged,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=summary,
    )


@router.post("/me/password")
def change_own_password(
    payload: ChangePasswordRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, str]:
    """Mengubah password akun milik pengguna yang sedang login."""
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password lama tidak sesuai",
        )

    current_user.password_hash = hash_password(payload.new_password)
    current_user.updated_at = utcnow()
    session.add(current_user)
    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=current_user.full_name,
        role=current_user.role,
        aksi="Ubah Password Mandiri",
        modul="Pengguna",
        target_id=current_user.username,
        detail=f"Pengguna '{current_user.username}' memperbarui password akunnya",
        level_risiko="Sedang",
        commit=False,
    )
    session.commit()
    return {"status": "ok", "detail": "Password berhasil diperbarui"}


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    session: SessionDep,
    admin_user: AdminUserDep,
) -> UserPublic:
    """Membuat akun pengguna baru (hanya Administrator)."""
    existing = session.exec(
        select(User).where(func.lower(User.username) == payload.username.lower())
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' sudah terdaftar",
        )

    new_user = User(
        username=payload.username,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    session.add(new_user)
    session.flush()

    record_audit_log(
        session,
        username=admin_user.username,
        nama_pengguna=admin_user.full_name,
        role=admin_user.role,
        aksi="Tambah Pengguna",
        modul="Pengguna",
        target_id=new_user.username,
        detail=f"Membuat akun '{new_user.username}' dengan peran {new_user.role}",
        level_risiko="Sedang",
        commit=False,
    )
    session.commit()
    session.refresh(new_user)
    return UserPublic.from_user(new_user)


def _apply_user_update(
    identifier: str,
    payload: UserUpdateRequest,
    session: Session,
    admin_user: User,
) -> UserPublic:
    target = _find_user(session, identifier)
    data = payload.model_dump(exclude_unset=True)

    if "nama_lengkap" in data and "full_name" not in data:
        data["full_name"] = data.pop("nama_lengkap")
    else:
        data.pop("nama_lengkap", None)

    if "status" in data and "is_active" not in data and data["status"] is not None:
        data["is_active"] = str(data.pop("status")).strip().lower() == "aktif"
    else:
        data.pop("status", None)

    # Cegah menonaktifkan atau menurunkan peran satu-satunya Administrator aktif
    was_active_admin = (
        target.role == UserRole.ADMINISTRATOR.value and target.is_active
    )
    new_role = data.get("role", target.role)
    new_active = data.get("is_active", target.is_active)
    if was_active_admin and (
        new_role != UserRole.ADMINISTRATOR.value or not new_active
    ):
        if _count_active_admins(session) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat menonaktifkan atau mengubah peran Administrator aktif terakhir",
            )

    if "full_name" in data and data["full_name"] is not None:
        target.full_name = str(data["full_name"]).strip()
    if "role" in data and data["role"] is not None:
        target.role = str(data["role"])
    if "is_active" in data and data["is_active"] is not None:
        target.is_active = bool(data["is_active"])
    if data.get("password"):
        target.password_hash = hash_password(str(data["password"]))

    target.updated_at = utcnow()
    session.add(target)

    record_audit_log(
        session,
        username=admin_user.username,
        nama_pengguna=admin_user.full_name,
        role=admin_user.role,
        aksi="Ubah Pengguna",
        modul="Pengguna",
        target_id=target.username,
        detail=(
            f"Memperbarui akun '{target.username}' "
            f"(role={target.role}, aktif={target.is_active})"
        ),
        level_risiko="Sedang",
        commit=False,
    )
    session.commit()
    session.refresh(target)
    return UserPublic.from_user(target)


@router.put("/{identifier}", response_model=UserPublic)
def update_user_put(
    identifier: str,
    payload: UserUpdateRequest,
    session: SessionDep,
    admin_user: AdminUserDep,
) -> UserPublic:
    """Memperbarui profil, peran, atau status pengguna (PUT)."""
    return _apply_user_update(identifier, payload, session, admin_user)


@router.patch("/{identifier}", response_model=UserPublic)
def update_user_patch(
    identifier: str,
    payload: UserUpdateRequest,
    session: SessionDep,
    admin_user: AdminUserDep,
) -> UserPublic:
    """Memperbarui sebagian profil, peran, atau status pengguna (PATCH)."""
    return _apply_user_update(identifier, payload, session, admin_user)


@router.post("/{identifier}/reset-password", response_model=UserPublic)
def admin_reset_user_password(
    identifier: str,
    payload: AdminResetPasswordRequest,
    session: SessionDep,
    admin_user: AdminUserDep,
) -> UserPublic:
    """Mereset password pengguna oleh Administrator."""
    target = _find_user(session, identifier)
    target.password_hash = hash_password(payload.new_password)
    target.updated_at = utcnow()
    session.add(target)

    record_audit_log(
        session,
        username=admin_user.username,
        nama_pengguna=admin_user.full_name,
        role=admin_user.role,
        aksi="Reset Password",
        modul="Pengguna",
        target_id=target.username,
        detail=f"Administrator mereset password akun '{target.username}'",
        level_risiko="Tinggi",
        commit=False,
    )
    session.commit()
    session.refresh(target)
    return UserPublic.from_user(target)


@router.delete("/{identifier}")
def delete_user(
    identifier: str,
    session: SessionDep,
    admin_user: AdminUserDep,
) -> dict[str, Any]:
    """Menghapus akun pengguna (hanya Administrator, dilarang menghapus akun sendiri)."""
    target = _find_user(session, identifier)
    if target.username.lower() == admin_user.username.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anda tidak dapat menghapus akun Anda sendiri yang sedang aktif",
        )
    if target.role == UserRole.ADMINISTRATOR.value and target.is_active:
        if _count_active_admins(session) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat menghapus Administrator aktif terakhir",
            )

    deleted_username = target.username
    deleted_id = target.id
    session.delete(target)

    record_audit_log(
        session,
        username=admin_user.username,
        nama_pengguna=admin_user.full_name,
        role=admin_user.role,
        aksi="Hapus Pengguna",
        modul="Pengguna",
        target_id=deleted_username,
        detail=f"Menghapus akun pengguna '{deleted_username}'",
        level_risiko="Tinggi",
        commit=False,
    )
    session.commit()
    return {"status": "ok", "id": deleted_id, "username": deleted_username}


@router.post("/import-csv", response_model=dict[str, Any])
def import_csv_data_users_alias(
    session: SessionDep,
    current_admin: AdminUserDep,
) -> dict[str, Any]:
    """Alias endpoint impor data CSV operasional ke database (khusus Administrator)."""
    return import_all_csv_data(session, username=current_admin.username)

