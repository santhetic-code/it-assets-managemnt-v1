"""Endpoint CRUD IP Address & Virtual Machine (konflik IP, VM tanpa host, urut numerik)."""

import csv
import io
import logging
import time
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import case, func, or_
from sqlalchemy import select as sa_select
from sqlmodel import Session, col, select

from app.core.ip_export import (
    build_a4_landscape_ip_pdf,
    build_openxml_xlsx,
    read_xlsx_rows,
)
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.base import utcnow
from app.models.ip_allocation import IPAllocation, IPSubnet
from app.schemas.audit import record_audit_log
from app.schemas.ip_allocation import (
    DEFAULT_REGISTERED_SUBNET,
    IPAllocationCreate,
    IPAllocationPageResponse,
    IPAllocationPublic,
    IPAllocationUpdate,
    has_kendala,
    is_ip_in_subnets,
    normalize_keterangan,
    parse_and_validate_ipv4,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Sesi cache in-memory untuk transaksi impor 2-fase (TTL 1 jam)
_IMPORT_SESSIONS: dict[str, dict[str, Any]] = {}

# Cache pendek (45 detik) untuk agregasi statistik & opsi metadata (C1)
_STATS_CACHE: dict[str, Any] = {"expires_at": 0.0, "sig": None, "data": None}
_STATS_CACHE_TTL = 45.0


def invalidate_ip_cache() -> None:
    """Batalkan cache statistik saat ada tambah/ubah/hapus/import (C1)."""
    _STATS_CACHE["expires_at"] = 0.0
    _STATS_CACHE["sig"] = None
    _STATS_CACHE["data"] = None


def _prune_import_sessions() -> None:
    """Membersihkan sesi impor yang telah berusia lebih dari 1 jam."""
    now = time.time()
    expired = [k for k, v in _IMPORT_SESSIONS.items() if now - v.get("created_at", 0) > 3600]
    for k in expired:
        _IMPORT_SESSIONS.pop(k, None)


def _ensure_registered_subnets(session: Session) -> list[IPSubnet]:
    """Pastikan tabel ip_subnets memiliki minimal 1 baris awal 192.168.1.0/24 (B4)."""
    subnets = list(session.exec(select(IPSubnet).order_by(col(IPSubnet.id).asc())).all())
    if not subnets:
        default_sub = IPSubnet(
            cidr=DEFAULT_REGISTERED_SUBNET,
            nama="Subnet Utama LAN",
            dibuat_oleh="system",
        )
        session.add(default_sub)
        session.commit()
        session.refresh(default_sub)
        subnets = [default_sub]
    return subnets


def _validate_ip_in_registered_subnets(
    session: Session,
    canonical_ip: str,
    allowed_cidrs: Sequence[str] | None = None,
) -> None:
    """Menolak IP baru di luar subnet terdaftar (B4)."""
    cidrs = (
        list(allowed_cidrs)
        if allowed_cidrs is not None
        else [s.cidr for s in _ensure_registered_subnets(session)]
    )
    if not is_ip_in_subnets(canonical_ip, cidrs):
        label = ", ".join(cidrs) if cidrs else DEFAULT_REGISTERED_SUBNET
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"IP di luar subnet terdaftar ({label})",
        )


def _check_ip_conflict(
    session: Session,
    ip_address: str,
    new_status: str,
    exclude_id: int | None = None,
) -> None:
    """Menolak penggunaan IP yang sama oleh dua entri aktif dengan HTTP 409 Conflict."""
    if new_status.lower() in ("bebas", "tersedia", "nonaktif"):
        return

    stmt = select(IPAllocation).where(
        IPAllocation.ip_address == ip_address,
        func.lower(IPAllocation.status).notin_(["bebas", "tersedia", "nonaktif"]),
    )
    if exclude_id is not None:
        stmt = stmt.where(IPAllocation.id != exclude_id)

    existing = session.exec(stmt).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Konflik IP: alamat {ip_address} sudah digunakan oleh '{existing.nama_perangkat}'"
            ),
        )


def _validate_and_resolve_host(
    session: Session,
    id_aset_host: str | None,
    host_name: str,
) -> tuple[str | None, str]:
    """Memvalidasi id_aset_host terhadap tabel assets bila diisi."""
    if not id_aset_host:
        return None, host_name

    host_asset = session.exec(
        select(Asset).where(func.lower(Asset.id_aset) == id_aset_host.lower())
    ).first()
    if host_asset is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Host aset '{id_aset_host}' tidak ditemukan di inventaris aset",
        )
    if host_asset.status.lower() in ("rusak", "nonaktif"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Host aset '{host_asset.id_aset}' berstatus {host_asset.status} "
                "dan tidak dapat menampung VM"
            ),
        )
    resolved_name = host_name or host_asset.nama_aset
    return host_asset.id_aset, resolved_name


def _detect_orphan_and_conflict_maps(
    session: Session,
    rows: Sequence[IPAllocation] | None = None,
) -> tuple[set[int], set[str]]:
    """Mendeteksi ID baris VM tanpa host aktif dan daftar IP yang mengalami konflik via SQL."""
    conflict_stmt = (
        select(IPAllocation.ip_address)
        .where(func.lower(IPAllocation.status).notin_(["bebas", "tersedia", "nonaktif"]))
        .group_by(IPAllocation.ip_address)
        .having(func.count(col(IPAllocation.id)) > 1)
    )
    conflict_ips = set(session.exec(conflict_stmt).all())

    active_assets = {
        id_aset.upper()
        for id_aset in session.exec(
            select(Asset.id_aset).where(func.lower(Asset.status).notin_(["rusak", "nonaktif"]))
        ).all()
    }

    vm_rows = session.exec(
        select(IPAllocation.id, IPAllocation.host_name, IPAllocation.id_aset_host).where(
            col(IPAllocation.is_vm).is_(True)
        )
    ).all()
    orphan_ids: set[int] = set()
    for r_id, r_host_name, r_host_id in vm_rows:
        if r_id is None:
            continue
        if not (r_host_name or "").strip() and not r_host_id:
            orphan_ids.add(r_id)
        elif r_host_id and r_host_id.upper() not in active_assets:
            orphan_ids.add(r_id)

    return orphan_ids, conflict_ips


def _build_counts_and_summary(
    rows: Sequence[IPAllocation],
    orphan_ids: set[int] | None = None,
    conflict_ips: set[str] | None = None,
) -> tuple[dict[str, int], dict[str, Any]]:
    """Menghitung statistik tab dan kartu KPI alokasi IP dari daftar baris."""
    orphan_ids = orphan_ids or set()
    conflict_ips = conflict_ips or set()

    total_ip = len(rows)
    total_fisik = sum(1 for r in rows if not r.is_vm)
    total_vm = sum(1 for r in rows if r.is_vm)
    total_aktif = sum(1 for r in rows if r.status.lower() == "aktif")
    total_nonaktif = sum(1 for r in rows if r.status.lower() == "nonaktif")
    total_konflik = len(conflict_ips)
    total_orphan = sum(1 for r in rows if r.id is not None and r.id in orphan_ids)

    counts = {
        "Semua": total_ip,
        "Fisik": total_fisik,
        "VM": total_vm,
        "Operasional": total_fisik,
        "Addon (VM)": total_vm,
        "Konflik": total_konflik,
        "VM Tanpa Host": total_orphan,
    }
    summary: dict[str, Any] = {
        "total_ip": total_ip,
        "total_fisik": total_fisik,
        "total_vm": total_vm,
        "operasional": total_fisik,
        "addon_vm": total_vm,
        "aktif": total_aktif,
        "nonaktif": total_nonaktif,
        "konflik": total_konflik,
        "vm_tanpa_host": total_orphan,
    }
    return counts, summary


