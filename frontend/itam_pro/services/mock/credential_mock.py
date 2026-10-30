"""Data Mock Credential Manager ITAM Pro (Tahap 12)."""
from copy import deepcopy
from datetime import date, datetime
from typing import Any

from itam_pro.services.credential_config import CREDENTIAL_CATEGORIES
from itam_pro.services.mock.audit_mock import record_audit_event

MOCK_CREDENTIALS: list[dict[str, Any]] = [
    {
        "id": "CRD-0001",
        "jenis": "website",
        "induk": "Situs Contoh Utama",
        "peran": "cPanel",
        "target": "https://cpanel.contoh.example",
        "username": "admin_contoh",
        "secret": "CONTOH-cPanelPass123!",
        "tanggal_penting": [{"label": "Hosting", "tanggal": "2026-10-15"}],
        "terakhir_diganti": "2026-01-01",
        "field_tambahan": [],
        "catatan": "Akses root ke VPS hosting.",
    },
    {
        "id": "CRD-0002",
        "jenis": "website",
        "induk": "Situs Contoh Utama",
        "peran": "WordPress",
        "target": "https://contoh.example/wp-admin",
        "username": "wp_admin",
        "secret": "CONTOH-WpPass456!",
        "tanggal_penting": [{"label": "Domain", "tanggal": "2026-11-20"}],
        "terakhir_diganti": "2026-05-12",
        "field_tambahan": [],
        "catatan": "",
    },
    {
        "id": "CRD-0003",
        "jenis": "mikrotik",
        "induk": "Router Core Blok 14",
        "peran": "Router Utama",
        "target": "192.168.10.1",
        "username": "sysadmin",
        "secret": "CONTOH-MikroPass789",
        "tanggal_penting": [],
        "terakhir_diganti": "2025-10-10",
        "field_tambahan": [
            {"name": "port", "label": "Port", "value": "8291", "is_secret": False},
            {
                "name": "lokasi",
                "label": "Lokasi Fisik",
                "value": "Rak Server Utama",
                "is_secret": False,
            },
        ],
        "catatan": "Login Winbox.",
    },
    {
        "id": "CRD-0004",
        "jenis": "lainnya",
        "induk": "GitHub Organisasi",
        "peran": "Akun Eksternal",
        "target": "",
        "username": "itam_dev",
        "secret": "CONTOH-Github@2026",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-08-01",
        "field_tambahan": [
            {
                "name": "recovery_code",
                "label": "Recovery Code",
                "value": "CONTOH-8X2A-9P4K\nCONTOH-1M2N-4B5V",
                "is_secret": True,
            }
        ],
        "catatan": "Digunakan oleh tim dev.",
    },
    {
        "id": "CRD-0005",
        "jenis": "detail_pc",
        "induk": "PC Admin Server Room",
        "peran": "Windows",
        "target": "192.168.1.150",
        "username": "Administrator",
        "secret": "",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-09-01",
        "field_tambahan": [],
        "catatan": "PC Ruang NOC",
    },
    {
        "id": "CRD-0006",
        "jenis": "sql_server",
        "induk": "Database Produksi (Utama)",
        "peran": "Database Utama",
        "target": "10.10.1.12:5432",
        "username": "postgres_admin",
        "secret": "CONTOH-DbPostgre!2026",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-08-20",
        "field_tambahan": [],
        "catatan": "Hanya via VPN",
    },
    {
        "id": "CRD-0007",
        "jenis": "email",
        "induk": "Email Support Operasional",
        "peran": "Support",
        "target": "",
        "username": "support@contoh.example",
        "secret": "CONTOH-MailSupp@2026",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-04-10",
        "field_tambahan": [
            {
                "name": "recovery_email",
                "label": "Recovery Email",
                "value": "admin@contoh.example",
                "is_secret": False,
            }
        ],
        "catatan": "Akun mailbox support",
    },
    {
        "id": "CRD-0008",
        "jenis": "sosmed",
        "induk": "Instagram Perusahaan",
        "peran": "Instagram",
        "target": "",
        "username": "@itampro.official",
        "secret": "CONTOH-IgAdmin2026!",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-07-15",
        "field_tambahan": [
            {
                "name": "no_hp",
                "label": "Nomor HP Terhubung",
                "value": "081234567890",
                "is_secret": False,
            }
        ],
        "catatan": "Akun publik resmi",
    },
    {
        "id": "CRD-0009",
        "jenis": "internet_kantor",
        "induk": "Indihome Fiber Kantor",
        "peran": "ISP Utama",
        "target": "",
        "username": "",
        "secret": "",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-03-01",
        "field_tambahan": [
            {
                "name": "id_billing",
                "label": "ID Billing",
                "value": "123456789012",
                "is_secret": False,
            },
            {
                "name": "no_pelanggan",
                "label": "Nomor Pelanggan",
                "value": "021987654",
                "is_secret": False,
            },
            {
                "name": "id_layanan",
                "label": "ID Layanan",
                "value": "INET-FIBER-01",
                "is_secret": False,
            },
            {
                "name": "paket_layanan",
                "label": "Paket Layanan",
                "value": "100 Mbps Unlimited",
                "is_secret": False,
            },
        ],
        "catatan": "Router GPON di lantai 1",
    },
]


