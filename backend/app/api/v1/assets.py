"""Endpoint CRUD Aset TI, pencarian, filter, dan generator ID otomatis."""

import re

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from app.core.master_data import get_prefix_for_category
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.base import utcnow
from app.schemas.asset import (
    FORBIDDEN_FIELDS,
    AssetCreate,
    AssetPageResponse,
    AssetPublic,
    AssetUpdate,
    _clean_serial_number,
)

router = APIRouter()

ID_PATTERN = re.compile(r"^([A-Z]+)-(\d+)$")


def generate_next_asset_id(session: Session, kategori: str) -> str:
    """Menghasilkan ID aset otomatis berikutnya dengan format {PREFIX}-{NNN}."""
    prefix = get_prefix_for_category(kategori)
    existing_ids = session.exec(
        select(Asset.id_aset).where(col(Asset.id_aset).like(f"{prefix}-%"))
    ).all()

    max_num = 0
    for code in existing_ids:
        match = ID_PATTERN.match(code.strip().upper())
        if match and match.group(1) == prefix:
            max_num = max(max_num, int(match.group(2)))

    return f"{prefix}-{max_num + 1:03d}"


def _check_duplicate_sn(
    session: Session,
    serial_number: str | None,
    exclude_asset_id: int | None = None,
) -> None:
    """Menolak serial_number yang sudah dipakai aset lain dengan HTTP 409 Conflict."""
    if not serial_number:
        return

    stmt = select(Asset).where(
        func.lower(Asset.serial_number) == serial_number.lower()
    )
    if exclude_asset_id is not None:
        stmt = stmt.where(Asset.id != exclude_asset_id)

    conflict = session.exec(stmt).first()
    if conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Serial number '{serial_number}' sudah terdaftar "
                f"pada aset {conflict.id_aset}"
            ),
        )


def _compute_counts_and_summary(session: Session) -> tuple[dict[str, int], dict[str, int]]:
    """Menghitung tab_counts (per kategori) dan summary (per status) untuk UI frontend."""
    all_assets = session.exec(select(Asset.kategori, Asset.status)).all()
    total_all = len(all_assets)

    tab_counts: dict[str, int] = {"Semua": total_all, "all": total_all}
    summary: dict[str, int] = {
        "total": total_all,
        "aktif": 0,
        "gudang": 0,
        "perbaikan": 0,
        "rusak": 0,
    }

    for kat, st in all_assets:
        tab_counts[kat] = tab_counts.get(kat, 0) + 1
        st_lower = (st or "").lower()
        if st_lower in ("aktif", "digunakan"):
            summary["aktif"] += 1
        elif st_lower in ("cadangan", "backup", "gudang"):
            summary["gudang"] += 1
        elif st_lower in ("perbaikan", "maintenance"):
            summary["perbaikan"] += 1
        elif st_lower in ("rusak", "tidak digunakan", "nonaktif"):
            summary["rusak"] += 1

    return tab_counts, summary


@router.get("/next-id")
def preview_next_asset_id(
    session: SessionDep,
    _: CurrentUserDep,
    kategori: str = Query(default="PC", min_length=1),
) -> dict[str, str]:
    """Mengembalikan pratinjau ID aset otomatis berikutnya untuk kategori tertentu."""
    return {
        "kategori": kategori,
        "id_aset": generate_next_asset_id(session, kategori),
    }


