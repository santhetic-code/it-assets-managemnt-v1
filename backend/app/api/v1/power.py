"""Endpoint Rekap Watt Server & Kapasitas UPS (100% turunan dari tabel assets)."""

import math
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.api.v1.assets import generate_next_asset_id
from app.core.master_data import LOCATIONS
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import (
    Asset,
    AssetLink,
    PowerAssumption,
    PowerCatalogItem,
    WattScenario,
)
from app.models.base import utcnow
from app.schemas.audit import record_audit_log
from app.schemas.power import (
    DEFAULT_TARIF_PER_KWH,
    CalculatorRequestSchema,
    CalculatorResultSchema,
    LocationPowerSummary,
    PowerAssumptionSchema,
    PowerCatalogItemSchema,
    PowerUpdatePayload,
    ServerPowerItem,
    UPSPowerItem,
    WattScenarioSchema,
    WattServerPageResponse,
    calculate_load_status,
    calculate_power_metrics,
    calculate_psu_specs,
    effective_ups_watt,
    ups_capacity_source_label,
)

router = APIRouter()

# Cache pendek (TTL 15 detik) yang dibatalkan otomatis saat spesifikasi/asumsi/relasi berubah
_POWER_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SEC = 15.0


def invalidate_power_cache() -> None:
    """Batalkan cache agregat Rekap Watt saat spesifikasi aset, relasi UPS, atau asumsi berubah."""
    _POWER_CACHE.clear()


def _record_power_audit(
    session: Session,
    actor: str,
    action: str,
    target_id: str,
    detail: str,
) -> None:
    """Catat perubahan Asumsi, Katalog Komponen, atau Kapasitas Watt UPS ke Audit Log."""
    record_audit_log(
        session,
        username=actor or "system",
        aksi=action,
        modul="power",
        target_id=target_id or "-",
        detail=detail,
        commit=False,
    )