def _get_cached_ip_metadata(session: Session) -> dict[str, Any]:
    """Mengambil statistik dengan SATU query agregat + cache pendek 45 detik (C1, A3, B4)."""
    now = time.time()
    subnets = _ensure_registered_subnets(session)
    allowed_cidrs = [s.cidr for s in subnets]

    srv_assets = session.exec(
        select(Asset.id_aset, Asset.nama_aset, Asset.kategori, Asset.status)
        .where(col(Asset.kategori).in_(["Server", "PC"]))
        .order_by(col(Asset.id_aset).asc())
    ).all()
    sig = (tuple((a[0], a[3]) for a in srv_assets), tuple(allowed_cidrs))

    if (
        _STATS_CACHE["data"] is not None
        and _STATS_CACHE["sig"] == sig
        and now < _STATS_CACHE["expires_at"]
    ):
        return _STATS_CACHE["data"]

    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session)

    # Satu query agregat COUNT ... CASE WHEN (C1).
    # Memakai select SQLAlchemy karena select SQLModel hanya mendukung maksimal 4 kolom.
    agg_row = (
        session.connection()
        .execute(
            sa_select(
                func.count(col(IPAllocation.id)),
                func.coalesce(func.sum(case((col(IPAllocation.is_vm).is_(False), 1), else_=0)), 0),
                func.coalesce(func.sum(case((col(IPAllocation.is_vm).is_(True), 1), else_=0)), 0),
                func.coalesce(
                    func.sum(
                        case(
                            (func.lower(IPAllocation.status).in_(["aktif", "digunakan"]), 1),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                col(IPAllocation.ip_address).like("192.168.1.%")
                                & ~col(IPAllocation.ip_address).in_(
                                    ["192.168.1.0", "192.168.1.255"]
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                col(IPAllocation.ip_address).in_(conflict_ips)
                                if conflict_ips
                                else (func.lower(IPAllocation.status) == "konflik"),
                                1,
                            ),
                            (func.lower(IPAllocation.status) == "konflik", 1),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
        )
        .one()
    )

    total = int(agg_row[0] or 0)
    fisik_count = int(agg_row[1] or 0)
    vm_count = int(agg_row[2] or 0)
    aktif_count = int(agg_row[3] or 0)
    terpakai_subnet = int(agg_row[4] or 0)
    konflik_count = int(agg_row[5] or 0)
    orphan_count = len(orphan_ids)
    kosong_count = max(0, 254 - terpakai_subnet)

    tab_counts = {
        "Semua": total,
        "all": total,
        "Fisik": fisik_count,
        "VM": vm_count,
        "Operasional": fisik_count,
        "Addon (VM)": vm_count,
        "Konflik": konflik_count,
        "VM Tanpa Host": orphan_count,
    }
    summary = {
        "total": total,
        "total_ip": total,
        "aktif": aktif_count,
        "terpakai": aktif_count,
        "bebas": kosong_count,
        "tersedia": kosong_count,
        "kosong": kosong_count,
        "total_vm": vm_count,
        "vm": vm_count,
        "fisik": fisik_count,
        "operasional": fisik_count,
        "addon": vm_count,
        "konflik": konflik_count,
        "bentrok": konflik_count,
        "vm_tanpa_host": orphan_count,
        "orphan_vm": orphan_count,
    }
    kpi_fe = {
        "total_ip": total,
        "fisik": fisik_count,
        "vm": vm_count,
        "kosong": kosong_count,
        "operasional": fisik_count,
        "addon": vm_count,
        "bentrok": konflik_count,
        "vm_tanpa_host": orphan_count,
    }

    # A3: Filter Host HANYA berisi host yang benar-benar punya VM terhubung beserta jumlah VM
    server_name_map = {a[0].upper(): a[1] for a in srv_assets if a[2].lower() == "server"}
    vm_host_rows = session.exec(
        select(
            IPAllocation.id_aset_host,
            IPAllocation.host_name,
            func.count(col(IPAllocation.id)),
        )
        .where(col(IPAllocation.is_vm).is_(True))
        .group_by(IPAllocation.id_aset_host, IPAllocation.host_name)
    ).all()

    host_vm_counts: dict[str, int] = {}
    for h_id, h_name, cnt in vm_host_rows:
        clean_id = (h_id or "").strip().upper()
        clean_name = (h_name or "").strip()
        if not clean_id and not clean_name:
            continue
        if clean_id:
            resolved_name = server_name_map.get(clean_id) or clean_name
            base_label = f"{clean_id} ({resolved_name})" if resolved_name else clean_id
        else:
            base_label = clean_name
        host_vm_counts[base_label] = host_vm_counts.get(base_label, 0) + cnt

    host_options = ["Semua host"] + [
        f"{lbl} · {cnt} VM" for lbl, cnt in sorted(host_vm_counts.items()) if cnt > 0
    ]

    # Daftar server fisik tetap utuh untuk Form Tambah/Edit IP (A3)
    host_server_options = [f"{a[0]} ({a[1]})" for a in srv_assets if a[2].lower() == "server"]
    server_asset_ids = ["—"] + [a[0] for a in srv_assets]

    os_rows = session.exec(
        select(IPAllocation.os).where(col(IPAllocation.os) != "").distinct()
    ).all()
    os_set = sorted({o.strip() for o in os_rows if o and o.strip() and o.strip() not in ("-", "—")})

    conflict_banner = ""
    if conflict_ips:
        conflict_banner = f"Terdeteksi bentrok alamat IP pada: {', '.join(sorted(conflict_ips))}"

    meta = {
        "orphan_ids": orphan_ids,
        "conflict_ips": conflict_ips,
        "tab_counts": tab_counts,
        "summary": summary,
        "kpi": kpi_fe,
        "conflict_banner": conflict_banner,
        "allowed_cidrs": allowed_cidrs,
        "subnets": [{"id": s.id, "cidr": s.cidr, "nama": s.nama} for s in subnets],
        "subnet_options": allowed_cidrs,
        "host_options": host_options,
        "host_server_options": host_server_options,
        "server_asset_ids": server_asset_ids,
        "os_suggestions": os_set,
    }
    _STATS_CACHE["sig"] = sig
    _STATS_CACHE["data"] = meta
    _STATS_CACHE["expires_at"] = now + _STATS_CACHE_TTL
    return meta


@router.get("", response_model=IPAllocationPageResponse)
def list_ip_allocations(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tipe: str | None = Query(default=None),
    jenis: str | None = Query(default=None),
    grup: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    host: str | None = Query(default=None),
    subnet: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    only_vm: bool | None = Query(default=None),
    orphan_only: bool = Query(default=False),
    only_orphan_vm: bool = Query(default=False),
    only_conflict: bool = Query(default=False),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="asc"),
) -> IPAllocationPageResponse:
    """Mengambil daftar alokasi IP & VM dengan filter, sort, dan pagination di SQL server (C1)."""
    meta = _get_cached_ip_metadata(session)
    orphan_ids: set[int] = meta["orphan_ids"]
    conflict_ips: set[str] = meta["conflict_ips"]
    allowed_cidrs: list[str] = meta["allowed_cidrs"]

    stmt = select(IPAllocation)

    keyword = (search or q or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                col(IPAllocation.ip_address).ilike(pattern),
                col(IPAllocation.nama_perangkat).ilike(pattern),
                col(IPAllocation.pengguna).ilike(pattern),
                col(IPAllocation.kategori).ilike(pattern),
                col(IPAllocation.os).ilike(pattern),
                col(IPAllocation.hostname).ilike(pattern),
                col(IPAllocation.host_name).ilike(pattern),
                col(IPAllocation.id_aset).ilike(pattern),
                col(IPAllocation.id_aset_host).ilike(pattern),
                col(IPAllocation.port_servis).ilike(pattern),
                col(IPAllocation.keterangan).ilike(pattern),
            )
        )

    if kategori and kategori.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(IPAllocation.kategori) == kategori.strip().lower())

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(IPAllocation.lokasi) == lokasi.strip().lower())

    if status_filter and status_filter.strip().lower() not in ("semua", "semua status", "all", ""):
        st_clean = status_filter.strip().lower()
        if st_clean in ("konflik", "bentrok"):
            only_conflict = True
        else:
            stmt = stmt.where(func.lower(IPAllocation.status) == st_clean)

    if only_vm is True:
        stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
    elif only_vm is False:
        stmt = stmt.where(col(IPAllocation.is_vm).is_(False))

    effective_tipe = (tipe or jenis or "").strip()
    if effective_tipe and effective_tipe.lower() not in ("semua", "semua jenis", "all", ""):
        t_clean = effective_tipe.lower()
        if t_clean == "vm":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
        elif t_clean == "fisik":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(False))
        elif t_clean in ("vm tanpa host", "orphan", "orphan_vm"):
            orphan_only = True
        elif t_clean in ("konflik", "bentrok"):
            only_conflict = True
        else:
            stmt = stmt.where(func.lower(IPAllocation.tipe) == t_clean)

    if grup and grup.strip().lower() not in ("semua", "all", ""):
        g_clean = grup.strip().lower()
        if "vm" in g_clean or "addon" in g_clean:
            stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
        elif "operasional" in g_clean or "fisik" in g_clean:
            stmt = stmt.where(col(IPAllocation.is_vm).is_(False))

    # A3: Dukungan filter host berformat "SRV-002 (SERVER OTO RETAIL) · 3 VM"
    if host and host.strip().lower() not in ("semua", "semua host", "all", ""):
        h_clean = host.strip()
        if "·" in h_clean:
            h_clean = h_clean.split("·", 1)[0].strip()
        h_code = h_clean.split(" ")[0].strip().upper()
        name_part = h_clean
        if "(" in h_clean and ")" in h_clean:
            name_part = h_clean.split("(", 1)[1].rsplit(")", 1)[0].strip()
        stmt = stmt.where(
            col(IPAllocation.is_vm).is_(True),
            or_(
                func.upper(IPAllocation.id_aset_host) == h_code,
                col(IPAllocation.host_name).ilike(f"%{name_part}%"),
            ),
        )

    if subnet and subnet.strip().lower() not in ("semua", "semua subnet", "all", ""):
        sub_clean = subnet.strip().lower()
        prefix_parts = sub_clean.split("/")[0].split(".")
        if len(prefix_parts) >= 3:
            prefix_3 = f"{prefix_parts[0]}.{prefix_parts[1]}.{prefix_parts[2]}."
            stmt = stmt.where(col(IPAllocation.ip_address).like(f"{prefix_3}%"))
        else:
            stmt = stmt.where(func.lower(IPAllocation.subnet) == sub_clean)

    if only_conflict:
        if conflict_ips:
            stmt = stmt.where(
                or_(
                    col(IPAllocation.ip_address).in_(conflict_ips),
                    func.lower(IPAllocation.status) == "konflik",
                )
            )
        else:
            stmt = stmt.where(func.lower(IPAllocation.status) == "konflik")

    if orphan_only or only_orphan_vm:
        if orphan_ids:
            stmt = stmt.where(col(IPAllocation.id).in_(orphan_ids))
        else:
            stmt = stmt.where(IPAllocation.id == -1)

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()

    sort_col_map = {
        "ip_address": col(IPAllocation.ip_int),
        "pengguna": func.lower(IPAllocation.pengguna),
        "nama": func.lower(IPAllocation.nama_perangkat),
        "nama_perangkat": func.lower(IPAllocation.nama_perangkat),
        "jenis": col(IPAllocation.is_vm),
        "tipe": func.lower(IPAllocation.tipe),
        "host": func.lower(IPAllocation.host_name),
        "os": func.lower(IPAllocation.os),
        "status": func.lower(IPAllocation.status),
        "lokasi": func.lower(IPAllocation.lokasi),
    }
    s_key = (sort_by or "ip_address").strip().lower()
    order_target = sort_col_map.get(s_key, col(IPAllocation.ip_int))
    is_desc = (sort_dir or "asc").strip().lower() == "desc"
    stmt = stmt.order_by(
        order_target.desc() if is_desc else order_target.asc(),
        col(IPAllocation.ip_int).asc(),
        col(IPAllocation.id).asc(),
    )

    page_rows = session.exec(stmt.offset(page_params.offset).limit(page_params.page_size)).all()

    items = [
        IPAllocationPublic.from_model(
            r,
            is_orphan=(r.id in orphan_ids),
            is_conflict=(r.ip_address in conflict_ips or r.status.lower() == "konflik"),
            allowed_subnets=allowed_cidrs,
        )
        for r in page_rows
    ]

    return IPAllocationPageResponse(
        items=items,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=meta["tab_counts"],
        summary=meta["summary"],
        kpi=meta["kpi"],
        conflict_banner=meta["conflict_banner"],
        subnet_options=meta["subnet_options"],
        subnets=meta["subnets"],
        host_options=meta["host_options"],
        host_server_options=meta["host_server_options"],
        server_asset_ids=meta["server_asset_ids"],
        os_suggestions=meta["os_suggestions"],
    )


