"""Layanan Audit Log (In-Memory) untuk ITAM Pro — selaras dengan kontrak backend."""

import csv
import io
import re
from copy import deepcopy
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    WIB_TZ = ZoneInfo("Asia/Jakarta")
except ZoneInfoNotFoundError:
    WIB_TZ = timezone(timedelta(hours=7))

BULAN_ID = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Ags",
    "Sep",
    "Okt",
    "Nov",
    "Des",
)

SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "key",
    "kredensial",
    "credential",
    "nilai_kredensial",
    "rahasia",
    "fernet",
    "hash",
)

WARNING_ACTIONS: tuple[str, ...] = (
    "login_gagal",
    "akun_terkunci",
    "reveal_ditolak",
    "hak_ditolak",
)

IMPORTANT_ACTIONS: tuple[str, ...] = (
    "reveal",
    "credential_reveal",
    "reveal_kredensial",
    "password_direset",
    "reset_password",
    "password_diubah",
    "peran_diubah",
    "pengguna_dibuat",
    "pengguna_dinonaktifkan",
    "pengguna_diaktifkan",
    "aset_dihapus",
    "aset_diarsipkan",
    "kredensial_dihapus",
    "kredensial_diarsipkan",
    "audit_diekspor",
)

_ACTION_LABELS: dict[str, str] = {
    "user_login": "Login berhasil",
    "login": "Login berhasil",
    "login_berhasil": "Login berhasil",
    "login_gagal": "Login gagal",
    "akun_terkunci": "Akun terkunci",
    "credential_reveal": "Reveal kredensial",
    "reveal": "Reveal kredensial",
    "reveal_ditolak": "Reveal ditolak",
    "hak_ditolak": "Akses ditolak",
    "password_direset": "Password direset",
    "password_diubah": "Password diubah",
    "peran_diubah": "Peran diubah",
    "pengguna_dibuat": "Pengguna dibuat",
    "pengguna_dinonaktifkan": "Pengguna dinonaktifkan",
    "pengguna_diaktifkan": "Pengguna diaktifkan",
    "asset_update": "Aset diubah",
    "aset_diubah": "Aset diubah",
    "audit_diekspor": "Audit diekspor",
}

_CSV_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _normalize_action_key(action: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (action or "").strip().lower()).strip("_")


def compute_mock_severity(action: str) -> str:
    """Hitung tingkat (Peringatan / Penting / Info) dari jenis aksi."""
    key = _normalize_action_key(action)
    if key in WARNING_ACTIONS:
        return "Peringatan"
    if key in IMPORTANT_ACTIONS:
        return "Penting"
    if ("aset" in key or "kredensial" in key) and ("hapus" in key or "arsip" in key):
        return "Penting"
    return "Info"


def sanitize_mock_detail(detail: str) -> str:
    cleaned = (detail or "").strip()
    for word in SENSITIVE_KEYWORDS:
        pat = re.compile(rf"([\w\-]*{word}[\w\-]*\s*[=:]\s*)([^\s,;)\]]+)", re.IGNORECASE)
        cleaned = pat.sub(r"\1(disembunyikan)", cleaned)
    return cleaned[:500]


def sanitize_mock_changes(changes: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if not changes:
        return []
    out: list[dict[str, str]] = []
    for c in changes:
        fld = str(c.get("field") or "").strip()
        if not fld:
            continue
        if any(kw in fld.lower() for kw in SENSITIVE_KEYWORDS):
            out.append(
                {"field": fld, "before": "(disembunyikan)", "after": "(disembunyikan)"}
            )
        else:
            b = c.get("before")
            a = c.get("after")
            out.append(
                {
                    "field": fld,
                    "before": (
                        sanitize_mock_detail(str(b)) if b not in (None, "") else "—"
                    ),
                    "after": (
                        sanitize_mock_detail(str(a)) if a not in (None, "") else "—"
                    ),
                }
            )
    return out


def sanitize_csv_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.lstrip(" ") and text.lstrip(" ")[0] in _CSV_INJECTION_PREFIXES:
        return "'" + text
    return text


def _parse_utc(ts_str: str) -> datetime:
    cleaned = (ts_str or "").strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        dt = datetime.now(UTC)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def format_mock_timestamps(ts_str: str) -> dict[str, str]:
    dt_utc = _parse_utc(ts_str)
    dt_wib = dt_utc.astimezone(WIB_TZ)
    tanggal_wib = f"{dt_wib.day} {BULAN_ID[dt_wib.month]} {dt_wib.year}"
    jam_wib = f"{dt_wib.strftime('%H:%M')} WIB"
    jam_utc = f"{dt_utc.strftime('%H:%M')} UTC"
    return {
        "iso_utc": dt_utc.isoformat(),
        "tanggal_wib": tanggal_wib,
        "jam_wib": jam_wib,
        "waktu_wib": f"{tanggal_wib} · {jam_wib}",
        "waktu_utc": f"{dt_utc.day} {BULAN_ID[dt_utc.month]} {dt_utc.year} · {jam_utc}",
        "waktu_lengkap": f"{tanggal_wib} · {jam_wib} ({jam_utc})",
    }


def _now_minus(minutes: int = 0) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes)).isoformat(timespec="seconds")