DEFAULT_CATALOG_SEED: list[dict[str, Any]] = [
    # 15 CPU dari 16 server saat ini (Sumber resmi Intel ARK & AMD)
    {
        "kategori": "cpu",
        "nama": "Intel Core i7-13700",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 219,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i7-13700F",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 219,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i7-12700",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 180,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i5-13400",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 148,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i5-12400",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 117,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i5-10600K",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 182,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i3-10105F",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 90,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i7-10700",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 224,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i7-10700F",
        "merek": "Intel",
        "tdp_w": 65,
        "peak_w": 224,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i7-10700K",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 229,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i9-10900K",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 250,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core i7-9800X",
        "merek": "Intel",
        "tdp_w": 165,
        "peak_w": 210,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "Intel Core Ultra 7 265KF",
        "merek": "Intel",
        "tdp_w": 125,
        "peak_w": 250,
        "jenis_data": "resmi",
        "sumber": "Intel ARK",
    },
    {
        "kategori": "cpu",
        "nama": "AMD Ryzen 7 3800X",
        "merek": "AMD",
        "tdp_w": 105,
        "peak_w": 142,
        "jenis_data": "resmi",
        "sumber": "AMD",
    },
    {
        "kategori": "cpu",
        "nama": "AMD Ryzen 5 5600G",
        "merek": "AMD",
        "tdp_w": 65,
        "peak_w": 88,
        "jenis_data": "resmi",
        "sumber": "AMD",
    },
    # GPU
    {
        "kategori": "gpu",
        "nama": "Intel UHD Graphics (terpadu)",
        "merek": "Intel",
        "tdp_w": 0,
        "peak_w": 0,
        "jenis_data": "resmi",
        "sumber": "Termasuk TDP CPU",
        "catatan": "termasuk TDP CPU",
    },
    {
        "kategori": "gpu",
        "nama": "NVIDIA GeForce GT 1030 2GB",
        "merek": "NVIDIA",
        "tdp_w": 30,
        "peak_w": 35,
        "jenis_data": "resmi",
        "sumber": "NVIDIA",
    },
    {
        "kategori": "gpu",
        "nama": "NVIDIA GeForce GT 730 2GB",
        "merek": "NVIDIA",
        "tdp_w": 38,
        "peak_w": 45,
        "jenis_data": "resmi",
        "sumber": "NVIDIA",
    },
    # Motherboard, RAM, Storage, Kipas (Estimasi umum yang dapat diatur admin)
    {
        "kategori": "motherboard",
        "nama": "Desktop ATX",
        "merek": "Generic",
        "tdp_w": 40,
        "peak_w": 55,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "motherboard",
        "nama": "Desktop Micro-ATX",
        "merek": "Generic",
        "tdp_w": 30,
        "peak_w": 45,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "ram",
        "nama": "RAM DDR4 per modul",
        "merek": "Generic",
        "tdp_w": 3,
        "peak_w": 4,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "ram",
        "nama": "RAM DDR5 per modul",
        "merek": "Generic",
        "tdp_w": 4,
        "peak_w": 5,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "ssd_sata",
        "nama": "SSD SATA 2,5 inci",
        "merek": "Generic",
        "tdp_w": 3,
        "peak_w": 5,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "nvme",
        "nama": "SSD NVMe M.2",
        "merek": "Generic",
        "tdp_w": 7,
        "peak_w": 10,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "hdd",
        "nama": "HDD SATA 3,5 inci 7200 RPM",
        "merek": "Generic",
        "tdp_w": 9,
        "peak_w": 15,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "fan",
        "nama": "Kipas casing",
        "merek": "Generic",
        "tdp_w": 3,
        "peak_w": 5,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "optical",
        "nama": "DVD-RW Internal",
        "merek": "Generic",
        "tdp_w": 15,
        "peak_w": 20,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
    {
        "kategori": "pcie",
        "nama": "Kartu PCIe NIC / HBA",
        "merek": "Generic",
        "tdp_w": 10,
        "peak_w": 15,
        "jenis_data": "estimasi",
        "sumber": "Estimasi umum",
    },
]


def _get_or_create_assumptions(session: Session) -> PowerAssumptionSchema:
    row = session.exec(select(PowerAssumption).order_by(col(PowerAssumption.id).asc())).first()
    if row is None:
        row = PowerAssumption(
            jam_operasional_per_hari=24,
            hari_per_bulan=30,
            faktor_beban_persen=100,
            tarif_listrik_per_kwh=None,
            faktor_daya_ups=0.6,
            batas_waspada_ups=70,
            batas_kritis_ups=85,
            updated_by="system",
        )
        session.add(row)
        session.commit()
        session.refresh(row)
    return PowerAssumptionSchema(
        jam_operasional_per_hari=row.jam_operasional_per_hari,
        hari_per_bulan=row.hari_per_bulan,
        faktor_beban_persen=row.faktor_beban_persen,
        tarif_listrik_per_kwh=row.tarif_listrik_per_kwh,
        faktor_daya_ups=row.faktor_daya_ups,
        batas_waspada_ups=row.batas_waspada_ups,
        batas_kritis_ups=row.batas_kritis_ups,
        updated_by=row.updated_by,
    )


def _ensure_catalog_seeded(session: Session) -> list[PowerCatalogItem]:
    existing = list(session.exec(select(PowerCatalogItem)).all())
    if existing:
        return existing
    for item in DEFAULT_CATALOG_SEED:
        session.add(PowerCatalogItem(**item))
    session.commit()
    return list(session.exec(select(PowerCatalogItem)).all())


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


def _effective_asset_watt(asset: Asset) -> int:
    """Hitung TDP (W) dari specs (tdp_cpu_w + tdp_gpu_w), kolom watt, atau default PC."""
    sp = {**(asset.extra_specs or {}), **(asset.specs or {})}
    cpu_w = int(float(sp.get("tdp_cpu_w") or 0))
    gpu_w = int(float(sp.get("tdp_gpu_w") or 0))
    if cpu_w + gpu_w > 0:
        return cpu_w + gpu_w
    if asset.watt > 0:
        return asset.watt
    raw_tdp = sp.get("tdp_total_w")
    if raw_tdp and str(raw_tdp).isdigit() and int(raw_tdp) > 0:
        return int(raw_tdp)
    if asset.kategori.strip().lower() in ("pc", "laptop"):
        return 95
    return 120


def _map_ups_to_servers(
    session: Session,
    consumers: list[Asset],
    ups_assets: list[Asset],
    asmp: PowerAssumptionSchema,
) -> tuple[list[UPSPowerItem], dict[str, dict[str, Any]]]:
    """Petakan relasi UPS menyuplai Server dari asset_links (serta fallback beban_perangkat)."""
    links = list(
        session.exec(
            select(AssetLink).where(col(AssetLink.tipe) == "menyuplai_daya")
        ).all()
    )
    consumer_by_id = {c.id_aset.strip().upper(): c for c in consumers}
    consumer_by_name = {c.nama_aset.strip().upper(): c for c in consumers}

    ups_server_map: dict[str, list[Asset]] = {u.id_aset.strip().upper(): [] for u in ups_assets}
    for lnk in links:
        u_tag = lnk.asset_id.strip().upper()
        s_tag = lnk.linked_asset_id.strip().upper()
        if u_tag in ups_server_map and s_tag in consumer_by_id:
            srv = consumer_by_id[s_tag]
            if srv not in ups_server_map[u_tag]:
                ups_server_map[u_tag].append(srv)

    # Fallback pencocokan nama dari kolom beban_perangkat bila asset_links belum terisi
    for u in ups_assets:
        u_tag = u.id_aset.strip().upper()
        if ups_server_map[u_tag]:
            continue
        raw_target = (u.beban_perangkat or "").upper().replace("OTOMAX", "OTO")
        if not raw_target or raw_target in ("BACKUP", "RAK JARINGAN", "SYNOLOGY"):
            continue
        for srv_name, srv_obj in consumer_by_name.items():
            if srv_name in raw_target and srv_obj not in ups_server_map[u_tag]:
                ups_server_map[u_tag].append(srv_obj)

    ups_items: list[UPSPowerItem] = []
    server_ups_lookup: dict[str, dict[str, Any]] = {}

    for u in ups_assets:
        u_tag = u.id_aset.strip().upper()
        linked = ups_server_map.get(u_tag, [])
        load_w = sum(
            calculate_power_metrics(
                base_watt=s.watt,
                watt_terukur=(s.extra_specs or {}).get("watt_terukur"),
                jam_per_hari=asmp.jam_operasional_per_hari,
                hari_per_bulan=asmp.hari_per_bulan,
                faktor_beban_persen=asmp.faktor_beban_persen,
                tarif_per_kwh=asmp.tarif_listrik_per_kwh,
            )["effective_watt"]
            for s in linked
        )
        u_item = UPSPowerItem.from_asset(
            u,
            power_factor=asmp.faktor_daya_ups,
            warn_pct=asmp.batas_waspada_ups,
            crit_pct=asmp.batas_kritis_ups,
            linked_servers=[s.nama_aset for s in linked],
            linked_server_ids=[s.id_aset for s in linked],
            beban_server_w=load_w,
        )
        ups_items.append(u_item)
        for s in linked:
            server_ups_lookup[s.id_aset.strip().upper()] = {
                "id_aset": u_item.id_aset,
                "nama_aset": f"{u_item.merek} {u_item.kapasitas_va}VA".strip(),
                "utilisasi_pct": u_item.utilisasi_pct,
                "status": u_item.status_utilisasi,
                "source_label": u_item.sumber_kapasitas,
                "kapasitas_watt": u_item.kapasitas_watt,
                "beban_server_w": u_item.beban_server_w,
            }

    return ups_items, server_ups_lookup


def _build_power_analytics(
    all_assets: list[Asset],
    tarif_per_kwh: float | None = DEFAULT_TARIF_PER_KWH,
    include_all_consumers: bool = False,
    scope: str = "server",
    session: Session | None = None,
    assumptions: PowerAssumptionSchema | None = None,
) -> tuple[
    list[Asset],
    list[UPSPowerItem],
    list[LocationPowerSummary],
    dict[str, int],
    dict[str, Any],
]:
    """Menghitung seluruh metrik daya, UPS, lokasi, tab_counts, dan KPI tanpa duplikat."""
    asmp = assumptions or (
        _get_or_create_assumptions(session)
        if session is not None
        else PowerAssumptionSchema(tarif_listrik_per_kwh=tarif_per_kwh)
    )
    eff_tarif = (
        tarif_per_kwh
        if (tarif_per_kwh is not None and tarif_per_kwh > 0)
        else asmp.tarif_listrik_per_kwh
    )

    raw_consumers = [
        a for a in all_assets if _is_power_consumer(a, include_all_consumers, scope=scope)
    ]
    seen_tags: set[str] = set()
    consumers: list[Asset] = []
    for a in raw_consumers:
        tag_up = a.id_aset.strip().upper()
        if tag_up in seen_tags:
            continue
        seen_tags.add(tag_up)
        if a.watt <= 0:
            a.watt = _effective_asset_watt(a)
        consumers.append(a)
    ups_assets = [a for a in all_assets if a.kategori.strip().lower() == "ups"]

    if session is not None:
        ups_items, server_ups_lookup = _map_ups_to_servers(session, consumers, ups_assets, asmp)
    else:
        ups_items = [
            UPSPowerItem.from_asset(
                u,
                power_factor=asmp.faktor_daya_ups,
                warn_pct=asmp.batas_waspada_ups,
                crit_pct=asmp.batas_kritis_ups,
            )
            for u in ups_assets
        ]
        server_ups_lookup = {}

    active_consumers = [a for a in consumers if a.status.strip().lower() in ("aktif", "digunakan")]
    active_ups = [a for a in ups_assets if a.status.strip().lower() in ("aktif", "digunakan")]

    total_watt = sum(a.watt for a in active_consumers)
    avg_watt = round(total_watt / len(active_consumers)) if active_consumers else 0
    kwh_day = round((total_watt * asmp.jam_operasional_per_hari) / 1000.0, 2)
    kwh_month = round(kwh_day * asmp.hari_per_bulan, 2)
    cost_month = round(kwh_month * float(eff_tarif)) if (eff_tarif and eff_tarif > 0) else None

    total_va_ups = sum(u.kapasitas_va for u in active_ups)
    total_watt_ups = sum(
        effective_ups_watt(u.kapasitas_va, u.kapasitas_watt, power_factor=asmp.faktor_daya_ups)
        for u in active_ups
    )
    overall_load_pct = (
        round((total_watt / total_watt_ups) * 100.0, 1) if total_watt_ups > 0 else 0.0
    )
    overall_load_status = calculate_load_status(
        overall_load_pct,
        warn_pct=asmp.batas_waspada_ups,
        crit_pct=asmp.batas_kritis_ups,
    )

    known_locations = list(LOCATIONS)
    for a in all_assets:
        if a.lokasi and a.lokasi not in known_locations:
            known_locations.append(a.lokasi)

    all_consumer_items = [
        ServerPowerItem.from_asset(
            a,
            assumptions=asmp,
            ups_info=server_ups_lookup.get(a.id_aset.strip().upper()),
            tarif_per_kwh=eff_tarif,
        )
        for a in consumers
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
        loc_ups_watt = sum(
            effective_ups_watt(u.kapasitas_va, u.kapasitas_watt, power_factor=asmp.faktor_daya_ups)
            for u in loc_ups
        )
        loc_load_pct = round((loc_watt / loc_ups_watt) * 100.0, 1) if loc_ups_watt > 0 else 0.0
        loc_kwh_month = round(
            (loc_watt * asmp.jam_operasional_per_hari * asmp.hari_per_bulan) / 1000.0,
            2,
        )
        loc_cost_month = (
            round(loc_kwh_month * float(eff_tarif)) if (eff_tarif and eff_tarif > 0) else 0
        )

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
                status_beban=calculate_load_status(
                    loc_load_pct,
                    warn_pct=asmp.batas_waspada_ups,
                    crit_pct=asmp.batas_kritis_ups,
                ),
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
        "est_kwh_month": round(
            (total_tdp_all * asmp.jam_operasional_per_hari * asmp.hari_per_bulan) / 1000.0
        ),
        "estimasi_biaya_bulan": cost_month,
        "tarif_per_kwh": eff_tarif,
        "total_ups": len(ups_assets),
        "ups_aktif": len(active_ups),
        "total_va_ups": total_va_ups,
        "total_kapasitas_watt_ups": total_watt_ups,
        "persentase_beban_ups": overall_load_pct,
        "status_beban_ups": overall_load_status,
        "server_ups_lookup": server_ups_lookup,
        "assumptions": asmp,
    }

    return consumers, ups_items, by_location, tab_counts, summary


@router.get("/assumptions", response_model=PowerAssumptionSchema)
def get_power_assumptions(
    session: SessionDep,
    _: CurrentUserDep,
) -> PowerAssumptionSchema:
    """Ambil pengaturan asumsi Rekap Watt Server saat ini."""
    return _get_or_create_assumptions(session)


@router.put("/assumptions", response_model=PowerAssumptionSchema)
def update_power_assumptions(
    payload: PowerAssumptionSchema,
    session: SessionDep,
    admin: AdminUserDep,
) -> PowerAssumptionSchema:
    """Ubah pengaturan asumsi (hanya Admin) dan catat ke Audit Log."""
    if payload.batas_waspada_ups >= payload.batas_kritis_ups:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batas waspada UPS harus lebih kecil dari batas kritis UPS.",
        )
    row = session.exec(select(PowerAssumption).order_by(col(PowerAssumption.id).asc())).first()
    if row is None:
        row = PowerAssumption()
    row.jam_operasional_per_hari = payload.jam_operasional_per_hari
    row.hari_per_bulan = payload.hari_per_bulan
    row.faktor_beban_persen = payload.faktor_beban_persen
    row.tarif_listrik_per_kwh = (
        payload.tarif_listrik_per_kwh
        if (payload.tarif_listrik_per_kwh and payload.tarif_listrik_per_kwh > 0)
        else None
    )
    row.faktor_daya_ups = payload.faktor_daya_ups
    row.batas_waspada_ups = payload.batas_waspada_ups
    row.batas_kritis_ups = payload.batas_kritis_ups
    actor_name = getattr(admin, "username", getattr(admin, "email", "admin"))
    row.updated_by = actor_name
    row.updated_at = utcnow()
    session.add(row)
    _record_power_audit(
        session,
        actor=actor_name,
        action="UPDATE_POWER_ASSUMPTIONS",
        target_id="power_assumptions",
        detail=(
            f"Jam={row.jam_operasional_per_hari}h, Hari={row.hari_per_bulan}d, "
            f"FaktorBeban={row.faktor_beban_persen}%, Tarif={row.tarif_listrik_per_kwh}, "
            f"PF_UPS={row.faktor_daya_ups}, Waspada={row.batas_waspada_ups}%, "
            f"Kritis={row.batas_kritis_ups}%"
        ),
    )
    session.commit()
    invalidate_power_cache()
    return _get_or_create_assumptions(session)


