"""Skema Pydantic untuk Audit Log dan helper pencatatan jejak audit (B8)."""

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, col, select

from app.models.audit import AuditLog

AUD_CODE_PATTERN = re.compile(r"^AUD-(\d+)$")

SENSITIVE_KEYWORDS = ("password", "secret", "token", "fernet", "hash")


def generate_next_audit_code(session: Session) -> str:
    """Menghasilkan kode otomatis AUD-001, AUD-002, dst."""
    existing = session.exec(
        select(AuditLog.kode_audit).where(col(AuditLog.kode_audit).like("AUD-%"))
    ).all()
    max_num = 0
    for code in existing:
        match = AUD_CODE_PATTERN.match(code.strip().upper())
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"AUD-{max_num + 1:03d}"


def sanitize_audit_detail(detail: str) -> str:
    """Memastikan detail log tidak pernah memuat nilai password/secret mentah."""
    cleaned = detail.strip()
    for word in SENSITIVE_KEYWORDS:
        pattern = re.compile(rf"({word}\s*[=:]\s*)(\S+)", re.IGNORECASE)
        cleaned = pattern.sub(r"\1***", cleaned)
    return cleaned[:500]


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
    level_risiko: str = "Rendah",
    status: str = "Sukses",
    ip_address: str = "127.0.0.1",
    commit: bool = True,
) -> AuditLog:
    """Mencatat satu entri jejak audit ke tabel audit_logs."""
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
        level_risiko=level_risiko.strip() or "Rendah",
        status=status.strip() or "Sukses",
        ip_address=ip_address.strip() or "127.0.0.1",
    )
    session.add(row)
    if commit:
        session.commit()
        session.refresh(row)
    else:
        session.flush()
    return row


class AuditLogCreate(BaseModel):
    """Payload pencatatan log audit manual/internal."""

    model_config = ConfigDict(extra="allow")

    aksi: str = Field(min_length=1, max_length=60)
    modul: str = Field(default="Sistem", max_length=50)
    target_id: str = Field(default="-", max_length=80)
    detail: str = Field(default="", max_length=500)
    level_risiko: str = Field(default="Rendah", max_length=30)
    status: str = Field(default="Sukses", max_length=30)
    ip_address: str = Field(default="127.0.0.1", max_length=45)


class AuditLogPublic(BaseModel):
    """Representasi JSON log audit sesuai kontrak frontend."""

    id: int
    kode_audit: str
    id_audit: str
    waktu: str
    timestamp: str
    tanggal: str
    time_display: str = ""
    relative_time: str = "Baru saja"

    username: str
    pengguna: str
    nama_pengguna: str
    actor: str = ""
    role: str

    aksi: str
    action: str = ""
    actor_and_action: str = ""
    modul: str
    kategori: str
    module_badge: str = "SISTEM"
    module_variant: str = "neutral"
    target_id: str
    target: str = "-"
    entitas: str
    detail: str
    keterangan: str

    level_risiko: str
    risiko: str
    status: str
    ip_address: str

    @classmethod
    def from_model(cls, row: AuditLog) -> "AuditLogPublic":
        iso_time = row.created_at.isoformat()
        date_only = row.created_at.date().isoformat()
        time_display = row.created_at.strftime("%Y-%m-%d %H:%M")
        actor_name = row.nama_pengguna or row.username or "System"
        mod_upper = (row.modul or "SISTEM").strip().upper()
        variant_map = {
            "ASET": "info",
            "IP & SERVER": "info",
            "JARINGAN": "info",
            "PEMBELIAN": "success",
            "KEUANGAN": "success",
            "MAINTENANCE": "warning",
            "KREDENSIAL": "danger",
            "KEAMANAN": "danger",
            "AUTENTIKASI": "neutral",
            "PENGGUNA": "neutral",
        }
        mod_variant = variant_map.get(mod_upper, "neutral")
        return cls(
            id=row.id or 0,
            kode_audit=row.kode_audit,
            id_audit=row.kode_audit,
            waktu=iso_time,
            timestamp=iso_time,
            tanggal=date_only,
            time_display=time_display,
            relative_time=time_display,
            username=row.username,
            pengguna=row.username,
            nama_pengguna=actor_name,
            actor=actor_name,
            role=row.role,
            aksi=row.aksi,
            action=row.aksi,
            actor_and_action=f"{actor_name} · {row.aksi}",
            modul=row.modul,
            kategori=row.modul,
            module_badge=mod_upper,
            module_variant=mod_variant,
            target_id=row.target_id,
            target=f"{row.target_id} ({row.detail})" if row.detail else row.target_id,
            entitas=row.target_id,
            detail=row.detail,
            keterangan=row.detail,
            level_risiko=row.level_risiko,
            risiko=row.level_risiko,
            status=row.status,
            ip_address=row.ip_address,
        )


class AuditLogPageResponse(BaseModel):
    """Respons berhalaman daftar Audit Log untuk frontend."""

    items: list[AuditLogPublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, Any]

