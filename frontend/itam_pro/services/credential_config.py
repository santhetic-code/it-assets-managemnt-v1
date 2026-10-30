"""
Master Data & Config untuk Credential Manager ITAM Pro (Tahap 12).
Menggantikan 13 halaman e-Report dengan satu konfigurasi terpusat.
"""
from typing import TypedDict


class CredentialField(TypedDict):
    name: str
    label: str
    type: str  # "text", "password", "date", "number"
    required: bool
    is_secret: bool


class CredentialCategory(TypedDict):
    slug: str
    name: str
    tab: str
    roles: list[str]
    has_target: bool
    target_label: str
    has_username: bool
    has_secret: bool
    important_dates: list[str]
    fields: list[CredentialField]


# Tab (urutan tetap): Semua | Website & Aplikasi | Perangkat | Akun Online
CREDENTIAL_TABS: list[str] = [
    "Semua",
    "Website & Aplikasi",
    "Perangkat",
    "Akun Online",
]

# Definisi Jenis Kredensial
CREDENTIAL_CATEGORIES: dict[str, CredentialCategory] = {
    "website": {
        "slug": "website",
        "name": "Website & Aplikasi Web",
        "tab": "Website & Aplikasi",
        "roles": [
            "WordPress",
            "WordPress (shop)",
            "cPanel",
            "Cloudflare",
            "Rumahweb",
            "Domainesia",
            "Webreport",
            "Lainnya",
        ],
        "has_target": True,
        "target_label": "Link Login (URL)",
        "has_username": True,
        "has_secret": True,
        "important_dates": ["Domain", "Hosting"],
        "fields": [],
    },
    "detail_pc": {
        "slug": "detail_pc",
        "name": "Detail PC",
        "tab": "Perangkat",
        "roles": ["Windows", "PIN", "Radmin", "Lainnya"],
        "has_target": True,
        "target_label": "IP Address / Hostname",
        "has_username": False,
        "has_secret": False,
        "important_dates": [],
        "fields": [],
    },
    "sql_server": {
        "slug": "sql_server",
        "name": "SQL Server",
        "tab": "Perangkat",
        "roles": ["Database Utama", "Replica", "Lainnya"],
        "has_target": True,
        "target_label": "Servername / IP",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [],
    },
    "mikrotik": {
        "slug": "mikrotik",
        "name": "Mikrotik",
        "tab": "Perangkat",
        "roles": ["Router Utama", "Switch", "Lainnya"],
        "has_target": True,
        "target_label": "IP / Host",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [
            {
                "name": "port",
                "label": "Port",
                "type": "number",
                "required": False,
                "is_secret": False,
            },
            {
                "name": "lokasi",
                "label": "Lokasi Fisik",
                "type": "text",
                "required": False,
                "is_secret": False,
            },
        ],
    },
    "internet_kantor": {
        "slug": "internet_kantor",
        "name": "Internet Kantor",
        "tab": "Perangkat",
        "roles": ["ISP Utama", "ISP Backup", "Lainnya"],
        "has_target": False,
        "target_label": "",
        "has_username": False,
        "has_secret": False,
        "important_dates": [],
        "fields": [
            {
                "name": "id_billing",
                "label": "ID Billing",
                "type": "text",
                "required": False,
                "is_secret": False,
            },
            {
                "name": "no_pelanggan",
                "label": "Nomor Pelanggan",
                "type": "text",
                "required": False,
                "is_secret": False,
            },
            {
                "name": "id_layanan",
                "label": "ID Layanan",
                "type": "text",
                "required": False,
                "is_secret": False,
            },
            {
                "name": "paket_layanan",
                "label": "Paket Layanan",
                "type": "text",
                "required": False,
                "is_secret": False,
            },
        ],
    },
    "email": {
        "slug": "email",
        "name": "Email",
        "tab": "Akun Online",
        "roles": ["Admin", "Support", "Marketing", "Lainnya"],
        "has_target": False,
        "target_label": "",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [
            {
                "name": "recovery_email",
                "label": "Recovery Email",
                "type": "text",
                "required": False,
                "is_secret": False,
            },
        ],
    },
    "sosmed": {
        "slug": "sosmed",
        "name": "Sosial Media & Chat",
        "tab": "Akun Online",
        "roles": ["Instagram", "Facebook", "Twitter/X", "Telegram", "Lainnya"],
        "has_target": False,
        "target_label": "",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [
            {
                "name": "no_hp",
                "label": "Nomor HP Terhubung",
                "type": "text",
                "required": False,
                "is_secret": False,
            },
        ],
    },
    "lainnya": {
        "slug": "lainnya",
        "name": "Akun Lain-lain",
        "tab": "Akun Online",
        "roles": ["Akun Eksternal", "Lainnya"],
        "has_target": False,
        "target_label": "",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [
            {
                "name": "recovery_code",
                "label": "Recovery Code",
                "type": "password",
                "required": False,
                "is_secret": True,
            },
        ],
    },
}