@router.get("/map")
def get_ip_map(
    session: SessionDep,
    _: CurrentUserDep,
    subnet: str = Query(default="1"),
) -> dict[str, Any]:
    """Mengembalikan peta alokasi IP untuk subnet terdaftar di ip_subnets (A4, B4, C1)."""
    registered_subnets = _ensure_registered_subnets(session)
    clean_param = (subnet or "1").strip()

    matched_subnet: IPSubnet | None = None
    if clean_param.isdigit():
        sub_id = int(clean_param)
        matched_subnet = next((s for s in registered_subnets if s.id == sub_id), None)
    else:
        norm_param = clean_param if "/" in clean_param else f"{clean_param}/24"
        matched_subnet = next(
            (s for s in registered_subnets if s.cidr.lower() == norm_param.lower()),
            None,
        )

    if matched_subnet is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Subnet '{subnet}' tidak terdaftar pada ip_subnets",
        )

    normalized_subnet = matched_subnet.cidr
    parts = normalized_subnet.split("/")[0].split(".")
    prefix = f"{parts[0]}.{parts[1]}.{parts[2]}"

    records = session.exec(
        select(IPAllocation)
        .where(col(IPAllocation.ip_address).like(f"{prefix}.%"))
        .order_by(col(IPAllocation.ip_int).asc(), col(IPAllocation.id).asc())
    ).all()

    # Hitung konflik di subnet ini (A4: pastikan selalu integer, default 0)
    active_ip_counts: dict[str, int] = {}
    for r in records:
        if r.status.lower() not in ("bebas", "tersedia", "nonaktif"):
            active_ip_counts[r.ip_address] = active_ip_counts.get(r.ip_address, 0) + 1
    subnet_conflict_ips = {ip for ip, cnt in active_ip_counts.items() if cnt > 1}

    alloc_map: dict[int, IPAllocation] = {}
    for r in records:
        try:
            oct_val = int(r.ip_address.split(".")[3])
            if 1 <= oct_val <= 254:
                alloc_map[oct_val] = r
        except (IndexError, ValueError):
            continue

    occupied: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    terpakai = 0
    fisik_count = 0
    vm_count = 0
    nonaktif_count = 0
    bentrok_count = 0

    for octet in range(256):
        ip_str = f"{prefix}.{octet}"
        if octet == 0:
            cells.append(
                {
                    "octet": octet,
                    "ip_address": ip_str,
                    "status": "network",
                    "label": "Network ID",
                    "is_reserved": True,
                    "is_occupied": False,
                }
            )
        elif octet == 255:
            cells.append(
                {
                    "octet": octet,
                    "ip_address": ip_str,
                    "status": "broadcast",
                    "label": "Broadcast",
                    "is_reserved": True,
                    "is_occupied": False,
                }
            )
        else:
            alloc = alloc_map.get(octet)
            if alloc:
                terpakai += 1
                is_conf = (
                    alloc.ip_address in subnet_conflict_ips or alloc.status.lower() == "konflik"
                )
                is_nonaktif = alloc.status.lower() == "nonaktif"
                if is_conf:
                    bentrok_count += 1
                if is_nonaktif:
                    cell_status = "nonaktif"
                    nonaktif_count += 1
                elif alloc.is_vm:
                    cell_status = "vm"
                    vm_count += 1
                else:
                    cell_status = "fisik"
                    fisik_count += 1

                fungsi_val = (alloc.port_servis or "Operasional").strip()
                ket_norm = normalize_keterangan(alloc.keterangan, fungsi_val)
                kendala = has_kendala(ket_norm, fungsi_val)
                entry_data = {
                    "id": alloc.id,
                    "entry_id": alloc.id,
                    "octet": octet,
                    "ip_address": ip_str,
                    "status": "konflik" if is_conf else cell_status,
                    "jenis": "VM" if alloc.is_vm else "Fisik",
                    "is_reserved": False,
                    "is_occupied": True,
                    "is_conflict": is_conf,
                    "has_kendala": kendala,
                    "nama": alloc.nama_perangkat,
                    "pengguna": alloc.pengguna or alloc.nama_perangkat,
                    "host": alloc.host_name
                    or alloc.id_aset_host
                    or ("—" if not alloc.is_vm else "Tanpa host"),
                    "os": alloc.os or "—",
                    "fungsi": fungsi_val,
                    "keterangan": ket_norm or "",
                    "lokasi": alloc.lokasi,
                }
                occupied.append(entry_data)
                cells.append(entry_data)
            else:
                cells.append(
                    {
                        "octet": octet,
                        "ip_address": ip_str,
                        "status": "kosong",
                        "is_reserved": False,
                        "is_occupied": False,
                        "label": "Tersedia",
                    }
                )

    kosong = 254 - terpakai
    empty_octets = [o for o in range(1, 255) if o not in alloc_map]
    suggested_octets = [o for o in empty_octets if o > 1][:5] or empty_octets[:5]
    suggested_ips = [f"{prefix}.{o}" for o in suggested_octets]

    largest_start = None
    largest_end = None
    largest_len = 0
    cur_start = None
    cur_len = 0
    for octet in range(1, 255):
        if octet not in alloc_map:
            if cur_start is None:
                cur_start = octet
                cur_len = 1
            else:
                cur_len += 1
            if cur_len > largest_len:
                largest_len = cur_len
                largest_start = cur_start
                largest_end = octet
        else:
            cur_start = None
            cur_len = 0

    largest_empty_range = (
        f"{prefix}.{largest_start} - {prefix}.{largest_end} ({largest_len} IP)"
        if (largest_start is not None and largest_end is not None and largest_len > 0)
        else "Tidak ada rentang kosong"
    )

    stats = {
        "total_allocatable": 254,
        "terpakai": terpakai,
        "kosong": kosong,
        "fisik": fisik_count,
        "vm": vm_count,
        "nonaktif": nonaktif_count,
        "bentrok": bentrok_count,
        "konflik": bentrok_count,
    }

    return {
        "subnet_id": matched_subnet.id,
        "subnet": normalized_subnet,
        "subnets": [{"id": s.id, "cidr": s.cidr, "nama": s.nama} for s in registered_subnets],
        "prefix": prefix,
        "occupied": occupied,
        "cells": cells,
        "stats": stats,
        "suggested_ips": suggested_ips,
        "largest_empty_range": largest_empty_range,
    }


