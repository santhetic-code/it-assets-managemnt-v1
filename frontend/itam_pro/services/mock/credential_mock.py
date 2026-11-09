"""Data Mock Credential Manager ITAM Pro (Tahap 12)."""

from copy import deepcopy
from datetime import date, datetime
from typing import Any

from itam_pro.services.credential_config import (
    CREDENTIAL_CATEGORIES,
    CREDENTIAL_TYPES_SCHEMA,
    LAPIS_1_MATRIX,
    ROLE_DEFAULT_DIVISION,
    can_access_credential_fe,
)
from itam_pro.services.mock.audit_mock import MOCK_AUDIT_LOGS, record_audit_event

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
    {
        "id": "CRD-0010",
        "jenis": "radmin",
        "type_code": "radmin",
        "induk": "Radmin · PC OPR H2H",
        "peran": "Operator & CS",
        "divisi": "Operator & CS",
        "subject_rank": 0,
        "min_view_rank": 0,
        "linked_asset_id": "PC-001",
        "target": "192.168.1.34",
        "username": "opr_h2h",
        "secret": "CONTOH-RadminOpr34!",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-09-15",
        "field_tambahan": [],
        "catatan": "Radmin operator transaksi H2H",
    },
    {
        "id": "CRD-0011",
        "jenis": "radmin",
        "type_code": "radmin",
        "induk": "Radmin · CS VOUCHER",
        "peran": "Voucher",
        "divisi": "Voucher",
        "subject_rank": 0,
        "min_view_rank": 0,
        "linked_asset_id": "PC-002",
        "target": "192.168.1.50",
        "username": "cs_voucher",
        "secret": "CONTOH-RadminVch50!",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-01-10",
        "field_tambahan": [],
        "catatan": "Radmin divisi voucher",
    },
    {
        "id": "CRD-0012",
        "jenis": "telegram",
        "type_code": "telegram",
        "induk": "Telegram CS Retail",
        "peran": "Operator & CS",
        "divisi": "Operator & CS",
        "subject_rank": 0,
        "min_view_rank": 0,
        "target": "@cs_retail",
        "username": "@cs_retail",
        "secret": "CONTOH-TeleCloud99!",
        "tanggal_penting": [],
        "terakhir_diganti": "2026-08-12",
        "field_tambahan": [
            {
                "name": "nomor_telepon",
                "label": "Nomor Telepon",
                "value": "081299887766",
                "is_secret": False,
            }
        ],
        "catatan": "Akun Telegram CS Retail",
    },
    {
        "id": "CRD-0013",
        "jenis": "cctv_wifi",
        "type_code": "cctv_wifi",
        "induk": "WiFi Kantor Lt. 2",
        "peran": "Umum",
        "divisi": "Umum",
        "subject_rank": 0,
        "min_view_rank": 0,
        "target": "SSID: Kantor-2",
        "username": "Kantor-2",
        "secret": "CONTOH-WifiKantorLt2!",
        "status_override": "Nonaktif",
        "tanggal_penting": [],
        "terakhir_diganti": "2025-12-01",
        "field_tambahan": [],
        "catatan": "SSID WiFi operasional lantai 2",
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


def _map_mock_type_code(item: dict[str, Any]) -> str:
    raw = str(item.get("type_code") or item.get("jenis", "pc")).lower()
    mapping = {
        "detail_pc": "pc",
        "sosmed": "telegram",
        "internet_kantor": "cctv_wifi",
        "lainnya": "cctv_wifi",
    }
    return mapping.get(raw, raw if raw in {t["kode"] for t in CREDENTIAL_TYPES_SCHEMA} else "pc")


def _infer_mock_division(item: dict[str, Any], t_code: str) -> str:
    if item.get("divisi"):
        return str(item["divisi"])
    if t_code == "website":
        return "Kreatif"
    if t_code in ("sql_server", "mikrotik"):
        return "IT"
    if t_code == "email":
        return "Umum"
    return "Operator & CS"


def get_filtered_credentials(
    permissions: dict[str, str],
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Filter kredensial berdasarkan hak akses (Lapis 1 & 2), jenis, divisi, status, dan teks."""
    search = str(filters.get("search", "")).strip().lower()
    tab = str(filters.get("tab", "Semua")).strip()
    type_code_filter = str(filters.get("type_code") or filters.get("type") or "").strip().lower()
    divisi_filter = str(filters.get("divisi", "")).strip()
    status_filter = str(filters.get("status", "")).strip()
    masa_berlaku_filter = (
        str(filters.get("masa_berlaku") or filters.get("card_filter") or "").strip().lower()
    )
    only_my_division = bool(filters.get("only_my_division", False))
    viewer_role = str(filters.get("viewer_role") or "").strip()
    viewer_div = str(
        filters.get("viewer_div") or ROLE_DEFAULT_DIVISION.get(viewer_role, "Manajemen")
    )
    matrix_override = filters.get("matrix_override")
    divisions_override = filters.get("divisions_override")

    today = date.today()
    filtered: list[dict[str, Any]] = []
    tab_counts: dict[str, int] = {
        "Semua": 0,
        "Website & Aplikasi": 0,
        "Perangkat": 0,
        "Akun Online": 0,
    }
    type_counts: dict[str, int] = {t["kode"]: 0 for t in CREDENTIAL_TYPES_SCHEMA}
    expiring_soon_count = 0
    old_password_count = 0
    expiry_reminders: list[dict[str, Any]] = []

    for item in MOCK_CREDENTIALS:
        if item.get("deleted_at"):
            continue
        j_key = item.get("jenis", "")
        t_code = _map_mock_type_code(item)
        div_name = _infer_mock_division(item, t_code)

        # 1. Evaluasi Hak Akses (Kompatibel dengan permissions dict test lama & aturan 2 lapis baru)
        if viewer_role:
            enriched_for_acl = {**item, "type_code": t_code, "divisi": div_name}
            if not can_access_credential_fe(
                viewer_role,
                viewer_div,
                enriched_for_acl,
                action="view",
                matrix_override=matrix_override,
                divisions_override=divisions_override,
            ):
                continue
            can_rev = can_access_credential_fe(
                viewer_role,
                viewer_div,
                enriched_for_acl,
                action="reveal",
                matrix_override=matrix_override,
                divisions_override=divisions_override,
            )
        else:
            perm = permissions.get(j_key, permissions.get(t_code, "none"))
            if perm == "none":
                continue
            can_rev = perm in ("reveal", "edit", "full")

        cfg = CREDENTIAL_CATEGORIES.get(j_key) or CREDENTIAL_CATEGORIES.get(t_code)
        if not cfg:
            continue

        # Hitung umur password & masa berlaku domain/hosting
        days_exp: int | None = None
        for dt_item in item.get("tanggal_penting", []):
            try:
                dt_val = datetime.strptime(str(dt_item.get("tanggal", "")), "%Y-%m-%d").date()
                diff = (dt_val - today).days
                if days_exp is None or diff < days_exp:
                    days_exp = diff
            except ValueError:
                continue

        rot_days = 0
        try:
            rot_dt = datetime.strptime(
                str(item.get("terakhir_diganti", "2026-09-01")), "%Y-%m-%d"
            ).date()
            rot_days = (today - rot_dt).days
        except ValueError:
            rot_days = 10
        is_old_pwd = rot_days > 90

        if days_exp is not None and days_exp <= 30:
            expiring_soon_count += 1
            stage = (
                "Kedaluwarsa"
                if days_exp < 0
                else ("H-1" if days_exp <= 1 else ("H-7" if days_exp <= 7 else "H-30"))
            )
            expiry_reminders.append(
                {
                    "id": item["id"],
                    "nama": item.get("induk", ""),
                    "days_left": days_exp,
                    "stage": stage,
                }
            )
        if is_old_pwd:
            old_password_count += 1

        # Hitung jumlah per Tab & per Tile Jenis (dalam lingkup akses pengguna)
        item_tab = cfg.get("tab", "Perangkat")
        if item_tab in tab_counts:
            tab_counts[item_tab] += 1
        tab_counts["Semua"] += 1
        if t_code in type_counts:
            type_counts[t_code] += 1

        # 2. Filter Tab / Tile Jenis
        if type_code_filter and type_code_filter not in ("semua", "all"):
            if t_code != type_code_filter and j_key != type_code_filter:
                continue
        elif tab != "Semua":
            if tab in (
                "website",
                "pc",
                "email",
                "sql_server",
                "telegram",
                "radmin",
                "mikrotik",
                "cctv_wifi",
            ):
                if t_code != tab and j_key != tab:
                    continue
            elif item_tab != tab:
                continue

        # 3. Filter Divisi & Hanya Divisi Saya
        if only_my_division and viewer_div and div_name.lower() != viewer_div.lower():
            continue
        if divisi_filter and divisi_filter not in ("Semua", "Semua divisi"):
            if div_name.lower() != divisi_filter.lower():
                continue

        # Tentukan label status sesuai Artboard 7
        st_override = str(item.get("status_override", "")).strip()
        if st_override.lower() == "nonaktif":
            status_lbl = "Nonaktif"
            status_var = "danger"
        elif days_exp is not None and days_exp < 0:
            status_lbl = "Kedaluwarsa"
            status_var = "danger"
        elif days_exp is not None and days_exp <= 30:
            status_lbl = f"Domain {days_exp} hari lagi"
            status_var = "warning"
        else:
            st_legacy = _hitung_status_tanggal(item.get("tanggal_penting", []))
            status_lbl = "Aktif" if st_legacy in ("-", "Aman") else st_legacy
            status_var = (
                "success"
                if status_lbl == "Aktif"
                else ("warning" if "habis" in status_lbl else "danger")
            )

        # 4. Filter Status & Masa Berlaku / Kartu KPI
        if status_filter and status_filter not in ("Semua", "Semua status"):
            if status_filter.lower() == "kedaluwarsa" and status_var != "danger":
                continue
            elif (
                status_filter.lower() in ("aktif", "nonaktif")
                and status_lbl.lower() != status_filter.lower()
            ):
                continue

        if masa_berlaku_filter in ("expiring", "segera kedaluwarsa", "<= 30 hari"):
            if days_exp is None or days_exp > 30:
                continue
        elif masa_berlaku_filter in ("old_password", "password lama", "> 90 hari"):
            if not is_old_pwd:
                continue

        # 5. Pencarian (JANGAN mencari di secret/password)
        if search:
            haystack = (
                f"{item.get('induk', '')} {item.get('peran', '')} {div_name} "
                f"{item.get('target', '')} {item.get('username', '')} "
                f"{item.get('jenis', '')} {cfg.get('name', '')} "
                f"{item.get('catatan', '')}"
            ).lower()
            if search not in haystack:
                continue

        row = deepcopy(item)
        # HAPUS SECRET ASLI (Wajib untuk keamanan & test_security_sanitization_strips_secret)
        row["secret_ada"] = bool(row.get("secret"))
        if "secret" in row:
            del row["secret"]

        for f in row.get("field_tambahan", []):
            if f.get("is_secret"):
                f["value_ada"] = bool(f.get("value"))
                if "value" in f:
                    del f["value"]

        t_meta = next(
            (t for t in CREDENTIAL_TYPES_SCHEMA if t["kode"] == t_code),
            CREDENTIAL_TYPES_SCHEMA[1],
        )
        row["type_code"] = t_code
        row["jenis_nama"] = t_meta["nama"]
        row["jenis_ikon"] = t_meta["ikon"]
        row["badge_bg"] = t_meta["badge_bg"]
        row["badge_fg"] = t_meta["badge_fg"]
        row["jenis_label"] = cfg["name"]
        row["divisi"] = div_name
        row["can_reveal"] = can_rev
        row["is_old_password"] = is_old_pwd
        row["days_until_expiry"] = days_exp

        if (
            div_name == "Accounting"
            or int(row.get("min_view_rank", 0) or 0) >= 40
            or int(row.get("subject_rank", 0) or 0) >= 30
        ):
            row["akses_label"] = "Hanya IT & Direksi"
        elif div_name == "Umum":
            row["akses_label"] = "Semua divisi"
        else:
            row["akses_label"] = "Divisi + atasan"

        st = _hitung_status_tanggal(row.get("tanggal_penting", []))
        row["status"] = st if not viewer_role else status_lbl
        row["status_display"] = status_lbl
        row["status_variant"] = status_var

        filtered.append(row)

    filtered.sort(key=lambda x: str(x.get("induk", "")))

    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    eff_role = viewer_role or "SPV Operasional"
    role_l1 = (matrix_override or LAPIS_1_MATRIX).get(eff_role, LAPIS_1_MATRIX["Owner"])
    type_tiles = []
    unlocked_cnt = 0
    for t_def in CREDENTIAL_TYPES_SCHEMA:
        kd = t_def["kode"]
        l1_mode = role_l1.get(kd, "full") if viewer_role else permissions.get(kd, "edit")
        is_locked = l1_mode == "none"
        if not is_locked:
            unlocked_cnt += 1
        type_tiles.append(
            {
                "id": t_def["id"],
                "kode": kd,
                "nama": t_def["nama"],
                "ikon": t_def["ikon"],
                "count": 0 if is_locked else type_counts.get(kd, 0),
                "locked": is_locked,
            }
        )

    revealed_today = sum(
        1 for lg in MOCK_AUDIT_LOGS if str(lg.get("action", "")).startswith("credential.")
    )

    return {
        "items": paginated,
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
        "tab_counts": tab_counts,
        "type_tiles": type_tiles,
        "kpi": {
            "bisa_diakses": tab_counts["Semua"],
            "unlocked_types_count": unlocked_cnt,
            "total_types_count": len(CREDENTIAL_TYPES_SCHEMA),
            "segera_kedaluwarsa": expiring_soon_count,
            "password_lama": old_password_count,
            "dibuka_hari_ini": revealed_today,
        },
        "expiry_reminders": expiry_reminders,
    }


def create_mock_credential(payload: dict[str, Any], actor: str = "Admin IT") -> dict[str, Any]:
    """Tambahkan kredensial baru ke MOCK_CREDENTIALS (dengan prefix CONTOH- untuk keamanan mock)."""
    next_num = len(MOCK_CREDENTIALS) + 1
    new_id = f"CRD-{next_num:04d}"
    t_code = str(payload.get("type_code") or payload.get("jenis", "website")).lower()
    jenis_key = "detail_pc" if t_code == "pc" else t_code
    if jenis_key not in CREDENTIAL_CATEGORIES:
        jenis_key = "website"

    raw_sec = str(payload.get("secret") or payload.get("password") or "Pass123!")
    if not raw_sec.startswith("CONTOH-"):
        raw_sec = f"CONTOH-{raw_sec}"

    tgl_penting: list[dict[str, str]] = []
    if payload.get("expired_domain"):
        tgl_penting.append({"label": "Domain", "tanggal": str(payload["expired_domain"])})
    if payload.get("expired_hosting"):
        tgl_penting.append({"label": "Hosting", "tanggal": str(payload["expired_hosting"])})

    new_item: dict[str, Any] = {
        "id": new_id,
        "jenis": jenis_key,
        "type_code": t_code,
        "induk": str(payload.get("nama") or payload.get("induk") or "Kredensial Baru"),
        "peran": str(payload.get("divisi") or "Operasional"),
        "divisi": str(payload.get("divisi") or "Umum"),
        "subject_rank": int(payload.get("subject_rank", 0) or 0),
        "min_view_rank": int(payload.get("min_view_rank", 0) or 0),
        "peer_access": bool(payload.get("peer_access", True)),
        "linked_asset_id": str(payload.get("linked_asset_id", "")),
        "target": str(payload.get("target", "")),
        "username": str(payload.get("username", "")),
        "secret": raw_sec,
        "data_publik": dict(payload.get("data_publik") or {}),
        "tanggal_penting": tgl_penting,
        "terakhir_diganti": date.today().isoformat(),
        "field_tambahan": list(payload.get("field_tambahan") or []),
        "catatan": str(payload.get("catatan", "")),
    }
    MOCK_CREDENTIALS.insert(0, new_item)
    record_audit_event(
        actor,
        "credential.create",
        new_id,
        f"Menambah kredensial {new_item['induk']} ({t_code})",
    )
    return new_item


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
