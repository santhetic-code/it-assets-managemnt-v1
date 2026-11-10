"""Endpoint Rekap Watt Server & Kapasitas UPS (100% turunan dari tabel assets)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.api.v1.assets import generate_next_asset_id
from app.core.master_data import LOCATIONS
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
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


def _is_power_consumer(
    asset: Asset,
    include_all_consumers: bool = False,
    scope: str = "server",
) -> bool:
    """Menentukan apakah aset masuk ke laporan Rekap Watt berdasarkan cakupan (scope)."""
    kat = asset.kategori.strip().lower()
    if kat == "ups":
        return False
    scope_clean = (scope or "server").strip().lower()
    if scope_clean in ("pc", "pc operasional"):
        return kat in ("pc", "laptop")
    if scope_clean in ("semua", "all") or include_all_consumers:
        return kat in ("server", "pc", "laptop") or asset.watt > 0
    return kat == "server"


def _build_power_analytics(
    all_assets: list[Asset],
    tarif_per_kwh: float,
    include_all_consumers: bool,
    scope: str = "server",
) -> tuple[
    list[Asset],
    list[UPSPowerItem],
    list[LocationPowerSummary],
    dict[str, int],
    dict[str, Any],
]:
    """Menghitung seluruh metrik daya, UPS, lokasi, tab_counts, dan KPI dari daftar Asset."""
    consumers = [a for a in all_assets if _is_power_consumer(a, include_all_consumers, scope=scope)]
    ups_assets = [a for a in all_assets if a.kategori.strip().lower() == "ups"]

    active_consumers = [a for a in consumers if a.status.strip().lower() in ("aktif", "digunakan")]
    active_ups = [a for a in ups_assets if a.status.strip().lower() in ("aktif", "digunakan")]

    total_watt = sum(a.watt for a in active_consumers)
    avg_watt = round(total_watt / len(active_consumers)) if active_consumers else 0
    kwh_day = round((total_watt * HOURS_PER_DAY) / 1000.0, 2)
    kwh_month = round(kwh_day * DAYS_PER_MONTH, 2)
    cost_month = round(kwh_month * tarif_per_kwh)

    total_va_ups = sum(u.kapasitas_va for u in active_ups)
    total_watt_ups = sum(effective_ups_watt(u.kapasitas_va, u.kapasitas_watt) for u in active_ups)
    overall_load_pct = (
        round((total_watt / total_watt_ups) * 100.0, 1) if total_watt_ups > 0 else 0.0
    )
    overall_load_status = calculate_load_status(overall_load_pct)

    # Rekap per lokasi
    known_locations = list(LOCATIONS)
    for a in all_assets:
        if a.lokasi and a.lokasi not in known_locations:
            known_locations.append(a.lokasi)

    all_consumer_items = [
        ServerPowerItem.from_asset(a, tarif_per_kwh=tarif_per_kwh) for a in consumers
    ]
    op_count = sum(1 for it in all_consumer_items if it.grup_server == "Operasional")
    bk_count = sum(1 for it in all_consumer_items if it.grup_server == "Backup")

    by_location: list[LocationPowerSummary] = []
    tab_counts: dict[str, int] = {
        "Semua": len(consumers),
        "all": len(consumers),
        "Operasional": op_count,
        "Backup": bk_count,
        "Server": sum(1 for a in consumers if a.kategori.strip().lower() == "server"),
        "UPS": len(ups_assets),
    }

    for loc in known_locations:
        loc_consumers = [a for a in consumers if a.lokasi.lower() == loc.lower()]
        loc_active_consumers = [a for a in active_consumers if a.lokasi.lower() == loc.lower()]
        loc_ups = [u for u in active_ups if u.lokasi.lower() == loc.lower()]

        tab_counts[loc] = len(loc_consumers)

        loc_watt = sum(a.watt for a in loc_active_consumers)
        loc_va = sum(u.kapasitas_va for u in loc_ups)
        loc_ups_watt = sum(effective_ups_watt(u.kapasitas_va, u.kapasitas_watt) for u in loc_ups)
        loc_load_pct = round((loc_watt / loc_ups_watt) * 100.0, 1) if loc_ups_watt > 0 else 0.0
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

    total_tdp_all = sum(it.tdp_total_w for it in all_consumer_items)
    total_psu_min_all = sum(it.psu_min_w for it in all_consumer_items)
    total_psu_rek_all = sum(it.psu_rekomendasi_w for it in all_consumer_items)
    avg_tdp_all = round(total_tdp_all / len(all_consumer_items)) if all_consumer_items else 0
    max_item = max(all_consumer_items, key=lambda it: it.tdp_total_w, default=None)

    summary: dict[str, Any] = {
        "total_server": len(consumers),
        "total_servers": len(consumers),
        "server_aktif": len(active_consumers),
        "total_watt": total_watt,
        "total_tdp_w": total_tdp_all,
        "total_tdp_kw": round(total_tdp_all / 1000.0, 2),
        "total_psu_min_w": total_psu_min_all,
        "total_psu_rek_w": total_psu_rek_all,
        "rata_rata_watt": avg_watt,
        "avg_tdp_w": avg_tdp_all,
        "max_tdp_w": max_item.tdp_total_w if max_item else 0,
        "max_tdp_server": max_item.nama_aset if max_item else "—",
        "estimasi_kwh_hari": kwh_day,
        "estimasi_kwh_bulan": kwh_month,
        "est_kwh_month": round((total_tdp_all * HOURS_PER_DAY * DAYS_PER_MONTH) / 1000.0),
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
    tab: str | None = Query(default=None),
    cpu_brand: str | None = Query(default=None),
    beban_level: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="asc"),
    scope: str | None = Query(default="server"),
    include_all_consumers: bool = Query(default=False),
    tarif_per_kwh: float = Query(default=DEFAULT_TARIF_PER_KWH, gt=0),
) -> WattServerPageResponse:
    """Mengambil Rekap Watt Server & UPS yang diturunkan langsung dari tabel assets."""
    all_assets = list(
        session.exec(
            select(Asset).where(col(Asset.deleted_at).is_(None)).order_by(col(Asset.id_aset).asc())
        ).all()
    )
    consumers, ups_items, by_location, tab_counts, summary = _build_power_analytics(
        all_assets,
        tarif_per_kwh=tarif_per_kwh,
        include_all_consumers=include_all_consumers,
        scope=scope or "server",
    )

    all_items = [ServerPowerItem.from_asset(a, tarif_per_kwh=tarif_per_kwh) for a in consumers]

    keyword = (search or q or "").strip().lower()
    if keyword:
        all_items = [
            it
            for it in all_items
            if keyword in it.id_aset.lower()
            or keyword in it.nama_aset.lower()
            or keyword in it.cpu.lower()
            or keyword in it.vga.lower()
            or keyword in it.ram.lower()
            or keyword in it.hdd_ssd.lower()
            or keyword in it.lokasi.lower()
            or keyword in it.beban_perangkat.lower()
        ]

    if tab and tab.strip().lower() not in ("semua", "all", ""):
        t_clean = tab.strip().lower()
        all_items = [it for it in all_items if it.grup_server.lower() == t_clean]

    if cpu_brand and cpu_brand.strip().lower() not in ("semua", "all", ""):
        c_clean = cpu_brand.strip().lower()
        all_items = [it for it in all_items if it.cpu_brand.lower() == c_clean]

    if beban_level and beban_level.strip().lower() not in ("semua", "all", ""):
        b_clean = beban_level.strip().lower()
        all_items = [it for it in all_items if it.beban_level.lower() == b_clean]

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        loc_clean = lokasi.strip().lower()
        all_items = [it for it in all_items if it.lokasi.lower() == loc_clean]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        all_items = [it for it in all_items if it.status.lower() == st_clean]

    if sort_by and sort_by.strip():
        s_key = sort_by.strip()
        rev = (sort_dir or "asc").strip().lower() == "desc"
        if s_key in ("tdp_total_w", "psu_min_w", "psu_rekomendasi_w", "watt"):
            all_items.sort(key=lambda it: int(getattr(it, s_key, 0) or 0), reverse=rev)
        else:
            all_items.sort(
                key=lambda it: str(getattr(it, s_key, "") or "").lower(),
                reverse=rev,
            )

    total = len(all_items)
    items = all_items[page_params.offset : page_params.offset + page_params.page_size]

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


@router.post("", response_model=ServerPowerItem, status_code=status.HTTP_201_CREATED)
def create_server_power(
    payload: PowerUpdatePayload,
    session: SessionDep,
    _: EditorUserDep,
) -> ServerPowerItem:
    """Menambahkan entri server baru atau memperbarui aset server yang sudah ada."""
    target_code = (payload.id_aset or "").strip()
    existing = None
    if target_code:
        existing = session.exec(
            select(Asset).where(func.lower(col(Asset.id_aset)) == target_code.lower())
        ).first()

    if existing is not None:
        res = _update_asset_power_fields(existing.id_aset, payload, session)
        if isinstance(res, ServerPowerItem):
            return res
        return ServerPowerItem.from_asset(existing)

    new_id = target_code.upper() if target_code else generate_next_asset_id(session, "Server")
    nama_val = (payload.nama_aset or f"SERVER {new_id}").strip()
    cpu_val = (payload.cpu or payload.processor or "").strip()
    vga_val = (payload.vga or payload.gpu or "").strip()
    ram_val = (payload.ram or "").strip()
    hdd_val = (payload.hdd_ssd or payload.storage or "").strip()
    tdp_val = payload.tdp_total_w or payload.watt or 120
    psu_min_val = payload.psu_min_w or round(tdp_val * 1.25)
    psu_rek_val = payload.psu_rekomendasi_w or max(450, ((int(tdp_val * 1.6) + 49) // 50) * 50)
    status_val = "Backup" if "BACKUP" in nama_val.upper() else (payload.status or "Digunakan")

    asset = Asset(
        id_aset=new_id,
        nama_aset=nama_val,
        kategori="Server",
        merek="Custom",
        model="Server",
        lokasi=payload.lokasi or "Head Office (Office Blok 14)",
        status=status_val,
        kondisi="Baik",
        processor=cpu_val,
        gpu=vga_val,
        ram=ram_val,
        storage=hdd_val,
        watt=tdp_val,
        catatan=(payload.catatan or "").strip(),
        extra_specs={
            "jenis": "Backup" if status_val == "Backup" else "Server",
            "cpu": cpu_val,
            "vga": vga_val,
            "ram": ram_val,
            "hdd_ssd": hdd_val,
            "tdp_total_w": tdp_val,
            "psu_min_w": psu_min_val,
            "psu_rekomendasi_w": psu_rek_val,
            "psu_minimum_watt": f"{psu_min_val} Watt",
            "psu_rekomendasi_watt": f"{psu_rek_val} Watt",
        },
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return ServerPowerItem.from_asset(asset)


def _update_asset_power_fields(
    id_aset: str,
    payload: PowerUpdatePayload,
    session: Session,
) -> ServerPowerItem | UPSPowerItem:
    asset = session.exec(
        select(Asset).where(
            (func.lower(col(Asset.id_aset)) == id_aset.strip().lower())
            | (func.lower(col(Asset.nama_aset)) == id_aset.strip().lower())
        )
    ).first()
    if asset is None and id_aset.strip().isdigit():
        asset = session.get(Asset, int(id_aset.strip()))
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )

    data = payload.model_dump(exclude_unset=True)
    if "cpu" in data and "processor" not in data:
        data["processor"] = data.pop("cpu") or ""
    else:
        data.pop("cpu", None)

    if "vga" in data and "gpu" not in data:
        data["gpu"] = data.pop("vga") or ""
    else:
        data.pop("vga", None)

    if "hdd_ssd" in data and "storage" not in data:
        data["storage"] = data.pop("hdd_ssd") or ""
    else:
        data.pop("hdd_ssd", None)

    if "tdp_total_w" in data and "watt" not in data:
        data["watt"] = int(data.pop("tdp_total_w") or 0)
    else:
        data.pop("tdp_total_w", None)

    extra = dict(asset.extra_specs or {})
    if "psu_min_w" in data and data["psu_min_w"] is not None:
        pmin = int(data.pop("psu_min_w"))
        extra["psu_min_w"] = pmin
        extra["psu_minimum_watt"] = f"{pmin} Watt"
    if "psu_rekomendasi_w" in data and data["psu_rekomendasi_w"] is not None:
        prek = int(data.pop("psu_rekomendasi_w"))
        extra["psu_rekomendasi_w"] = prek
        extra["psu_rekomendasi_watt"] = f"{prek} Watt"
    if "watt" in data and data["watt"] is not None:
        extra["tdp_total_w"] = int(data["watt"])
    asset.extra_specs = extra

    for key, val in data.items():
        if key in ("id", "id_aset", "created_at"):
            continue
        if hasattr(asset, key) and val is not None:
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


@router.delete("/{id_aset}")
def delete_asset_power(
    id_aset: str,
    session: SessionDep,
    _: AdminUserDep,
) -> dict[str, Any]:
    """Menghapus aset server dari Rekap Watt Server (hanya Administrator)."""
    asset = session.exec(
        select(Asset).where(
            (func.lower(col(Asset.id_aset)) == id_aset.strip().lower())
            | (func.lower(col(Asset.nama_aset)) == id_aset.strip().lower())
        )
    ).first()
    if asset is None and id_aset.strip().isdigit():
        asset = session.get(Asset, int(id_aset.strip()))
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )
    deleted_code = asset.id_aset
    session.delete(asset)
    session.commit()
    return {"status": "ok", "id_aset": deleted_code}