@router.get("/catalog", response_model=list[PowerCatalogItemSchema])
def list_power_catalog(
    session: SessionDep,
    _: CurrentUserDep,
    q: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> list[PowerCatalogItemSchema]:
    """Daftar katalog komponen daya dengan filter pencarian & kategori."""
    _ensure_catalog_seeded(session)
    stmt = select(PowerCatalogItem)
    if active_only:
        stmt = stmt.where(col(PowerCatalogItem.aktif).is_(True))
    if kategori and kategori.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(col(PowerCatalogItem.kategori)) == kategori.strip().lower())
    if q and q.strip():
        kw = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            func.lower(col(PowerCatalogItem.nama)).like(kw)
            | func.lower(col(PowerCatalogItem.merek)).like(kw)
        )
    rows = session.exec(
        stmt.order_by(col(PowerCatalogItem.kategori).asc(), col(PowerCatalogItem.nama).asc())
    ).all()
    return [
        PowerCatalogItemSchema(
            id=r.id,
            kategori=r.kategori,  # type: ignore[arg-type]
            nama=r.nama,
            merek=r.merek,
            tdp_w=r.tdp_w,
            peak_w=r.peak_w,
            jenis_data=r.jenis_data,  # type: ignore[arg-type]
            sumber=r.sumber,
            catatan=r.catatan,
            diperbarui_oleh=r.diperbarui_oleh,
            diperbarui_pada=r.updated_at,
            aktif=r.aktif,
        )
        for r in rows
    ]


