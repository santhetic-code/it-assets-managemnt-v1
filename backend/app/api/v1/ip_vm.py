"""Endpoint CRUD IP Address & Virtual Machine (konflik IP, VM tanpa host, urut numerik)."""

from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.base import utcnow
from app.models.ip_allocation import IPAllocation
from app.schemas.ip_allocation import (
    IPAllocationCreate,
    IPAllocationPageResponse,
    IPAllocationPublic,
    IPAllocationUpdate,
    parse_and_validate_ipv4,
)

router = APIRouter()


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
                f"Konflik IP: alamat {ip_address} sudah digunakan oleh "
                f"'{existing.nama_perangkat}'"
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
    """Mendeteksi ID baris VM tanpa host aktif dan daftar IP yang mengalami konflik."""
    all_rows = session.exec(select(IPAllocation)).all()

    # Hitung frekuensi IP aktif untuk deteksi konflik di DB
    ip_counts: dict[str, int] = {}
    for r in all_rows:
        if r.status.lower() not in ("bebas", "tersedia", "nonaktif"):
            ip_counts[r.ip_address] = ip_counts.get(r.ip_address, 0) + 1
    conflict_ips = {ip for ip, count in ip_counts.items() if count > 1}

    # Ambil semua aset yang aktif sebagai referensi host fisik
    active_assets = {
        a.id_aset.upper(): a
        for a in session.exec(select(Asset)).all()
        if a.status.lower() not in ("rusak", "nonaktif")
    }

    orphan_ids: set[int] = set()
    for r in all_rows:
        if not r.is_vm or r.id is None:
            continue
        if not r.host_name.strip() and not r.id_aset_host:
            orphan_ids.add(r.id)
        elif r.id_aset_host and r.id_aset_host.upper() not in active_assets:
            orphan_ids.add(r.id)

    return orphan_ids, conflict_ips


def _build_counts_and_summary(
    all_rows: Sequence[IPAllocation],
    orphan_ids: set[int],
    conflict_ips: set[str],
) -> tuple[dict[str, int], dict[str, Any]]:
    total = len(all_rows)
    fisik_count = sum(1 for r in all_rows if not r.is_vm)
    vm_count = sum(1 for r in all_rows if r.is_vm)
    aktif_count = sum(1 for r in all_rows if r.status.lower() in ("aktif", "digunakan"))
    bebas_count = sum(1 for r in all_rows if r.status.lower() in ("bebas", "tersedia"))
    konflik_count = sum(
        1 for r in all_rows if r.ip_address in conflict_ips or r.status.lower() == "konflik"
    )
    orphan_count = len(orphan_ids)

    tab_counts = {
        "Semua": total,
        "all": total,
        "Fisik": fisik_count,
        "VM": vm_count,
        "Konflik": konflik_count,
        "VM Tanpa Host": orphan_count,
    }
    summary = {
        "total": total,
        "total_ip": total,
        "aktif": aktif_count,
        "terpakai": aktif_count,
        "bebas": bebas_count,
        "tersedia": bebas_count,
        "total_vm": vm_count,
        "vm": vm_count,
        "fisik": fisik_count,
        "konflik": konflik_count,
        "vm_tanpa_host": orphan_count,
        "orphan_vm": orphan_count,
    }
    return tab_counts, summary


