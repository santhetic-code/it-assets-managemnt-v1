"""Endpoint CRUD Aset TI, pencarian, filter, dan generator ID otomatis."""

import csv
import io
import re
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import and_, func, or_
from sqlmodel import Session, col, select

from app.api.v1.credentials import can_access_credential, resolve_viewer_context
from app.core.master_data import (
    CATEGORY_TREE,
    get_prefix_for_category,
    normalize_asset_condition,
    normalize_asset_status,
)
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset, AssetLink, AssetMovement, Category
from app.models.base import utcnow
from app.models.credential import Credential
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation
from app.models.maintenance import Maintenance
from app.schemas.asset import (
    FORBIDDEN_FIELDS,
    AssetCreate,
    AssetPageResponse,
    AssetPublic,
    AssetUpdate,
    _clean_serial_number,
    _resolve_category_group,
)
from app.schemas.audit import record_audit_log

router = APIRouter()

ID_PATTERN = re.compile(r"^([A-Z]+)-(\d+)$")


def generate_next_asset_id(session: Session, kategori: str) -> str:
    """Menghasilkan ID aset otomatis berikutnya dengan transaksi lock (termasuk soft-deleted)."""
    prefix = get_prefix_for_category(kategori)
    # Lock baris kategori jika ada untuk mencegah race condition saat 2 user simpan bersamaan
    session.exec(select(Category).where(col(Category.kode) == prefix).with_for_update()).first()

    # Sertakan semua baris (termasuk deleted_at IS NOT NULL) agar ID tidak pernah dipakai ulang
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
        func.lower(Asset.serial_number) == serial_number.lower(),
        col(Asset.deleted_at).is_(None),
    )
    if exclude_asset_id is not None:
        stmt = stmt.where(Asset.id != exclude_asset_id)

    conflict = session.exec(stmt).first()
    if conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Serial number '{serial_number}' sudah terdaftar pada aset {conflict.id_aset}"
            ),
        )


def _build_relations_map(
    session: Session,
    assets: list[Asset],
) -> dict[str, dict[str, Any]]:
    """Membangun peta relasi dua arah (Monitor, UPS, IP, VM, Kredensial) untuk setiap aset."""
    all_active = list(session.exec(select(Asset).where(col(Asset.deleted_at).is_(None))).all())
    by_tag = {a.id_aset: a for a in all_active}

    # 1. Parent-child (Monitor / Komponen terpasang ke PC/Server)
    children_by_parent: dict[str, list[Asset]] = {}
    for a in all_active:
        if a.parent_asset_id:
            children_by_parent.setdefault(a.parent_asset_id, []).append(a)

    # 2. Asset Links (UPS menyuplai Server)
    links = list(session.exec(select(AssetLink)).all())
    ups_by_server: dict[str, list[str]] = {}
    server_by_ups: dict[str, list[str]] = {}
    for lnk in links:
        ups_by_server.setdefault(lnk.linked_asset_id, []).append(lnk.asset_id)
        server_by_ups.setdefault(lnk.asset_id, []).append(lnk.linked_asset_id)

    # Fallback jika asset_links belum terisi namun beban_perangkat ada pada UPS
    servers_by_name = {
        a.nama_aset.strip().upper(): a.id_aset for a in all_active if a.kategori.lower() == "server"
    }
    for a in all_active:
        if a.kategori.lower() == "ups" and a.id_aset not in server_by_ups and a.beban_perangkat:
            b_up = a.beban_perangkat.strip().upper()
            matched_srv_tag = servers_by_name.get(b_up) or servers_by_name.get(f"SERVER {b_up}")
            if not matched_srv_tag:
                for s_name, s_tag in servers_by_name.items():
                    if b_up in s_name or s_name in b_up:
                        matched_srv_tag = s_tag
                        break
            if matched_srv_tag:
                server_by_ups.setdefault(a.id_aset, []).append(matched_srv_tag)
                ups_by_server.setdefault(matched_srv_tag, []).append(a.id_aset)

    # 3. IP Fisik & VM Host
    ips = list(session.exec(select(IPAllocation)).all())
    ip_count_by_asset: dict[str, int] = {}
    vm_count_by_host: dict[str, int] = {}
    for ip_row in ips:
        if ip_row.id_aset and not ip_row.is_vm:
            ip_count_by_asset[ip_row.id_aset] = ip_count_by_asset.get(ip_row.id_aset, 0) + 1
        if ip_row.is_vm and ip_row.id_aset_host:
            vm_count_by_host[ip_row.id_aset_host] = vm_count_by_host.get(ip_row.id_aset_host, 0) + 1

    # 4. Kredensial
    creds = list(session.exec(select(Credential).where(col(Credential.deleted_at).is_(None))).all())
    cred_count_by_asset: dict[str, int] = {}
    for c in creds:
        if c.linked_asset_id:
            cred_count_by_asset[c.linked_asset_id] = (
                cred_count_by_asset.get(c.linked_asset_id, 0) + 1
            )

    result: dict[str, dict[str, Any]] = {}
    for a in assets:
        tag = a.id_aset
        chips: list[str] = []
        counts: dict[str, int] = {}
        monitor_label = ""
        penempatan_label = ""

        # Cek Monitor yang terpasang pada PC ini
        child_mons = [c for c in children_by_parent.get(tag, []) if c.kategori.lower() == "monitor"]
        if child_mons:
            counts["monitor"] = len(child_mons)
            chips.append(f"Monitor {len(child_mons)}")
            m0 = child_mons[0]
            uk = (m0.ukuran_layar or "24").replace('"', "").strip()
            monitor_label = f'{uk}" FHD ({m0.id_aset})'

        # Jika aset ini adalah Monitor yang terpasang di PC induk
        if a.kategori.lower() == "monitor" and a.parent_asset_id:
            counts["pc"] = 1
            chips.append("PC 1")
            penempatan_label = f"Terpasang di {a.parent_asset_id}"

        # Jika aset ini Server yang disuplai UPS
        srv_ups = ups_by_server.get(tag, [])
        if srv_ups:
            counts["ups"] = len(srv_ups)
            chips.append(f"UPS {len(srv_ups)}")

        # Jika aset ini UPS yang menyuplai Server
        ups_srvs = server_by_ups.get(tag, [])
        if ups_srvs:
            counts["server"] = len(ups_srvs)
            chips.append(f"Server {len(ups_srvs)}")
            srv_obj = by_tag.get(ups_srvs[0])
            if srv_obj:
                penempatan_label = f"Menyuplai {srv_obj.nama_aset}"

        # IP, VM, Kredensial
        ip_cnt = ip_count_by_asset.get(tag, 0) or (1 if a.ip_address else 0)
        if ip_cnt > 0:
            counts["ip"] = ip_cnt
            chips.append(f"IP {ip_cnt}")

        vm_cnt = vm_count_by_host.get(tag, 0)
        if vm_cnt > 0:
            counts["vm"] = vm_cnt
            chips.append(f"VM {vm_cnt}")

        cred_cnt = cred_count_by_asset.get(tag, 0)
        if cred_cnt > 0:
            counts["kredensial"] = cred_cnt
            chips.append(f"Kredensial {cred_cnt}")

        result[tag] = {
            "terkait_chips": chips,
            "related_counts": counts,
            "monitor_label": monitor_label,
            "penempatan_label": penempatan_label,
        }
    return result