@router.get("", response_model=AssetPageResponse)
def list_assets(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    kondisi: str | None = Query(default=None),
) -> AssetPageResponse:
    """Mengambil daftar aset berhalaman dengan filter, pencarian, tab_counts, dan summary."""
    stmt = select(Asset)

    keyword = (search or q or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                col(Asset.id_aset).ilike(pattern),
                col(Asset.nama_aset).ilike(pattern),
                col(Asset.serial_number).ilike(pattern),
                col(Asset.merek).ilike(pattern),
                col(Asset.model).ilike(pattern),
                col(Asset.penanggung_jawab).ilike(pattern),
            )
        )

    if kategori and kategori.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(Asset.kategori) == kategori.strip().lower())

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(Asset.lokasi) == lokasi.strip().lower())

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(Asset.status) == status_filter.strip().lower())

    if kondisi and kondisi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(Asset.kondisi) == kondisi.strip().lower())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()

    rows = session.exec(
        stmt.order_by(Asset.id_aset.asc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
    ).all()

    tab_counts, summary = _compute_counts_and_summary(session)

    return AssetPageResponse(
        items=[AssetPublic.from_asset(r) for r in rows],
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
    )


@router.get("/{id_aset}", response_model=AssetPublic)
def get_asset_detail(
    id_aset: str,
    session: SessionDep,
    _: CurrentUserDep,
) -> AssetPublic:
    """Mengambil detail satu aset berdasarkan id_aset."""
    asset = session.exec(
        select(Asset).where(func.lower(Asset.id_aset) == id_aset.strip().lower())
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )
    return AssetPublic.from_asset(asset)


@router.post("", response_model=AssetPublic, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    session: SessionDep,
    _: EditorUserDep,
) -> AssetPublic:
    """Membuat aset baru dengan ID otomatis dan validasi duplikat SN."""
    _check_duplicate_sn(session, payload.serial_number)

    if payload.id_aset and payload.id_aset.strip():
        final_id_aset = payload.id_aset.strip().upper()
        existing_code = session.exec(
            select(Asset).where(func.lower(Asset.id_aset) == final_id_aset.lower())
        ).first()
        if existing_code is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"ID aset '{final_id_aset}' sudah digunakan",
            )
    else:
        final_id_aset = generate_next_asset_id(session, payload.kategori)

    extra_raw = payload.model_extra or {}
    clean_extra = {
        k: v for k, v in extra_raw.items() if k.lower() not in FORBIDDEN_FIELDS
    }

    asset = Asset(
        id_aset=final_id_aset,
        nama_aset=payload.nama_aset,
        kategori=payload.kategori,
        merek=payload.merek.strip(),
        model=payload.model.strip(),
        serial_number=payload.serial_number,
        lokasi=payload.lokasi,
        detail_lokasi=payload.detail_lokasi.strip(),
        penanggung_jawab=payload.penanggung_jawab.strip(),
        status=payload.status,
        kondisi=payload.kondisi,
        tanggal_masuk=payload.tanggal_masuk,
        processor=payload.processor.strip(),
        motherboard=payload.motherboard.strip(),
        ram=payload.ram.strip(),
        storage=payload.storage.strip(),
        gpu=payload.gpu.strip(),
        os=payload.os.strip(),
        watt=payload.watt,
        ukuran_layar=payload.ukuran_layar.strip(),
        resolusi=payload.resolusi.strip(),
        panel=payload.panel.strip(),
        port_display=payload.port_display.strip(),
        kapasitas_va=payload.kapasitas_va,
        kapasitas_watt=payload.kapasitas_watt,
        baterai=payload.baterai.strip(),
        jumlah_baterai=payload.jumlah_baterai,
        beban_perangkat=payload.beban_perangkat.strip(),
        ip_address=payload.ip_address.strip(),
        mac_address=payload.mac_address.strip(),
        koneksi=payload.koneksi.strip(),
        catatan=payload.catatan.strip(),
        extra_specs=clean_extra,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return AssetPublic.from_asset(asset)


def _apply_asset_update(
    id_aset: str,
    payload: AssetUpdate,
    session: Session,
) -> AssetPublic:
    asset = session.exec(
        select(Asset).where(func.lower(Asset.id_aset) == id_aset.strip().lower())
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "ruangan" in update_data and "detail_lokasi" not in update_data:
        update_data["detail_lokasi"] = update_data.pop("ruangan") or ""
    else:
        update_data.pop("ruangan", None)

    if "pengguna" in update_data and "penanggung_jawab" not in update_data:
        update_data["penanggung_jawab"] = update_data.pop("pengguna") or ""
    else:
        update_data.pop("pengguna", None)

    if "tanggal_masuk_gudang" in update_data and "tanggal_masuk" not in update_data:
        update_data["tanggal_masuk"] = update_data.pop("tanggal_masuk_gudang")
    else:
        update_data.pop("tanggal_masuk_gudang", None)

    if "serial_number" in update_data:
        cleaned_sn = _clean_serial_number(update_data["serial_number"])
        _check_duplicate_sn(session, cleaned_sn, exclude_asset_id=asset.id)
        update_data["serial_number"] = cleaned_sn

    for field_name, val in update_data.items():
        if field_name.lower() in FORBIDDEN_FIELDS:
            continue
        if hasattr(asset, field_name) and field_name not in ("id", "id_aset", "created_at"):
            setattr(asset, field_name, val.strip() if isinstance(val, str) else val)

    asset.updated_at = utcnow()
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return AssetPublic.from_asset(asset)


@router.put("/{id_aset}", response_model=AssetPublic)
def update_asset_put(
    id_aset: str,
    payload: AssetUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> AssetPublic:
    """Memperbarui data aset berdasarkan id_aset (PUT)."""
    return _apply_asset_update(id_aset, payload, session)


@router.patch("/{id_aset}", response_model=AssetPublic)
def update_asset_patch(
    id_aset: str,
    payload: AssetUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> AssetPublic:
    """Memperbarui sebagian data aset berdasarkan id_aset (PATCH)."""
    return _apply_asset_update(id_aset, payload, session)


@router.delete("/{id_aset}")
def delete_asset(
    id_aset: str,
    session: SessionDep,
    _: AdminUserDep,
) -> dict[str, str]:
    """Menghapus aset berdasarkan id_aset (hanya Administrator)."""
    asset = session.exec(
        select(Asset).where(func.lower(Asset.id_aset) == id_aset.strip().lower())
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )
    deleted_code = asset.id_aset
    session.delete(asset)
    session.commit()
    return {"status": "ok", "id_aset": deleted_code}