@router.get("/import-template")
def get_ip_import_template(_: CurrentUserDep) -> Response:
    """Unduh file template Excel (.xlsx) resmi untuk impor alokasi IP & VM."""
    headers = [
        "IP Address",
        "Nama Server/VM",
        "Jenis",
        "Host Server",
        "Status",
        "Fungsi",
        "OS",
        "Keterangan",
    ]
    sample_row = [
        "192.168.1.30",
        "PC CS RETAIL",
        "Fisik",
        "",
        "Aktif",
        "Workstation Operasional",
        "Windows 11 Pro",
        "",
    ]
    widths = [18, 26, 12, 18, 14, 32, 24, 34]
    xlsx_bytes = build_openxml_xlsx(headers, [sample_row], widths, is_template=True)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="Template_Import_IP_Server_ITAM_Pro.xlsx"'
        },
    )


@router.post("/import-preview")
async def preview_ip_import(
    session: SessionDep,
    _: EditorUserDep,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Validasi file .xlsx / .csv (maks 5 MB) sebelum disimpan permanen."""
    raw_bytes = await file.read()
    if len(raw_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ukuran file melebihi batas maksimum 5 MB",
        )

    filename = file.filename or "data.xlsx"
    raw_rows: list[list[str]] = []
    try:
        if filename.lower().endswith(".xlsx"):
            raw_rows = read_xlsx_rows(raw_bytes)
        else:
            text_csv = raw_bytes.decode("utf-8-sig", errors="replace")
            first_line = text_csv.split("\n")[0] if text_csv else ""
            delim = (
                ";" if ";" in first_line and first_line.count(";") > first_line.count(",") else ","
            )
            reader = csv.reader(io.StringIO(text_csv), delimiter=delim)
            raw_rows = [[c.strip() for c in r] for r in reader if any(r)]
    except Exception as exc:
        return {
            "import_id": "",
            "valid_count": 0,
            "error_count": 1,
            "valid_rows": [],
            "errors": [
                {"row_number": 1, "ip_address": "—", "reason": f"File rusak/tidak terbaca ({exc})"}
            ],
            "error_report_csv": "",
        }

    if len(raw_rows) <= 1:
        return {
            "import_id": "",
            "valid_count": 0,
            "error_count": 1,
            "valid_rows": [],
            "errors": [
                {"row_number": 1, "ip_address": "—", "reason": "File tidak memiliki baris data"}
            ],
            "error_report_csv": "",
        }

    # Batasi maksimum 1000 baris data
    if len(raw_rows) > 1001:
        raw_rows = raw_rows[:1001]

    # Kumpulkan IP eksisting, subnet terdaftar, & server fisik aktif untuk validasi
    existing_ips = set(session.exec(select(IPAllocation.ip_address)).all())
    allowed_cidrs = [s.cidr for s in _ensure_registered_subnets(session)]
    active_servers = {
        a.id_aset.upper(): a.nama_aset
        for a in session.exec(
            select(Asset).where(
                Asset.kategori == "Server",
                func.lower(Asset.status).notin_(["rusak", "nonaktif"]),
            )
        ).all()
    }

    seen_in_file: set[str] = set()
    valid_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, cols in enumerate(raw_rows[1:], start=2):
        padded = [*cols, "", "", "", "", "", "", "", ""][:8]
        ip_val, nama_val, jenis_val, host_val, status_val, fungsi_val, os_val, ket_val = [
            x.strip() for x in padded
        ]
        if not any([ip_val, nama_val, jenis_val]):
            continue

        if not ip_val:
            errors.append({"row_number": idx, "ip_address": "—", "reason": "IP Address kosong"})
            continue

        try:
            canonical_ip, ip_int = parse_and_validate_ipv4(ip_val)
        except ValueError as exc:
            errors.append({"row_number": idx, "ip_address": ip_val, "reason": str(exc)})
            continue

        if not is_ip_in_subnets(canonical_ip, allowed_cidrs):
            errors.append(
                {
                    "row_number": idx,
                    "ip_address": canonical_ip,
                    "reason": f"IP di luar subnet terdaftar ({', '.join(allowed_cidrs)})",
                }
            )
            continue

        if canonical_ip in seen_in_file:
            errors.append(
                {
                    "row_number": idx,
                    "ip_address": canonical_ip,
                    "reason": "IP duplikat di dalam file yang sama",
                }
            )
            continue

        is_existing = canonical_ip in existing_ips

        if not nama_val:
            errors.append(
                {"row_number": idx, "ip_address": canonical_ip, "reason": "Nama Server/VM kosong"}
            )
            continue

        jenis_norm = (
            "VM" if jenis_val.upper() == "VM" else ("Fisik" if jenis_val.lower() == "fisik" else "")
        )
        if not jenis_norm:
            errors.append(
                {
                    "row_number": idx,
                    "ip_address": canonical_ip,
                    "reason": "Jenis harus Fisik atau VM",
                }
            )
            continue

        status_norm = (
            "Aktif"
            if status_val.lower() in ("aktif", "")
            else ("Nonaktif" if status_val.lower() == "nonaktif" else "")
        )
        if not status_norm:
            errors.append(
                {
                    "row_number": idx,
                    "ip_address": canonical_ip,
                    "reason": "Status harus Aktif atau Nonaktif",
                }
            )
            continue

        host_id_clean = host_val.split(" ")[0].strip().upper() if jenis_norm == "VM" else ""
        host_name_resolved = ""
        if jenis_norm == "VM":
            if not host_id_clean:
                errors.append(
                    {
                        "row_number": idx,
                        "ip_address": canonical_ip,
                        "reason": "Host Server wajib diisi untuk VM",
                    }
                )
                continue
            if host_id_clean not in active_servers:
                matched_id = next(
                    (
                        aid
                        for aid, aname in active_servers.items()
                        if aname.lower() == host_val.lower()
                    ),
                    None,
                )
                if not matched_id:
                    errors.append(
                        {
                            "row_number": idx,
                            "ip_address": canonical_ip,
                            "reason": (
                                f"Host '{host_val}' tidak ditemukan di daftar server fisik aktif"
                            ),
                        }
                    )
                    continue
                host_id_clean = matched_id
                host_name_resolved = active_servers[matched_id]
            else:
                host_name_resolved = active_servers[host_id_clean]

        seen_in_file.add(canonical_ip)
        parts = canonical_ip.split(".")
        subnet_24 = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        ket_norm = normalize_keterangan(ket_val, fungsi_val)
        valid_rows.append(
            {
                "ip_address": canonical_ip,
                "ip_int": ip_int,
                "subnet": subnet_24,
                "gateway": "",
                "nama_perangkat": nama_val,
                "hostname": nama_val,
                "tipe": jenis_norm,
                "status": status_norm,
                "is_vm": (jenis_norm == "VM"),
                "id_aset_host": host_id_clean or None,
                "host_name": host_name_resolved,
                "fungsi": fungsi_val,
                "os": os_val,
                "keterangan": ket_norm,
                "lokasi": "Head Office (Office Blok 14)",
                "is_existing": is_existing,
            }
        )

    err_buf = io.StringIO()
    writer = csv.writer(err_buf)
    writer.writerow(["Baris", "IP Address", "Alasan Error"])
    for e in errors:
        writer.writerow([e["row_number"], e["ip_address"], e["reason"]])

    _prune_import_sessions()
    import_id = str(uuid.uuid4())
    _IMPORT_SESSIONS[import_id] = {
        "created_at": time.time(),
        "valid_rows": valid_rows,
    }

    return {
        "import_id": import_id,
        "valid_count": len(valid_rows),
        "error_count": len(errors),
        "valid_rows": valid_rows,
        "errors": errors,
        "error_report_csv": err_buf.getvalue(),
    }


@router.post("/import-commit")
def commit_ip_import(
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Menyimpan seluruh baris valid hasil preview ke database dalam satu transaksi (A1)."""
    import_id = payload.get("import_id")
    duplicate_mode = str(payload.get("duplicate_mode", "skip")).lower().strip()
    if duplicate_mode not in ("skip", "update"):
        duplicate_mode = "skip"

    rows: list[dict[str, Any]] = []
    if import_id and import_id in _IMPORT_SESSIONS:
        cached = _IMPORT_SESSIONS.pop(import_id)
        rows = cached.get("valid_rows", [])
    elif "valid_rows" in payload and isinstance(payload["valid_rows"], list):
        rows = payload["valid_rows"]

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tidak ada data baris valid yang dikirim untuk diimpor atau sesi telah kedaluwarsa"
            ),
        )

    allowed_cidrs = [s.cidr for s in _ensure_registered_subnets(session)]
    imported_count = 0
    updated_count = 0
    skipped_count = 0

    try:
        for item in rows:
            raw_ip = str(item.get("ip_address") or "").strip()
            # A1 (2, 3, 4): Selalu hitung ulang ip_int di server sebelum insert maupun update
            canonical_ip, computed_ip_int = parse_and_validate_ipv4(raw_ip)
            if not is_ip_in_subnets(canonical_ip, allowed_cidrs):
                raise ValueError(
                    f"IP {canonical_ip} di luar subnet terdaftar ({', '.join(allowed_cidrs)})"
                )

            nama_val = str(item.get("nama_perangkat") or item.get("pengguna") or "").strip()
            if not nama_val:
                raise ValueError(f"Nama perangkat/pengguna kosong untuk IP {canonical_ip}")

            fungsi_val = str(item.get("fungsi") or item.get("port_servis") or "").strip()[:120]
            ket_norm = normalize_keterangan(item.get("keterangan"), fungsi_val)
            parts = canonical_ip.split(".")
            subnet_cidr = str(
                item.get("subnet") or f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            ).strip()

            existing = session.exec(
                select(IPAllocation).where(IPAllocation.ip_address == canonical_ip)
            ).first()

            if existing:
                if duplicate_mode == "update":
                    existing.ip_address = canonical_ip
                    existing.ip_int = computed_ip_int
                    existing.subnet = subnet_cidr
                    existing.nama_perangkat = nama_val
                    existing.hostname = str(item.get("hostname") or nama_val).strip()
                    existing.tipe = str(item.get("tipe", "Fisik")).strip()
                    existing.status = str(item.get("status", "Aktif")).strip()
                    existing.is_vm = bool(item.get("is_vm", existing.tipe.upper() == "VM"))
                    existing.host_name = str(item.get("host_name") or "").strip()
                    existing.id_aset_host = item.get("id_aset_host") or None
                    existing.os = str(item.get("os") or "").strip()
                    if fungsi_val:
                        existing.port_servis = fungsi_val
                    existing.pengguna = str(item.get("pengguna") or nama_val).strip()
                    existing.kategori = str(
                        item.get(
                            "kategori",
                            "IP VM" if existing.is_vm else "IP Operasional",
                        )
                    ).strip()
                    existing.keterangan = ket_norm
                    existing.updated_at = utcnow()
                    session.add(existing)
                    updated_count += 1
                else:
                    skipped_count += 1
                    continue
            else:
                is_vm_flag = bool(item.get("is_vm", str(item.get("tipe", "")).upper() == "VM"))
                new_alloc = IPAllocation(
                    ip_address=canonical_ip,
                    ip_int=computed_ip_int,
                    subnet=subnet_cidr,
                    gateway=str(item.get("gateway") or "").strip(),
                    nama_perangkat=nama_val,
                    hostname=str(item.get("hostname") or nama_val).strip(),
                    tipe="VM" if is_vm_flag else str(item.get("tipe", "Fisik")).strip(),
                    status=str(item.get("status", "Aktif")).strip(),
                    lokasi=str(item.get("lokasi", "Head Office (Office Blok 14)")).strip(),
                    id_aset=item.get("id_aset"),
                    is_vm=is_vm_flag,
                    host_name=str(item.get("host_name") or "").strip(),
                    id_aset_host=item.get("id_aset_host") or None,
                    os=str(item.get("os") or "").strip(),
                    vcpu=int(item.get("vcpu") or 0),
                    ram=str(item.get("ram") or ""),
                    storage=str(item.get("storage") or ""),
                    port_servis=fungsi_val,
                    mac_address=str(item.get("mac_address") or ""),
                    pengguna=str(item.get("pengguna") or nama_val).strip(),
                    kategori=str(
                        item.get("kategori", "IP VM" if is_vm_flag else "IP Operasional")
                    ).strip(),
                    keterangan=ket_norm,
                )
                session.add(new_alloc)
                imported_count += 1

        record_audit_log(
            session,
            username=current_user.username,
            nama_pengguna=current_user.full_name or current_user.username,
            role=current_user.role,
            aksi="IMPORT",
            modul="Infrastructure",
            target_id="ip_allocations",
            detail=(
                f"Import massal: {imported_count} baru, {updated_count} diperbarui, "
                f"{skipped_count} dilewati (mode: {duplicate_mode})"
            ),
            level_risiko="Sedang",
        )
        session.commit()
        invalidate_ip_cache()
    except Exception as exc:
        session.rollback()
        err_code = f"ERR-{uuid.uuid4().hex[:4].upper()}"
        logger.exception(
            "Gagal melakukan transaksi impor IP [%s] oleh %s: %s",
            err_code,
            current_user.username,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import gagal. Kode: {err_code}",
        ) from exc

    return {
        "success": True,
        "imported_count": imported_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "total_processed": len(rows),
    }


