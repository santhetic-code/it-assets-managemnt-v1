"""Skema Pydantic untuk Audit Log dan helper pencatatan jejak audit (B8)."""

import ipaddress
import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.models.audit import AuditLog, AuditLogImmutableError

AUD_CODE_PATTERN = re.compile(r"^AUD-(\d+)$")

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

UNKNOWN_ORIGIN = "tidak diketahui"
_CONTAINER_UA_MARKERS = (
    "python-httpx",
    "httpx/",
    "python-requests",
    "aiohttp",
    "testclient",
)
_ACTION_LABEL_MAP: dict[str, str] = {
    "login": "Login berhasil",
    "login_berhasil": "Login berhasil",
    "login_gagal": "Login gagal",
    "akun_terkunci": "Akun terkunci",
    "reveal": "Reveal kredensial",
    "reveal_kredensial": "Reveal kredensial",
    "copy_kredensial": "Salin kredensial",
    "reveal_ditolak": "Reveal ditolak",
    "hak_ditolak": "Akses ditolak",
    "password_direset": "Password direset",
    "reset_password": "Password direset",
    "password_diubah": "Password diubah",
    "ubah_password_mandiri": "Password diubah",
    "peran_diubah": "Peran diubah",
    "pengguna_dibuat": "Pengguna dibuat",
    "tambah_pengguna": "Pengguna dibuat",
    "pengguna_dinonaktifkan": "Pengguna dinonaktifkan",
    "pengguna_diaktifkan": "Pengguna diaktifkan",
    "audit_diekspor": "Audit diekspor",
}


