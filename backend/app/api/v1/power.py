"""Endpoint Rekap Watt Server & Kapasitas UPS (100% turunan dari tabel assets)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.master_data import LOCATIONS
from app.deps import CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.base import utcnow
from app.schemas.power import (
    DAYS_PER_MONTH,
    DEFAULT_TARIF_PER_KWH,
    HOURS_PER_DAY,
    LocationPowerSummary,
    PowerUpdatePayload,
    ServerPowerItem,
    UPSPowerItem,
    WattServerPageResponse,
    calculate_load_status,
    effective_ups_watt,
)

router = APIRouter()


def _is_power_consumer(asset: Asset, include_all_consumers: bool = False) -> bool:
    """Menentukan apakah aset termasuk ke dalam daftar Rekap Watt Server."""
    kat = asset.kategori.strip().lower()
    if kat == "ups":
        return False
    if kat == "server":
        return True
    if include_all_consumers and asset.watt > 0:
        return True
    return False


def _build_power_analytics(
    all_assets: list[Asset],
    tarif_per_kwh: float,
    include_all_consumers: bool,
) -> tuple[
    list[Asset],
    list[UPSPowerItem],
    list[LocationPowerSummary],
    dict[str, int],
    dict[str, Any],
]:
    """Menghitung seluruh metrik daya, UPS, lokasi, tab_counts, dan KPI dari daftar Asset."""
    consumers = [
        a for a in all_assets if _is_power_consumer(a, include_all_consumers)
    ]
    ups_assets = [a for a in all_assets if a.kategori.strip().lower() == "ups"]

    active_consumers = [
        a for a in consumers if a.status.strip().lower() in ("aktif", "digunakan")
    ]
    active_ups = [
        a for a in ups_assets if a.status.strip().lower() in ("aktif", "digunakan")
    ]

    total_watt = sum(a.watt for a in active_consumers)
    avg_watt = round(total_watt / len(active_consumers)) if active_consumers else 0
    kwh_day = round((total_watt * HOURS_PER_DAY) / 1000.0, 2)
    kwh_month = round(kwh_day * DAYS_PER_MONTH, 2)
    cost_month = round(kwh_month * tarif_per_kwh)

    total_va_ups = sum(u.kapasitas_va for u in active_ups)
    total_watt_ups = sum(
        effective_ups_watt(u.kapasitas_va, u.kapasitas_watt) for u in active_ups
    )
    overall_load_pct = (
        round((total_watt / total_watt_ups) * 100.0, 1) if total_watt_ups > 0 else 0.0
    )
    overall_load_status = calculate_load_status(overall_load_pct)

    # Rekap per lokasi
    known_locations = list(LOCATIONS)
    for a in all_assets:
        if a.lokasi and a.lokasi not in known_locations:
            known_locations.append(a.lokasi)

    by_location: list[LocationPowerSummary] = []
    tab_counts: dict[str, int] = {
        "Semua": len(consumers),
        "all": len(consumers),
        "Server": sum(1 for a in consumers if a.kategori.strip().lower() == "server"),
        "UPS": len(ups_assets),
    }

    for loc in known_locations:
        loc_consumers = [a for a in consumers if a.lokasi.lower() == loc.lower()]
        loc_active_consumers = [
            a for a in active_consumers if a.lokasi.lower() == loc.lower()
        ]
        loc_ups = [u for u in active_ups if u.lokasi.lower() == loc.lower()]

        tab_counts[loc] = len(loc_consumers)

        loc_watt = sum(a.watt for a in loc_active_consumers)
        loc_va = sum(u.kapasitas_va for u in loc_ups)
        loc_ups_watt = sum(
            effective_ups_watt(u.kapasitas_va, u.kapasitas_watt) for u in loc_ups
        )
        loc_load_pct = (
            round((loc_watt / loc_ups_watt) * 100.0, 1) if loc_ups_watt > 0 else 0.0
        )
        loc_kwh_month = round(
            (loc_watt * HOURS_PER_DAY * DAYS_PER_MONTH) / 1000.0,
            2,
        )
        loc_cost_month = round(loc_kwh_month * tarif_per_kwh)

        by_location.append(
            LocationPowerSummary(
                lokasi=loc,
                jumlah_server=sum(
                    1 for a in loc_consumers if a.kategori.strip().lower() == "server"
                ),
                jumlah_perangkat_daya=len(loc_consumers),
                jumlah_ups=len(loc_ups),
                total_watt=loc_watt,
                total_va_ups=loc_va,
                total_kapasitas_watt_ups=loc_ups_watt,
                persentase_beban_ups=loc_load_pct,
                status_beban=calculate_load_status(loc_load_pct),
                kwh_per_bulan=loc_kwh_month,
                estimasi_biaya_bulan=loc_cost_month,
            )
        )

    summary: dict[str, Any] = {
        "total_server": len(consumers),
        "server_aktif": len(active_consumers),
        "total_watt": total_watt,
        "rata_rata_watt": avg_watt,
        "estimasi_kwh_hari": kwh_day,
        "estimasi_kwh_bulan": kwh_month,
        "estimasi_biaya_bulan": cost_month,
        "tarif_per_kwh": tarif_per_kwh,
        "total_ups": len(ups_assets),
        "ups_aktif": len(active_ups),
        "total_va_ups": total_va_ups,
        "total_kapasitas_watt_ups": total_watt_ups,
        "persentase_beban_ups": overall_load_pct,
        "status_beban_ups": overall_load_status,
    }

    ups_items = [UPSPowerItem.from_asset(u) for u in ups_assets]
    return consumers, ups_items, by_location, tab_counts, summary


@router.get("", response_model=WattServerPageResponse)
def get_watt_server_recap(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_all_consumers: bool = Query(default=True),
    tarif_per_kwh: float = Query(default=DEFAULT_TARIF_PER_KWH, gt=0),
) -> WattServerPageResponse:
    """Mengambil Rekap Watt Server & UPS yang diturunkan langsung dari tabel assets."""
    all_assets = list(
        session.exec(select(Asset).order_by(col(Asset.id_aset).asc())).all()
    )
    consumers, ups_items, by_location, tab_counts, summary = _build_power_analytics(
        all_assets,
        tarif_per_kwh=tarif_per_kwh,
        include_all_consumers=include_all_consumers,
    )

    filtered = consumers
    keyword = (search or q or "").strip().lower()
    if keyword:
        filtered = [
            a
            for a in filtered
            if keyword in a.id_aset.lower()
            or keyword in a.nama_aset.lower()
            or keyword in a.processor.lower()
            or keyword in a.lokasi.lower()
            or keyword in a.beban_perangkat.lower()
        ]

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        loc_clean = lokasi.strip().lower()
        filtered = [a for a in filtered if a.lokasi.lower() == loc_clean]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        filtered = [a for a in filtered if a.status.lower() == st_clean]

    total = len(filtered)
    paged_rows = filtered[
        page_params.offset : page_params.offset + page_params.page_size
    ]
    items = [
        ServerPowerItem.from_asset(a, tarif_per_kwh=tarif_per_kwh)
        for a in paged_rows
    ]

    return WattServerPageResponse(
        items=items,
        ups_items=ups_items,
        by_location=by_location,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=summary,
    )


@router.get("/ups", response_model=list[UPSPowerItem])
def list_ups_units(
    session: SessionDep,
    _: CurrentUserDep,
    lokasi: str | None = Query(default=None),
) -> list[UPSPowerItem]:
    """Mengambil daftar unit UPS yang diturunkan dari aset berkategori UPS."""
    stmt = select(Asset).where(func.lower(col(Asset.kategori)) == "ups")
    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(col(Asset.lokasi)) == lokasi.strip().lower())

    rows = session.exec(stmt.order_by(col(Asset.id_aset).asc())).all()
    return [UPSPowerItem.from_asset(r) for r in rows]


def _update_asset_power_fields(
    id_aset: str,
    payload: PowerUpdatePayload,
    session: Session,
) -> ServerPowerItem | UPSPowerItem:
    asset = session.exec(
        select(Asset).where(func.lower(col(Asset.id_aset)) == id_aset.strip().lower())
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )

    data = payload.model_dump(exclude_unset=True)
    for key, val in data.items():
        if hasattr(asset, key):
            setattr(asset, key, val.strip() if isinstance(val, str) else val)

    asset.updated_at = utcnow()
    session.add(asset)
    session.commit()
    session.refresh(asset)

    if asset.kategori.strip().lower() == "ups":
        return UPSPowerItem.from_asset(asset)
    return ServerPowerItem.from_asset(asset)


@router.patch("/{id_aset}", response_model=ServerPowerItem | UPSPowerItem)
def patch_asset_power(
    id_aset: str,
    payload: PowerUpdatePayload,
    session: SessionDep,
    _: EditorUserDep,
) -> ServerPowerItem | UPSPowerItem:
    """Memperbarui nilai watt atau spesifikasi UPS langsung pada aset terkait."""
    return _update_asset_power_fields(id_aset, payload, session)


@router.put("/{id_aset}", response_model=ServerPowerItem | UPSPowerItem)
def put_asset_power(
    id_aset: str,
    payload: PowerUpdatePayload,
    session: SessionDep,
    _: EditorUserDep,
) -> ServerPowerItem | UPSPowerItem:
    """Memperbarui nilai watt atau spesifikasi UPS langsung pada aset terkait (PUT)."""
    return _update_asset_power_fields(id_aset, payload, session)
