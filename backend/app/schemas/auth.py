"""Skema request dan response untuk autentikasi dan profil pengguna."""

from pydantic import BaseModel, Field

from app.models.user import User, UserRole


class LoginRequest(BaseModel):
    """Payload login dari frontend."""

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    """Data publik pengguna (tanpa password_hash) sesuai kontrak frontend."""

    id: int
    username: str
    full_name: str
    nama_lengkap: str
    role: UserRole
    is_active: bool
    status: str

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        return cls(
            id=user.id or 0,
            username=user.username,
            full_name=user.full_name,
            nama_lengkap=user.full_name,
            role=UserRole(user.role),
            is_active=user.is_active,
            status="Aktif" if user.is_active else "Nonaktif",
        )


class TokenResponse(BaseModel):
    """Respons sukses POST /api/v1/auth/login."""

    access_token: str
    token_type: str = "bearer"
    user: UserPublic
    username: str
    full_name: str
    nama_lengkap: str
    role: UserRole