@router.get("", response_model=IPAllocationPageResponse)
def list_ip_allocations(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tipe: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    only_vm: bool | None = Query(default=None),
    orphan_only: bool = Query(default=False),
) -> IPAllocationPageResponse:
    """Mengambil daftar alokasi IP & VM yang diurutkan secara numerik berdasarkan IPv4."""
    all_rows = session.exec(select(IPAllocation)).all()
    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session, all_rows)
    tab_counts, summary = _build_counts_and_summary(all_rows, orphan_ids, conflict_ips)

    stmt = select(IPAllocation)

    keyword = (search or q or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                col(IPAllocation.ip_address).ilike(pattern),
                col(IPAllocation.nama_perangkat).ilike(pattern),
                col(IPAllocation.hostname).ilike(pattern),
                col(IPAllocation.host_name).ilike(pattern),
                col(IPAllocation.pengguna).ilike(pattern),
                col(IPAllocation.keterangan).ilike(pattern),
            )
        )

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(IPAllocation.lokasi) == lokasi.strip().lower())

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        if st_clean == "konflik":
            if conflict_ips:
                stmt = stmt.where(
                    or_(
                        col(IPAllocation.ip_address).in_(conflict_ips),
                        func.lower(IPAllocation.status) == "konflik",
                    )
                )
            else:
                stmt = stmt.where(func.lower(IPAllocation.status) == "konflik")
        else:
            stmt = stmt.where(func.lower(IPAllocation.status) == st_clean)

    if only_vm is True:
        stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
    elif only_vm is False:
        stmt = stmt.where(col(IPAllocation.is_vm).is_(False))

    if tipe and tipe.strip().lower() not in ("semua", "all", ""):
        t_clean = tipe.strip().lower()
        if t_clean == "vm":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
        elif t_clean == "fisik":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(False))
        elif t_clean in ("vm tanpa host", "orphan", "orphan_vm"):
            orphan_only = True
        elif t_clean == "konflik":
            stmt = stmt.where(
                or_(
                    col(IPAllocation.ip_address).in_(conflict_ips) if conflict_ips else False,
                    func.lower(IPAllocation.status) == "konflik",
                )
            )
        else:
            stmt = stmt.where(func.lower(IPAllocation.tipe) == t_clean)

    if orphan_only:
        if orphan_ids:
            stmt = stmt.where(col(IPAllocation.id).in_(orphan_ids))
        else:
            stmt = stmt.where(IPAllocation.id == -1)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()

    # Pengurutan wajib numerik berdasarkan ip_int ASC
    rows = session.exec(
        stmt.order_by(col(IPAllocation.ip_int).asc(), col(IPAllocation.id).asc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
    ).all()

    items = [
        IPAllocationPublic.from_model(
            r,
            is_orphan=(r.id in orphan_ids),
            is_conflict=(r.ip_address in conflict_ips or r.status.lower() == "konflik"),
        )
        for r in rows
    ]

    return IPAllocationPageResponse(
        items=items,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
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
    return IPAllocationPublic.from_model(
        row,
        is_orphan=(row.id in orphan_ids),
        is_conflict=(row.ip_address in conflict_ips or row.status.lower() == "konflik"),
    )


@router.post("", response_model=IPAllocationPublic, status_code=status.HTTP_201_CREATED)
def create_ip_allocation(
    payload: IPAllocationCreate,
    session: SessionDep,
    _: EditorUserDep,
) -> IPAllocationPublic:
    """Membuat alokasi IP / VM baru dengan deteksi konflik IP dan validasi host VM."""
    canonical_ip, ip_int = parse_and_validate_ipv4(payload.ip_address)
    _check_ip_conflict(session, canonical_ip, payload.status)

    resolved_host_id, resolved_host_name = _validate_and_resolve_host(
        session,
        payload.id_aset_host,
        payload.host_name,
    )

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
        port_servis=payload.port_servis.strip(),
        mac_address=payload.mac_address.strip(),
        pengguna=payload.pengguna.strip(),
        keterangan=payload.keterangan.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

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
    if "host" in data and "host_name" not in data:
        data["host_name"] = data.pop("host") or ""
    else:
        data.pop("host", None)

    new_ip = data.get("ip_address", row.ip_address)
    new_status = data.get("status", row.status)
    canonical_ip, ip_int = parse_and_validate_ipv4(new_ip)
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
        if key in ("id", "ip_address", "ip_int", "created_at"):
            continue
        if hasattr(row, key):
            setattr(row, key, val.strip() if isinstance(val, str) else val)

    if row.is_vm and not row.host_name and not row.id_aset_host:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="VM wajib memiliki host induk (host_name atau id_aset_host)",
        )

    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)

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
    return {"status": "ok", "id": item_id, "ip_address": deleted_ip}

