"""
Master Data & Config untuk Credential Manager ITAM Pro (Tahap 12).
Menggantikan 13 halaman e-Report dengan satu konfigurasi terpusat.
"""

from typing import Any, TypedDict

from itam_pro.styles.colors import Color


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
    "pc": {
        "slug": "pc",
        "name": "PC",
        "tab": "Perangkat",
        "roles": ["Windows", "Linux", "Lainnya"],
        "has_target": True,
        "target_label": "IP Address",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [],
    },
    "telegram": {
        "slug": "telegram",
        "name": "Telegram",
        "tab": "Akun Online",
        "roles": ["CS", "Bot", "Operasional"],
        "has_target": True,
        "target_label": "Username / No. Telepon",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [],
    },
    "radmin": {
        "slug": "radmin",
        "name": "Radmin",
        "tab": "Perangkat",
        "roles": ["Remote PC", "Operasional"],
        "has_target": True,
        "target_label": "IP Address PC",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [],
    },
    "cctv_wifi": {
        "slug": "cctv_wifi",
        "name": "CCTV & Wifi",
        "tab": "Perangkat",
        "roles": ["SSID WiFi", "NVR / Kamera CCTV"],
        "has_target": True,
        "target_label": "SSID / IP CCTV",
        "has_username": True,
        "has_secret": True,
        "important_dates": [],
        "fields": [],
    },
}

