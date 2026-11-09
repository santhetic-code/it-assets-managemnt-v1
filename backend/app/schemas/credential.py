"""Skema Pydantic dan matriks izin per jenis untuk Credential Manager (B7)."""

from datetime import UTC, datetime
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

# C: Peringkat (Rank) posisi/jabatan untuk Lapis 2
ROLE_RANKS: dict[str, int] = {
    "Owner": 50,
    "Direktur": 40,
    "General Manager": 30,
    "GM": 30,
    "SPV Operasional": 20,
    "Supervisor Operasional": 20,
    "Lead IT": 15,
    "IT Support": 15,
    "Administrator": 15,
    "HRD": 10,
    "Staff Legal": 10,
    "Head Marketing": 10,
    "SPV Cilacap": 10,
    "HRD / Legal / Head Mkt": 10,
    "Member": 0,
    "Staff Operator & CS": 0,
    "Staff Accounting": 0,
    "Staff Voucher": 0,
    "Staff Kreatif": 0,
    "Programmer / QA": 0,
    "Viewer": -1,
}

# C: Daftar Divisi standar beserta peer_access & upward_min_rank
INITIAL_DIVISIONS: list[dict[str, Any]] = [
    {"nama": "Manajemen", "peer_access": False, "upward_min_rank": 20},
    {"nama": "IT", "peer_access": True, "upward_min_rank": 20},
    {"nama": "Senior & Cabang", "peer_access": False, "upward_min_rank": 20},
    {"nama": "Accounting", "peer_access": True, "upward_min_rank": 40},  # Divisi sensitif
    {"nama": "Operator & CS", "peer_access": True, "upward_min_rank": 20},
    {"nama": "Voucher", "peer_access": True, "upward_min_rank": 20},
    {"nama": "Kreatif", "peer_access": True, "upward_min_rank": 20},
    {"nama": "Programmer / QA", "peer_access": True, "upward_min_rank": 20},
    {"nama": "Umum", "peer_access": True, "upward_min_rank": 0},
]

