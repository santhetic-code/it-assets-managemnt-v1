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
from app.schemas.audit import record_audit_log
from app.schemas.auth import LoginRequest, TokenResponse, UserPublic

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Mendapatkan alamat IP klien dari header x-forwarded-for atau koneksi langsung."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: SessionDep, request: Request) -> TokenResponse:
    """Autentikasi username dan password, lalu kembalikan JWT access token."""
    username = payload.username.strip()
    client_ip = _get_client_ip(request)

    if is_login_rate_limited(client_ip, username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Terlalu banyak percobaan login gagal. Silakan coba lagi dalam beberapa saat.",
        )

    user = session.exec(select(User).where(func.lower(User.username) == username.lower())).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        record_failed_login(client_ip, username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    if not user.is_active:
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
        level_risiko="Rendah",
        ip_address=client_ip,
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