def _compute_counts_and_summary(
    session: Session,
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Menghitung tab_counts, summary (termasuk 4 kartu Artboard 10), dan category_counts."""
    today = date.today()
    soon_limit = today + timedelta(days=30)

    all_assets = list(session.exec(select(Asset).where(col(Asset.deleted_at).is_(None))).all())
    total_all = len(all_assets)

    tab_counts: dict[str, int] = {"Semua": total_all, "all": total_all}
    summary: dict[str, int] = {
        "total": total_all,
        "aktif": 0,
        "gudang": 0,
        "perbaikan": 0,
        "rusak": 0,
        "perlu_perhatian": 0,
        "garansi_segera_habis": 0,
        "belum_terhubung_pembelian": 0,
    }

    for a in all_assets:
        kat = a.kategori
        tab_counts[kat] = tab_counts.get(kat, 0) + 1
        grp_name = _resolve_category_group(kat)
        tab_counts[grp_name] = tab_counts.get(grp_name, 0) + 1

        st_norm = normalize_asset_status(a.status)
        kd_norm = normalize_asset_condition(a.kondisi)

        if st_norm == "Digunakan":
            summary["aktif"] += 1
        elif st_norm == "Cadangan":
            summary["gudang"] += 1
        elif st_norm == "Dalam Perbaikan":
            summary["perbaikan"] += 1
        elif st_norm in ("Rusak", "Dihapusbukukan"):
            summary["rusak"] += 1

        if st_norm in ("Dalam Perbaikan", "Rusak") or kd_norm in ("Perlu Servis", "Rusak"):
            summary["perlu_perhatian"] += 1

        if a.garansi_sampai and today <= a.garansi_sampai <= soon_limit:
            summary["garansi_segera_habis"] += 1

        if a.purchase_item_id is None:
            summary["belum_terhubung_pembelian"] += 1

    pc_laptop_count = tab_counts.get("PC", 0) + tab_counts.get("Laptop", 0)
    server_count = tab_counts.get("Server", 0)
    monitor_count = tab_counts.get("Monitor", 0)
    ups_count = tab_counts.get("UPS", 0)

    tab_counts["Operasional"] = sum(
        1
        for a in all_assets
        if a.kategori in ("PC", "Laptop") and normalize_asset_status(a.status) != "Cadangan"
    )
    tab_counts["Backup"] = sum(
        1
        for a in all_assets
        if a.kategori in ("PC", "Laptop", "Server")
        and (normalize_asset_status(a.status) == "Cadangan" or "BACKUP" in a.nama_aset.upper())
    )

    category_counts: dict[str, int] = {
        "all": total_all,
        "pc": pc_laptop_count,
        "server": server_count,
        "monitor": monitor_count,
        "ups": ups_count,
        "perangkat-it": tab_counts.get("Perangkat IT", 0),
        "komponen-periferal": tab_counts.get("Komponen & Periferal", 0),
        "jaringan": tab_counts.get("Jaringan", 0),
        "kendaraan": tab_counts.get("Kendaraan", 0),
        "peralatan-kantor": tab_counts.get("Peralatan Kantor", 0),
        "furnitur": tab_counts.get("Furnitur", 0),
        "lainnya": tab_counts.get("Lainnya", 0),
    }

    return tab_counts, summary, category_counts


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
    slug: str | None = Query(default=None),
    category: str | None = Query(default=None),
    group: str | None = Query(default=None),
    tab: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    pengguna: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    kondisi: str | None = Query(default=None),
    kepemilikan: str | None = Query(default=None),
    warranty: str | None = Query(default=None),
    no_purchase: str | int | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="asc"),
    attr_os: str | None = Query(default=None),
    attr_ram: str | None = Query(default=None),
    attr_merk: str | None = Query(default=None),
    attr_ukuran_layar: str | None = Query(default=None),
    attr_resolusi_layar: str | None = Query(default=None),
    attr_konektivitas: str | None = Query(default=None),
) -> AssetPageResponse:
    """Mengambil daftar aset dari tabel induk assets dengan filter server-side & relasi."""
    stmt = select(Asset).where(col(Asset.deleted_at).is_(None))

    slug_clean = (category or slug or "").strip().lower()
    if slug_clean == "pc":
        stmt = stmt.where(col(Asset.kategori).in_(["PC", "Laptop"]))
    elif slug_clean == "server":
        stmt = stmt.where(func.lower(Asset.kategori) == "server")
    elif slug_clean == "monitor":
        stmt = stmt.where(func.lower(Asset.kategori) == "monitor")
    elif slug_clean == "ups":
        stmt = stmt.where(func.lower(Asset.kategori) == "ups")
    elif slug_clean in (
        "perangkat-it",
        "komponen-periferal",
        "jaringan",
        "kendaraan",
        "peralatan-kantor",
        "furnitur",
        "lainnya",
    ):
        grp_obj = next((g for g in CATEGORY_TREE if g["slug"] == slug_clean), None)
        if grp_obj:
            sub_names = [s["nama"] for s in grp_obj.get("children", [])]
            stmt = stmt.where(col(Asset.kategori).in_(sub_names))

    if group and group.strip().lower() not in ("semua", "all", ""):
        grp_clean = group.strip().lower()
        grp_obj = next(
            (g for g in CATEGORY_TREE if g["slug"] == grp_clean or g["nama"].lower() == grp_clean),
            None,
        )
        if grp_obj:
            sub_names = [s["nama"] for s in grp_obj.get("children", [])]
            stmt = stmt.where(col(Asset.kategori).in_(sub_names))

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
                col(Asset.processor).ilike(pattern),
                col(Asset.os).ilike(pattern),
            )
        )

    if kategori and kategori.strip().lower() not in ("semua", "all", ""):
        kat_clean = kategori.strip().lower()
        if kat_clean in ("pc", "pc & laptop"):
            stmt = stmt.where(col(Asset.kategori).in_(["PC", "Laptop"]))
        else:
            stmt = stmt.where(func.lower(Asset.kategori) == kat_clean)

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(func.lower(Asset.lokasi) == lokasi.strip().lower())

    if pengguna and pengguna.strip().lower() not in ("semua", "all", ""):
        stmt = stmt.where(col(Asset.penanggung_jawab).ilike(f"%{pengguna.strip()}%"))

    if str(no_purchase or "").strip().lower() in ("1", "true", "yes"):
        stmt = stmt.where(col(Asset.purchase_item_id).is_(None))

    if warranty and warranty.strip().lower() == "expiring":
        today = date.today()
        stmt = stmt.where(
            col(Asset.garansi_sampai).is_not(None),
            col(Asset.garansi_sampai) >= today,
            col(Asset.garansi_sampai) <= today + timedelta(days=30),
        )

    all_matching_rows = list(session.exec(stmt.order_by(col(Asset.id_aset).asc())).all())
    rel_map = _build_relations_map(session, all_matching_rows)
    public_items = [AssetPublic.from_asset(r, rel_map.get(r.id_aset)) for r in all_matching_rows]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        if st_clean in ("attention", "perlu_perhatian", "rusak,perbaikan"):
            public_items = [
                it
                for it in public_items
                if it.status in ("Dalam Perbaikan", "Rusak")
                or it.kondisi in ("Perlu Servis", "Rusak")
            ]
        else:
            norm_target = normalize_asset_status(st_clean)
            public_items = [it for it in public_items if it.status.lower() == norm_target.lower()]

    if kondisi and kondisi.strip().lower() not in ("semua", "all", ""):
        kd_target = normalize_asset_condition(kondisi.strip())
        public_items = [it for it in public_items if it.kondisi.lower() == kd_target.lower()]

    tab_counts, summary, category_counts = _compute_counts_and_summary(session)

    # Filter kepemilikan & atribut spesifik kategori
    if kepemilikan and kepemilikan.strip().lower() not in ("semua", "all", ""):
        kep_low = kepemilikan.strip().lower()
        public_items = [
            it for it in public_items if (it.kepemilikan or "").strip().lower() == kep_low
        ]

    if attr_os and attr_os.strip().lower() not in ("semua", "all", ""):
        v_low = attr_os.strip().lower()
        public_items = [it for it in public_items if (it.os or "").strip().lower() == v_low]
    if attr_ram and attr_ram.strip().lower() not in ("semua", "all", ""):
        v_low = attr_ram.strip().lower()
        public_items = [it for it in public_items if (it.ram or "").strip().lower() == v_low]
    if attr_merk and attr_merk.strip().lower() not in ("semua", "all", ""):
        v_low = attr_merk.strip().lower()
        public_items = [it for it in public_items if (it.merk or "").strip().lower() == v_low]
    if attr_ukuran_layar and attr_ukuran_layar.strip().lower() not in ("semua", "all", ""):
        v_low = attr_ukuran_layar.strip().lower().replace('"', "")
        public_items = [
            it
            for it in public_items
            if (it.ukuran_layar or "").strip().lower().replace('"', "") == v_low
        ]
    if attr_resolusi_layar and attr_resolusi_layar.strip().lower() not in ("semua", "all", ""):
        v_low = attr_resolusi_layar.strip().lower()
        public_items = [
            it for it in public_items if (it.resolusi_layar or "").strip().lower() == v_low
        ]
    if attr_konektivitas and attr_konektivitas.strip().lower() not in ("semua", "all", ""):
        v_low = attr_konektivitas.strip().lower()
        public_items = [
            it for it in public_items if any(v_low in k.lower() for k in it.konektivitas)
        ]

    if sort_by and sort_by.strip():
        s_key = sort_by.strip()
        rev = (sort_dir or "asc").strip().lower() == "desc"
        public_items.sort(
            key=lambda it: str(getattr(it, s_key, "") or "").lower(),
            reverse=rev,
        )

    total = len(public_items)
    paged_items = public_items[page_params.offset : page_params.offset + page_params.page_size]

    return AssetPageResponse(
        items=paged_items,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        category_counts=category_counts,
        group_counts={
            "all": summary["total"],
            "perangkat-it": category_counts.get("perangkat-it", 0),
            "komponen-periferal": category_counts.get("komponen-periferal", 0),
            "jaringan": category_counts.get("jaringan", 0),
            "kendaraan": category_counts.get("kendaraan", 0),
            "peralatan-kantor": category_counts.get("peralatan-kantor", 0),
            "furnitur": category_counts.get("furnitur", 0),
            "lainnya": category_counts.get("lainnya", 0),
        },
        subcategory_counts={
            "pc": category_counts.get("pc", 0),
            "server": category_counts.get("server", 0),
            "monitor": category_counts.get("monitor", 0),
            "ups": category_counts.get("ups", 0),
        },
    )


# Status Stock Opname in-memory / session-backed
_STOCK_OPNAME_STATE: dict[str, dict[str, Any]] = {}


def _compute_depreciation_info(asset: Asset) -> dict[str, Any]:
    """Menghitung depresiasi garis lurus (4 tahun / 48 bulan) dan nilai buku saat ini (Seksi 14)."""
    harga = asset.nilai_perolehan or 0
    tgl_awal = asset.tanggal_perolehan or asset.tanggal_masuk
    if harga <= 0 or tgl_awal is None:
        return {
            "nilai_perolehan": harga,
            "umur_ekonomis_bulan": 48,
            "bulan_berjalan": 0,
            "akumulasi_depresiasi": 0,
            "nilai_buku": harga,
            "persentase_sisa": 100.0 if harga > 0 else 0.0,
        }
    today = date.today()
    months_elapsed = max(0, (today.year - tgl_awal.year) * 12 + (today.month - tgl_awal.month))
    useful_months = 48
    dep_per_month = harga / useful_months
    accumulated = min(harga, round(dep_per_month * min(months_elapsed, useful_months)))
    book_value = max(0, harga - accumulated)
    pct_left = round((book_value / harga) * 100.0, 1) if harga > 0 else 0.0
    return {
        "nilai_perolehan": harga,
        "umur_ekonomis_bulan": useful_months,
        "bulan_berjalan": months_elapsed,
        "akumulasi_depresiasi": accumulated,
        "nilai_buku": book_value,
        "persentase_sisa": pct_left,
    }


@router.get("/check-duplicate")
def check_potential_duplicate_asset(
    session: SessionDep,
    _: CurrentUserDep,
    nama_aset: str = Query(default=""),
    kategori: str = Query(default=""),
    pengguna: str = Query(default=""),
    exclude_id: str = Query(default=""),
) -> dict[str, Any]:
    """Mendeteksi kemungkinan duplikat jika nama, kategori, dan pengguna mirip (Seksi 13)."""
    nama_clean = nama_aset.strip().lower()
    kat_clean = kategori.strip().lower()
    user_clean = pengguna.strip().lower()
    if not nama_clean:
        return {"has_duplicate": False, "matches": [], "warning": ""}

    candidates = list(
        session.exec(
            select(Asset).where(
                col(Asset.deleted_at).is_(None),
                func.lower(Asset.kategori) == kat_clean if kat_clean else True,
            )
        ).all()
    )
    matches: list[dict[str, str]] = []
    for c in candidates:
        if exclude_id and c.id_aset.lower() == exclude_id.strip().lower():
            continue
        c_nama = c.nama_aset.strip().lower()
        c_user = (c.pemakai_text or c.penanggung_jawab or "").strip().lower()
        if c_nama == nama_clean or (
            nama_clean in c_nama and user_clean and user_clean in c_user
        ):
            matches.append(
                {
                    "id_aset": c.id_aset,
                    "nama_aset": c.nama_aset,
                    "pengguna": c.pemakai_text or c.penanggung_jawab or "—",
                    "lokasi": c.lokasi,
                }
            )
    warn = (
        f"Kemungkinan duplikat dengan {matches[0]['id_aset']} ({matches[0]['nama_aset']})"
        if matches
        else ""
    )
    return {"has_duplicate": len(matches) > 0, "matches": matches[:5], "warning": warn}


@router.get("/export/csv")
def export_assets_csv(
    session: SessionDep,
    _: CurrentUserDep,
    category: str | None = Query(default=None),
    group: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
) -> Response:
    """Export daftar aset sesuai filter aktif ke format CSV (Seksi 7 & 14)."""
    stmt = select(Asset).where(col(Asset.deleted_at).is_(None))
    if category and category.strip().lower() not in ("", "all", "semua"):
        c_low = category.strip().lower()
        if c_low == "pc":
            stmt = stmt.where(col(Asset.kategori).in_(["PC", "Laptop"]))
        else:
            stmt = stmt.where(func.lower(Asset.kategori) == c_low)
    if status_filter and status_filter.strip().lower() not in ("", "all", "semua"):
        st_norm = normalize_asset_status(status_filter)
        stmt = stmt.where(func.lower(Asset.status) == st_norm.lower())
    if search and search.strip():
        pat = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                col(Asset.id_aset).ilike(pat),
                col(Asset.nama_aset).ilike(pat),
                col(Asset.penanggung_jawab).ilike(pat),
            )
        )

    rows = list(session.exec(stmt.order_by(col(Asset.id_aset).asc())).all())
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "Aset ID",
            "Nama",
            "Kategori",
            "Pengguna / Penempatan",
            "Lokasi",
            "Status",
            "Kondisi",
            "Serial Number",
            "Tanggal Perolehan",
            "Nilai Perolehan",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.id_aset,
                r.nama_aset,
                r.kategori,
                r.pemakai_text or r.penanggung_jawab or "—",
                r.lokasi,
                normalize_asset_status(r.status),
                normalize_asset_condition(r.kondisi),
                r.serial_number or "",
                (r.tanggal_perolehan or r.tanggal_masuk or ""),
                r.nilai_perolehan or "",
            ]
        )
    return Response(
        content=buf.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="Export_Aset_ITAM_Pro.csv"'},
    )


@router.get("/stock-opname")
def get_stock_opname_report(
    session: SessionDep,
    _: CurrentUserDep,
    lokasi: str | None = Query(default=None),
) -> dict[str, Any]:
    """Mengambil laporan Stock Opname & selisih hasil pindai QR (Seksi 14 & 18)."""
    stmt = select(Asset).where(col(Asset.deleted_at).is_(None))
    if lokasi and lokasi.strip().lower() not in ("", "semua", "all"):
        stmt = stmt.where(func.lower(Asset.lokasi) == lokasi.strip().lower())
    assets = list(session.exec(stmt.order_by(col(Asset.id_aset).asc())).all())

    items: list[dict[str, Any]] = []
    found_cnt = 0
    missing_cnt = 0
    unscanned_cnt = 0

    for a in assets:
        rec = _STOCK_OPNAME_STATE.get(a.id_aset.upper())
        st_scan = rec["status"] if rec else "Belum dipindai"
        if st_scan == "Ditemukan":
            found_cnt += 1
        elif st_scan == "Tidak ditemukan":
            missing_cnt += 1
        else:
            unscanned_cnt += 1
        items.append(
            {
                "id_aset": a.id_aset,
                "nama_aset": a.nama_aset,
                "kategori": a.kategori,
                "lokasi": a.lokasi,
                "pengguna": a.pemakai_text or a.penanggung_jawab or "—",
                "opname_status": st_scan,
                "scanned_at": rec["scanned_at"] if rec else "—",
                "catatan": rec["catatan"] if rec else "",
            }
        )

    return {
        "summary": {
            "total_terdaftar": len(assets),
            "ditemukan": found_cnt,
            "tidak_ditemukan": missing_cnt,
            "belum_dipindai": unscanned_cnt,
            "selisih": missing_cnt + unscanned_cnt,
        },
        "items": items,
    }


@router.post("/stock-opname/scan")
def scan_stock_opname_qr(
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Memproses pindai QR (URL detail aset atau Aset ID) pada Stock Opname (Seksi 9 & 14)."""
    raw_input = str(payload.get("qr_code") or payload.get("id_aset") or "").strip()
    if "/assets/" in raw_input:
        raw_input = raw_input.split("/assets/", 1)[1].split("?")[0].strip("/")
    clean_tag = raw_input.upper()
    if not clean_tag:
        raise HTTPException(status_code=422, detail="Kode QR atau Aset ID tidak boleh kosong")

    asset = session.exec(
        select(Asset).where(
            func.upper(Asset.id_aset) == clean_tag,
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aset '{clean_tag}' tidak ditemukan di daftar induk",
        )

    opname_status = str(payload.get("status") or "Ditemukan").strip()
    if opname_status not in ("Ditemukan", "Tidak ditemukan"):
        opname_status = "Ditemukan"
    catatan = str(payload.get("catatan") or "").strip()

    _STOCK_OPNAME_STATE[asset.id_aset.upper()] = {
        "status": opname_status,
        "scanned_at": date.today().isoformat(),
        "scanned_by": current_user.username,
        "catatan": catatan,
    }
    return {
        "status": "ok",
        "id_aset": asset.id_aset,
        "nama_aset": asset.nama_aset,
        "opname_status": opname_status,
    }


@router.post("/import-preview")
def preview_assets_import(
    payload: dict[str, Any],
    session: SessionDep,
    _: EditorUserDep,
) -> dict[str, Any]:
    """Validasi CSV/baris impor aset lama dengan laporan baris valid & error (Seksi 14)."""
    csv_text = str(payload.get("csv_text") or "").strip()
    if not csv_text:
        return {
            "valid_count": 0,
            "error_count": 1,
            "valid_rows": [],
            "errors": [{"row": 1, "reason": "Data CSV kosong"}],
        }

    first_line = csv_text.split("\n", 1)[0]
    delim = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = list(csv.reader(io.StringIO(csv_text), delimiter=delim))
    if len(reader) <= 1:
        return {
            "valid_count": 0,
            "error_count": 1,
            "valid_rows": [],
            "errors": [{"row": 1, "reason": "Tidak ada baris data setelah header"}],
        }

    existing_sns = {
        (sn or "").lower()
        for sn in session.exec(
            select(Asset.serial_number).where(col(Asset.serial_number).is_not(None))
        ).all()
        if sn
    }
    seen_sns: set[str] = set()
    valid_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, cols in enumerate(reader[1:], start=2):
        padded = [*cols, "", "", "", "", "", "", ""][:7]
        nama_val, kat_val, user_val, lok_val, st_val, kd_val, sn_val = [c.strip() for c in padded]
        if not any([nama_val, kat_val]):
            continue
        if not nama_val:
            errors.append({"row": idx, "nama": "—", "reason": "Nama aset wajib diisi"})
            continue
        if not kat_val:
            errors.append({"row": idx, "nama": nama_val, "reason": "Kategori wajib diisi"})
            continue
        if sn_val and sn_val not in ("-", "—"):
            if sn_val.lower() in existing_sns or sn_val.lower() in seen_sns:
                errors.append(
                    {"row": idx, "nama": nama_val, "reason": f"Serial number '{sn_val}' duplikat"}
                )
                continue
            seen_sns.add(sn_val.lower())

        valid_rows.append(
            {
                "row": idx,
                "nama_aset": nama_val,
                "kategori": kat_val,
                "penanggung_jawab": user_val or "Operasional",
                "lokasi": lok_val or "Head Office (Office Blok 14)",
                "status": normalize_asset_status(st_val or "Digunakan"),
                "kondisi": normalize_asset_condition(kd_val or "Baik"),
                "serial_number": sn_val if sn_val not in ("", "-", "—") else None,
            }
        )

    return {
        "valid_count": len(valid_rows),
        "error_count": len(errors),
        "valid_rows": valid_rows,
        "errors": errors,
    }


@router.post("/import-commit")
def commit_assets_import(
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Menyimpan seluruh baris valid hasil import aset lama dalam satu transaksi (Seksi 13 & 14)."""
    rows = payload.get("valid_rows") or []
    if not isinstance(rows, list) or not rows:
        raise HTTPException(status_code=400, detail="Tidak ada baris valid untuk diimpor")

    created_tags: list[str] = []
    for r in rows:
        kat = str(r.get("kategori") or "PC").strip()
        new_tag = generate_next_asset_id(session, kat)
        nama_v = str(r.get("nama_aset") or new_tag).strip()
        user_v = str(r.get("penanggung_jawab") or "Operasional").strip()
        lok_v = str(r.get("lokasi") or "Head Office (Office Blok 14)").strip()
        asset = Asset(
            id_aset=new_tag,
            asset_tag=new_tag,
            nama_aset=nama_v,
            nama=nama_v,
            kategori=kat,
            serial_number=r.get("serial_number") or None,
            lokasi=lok_v,
            penanggung_jawab=user_v,
            pemakai_text=user_v,
            status=normalize_asset_status(r.get("status")),
            kondisi=normalize_asset_condition(r.get("kondisi")),
            tanggal_masuk=date.today(),
            tanggal_perolehan=date.today(),
            tracking="unit",
            qty=1,
            created_by=current_user.username,
        )
        session.add(asset)
        session.flush()
        created_tags.append(new_tag)

    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=getattr(current_user, "full_name", current_user.username),
        role=current_user.role,
        aksi="Import Aset Lama",
        modul="Inventory",
        target_id="IMPORT-ASET",
        detail=f"Berhasil mengimpor {len(created_tags)} aset baru",
        level_risiko="Sedang",
    )
    session.commit()
    return {"status": "ok", "imported_count": len(created_tags), "created_assets": created_tags}


@router.post("/merge")
def merge_duplicate_assets(
    payload: dict[str, Any],
    session: SessionDep,
    current_user: AdminUserDep,
) -> dict[str, Any]:
    """Menggabungkan aset ganda (source -> target) dalam satu transaksi atomik (Seksi 13)."""
    src_tag = str(payload.get("source_id_aset") or "").strip().upper()
    tgt_tag = str(payload.get("target_id_aset") or "").strip().upper()
    if not src_tag or not tgt_tag or src_tag == tgt_tag:
        raise HTTPException(
            status_code=422,
            detail="Pilih aset duplikat (sumber) dan aset induk (tujuan) yang berbeda",
        )

    source = session.exec(
        select(Asset)
        .where(func.upper(Asset.id_aset) == src_tag, col(Asset.deleted_at).is_(None))
        .with_for_update()
    ).first()
    target = session.exec(
        select(Asset)
        .where(func.upper(Asset.id_aset) == tgt_tag, col(Asset.deleted_at).is_(None))
        .with_for_update()
    ).first()
    if source is None or target is None:
        raise HTTPException(status_code=404, detail="Aset sumber atau tujuan tidak ditemukan")

    # 1. Pindahkan child assets (Monitor & Komponen)
    for child in session.exec(
        select(Asset).where(col(Asset.parent_asset_id) == source.id_aset)
    ).all():
        child.parent_asset_id = target.id_aset
        child.pemakai_text = f"Terpasang di {target.id_aset}"
        child.penanggung_jawab = child.pemakai_text
        session.add(child)

    # 2. Pindahkan AssetLink
    for lnk in session.exec(
        select(AssetLink).where(col(AssetLink.asset_id) == source.id_aset)
    ).all():
        lnk.asset_id = target.id_aset
        session.add(lnk)
    for lnk2 in session.exec(
        select(AssetLink).where(col(AssetLink.linked_asset_id) == source.id_aset)
    ).all():
        lnk2.linked_asset_id = target.id_aset
        session.add(lnk2)

    # 3. Pindahkan IPAllocation, Credential, & Maintenance
    for ip_r in session.exec(
        select(IPAllocation).where(col(IPAllocation.id_aset) == source.id_aset)
    ).all():
        ip_r.id_aset = target.id_aset
        session.add(ip_r)
    for vm_r in session.exec(
        select(IPAllocation).where(col(IPAllocation.id_aset_host) == source.id_aset)
    ).all():
        vm_r.id_aset_host = target.id_aset
        session.add(vm_r)
    for crd in session.exec(
        select(Credential).where(col(Credential.linked_asset_id) == source.id_aset)
    ).all():
        crd.linked_asset_id = target.id_aset
        session.add(crd)
    for mnt in session.exec(
        select(Maintenance).where(col(Maintenance.id_aset) == source.id_aset)
    ).all():
        mnt.id_aset = target.id_aset
        session.add(mnt)

    # 4. Catat di AssetMovement & Soft-delete source
    source.deleted_at = utcnow()
    source.status = "Dihapusbukukan"
    source.catatan = f"{source.catatan or ''} [Digabungkan ke {target.id_aset}]".strip()
    session.add(source)

    session.add(
        AssetMovement(
            asset_id=target.id_aset,
            jenis="ubah_status",
            dari=source.id_aset,
            ke=target.id_aset,
            alasan="Gabungkan aset duplikat",
            catatan=f"Seluruh relasi dari {source.id_aset} digabung ke {target.id_aset}",
            tanggal=date.today(),
            oleh=current_user.username,
        )
    )
    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=getattr(current_user, "full_name", current_user.username),
        role=current_user.role,
        aksi="Gabungkan Aset",
        modul="Inventory",
        target_id=target.id_aset,
        detail=f"Menggabungkan aset duplikat {source.id_aset} ke {target.id_aset}",
        level_risiko="Tinggi",
    )
    session.commit()
    return {"status": "ok", "merged_from": source.id_aset, "merged_into": target.id_aset}


@router.get("/{id_aset}", response_model=AssetPublic)
def get_asset_detail(
    id_aset: str,
    session: SessionDep,
    _: CurrentUserDep,
) -> AssetPublic:
    """Mengambil detail satu aset berdasarkan id_aset."""
    asset = session.exec(
        select(Asset).where(
            func.lower(Asset.id_aset) == id_aset.strip().lower(),
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )
    rel_map = _build_relations_map(session, [asset])
    return AssetPublic.from_asset(asset, rel_map.get(asset.id_aset))


COMPONENT_CATEGORIES = {"ram", "ssd", "hdd", "ssd/hdd", "vga", "psu"}


def _parse_capacity_gb(raw_val: Any) -> int:
    """Mengekstrak angka kapasitas GB dari angka atau teks (mis. '512 GB', '1 TB' -> 1024)."""
    if isinstance(raw_val, (int, float)):
        return int(raw_val)
    text = str(raw_val or "").strip().upper()
    if not text:
        return 0
    m_tb = re.search(r"(\d+(?:[.,]\d+)?)\s*TB", text)
    if m_tb:
        return int(float(m_tb.group(1).replace(",", ".")) * 1024)
    m_gb = re.search(r"(\d+)\s*GB", text)
    if m_gb:
        return int(m_gb.group(1))
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def _compute_pc_component_totals(
    session: Session,
    parent_tag: str,
) -> dict[str, Any]:
    """Menghitung total RAM (GB & modul) dan Storage (GB & disk) dari komponen terpasang."""
    children = list(
        session.exec(
            select(Asset).where(
                func.upper(Asset.parent_asset_id) == parent_tag.strip().upper(),
                col(Asset.deleted_at).is_(None),
            )
        ).all()
    )
    comp_children = [c for c in children if c.kategori.strip().lower() in COMPONENT_CATEGORIES]

    ram_gb = 0
    ram_modules = 0
    ram_types: set[str] = set()
    storage_gb = 0
    storage_disks = 0
    storage_labels: list[str] = []

    for c in comp_children:
        kat_low = c.kategori.strip().lower()
        sp = {**(c.extra_specs or {}), **(c.specs or {})}
        cap = _parse_capacity_gb(sp.get("kapasitas_gb") or c.ram or c.storage or c.nama_aset)
        tipe = str(sp.get("tipe") or c.model or "").strip().upper()
        if kat_low == "ram":
            ram_modules += 1
            ram_gb += cap or 8
            if tipe:
                ram_types.add(tipe)
        elif kat_low in ("ssd", "hdd", "ssd/hdd"):
            storage_disks += 1
            storage_gb += cap or 256
            st_type = tipe or ("NVMe" if "NVME" in c.nama_aset.upper() else "SSD")
            storage_labels.append(f"{st_type} {cap or 256}GB")

    ram_type_str = "/".join(sorted(ram_types)) or "DDR4"
    return {
        "is_tracked": len(comp_children) > 0,
        "ram_total_gb": ram_gb,
        "ram_modules": ram_modules,
        "ram_summary_chip": f"RAM total {ram_gb} GB · {ram_modules} modul",
        "ram_text": f"{ram_gb}GB {ram_type_str}" if ram_modules > 0 else "",
        "storage_total_gb": storage_gb,
        "storage_disks": storage_disks,
        "storage_summary_chip": f"Storage total {storage_gb} GB · {storage_disks} disk",
        "storage_text": ", ".join(storage_labels) if storage_disks > 0 else "",
        "components": comp_children,
    }


def _recalculate_parent_component_totals(session: Session, parent_tag: str | None) -> None:
    """Sinkronkan field teks RAM & Storage pada PC/Server induk setiap ada mutasi komponen."""
    if not parent_tag:
        return
    parent = session.exec(
        select(Asset).where(
            func.upper(Asset.id_aset) == parent_tag.strip().upper(),
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if parent is None:
        return

    totals = _compute_pc_component_totals(session, parent.id_aset)
    extra = dict(parent.extra_specs or {})
    specs = dict(parent.specs or {})
    extra["component_tracked"] = totals["is_tracked"]
    specs["component_tracked"] = totals["is_tracked"]

    if totals["ram_modules"] > 0:
        parent.ram = totals["ram_text"]
        extra["ram"] = totals["ram_text"]
        specs["ram"] = totals["ram_text"]
    if totals["storage_disks"] > 0:
        parent.storage = totals["storage_text"]
        extra["hdd_ssd"] = totals["storage_text"]
        specs["storage"] = totals["storage_text"]

    parent.extra_specs = extra
    parent.specs = specs
    parent.updated_at = utcnow()
    session.add(parent)


def format_date_id(dt_or_str: Any) -> str:
    """Format tanggal ke 'Mon YYYY' mis. 'Nov 2026'."""
    bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
    if isinstance(dt_or_str, str):
        try:
            d = date.fromisoformat(dt_or_str[:10])
        except Exception:
            return dt_or_str
    elif isinstance(dt_or_str, date):
        d = dt_or_str
    else:
        return str(dt_or_str)
    return f"{bulan[d.month - 1]} {d.year}"


def _format_component_row(c: Asset) -> dict[str, Any]:
    sp = {**(c.extra_specs or {}), **(c.specs or {})}
    kat_up = c.kategori.upper()
    cap = _parse_capacity_gb(sp.get("kapasitas_gb") or c.ram or c.storage or c.nama_aset)
    tipe = str(sp.get("tipe") or ("DDR4" if kat_up == "RAM" else "NVMe")).strip()
    slot = str(sp.get("slot") or ("DIMM 1" if kat_up == "RAM" else "M.2")).strip()
    data_status = str(
        sp.get("data_status") or ("Kosong" if kat_up == "RAM" else "Siap pakai")
    ).strip()
    dipasang_sejak = str(sp.get("dipasang_sejak") or "Jun 2025")
    spec_label = f"{tipe} · {cap} GB" if cap > 0 else (c.model or c.nama_aset)
    return {
        "id_aset": c.id_aset,
        "komponen": "SSD" if kat_up in ("SSD", "HDD", "SSD/HDD") else kat_up,
        "nama_aset": c.nama_aset,
        "spesifikasi": spec_label,
        "tipe": tipe,
        "kapasitas_gb": cap,
        "slot": slot,
        "dipasang_sejak": dipasang_sejak,
        "lokasi": f"{c.status} · {c.lokasi}",
        "status": c.status,
        "parent_asset_id": c.parent_asset_id or "",
        "data_status": data_status,
        "catatan_chip": (
            "Berisi data, belum di-wipe"
            if data_status.lower() == "berisi data"
            else "Siap pakai"
        ),
        "needs_wipe": data_status.lower() == "berisi data",
    }


@router.get("/{id_aset}/full-detail")
def get_asset_full_detail(
    id_aset: str,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    """Mengambil detail lengkap aset beserta seluruh relasi lintas modul (Artboard 11)."""
    clean_tag = id_aset.strip().upper()
    asset = session.exec(
        select(Asset).where(
            func.upper(Asset.id_aset) == clean_tag,
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )

    rel_map = _build_relations_map(session, [asset])
    pub = AssetPublic.from_asset(asset, rel_map.get(asset.id_aset))

    # 1. Monitor terpasang (jika aset ini PC/Server) atau PC induk (jika aset ini Monitor)
    child_monitors = list(
        session.exec(
            select(Asset).where(
                col(Asset.parent_asset_id) == asset.id_aset,
                func.lower(Asset.kategori) == "monitor",
                col(Asset.deleted_at).is_(None),
            )
        ).all()
    )
    parent_asset = (
        session.exec(
            select(Asset).where(
                col(Asset.id_aset) == asset.parent_asset_id,
                col(Asset.deleted_at).is_(None),
            )
        ).first()
        if asset.parent_asset_id
        else None
    )

    # 2. Relasi UPS <-> Server dari asset_links
    ups_links = list(
        session.exec(
            select(AssetLink).where(
                or_(
                    col(AssetLink.asset_id) == asset.id_aset,
                    col(AssetLink.linked_asset_id) == asset.id_aset,
                )
            )
        ).all()
    )
    linked_tags = {
        lnk.linked_asset_id if lnk.asset_id == asset.id_aset else lnk.asset_id for lnk in ups_links
    }
    linked_power_assets = (
        list(
            session.exec(
                select(Asset).where(
                    col(Asset.id_aset).in_(linked_tags),
                    col(Asset.deleted_at).is_(None),
                )
            ).all()
        )
        if linked_tags
        else []
    )

    # 3. Jaringan (IP Fisik & VM yang berjalan di host ini)
    ip_entries = list(
        session.exec(
            select(IPAllocation).where(
                or_(
                    func.upper(IPAllocation.id_aset) == asset.id_aset.upper(),
                    func.upper(IPAllocation.id_aset_host) == asset.id_aset.upper(),
                )
            )
        ).all()
    )

    # 4. Kredensial terkait (difilter sesuai hak akses pengguna saat ini - Seksi 7 & 9)
    v_ctx = resolve_viewer_context(session, current_user)
    raw_creds = list(
        session.exec(
            select(Credential).where(
                col(Credential.deleted_at).is_(None),
                or_(
                    func.upper(Credential.linked_asset_id) == asset.id_aset.upper(),
                    func.upper(Credential.id_aset) == asset.id_aset.upper(),
                ),
            )
        ).all()
    )
    accessible_creds = [
        {
            "kode_kredensial": c.kode_kredensial,
            "nama": c.nama or c.nama_layanan,
            "jenis": c.jenis_kredensial,
            "username": c.username,
        }
        for c in raw_creds
        if can_access_credential(session, v_ctx, c, action="view")
    ]

    # 5. Pembelian & Garansi
    purchase_row = None
    if asset.purchase_item_id:
        purchase_row = session.get(Purchase, asset.purchase_item_id)
    if purchase_row is None:
        purchase_row = session.exec(
            select(Purchase).where(func.upper(Purchase.id_aset) == asset.id_aset.upper())
        ).first()

    # 6. Jadwal & Riwayat Maintenance
    maintenances = list(
        session.exec(
            select(Maintenance)
            .where(func.upper(Maintenance.id_aset) == asset.id_aset.upper())
            .order_by(col(Maintenance.tanggal_jadwal).desc())
        ).all()
    )

    # 7. Riwayat Mutasi & Serah Terima (asset_movements)
    movements = list(
        session.exec(
            select(AssetMovement)
            .where(func.upper(AssetMovement.asset_id) == asset.id_aset.upper())
            .order_by(col(AssetMovement.tanggal).desc(), col(AssetMovement.id).desc())
        ).all()
    )

    # 8. Komponen Terpasang & Stok Komponen Cadangan (Seksi 6 & Artboard 12)
    comp_totals = _compute_pc_component_totals(session, asset.id_aset)
    installed_components = [_format_component_row(c) for c in comp_totals["components"]]

    spare_rows = list(
        session.exec(
            select(Asset).where(
                col(Asset.parent_asset_id).is_(None),
                func.lower(Asset.kategori).in_(
                    ["ram", "ssd", "hdd", "ssd/hdd", "vga", "psu"]
                ),
                func.lower(Asset.status).in_(["cadangan", "backup", "gudang"]),
                col(Asset.deleted_at).is_(None),
            )
        ).all()
    )
    spare_components = [_format_component_row(s) for s in spare_rows]

    pc_targets = [
        f"{p.id_aset} · {p.nama_aset}"
        for p in session.exec(
            select(Asset)
            .where(
                func.lower(Asset.kategori).in_(["pc", "laptop", "server"]),
                col(Asset.id_aset) != asset.id_aset,
                col(Asset.deleted_at).is_(None),
            )
            .order_by(col(Asset.id_aset).asc())
        ).all()
    ]

    return {
        "asset": pub,
        "relations": {
            "monitors": [
                {
                    "id_aset": m.id_aset,
                    "nama_aset": m.nama_aset,
                    "summary": (
                        f"{m.id_aset} · {m.nama_aset} · "
                        f'{(m.ukuran_layar or "24").replace('"', "")}" FHD'
                    ),
                }
                for m in child_monitors
            ],
            "parent_asset": (
                {
                    "id_aset": parent_asset.id_aset,
                    "nama_aset": parent_asset.nama_aset,
                    "kategori": parent_asset.kategori,
                }
                if parent_asset
                else None
            ),
            "power_links": [
                {
                    "id_aset": p.id_aset,
                    "nama_aset": p.nama_aset,
                    "kategori": p.kategori,
                    "summary": f"{p.id_aset} · {p.nama_aset}",
                }
                for p in linked_power_assets
            ],
            "ips": [
                {
                    "id": ip.id,
                    "ip_address": ip.ip_address,
                    "nama_perangkat": ip.nama_perangkat,
                    "is_vm": ip.is_vm,
                    "status": ip.status,
                    "summary": f"{ip.ip_address} · {ip.status}",
                }
                for ip in ip_entries
            ],
            "credentials": accessible_creds,
            "credentials_summary": (
                f"{len(accessible_creds)} entri "
                f"({', '.join(sorted({c['jenis'] for c in accessible_creds}))}) · "
                "sesuai hak akses Anda"
                if accessible_creds
                else "Belum ada kredensial tertaut"
            ),
            "purchase": (
                {
                    "kode_pembelian": purchase_row.kode_pembelian,
                    "nomor_invoice": purchase_row.nomor_invoice,
                    "nama_item": purchase_row.nama_item,
                    "vendor": purchase_row.vendor,
                    "harga_satuan": purchase_row.harga_satuan,
                    "tanggal_beli": (
                        purchase_row.tanggal_beli.isoformat() if purchase_row.tanggal_beli else ""
                    ),
                }
                if purchase_row
                else None
            ),
            "maintenances": [
                {
                    "kode_maintenance": m.kode_maintenance,
                    "judul": m.judul,
                    "jenis_maintenance": m.jenis_maintenance,
                    "tanggal_jadwal": m.tanggal_jadwal.isoformat() if m.tanggal_jadwal else "",
                    "status": m.status,
                    "teknisi": m.teknisi,
                }
                for m in maintenances
            ],
        },
        "movements": [
            {
                "id": mv.id,
                "jenis": mv.jenis,
                "dari": mv.dari,
                "ke": mv.ke,
                "alasan": mv.alasan,
                "catatan": mv.catatan,
                "tanggal": mv.tanggal.isoformat(),
                "oleh": mv.oleh,
            }
            for mv in movements
        ],
        "components": {
            "is_tracked": comp_totals["is_tracked"],
            "ram_summary_chip": comp_totals["ram_summary_chip"],
            "storage_summary_chip": comp_totals["storage_summary_chip"],
            "installed": installed_components,
            "spares": spare_components,
            "pc_targets": pc_targets,
        },
        "depreciation": _compute_depreciation_info(asset),
    }


@router.post("/{id_aset}/handover")
def handover_or_move_asset(
    id_aset: str,
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Mencatat Serah Terima atau Pindah Lokasi ke asset_movements secara atomik (Seksi 4.4 & 9)."""
    asset = session.exec(
        select(Asset).where(
            func.lower(Asset.id_aset) == id_aset.strip().lower(),
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )

    jenis_mutasi = str(payload.get("jenis") or "serah_terima").strip().lower()
    if jenis_mutasi not in ("serah_terima", "pindah", "ubah_status"):
        jenis_mutasi = "serah_terima"

    new_user = str(payload.get("pengguna_baru") or "").strip()
    new_loc = str(payload.get("lokasi_baru") or "").strip()
    new_status = str(payload.get("status_baru") or "").strip()
    alasan = str(payload.get("alasan") or "Serah terima operasional").strip()
    catatan = str(payload.get("catatan") or "").strip()
    raw_tgl = str(payload.get("tanggal") or "").strip()
    tgl_mutasi = date.fromisoformat(raw_tgl) if raw_tgl else date.today()

    old_user = asset.pemakai_text or asset.penanggung_jawab or "Gudang"
    old_loc = asset.lokasi
    dari_str = f"{old_user} ({old_loc})"

    if new_user:
        asset.penanggung_jawab = new_user
        asset.pemakai_text = new_user
    if new_loc:
        asset.lokasi = new_loc
    if new_status:
        asset.status = normalize_asset_status(new_status)

    ke_str = f"{asset.pemakai_text or asset.penanggung_jawab} ({asset.lokasi})"
    asset.updated_at = utcnow()
    session.add(asset)

    movement = AssetMovement(
        asset_id=asset.id_aset,
        jenis=jenis_mutasi,
        dari=dari_str[:150],
        ke=ke_str[:150],
        alasan=alasan[:150],
        catatan=catatan[:500],
        tanggal=tgl_mutasi,
        oleh=current_user.username,
    )
    session.add(movement)

    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=getattr(current_user, "full_name", current_user.username),
        role=current_user.role,
        aksi="Serah Terima / Pindah Aset",
        modul="Inventory",
        target_id=asset.id_aset,
        detail=f"{jenis_mutasi}: {dari_str} -> {ke_str}. Catatan: {catatan}",
        level_risiko="Rendah",
    )
    session.commit()
    session.refresh(asset)
    return {"status": "ok", "id_aset": asset.id_aset, "ke": ke_str}


@router.post("/{id_aset}/links")
def manage_asset_relation_link(
    id_aset: str,
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Menautkan atau melepas relasi Monitor <-> PC atau UPS <-> Server (Seksi 4.4 & 9)."""
    source = session.exec(
        select(Asset).where(
            func.lower(Asset.id_aset) == id_aset.strip().lower(),
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    target_tag = str(payload.get("target_asset_id") or "").strip().upper()
    action = str(payload.get("action") or "link").strip().lower()
    rel_type = str(payload.get("tipe") or "terpasang").strip().lower()

    if source is None:
        raise HTTPException(status_code=404, detail="Aset sumber tidak ditemukan")

    if action == "unlink":
        if source.kategori.lower() == "monitor":
            old_parent = source.parent_asset_id or "—"
            source.parent_asset_id = None
            source.status = "Cadangan"
            source.pemakai_text = "Cadangan Gudang IT"
            source.penanggung_jawab = "Cadangan Gudang IT"
            session.add(source)
            session.add(
                AssetMovement(
                    asset_id=source.id_aset,
                    jenis="lepas",
                    dari=old_parent,
                    ke="Cadangan (Gudang)",
                    alasan="Lepas tautan monitor",
                    oleh=current_user.username,
                )
            )
        elif target_tag:
            child_mon = session.exec(
                select(Asset).where(
                    func.upper(Asset.id_aset) == target_tag,
                    col(Asset.parent_asset_id) == source.id_aset,
                )
            ).first()
            if child_mon:
                child_mon.parent_asset_id = None
                child_mon.status = "Cadangan"
                child_mon.pemakai_text = "Cadangan Gudang IT"
                child_mon.penanggung_jawab = "Cadangan Gudang IT"
                session.add(child_mon)
            existing_lnk = session.exec(
                select(AssetLink).where(
                    or_(
                        and_(
                            col(AssetLink.asset_id) == source.id_aset,
                            col(AssetLink.linked_asset_id) == target_tag,
                        ),
                        and_(
                            col(AssetLink.asset_id) == target_tag,
                            col(AssetLink.linked_asset_id) == source.id_aset,
                        ),
                    )
                )
            ).first()
            if existing_lnk:
                session.delete(existing_lnk)
        session.commit()
        return {"status": "ok", "action": "unlink"}

    target = session.exec(
        select(Asset).where(
            func.upper(Asset.id_aset) == target_tag,
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if target is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aset tujuan '{target_tag}' tidak ditemukan",
        )

    # Jika menautkan Monitor ke PC
    if (
        source.kategori.lower() in ("pc", "laptop", "server")
        and target.kategori.lower() == "monitor"
    ):
        target.parent_asset_id = source.id_aset
        target.status = "Digunakan"
        target.lokasi = source.lokasi
        target.pemakai_text = f"Terpasang di {source.id_aset}"
        target.penanggung_jawab = f"Terpasang di {source.id_aset}"
        session.add(target)
        session.add(
            AssetMovement(
                asset_id=target.id_aset,
                jenis="pasang",
                dari="Cadangan",
                ke=source.id_aset,
                alasan=f"Dipasang ke {source.id_aset}",
                oleh=current_user.username,
            )
        )
    elif source.kategori.lower() == "monitor" and target.kategori.lower() in (
        "pc",
        "laptop",
        "server",
    ):
        source.parent_asset_id = target.id_aset
        source.status = "Digunakan"
        source.lokasi = target.lokasi
        source.pemakai_text = f"Terpasang di {target.id_aset}"
        source.penanggung_jawab = f"Terpasang di {target.id_aset}"
        session.add(source)
    else:
        # Tautan UPS <-> Server melalui asset_links
        ups_asset = source if source.kategori.lower() == "ups" else target
        srv_asset = target if source.kategori.lower() == "ups" else source
        existing = session.exec(
            select(AssetLink).where(
                col(AssetLink.asset_id) == ups_asset.id_aset,
                col(AssetLink.linked_asset_id) == srv_asset.id_aset,
            )
        ).first()
        if existing is None:
            session.add(
                AssetLink(
                    asset_id=ups_asset.id_aset,
                    linked_asset_id=srv_asset.id_aset,
                    tipe=rel_type if rel_type != "terpasang" else "menyuplai_daya",
                )
            )
        ups_asset.beban_perangkat = srv_asset.nama_aset
        ups_asset.pemakai_text = f"Menyuplai {srv_asset.nama_aset}"
        ups_asset.penanggung_jawab = ups_asset.pemakai_text
        ups_asset.status = "Digunakan"
        session.add(ups_asset)

    session.commit()
    return {"status": "ok", "source": source.id_aset, "target": target.id_aset}


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def create_assets_bulk(
    payload: dict,
    session: SessionDep,
    _: EditorUserDep,
) -> dict:
    """Membuat satu atau beberapa aset sekaligus (mendukung duplicate_count dari frontend)."""
    raw_asset = dict(payload.get("asset") or payload)
    duplicate_count = max(1, int(payload.get("duplicate_count", 1) or 1))
    created_items: list[AssetPublic] = []

    for idx in range(duplicate_count):
        item_data = dict(raw_asset)
        if duplicate_count > 1:
            item_data.pop("id_aset", None)
            item_data["serial_number"] = None
            item_data["sn_pid"] = ""
            if isinstance(item_data.get("attributes"), dict):
                attrs = dict(item_data["attributes"])
                attrs.pop("sn_pid", None)
                item_data["attributes"] = attrs

        parsed = AssetCreate.model_validate(item_data)
        _check_duplicate_sn(session, parsed.serial_number)
        if parsed.id_aset and parsed.id_aset.strip() and idx == 0:
            final_id_aset = parsed.id_aset.strip().upper()
            existing_code = session.exec(
                select(Asset).where(func.lower(Asset.id_aset) == final_id_aset.lower())
            ).first()
            if existing_code is not None:
                final_id_aset = generate_next_asset_id(session, parsed.kategori)
        else:
            final_id_aset = generate_next_asset_id(session, parsed.kategori)

        extra_raw = dict(parsed.model_extra or {})
        if parsed.attributes:
            extra_raw.update(parsed.attributes)
        if parsed.kepemilikan:
            extra_raw["kepemilikan"] = parsed.kepemilikan
        if parsed.tanggal_keluar_gudang:
            extra_raw["tanggal_keluar_gudang"] = parsed.tanggal_keluar_gudang
        clean_extra = {k: v for k, v in extra_raw.items() if k.lower() not in FORBIDDEN_FIELDS}

        asset = Asset(
            id_aset=final_id_aset,
            nama_aset=parsed.nama_aset,
            kategori=parsed.kategori,
            merek=parsed.merek.strip(),
            model=parsed.model.strip(),
            serial_number=parsed.serial_number,
            lokasi=parsed.lokasi,
            detail_lokasi=parsed.detail_lokasi.strip(),
            penanggung_jawab=parsed.penanggung_jawab.strip(),
            status=parsed.status,
            kondisi=parsed.kondisi,
            tanggal_masuk=parsed.tanggal_masuk,
            processor=parsed.processor.strip(),
            motherboard=parsed.motherboard.strip(),
            ram=parsed.ram.strip(),
            storage=parsed.storage.strip(),
            gpu=parsed.gpu.strip(),
            os=parsed.os.strip(),
            watt=parsed.watt,
            ukuran_layar=parsed.ukuran_layar.strip(),
            resolusi=parsed.resolusi.strip(),
            panel=parsed.panel.strip(),
            port_display=parsed.port_display.strip(),
            kapasitas_va=parsed.kapasitas_va,
            kapasitas_watt=parsed.kapasitas_watt,
            baterai=parsed.baterai.strip(),
            jumlah_baterai=parsed.jumlah_baterai,
            beban_perangkat=parsed.beban_perangkat.strip(),
            ip_address=parsed.ip_address.strip(),
            mac_address=parsed.mac_address.strip(),
            koneksi=parsed.koneksi.strip(),
            catatan=parsed.catatan.strip(),
            extra_specs=clean_extra,
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        created_items.append(AssetPublic.from_asset(asset))

    return {"created_count": len(created_items), "items": created_items}


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

    extra_raw = dict(payload.model_extra or {})
    if payload.attributes:
        extra_raw.update(payload.attributes)
    if payload.kepemilikan:
        extra_raw["kepemilikan"] = payload.kepemilikan
    if payload.tanggal_keluar_gudang:
        extra_raw["tanggal_keluar_gudang"] = payload.tanggal_keluar_gudang
    clean_extra = {k: v for k, v in extra_raw.items() if k.lower() not in FORBIDDEN_FIELDS}

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

    if "digunakan_oleh" in update_data and "penanggung_jawab" not in update_data:
        update_data["penanggung_jawab"] = update_data.pop("digunakan_oleh") or ""
    else:
        update_data.pop("digunakan_oleh", None)

    if "tanggal_masuk_gudang" in update_data and "tanggal_masuk" not in update_data:
        update_data["tanggal_masuk"] = update_data.pop("tanggal_masuk_gudang")
    else:
        update_data.pop("tanggal_masuk_gudang", None)

    if "sn_pid" in update_data and "serial_number" not in update_data:
        update_data["serial_number"] = update_data.pop("sn_pid")
    else:
        update_data.pop("sn_pid", None)

    if "serial_number" in update_data:
        cleaned_sn = _clean_serial_number(update_data["serial_number"])
        _check_duplicate_sn(session, cleaned_sn, exclude_asset_id=asset.id)
        update_data["serial_number"] = cleaned_sn

    extra_specs = dict(asset.extra_specs or {})
    if "attributes" in update_data and isinstance(update_data["attributes"], dict):
        for k, v in update_data.pop("attributes").items():
            if k.lower() not in FORBIDDEN_FIELDS:
                extra_specs[k] = v
    if "kepemilikan" in update_data and update_data["kepemilikan"] is not None:
        extra_specs["kepemilikan"] = update_data.pop("kepemilikan")
    if "tanggal_keluar_gudang" in update_data and update_data["tanggal_keluar_gudang"] is not None:
        extra_specs["tanggal_keluar_gudang"] = update_data.pop("tanggal_keluar_gudang")
    asset.extra_specs = extra_specs

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
    """Soft-delete aset berdasarkan id_aset setelah memastikan tidak ada relasi aktif (Seksi 13)."""
    asset = session.exec(
        select(Asset).where(
            func.lower(Asset.id_aset) == id_aset.strip().lower(),
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aset tidak ditemukan",
        )

    has_child = session.exec(
        select(Asset.id_aset).where(
            col(Asset.parent_asset_id) == asset.id_aset,
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if has_child:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Aset {asset.id_aset} masih memiliki komponen/perangkat terpasang "
                f"({has_child}). Lepas terlebih dahulu."
            ),
        )

    asset.deleted_at = utcnow()
    asset.updated_at = utcnow()
    session.add(asset)
    session.commit()
    return {"status": "ok", "id_aset": asset.id_aset}


@router.get("/{id_aset}/components/preview-impact")
def preview_component_move_impact(
    id_aset: str,
    session: SessionDep,
    _: CurrentUserDep,
    action: str = Query(default="pindah"),
    target_pc_id: str | None = Query(default=None),
) -> dict[str, Any]:
    """Menghitung dampak kapasitas sebelum & sesudah pemindahan komponen (Artboard 12)."""
    comp = session.exec(
        select(Asset).where(
            func.upper(Asset.id_aset) == id_aset.strip().upper(),
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if comp is None:
        raise HTTPException(status_code=404, detail="Komponen tidak ditemukan")

    sp = {**(comp.extra_specs or {}), **(comp.specs or {})}
    cap = _parse_capacity_gb(sp.get("kapasitas_gb") or comp.ram or comp.storage or comp.nama_aset)
    is_ram = comp.kategori.strip().lower() == "ram"
    label_metric = "RAM" if is_ram else "Storage"
    default_cap = 8 if is_ram else 256
    delta = cap or default_cap

    source_id = comp.parent_asset_id
    impacts: list[dict[str, str]] = []
    warning_msg = ""

    if source_id:
        src_totals = _compute_pc_component_totals(session, source_id)
        before_src = src_totals["ram_total_gb"] if is_ram else src_totals["storage_total_gb"]
        if before_src == 0:
            before_src = delta * 2
        after_src = max(0, before_src - delta)
        impacts.append(
            {
                "label": f"{source_id} {label_metric}",
                "change": f"{before_src} GB → {after_src} GB",
            }
        )

    clean_target = (target_pc_id or "").split("·")[0].strip().upper()
    if action.lower() in ("pindah", "pasang") and clean_target:
        tgt_asset = session.exec(
            select(Asset).where(
                func.upper(Asset.id_aset) == clean_target,
                col(Asset.deleted_at).is_(None),
            )
        ).first()
        if tgt_asset:
            tgt_totals = _compute_pc_component_totals(session, tgt_asset.id_aset)
            before_tgt = tgt_totals["ram_total_gb"] if is_ram else tgt_totals["storage_total_gb"]
            if before_tgt == 0:
                raw_spec = tgt_asset.ram if is_ram else tgt_asset.storage
                before_tgt = _parse_capacity_gb(raw_spec) or delta
            after_tgt = before_tgt + delta
            impacts.append(
                {
                    "label": f"{tgt_asset.id_aset} {label_metric}",
                    "change": f"{before_tgt} GB → {after_tgt} GB",
                }
            )
            # Peringatan non-blocking jika tipe DDR tidak cocok (Seksi 6)
            comp_tipe = str(sp.get("tipe") or "").upper()
            if is_ram and comp_tipe and tgt_asset.ram and comp_tipe not in tgt_asset.ram.upper():
                warning_msg = (
                    f"Peringatan: Tipe memori {comp_tipe} mungkin berbeda dengan spesifikasi "
                    f"induk {tgt_asset.id_aset} ({tgt_asset.ram})."
                )

    return {
        "component_id": comp.id_aset,
        "impacts": impacts,
        "warning": warning_msg,
        "needs_wipe_confirmation": (
            comp.kategori.strip().lower() in ("ssd", "hdd", "ssd/hdd")
            and str(sp.get("data_status") or "").lower() == "berisi data"
        ),
    }


@router.post("/components/mutate")
def mutate_component_unit(
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Operasi atomik Pasang, Lepas, Pindah, dan Tandai Rusak komponen per unit (Seksi 6)."""
    comp_id = str(payload.get("component_id") or "").strip().upper()
    action = str(payload.get("action") or "pindah").strip().lower()
    raw_target = str(payload.get("target_pc_id") or "").strip()
    target_pc_id = raw_target.split("·")[0].strip().upper() if raw_target else ""
    slot = str(payload.get("slot") or "").strip()
    lokasi_cadangan = str(payload.get("lokasi") or "Gudang").strip()
    alasan = str(payload.get("alasan") or "Upgrade / Mutasi Komponen").strip()
    catatan = str(payload.get("catatan") or "").strip()
    raw_tgl = str(payload.get("tanggal") or "").strip()
    confirm_wipe = bool(payload.get("confirm_wipe", False))
    data_status_new = str(payload.get("data_status") or "").strip()

    try:
        tgl_mutasi = date.fromisoformat(raw_tgl) if raw_tgl else date.today()
    except ValueError:
        tgl_mutasi = date.today()

    # Kunci baris komponen (FOR UPDATE) agar tidak bisa dipasang ke 2 PC bersamaan (Seksi 6 & 19)
    comp = session.exec(
        select(Asset)
        .where(
            func.upper(Asset.id_aset) == comp_id,
            col(Asset.deleted_at).is_(None),
        )
        .with_for_update()
    ).first()
    if comp is None:
        raise HTTPException(status_code=404, detail=f"Komponen '{comp_id}' tidak ditemukan")

    old_parent_id = comp.parent_asset_id
    sp = {**(comp.extra_specs or {}), **(comp.specs or {})}
    is_disk = comp.kategori.strip().lower() in ("ssd", "hdd", "ssd/hdd")
    current_data_status = str(sp.get("data_status") or "Kosong").strip()

    if action in ("pasang", "pindah"):
        if not target_pc_id:
            raise HTTPException(status_code=422, detail="PC atau Server tujuan wajib dipilih")
        if old_parent_id and target_pc_id == old_parent_id.upper():
            raise HTTPException(
                status_code=422,
                detail="PC tujuan tidak boleh sama dengan PC asal",
            )
        target_pc = session.exec(
            select(Asset)
            .where(
                func.upper(Asset.id_aset) == target_pc_id,
                col(Asset.deleted_at).is_(None),
            )
            .with_for_update()
        ).first()
        if target_pc is None:
            raise HTTPException(
                status_code=404,
                detail=f"PC tujuan '{target_pc_id}' tidak ditemukan",
            )
        if target_pc.kategori.strip().lower() not in ("pc", "laptop", "server"):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Aset tujuan '{target_pc.id_aset}' ({target_pc.kategori}) bukan "
                    "PC/Laptop/Server"
                ),
            )
        # Validasi ketat Wipe Disk SSD/HDD (Seksi 6 & 19)
        if is_disk and current_data_status.lower() == "berisi data" and not confirm_wipe:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Disk {comp.id_aset} berstatus 'Berisi data'. Harap centang konfirmasi "
                    "bahwa data pada disk sudah dihapus (wipe) atau dipindah dengan aman."
                ),
            )
        if is_disk and confirm_wipe:
            sp["data_status"] = "Sudah di-wipe"

        if slot:
            sp["slot"] = slot
        sp["dipasang_sejak"] = format_date_id(tgl_mutasi.isoformat())

        comp.parent_asset_id = target_pc.id_aset
        comp.status = "Digunakan"
        comp.lokasi = target_pc.lokasi
        comp.pemakai_text = f"Terpasang di {target_pc.id_aset}"
        comp.penanggung_jawab = comp.pemakai_text
        dari_label = old_parent_id or f"Cadangan ({comp.lokasi})"
        ke_label = f"{target_pc.id_aset} ({slot or 'Slot Default'})"
        jenis_mv = "pindah" if old_parent_id else "pasang"

    elif action == "lepas":
        comp.parent_asset_id = None
        comp.status = "Cadangan"
        comp.lokasi = lokasi_cadangan or "Head Office (Office Blok 14)"
        comp.pemakai_text = "Cadangan · Gudang"
        comp.penanggung_jawab = "Cadangan · Gudang"
        if is_disk:
            sp["data_status"] = data_status_new or (
                "Sudah di-wipe" if confirm_wipe else "Berisi data"
            )
        dari_label = old_parent_id or "PC Induk"
        ke_label = f"Cadangan · {lokasi_cadangan}"
        jenis_mv = "lepas"

    elif action in ("rusak", "tandai_rusak"):
        comp.parent_asset_id = None
        comp.status = "Rusak"
        comp.kondisi = "Rusak"
        comp.pemakai_text = "Rusak · Gudang"
        comp.penanggung_jawab = "Rusak · Gudang"
        dari_label = old_parent_id or comp.lokasi
        ke_label = "Status: Rusak"
        jenis_mv = "ubah_status"
    else:
        raise HTTPException(status_code=422, detail=f"Tindakan '{action}' tidak dikenal")

    comp.specs = sp
    comp.extra_specs = sp
    comp.updated_at = utcnow()
    session.add(comp)
    session.flush()

    # Rekalkulasi otomatis kapasitas RAM & Storage pada PC asal dan PC tujuan
    if old_parent_id:
        _recalculate_parent_component_totals(session, old_parent_id)
    if comp.parent_asset_id:
        _recalculate_parent_component_totals(session, comp.parent_asset_id)

    session.add(
        AssetMovement(
            asset_id=comp.id_aset,
            jenis=jenis_mv,
            dari=dari_label[:150],
            ke=ke_label[:150],
            alasan=alasan[:150],
            catatan=catatan[:500],
            tanggal=tgl_mutasi,
            oleh=current_user.username,
        )
    )
    if old_parent_id:
        session.add(
            AssetMovement(
                asset_id=old_parent_id,
                jenis=jenis_mv,
                dari=f"{comp.id_aset} ({old_parent_id})",
                ke=ke_label[:150],
                alasan=alasan[:150],
                catatan=f"Komponen {comp.id_aset}: {catatan}"[:500],
                tanggal=tgl_mutasi,
                oleh=current_user.username,
            )
        )
    if comp.parent_asset_id and comp.parent_asset_id != old_parent_id:
        session.add(
            AssetMovement(
                asset_id=comp.parent_asset_id,
                jenis=jenis_mv,
                dari=dari_label[:150],
                ke=f"{comp.id_aset} -> {comp.parent_asset_id}",
                alasan=alasan[:150],
                catatan=f"Komponen {comp.id_aset}: {catatan}"[:500],
                tanggal=tgl_mutasi,
                oleh=current_user.username,
            )
        )

    record_audit_log(
        session,
        username=current_user.username,
        nama_pengguna=getattr(current_user, "full_name", current_user.username),
        role=current_user.role,
        aksi=f"Komponen {jenis_mv.title()}",
        modul="Inventory",
        target_id=comp.id_aset,
        detail=f"{comp.id_aset}: {dari_label} -> {ke_label} ({alasan})",
        level_risiko="Sedang",
    )
    session.commit()
    return {"status": "ok", "component_id": comp.id_aset, "action": jenis_mv}


