"""Endpoint CRUD IP Address & Virtual Machine (konflik IP, VM tanpa host, urut numerik)."""

from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from app.core.ip_export import (
    build_a4_landscape_ip_pdf,
    build_openxml_xlsx,
    read_xlsx_rows,
)
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.base import utcnow
from app.models.ip_allocation import IPAllocation
from app.schemas.audit import record_audit_log
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
        "bebas": bebas_count,
        "tersedia": bebas_count,
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
    return tab_counts, summary


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
                col(IPAllocation.id_aset).ilike(pattern),
                col(IPAllocation.id_aset_host).ilike(pattern),
                col(IPAllocation.os).ilike(pattern),
                col(IPAllocation.pengguna).ilike(pattern),
                col(IPAllocation.keterangan).ilike(pattern),
            )
        )

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(IPAllocation.lokasi) == lokasi.strip().lower())

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        if st_clean == "konflik":
            only_conflict = True
        else:
            stmt = stmt.where(func.lower(IPAllocation.status) == st_clean)

    if only_vm is True:
        stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
    elif only_vm is False:
        stmt = stmt.where(col(IPAllocation.is_vm).is_(False))

    effective_tipe = (tipe or jenis or "").strip()
    if effective_tipe and effective_tipe.lower() not in ("semua", "all", ""):
        t_clean = effective_tipe.lower()
        if t_clean == "vm":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
        elif t_clean == "fisik":
            stmt = stmt.where(col(IPAllocation.is_vm).is_(False))
        elif t_clean in ("vm tanpa host", "orphan", "orphan_vm"):
            orphan_only = True
        elif t_clean == "konflik":
            only_conflict = True
        else:
            stmt = stmt.where(func.lower(IPAllocation.tipe) == t_clean)

    if grup and grup.strip().lower() not in ("semua", "all", ""):
        g_clean = grup.strip().lower()
        if "vm" in g_clean or "addon" in g_clean:
            stmt = stmt.where(col(IPAllocation.is_vm).is_(True))
        elif "operasional" in g_clean or "fisik" in g_clean:
            stmt = stmt.where(col(IPAllocation.is_vm).is_(False))

    if host and host.strip().lower() not in ("semua", "all", ""):
        h_clean = host.strip()
        h_code = h_clean.split(" ")[0].strip().upper()
        stmt = stmt.where(
            or_(
                func.upper(IPAllocation.id_aset_host) == h_code,
                col(IPAllocation.host_name).ilike(f"%{h_clean}%"),
            )
        )

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

    matched_rows = session.exec(
        stmt.order_by(col(IPAllocation.ip_int).asc(), col(IPAllocation.id).asc())
    ).all()

    all_matching_items = [
        IPAllocationPublic.from_model(
            r,
            is_orphan=(r.id in orphan_ids),
            is_conflict=(r.ip_address in conflict_ips or r.status.lower() == "konflik"),
        )
        for r in matched_rows
    ]

    if subnet and subnet.strip().lower() not in ("semua", "all", ""):
        sub_clean = subnet.strip().lower()
        all_matching_items = [it for it in all_matching_items if it.subnet.lower() == sub_clean]

    if sort_by and sort_by.strip():
        s_key = sort_by.strip()
        rev = (sort_dir or "asc").strip().lower() == "desc"
        if s_key == "ip_address":
            all_matching_items.sort(key=lambda it: it.ip_int, reverse=rev)
        else:
            all_matching_items.sort(
                key=lambda it: str(getattr(it, s_key, "") or "").lower(),
                reverse=rev,
            )

    total = len(all_matching_items)
    items = all_matching_items[page_params.offset : page_params.offset + page_params.page_size]

    all_public_for_opts = [
        IPAllocationPublic.from_model(
            r,
            is_orphan=(r.id in orphan_ids),
            is_conflict=(r.ip_address in conflict_ips or r.status.lower() == "konflik"),
        )
        for r in all_rows
    ]
    subnet_set = sorted({it.subnet for it in all_public_for_opts if it.subnet})
    subnet_options = ["Semua", *subnet_set]

    srv_assets = session.exec(
        select(Asset)
        .where(col(Asset.kategori).in_(["Server", "PC"]))
        .order_by(col(Asset.id_aset).asc())
    ).all()
    server_only_assets = [a for a in srv_assets if a.kategori.lower() == "server"]
    host_options = ["Semua"] + [f"{a.id_aset} ({a.nama_aset})" for a in server_only_assets]
    server_asset_ids = ["—"] + [a.id_aset for a in srv_assets]
    os_set = sorted(
        {r.os.strip() for r in all_rows if r.os and r.os.strip() and r.os.strip() not in ("-", "—")}
    )

    conflict_banner = ""
    if conflict_ips:
        conflict_list = ", ".join(sorted(conflict_ips))
        conflict_banner = f"Terdeteksi bentrok alamat IP pada: {conflict_list}"

    kpi_fe = {
        "total_ip": summary["total_ip"],
        "fisik": summary.get("fisik", summary["operasional"]),
        "vm": summary.get("vm", summary["addon"]),
        "operasional": summary["operasional"],
        "addon": summary["addon"],
        "bentrok": summary["bentrok"],
        "vm_tanpa_host": summary["vm_tanpa_host"],
    }

    return IPAllocationPageResponse(
        items=items,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=kpi_fe,
        conflict_banner=conflict_banner,
        subnet_options=subnet_options,
        host_options=host_options,
        server_asset_ids=server_asset_ids,
        os_suggestions=os_set,
    )


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
            import csv
            import io

            text_csv = raw_bytes.decode("utf-8-sig", errors="replace")
            reader = csv.reader(io.StringIO(text_csv))
            raw_rows = [[str(c).strip() for c in r] for r in reader if any(r)]
    except Exception as exc:
        return {
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
            "valid_count": 0,
            "error_count": 1,
            "valid_rows": [],
            "errors": [
                {"row_number": 1, "ip_address": "—", "reason": "File tidak memiliki baris data"}
            ],
            "error_report_csv": "",
        }

    # Kumpulkan IP eksisting & server fisik aktif untuk validasi
    existing_ips = set(session.exec(select(IPAllocation.ip_address)).all())
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
            str(x).strip() for x in padded
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

        if canonical_ip in seen_in_file or canonical_ip in existing_ips:
            errors.append(
                {
                    "row_number": idx,
                    "ip_address": canonical_ip,
                    "reason": "IP sudah terdaftar (duplikat)",
                }
            )
            continue

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
                "keterangan": ket_val,
                "lokasi": "Head Office (Office Blok 14)",
            }
        )

    import csv
    import io

    err_buf = io.StringIO()
    writer = csv.writer(err_buf)
    writer.writerow(["Baris", "IP Address", "Alasan Error"])
    for e in errors:
        writer.writerow([e["row_number"], e["ip_address"], e["reason"]])

    return {
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
    """Menyimpan seluruh baris valid hasil preview ke database dalam satu transaksi."""
    rows = payload.get("valid_rows", [])
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak ada data baris valid yang dikirim untuk diimpor",
        )

    for item in rows:
        row = IPAllocation(
            ip_address=item["ip_address"],
            ip_int=item["ip_int"],
            subnet=item.get("subnet", "192.168.1.0/24"),
            gateway=item.get("gateway", ""),
            nama_perangkat=item["nama_perangkat"],
            hostname=item.get("hostname", item["nama_perangkat"]),
            tipe=item.get("tipe", "Fisik"),
            status=item.get("status", "Aktif"),
            lokasi=item.get("lokasi", "Head Office (Office Blok 14)"),
            id_aset=item.get("id_aset"),
            is_vm=bool(item.get("is_vm", False)),
            host_name=item.get("host_name", ""),
            id_aset_host=item.get("id_aset_host"),
            os=item.get("os", ""),
            vcpu=int(item.get("vcpu", 0)),
            ram=str(item.get("ram", "")),
            storage=str(item.get("storage", "")),
            port_servis=str(item.get("port_servis", "")),
            mac_address=str(item.get("mac_address", "")),
            pengguna=str(item.get("pengguna", "")),
            keterangan=str(item.get("keterangan", "")),
        )
        session.add(row)

    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=current_user.full_name or current_user.username,
        role=current_user.role,
        aksi="IMPORT",
        modul="Infrastructure",
        target_id="ip_allocations",
        detail=f"Import massal {len(rows)} data IP & Server (VM)",
        level_risiko="Sedang",
    )
    session.commit()
    return {"success": True, "imported_count": len(rows)}