def _query_filtered_export_items(
    session: Session,
    *,
    search: str | None = None,
    tipe: str | None = None,
    jenis: str | None = None,
    grup: str | None = None,
    host: str | None = None,
    subnet: str | None = None,
    status_filter: str | None = None,
    only_conflict: bool = False,
    only_orphan_vm: bool = False,
) -> list[dict[str, Any]]:
    """Helper bersama untuk mengambil seluruh baris terfilter pada Export & Cetak (B2)."""
    stmt = select(IPAllocation)

    effective_jenis = (jenis or tipe or "").strip()
    if effective_jenis and effective_jenis.lower() not in ("semua", "semua jenis", "all", ""):
        if effective_jenis.lower() == "vm":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
        elif effective_jenis.lower() == "fisik":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(False))
        elif effective_jenis.lower() in ("konflik", "bentrok"):
            only_conflict = True

    if grup and grup.lower() not in ("semua", "all", ""):
        if grup in ("VM", "Addon (VM)"):
            stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
        elif grup in ("Fisik", "Operasional"):
            stmt = stmt.where(col(IPAllocation.is_vm).is_(False))

    if status_filter and status_filter.lower() not in ("semua", "semua status", "all", ""):
        if status_filter.lower() in ("konflik", "bentrok"):
            only_conflict = True
        else:
            stmt = stmt.where(func.lower(IPAllocation.status) == status_filter.lower())

    if host and host.strip().lower() not in ("semua", "semua host", "all", ""):
        h_clean = host.strip()
        if "·" in h_clean:
            h_clean = h_clean.split("·", 1)[0].strip()
        h_code = h_clean.split(" ")[0].strip().upper()
        name_part = h_clean
        if "(" in h_clean and ")" in h_clean:
            name_part = h_clean.split("(", 1)[1].rsplit(")", 1)[0].strip()
        stmt = stmt.where(
            col(IPAllocation.is_vm).is_(True),
            or_(
                func.upper(IPAllocation.id_aset_host) == h_code,
                col(IPAllocation.host_name).ilike(f"%{name_part}%"),
            ),
        )

    if subnet and subnet.lower() not in ("semua", "semua subnet", "all", ""):
        prefix_parts = subnet.strip().split("/")[0].split(".")
        if len(prefix_parts) >= 3:
            prefix_3 = f"{prefix_parts[0]}.{prefix_parts[1]}.{prefix_parts[2]}."
            stmt = stmt.where(col(IPAllocation.ip_address).like(f"{prefix_3}%"))
        else:
            stmt = stmt.where(func.lower(IPAllocation.subnet) == subnet.lower())

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(IPAllocation.ip_address).like(term),
                func.lower(IPAllocation.nama_perangkat).like(term),
                func.lower(IPAllocation.pengguna).like(term),
                func.lower(IPAllocation.hostname).like(term),
                func.lower(IPAllocation.host_name).like(term),
                func.lower(IPAllocation.os).like(term),
                func.lower(IPAllocation.port_servis).like(term),
                func.lower(col(IPAllocation.keterangan)).like(term),
            )
        )

    stmt = stmt.order_by(col(IPAllocation.ip_int).asc(), col(IPAllocation.id).asc())
    rows = session.exec(stmt).all()
    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session, rows)

    def _sanitize_formula(val: Any) -> str:
        s = str(val or "")
        if s and s[0] in ("=", "+", "-", "@"):
            return "'" + s
        return s

    items: list[dict[str, Any]] = []
    for r in rows:
        is_conf = r.ip_address in conflict_ips or r.status.lower() == "konflik"
        is_orph = r.id in orphan_ids
        if only_conflict and not is_conf:
            continue
        if only_orphan_vm and not is_orph:
            continue
        host_disp = (
            "—"
            if not r.is_vm
            else (
                f"{r.id_aset_host} ({r.host_name})"
                if (r.id_aset_host and r.host_name)
                else (r.host_name or r.id_aset_host or "Tanpa host")
            )
        )
        fungsi_val = (r.port_servis or "Operasional").strip()
        ket_norm = normalize_keterangan(r.keterangan, fungsi_val)
        items.append(
            {
                "ip_address": r.ip_address,
                "nama": _sanitize_formula(r.pengguna or r.nama_perangkat),
                "pengguna": _sanitize_formula(r.pengguna or r.nama_perangkat),
                "jenis": "VM" if r.is_vm else "Fisik",
                "host_display": _sanitize_formula(host_disp),
                "fungsi": _sanitize_formula(fungsi_val),
                "os": _sanitize_formula(r.os or "—"),
                "status": "Konflik" if is_conf else r.status,
                "keterangan": _sanitize_formula(ket_norm or "—"),
                "has_kendala": has_kendala(ket_norm, fungsi_val),
            }
        )
    return items