def normalize_action_key(aksi: str) -> str:
    """Normalisasi nama aksi ke bentuk snake_case konsisten."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", (aksi or "").strip().lower()).strip("_")
    return cleaned


def compute_audit_severity(aksi: str) -> str:
    """Menghitung tingkat (Peringatan / Penting / Info) secara deterministik dari konfigurasi."""
    settings = get_settings()
    key = normalize_action_key(aksi)
    if key in settings.audit_warning_actions:
        return "Peringatan"
    if key in settings.audit_important_actions:
        return "Penting"
    # Cek kombinasi aksi hapus/arsip pada aset atau kredensial
    if ("aset" in key or "kredensial" in key) and ("hapus" in key or "arsip" in key):
        return "Penting"
    return "Info"


def format_action_label(aksi: str) -> str:
    key = normalize_action_key(aksi)
    return _ACTION_LABEL_MAP.get(key, aksi.strip() or "-")


def is_sensitive_field(field_name: str) -> bool:
    low = (field_name or "").strip().lower()
    return any(kw in low for kw in get_settings().audit_sensitive_keywords)


def sanitize_audit_detail(detail: str) -> str:
    """Memastikan detail log tidak pernah memuat nilai password/secret/token/key mentah."""
    cleaned = (detail or "").strip()
    for word in get_settings().audit_sensitive_keywords:
        # Pola key=value, key: value, "key": "value"
        pattern_quoted = re.compile(
            rf'(["\']?[\w\-]*{word}[\w\-]*["\']?\s*[=:]\s*)(["\'])(?:\\.|(?!\2).)*\2',
            re.IGNORECASE,
        )
        cleaned = pattern_quoted.sub(r"\1(disembunyikan)", cleaned)
        pattern_plain = re.compile(
            rf"([\w\-]*{word}[\w\-]*\s*[=:]\s*)([^\s,;)\]]+)",
            re.IGNORECASE,
        )
        cleaned = pattern_plain.sub(r"\1(disembunyikan)", cleaned)
    return cleaned[:500]


def sanitize_audit_changes(
    changes: list[dict[str, Any]] | None,
) -> list[dict[str, str]] | None:
    """Menyaring daftar diff Field | Sebelum | Sesudah agar field sensitif tidak tercatat."""
    if not changes:
        return None
    sanitized: list[dict[str, str]] = []
    for item in changes:
        field_name = str(item.get("field") or item.get("nama") or "").strip()
        if not field_name:
            continue
        if is_sensitive_field(field_name):
            sanitized.append(
                {
                    "field": field_name,
                    "before": "(disembunyikan)",
                    "after": "(disembunyikan)",
                }
            )
        else:
            before_raw = item.get("before", item.get("sebelum"))
            after_raw = item.get("after", item.get("sesudah"))
            sanitized.append(
                {
                    "field": field_name,
                    "before": (
                        sanitize_audit_detail(str(before_raw))
                        if before_raw not in (None, "")
                        else "—"
                    ),
                    "after": (
                        sanitize_audit_detail(str(after_raw))
                        if after_raw not in (None, "")
                        else "—"
                    ),
                }
            )
    return sanitized or None


def _is_trusted_proxy(peer_host: str | None) -> bool:
    if not peer_host:
        return False
    host = peer_host.strip()
    if host == "testclient":
        return True
    try:
        peer_ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    for cidr in get_settings().audit_trusted_proxy_cidrs:
        try:
            if peer_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def _validate_ip(raw_ip: str | None) -> str | None:
    if not raw_ip:
        return None
    candidate = raw_ip.strip()
    if not candidate:
        return None
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _sanitize_user_agent(raw_ua: str | None) -> str:
    ua = (raw_ua or "").strip()
    if not ua:
        return UNKNOWN_ORIGIN
    low = ua.lower()
    if low == UNKNOWN_ORIGIN or any(marker in low for marker in _CONTAINER_UA_MARKERS):
        return UNKNOWN_ORIGIN
    return ua[:255]


def extract_client_origin(request: Request | None) -> tuple[str, str]:
    """Mengambil (client_ip, client_ua) secara aman; hanya percaya header dari jaringan internal."""
    if request is None:
        return UNKNOWN_ORIGIN, UNKNOWN_ORIGIN

    peer_host = request.client.host if request.client else None
    trusted = _is_trusted_proxy(peer_host)

    resolved_ip: str | None = None
    if trusted:
        # Prioritas 1: X-Client-IP (dari frontend Reflex)
        resolved_ip = _validate_ip(request.headers.get("x-client-ip"))
        # Prioritas 2: X-Forwarded-For (dari reverse proxy tepercaya)
        if resolved_ip is None:
            xff = request.headers.get("x-forwarded-for", "")
            for part in xff.split(","):
                valid = _validate_ip(part)
                if valid:
                    resolved_ip = valid
                    break
        # Jangan pernah jatuh ke IP kontainer/proxy saat header klien tidak ada
        final_ip = resolved_ip or UNKNOWN_ORIGIN
        raw_ua = request.headers.get("x-client-ua") or request.headers.get("user-agent")
        final_ua = _sanitize_user_agent(raw_ua)
    else:
        # Pengirim langsung dari luar jaringan internal: abaikan header spoofing
        final_ip = _validate_ip(peer_host) or UNKNOWN_ORIGIN
        final_ua = _sanitize_user_agent(request.headers.get("user-agent"))

    return final_ip, final_ua


def format_device_display(user_agent: str) -> str:
    """Memformat User-Agent menjadi ringkas seperti 'Chrome 130 · Windows 11'."""
    ua = (user_agent or "").strip()
    if not ua or ua.lower() == UNKNOWN_ORIGIN:
        return "Tidak diketahui"
    if any(m in ua.lower() for m in _CONTAINER_UA_MARKERS):
        return "Tidak diketahui"

    browser = "Browser"
    for pattern, label in (
        (r"Edg/(\d+)", "Edge"),
        (r"OPR/(\d+)", "Opera"),
        (r"Chrome/(\d+)", "Chrome"),
        (r"Firefox/(\d+)", "Firefox"),
        (r"Version/(\d+).*Safari", "Safari"),
    ):
        m = re.search(pattern, ua)
        if m:
            browser = f"{label} {m.group(1)}"
            break

    os_name = "OS tidak diketahui"
    if "Windows NT 10.0" in ua or "Windows 11" in ua:
        os_name = "Windows 11"
    elif "Windows NT 6.3" in ua:
        os_name = "Windows 8.1"
    elif "Windows NT 6.1" in ua:
        os_name = "Windows 7"
    elif "Windows" in ua:
        os_name = "Windows"
    elif m_and := re.search(r"Android\s+(\d+)", ua):
        os_name = f"Android {m_and.group(1)}"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
    elif "Mac OS X" in ua:
        os_name = "macOS"
    elif "Linux" in ua:
        os_name = "Linux"

    return f"{browser} · {os_name}"


def format_audit_timestamps(dt: datetime) -> dict[str, str]:
    """Konversi UTC -> WIB ('19 Nov 2026', '04:29 WIB', '19 Nov 2026 · 04:29 WIB (21:29 UTC)')."""
    dt_utc = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    dt_wib = dt_utc.astimezone(WIB_TZ)
    tanggal_wib = f"{dt_wib.day} {BULAN_ID[dt_wib.month]} {dt_wib.year}"
    jam_wib = f"{dt_wib.strftime('%H:%M')} WIB"
    jam_utc = f"{dt_utc.strftime('%H:%M')} UTC"
    return {
        "iso_utc": dt_utc.isoformat(),
        "tanggal_wib": tanggal_wib,
        "jam_wib": jam_wib,
        "waktu_wib": f"{tanggal_wib} · {jam_wib}",
        "waktu_lengkap": f"{tanggal_wib} · {jam_wib} ({jam_utc})",
        "waktu_utc": f"{dt_utc.day} {BULAN_ID[dt_utc.month]} {dt_utc.year} · {jam_utc}",
    }


def _normalize_hasil(status_raw: str) -> str:
    low = (status_raw or "").strip().lower()
    if low in ("ditolak", "denied", "forbidden"):
        return "Ditolak"
    if low in ("gagal", "failed", "error"):
        return "Gagal"
    return "Berhasil"


def generate_next_audit_code(session: Session) -> str:
    """Menghasilkan kode otomatis berurutan AUD-000001, AUD-000002, dst."""
    existing = session.exec(
        select(AuditLog.kode_audit).where(col(AuditLog.kode_audit).like("AUD-%"))
    ).all()
    max_num = 0
    for code in existing:
        match = AUD_CODE_PATTERN.match(code.strip().upper())
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"AUD-{max_num + 1:06d}"


def record_audit_log(
    session: Session,
    *,
    username: str,
    nama_pengguna: str = "",
    role: str = "Viewer",
    aksi: str,
    modul: str,
    target_id: str = "-",
    detail: str = "",
    level_risiko: str = "",
    status: str = "Berhasil",
    ip_address: str | None = None,
    user_agent: str | None = None,
    changes: list[dict[str, Any]] | None = None,
    request: Request | None = None,
    commit: bool = True,
) -> AuditLog:
    """Mencatat satu entri jejak audit (append-only) dengan tingkat terhitung & asal klien valid."""
    req_ip, req_ua = extract_client_origin(request)

    if ip_address is not None and ip_address.strip():
        validated_manual_ip = _validate_ip(ip_address)
        final_ip = validated_manual_ip if validated_manual_ip else UNKNOWN_ORIGIN
    else:
        final_ip = req_ip

    final_ua = _sanitize_user_agent(user_agent) if user_agent is not None else req_ua
    computed_tingkat = compute_audit_severity(aksi)
    risk_legacy_map = {"Peringatan": "Tinggi", "Penting": "Sedang", "Info": "Rendah"}
    final_risk = level_risiko.strip() or risk_legacy_map[computed_tingkat]

    code = generate_next_audit_code(session)
    row = AuditLog(
        kode_audit=code,
        username=username.strip() or "system",
        nama_pengguna=nama_pengguna.strip() or username.strip() or "System",
        role=role.strip() or "Viewer",
        aksi=aksi.strip(),
        modul=modul.strip(),
        target_id=target_id.strip() or "-",
        detail=sanitize_audit_detail(detail),
        level_risiko=final_risk,
        status=_normalize_hasil(status),
        ip_address=final_ip,
        user_agent=final_ua,
        changes=sanitize_audit_changes(changes),
    )
    session.add(row)
    if commit:
        session.commit()
        session.refresh(row)
    else:
        session.flush()
    return row


# Alias untuk menjaga konsistensi penamaan dokumentasi
record_audit_event = record_audit_log


def update_audit_log(*_args: Any, **_kwargs: Any) -> None:
    """Service eksplisit menolak pembaruan Audit Log (append-only)."""
    raise AuditLogImmutableError("Audit log bersifat append-only dan tidak dapat diubah")


def delete_audit_log(*_args: Any, **_kwargs: Any) -> None:
    """Service eksplisit menolak penghapusan Audit Log (append-only)."""
    raise AuditLogImmutableError("Audit log bersifat append-only dan tidak dapat dihapus")


def get_recent_audit_logs(session: Session, limit: int = 8) -> list["AuditLogPublic"]:
    """Sumber data bersama untuk Dashboard ('Aktivitas Terbaru') dan halaman Audit Log."""
    rows = list(
        session.exec(
            select(AuditLog)
            .order_by(col(AuditLog.created_at).desc(), col(AuditLog.id).desc())
            .limit(limit)
        ).all()
    )
    return [AuditLogPublic.from_model(r) for r in rows]


class AuditLogCreate(BaseModel):
    """Payload pencatatan log audit manual/internal."""

    model_config = ConfigDict(extra="allow")

    aksi: str = Field(min_length=1, max_length=60)
    modul: str = Field(default="Sistem", max_length=50)
    target_id: str = Field(default="-", max_length=80)
    detail: str = Field(default="", max_length=500)
    level_risiko: str = Field(default="", max_length=30)
    status: str = Field(default="Berhasil", max_length=30)
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=255)
    changes: list[dict[str, Any]] | None = None


class AuditLogPublic(BaseModel):
    """Representasi JSON log audit sesuai kontrak frontend & artboard."""

    id: int
    kode_audit: str
    id_audit: str
    waktu: str
    timestamp: str
    tanggal: str
    tanggal_wib: str
    jam_wib: str
    waktu_wib: str
    waktu_utc: str
    waktu_lengkap: str
    time_display: str = ""
    relative_time: str = ""

    username: str
    pengguna: str
    nama_pengguna: str
    actor: str = ""
    role: str

    aksi: str
    aksi_label: str
    action: str = ""
    actor_and_action: str = ""
    modul: str
    kategori: str
    module_badge: str = "SISTEM"
    module_variant: str = "neutral"
    target_id: str
    target: str = "-"
    target_url: str = ""
    target_link_label: str = ""
    entitas: str
    detail: str
    keterangan: str

    tingkat: str  # Peringatan | Penting | Info
    level_risiko: str
    risiko: str
    status: str
    hasil: str  # Berhasil | Ditolak | Gagal
    ip_address: str
    user_agent: str
    perangkat: str
    changes: list[dict[str, str]] = Field(default_factory=list)

    # Penggabungan tampilan xN dalam 60 detik
    group_count: int = 1
    grouped_ids: list[str] = Field(default_factory=list)
    grouped_timestamps: list[dict[str, str]] = Field(default_factory=list)

    @staticmethod
    def _resolve_target_link(modul: str, target_id: str, aksi: str) -> tuple[str, str]:
        tid = (target_id or "").strip()
        if not tid or tid in ("-", "—"):
            return "", ""
        aksi_key = normalize_action_key(aksi)
        if "hapus" in aksi_key or "arsip" in aksi_key:
            return "", ""
        mod_low = (modul or "").strip().lower()
        if mod_low in ("aset", "inventory") and re.match(r"^[A-Z]+-\d+$", tid.upper()):
            return f"/assets?search={tid}", "Buka aset"
        if mod_low in ("ip", "ip & server", "infrastructure", "jaringan"):
            return f"/infrastructure/ip?search={tid}", "Buka IP"
        if mod_low in ("kredensial", "credential manager", "security") and tid.upper().startswith(
            "CRD-"
        ):
            return f"/security/credentials?search={tid}", "Buka kredensial"
        return "", ""

    @classmethod
    def from_model(cls, row: AuditLog) -> "AuditLogPublic":
        ts = format_audit_timestamps(row.created_at)
        actor_name = row.nama_pengguna or row.username or "System"
        mod_upper = (row.modul or "SISTEM").strip().upper()
        variant_map = {
            "ASET": "info",
            "INVENTORY": "info",
            "IP": "info",
            "IP & SERVER": "info",
            "INFRASTRUCTURE": "info",
            "JARINGAN": "info",
            "PEMBELIAN": "success",
            "KEUANGAN": "success",
            "MAINTENANCE": "warning",
            "KREDENSIAL": "danger",
            "KEAMANAN": "danger",
            "AUTENTIKASI": "neutral",
            "PENGGUNA": "neutral",
            "AUDIT LOG": "neutral",
        }
        mod_variant = variant_map.get(mod_upper, "neutral")
        tingkat = compute_audit_severity(row.aksi)
        hasil = _normalize_hasil(row.status)
        aksi_lbl = format_action_label(row.aksi)
        target_url, target_link_label = cls._resolve_target_link(
            row.modul, row.target_id, row.aksi
        )
        safe_changes = sanitize_audit_changes(row.changes) or []
        ua_val = row.user_agent or UNKNOWN_ORIGIN

        return cls(
            id=row.id or 0,
            kode_audit=row.kode_audit,
            id_audit=row.kode_audit,
            waktu=ts["iso_utc"],
            timestamp=ts["iso_utc"],
            tanggal=ts["tanggal_wib"],
            tanggal_wib=ts["tanggal_wib"],
            jam_wib=ts["jam_wib"],
            waktu_wib=ts["waktu_wib"],
            waktu_utc=ts["waktu_utc"],
            waktu_lengkap=ts["waktu_lengkap"],
            time_display=ts["waktu_wib"],
            relative_time=ts["waktu_wib"],
            username=row.username,
            pengguna=row.username,
            nama_pengguna=actor_name,
            actor=actor_name,
            role=row.role,
            aksi=row.aksi,
            aksi_label=aksi_lbl,
            action=aksi_lbl,
            actor_and_action=f"{actor_name} · {aksi_lbl}",
            modul=row.modul,
            kategori=row.modul,
            module_badge=mod_upper,
            module_variant=mod_variant,
            target_id=row.target_id,
            target=f"{row.target_id} ({row.detail})" if row.detail else row.target_id,
            target_url=target_url,
            target_link_label=target_link_label,
            entitas=row.target_id,
            detail=sanitize_audit_detail(row.detail),
            keterangan=sanitize_audit_detail(row.detail),
            tingkat=tingkat,
            level_risiko=row.level_risiko,
            risiko=row.level_risiko,
            status=hasil,
            hasil=hasil,
            ip_address=row.ip_address or UNKNOWN_ORIGIN,
            user_agent=ua_val,
            perangkat=format_device_display(ua_val),
            changes=safe_changes,
            group_count=1,
            grouped_ids=[row.kode_audit],
            grouped_timestamps=[
                {
                    "kode_audit": row.kode_audit,
                    "tanggal_wib": ts["tanggal_wib"],
                    "jam_wib": ts["jam_wib"],
                    "waktu_wib": ts["waktu_wib"],
                    "waktu_utc": ts["waktu_utc"],
                    "waktu_lengkap": ts["waktu_lengkap"],
                }
            ],
        )


class AuditLogPageResponse(BaseModel):
    """Respons berhalaman daftar Audit Log untuk frontend."""

    items: list[AuditLogPublic]
    total: int
    raw_total: int = 0
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, Any]
    warning_banner: dict[str, Any] = Field(default_factory=dict)
    filter_options: dict[str, list[str]] = Field(default_factory=dict)