# A: 8 Jenis Kredensial Awal sebagai Data (Schema JSON)
INITIAL_CREDENTIAL_TYPES: list[dict[str, Any]] = [
    {
        "kode": "website",
        "nama": "Website",
        "ikon": "globe",
        "urutan": 1,
        "schema": [
            {
                "key": "nama_website",
                "label": "Nama website",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "wp_link",
                "label": "Link login",
                "tipe": "url",
                "wajib": False,
                "rahasia": False,
                "grup": "WordPress",
            },
            {
                "key": "wp_username",
                "label": "Username",
                "tipe": "text",
                "wajib": False,
                "rahasia": False,
                "grup": "WordPress",
            },
            {
                "key": "wp_password",
                "label": "Password",
                "tipe": "password",
                "wajib": False,
                "rahasia": True,
                "grup": "WordPress",
            },
            {
                "key": "wps_link",
                "label": "Link login",
                "tipe": "url",
                "wajib": False,
                "rahasia": False,
                "grup": "WordPress (Shop)",
            },
            {
                "key": "wps_username",
                "label": "Username",
                "tipe": "text",
                "wajib": False,
                "rahasia": False,
                "grup": "WordPress (Shop)",
            },
            {
                "key": "wps_password",
                "label": "Password",
                "tipe": "password",
                "wajib": False,
                "rahasia": True,
                "grup": "WordPress (Shop)",
            },
            {
                "key": "cpanel_link",
                "label": "Link login",
                "tipe": "url",
                "wajib": False,
                "rahasia": False,
                "grup": "cPanel",
            },
            {
                "key": "cpanel_username",
                "label": "Username",
                "tipe": "text",
                "wajib": False,
                "rahasia": False,
                "grup": "cPanel",
            },
            {
                "key": "cpanel_password",
                "label": "Password",
                "tipe": "password",
                "wajib": False,
                "rahasia": True,
                "grup": "cPanel",
            },
            {
                "key": "cf_username",
                "label": "Username",
                "tipe": "text",
                "wajib": False,
                "rahasia": False,
                "grup": "Cloudflare",
            },
            {
                "key": "cf_password",
                "label": "Password",
                "tipe": "password",
                "wajib": False,
                "rahasia": True,
                "grup": "Cloudflare",
            },
            {
                "key": "rw_username",
                "label": "Username",
                "tipe": "text",
                "wajib": False,
                "rahasia": False,
                "grup": "Rumahweb",
            },
            {
                "key": "rw_password",
                "label": "Password",
                "tipe": "password",
                "wajib": False,
                "rahasia": True,
                "grup": "Rumahweb",
            },
            {
                "key": "expired_domain",
                "label": "Expired domain",
                "tipe": "date",
                "wajib": False,
                "rahasia": False,
                "grup": "Masa berlaku",
            },
            {
                "key": "expired_hosting",
                "label": "Expired hosting",
                "tipe": "date",
                "wajib": False,
                "rahasia": False,
                "grup": "Masa berlaku",
            },
        ],
    },
    {
        "kode": "pc",
        "nama": "PC",
        "ikon": "monitor",
        "urutan": 2,
        "schema": [
            {
                "key": "pengguna",
                "label": "Pengguna",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "ip_address",
                "label": "IP Address",
                "tipe": "ip",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "password",
                "label": "Password",
                "tipe": "password",
                "wajib": True,
                "rahasia": True,
                "grup": "Umum",
            },
            {
                "key": "linked_asset_id",
                "label": "Tautan Entri IP / PC",
                "tipe": "select",
                "wajib": False,
                "rahasia": False,
                "grup": "Umum",
            },
        ],
    },
    {
        "kode": "email",
        "nama": "Email",
        "ikon": "mail",
        "urutan": 3,
        "schema": [
            {
                "key": "nama",
                "label": "Nama",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "email",
                "label": "Email",
                "tipe": "email",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "password",
                "label": "Password",
                "tipe": "password",
                "wajib": True,
                "rahasia": True,
                "grup": "Umum",
            },
        ],
    },
    {
        "kode": "sql_server",
        "nama": "SQL Server",
        "ikon": "database",
        "urutan": 4,
        "schema": [
            {
                "key": "nama",
                "label": "Nama",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "server_name",
                "label": "Server Name",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "user_id",
                "label": "User ID",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "password",
                "label": "Password",
                "tipe": "password",
                "wajib": True,
                "rahasia": True,
                "grup": "Umum",
            },
        ],
    },
    {
        "kode": "telegram",
        "nama": "Telegram",
        "ikon": "send",
        "urutan": 5,
        "schema": [
            {
                "key": "nama",
                "label": "Nama",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "username",
                "label": "Username",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "cloud_password",
                "label": "Cloud Password",
                "tipe": "password",
                "wajib": True,
                "rahasia": True,
                "grup": "Umum",
            },
            {
                "key": "nomor_telepon",
                "label": "Nomor Telepon",
                "tipe": "phone",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
        ],
    },
    {
        "kode": "radmin",
        "nama": "Radmin",
        "ikon": "monitor-smartphone",
        "urutan": 6,
        "schema": [
            {
                "key": "nama",
                "label": "Nama",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "username",
                "label": "Username",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "password",
                "label": "Password",
                "tipe": "password",
                "wajib": True,
                "rahasia": True,
                "grup": "Umum",
            },
            {
                "key": "linked_asset_id",
                "label": "Tautan PC / IP",
                "tipe": "select",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
        ],
    },
    {
        "kode": "mikrotik",
        "nama": "Mikrotik",
        "ikon": "router",
        "urutan": 7,
        "schema": [
            {
                "key": "nama",
                "label": "Nama",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "ip_address",
                "label": "IP Address",
                "tipe": "ip",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "username",
                "label": "Username",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "password",
                "label": "Password",
                "tipe": "password",
                "wajib": True,
                "rahasia": True,
                "grup": "Umum",
            },
            {
                "key": "lokasi",
                "label": "Lokasi",
                "tipe": "select",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
        ],
    },
    {
        "kode": "cctv_wifi",
        "nama": "CCTV & Wifi",
        "ikon": "video",
        "urutan": 8,
        "schema": [
            {
                "key": "nama",
                "label": "Nama",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "ssid_username",
                "label": "SSID / Username",
                "tipe": "text",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
            {
                "key": "password",
                "label": "Password",
                "tipe": "password",
                "wajib": True,
                "rahasia": True,
                "grup": "Umum",
            },
        ],
    },
]

# C & D: Matriks Izin Lapis 1 ("full"=lihat+password, "view"=lihat saja, "none"=terkunci)
INITIAL_ROLE_MATRIX: dict[str, dict[str, str]] = {
    "Owner": {t["kode"]: "full" for t in INITIAL_CREDENTIAL_TYPES},
    "Direktur": {t["kode"]: "full" for t in INITIAL_CREDENTIAL_TYPES},
    "General Manager": {t["kode"]: "full" for t in INITIAL_CREDENTIAL_TYPES},
    "SPV Operasional": {
        "website": "full",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "full",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "full",
    },
    "Lead IT": {t["kode"]: "full" for t in INITIAL_CREDENTIAL_TYPES},
    "IT Support": {t["kode"]: "full" for t in INITIAL_CREDENTIAL_TYPES},
    "Administrator": {t["kode"]: "full" for t in INITIAL_CREDENTIAL_TYPES},
    "HRD": {
        "website": "view",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "full",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "Staff Legal": {
        "website": "view",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "full",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "Head Marketing": {
        "website": "view",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "full",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "SPV Cilacap": {
        "website": "view",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "full",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "HRD / Legal / Head Mkt": {
        "website": "view",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "full",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "Staff Operator & CS": {
        "website": "none",
        "pc": "full",
        "email": "view",
        "sql_server": "none",
        "telegram": "none",
        "radmin": "full",
        "mikrotik": "full",
        "cctv_wifi": "view",
    },
    "Staff Accounting": {
        "website": "none",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "none",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "Staff Voucher": {
        "website": "none",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "none",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "Staff Kreatif": {
        "website": "full",
        "pc": "full",
        "email": "view",
        "sql_server": "none",
        "telegram": "none",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "Programmer / QA": {
        "website": "full",
        "pc": "view",
        "email": "full",
        "sql_server": "full",
        "telegram": "none",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "view",
    },
    "Member": {
        "website": "full",
        "pc": "full",
        "email": "full",
        "sql_server": "none",
        "telegram": "full",
        "radmin": "full",
        "mikrotik": "none",
        "cctv_wifi": "full",
    },
    "Viewer": {t["kode"]: "none" for t in INITIAL_CREDENTIAL_TYPES},
}


def map_legacy_type_to_code(raw_type: str) -> str:
    """Memetakan jenis_kredensial lama maupun baru ke kode 8 credential_types (A & H)."""
    low = (raw_type or "").strip().lower()
    mapping = {
        "website": "website",
        "website & aplikasi": "website",
        "aplikasi": "website",
        "domain / dns": "website",
        "cloud / vps": "website",
        "pc": "pc",
        "detail pc": "pc",
        "laptop": "pc",
        "server": "pc",
        "perangkat": "pc",
        "email": "email",
        "akun": "email",
        "akun online": "email",
        "sql_server": "sql_server",
        "sql server": "sql_server",
        "database": "sql_server",
        "telegram": "telegram",
        "radmin": "radmin",
        "mikrotik": "mikrotik",
        "router": "mikrotik",
        "router / mikrotik": "mikrotik",
        "firewall": "mikrotik",
        "cctv_wifi": "cctv_wifi",
        "cctv & wifi": "cctv_wifi",
        "cctv": "cctv_wifi",
        "wifi": "cctv_wifi",
        "jaringan": "cctv_wifi",
        "switch / ap": "cctv_wifi",
    }
    return mapping.get(low, low if low in {t["kode"] for t in INITIAL_CREDENTIAL_TYPES} else "pc")


def normalize_legacy_division_and_rank(raw_name_or_user: str) -> tuple[str, int, str]:
    """H: Menormalkan salah ketik nama/jabatan ke (divisi, subject_rank, clean_name)."""
    text = (raw_name_or_user or "").strip()
    typos = {
        "ACCOUNITNG": "ACCOUNTING",
        "ACOUNTING": "ACCOUNTING",
        "ENGIEER": "ENGINEER",
        "ENGINER": "ENGINEER",
        "AMDIN": "ADMIN",
        "OPRATOR": "OPERATOR",
        "DIREKTR": "DIREKTUR",
        "MARKTING": "MARKETING",
    }
    upper = text.upper()
    for bad, good in typos.items():
        upper = upper.replace(bad, good)

    if "OWNER" in upper:
        return "Manajemen", 50, upper
    if "DIREKTUR" in upper:
        return "Manajemen", 40, upper
    if "GENERAL MANAGER" in upper or upper == "GM" or " GM " in f" {upper} ":
        return "Manajemen", 30, upper
    if "SPV OPERASIONAL" in upper or "SUPERVISOR OPERASIONAL" in upper:
        return "Manajemen", 20, upper
    if "LEAD IT" in upper or "IT SUPPORT" in upper or upper.startswith("IT "):
        return "IT", 15, upper
    if any(k in upper for k in ("HRD", "LEGAL", "HEAD MARKETING", "SPV CILACAP")):
        return "Senior & Cabang", 10, upper
    if any(k in upper for k in ("ACCOUNTING", "FINANCE", "PAJAK", "MBL")):
        return "Accounting", 0, upper
    if "VOUCHER" in upper:
        return "Voucher", 0, upper
    if any(k in upper for k in ("SEO", "DESIGN", "CONTENT", "KREATIF")):
        return "Kreatif", 0, upper
    if any(k in upper for k in ("PROGRAMMER", "FULL STACK", "FULLSTACK", "ENGINEER", "QA")):
        return "Programmer / QA", 0, upper
    if any(
        k in upper for k in ("OPERATOR", "CS", "ADMIN", "H2H", "RETAIL", "PH", "OTOTEPE", "SDP")
    ):
        return "Operator & CS", 0, upper
    return "Umum", 0, text or "Umum"


def compute_nearest_expiry(data_publik: dict[str, Any]) -> datetime | None:
    """B: Menghitung expired_at turunan dari tanggal paling dekat di data_publik."""
    candidates: list[datetime] = []
    for k, v in (data_publik or {}).items():
        if ("expired" in k.lower() or "berlaku" in k.lower()) and v:
            val_str = str(v).strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    dt = datetime.strptime(val_str[:10], fmt).replace(tzinfo=UTC)
                    candidates.append(dt)
                    break
                except ValueError:
                    continue
    return min(candidates) if candidates else None


def resolve_canonical_type(raw_type: str) -> str:
    """Menormalisasi nama jenis kredensial ke bentuk kanonik (mendukung 8 jenis baru & lama)."""
    cleaned = raw_type.strip()
    if not cleaned:
        raise ValueError("Jenis kredensial wajib diisi")
    fe_aliases = {
        "website": "Aplikasi",
        "website & aplikasi": "Aplikasi",
        "perangkat": "Server",
        "akun": "Email",
        "akun online": "Email",
        "sql_server": "Database",
        "sql server": "Database",
        "telegram": "Aplikasi",
        "radmin": "PC",
        "cctv_wifi": "CCTV",
        "cctv & wifi": "CCTV",
    }
    if cleaned.lower() in fe_aliases:
        return fe_aliases[cleaned.lower()]
    for canonical in CREDENTIAL_TYPE_PERMISSIONS:
        if canonical.lower() == cleaned.lower():
            return canonical
    return cleaned


def default_roles_for_type(jenis_kredensial: str) -> list[str]:
    """Mengembalikan daftar peran yang berhak mengakses/me-reveal jenis kredensial ini."""
    canonical = resolve_canonical_type(jenis_kredensial)
    return list(
        CREDENTIAL_TYPE_PERMISSIONS.get(
            canonical,
            [UserRole.ADMINISTRATOR.value, UserRole.MEMBER.value],
        )
    )


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
    """Representasi JSON kredensial untuk tabel/detail (rahasia TIDAK PERNAH dikirim)."""

    model_config = ConfigDict(extra="allow")

    id: int
    kode_kredensial: str
    id_kredensial: str
    type_id: int | None = None
    type_code: str = "pc"
    nama: str = ""
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
    linked_asset_id: str | None = None

    divisi_pemilik_id: int | None = None
    divisi_label: str = "Umum"
    subject_rank: int = 0
    min_view_rank: int = 0
    akses_label: str = "Divisi + atasan"

    ip_address: str
    host: str
    target: str = "—"
    port: str
    url_akses: str

    username: str
    password: str
    secret: str
    secret_ada: bool = True
    is_masked: bool = True
    has_secret_extra: bool = False
    data_publik: dict[str, Any] = Field(default_factory=dict)
    secret_fields_meta: dict[str, dict[str, bool]] = Field(default_factory=dict)

    level_akses: str
    peran: str = ""
    allowed_roles: list[str]
    can_reveal: bool
    can_edit: bool = False
    can_delete: bool = False
    is_admin_only: bool

    status: str
    status_label: str = "Aktif"
    status_variant: str = "success"
    days_until_expiry: int | None = None
    is_old_password: bool = False
    expired_at: str | None = None
    last_rotated_at: str = ""
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
        *,
        type_obj: Any | None = None,
        division_name: str = "Umum",
        can_reveal_override: bool | None = None,
        can_edit_override: bool | None = None,
        can_delete_override: bool | None = None,
    ) -> "CredentialPublic":
        can_rev = (
            can_reveal_override
            if can_reveal_override is not None
            else can_user_access_credential_type(
                viewer_role,
                row.jenis_kredensial,
                row.allowed_roles,
            )
        )
        adm_only = is_admin_only_type(row.jenis_kredensial) or (
            row.allowed_roles == [UserRole.ADMINISTRATOR.value]
        )
        t_code = (
            getattr(type_obj, "kode", None)
            or (row.data_publik or {}).get("type_code")
            or map_legacy_type_to_code(row.jenis_kredensial)
        )
        t_label = getattr(type_obj, "nama", None) or next(
            (t["nama"] for t in INITIAL_CREDENTIAL_TYPES if t["kode"] == t_code),
            row.jenis_kredensial,
        )

        pub = dict(row.data_publik or {})
        target_str = (
            pub.get("wp_link")
            or pub.get("email")
            or pub.get("server_name")
            or (f"SSID: {pub['ssid_username']}" if pub.get("ssid_username") else "")
            or row.url_akses
            or (f"{row.ip_address}:{row.port}" if row.ip_address and row.port else row.ip_address)
            or (f"@{row.username.lstrip('@')}" if t_code == "telegram" and row.username else "")
            or "—"
        )

        now_utc = datetime.now(UTC)
        days_exp: int | None = None
        if row.expired_at is not None:
            exp_dt = (
                row.expired_at
                if row.expired_at.tzinfo is not None
                else row.expired_at.replace(tzinfo=UTC)
            )
            days_exp = (exp_dt.date() - now_utc.date()).days

        rot_dt = row.last_rotated_at or row.updated_at
        if rot_dt.tzinfo is None:
            rot_dt = rot_dt.replace(tzinfo=UTC)
        is_old_pwd = (now_utc - rot_dt).days > 90

        raw_status = row.status or "Aktif"
        if raw_status.lower() == "nonaktif":
            status_lbl = "Nonaktif"
            st_var = "danger"
        elif days_exp is not None and days_exp < 0:
            status_lbl = "Kedaluwarsa"
            st_var = "danger"
        elif days_exp is not None and days_exp <= 30:
            status_lbl = f"Domain {days_exp} hari lagi"
            st_var = "warning"
        else:
            status_lbl = raw_status
            st_var = "success"

        if row.min_view_rank >= 40 or division_name == "Accounting" or row.subject_rank >= 30:
            akses_lbl = "Hanya IT & Direksi"
        elif division_name == "Umum" and row.min_view_rank == 0:
            akses_lbl = "Semua divisi"
        else:
            akses_lbl = "Divisi + atasan"

        has_sec = bool(row.password_encrypted or row.data_rahasia)
        sec_meta: dict[str, dict[str, bool]] = {"password": {"hasValue": has_sec}}
        if type_obj and getattr(type_obj, "schema_fields", None):
            for f_def in type_obj.schema_fields:
                if f_def.get("rahasia"):
                    sec_meta[f_def["key"]] = {"hasValue": has_sec}

        disp_name = row.nama or row.nama_layanan
        return cls(
            id=row.id or 0,
            kode_kredensial=row.kode_kredensial,
            id_kredensial=row.kode_kredensial,
            type_id=row.type_id,
            type_code=t_code,
            nama=disp_name,
            nama_layanan=row.nama_layanan or disp_name,
            nama_perangkat=row.nama_layanan or disp_name,
            induk=row.nama_layanan or disp_name,
            jenis_kredensial=row.jenis_kredensial,
            jenis_key=t_code,
            jenis_label=t_label,
            kategori=row.jenis_kredensial,
            tipe=row.jenis_kredensial,
            lokasi=row.lokasi,
            id_aset=row.id_aset,
            linked_asset_id=row.linked_asset_id or row.id_aset,
            divisi_pemilik_id=row.divisi_pemilik_id,
            divisi_label=division_name,
            subject_rank=row.subject_rank,
            min_view_rank=row.min_view_rank,
            akses_label=akses_lbl,
            ip_address=row.ip_address or "-",
            host=row.ip_address or "-",
            target=target_str,
            port=row.port or "-",
            url_akses=row.url_akses,
            username=row.username,
            password=MASKED_SECRET_DISPLAY,
            secret=MASKED_SECRET_DISPLAY,
            secret_ada=has_sec,
            is_masked=True,
            has_secret_extra=bool(row.secret_extra_encrypted),
            data_publik=pub,
            secret_fields_meta=sec_meta,
            level_akses=row.level_akses,
            peran=row.level_akses,
            allowed_roles=row.allowed_roles,
            can_reveal=can_rev,
            can_edit=bool(can_edit_override) if can_edit_override is not None else can_rev,
            can_delete=bool(can_delete_override)
            if can_delete_override is not None
            else (viewer_role == UserRole.ADMINISTRATOR.value),
            is_admin_only=adm_only,
            status=row.status,
            status_label=status_lbl,
            status_variant=st_var,
            days_until_expiry=days_exp,
            is_old_password=is_old_pwd,
            expired_at=row.expired_at.date().isoformat() if row.expired_at else None,
            last_rotated_at=rot_dt.date().isoformat(),
            terakhir_diubah_oleh=row.terakhir_diubah_oleh,
            terakhir_diganti=rot_dt.date().isoformat(),
            updated_at=row.updated_at.isoformat(),
            catatan=row.catatan,
            keterangan=row.catatan,
        )


class CredentialRevealResponse(BaseModel):
    """Respons khusus endpoint /reveal yang mengembalikan password hasil dekripsi."""

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
    """Respons berhalaman daftar kredensial beserta tile_counts, summary, dan kpi."""

    items: list[CredentialPublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    type_tiles: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any]
    kpi: dict[str, Any]
    viewer_context: dict[str, Any] = Field(default_factory=dict)
