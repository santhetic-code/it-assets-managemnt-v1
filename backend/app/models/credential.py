"""Model database untuk penyimpanan kredensial terenkripsi Fernet (credentials)."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin, utcnow


class CredentialType(SQLModel, table=True):
    """A: Tabel jenis kredensial dinamis beserta schema JSON field-nya."""

    __tablename__: Any = "credential_types"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kode: str = Field(index=True, unique=True, max_length=40, nullable=False)
    nama: str = Field(max_length=80, nullable=False)
    ikon: str = Field(default="key", max_length=40, nullable=False)
    urutan: int = Field(default=1, index=True, nullable=False)
    schema_fields: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column("schema", JSON, nullable=False),
    )


class Division(SQLModel, table=True):
    """C: Tabel divisi pemilik kredensial & aturan akses Lapis 2."""

    __tablename__: Any = "divisions"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    nama: str = Field(index=True, unique=True, max_length=80, nullable=False)
    peer_access: bool = Field(default=True, nullable=False)
    upward_min_rank: int = Field(default=20, nullable=False)


class RoleTypePermission(SQLModel, table=True):
    """C: Matriks izin Lapis 1 (peran/jabatan x jenis kredensial)."""

    __tablename__: Any = "role_type_permissions"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    role_id: str = Field(index=True, max_length=60, nullable=False)
    type_id: int = Field(index=True, nullable=False)
    can_view: bool = Field(default=False, nullable=False)
    can_reveal: bool = Field(default=False, nullable=False)
    can_edit: bool = Field(default=False, nullable=False)
    can_delete: bool = Field(default=False, nullable=False)


class DivisionGrant(SQLModel, table=True):
    """C: Pengecualian lintas divisi (contoh: HRD -> Operator & CS, Head Marketing -> Kreatif)."""

    __tablename__: Any = "division_grants"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    viewer_role_id: str | None = Field(default=None, index=True, max_length=60, nullable=True)
    viewer_division_id: int | None = Field(default=None, index=True, nullable=True)
    target_division_id: int = Field(index=True, nullable=False)
    type_id: int | None = Field(default=None, index=True, nullable=True)


class CredentialACL(SQLModel, table=True):
    """C: Override izin per entri kredensial untuk user/role/division (deny menang)."""

    __tablename__: Any = "credential_acl"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    credential_id: int = Field(index=True, nullable=False)
    principal: str = Field(max_length=20, nullable=False)  # "user" | "role" | "division"
    principal_id: str = Field(index=True, max_length=80, nullable=False)
    effect: str = Field(default="allow", max_length=10, nullable=False)  # "allow" | "deny"
    actions: list[str] = Field(
        default_factory=lambda: ["view", "reveal"],
        sa_column=Column(JSON, nullable=False),
    )


class Credential(TimestampMixin, SQLModel, table=True):
    """Tabel kredensial sistem & perangkat TI (password disimpan terenkripsi Fernet)."""

    __tablename__: Any = "credentials"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kode_kredensial: str = Field(
        index=True,
        unique=True,
        max_length=30,
        nullable=False,
    )

    nama_layanan: str = Field(index=True, max_length=150, nullable=False)
    jenis_kredensial: str = Field(
        default="Server",
        index=True,
        max_length=50,
        nullable=False,
    )
    lokasi: str = Field(
        default="Head Office (Office Blok 14)",
        index=True,
        max_length=100,
        nullable=False,
    )
    id_aset: str | None = Field(default=None, index=True, max_length=30, nullable=True)

    ip_address: str = Field(default="", max_length=80, nullable=False)
    port: str = Field(default="", max_length=30, nullable=False)
    url_akses: str = Field(default="", max_length=255, nullable=False)

    username: str = Field(index=True, max_length=120, nullable=False)
    password_encrypted: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    secret_extra_encrypted: str = Field(
        default="",
        sa_column=Column(Text, nullable=False, server_default=""),
    )

    level_akses: str = Field(
        default="Administrator",
        index=True,
        max_length=40,
        nullable=False,
    )
    allowed_roles: list[str] = Field(
        default_factory=lambda: ["Administrator"],
        sa_column=Column(JSON, nullable=False, server_default='["Administrator"]'),
    )

    status: str = Field(default="Aktif", index=True, max_length=30, nullable=False)
    terakhir_diubah_oleh: str = Field(default="admin", max_length=80, nullable=False)
    catatan: str = Field(default="", max_length=500, nullable=False)

    # Kolom Redesain Credential Manager (B, C, I)
    type_id: int | None = Field(default=None, index=True, nullable=True)
    nama: str = Field(default="", index=True, max_length=150, nullable=False)
    divisi_pemilik_id: int | None = Field(default=None, index=True, nullable=True)
    subject_rank: int = Field(default=0, index=True, nullable=False)
    min_view_rank: int = Field(default=0, nullable=False)
    linked_asset_id: str | None = Field(default=None, index=True, max_length=50, nullable=True)
    data_publik: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    data_rahasia: str = Field(
        default="",
        sa_column=Column(Text, nullable=False, server_default=""),
    )
    key_version: int = Field(default=1, nullable=False)
    last_rotated_at: datetime = Field(default_factory=utcnow, index=True, nullable=False)
    expired_at: datetime | None = Field(default=None, index=True, nullable=True)
    created_by: str = Field(default="admin", max_length=80, nullable=False)
    deleted_at: datetime | None = Field(default=None, index=True, nullable=True)
