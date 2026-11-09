"""Endpoint CRUD Aset TI, pencarian, filter, dan generator ID otomatis."""

import re
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from app.core.master_data import (
    CATEGORY_TREE,
    get_prefix_for_category,
    normalize_asset_condition,
    normalize_asset_status,
)
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset, AssetLink, Category
from app.models.base import utcnow
from app.models.credential import Credential
from app.models.ip_allocation import IPAllocation
from app.schemas.asset import (
    FORBIDDEN_FIELDS,
    AssetCreate,
    AssetPageResponse,
    AssetPublic,
    AssetUpdate,
    _clean_serial_number,
    _resolve_category_group,
)

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
    no_purchase: int | None = Query(default=None),
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

    if no_purchase == 1:
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