@router.get("/print-data")
def get_ip_print_data(
    session: SessionDep,
    current_user: CurrentUserDep,
    search: str | None = Query(default=None),
    tipe: str | None = Query(default=None),
    jenis: str | None = Query(default=None),
    grup: str | None = Query(default=None),
    host: str | None = Query(default=None),
    subnet: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    only_conflict: bool = Query(default=False),
    only_orphan_vm: bool = Query(default=False),
    record_log: bool = Query(default=True),
) -> dict[str, Any]:
    """Endpoint khusus Cetak: ambil SEMUA baris sesuai filter aktif (maks 5.000) + Audit Log."""
    items = _query_filtered_export_items(
        session,
        search=search,
        tipe=tipe,
        jenis=jenis,
        grup=grup,
        host=host,
        subnet=subnet,
        status_filter=status_filter,
        only_conflict=only_conflict,
        only_orphan_vm=only_orphan_vm,
    )
    if len(items) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Jumlah data melebihi batas maksimum cetak langsung (5.000 baris). "
                "Silakan gunakan fitur Export Excel atau PDF."
            ),
        )

    now = datetime.now()
    months_id = [
        "",
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]
    printed_at = f"{now.day} {months_id[now.month]} {now.year}, {now.strftime('%H:%M')} WIB"
    printed_by = current_user.full_name or current_user.username

    active_filters: list[str] = []
    if (jenis or tipe) and (jenis or tipe) not in ("Semua", "Semua jenis", "all"):
        active_filters.append(f"Jenis: {jenis or tipe}")
    if status_filter and status_filter not in ("Semua", "Semua status", "all"):
        active_filters.append(f"Status: {status_filter}")
    if host and host not in ("Semua", "Semua host", "all"):
        active_filters.append(f"Host: {host.split('·')[0].strip()}")
    if search and search.strip():
        active_filters.append(f"Pencarian: '{search.strip()}'")
    if only_conflict:
        active_filters.append("Filter: Hanya IP Bentrok")

    filter_label = " · ".join(active_filters) if active_filters else "Semua Data"

    if record_log:
        record_audit_log(
            session,
            username=current_user.username,
            nama_pengguna=printed_by,
            role=current_user.role,
            aksi="PRINT",
            modul="Infrastructure",
            target_id="ip_allocations",
            detail=f"Cetak data IP ({len(items)} baris, filter: {filter_label})",
            level_risiko="Rendah",
        )
        session.commit()

    return {
        "title": "Daftar IP & Server (VM)",
        "subnet": subnet or DEFAULT_REGISTERED_SUBNET,
        "filter_label": filter_label,
        "printed_at": printed_at,
        "printed_by": printed_by,
        "total": len(items),
        "items": items,
    }


