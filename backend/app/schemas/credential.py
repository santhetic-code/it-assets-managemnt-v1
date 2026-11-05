"""Skema Pydantic dan matriks izin per jenis untuk Credential Manager (B7)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.master_data import LOCATION_ALIASES, LOCATIONS
from app.core.security import MASKED_SECRET_DISPLAY
from app.models.credential import Credential
from app.models.user import UserRole

# Matriks izin default per jenis kredensial:
# - Jenis infrastruktur kritis hanya boleh diakses/di-reveal oleh Administrator.
# - Jenis operasional harian boleh diakses/di-reveal oleh Administrator & Member.
# - Viewer tidak pernah diizinkan melakukan reveal password.
CREDENTIAL_TYPE_PERMISSIONS: dict[str, list[str]] = {
    "Server": [UserRole.ADMINISTRATOR.value],
    "Database": [UserRole.ADMINISTRATOR.value],
    "MikroTik": [UserRole.ADMINISTRATOR.value],
    "Router": [UserRole.ADMINISTRATOR.value],
    "Router / MikroTik": [UserRole.ADMINISTRATOR.value],
    "Firewall": [UserRole.ADMINISTRATOR.value],
    "Cloud / VPS": [UserRole.ADMINISTRATOR.value],
    "Domain / DNS": [UserRole.ADMINISTRATOR.value],
    "VPN": [UserRole.ADMINISTRATOR.value],
    "Jaringan": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "Switch / AP": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "CCTV": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "WiFi": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "PC": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "Laptop": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "Printer": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "Aplikasi": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "Email": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
    "Lainnya": [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
}

ADMIN_ONLY_TYPES = {
    k.lower()
    for k, roles in CREDENTIAL_TYPE_PERMISSIONS.items()
    if roles == [UserRole.ADMINISTRATOR.value]
}


def resolve_canonical_type(raw_type: str) -> str:
    """Menormalisasi nama jenis kredensial ke bentuk kanonik."""
    cleaned = raw_type.strip()
    if not cleaned:
        raise ValueError("Jenis kredensial wajib diisi")
    fe_aliases = {
        "website": "Aplikasi",
        "website & aplikasi": "Aplikasi",
        "perangkat": "Server",
        "akun": "Email",
        "akun online": "Email",
    }
    if cleaned.lower() in fe_aliases:
        return fe_aliases[cleaned.lower()]
    for canonical in CREDENTIAL_TYPE_PERMISSIONS:
        if canonical.lower() == cleaned.lower():
            return canonical
    raise ValueError(f"Jenis kredensial '{cleaned}' tidak valid")


def default_roles_for_type(jenis_kredensial: str) -> list[str]:
    """Mengembalikan daftar peran yang berhak mengakses/me-reveal jenis kredensial ini."""
    canonical = resolve_canonical_type(jenis_kredensial)
    return list(CREDENTIAL_TYPE_PERMISSIONS[canonical])


def is_admin_only_type(jenis_kredensial: str) -> bool:
    """Memeriksa apakah jenis kredensial khusus untuk Administrator."""
    return jenis_kredensial.strip().lower() in ADMIN_ONLY_TYPES


def can_user_access_credential_type(
    user_role: str,
    jenis_kredensial: str,
    allowed_roles: list[str] | None = None,
) -> bool:
    """Memeriksa apakah peran pengguna diizinkan untuk membuka (reveal) atau mengelola jenis ini."""
    if user_role == UserRole.ADMINISTRATOR.value:
        return True
    if user_role == UserRole.VIEWER.value:
        return False

    # Untuk Member: jika jenis kredensial khusus Admin, selalu tolak
    if is_admin_only_type(jenis_kredensial):
        return False

    effective_roles = allowed_roles or default_roles_for_type(jenis_kredensial)
    return user_role in effective_roles


def _normalize_location(val: str) -> str:
    cleaned = val.strip()
    if not cleaned:
        return "Head Office (Office Blok 14)"
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc
    if cleaned.lower() in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned.lower()]
    return cleaned


def _map_to_frontend_jenis(jenis_kredensial: str) -> tuple[str, str]:
    low = (jenis_kredensial or "").lower()
    if low in ("aplikasi", "domain / dns", "cloud / vps"):
        return "website", "Website & Aplikasi"
    if low in ("email", "lainnya"):
        return "akun", "Akun Online"
    return "perangkat", "Perangkat"


class CredentialCreate(BaseModel):
    """Payload penambahan kredensial baru."""

    model_config = ConfigDict(extra="allow")

    kode_kredensial: str | None = Field(default=None, max_length=30)
    id_kredensial: str | None = Field(default=None, max_length=30)

    nama_layanan: str = Field(default="", max_length=150)
    nama_perangkat: str | None = Field(default=None, max_length=150)
    induk: str | None = Field(default=None, max_length=150)
    judul: str | None = Field(default=None, max_length=150)

    jenis_kredensial: str = Field(default="Server", max_length=50)
    jenis_key: str | None = Field(default=None, max_length=50)
    jenis_label: str | None = Field(default=None, max_length=50)
    kategori: str | None = Field(default=None, max_length=50)
    tipe: str | None = Field(default=None, max_length=50)

    lokasi: str = Field(default="Head Office (Office Blok 14)", max_length=100)
    id_aset: str | None = Field(default=None, max_length=30)

    ip_address: str = Field(default="", max_length=80)
    host: str | None = Field(default=None, max_length=80)
    target: str | None = Field(default=None, max_length=255)
    port: str | int = Field(default="")
    url_akses: str = Field(default="", max_length=255)

    username: str = Field(min_length=1, max_length=120)
    password: str = Field(default="", max_length=500)
    secret: str | None = Field(default=None, max_length=500)
    secret_extra: str = Field(default="", max_length=500)

    level_akses: str | None = Field(default=None, max_length=40)
    peran: str | None = Field(default=None, max_length=40)
    allowed_roles: list[str] | None = Field(default=None)

    status: str = Field(default="Aktif", max_length=30)
    catatan: str = Field(default="", max_length=500)
    keterangan: str | None = Field(default=None, max_length=500)

    @field_validator("lokasi")
    @classmethod
    def _check_loc(cls, v: str) -> str:
        return _normalize_location(v)

    @model_validator(mode="after")
    def _normalize_and_validate(self) -> "CredentialCreate":
        if not self.kode_kredensial and self.id_kredensial:
            self.kode_kredensial = self.id_kredensial.strip()

        if not self.nama_layanan:
            if self.induk:
                self.nama_layanan = self.induk.strip()
            elif self.nama_perangkat:
                self.nama_layanan = self.nama_perangkat.strip()
            elif self.judul:
                self.nama_layanan = self.judul.strip()
        self.nama_layanan = self.nama_layanan.strip()
        if not self.nama_layanan:
            raise ValueError("Nama layanan/perangkat wajib diisi")

        raw_type = (
            self.kategori
            or self.tipe
            or self.jenis_key
            or self.jenis_label
            or self.jenis_kredensial
        )
        self.jenis_kredensial = resolve_canonical_type(raw_type)

        if not self.password and self.secret:
            self.password = self.secret
        if not self.password or not self.password.strip():
            raise ValueError("Password atau secret kredensial wajib diisi")

        if self.target and not self.ip_address and not self.url_akses:
            t_clean = self.target.strip()
            if "http" in t_clean.lower() or "/" in t_clean:
                self.url_akses = t_clean
            else:
                self.ip_address = t_clean[:80]
        elif not self.ip_address and self.host:
            self.ip_address = self.host.strip()
        self.port = str(self.port).strip() if self.port is not None else ""

        if not self.catatan and self.keterangan:
            self.catatan = self.keterangan.strip()

        if self.id_aset:
            cleaned_asset = self.id_aset.strip().upper()
            self.id_aset = cleaned_asset if cleaned_asset not in ("", "-", "—") else None

        default_roles = default_roles_for_type(self.jenis_kredensial)
        if is_admin_only_type(self.jenis_kredensial):
            self.allowed_roles = [UserRole.ADMINISTRATOR.value]
            self.level_akses = self.peran or "Administrator"
        else:
            if self.allowed_roles is None:
                self.allowed_roles = default_roles
            if not self.level_akses:
                self.level_akses = self.peran or (
                    "Administrator"
                    if self.allowed_roles == [UserRole.ADMINISTRATOR.value]
                    else "Member"
                )

        return self


class CredentialUpdate(BaseModel):
    """Payload pembaruan kredensial (password opsional; bila diisi akan dienkripsi ulang)."""

    model_config = ConfigDict(extra="allow")

    nama_layanan: str | None = None
    nama_perangkat: str | None = None
    induk: str | None = None
    jenis_kredensial: str | None = None
    jenis_key: str | None = None
    jenis_label: str | None = None
    kategori: str | None = None
    lokasi: str | None = None
    id_aset: str | None = None
    ip_address: str | None = None
    target: str | None = None
    port: str | int | None = None
    url_akses: str | None = None
    username: str | None = None
    password: str | None = None
    secret: str | None = None
    secret_extra: str | None = None
    level_akses: str | None = None
    peran: str | None = None
    allowed_roles: list[str] | None = None
    status: str | None = None
    catatan: str | None = None


class CredentialPublic(BaseModel):
    """Representasi JSON kredensial untuk tabel/detail (password SELALU disamarkan)."""

    id: int
    kode_kredensial: str
    id_kredensial: str
    nama_layanan: str
    nama_perangkat: str
    induk: str = ""
    jenis_kredensial: str
    jenis_key: str = "perangkat"
    jenis_label: str = "Perangkat"
    kategori: str
    tipe: str
    lokasi: str
    id_aset: str | None

    ip_address: str
    host: str
    target: str = "—"
    port: str
    url_akses: str

    username: str
    password: str
    secret: str
    secret_ada: bool = True
    is_masked: bool
    has_secret_extra: bool

    level_akses: str
    peran: str = ""
    allowed_roles: list[str]
    can_reveal: bool
    is_admin_only: bool

    status: str
    status_variant: str = "success"
    terakhir_diubah_oleh: str
    terakhir_diganti: str = ""
    updated_at: str
    catatan: str
    keterangan: str

    @classmethod
    def from_model(
        cls,
        row: Credential,
        viewer_role: str = UserRole.VIEWER.value,
    ) -> "CredentialPublic":
        can_rev = can_user_access_credential_type(
            viewer_role,
            row.jenis_kredensial,
            row.allowed_roles,
        )
        adm_only = is_admin_only_type(row.jenis_kredensial) or (
            row.allowed_roles == [UserRole.ADMINISTRATOR.value]
        )
        j_key, j_label = _map_to_frontend_jenis(row.jenis_kredensial)
        target_str = (
            row.url_akses
            or (f"{row.ip_address}:{row.port}" if row.ip_address and row.port else row.ip_address)
            or "—"
        )
        st_var = "success" if (row.status or "").lower() == "aktif" else "warning"
        return cls(
            id=row.id or 0,
            kode_kredensial=row.kode_kredensial,
            id_kredensial=row.kode_kredensial,
            nama_layanan=row.nama_layanan,
            nama_perangkat=row.nama_layanan,
            induk=row.nama_layanan,
            jenis_kredensial=row.jenis_kredensial,
            jenis_key=j_key,
            jenis_label=j_label,
            kategori=row.jenis_kredensial,
            tipe=row.jenis_kredensial,
            lokasi=row.lokasi,
            id_aset=row.id_aset,
            ip_address=row.ip_address or "-",
            host=row.ip_address or "-",
            target=target_str,
            port=row.port or "-",
            url_akses=row.url_akses,
            username=row.username,
            password=MASKED_SECRET_DISPLAY,
            secret=MASKED_SECRET_DISPLAY,
            secret_ada=bool(row.password_encrypted),
            is_masked=True,
            has_secret_extra=bool(row.secret_extra_encrypted),
            level_akses=row.level_akses,
            peran=row.level_akses,
            allowed_roles=row.allowed_roles,
            can_reveal=can_rev,
            is_admin_only=adm_only,
            status=row.status,
            status_variant=st_var,
            terakhir_diubah_oleh=row.terakhir_diubah_oleh,
            terakhir_diganti=row.updated_at.date().isoformat(),
            updated_at=row.updated_at.isoformat(),
            catatan=row.catatan,
            keterangan=row.catatan,
        )


class CredentialRevealResponse(BaseModel):
    """Respons khusus endpoint /reveal yang mengembalikan password hasil dekripsi Fernet."""

    id: int
    kode_kredensial: str
    nama_layanan: str
    jenis_kredensial: str
    username: str
    password: str
    secret: str
    value: str = ""
    secret_extra: str
    revealed_by: str


class CredentialPageResponse(BaseModel):
    """Respons berhalaman daftar kredensial beserta tab_counts, summary, dan kpi."""

    items: list[CredentialPublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, Any]

