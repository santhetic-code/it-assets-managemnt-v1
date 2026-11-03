"""Model database untuk tabel pengguna (users) dan definisi peran."""

from enum import StrEnum
from typing import Any

from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class UserRole(StrEnum):
    """Peran pengguna resmi di ITAM Pro."""

    ADMINISTRATOR = "Administrator"
    MEMBER = "Member"
    VIEWER = "Viewer"


class User(TimestampMixin, SQLModel, table=True):
    """Tabel pengguna sistem ITAM Pro."""

    __tablename__: Any = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50, nullable=False)
    full_name: str = Field(max_length=100, nullable=False)
    password_hash: str = Field(max_length=255, nullable=False)
    role: str = Field(default=UserRole.VIEWER.value, max_length=30, nullable=False)
    is_active: bool = Field(default=True, nullable=False)