@router.get("/export")
def export_ip_allocations(
    session: SessionDep,
    current_user: CurrentUserDep,
    format: str = Query(default="xlsx"),
    search: str | None = Query(default=None),
    tipe: str | None = Query(default=None),
    jenis: str | None = Query(default=None),
    grup: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    host: str | None = Query(default=None),
    subnet: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    only_conflict: bool = Query(default=False),
    only_orphan_vm: bool = Query(default=False),
    columns: str | None = Query(default=None),
) -> Response:
    """Ekspor seluruh data IP & Server (VM) sesuai filter aktif dalam format Excel atau PDF."""
    export_items = _query_filtered_export_items(
        session,
        search=search,
        tipe=tipe,
        jenis=jenis,
        grup=grup,
        host=host,
        subnet=subnet,
        status_filter=status_filter,
        only_conflict=only_conflict,
        only_orphan_vm=only_orphan_vm,
    )

    selected_cols = (
        [c.strip().lower() for c in columns.split(",") if c.strip()] if columns else None
    )

    now = datetime.now()
    today_str = now.strftime("%Y%m%d")

    if format.lower() == "pdf":
        months_id = [
            "",
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]
        date_lbl = f"{now.day} {months_id[now.month]} {now.year}"
        pdf_bytes = build_a4_landscape_ip_pdf(
            rows=export_items,
            export_date_label=date_lbl,
            exporter_name=current_user.full_name or current_user.username,
            selected_columns=selected_cols,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="Daftar_IP_Server_VM_{today_str}.pdf"'
            },
        )

    headers = [
        "No",
        "IP Address",
        "Nama Server/VM",
        "Jenis",
        "Host",
        "Fungsi",
        "OS",
        "Status",
        "Keterangan",
    ]
    xlsx_rows = [
        [
            str(i),
            it["ip_address"],
            it["nama"],
            it["jenis"],
            it["host_display"],
            it["fungsi"],
            it["os"],
            it["status"],
            it["keterangan"],
        ]
        for i, it in enumerate(export_items, start=1)
    ]
    widths = [6, 18, 28, 12, 18, 34, 24, 14, 34]
    xlsx_bytes = build_openxml_xlsx(headers, xlsx_rows, widths, is_template=False)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="Daftar_IP_Server_VM_{today_str}.xlsx"'
        },
    )