CREDENTIAL_TYPES_SCHEMA: list[dict[str, Any]] = [
    {
        "id": 1,
        "kode": "website",
        "nama": "Website",
        "ikon": "globe",
        "urutan": 1,
        "badge_bg": Color.BLUE_50,
        "badge_fg": Color.BLUE_700,
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
        "id": 2,
        "kode": "pc",
        "nama": "PC",
        "ikon": "monitor",
        "urutan": 2,
        "badge_bg": Color.SLATE_100,
        "badge_fg": Color.SLATE_700,
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
                "label": "Tautkan ke PC / IP",
                "tipe": "select",
                "wajib": False,
                "rahasia": False,
                "grup": "Umum",
            },
        ],
    },
    {
        "id": 3,
        "kode": "email",
        "nama": "Email",
        "ikon": "mail",
        "urutan": 3,
        "badge_bg": Color.AMBER_50,
        "badge_fg": Color.AMBER_700,
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
        "id": 4,
        "kode": "sql_server",
        "nama": "SQL Server",
        "ikon": "database",
        "urutan": 4,
        "badge_bg": Color.PURPLE_100,
        "badge_fg": Color.PURPLE_700,
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
        "id": 5,
        "kode": "telegram",
        "nama": "Telegram",
        "ikon": "send",
        "urutan": 5,
        "badge_bg": Color.SKY_100,
        "badge_fg": Color.SKY_700,
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
        "id": 6,
        "kode": "radmin",
        "nama": "Radmin",
        "ikon": "monitor-smartphone",
        "urutan": 6,
        "badge_bg": Color.GREEN_100,
        "badge_fg": Color.GREEN_700,
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
                "label": "Tautkan ke PC / IP (Wajib)",
                "tipe": "select",
                "wajib": True,
                "rahasia": False,
                "grup": "Umum",
            },
        ],
    },
    {
        "id": 7,
        "kode": "mikrotik",
        "nama": "Mikrotik",
        "ikon": "router",
        "urutan": 7,
        "badge_bg": Color.PINK_100,
        "badge_fg": Color.PINK_700,
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
        "id": 8,
        "kode": "cctv_wifi",
        "nama": "CCTV & Wifi",
        "ikon": "video",
        "urutan": 8,
        "badge_bg": Color.FUCHSIA_100,
        "badge_fg": Color.FUCHSIA_700,
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

ROLE_RANKS: dict[str, int] = {
    "Owner": 50,
    "Direktur": 40,
    "General Manager": 30,
    "SPV Operasional": 20,
    "Lead IT": 15,
    "IT Support": 15,
    "Administrator": 15,
    "HRD": 10,
    "Staff Legal": 10,
    "Head Marketing": 10,
    "SPV Cilacap": 10,
    "HRD / Legal / Head Mkt": 10,
    "Staff Operator & CS": 0,
    "Staff Accounting": 0,
    "Staff Voucher": 0,
    "Staff Kreatif": 0,
    "Programmer / QA": 0,
    "Member": 0,
    "Viewer": -1,
}

ROLE_DEFAULT_DIVISION: dict[str, str] = {
    "Owner": "Manajemen",
    "Direktur": "Manajemen",
    "General Manager": "Manajemen",
    "SPV Operasional": "Manajemen",
    "Lead IT": "IT",
    "IT Support": "IT",
    "Administrator": "IT",
    "HRD": "Senior & Cabang",
    "Staff Legal": "Senior & Cabang",
    "Head Marketing": "Senior & Cabang",
    "SPV Cilacap": "Senior & Cabang",
    "HRD / Legal / Head Mkt": "Senior & Cabang",
    "Staff Operator & CS": "Operator & CS",
    "Staff Accounting": "Accounting",
    "Staff Voucher": "Voucher",
    "Staff Kreatif": "Kreatif",
    "Programmer / QA": "Programmer / QA",
}

DIVISIONS_CONFIG: dict[str, dict[str, Any]] = {
    "Manajemen": {"peer_access": False, "upward_min_rank": 20},
    "IT": {"peer_access": True, "upward_min_rank": 20},
    "Senior & Cabang": {"peer_access": False, "upward_min_rank": 20},
    "Accounting": {"peer_access": True, "upward_min_rank": 40},
    "Operator & CS": {"peer_access": True, "upward_min_rank": 20},
    "Voucher": {"peer_access": True, "upward_min_rank": 20},
    "Kreatif": {"peer_access": True, "upward_min_rank": 20},
    "Programmer / QA": {"peer_access": True, "upward_min_rank": 20},
    "Umum": {"peer_access": True, "upward_min_rank": 0},
}

DIVISION_GRANTS_CONFIG: list[tuple[str, str]] = [
    ("HRD", "Operator & CS"),
    ("Head Marketing", "Kreatif"),
]

LAPIS_1_MATRIX: dict[str, dict[str, str]] = {
    "Owner": {t["kode"]: "full" for t in CREDENTIAL_TYPES_SCHEMA},
    "Direktur": {t["kode"]: "full" for t in CREDENTIAL_TYPES_SCHEMA},
    "General Manager": {t["kode"]: "full" for t in CREDENTIAL_TYPES_SCHEMA},
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
    "Lead IT": {t["kode"]: "full" for t in CREDENTIAL_TYPES_SCHEMA},
    "IT Support": {t["kode"]: "full" for t in CREDENTIAL_TYPES_SCHEMA},
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
}


def can_access_credential_fe(
    viewer_role: str,
    viewer_div: str,
    cred: dict[str, Any],
    action: str = "view",
    matrix_override: dict[str, dict[str, str]] | None = None,
    divisions_override: dict[str, dict[str, Any]] | None = None,
) -> bool:
    """C: Evaluasi Algoritma 7 Langkah canAccess(user, cred, action) di sisi Frontend/Mock."""
    if cred.get("deleted_at"):
        return False

    matrix = matrix_override or LAPIS_1_MATRIX
    divs_cfg = divisions_override or DIVISIONS_CONFIG

    role_perms = matrix.get(viewer_role) or matrix.get("SPV Operasional", {})
    t_code = str(cred.get("type_code") or cred.get("jenis", "pc"))
    if t_code == "detail_pc":
        t_code = "pc"
    elif t_code in ("sosmed",):
        t_code = "telegram"
    elif t_code in ("internet_kantor", "lainnya"):
        t_code = "cctv_wifi"

    cell_mode = role_perms.get(t_code, "none")
    if action in ("reveal", "copy", "edit") and cell_mode != "full":
        return False
    if cell_mode == "none":
        return False

    is_it_admin = viewer_role in ("Lead IT", "IT Support", "Administrator")
    if is_it_admin:
        return True

    user_rank = ROLE_RANKS.get(viewer_role, 0)
    min_view_rank = int(cred.get("min_view_rank", 0) or 0)
    if user_rank < min_view_rank:
        return False

    cred_div = str(cred.get("divisi") or "Umum")
    subj_rank = int(cred.get("subject_rank", 0) or 0)
    d_rule = divs_cfg.get(cred_div, {"peer_access": True, "upward_min_rank": 20})
    peer_ok = bool(cred.get("peer_access", d_rule["peer_access"]))
    upward_min = int(d_rule["upward_min_rank"])

    # 7a. Satu divisi & peer_access
    if viewer_div == cred_div and peer_ok and user_rank >= subj_rank:
        return True

    # 7b. Grants lintas divisi
    for g_role, g_target_div in DIVISION_GRANTS_CONFIG:
        if viewer_role == g_role and cred_div == g_target_div:
            return True

    # 7c. Atasan -> bawahan
    if user_rank > subj_rank and user_rank >= upward_min:
        return True

    if cred_div == "Umum" and user_rank >= subj_rank:
        return True

    return False


def compute_visibility_preview_fe(
    type_code: str,
    divisi: str,
    subject_rank: int = 0,
    min_view_rank: int = 0,
    peer_access: bool = True,
    matrix_override: dict[str, dict[str, str]] | None = None,
) -> list[str]:
    """F: Menghitung daftar 'Terlihat oleh: ...' untuk form tambah/ubah kredensial."""
    dummy = {
        "type_code": type_code,
        "jenis": type_code,
        "divisi": divisi,
        "subject_rank": subject_rank,
        "min_view_rank": min_view_rank,
        "peer_access": peer_access,
    }
    personas = [
        ("Owner", "Manajemen"),
        ("Direktur", "Manajemen"),
        ("General Manager", "Manajemen"),
        ("SPV Operasional", "Manajemen"),
        ("Lead IT", "IT"),
        ("IT Support", "IT"),
        ("HRD", "Senior & Cabang"),
        ("Head Marketing", "Senior & Cabang"),
        ("Staff Operator & CS", "Operator & CS"),
        ("Staff Accounting", "Accounting"),
        ("Staff Voucher", "Voucher"),
        ("Staff Kreatif", "Kreatif"),
        ("Programmer / QA", "Programmer / QA"),
    ]
    visible: list[str] = []
    for r_name, d_name in personas:
        if can_access_credential_fe(r_name, d_name, dummy, "view", matrix_override=matrix_override):
            visible.append(r_name)
    return visible
