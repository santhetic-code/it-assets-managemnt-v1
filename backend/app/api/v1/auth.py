"""Endpoint autentikasi: login dan informasi pengguna aktif."""

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func
from sqlmodel import select

from app.core.rate_limit import (
    clear_failed_login,
    is_login_rate_limited,
    record_failed_login,
)
from app.core.security import create_access_token, verify_password
from app.deps import CurrentUserDep, SessionDep
from app.models.user import User
from app.schemas.audit import extract_client_origin, record_audit_log
from app.schemas.auth import LoginRequest, TokenResponse, UserPublic

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Mendapatkan alamat IP klien tervalidasi (hanya percaya header dari proxy internal)."""
    client_ip, _ = extract_client_origin(request)
    return client_ip


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: SessionDep, request: Request) -> TokenResponse:
    """Autentikasi username dan password, lalu kembalikan JWT access token."""
    username = payload.username.strip()
    client_ip = _get_client_ip(request)

    if is_login_rate_limited(client_ip, username):
        record_audit_log(
            session,
            username=username or "anonymous",
            nama_pengguna=username or "Anonymous",
            role="Viewer",
            aksi="akun_terkunci",
            modul="Autentikasi",
            target_id=username or "-",
            detail=(
                f"Akun '{username}' terkunci sementara karena "
                "terlalu banyak percobaan login gagal"
            ),
            status="Ditolak",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Terlalu banyak percobaan login gagal. Silakan coba lagi dalam beberapa saat.",
        )

    user = session.exec(select(User).where(func.lower(User.username) == username.lower())).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        record_failed_login(client_ip, username)
        record_audit_log(
            session,
            username=user.username if user else (username or "anonymous"),
            nama_pengguna=user.full_name if user else (username or "Anonymous"),
            role=user.role if user else "Viewer",
            aksi="login_gagal",
            modul="Autentikasi",
            target_id=username or "-",
            detail=f"Percobaan login gagal untuk akun '{username}'",
            status="Gagal",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    if not user.is_active:
        record_audit_log(
            session,
            username=user.username,
            nama_pengguna=user.full_name,
            role=user.role,
            aksi="login_gagal",
            modul="Autentikasi",
            target_id=user.username,
            detail=f"Login ditolak karena akun '{user.username}' tidak aktif",
            status="Ditolak",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna tidak aktif",
        )

    clear_failed_login(client_ip, username)

    record_audit_log(
        session,
        username=user.username,
        nama_pengguna=user.full_name,
        role=user.role,
        aksi="Login",
        modul="Autentikasi",
        target_id=user.username,
        detail=f"Pengguna '{user.username}' berhasil login ke sistem",
        status="Berhasil",
        request=request,
    )

    user_public = UserPublic.from_user(user)
    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(
        access_token=token,
        user=user_public,
        username=user_public.username,
        full_name=user_public.full_name,
        nama_lengkap=user_public.nama_lengkap,
        role=user_public.role,
    )


@router.get("/me", response_model=UserPublic)
def get_me(current_user: CurrentUserDep) -> UserPublic:
    """Mengembalikan profil pengguna yang sedang login."""
    return UserPublic.from_user(current_user)