MOCK_AUDIT_LOGS: list[dict[str, Any]] = [
    {
        "id": "AUD-000738",
        "timestamp": _now_minus(12),
        "actor": "Administrator IT",
        "username": "admin",
        "role": "Administrator",
        "modul": "Autentikasi",
        "action": "user.login",
        "target_id": "admin",
        "detail": "Login berhasil ke sistem ITAM Pro",
        "hasil": "Berhasil",
        "ip_address": "10.20.5.12",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [],
    },
    {
        "id": "AUD-000737",
        "timestamp": _now_minus(45),
        "actor": "Member IT",
        "username": "member",
        "role": "Member",
        "modul": "Autentikasi",
        "action": "akun_terkunci",
        "target_id": "member",
        "detail": "Akun member terkunci (5× gagal login)",
        "hasil": "Ditolak",
        "ip_address": "10.20.5.41",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [],
    },
    {
        "id": "AUD-000736",
        "timestamp": _now_minus(65),
        "actor": "Administrator IT",
        "username": "admin",
        "role": "Administrator",
        "modul": "Kredensial",
        "action": "credential.reveal",
        "target_id": "CRD-0001",
        "detail": "Membuka field secret pada kredensial CRD-0001",
        "hasil": "Berhasil",
        "ip_address": "10.20.5.12",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [],
    },
    {
        "id": "AUD-000735",
        "timestamp": _now_minus(65),
        "actor": "Administrator IT",
        "username": "admin",
        "role": "Administrator",
        "modul": "Kredensial",
        "action": "credential.reveal",
        "target_id": "CRD-0001",
        "detail": "Membuka field secret pada kredensial CRD-0001",
        "hasil": "Berhasil",
        "ip_address": "10.20.5.12",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [],
    },
    {
        "id": "AUD-000734",
        "timestamp": _now_minus(80),
        "actor": "Member IT",
        "username": "member",
        "role": "Member",
        "modul": "Kredensial",
        "action": "reveal_ditolak",
        "target_id": "CRD-0004",
        "detail": "Reveal kredensial ditolak karena izin peran",
        "hasil": "Ditolak",
        "ip_address": "10.20.5.41",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [],
    },
    {
        "id": "AUD-000733",
        "timestamp": "2026-11-18T09:12:00+00:00",
        "actor": "Administrator IT",
        "username": "admin",
        "role": "Administrator",
        "modul": "Pengguna",
        "action": "password_direset",
        "target_id": "staf_it",
        "detail": "Administrator mereset password akun staf_it",
        "hasil": "Berhasil",
        "ip_address": "10.20.5.12",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [
            {"field": "password", "before": "(disembunyikan)", "after": "(disembunyikan)"}
        ],
    },
    {
        "id": "AUD-000731",
        "timestamp": "2026-11-18T04:05:00+00:00",
        "actor": "Member IT",
        "username": "member",
        "role": "Member",
        "modul": "Aset",
        "action": "asset.update",
        "target_id": "PC-0012",
        "detail": "Memperbarui lokasi dan status aset PC-0012",
        "hasil": "Berhasil",
        "ip_address": "10.20.5.41",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [
            {"field": "Lokasi", "before": "Kantor Blok 12", "after": "Kantor Blok 14"},
            {"field": "Digunakan oleh", "before": "—", "after": "Staf Keuangan"},
            {"field": "Status", "before": "Tidak Digunakan", "after": "Digunakan"},
        ],
    },
    {
        "id": "AUD-000730",
        "timestamp": "2026-10-30T09:15:00+00:00",
        "actor": "Admin IT",
        "username": "admin",
        "role": "Administrator",
        "modul": "Aset",
        "action": "asset.update",
        "target_id": "SRV-0001",
        "detail": "Memperbarui spesifikasi TDP server",
        "hasil": "Berhasil",
        "ip_address": "10.20.5.12",
        "perangkat": "Chrome 130 · Windows 11",
        "changes": [{"field": "TDP", "before": "300 W", "after": "350 W"}],
    },
]