def _hitung_status_tanggal(tgl_penting: list[dict[str, Any]]) -> str:
    """Hitung status kedaluwarsa dari daftar tanggal penting."""
    if not tgl_penting:
        return "-"

    today = date.today()
    terdekat = None
    min_diff = 999999

    for item in tgl_penting:
        try:
            dt = datetime.strptime(str(item.get("tanggal", "")), "%Y-%m-%d").date()
            diff = (dt - today).days
            if terdekat is None or diff < min_diff:
                terdekat = dt
                min_diff = diff
        except (ValueError, KeyError):
            continue

    if terdekat is None:
        return "-"

    if min_diff < 0:
        return "Lewat jatuh tempo"
    elif min_diff <= 30:
        return "Segera habis"
    else:
        return "Aman"


def get_filtered_credentials(
    permissions: dict[str, str],
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Filter kredensial berdasarkan hak akses, tab, dan kata kunci."""
    search = str(filters.get("search", "")).strip().lower()
    tab = str(filters.get("tab", "Semua")).strip()

    filtered = []
    tab_counts: dict[str, int] = {
        "Semua": 0,
        "Website & Aplikasi": 0,
        "Perangkat": 0,
        "Akun Online": 0,
    }

    for item in MOCK_CREDENTIALS:
        j_key = item.get("jenis", "")
        # 1. Hak Akses (Layanan memfilter jenis)
        perm = permissions.get(j_key, "none")
        if perm == "none":
            continue

        cfg = CREDENTIAL_CATEGORIES.get(j_key)
        if not cfg:
            continue

        item_tab = cfg.get("tab", "")
        if item_tab in tab_counts:
            tab_counts[item_tab] += 1
        tab_counts["Semua"] += 1

        # 2. Filter Tab
        if tab != "Semua" and item_tab != tab:
            continue

        # 3. Pencarian
        if search:
            haystack = (
                f"{item.get('induk', '')} {item.get('peran', '')} "
                f"{item.get('target', '')} {item.get('username', '')} "
                f"{item.get('jenis', '')} {cfg.get('name', '')} "
                f"{item.get('catatan', '')}"
            ).lower()
            if search not in haystack:
                continue

        row = deepcopy(item)
        # HAPUS SECRET ASLI
        row["secret_ada"] = bool(row.get("secret"))
        if "secret" in row:
            del row["secret"]

        # Samarkan field tambahan rahasia
        for f in row.get("field_tambahan", []):
            if f.get("is_secret"):
                f["value_ada"] = bool(f.get("value"))
                if "value" in f:
                    del f["value"]

        # Tambah field presentasi
        row["jenis_label"] = cfg["name"]
        st = _hitung_status_tanggal(row.get("tanggal_penting", []))
        row["status"] = st
        if st == "Lewat jatuh tempo":
            row["status_variant"] = "danger"
        elif st == "Segera habis":
            row["status_variant"] = "warning"
        elif st == "Aman":
            row["status_variant"] = "success"
        else:
            row["status_variant"] = "neutral"

        filtered.append(row)

    filtered.sort(key=lambda x: str(x.get("induk", "")))

    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    return {
        "items": paginated,
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
        "tab_counts": tab_counts,
    }


async def reveal_mock_credential(crd_id: str, field_key: str, actor: str) -> dict[str, Any]:
    """Buka rahasia kredensial dan catat ke audit log."""
    for c in MOCK_CREDENTIALS:
        if c.get("id") == crd_id:
            val = ""
            if field_key in ("secret", "secret_copy"):
                val = str(c.get("secret", ""))
            else:
                clean_key = field_key.replace("_copy", "")
                for f in c.get("field_tambahan", []):
                    if f.get("name") == clean_key:
                        val = str(f.get("value", ""))

            # Catat audit log
            act_name = "credential.copy" if "copy" in field_key else "credential.reveal"
            record_audit_event(
                actor,
                act_name,
                crd_id,
                f"Membuka field {field_key.replace('_copy', '')}",
            )

            return {"value": val, "expires_in": 30}
    return {"value": "", "expires_in": 0}
