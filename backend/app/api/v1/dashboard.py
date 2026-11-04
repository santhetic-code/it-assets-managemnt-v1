"""Endpoint Dashboard Asli: agregasi KPI lintas modul secara real-time (B8)."""

from datetime import date
from typing import Any

from fastapi import APIRouter
from sqlmodel import col, select

from app.api.v1.assets import _compute_counts_and_summary as compute_asset_summary
from app.api.v1.finance import _compute_finance_summary as compute_finance_summary
from app.api.v1.ip_vm import (
    _build_counts_and_summary as build_ip_summary,
)
from app.api.v1.ip_vm import (
    _detect_orphan_and_conflict_maps,
)
from app.api.v1.maintenance import (
    _compute_maintenance_summary as compute_maintenance_summary,
)
from app.api.v1.power import _build_power_analytics
from app.core.master_data import CATEGORIES, LOCATIONS
from app.deps import CurrentUserDep, SessionDep
from app.models.asset import Asset
from app.models.audit import AuditLog
from app.models.credential import Credential
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation
from app.models.maintenance import Maintenance
from app.models.user import User
from app.schemas.audit import AuditLogPublic
from app.schemas.dashboard import DashboardAlertItem, DashboardResponse
from app.schemas.finance import PurchasePublic
from app.schemas.maintenance import MaintenancePublic
from app.schemas.power import DEFAULT_TARIF_PER_KWH

router = APIRouter()


