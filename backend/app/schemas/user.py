"""Skema Pydantic untuk Manajemen Pengguna dan Pengaturan Akun (B8)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.user import UserRole
from app.schemas.auth import UserPublic


def _validate_role(val: str) -> str:
    cleaned = val.strip()
    for role in UserRole:
        if role.value.lower() == cleaned.lower():
            return role.value
    raise ValueError(
        f"Peran '{cleaned}' tidak valid (pilih Administrator, Member, atau Viewer)"
    )


class UserCreateRequest(BaseModel):
    """Payload penambahan pengguna baru oleh Administrator."""

    model_config = ConfigDict(extra="allow")

    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(default="", max_length=100)
    nama_lengkap: str | None = Field(default=None, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default=UserRole.MEMBER.value, max_length=30)
    is_active: bool = Field(default=True)
    status: str | None = Field(default=None, max_length=20)

    @field_validator("username")
    @classmethod
    def _clean_username(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not cleaned or " " in cleaned:
            raise ValueError("Username tidak boleh kosong atau mengandung spasi")
        return cleaned

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        return _validate_role(v)

    @model_validator(mode="after")
    def _sync_fields(self) -> "UserCreateRequest":
        if not self.full_name and self.nama_lengkap:
            self.full_name = self.nama_lengkap.strip()
        if not self.full_name:
            self.full_name = self.username.capitalize()
        if self.status is not None:
            self.is_active = self.status.strip().lower() == "aktif"
        return self


class UserUpdateRequest(BaseModel):
    """Payload pembaruan pengguna oleh Administrator."""

    model_config = ConfigDict(extra="allow")

    full_name: str | None = Field(default=None, max_length=100)
    nama_lengkap: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None
    status: str | None = Field(default=None, max_length=20)
    password: str | None = Field(default=None, min_length=6, max_length=128)

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str | None) -> str | None:
        return _validate_role(v) if v is not None else None


class ChangePasswordRequest(BaseModel):
    """Payload ubah password mandiri oleh pengguna yang sedang login."""

    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class AdminResetPasswordRequest(BaseModel):
    """Payload reset password pengguna oleh Administrator."""

    new_password: str = Field(min_length=6, max_length=128)


class UserPageResponse(BaseModel):
    """Respons daftar pengguna berhalaman beserta tab_counts dan summary."""

    items: list[UserPublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, Any]