@router.post(
    "/catalog",
    response_model=PowerCatalogItemSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_power_catalog_item(
    payload: PowerCatalogItemSchema,
    session: SessionDep,
    admin: AdminUserDep,
) -> PowerCatalogItemSchema:
    """Tambah komponen baru ke katalog daya (hanya Admin) + Audit Log."""
    tdp_val = (
        0
        if (payload.kategori == "gpu" and "terpadu" in payload.nama.lower())
        else payload.tdp_w
    )
    catatan_val = (
        "termasuk TDP CPU"
        if (payload.kategori == "gpu" and tdp_val == 0 and not payload.catatan)
        else payload.catatan
    )
    actor_name = getattr(admin, "username", getattr(admin, "email", "admin"))
    item = PowerCatalogItem(
        kategori=payload.kategori,
        nama=payload.nama.strip(),
        merek=payload.merek.strip(),
        tdp_w=tdp_val,
        peak_w=payload.peak_w,
        jenis_data=payload.jenis_data,
        sumber=payload.sumber.strip(),
        catatan=catatan_val.strip(),
        diperbarui_oleh=actor_name,
        aktif=payload.aktif,
    )
    session.add(item)
    session.flush()
    _record_power_audit(
        session,
        actor=actor_name,
        action="CREATE_POWER_CATALOG",
        target_id=str(item.id),
        detail=f"Tambah komponen katalog {item.kategori}: {item.nama} ({item.tdp_w} W)",
    )
    session.commit()
    session.refresh(item)
    invalidate_power_cache()
    payload.id = item.id
    payload.tdp_w = item.tdp_w
    payload.catatan = item.catatan
    return payload


@router.put("/catalog/{item_id}", response_model=PowerCatalogItemSchema)
def update_power_catalog_item(
    item_id: int,
    payload: PowerCatalogItemSchema,
    session: SessionDep,
    admin: AdminUserDep,
) -> PowerCatalogItemSchema:
    """Ubah atau nonaktifkan komponen katalog daya (hanya Admin) + Audit Log."""
    item = session.get(PowerCatalogItem, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item katalog tidak ditemukan",
        )
    item.kategori = payload.kategori
    item.nama = payload.nama.strip()
    item.merek = payload.merek.strip()
    item.tdp_w = (
        0
        if (payload.kategori == "gpu" and "terpadu" in payload.nama.lower())
        else payload.tdp_w
    )
    item.peak_w = payload.peak_w
    item.jenis_data = payload.jenis_data
    item.sumber = payload.sumber.strip()
    item.catatan = payload.catatan.strip()
    actor_name = getattr(admin, "username", getattr(admin, "email", "admin"))
    item.aktif = payload.aktif
    item.diperbarui_oleh = actor_name
    item.updated_at = utcnow()
    session.add(item)
    _record_power_audit(
        session,
        actor=actor_name,
        action="UPDATE_POWER_CATALOG",
        target_id=str(item.id),
        detail=f"Ubah komponen katalog {item.nama}: TDP={item.tdp_w}W, Aktif={item.aktif}",
    )
    session.commit()
    session.refresh(item)
    invalidate_power_cache()
    payload.id = item.id
    return payload


@router.post("/calculate", response_model=CalculatorResultSchema)
def calculate_server_watt_endpoint(
    payload: CalculatorRequestSchema,
    session: SessionDep,
    _: CurrentUserDep,
) -> CalculatorResultSchema:
    """Mesin hitung tunggal untuk Kalkulator Watt Server & Simulasi (identik dengan Rekap)."""
    asmp = _get_or_create_assumptions(session)
    catalog_rows = _ensure_catalog_seeded(session)
    cat_by_id = {r.id: r for r in catalog_rows if r.id is not None}

    komposisi: dict[str, int] = {
        "CPU": 0,
        "Motherboard": 0,
        "Storage": 0,
        "RAM": 0,
        "GPU": 0,
        "Kipas": 0,
        "Lainnya": 0,
    }
    base_watt = 0

    for comp in payload.components:
        if comp.qty <= 0:
            continue
        unit_w = 0
        if comp.custom_watt is not None and comp.custom_watt >= 0:
            unit_w = comp.custom_watt
        elif comp.catalog_id and comp.catalog_id in cat_by_id:
            c_item = cat_by_id[comp.catalog_id]
            if payload.mode == "puncak" and c_item.peak_w is not None and c_item.peak_w > 0:
                unit_w = c_item.peak_w
            else:
                unit_w = c_item.tdp_w
        sub_w = unit_w * comp.qty
        base_watt += sub_w

        kat_low = comp.kategori.lower()
        if kat_low == "cpu":
            komposisi["CPU"] += sub_w
        elif kat_low == "gpu":
            komposisi["GPU"] += sub_w
        elif kat_low == "motherboard":
            komposisi["Motherboard"] += sub_w
        elif kat_low == "ram":
            komposisi["RAM"] += sub_w
        elif kat_low in ("ssd_sata", "nvme", "hdd", "storage"):
            komposisi["Storage"] += sub_w
        elif kat_low == "fan":
            komposisi["Kipas"] += sub_w
        else:
            komposisi["Lainnya"] += sub_w

    metrics = calculate_power_metrics(
        base_watt=base_watt,
        watt_terukur=None,
        jam_per_hari=asmp.jam_operasional_per_hari,
        hari_per_bulan=asmp.hari_per_bulan,
        faktor_beban_persen=asmp.faktor_beban_persen,
        tarif_per_kwh=asmp.tarif_listrik_per_kwh,
    )
    eff_w = metrics["effective_watt"]
    psu_info = calculate_psu_specs(eff_w)

    ups_check: dict[str, Any] | None = None
    min_ups_recommended_w = (
        math.ceil(eff_w / (asmp.batas_waspada_ups / 100.0)) if eff_w > 0 else 0
    )

    if payload.ups_id:
        ups_asset = session.exec(
            select(Asset).where(func.lower(col(Asset.id_aset)) == payload.ups_id.strip().lower())
        ).first()
        if ups_asset is not None:
            cap_w = effective_ups_watt(
                ups_asset.kapasitas_va,
                ups_asset.kapasitas_watt,
                power_factor=asmp.faktor_daya_ups,
            )
            is_manual = (ups_asset.kapasitas_watt or 0) > 0
            other_servers_w = 0
            links = session.exec(
                select(AssetLink).where(
                    (func.lower(col(AssetLink.asset_id)) == ups_asset.id_aset.lower())
                    & (col(AssetLink.tipe) == "menyuplai_daya")
                )
            ).all()
            for lnk in links:
                if (
                    payload.asset_id
                    and lnk.linked_asset_id.lower() == payload.asset_id.strip().lower()
                ):
                    continue
                linked_srv = session.exec(
                    select(Asset).where(
                        func.lower(col(Asset.id_aset)) == lnk.linked_asset_id.lower()
                    )
                ).first()
                if linked_srv:
                    other_servers_w += linked_srv.watt or 0

            total_ups_load_w = other_servers_w + eff_w
            util_pct = round((total_ups_load_w / cap_w) * 100.0, 1) if cap_w > 0 else 0.0
            src_lbl = ups_capacity_source_label(ups_asset.kapasitas_watt)
            ups_check = {
                "id_aset": ups_asset.id_aset,
                "nama_ups": (
                    f"{ups_asset.id_aset} · {ups_asset.merek} {ups_asset.kapasitas_va}VA · "
                    f"{cap_w} W ({src_lbl.lower()})"
                ),
                "kapasitas_watt": cap_w,
                "sumber_kapasitas": src_lbl,
                "total_beban_ups_w": total_ups_load_w,
                "utilisasi_pct": util_pct,
                "status": calculate_load_status(
                    util_pct,
                    warn_pct=asmp.batas_waspada_ups,
                    crit_pct=asmp.batas_kritis_ups,
                    is_estimated_capacity=not is_manual,
                ),
                "ups_minimal_disarankan_w": min_ups_recommended_w,
            }

    komp_filtered = {
        k: v
        for k, v in komposisi.items()
        if v > 0 or k in ("CPU", "Motherboard", "Storage", "RAM", "Kipas")
    }

    return CalculatorResultSchema(
        beban_dasar_w=base_watt,
        beban_efektif_w=eff_w,
        mode=payload.mode,
        faktor_beban_persen=asmp.faktor_beban_persen,
        psu_min_w=psu_info["psu_min_w"],
        psu_rekomendasi_w=psu_info["psu_rekomendasi_w"],
        formula_psu_min_w=psu_info["formula_psu_min_w"],
        formula_psu_rek_w=psu_info["formula_psu_rek_w"],
        psu_formula_text=psu_info["psu_formula_text"],
        kwh_per_bulan=metrics["kwh_per_bulan"],
        estimasi_biaya_bulan=metrics["estimasi_biaya_bulan"],
        source_label="Estimasi dari katalog",
        komposisi=komp_filtered,
        ups_check=ups_check or {"ups_minimal_disarankan_w": min_ups_recommended_w},
    )


@router.patch("/ups/{id_aset}/capacity", response_model=UPSPowerItem)
def update_ups_manual_capacity(
    id_aset: str,
    session: SessionDep,
    editor: EditorUserDep,
    kapasitas_watt: int = Query(..., ge=0),
) -> UPSPowerItem:
    """Inline edit kapasitas_watt UPS dari datasheet + validasi VA + Audit Log."""
    ups = session.exec(
        select(Asset).where(func.lower(col(Asset.id_aset)) == id_aset.strip().lower())
    ).first()
    if ups is None or ups.kategori.strip().lower() != "ups":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset UPS tidak ditemukan",
        )

    old_val = ups.kapasitas_watt
    ups.kapasitas_watt = kapasitas_watt
    ups.updated_at = utcnow()
    session.add(ups)
    actor_name = getattr(editor, "username", getattr(editor, "email", "editor"))
    _record_power_audit(
        session,
        actor=actor_name,
        action="UPDATE_UPS_CAPACITY_WATT",
        target_id=ups.id_aset,
        detail=(
            f"Ubah kapasitas_watt UPS {ups.id_aset} dari {old_val} W menjadi "
            f"{kapasitas_watt} W (VA={ups.kapasitas_va})"
        ),
    )
    session.commit()
    session.refresh(ups)
    invalidate_power_cache()
    asmp = _get_or_create_assumptions(session)
    return UPSPowerItem.from_asset(
        ups,
        power_factor=asmp.faktor_daya_ups,
        warn_pct=asmp.batas_waspada_ups,
        crit_pct=asmp.batas_kritis_ups,
    )