@router.get("/export")
def export_ip_allocations(
    session: SessionDep,
    current_user: CurrentUserDep,
    format: str = Query(default="xlsx"),
    search: str | None = Query(default=None),
    tipe: str | None = Query(default=None),
    jenis: str | None = Query(default=None),
    grup: str | None = Query(default=None),
    host: str | None = Query(default=None),
    subnet: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    only_conflict: bool = Query(default=False),
    only_orphan_vm: bool = Query(default=False),
) -> Response:
    """Ekspor seluruh data IP & Server (VM) sesuai filter aktif dalam format Excel atau PDF."""
    stmt = select(IPAllocation)

    effective_jenis = jenis or tipe
    if effective_jenis and effective_jenis not in ("Semua", "Semua jenis"):
        if effective_jenis == "VM":
            stmt = stmt.where(IPAllocation.is_vm == True)  # noqa: E712
        elif effective_jenis == "Fisik":
            stmt = stmt.where(IPAllocation.is_vm == False)  # noqa: E712

    if grup and grup not in ("Semua", "all"):
        if grup in ("VM", "Addon (VM)"):
            stmt = stmt.where(IPAllocation.is_vm == True)  # noqa: E712
        elif grup in ("Fisik", "Operasional"):
            stmt = stmt.where(IPAllocation.is_vm == False)  # noqa: E712

    if status_filter and status_filter not in ("Semua", "Semua status"):
        stmt = stmt.where(func.lower(IPAllocation.status) == status_filter.lower())

    if subnet and subnet not in ("Semua", "Semua subnet"):
        stmt = stmt.where(func.lower(IPAllocation.subnet) == subnet.lower())

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(IPAllocation.ip_address).like(term),
                func.lower(IPAllocation.nama_perangkat).like(term),
                func.lower(IPAllocation.hostname).like(term),
                func.lower(IPAllocation.host_name).like(term),
                func.lower(IPAllocation.os).like(term),
                func.lower(IPAllocation.keterangan).like(term),
            )
        )

    # Urutkan berdasarkan IPv4 secara numerik naik
    stmt = stmt.order_by(IPAllocation.ip_int.asc())
    rows = session.exec(stmt).all()

    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session, rows)

    export_items: list[dict[str, Any]] = []
    for r in rows:
        is_conf = r.ip_address in conflict_ips or r.status.lower() == "konflik"
        is_orph = r.id in orphan_ids
        if only_conflict and not is_conf:
            continue
        if only_orphan_vm and not is_orph:
            continue
        host_disp = "—" if not r.is_vm else (r.host_name or r.id_aset_host or "Tanpa host")
        export_items.append(
            {
                "ip_address": r.ip_address,
                "nama": r.nama_perangkat,
                "jenis": "VM" if r.is_vm else "Fisik",
                "host_display": host_disp,
                "fungsi": r.keterangan or "—",
                "os": r.os or "—",
                "status": "Konflik" if is_conf else r.status,
                "keterangan": r.keterangan or "—",
            }
        )

    from datetime import datetime

    today_str = datetime.now().strftime("%Y%m%d")

    if format.lower() == "pdf":
        from datetime import datetime

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
        date_lbl = f"{now.day} {months_id[now.month]} {now.year}"
        pdf_bytes = build_a4_landscape_ip_pdf(
            rows=export_items,
            export_date_label=date_lbl,
            exporter_name=current_user.full_name or current_user.username,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="Daftar_IP_Server_VM_{today_str}.pdf"'
            },
        )

    # Default: Excel (.xlsx)
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

    if "fungsi" in data and "keterangan" not in data:
        data["keterangan"] = data.pop("fungsi") or ""
    else:
        data.pop("fungsi", None)

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