@router.get("/{item_id}", response_model=IPAllocationPublic)
def get_ip_allocation(
    item_id: int,
    session: SessionDep,
    _: CurrentUserDep,
) -> IPAllocationPublic:
    """Mengambil detail satu alokasi IP / VM."""
    row = session.get(IPAllocation, item_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data IP/VM tidak ditemukan",
        )
    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session, [row])
    allowed_cidrs = [s.cidr for s in _ensure_registered_subnets(session)]
    return IPAllocationPublic.from_model(
        row,
        is_orphan=(row.id in orphan_ids),
        is_conflict=(row.ip_address in conflict_ips or row.status.lower() == "konflik"),
        allowed_subnets=allowed_cidrs,
    )


@router.post("", response_model=IPAllocationPublic, status_code=status.HTTP_201_CREATED)
def create_ip_allocation(
    payload: IPAllocationCreate,
    session: SessionDep,
    _: EditorUserDep,
) -> IPAllocationPublic:
    """Membuat alokasi IP / VM baru dengan deteksi konflik IP, validasi subnet, dan host VM."""
    canonical_ip, ip_int = parse_and_validate_ipv4(payload.ip_address)
    _validate_ip_in_registered_subnets(session, canonical_ip)
    _check_ip_conflict(session, canonical_ip, payload.status)

    resolved_host_id, resolved_host_name = _validate_and_resolve_host(
        session,
        payload.id_aset_host,
        payload.host_name,
    )

    fungsi_str = payload.port_servis.strip()
    ket_norm = normalize_keterangan(payload.keterangan, fungsi_str)

    row = IPAllocation(
        ip_address=canonical_ip,
        ip_int=ip_int,
        subnet=payload.subnet.strip(),
        gateway=payload.gateway.strip(),
        nama_perangkat=payload.nama_perangkat,
        hostname=payload.hostname.strip(),
        tipe=payload.tipe,
        status=payload.status,
        lokasi=payload.lokasi,
        id_aset=payload.id_aset,
        is_vm=bool(payload.is_vm),
        host_name=resolved_host_name,
        id_aset_host=resolved_host_id,
        os=payload.os.strip(),
        vcpu=payload.vcpu,
        ram=payload.ram.strip(),
        storage=payload.storage.strip(),
        port_servis=fungsi_str,
        mac_address=payload.mac_address.strip(),
        pengguna=payload.pengguna.strip(),
        kategori=payload.kategori.strip(),
        keterangan=ket_norm,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    invalidate_ip_cache()

    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session, [row])
    return IPAllocationPublic.from_model(
        row,
        is_orphan=(row.id in orphan_ids),
        is_conflict=(row.ip_address in conflict_ips),
    )


def _apply_ip_update(
    item_id: int,
    payload: IPAllocationUpdate,
    session: Session,
) -> IPAllocationPublic:
    row = session.get(IPAllocation, item_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data IP/VM tidak ditemukan",
        )

    data = payload.model_dump(exclude_unset=True)
    if "pengguna" in data and data["pengguna"] and "nama_perangkat" not in data:
        data["nama_perangkat"] = str(data["pengguna"]).strip()
    if "nama" in data and "nama_perangkat" not in data:
        data["nama_perangkat"] = data.pop("nama") or ""
    else:
        data.pop("nama", None)

    if "jenis" in data and "tipe" not in data:
        data["tipe"] = data.pop("jenis") or "Fisik"
        data["is_vm"] = data["tipe"].strip().upper() == "VM"
    else:
        data.pop("jenis", None)

    if "grup" in data:
        g_val = (data.pop("grup") or "").lower()
        if "vm" in g_val and "is_vm" not in data:
            data["is_vm"] = True
            data["tipe"] = "VM"

    if "asset_id" in data and "id_aset" not in data:
        aid = (data.pop("asset_id") or "").strip().upper()
        data["id_aset"] = aid if aid not in ("", "-", "—") else None
    else:
        data.pop("asset_id", None)

    if "host_asset_id" in data and "id_aset_host" not in data:
        haid = (data.pop("host_asset_id") or "").strip().upper()
        data["id_aset_host"] = haid if haid not in ("", "-", "—") else None
    else:
        data.pop("host_asset_id", None)

    # A2: Simpan fungsi ke port_servis, JANGAN menyalin fungsi ke keterangan
    if "fungsi" in data:
        fn_val = (data.pop("fungsi") or "").strip()
        if "port_servis" not in data:
            data["port_servis"] = fn_val[:120]

    if "host" in data and "host_name" not in data:
        data["host_name"] = data.pop("host") or ""
    else:
        data.pop("host", None)

    new_ip = data.get("ip_address", row.ip_address)
    new_status = data.get("status", row.status)
    canonical_ip, ip_int = parse_and_validate_ipv4(new_ip)

    # B4: Validasi subnet bila IP diubah (data lama di luar subnet tetap bisa diedit metadatanya)
    if canonical_ip != row.ip_address:
        _validate_ip_in_registered_subnets(session, canonical_ip)

    _check_ip_conflict(session, canonical_ip, new_status, exclude_id=row.id)

    row.ip_address = canonical_ip
    row.ip_int = ip_int

    if "id_aset_host" in data or "host_name" in data:
        cand_id = data.get("id_aset_host", row.id_aset_host)
        if cand_id:
            cand_id = cand_id.strip().upper()
            cand_id = cand_id if cand_id not in ("", "-") else None
        cand_name = (data.get("host_name", row.host_name) or "").strip()
        resolved_id, resolved_name = _validate_and_resolve_host(session, cand_id, cand_name)
        row.id_aset_host = resolved_id
        row.host_name = resolved_name
        data.pop("id_aset_host", None)
        data.pop("host_name", None)

    for key, val in data.items():
        if key in ("id", "ip_address", "ip_int", "created_at", "keterangan"):
            continue
        if hasattr(row, key):
            setattr(row, key, val.strip() if isinstance(val, str) else val)

    if "keterangan" in data:
        row.keterangan = normalize_keterangan(data["keterangan"], row.port_servis)
    else:
        row.keterangan = normalize_keterangan(row.keterangan, row.port_servis)

    if row.is_vm and not row.host_name and not row.id_aset_host:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="VM wajib memiliki host induk (host_name atau id_aset_host)",
        )

    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    invalidate_ip_cache()

    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session, [row])
    return IPAllocationPublic.from_model(
        row,
        is_orphan=(row.id in orphan_ids),
        is_conflict=(row.ip_address in conflict_ips),
    )


@router.put("/{item_id}", response_model=IPAllocationPublic)
def update_ip_put(
    item_id: int,
    payload: IPAllocationUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> IPAllocationPublic:
    """Memperbarui data alokasi IP / VM (PUT)."""
    return _apply_ip_update(item_id, payload, session)


@router.patch("/{item_id}", response_model=IPAllocationPublic)
def update_ip_patch(
    item_id: int,
    payload: IPAllocationUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> IPAllocationPublic:
    """Memperbarui sebagian data alokasi IP / VM (PATCH)."""
    return _apply_ip_update(item_id, payload, session)


@router.delete("/{item_id}")
def delete_ip_allocation(
    item_id: int,
    session: SessionDep,
    _: AdminUserDep,
) -> dict[str, Any]:
    """Menghapus alokasi IP / VM (hanya Administrator)."""
    row = session.get(IPAllocation, item_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data IP/VM tidak ditemukan",
        )
    deleted_ip = row.ip_address
    session.delete(row)
    session.commit()
    invalidate_ip_cache()
    return {"status": "ok", "id": item_id, "ip_address": deleted_ip}
