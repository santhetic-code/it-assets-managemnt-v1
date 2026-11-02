"""Endpoint autentikasi: login dan informasi pengguna aktif."""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.core.security import create_access_token, verify_password
from app.deps import CurrentUserDep, SessionDep
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserPublic

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    """Autentikasi username dan password, lalu kembalikan JWT access token."""
    username = payload.username.strip()
    user = session.exec(select(User).where(User.username == username)).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna tidak aktif",
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