def record_audit_event(
    actor: str,
    action: str,
    target_id: str,
    detail: str,
    *,
    username: str = "",
    role: str = "Administrator",
    modul: str = "",
    hasil: str = "Berhasil",
    ip_address: str = "10.20.5.12",
    perangkat: str = "Chrome 130 · Windows 11",
    changes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Catat aktivitas ke audit log in-memory (append-only, tanpa memuat secret/password)."""
    next_num = len(MOCK_AUDIT_LOGS) + 731
    inferred_mod = modul or (
        action.split(".", 1)[0].title() if "." in action else "Sistem"
    )
    entry = {
        "id": f"AUD-{next_num:06d}",
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "actor": actor,
        "username": username or actor.lower().replace(" ", "_"),
        "role": role,
        "modul": inferred_mod,
        "action": action,
        "target_id": target_id,
        "detail": sanitize_mock_detail(detail),
        "hasil": hasil,
        "ip_address": ip_address or "tidak diketahui",
        "perangkat": perangkat or "Tidak diketahui",
        "changes": sanitize_mock_changes(changes),
    }
    MOCK_AUDIT_LOGS.insert(0, entry)
    return entry


def update_audit_event(*_args: Any, **_kwargs: Any) -> None:
    raise ValueError("Audit log bersifat append-only dan tidak dapat diubah")


def delete_audit_event(*_args: Any, **_kwargs: Any) -> None:
    raise ValueError("Audit log bersifat append-only dan tidak dapat dihapus")


def _enrich_row(item: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(item)
    act = str(row.get("action") or row.get("aksi") or "")
    act_key = _normalize_action_key(act)
    ts = format_mock_timestamps(str(row.get("timestamp", "")))
    tingkat = compute_mock_severity(act)
    mod_prefix = (
        act.split(".", 1)[0].upper()
        if "." in act
        else str(row.get("modul", "SISTEM")).upper()
    )
    modul_label = str(row.get("modul") or mod_prefix.title())
    target_id = str(row.get("target_id") or "-")

    target_url = ""
    target_link_label = ""
    if "hapus" not in act_key and "arsip" not in act_key:
        if modul_label.lower() in ("aset", "asset", "inventory") and re.match(
            r"^[A-Z]+-\d+$", target_id.upper()
        ):
            target_url = f"/assets?search={target_id}"
            target_link_label = "Buka aset"
        elif modul_label.lower() in ("ip", "ip & server", "infrastructure"):
            target_url = f"/infrastructure/ip?search={target_id}"
            target_link_label = "Buka IP"
        elif modul_label.lower() in ("kredensial", "credential") and target_id.upper().startswith(
            "CRD-"
        ):
            target_url = f"/security/credentials?search={target_id}"
            target_link_label = "Buka kredensial"

    act_label = _ACTION_LABELS.get(act_key, act)
    actor_name = row.get("actor", "System")
    row.update(
        {
            "kode_audit": row.get("id", "AUD-000001"),
            "timestamp": ts["iso_utc"],
            "tanggal_wib": ts["tanggal_wib"],
            "jam_wib": ts["jam_wib"],
            "waktu_wib": ts["waktu_wib"],
            "waktu_utc": ts["waktu_utc"],
            "waktu_lengkap": ts["waktu_lengkap"],
            "time_display": ts["waktu_wib"],
            "relative_time": ts["waktu_wib"],
            "aksi": act,
            "aksi_label": act_label,
            "actor_and_action": f"{actor_name} · {act_label}",
            "nama_pengguna": actor_name,
            "username": row.get("username")
            or str(actor_name).lower().replace(" ", "_"),
            "role": row.get("role", "Administrator"),
            "modul": modul_label,
            "module_badge": mod_prefix,
            "module_variant": (
                "danger"
                if tingkat == "Peringatan"
                else ("warning" if tingkat == "Penting" else "info")
            ),
            "tingkat": tingkat,
            "hasil": row.get("hasil", "Berhasil"),
            "status": row.get("hasil", "Berhasil"),
            "ip_address": row.get("ip_address", "tidak diketahui"),
            "perangkat": row.get("perangkat", "Tidak diketahui"),
            "detail": sanitize_mock_detail(str(row.get("detail", ""))),
            "target_url": target_url,
            "target_link_label": target_link_label,
            "changes": sanitize_mock_changes(row.get("changes")),
            "group_count": 1,
            "grouped_ids": [row.get("id", "AUD-000001")],
            "grouped_timestamps": [
                {
                    "kode_audit": str(row.get("id", "AUD-000001")),
                    "tanggal_wib": ts["tanggal_wib"],
                    "jam_wib": ts["jam_wib"],
                    "waktu_wib": ts["waktu_wib"],
                    "waktu_utc": ts["waktu_utc"],
                    "waktu_lengkap": ts["waktu_lengkap"],
                }
            ],
        }
    )
    return row


def group_mock_audit_events(
    items: list[dict[str, Any]], window_seconds: int = 60
) -> list[dict[str, Any]]:
    grouped: list[dict[str, Any]] = []
    for item in items:
        item_dt = _parse_utc(item["timestamp"])
        item_key = (
            str(item["username"]).lower(),
            _normalize_action_key(str(item["aksi"])),
            str(item["target_id"]).lower(),
        )
        merged = False
        for prev in reversed(grouped):
            prev_dt = _parse_utc(prev["timestamp"])
            if abs((prev_dt - item_dt).total_seconds()) > window_seconds:
                break
            prev_key = (
                str(prev["username"]).lower(),
                _normalize_action_key(str(prev["aksi"])),
                str(prev["target_id"]).lower(),
            )
            if prev_key == item_key:
                prev["group_count"] = int(prev["group_count"]) + 1
                prev["grouped_ids"].append(item["kode_audit"])
                prev["grouped_timestamps"].extend(item["grouped_timestamps"])
                merged = True
                break
        if not merged:
            grouped.append(deepcopy(item))
    return grouped


def query_audit_logs(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Ambil daftar Audit Log dengan filter lengkap, tab tingkat, banner 24 jam, & grup xN."""
    enriched_all = [_enrich_row(item) for item in MOCK_AUDIT_LOGS]
    enriched_all.sort(key=lambda r: _parse_utc(r["timestamp"]), reverse=True)

    # Banner peringatan 24 jam terakhir
    cutoff_24h = datetime.now(UTC) - timedelta(hours=24)
    recent_warnings = [
        r
        for r in enriched_all
        if r["tingkat"] == "Peringatan" and _parse_utc(r["timestamp"]) >= cutoff_24h
    ]
    warning_banner = (
        {
            "visible": True,
            "count": len(recent_warnings),
            "summary": f"{len(recent_warnings)} peringatan dalam 24 jam terakhir: "
            + ", ".join(r["detail"] for r in recent_warnings[:2]),
        }
        if recent_warnings
        else {"visible": False, "count": 0, "summary": ""}
    )

    search = str(filters.get("search", "")).strip().lower()
    module = str(filters.get("module") or filters.get("modul") or "").strip().lower()
    pelaku = str(filters.get("pelaku") or filters.get("username") or "").strip().lower()
    tingkat = str(filters.get("tingkat") or "").strip().lower()
    periode = str(filters.get("periode") or "").strip().lower()
    date_from = str(filters.get("date_from") or "").strip()
    date_to = str(filters.get("date_to") or "").strip()
    hide_login = str(filters.get("hide_login_success", "")).lower() in (
        "true",
        "1",
        "yes",
    )
    do_group = str(filters.get("group", "true")).lower() not in ("false", "0")

    now_wib = datetime.now(UTC).astimezone(WIB_TZ)
    start_utc: datetime | None = None
    end_utc: datetime | None = None
    if periode in ("hari_ini", "hari ini", "today"):
        start_utc = datetime.combine(
            now_wib.date(), time.min, tzinfo=WIB_TZ
        ).astimezone(UTC)
    elif periode in ("7_hari", "7 hari", "7d"):
        start_utc = datetime.combine(
            now_wib.date() - timedelta(days=6), time.min, tzinfo=WIB_TZ
        ).astimezone(UTC)
    elif periode in ("30_hari", "30 hari", "30d"):
        start_utc = datetime.combine(
            now_wib.date() - timedelta(days=29), time.min, tzinfo=WIB_TZ
        ).astimezone(UTC)
    else:
        if date_from:
            try:
                start_utc = datetime.combine(
                    date.fromisoformat(date_from[:10]), time.min, tzinfo=WIB_TZ
                ).astimezone(UTC)
            except ValueError:
                pass
        if date_to:
            try:
                end_utc = datetime.combine(
                    date.fromisoformat(date_to[:10]), time.max, tzinfo=WIB_TZ
                ).astimezone(UTC)
            except ValueError:
                pass

    base_filtered: list[dict[str, Any]] = []
    for row in enriched_all:
        act_key = _normalize_action_key(row["aksi"])
        if (
            hide_login
            and act_key in ("user_login", "login", "login_berhasil")
            and row["hasil"] == "Berhasil"
        ):
            continue
        dt_u = _parse_utc(row["timestamp"])
        if start_utc and dt_u < start_utc:
            continue
        if end_utc and dt_u > end_utc:
            continue
        if module and module not in ("semua", "semua modul", "all"):
            if not (
                row["aksi"].lower().startswith(module)
                or row["modul"].lower() == module
                or module in row["module_badge"].lower()
            ):
                continue
        if pelaku and pelaku not in ("semua", "semua pelaku", "all"):
            if pelaku not in (row["username"].lower(), row["actor"].lower()):
                continue
        if search:
            haystack = (
                f"{row['kode_audit']} {row['actor']} {row['username']} "
                f"{row['aksi']} {row['aksi_label']} {row['modul']} "
                f"{row['target_id']} {row['detail']}"
            ).lower()
            if search not in haystack:
                continue
        base_filtered.append(row)

    tab_counts = {
        "Semua": len(base_filtered),
        "Peringatan": sum(1 for r in base_filtered if r["tingkat"] == "Peringatan"),
        "Penting": sum(1 for r in base_filtered if r["tingkat"] == "Penting"),
        "Info": sum(1 for r in base_filtered if r["tingkat"] == "Info"),
    }

    if tingkat and tingkat not in ("semua", "all"):
        filtered = [r for r in base_filtered if r["tingkat"].lower() == tingkat]
    else:
        filtered = base_filtered

    display_items = (
        group_mock_audit_events(filtered, window_seconds=60) if do_group else filtered
    )
    total = len(display_items)
    start = max(0, (page - 1) * page_size)
    return {
        "items": display_items[start : start + page_size],
        "total": total,
        "raw_total": len(filtered),
        "page": page,
        "page_size": page_size,
        "tab_counts": tab_counts,
        "warning_banner": warning_banner,
        "filter_options": {
            "modules": sorted({r["modul"] for r in enriched_all}),
            "actors": sorted({r["username"] for r in enriched_all}),
        },
    }


def get_mock_audit_detail(identifier: str) -> dict[str, Any]:
    cid = identifier.strip().lower()
    for item in MOCK_AUDIT_LOGS:
        if str(item.get("id", "")).lower() == cid:
            return _enrich_row(item)
    return {}


def export_mock_audit_csv(
    filters: dict[str, Any], actor: str = "Administrator IT"
) -> bytes:
    res = query_audit_logs({**filters, "group": "false"}, page=1, page_size=10000)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "ID Kejadian",
            "Waktu (WIB)",
            "Waktu (UTC)",
            "Pelaku",
            "Peran",
            "Modul",
            "Aksi",
            "Tingkat",
            "Target",
            "Hasil",
            "Alamat IP",
            "Perangkat",
            "Ringkasan",
        ]
    )
    for r in res["items"]:
        writer.writerow(
            [
                sanitize_csv_cell(r["kode_audit"]),
                sanitize_csv_cell(r["waktu_wib"]),
                sanitize_csv_cell(r["waktu_utc"]),
                sanitize_csv_cell(f"{r['actor']} ({r['username']})"),
                sanitize_csv_cell(r["role"]),
                sanitize_csv_cell(r["modul"]),
                sanitize_csv_cell(r["aksi_label"]),
                sanitize_csv_cell(r["tingkat"]),
                sanitize_csv_cell(r["target_id"]),
                sanitize_csv_cell(r["hasil"]),
                sanitize_csv_cell(r["ip_address"]),
                sanitize_csv_cell(r["perangkat"]),
                sanitize_csv_cell(r["detail"]),
            ]
        )
    record_audit_event(
        actor,
        "audit_diekspor",
        "audit_logs.csv",
        f"Export CSV Audit Log ({len(res['items'])} kejadian)",
        modul="Audit Log",
    )
    return buf.getvalue().encode("utf-8-sig")


__all__ = [
    "MOCK_AUDIT_LOGS",
    "compute_mock_severity",
    "delete_audit_event",
    "export_mock_audit_csv",
    "format_mock_timestamps",
    "get_mock_audit_detail",
    "group_mock_audit_events",
    "query_audit_logs",
    "record_audit_event",
    "sanitize_csv_cell",
    "update_audit_event",
]