@router.get("", response_model=DashboardResponse)
def get_dashboard_overview(
    session: SessionDep,
    _current_user: CurrentUserDep,
) -> DashboardResponse:
    """Mengambil seluruh metrik KPI, distribusi, peringatan, dan aktivitas terbaru."""
    today = date.today()

    # 1. Aset & Daya
    all_assets = list(session.exec(select(Asset)).all())
    _, asset_sum = compute_asset_summary(session)
    _, _, _, _, power_sum = _build_power_analytics(
        all_assets,
        tarif_per_kwh=DEFAULT_TARIF_PER_KWH,
        include_all_consumers=True,
    )

    # 2. IP & VM
    all_ips = list(session.exec(select(IPAllocation)).all())
    orphan_ids, conflict_ips = _detect_orphan_and_conflict_maps(session, all_ips)
    _, ip_sum = build_ip_summary(all_ips, orphan_ids, conflict_ips)

    # 3. Keuangan
    all_purchases = list(
        session.exec(
            select(Purchase).order_by(col(Purchase.tanggal_jatuh_tempo).asc())
        ).all()
    )
    _, fin_sum = compute_finance_summary(all_purchases, today=today)
    all_purchases_pub = [
        PurchasePublic.from_model(p, today=today) for p in all_purchases
    ]
    upcoming_bills = [
        p
        for p in all_purchases_pub
        if p.status.lower() not in ("lunas", "dibatalkan")
    ][:5]

    # 4. Maintenance
    all_mnt = list(
        session.exec(
            select(Maintenance).order_by(col(Maintenance.tanggal_jadwal).asc())
        ).all()
    )
    _, mnt_sum = compute_maintenance_summary(all_mnt, today=today)
    all_mnt_pub = [MaintenancePublic.from_model(m, today=today) for m in all_mnt]
    upcoming_mnt = [m for m in all_mnt_pub if not m.is_history][:5]

    # 5. Kredensial, Pengguna, & Audit Log
    total_credentials = len(session.exec(select(Credential.id)).all())
    total_users = len(session.exec(select(User.id)).all())
    recent_audits_rows = list(
        session.exec(
            select(AuditLog)
            .order_by(col(AuditLog.created_at).desc(), col(AuditLog.id).desc())
            .limit(8)
        ).all()
    )
    recent_activities = [AuditLogPublic.from_model(r) for r in recent_audits_rows]

    # 6. Distribusi Aset per Kategori & Lokasi
    cat_counts: dict[str, int] = {c: 0 for c in CATEGORIES}
    loc_counts: dict[str, int] = {loc: 0 for loc in LOCATIONS}
    for a in all_assets:
        cat_counts[a.kategori] = cat_counts.get(a.kategori, 0) + 1
        loc_counts[a.lokasi] = loc_counts.get(a.lokasi, 0) + 1

    total_asset_count = max(len(all_assets), 1)
    asset_by_category = [
        {
            "kategori": k,
            "label": k,
            "jumlah": v,
            "total": v,
            "persentase": round((v / total_asset_count) * 100.0, 1)
            if all_assets
            else 0.0,
        }
        for k, v in cat_counts.items()
        if v > 0 or k in ("PC", "Server", "Monitor", "UPS", "Jaringan", "CCTV")
    ]
    asset_by_location = [
        {
            "lokasi": k,
            "label": k,
            "jumlah": v,
            "total": v,
            "persentase": round((v / total_asset_count) * 100.0, 1)
            if all_assets
            else 0.0,
        }
        for k, v in loc_counts.items()
    ]

    # 7. Daftar Peringatan Aktif (Alerts)
    alerts: list[DashboardAlertItem] = []
    if ip_sum["konflik"] > 0:
        alerts.append(
            DashboardAlertItem(
                kategori="Jaringan",
                judul="Konflik IP Terdeteksi",
                pesan=f"Terdapat {ip_sum['konflik']} alokasi IP yang mengalami bentrok aktif",
                tingkat="Kritis",
                jumlah=ip_sum["konflik"],
            )
        )
    if ip_sum["vm_tanpa_host"] > 0:
        alerts.append(
            DashboardAlertItem(
                kategori="Infrastruktur",
                judul="VM Tanpa Host Aktif",
                pesan=f"Terdapat {ip_sum['vm_tanpa_host']} VM yang kehilangan host induk aktif",
                tingkat="Tinggi",
                jumlah=ip_sum["vm_tanpa_host"],
            )
        )
    if mnt_sum["terlambat"] > 0:
        alerts.append(
            DashboardAlertItem(
                kategori="Maintenance",
                judul="Jadwal Maintenance Terlambat",
                pesan=f"Ada {mnt_sum['terlambat']} jadwal pemeliharaan melewati tanggal target",
                tingkat="Tinggi",
                jumlah=mnt_sum["terlambat"],
            )
        )
    if fin_sum["jumlah_jatuh_tempo"] > 0:
        alerts.append(
            DashboardAlertItem(
                kategori="Keuangan",
                judul="Tagihan Melewati Jatuh Tempo",
                pesan=(
                    f"Ada {fin_sum['jumlah_jatuh_tempo']} tagihan belum lunas "
                    "yang melewati jatuh tempo"
                ),
                tingkat="Tinggi",
                jumlah=fin_sum["jumlah_jatuh_tempo"],
            )
        )

    kpi: dict[str, Any] = {
        "total_aset": asset_sum["total"],
        "aset_aktif": asset_sum["aktif"],
        "aset_gudang": asset_sum["gudang"],
        "aset_perbaikan": asset_sum["perbaikan"],
        "aset_rusak": asset_sum["rusak"],
        "total_ip": ip_sum["total_ip"],
        "ip_aktif": ip_sum["aktif"],
        "total_vm": ip_sum["total_vm"],
        "konflik_ip": ip_sum["konflik"],
        "vm_tanpa_host": ip_sum["vm_tanpa_host"],
        "total_watt": power_sum["total_watt"],
        "estimasi_kwh_bulan": power_sum["estimasi_kwh_bulan"],
        "estimasi_biaya_listrik": power_sum["estimasi_biaya_bulan"],
        "total_ups": power_sum["total_ups"],
        "total_va_ups": power_sum["total_va_ups"],
        "persentase_beban_ups": power_sum["persentase_beban_ups"],
        "status_beban_ups": power_sum["status_beban_ups"],
        "total_pengeluaran": fin_sum["total_pengeluaran"],
        "tagihan_belum_lunas": fin_sum["jumlah_belum_lunas"],
        "tagihan_jatuh_tempo": fin_sum["jumlah_jatuh_tempo"],
        "jadwal_maintenance": mnt_sum["total_jadwal"],
        "maintenance_terlambat": mnt_sum["terlambat"],
        "maintenance_selesai": mnt_sum["selesai"],
        "total_kredensial": total_credentials,
        "total_pengguna": total_users,
        "jumlah_peringatan": len(alerts),
    }

    return DashboardResponse(
        kpi=kpi,
        summary=kpi,
        asset_by_category=asset_by_category,
        distribusi_kategori=asset_by_category,
        asset_by_location=asset_by_location,
        distribusi_lokasi=asset_by_location,
        asset_by_status=asset_sum,
        upcoming_maintenance=upcoming_mnt,
        jadwal_maintenance=upcoming_mnt,
        upcoming_bills=upcoming_bills,
        tagihan_mendatang=upcoming_bills,
        recent_activities=recent_activities,
        aktivitas_terbaru=recent_activities,
        alerts=alerts,
        peringatan=alerts,
    )