@router.get("/scenarios", response_model=list[WattScenarioSchema])
def list_watt_scenarios(
    session: SessionDep,
    _: CurrentUserDep,
) -> list[WattScenarioSchema]:
    """Mengambil riwayat skenario simulasi daya."""
    rows = session.exec(select(WattScenario).order_by(col(WattScenario.id).desc())).all()
    return [
        WattScenarioSchema(
            id=r.id,
            nama=r.nama,
            asset_id=r.asset_id,
            komponen=r.komponen,
            hasil=r.hasil,
            dibuat_oleh=r.dibuat_oleh,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post(
    "/scenarios",
    response_model=WattScenarioSchema,
    status_code=status.HTTP_201_CREATED,
)
def save_watt_scenario(
    payload: WattScenarioSchema,
    session: SessionDep,
    user: CurrentUserDep,
) -> WattScenarioSchema:
    """Menyimpan skenario simulasi daya baru."""
    actor_name = getattr(user, "username", getattr(user, "email", "user"))
    row = WattScenario(
        nama=payload.nama.strip(),
        asset_id=payload.asset_id,
        komponen=payload.komponen,
        hasil=payload.hasil,
        dibuat_oleh=actor_name,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    payload.id = row.id
    payload.created_at = row.created_at
    return payload


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
    tarif_per_kwh: float | None = Query(default=None),
) -> WattServerPageResponse:
    """Mengambil Rekap Watt Server & UPS yang diturunkan langsung dari tabel assets."""
    asmp = _get_or_create_assumptions(session)
    effective_tarif = (
        tarif_per_kwh
        if (tarif_per_kwh is not None and tarif_per_kwh > 0)
        else asmp.tarif_listrik_per_kwh
    )

    all_assets = list(
        session.exec(
            select(Asset).where(col(Asset.deleted_at).is_(None)).order_by(col(Asset.id_aset).asc())
        ).all()
    )
    consumers, ups_items, by_location, tab_counts, summary = _build_power_analytics(
        all_assets,
        tarif_per_kwh=effective_tarif,
        include_all_consumers=include_all_consumers,
        scope=scope or "server",
        session=session,
        assumptions=asmp,
    )

    server_ups_lookup = summary.get("server_ups_lookup", {})
    all_items = [
        ServerPowerItem.from_asset(
            a,
            assumptions=asmp,
            ups_info=server_ups_lookup.get(a.id_aset.strip().upper()),
            tarif_per_kwh=effective_tarif,
        )
        for a in consumers
    ]

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
        if s_key in (
            "tdp_total_w",
            "psu_min_w",
            "psu_rekomendasi_w",
            "watt",
            "beban_efektif_w",
        ):
            all_items.sort(key=lambda it: int(getattr(it, s_key, 0) or 0), reverse=rev)
        else:
            all_items.sort(
                key=lambda it: str(getattr(it, s_key, "") or "").lower(),
                reverse=rev,
            )

    top_servers = sorted(all_items, key=lambda it: it.beban_efektif_w, reverse=True)[:5]
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
        assumptions=asmp,
        top_servers=top_servers,
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
    asmp = _get_or_create_assumptions(session)
    return [
        UPSPowerItem.from_asset(
            r,
            power_factor=asmp.faktor_daya_ups,
            warn_pct=asmp.batas_waspada_ups,
            crit_pct=asmp.batas_kritis_ups,
        )
        for r in rows
    ]


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
    invalidate_power_cache()
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
    if "psu_terpasang_watt" in data and data["psu_terpasang_watt"] is not None:
        extra["psu_terpasang_watt"] = int(data.pop("psu_terpasang_watt"))
    if "watt_terukur" in data and data["watt_terukur"] is not None:
        extra["watt_terukur"] = int(data.pop("watt_terukur"))
    if "tanggal_ukur_watt" in data and data["tanggal_ukur_watt"] is not None:
        extra["tanggal_ukur_watt"] = str(data.pop("tanggal_ukur_watt"))
    if "catalog_refs" in data and data["catalog_refs"] is not None:
        extra["catalog_refs"] = data.pop("catalog_refs")
    if "komposisi_beban" in data and data["komposisi_beban"] is not None:
        extra["komposisi_beban"] = data.pop("komposisi_beban")
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
    invalidate_power_cache()

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
    invalidate_power_cache()
    return {"status": "ok", "id_aset": deleted_code}