@router.post("/{id_aset}/components/convert-wizard")
def convert_legacy_specs_to_components(
    id_aset: str,
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Wizard Konversi spesifikasi teks lama PC/Server menjadi komponen per unit (Seksi 15.5)."""
    parent = session.exec(
        select(Asset).where(
            func.upper(Asset.id_aset) == id_aset.strip().lower().upper(),
            col(Asset.deleted_at).is_(None),
        )
    ).first()
    if parent is None:
        raise HTTPException(status_code=404, detail="Aset induk tidak ditemukan")

    items = payload.get("items")
    if not isinstance(items, list) or not items:
        # Buat usulan otomatis dari teks parent.ram dan parent.storage
        ram_cap = _parse_capacity_gb(parent.ram) or 16
        parent_ram_u = (parent.ram or "").upper()
        if "DDR5" in parent_ram_u:
            ram_type = "DDR5"
        elif "DDR3" in parent_ram_u:
            ram_type = "DDR3"
        else:
            ram_type = "DDR4"

        st_cap = _parse_capacity_gb(parent.storage) or 512
        parent_st_u = (parent.storage or "").upper()
        if "NVME" in parent_st_u:
            st_type = "NVMe"
        elif "HDD" in parent_st_u:
            st_type = "HDD"
        else:
            st_type = "SATA"

        if ram_cap >= 16:
            items = [
                {
                    "kategori": "RAM",
                    "tipe": ram_type,
                    "kapasitas_gb": ram_cap // 2,
                    "slot": "DIMM 1",
                },
                {
                    "kategori": "RAM",
                    "tipe": ram_type,
                    "kapasitas_gb": ram_cap // 2,
                    "slot": "DIMM 2",
                },
            ]
        else:
            items = [
                {
                    "kategori": "RAM",
                    "tipe": ram_type,
                    "kapasitas_gb": ram_cap,
                    "slot": "DIMM 1",
                },
            ]
        items.append(
            {
                "kategori": "SSD",
                "tipe": st_type,
                "kapasitas_gb": st_cap,
                "slot": "M.2" if st_type == "NVMe" else "SATA 1",
            }
        )

    created_tags: list[str] = []
    for it in items:
        kat = str(it.get("kategori") or "RAM").strip().upper()
        if kat not in ("RAM", "SSD", "HDD", "VGA", "PSU"):
            kat = "RAM"
        tipe = str(it.get("tipe") or ("DDR4" if kat == "RAM" else "NVMe")).strip()
        cap_gb = int(it.get("kapasitas_gb") or (8 if kat == "RAM" else 512))
        slot = str(it.get("slot") or ("DIMM 1" if kat == "RAM" else "M.2")).strip()
        new_tag = generate_next_asset_id(session, kat)
        nama_comp = f"{kat} {tipe} {cap_gb} GB"
        sp_comp = {
            "tipe": tipe,
            "kapasitas_gb": cap_gb,
            "slot": slot,
            "dipasang_sejak": "Jun 2025",
            "data_status": "Berisi data" if kat in ("SSD", "HDD") else "Kosong",
            "kepemilikan": "XML",
        }
        comp_asset = Asset(
            id_aset=new_tag,
            asset_tag=new_tag,
            nama_aset=nama_comp,
            nama=nama_comp,
            kategori=kat,
            merek="Kingston" if kat == "RAM" else "Samsung",
            model=f"{tipe} {cap_gb}GB",
            lokasi=parent.lokasi,
            penanggung_jawab=f"Terpasang di {parent.id_aset}",
            pemakai_text=f"Terpasang di {parent.id_aset}",
            parent_asset_id=parent.id_aset,
            status="Digunakan",
            kondisi="Baik",
            tanggal_masuk=parent.tanggal_masuk or date.today(),
            tanggal_perolehan=parent.tanggal_perolehan or date.today(),
            ram=f"{cap_gb}GB {tipe}" if kat == "RAM" else "",
            storage=f"{tipe} {cap_gb}GB" if kat in ("SSD", "HDD") else "",
            specs=sp_comp,
            extra_specs=sp_comp,
            tracking="unit",
            qty=1,
            created_by=current_user.username,
        )
        session.add(comp_asset)
        session.flush()
        created_tags.append(new_tag)

    _recalculate_parent_component_totals(session, parent.id_aset)
    session.add(
        AssetMovement(
            asset_id=parent.id_aset,
            jenis="pasang",
            dari="Konversi Spesifikasi Teks",
            ke=", ".join(created_tags),
            alasan="Wizard Konversi Komponen per Unit",
            tanggal=date.today(),
            oleh=current_user.username,
        )
    )
    session.commit()
    return {"status": "ok", "parent_id": parent.id_aset, "created_components": created_tags}
