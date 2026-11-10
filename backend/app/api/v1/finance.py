"""Endpoint CRUD Pembelian, Invoice, dan Tagihan Berulang (/api/v1/purchases)."""

import re
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.api.v1.assets import generate_next_asset_id
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
from app.models.asset import Asset
from app.models.base import utcnow
from app.models.finance import Purchase
from app.schemas.finance import (
    VALID_BILLING_CYCLES,
    VALID_FINANCE_STATUSES,
    MarkPaidRequest,
    PurchaseCreate,
    PurchasePageResponse,
    PurchasePublic,
    PurchaseUpdate,
    advance_due_date,
)

router = APIRouter()

CODE_PATTERN = re.compile(r"^([A-Z]+)-(\d+)$")


def _prefix_for_purchase(payload: PurchaseCreate) -> str:
    if payload.is_recurring:
        return "BIL"
    if payload.jenis_transaksi.strip().lower() == "invoice":
        return "INV"
    return "PO"


def generate_next_purchase_code(session: Session, prefix: str = "PO") -> str:
    """Menghasilkan kode otomatis seperti PO-001, INV-001, atau BIL-001."""
    clean_prefix = prefix.strip().upper() or "PO"
    existing = session.exec(
        select(Purchase.kode_pembelian).where(
            col(Purchase.kode_pembelian).like(f"{clean_prefix}-%")
        )
    ).all()

    max_num = 0
    for code in existing:
        match = CODE_PATTERN.match(code.strip().upper())
        if match and match.group(1) == clean_prefix:
            max_num = max(max_num, int(match.group(2)))
    return f"{clean_prefix}-{max_num + 1:03d}"


def _compute_finance_summary(
    all_rows: list[Purchase],
    today: date | None = None,
) -> tuple[dict[str, int], dict[str, Any]]:
    """Menghitung tab_counts, summary, dan KPI keuangan dari seluruh baris."""
    ref_today = today or date.today()
    public_items = [PurchasePublic.from_model(r, today=ref_today) for r in all_rows]

    total_count = len(public_items)
    pembelian_count = sum(1 for i in public_items if not i.is_recurring)
    recurring_count = sum(1 for i in public_items if i.is_recurring)
    invoice_count = sum(
        1 for i in public_items if i.nomor_invoice != "-" or i.jenis_transaksi.lower() == "invoice"
    )
    lunas_count = sum(1 for i in public_items if i.status.lower() == "lunas")
    unpaid_count = sum(1 for i in public_items if i.status.lower() not in ("lunas", "dibatalkan"))
    overdue_count = sum(1 for i in public_items if i.is_overdue)
    due_soon_count = sum(1 for i in public_items if i.is_due_soon)

    total_pengeluaran = sum(i.total_harga for i in public_items if i.status.lower() != "dibatalkan")
    total_lunas = sum(i.total_harga for i in public_items if i.status.lower() == "lunas")
    total_belum_lunas = sum(
        i.total_harga for i in public_items if i.status.lower() not in ("lunas", "dibatalkan")
    )

    # Estimasi biaya langganan berulang per bulan
    biaya_bulanan_berulang = 0
    for i in public_items:
        if not i.is_recurring or i.status.lower() == "dibatalkan":
            continue
        if i.siklus_tagihan == "Mingguan":
            biaya_bulanan_berulang += i.total_harga * 4
        elif i.siklus_tagihan == "Bulanan":
            biaya_bulanan_berulang += i.total_harga
        elif i.siklus_tagihan == "Triwulan":
            biaya_bulanan_berulang += round(i.total_harga / 3)
        elif i.siklus_tagihan == "Tahunan":
            biaya_bulanan_berulang += round(i.total_harga / 12)

    tab_counts = {
        "Semua": total_count,
        "all": total_count,
        "Pembelian": pembelian_count,
        "Invoice": invoice_count,
        "Tagihan Berulang": recurring_count,
        "Lunas": lunas_count,
        "Belum Lunas": unpaid_count,
        "Jatuh Tempo": overdue_count,
    }

    reguler_items = [i for i in public_items if not i.is_recurring]
    max_item = max(reguler_items, key=lambda i: i.total_harga, default=None)
    belanja_terbesar_str = (
        f"Rp {max_item.total_harga:,} ({max_item.nama_item[:20]})".replace(",", ".")
        if max_item
        else "Rp 0"
    )
    belum_dicatat_cnt = sum(1 for i in reguler_items if not i.id_aset)
    sudah_ditautkan_cnt = sum(1 for i in public_items if i.terkait_id)
    belum_ditautkan_cnt = sum(1 for i in public_items if not i.terkait_id)

    summary: dict[str, Any] = {
        "total_transaksi": total_count,
        "total_pembelian": pembelian_count,
        "total_invoice": invoice_count or total_count,
        "total_tagihan_berulang": recurring_count,
        "total_pengeluaran": total_pengeluaran,
        "total_nilai": total_pengeluaran,
        "total_belanja": f"Rp {total_pengeluaran:,}".replace(",", "."),
        "belanja_terbesar": belanja_terbesar_str,
        "belum_dicatat": belum_dicatat_cnt,
        "sudah_ditautkan": sudah_ditautkan_cnt,
        "belum_ditautkan": belum_ditautkan_cnt,
        "tanpa_bukti": 0,
        "terlambat": overdue_count,
        "segera": due_soon_count,
        "tagihan_aktif": recurring_count,
        "perlu_dibayar_30d": f"Rp {biaya_bulanan_berulang:,}".replace(",", "."),
        "total_lunas": total_lunas,
        "total_belum_lunas": total_belum_lunas,
        "estimasi_tagihan_bulanan": biaya_bulanan_berulang,
        "jumlah_lunas": lunas_count,
        "jumlah_belum_lunas": unpaid_count,
        "jumlah_jatuh_tempo": overdue_count,
        "jumlah_segera_jatuh_tempo": due_soon_count,
    }
    return tab_counts, summary


def _find_purchase(session: Session, identifier: str) -> Purchase:
    cleaned = identifier.strip()
    row: Purchase | None = None
    if cleaned.isdigit():
        row = session.get(Purchase, int(cleaned))
    if row is None:
        row = session.exec(
            select(Purchase).where(func.lower(col(Purchase.kode_pembelian)) == cleaned.lower())
        ).first()
    if row is None:
        row = session.exec(
            select(Purchase).where(func.lower(col(Purchase.nomor_invoice)) == cleaned.lower())
        ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data pembelian/tagihan tidak ditemukan",
        )
    return row


@router.get("", response_model=PurchasePageResponse)
def list_purchases(
    session: SessionDep,
    _: CurrentUserDep,
    page_params: PageParamsDep,
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tab: str | None = Query(default=None),
    jenis: str | None = Query(default=None),
    kategori: str | None = Query(default=None),
    lokasi: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    month: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    link_status: str | None = Query(default=None),
    periode: str | None = Query(default=None),
    is_recurring: bool | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="asc"),
) -> PurchasePageResponse:
    """Mengambil daftar pembelian, invoice, dan tagihan berulang berhalaman."""
    all_rows = list(
        session.exec(
            select(Purchase).order_by(
                col(Purchase.tanggal_beli).desc(),
                col(Purchase.id).desc(),
            )
        ).all()
    )
    today = date.today()
    tab_counts, summary = _compute_finance_summary(all_rows, today=today)
    all_public = [
        PurchasePublic.from_model(r, today=today, seq_no=idx + 1) for idx, r in enumerate(all_rows)
    ]

    filtered = all_public

    keyword = (search or q or "").strip().lower()
    if keyword:
        filtered = [
            i
            for i in filtered
            if keyword in i.kode_pembelian.lower()
            or keyword in i.nomor_invoice.lower()
            or keyword in i.no_invoice.lower()
            or keyword in i.nama_item.lower()
            or keyword in i.vendor.lower()
            or keyword in i.kategori.lower()
            or keyword in i.penanggung_jawab.lower()
            or keyword in i.keterangan.lower()
        ]

    active_tab = (tab or jenis or "").strip().lower()
    if active_tab and active_tab not in ("semua", "all"):
        if active_tab in ("pembelian", "reguler"):
            filtered = [i for i in filtered if not i.is_recurring]
        elif active_tab in ("tagihan berulang", "berulang", "recurring", "langganan"):
            filtered = [i for i in filtered if i.is_recurring]
        elif active_tab == "invoice":
            filtered = [
                i
                for i in filtered
                if i.nomor_invoice != "-"
                or i.jenis_transaksi.lower() == "invoice"
                or not i.is_recurring
            ]
        elif active_tab == "belum lunas":
            filtered = [i for i in filtered if i.status.lower() not in ("lunas", "dibatalkan")]
        elif active_tab in ("jatuh tempo", "overdue", "terlambat"):
            filtered = [i for i in filtered if i.is_overdue]

    if is_recurring is True:
        filtered = [i for i in filtered if i.is_recurring]
    elif is_recurring is False:
        filtered = [i for i in filtered if not i.is_recurring]

    if overdue_only:
        filtered = [i for i in filtered if i.is_overdue]

    if kategori and kategori.strip().lower() not in ("semua", "all", ""):
        kat_clean = kategori.strip().lower()
        filtered = [i for i in filtered if i.kategori.lower() == kat_clean]

    if lokasi and lokasi.strip().lower() not in ("semua", "all", ""):
        loc_clean = lokasi.strip().lower()
        filtered = [i for i in filtered if i.lokasi.lower() == loc_clean]

    if month and month.strip().lower() not in ("semua", "all", ""):
        m_map = {
            "januari": "-01-",
            "februari": "-02-",
            "maret": "-03-",
            "april": "-04-",
            "mei": "-05-",
            "juni": "-06-",
            "juli": "-07-",
            "agustus": "-08-",
            "september": "-09-",
            "oktober": "-10-",
            "november": "-11-",
            "desember": "-12-",
        }
        m_sub = m_map.get(month.strip().lower(), month.strip())
        filtered = [i for i in filtered if m_sub in i.tanggal_beli]

    if platform and platform.strip().lower() not in ("semua", "all", ""):
        p_clean = platform.strip().lower()
        filtered = [i for i in filtered if i.domain_chip.lower() == p_clean]

    if periode and periode.strip().lower() not in ("semua", "all", ""):
        per_clean = periode.strip().lower()
        filtered = [i for i in filtered if i.periode.lower() == per_clean]

    if link_status and link_status.strip().lower() not in ("semua", "all", ""):
        ls_clean = link_status.strip().lower()
        if "sudah" in ls_clean:
            filtered = [i for i in filtered if bool(i.terkait_id)]
        elif "belum" in ls_clean:
            filtered = [i for i in filtered if not i.terkait_id]

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        if st_clean in ("jatuh tempo", "overdue", "terlambat"):
            filtered = [i for i in filtered if i.is_overdue]
        elif st_clean == "segera":
            filtered = [i for i in filtered if i.is_due_soon]
        elif st_clean == "aktif":
            filtered = [i for i in filtered if i.aktif]
        else:
            filtered = [
                i
                for i in filtered
                if i.status.lower() == st_clean or i.status_efektif.lower() == st_clean
            ]

    if sort_by and sort_by.strip():
        s_key = sort_by.strip()
        rev = (sort_dir or "asc").strip().lower() == "desc"
        if s_key in ("harga", "pcs", "total", "nominal", "no"):
            filtered.sort(key=lambda i: int(getattr(i, s_key, 0) or 0), reverse=rev)
        else:
            filtered.sort(
                key=lambda i: str(getattr(i, s_key, "") or "").lower(),
                reverse=rev,
            )

    total = len(filtered)
    paged = filtered[page_params.offset : page_params.offset + page_params.page_size]

    return PurchasePageResponse(
        items=paged,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
        tab_counts=tab_counts,
        summary=summary,
        kpi=summary,
    )


@router.get("/{identifier}", response_model=PurchasePublic)
def get_purchase_detail(
    identifier: str,
    session: SessionDep,
    _: CurrentUserDep,
) -> PurchasePublic:
    """Mengambil detail satu pembelian/invoice berdasarkan ID atau kode_pembelian."""
    row = _find_purchase(session, identifier)
    return PurchasePublic.from_model(row)


@router.post("", response_model=PurchasePublic, status_code=status.HTTP_201_CREATED)
def create_purchase(
    payload: PurchaseCreate,
    session: SessionDep,
    _: EditorUserDep,
) -> PurchasePublic:
    """Membuat catatan pembelian, invoice, atau tagihan berulang baru."""
    if payload.kode_pembelian and payload.kode_pembelian.strip():
        final_code = payload.kode_pembelian.strip().upper()
        dup = session.exec(
            select(Purchase).where(func.lower(col(Purchase.kode_pembelian)) == final_code.lower())
        ).first()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Kode pembelian '{final_code}' sudah terdaftar",
            )
    else:
        prefix = _prefix_for_purchase(payload)
        final_code = generate_next_purchase_code(session, prefix=prefix)

    row = Purchase(
        kode_pembelian=final_code,
        nomor_invoice=payload.nomor_invoice.strip(),
        nama_item=payload.nama_item,
        kategori=payload.kategori.strip(),
        jenis_transaksi=payload.jenis_transaksi.strip(),
        vendor=payload.vendor,
        lokasi=payload.lokasi,
        jumlah=payload.jumlah,
        satuan=payload.satuan.strip(),
        harga_satuan=payload.harga_satuan,
        total_harga=payload.total_harga or (payload.jumlah * payload.harga_satuan),
        tanggal_beli=payload.tanggal_beli or date.today(),
        tanggal_jatuh_tempo=payload.tanggal_jatuh_tempo,
        tanggal_bayar=payload.tanggal_bayar,
        status=payload.status,
        metode_pembayaran=payload.metode_pembayaran.strip(),
        is_recurring=bool(payload.is_recurring),
        siklus_tagihan=payload.siklus_tagihan,
        id_aset=payload.id_aset,
        penanggung_jawab=payload.penanggung_jawab.strip(),
        keterangan=payload.keterangan.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return PurchasePublic.from_model(row)


@router.post("/{identifier}/convert-to-asset")
def convert_purchase_to_asset(
    identifier: str,
    payload: dict[str, Any],
    session: SessionDep,
    current_user: EditorUserDep,
) -> dict[str, Any]:
    """Mendaftarkan item pembelian menjadi N aset atau menandai Bukan Aset (Seksi 10)."""
    from app.core.master_data import resolve_tracking_mode

    row = _find_purchase(session, identifier)

    # Opsi 1: Tandai sebagai Bukan Aset (jasa, langganan, habis pakai)
    if (
        payload.get("bukan_aset") is True
        or str(payload.get("kategori", "")).lower() == "bukan aset"
    ):
        row.id_aset = "BUKAN-ASET"
        row.updated_at = utcnow()
        session.add(row)
        session.commit()
        session.refresh(row)
        return {
            "asset_id": "BUKAN-ASET",
            "created_assets": [],
            "item": PurchasePublic.from_model(row),
        }

    # Hitung aset yang sudah pernah didaftarkan dari item pembelian ini
    existing_linked = list(
        session.exec(
            select(Asset.id_aset).where(
                col(Asset.purchase_item_id) == row.id,
                col(Asset.deleted_at).is_(None),
            )
        ).all()
    )
    if not existing_linked and row.id_aset and row.id_aset != "BUKAN-ASET":
        existing_linked = [x.strip() for x in row.id_aset.split(",") if x.strip()]

    remaining_qty = max(0, row.jumlah - len(existing_linked))
    if remaining_qty == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Seluruh qty ({row.jumlah} unit) pada pembelian {row.kode_pembelian} "
                "sudah terdaftar menjadi aset."
            ),
        )

    req_qty = int(payload.get("jumlah") or payload.get("qty") or remaining_qty)
    if req_qty < 1 or req_qty > remaining_qty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Jumlah aset yang didaftarkan ({req_qty}) tidak boleh melebihi sisa "
                f"qty pembelian ({remaining_qty})."
            ),
        )

    kategori_raw = str(payload.get("kategori") or row.kategori or "PC").strip()
    kat_map = {
        "pc": "PC",
        "laptop": "Laptop",
        "server": "Server",
        "monitor": "Monitor",
        "ups": "UPS",
        "ram": "RAM",
        "ssd": "SSD",
        "hdd": "HDD",
        "ssd/hdd": "SSD",
        "vga": "VGA",
        "psu": "PSU",
        "keyboard": "Keyboard",
        "mouse": "Mouse",
        "jaringan": "Router/Switch",
        "router": "Router/Switch",
        "cctv": "CCTV",
        "ac": "AC",
        "mobil": "Mobil",
        "motor": "Motor",
        "meja": "Meja",
        "kursi": "Kursi",
        "lemari": "Lemari",
        "lainnya": "Lainnya",
    }
    kat_final = kat_map.get(kategori_raw.lower(), kategori_raw)
    is_component = kat_final.lower() in ("ram", "ssd", "hdd", "vga", "psu")
    tracking_mode = resolve_tracking_mode(kat_final, row.harga_satuan)

    lokasi_val = str(payload.get("lokasi") or row.lokasi or "Head Office (Office Blok 14)").strip()
    pemakai_val = str(
        payload.get("penanggung_jawab")
        or ("Cadangan · Gudang" if is_component else (row.penanggung_jawab or "Gudang IT"))
    ).strip()
    serial_numbers: list[str] = payload.get("serial_numbers") or []
    raw_garansi = str(payload.get("garansi_sampai") or "").strip()
    garansi_dt = date.fromisoformat(raw_garansi) if raw_garansi else None

    created_codes: list[str] = []

    # Bila kategori mengikuti batas nilai dan harga_satuan < Rp 1.000.000 -> mode stok
    if tracking_mode == "stok":
        new_id = generate_next_asset_id(session, kat_final)
        stok_asset = Asset(
            id_aset=new_id,
            asset_tag=new_id,
            nama_aset=row.nama_item[:145],
            nama=row.nama_item[:145],
            kategori=kat_final,
            merek=row.vendor[:100] if row.vendor else "Umum",
            model=row.nama_item[:100],
            lokasi=lokasi_val,
            penanggung_jawab=pemakai_val,
            pemakai_text=pemakai_val,
            status="Cadangan",
            kondisi="Baru",
            tanggal_masuk=row.tanggal_beli,
            tanggal_perolehan=row.tanggal_beli,
            nilai_perolehan=row.harga_satuan,
            vendor=row.vendor,
            garansi_sampai=garansi_dt,
            purchase_item_id=row.id,
            tracking="stok",
            qty=req_qty,
            catatan=f"Stok ({req_qty} unit) dari {row.kode_pembelian} ({row.vendor})",
            specs={"kepemilikan": str(payload.get("kepemilikan") or "XML")},
            extra_specs={"kepemilikan": str(payload.get("kepemilikan") or "XML")},
        )
        session.add(stok_asset)
        created_codes.append(new_id)
    else:
        for idx in range(req_qty):
            new_id = generate_next_asset_id(session, kat_final)
            sn_item = (
                serial_numbers[idx].strip()
                if idx < len(serial_numbers) and serial_numbers[idx]
                else None
            )
            cap_gb = 0
            m_gb = re.search(r"(\d+)\s*GB", row.nama_item.upper())
            if m_gb:
                cap_gb = int(m_gb.group(1))
            elif "1TB" in row.nama_item.upper() or "1 TB" in row.nama_item.upper():
                cap_gb = 1024

            comp_specs: dict[str, Any] = {
                "kepemilikan": str(payload.get("kepemilikan") or "XML"),
                "jenis": "Operasional",
            }
            if is_component:
                comp_specs.update(
                    {
                        "tipe": (
                            "DDR4"
                            if kat_final == "RAM"
                            else ("NVMe" if "NVME" in row.nama_item.upper() else "SATA")
                        ),
                        "kapasitas_gb": cap_gb or (8 if kat_final == "RAM" else 512),
                        "data_status": "Kosong",
                    }
                )

            unit_asset = Asset(
                id_aset=new_id,
                asset_tag=new_id,
                nama_aset=row.nama_item[:145],
                nama=row.nama_item[:145],
                kategori=kat_final,
                merek=row.vendor[:100] if row.vendor else "Umum",
                model=row.nama_item[:100],
                serial_number=sn_item,
                lokasi=lokasi_val,
                penanggung_jawab=pemakai_val,
                pemakai_text=pemakai_val,
                status="Cadangan" if is_component else "Digunakan",
                kondisi="Baru",
                tanggal_masuk=row.tanggal_beli,
                tanggal_perolehan=row.tanggal_beli,
                nilai_perolehan=row.harga_satuan,
                vendor=row.vendor,
                garansi_sampai=garansi_dt,
                purchase_item_id=row.id,
                tracking="unit",
                qty=1,
                catatan=f"Didaftarkan dari pembelian {row.kode_pembelian} ({row.vendor})",
                specs=comp_specs,
                extra_specs=comp_specs,
                created_by=current_user.username,
            )
            session.add(unit_asset)
            session.flush()
            created_codes.append(new_id)

    all_codes = [*existing_linked, *created_codes]
    row.id_aset = ", ".join(all_codes)[:250]
    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)

    return {
        "asset_id": created_codes[0] if created_codes else "",
        "id_aset": row.id_aset,
        "created_assets": created_codes,
        "item": PurchasePublic.from_model(row),
    }


def _apply_purchase_update(
    identifier: str,
    payload: PurchaseUpdate,
    session: Session,
) -> PurchasePublic:
    row = _find_purchase(session, identifier)
    data = payload.model_dump(exclude_unset=True)

    for alias_k in ("nama_barang", "produk", "nama"):
        if alias_k in data and "nama_item" not in data:
            data["nama_item"] = data.pop(alias_k)
        else:
            data.pop(alias_k, None)

    if "no_invoice" in data and "nomor_invoice" not in data:
        data["nomor_invoice"] = data.pop("no_invoice")
    else:
        data.pop("no_invoice", None)

    if "nama_toko" in data and "vendor" not in data:
        data["vendor"] = data.pop("nama_toko")
    else:
        data.pop("nama_toko", None)

    if "pcs" in data and "jumlah" not in data:
        data["jumlah"] = data.pop("pcs")
    else:
        data.pop("pcs", None)

    for price_k in ("harga", "nominal"):
        if price_k in data and "harga_satuan" not in data:
            data["harga_satuan"] = data.pop(price_k)
        else:
            data.pop(price_k, None)

    if "total" in data and "total_harga" not in data:
        data["total_harga"] = data.pop("total")
    else:
        data.pop("total", None)

    if "tanggal" in data and "tanggal_beli" not in data:
        data["tanggal_beli"] = data.pop("tanggal")
    else:
        data.pop("tanggal", None)

    if "jatuh_tempo" in data and "tanggal_jatuh_tempo" not in data:
        data["tanggal_jatuh_tempo"] = data.pop("jatuh_tempo")
    else:
        data.pop("jatuh_tempo", None)

    if "periode" in data and "siklus_tagihan" not in data:
        data["siklus_tagihan"] = data.pop("periode")
    else:
        data.pop("periode", None)

    for pic_k in ("dibeli_oleh", "pembayar"):
        if pic_k in data and "penanggung_jawab" not in data:
            data["penanggung_jawab"] = data.pop(pic_k)
        else:
            data.pop(pic_k, None)

    if "link_marketplace" in data and "keterangan" not in data:
        data["keterangan"] = data.pop("link_marketplace")
    else:
        data.pop("link_marketplace", None)

    if "siklus_tagihan" in data and data["siklus_tagihan"] is not None:
        raw_cycle = str(data["siklus_tagihan"]).strip()
        if raw_cycle not in VALID_BILLING_CYCLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Siklus tagihan '{raw_cycle}' tidak valid",
            )
        data["siklus_tagihan"] = VALID_BILLING_CYCLES[raw_cycle]

    if "status" in data and data["status"] is not None:
        raw_st = str(data["status"]).strip()
        matched_st = next(
            (s for s in VALID_FINANCE_STATUSES if s.lower() == raw_st.lower()),
            None,
        )
        if not matched_st:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Status '{raw_st}' tidak valid",
            )
        data["status"] = matched_st

    for key, val in data.items():
        if key in ("id", "kode_pembelian", "created_at") or val is None:
            continue
        if hasattr(row, key):
            setattr(row, key, val.strip() if isinstance(val, str) else val)

    # Rekalkulasi total_harga otomatis bila jumlah atau harga_satuan berubah
    if ("jumlah" in data or "harga_satuan" in data) and "total_harga" not in data:
        row.total_harga = row.jumlah * row.harga_satuan

    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return PurchasePublic.from_model(row)


@router.put("/{identifier}", response_model=PurchasePublic)
def update_purchase_put(
    identifier: str,
    payload: PurchaseUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> PurchasePublic:
    """Memperbarui data pembelian/invoice/tagihan (PUT)."""
    return _apply_purchase_update(identifier, payload, session)


@router.patch("/{identifier}", response_model=PurchasePublic)
def update_purchase_patch(
    identifier: str,
    payload: PurchaseUpdate,
    session: SessionDep,
    _: EditorUserDep,
) -> PurchasePublic:
    """Memperbarui sebagian data pembelian/invoice/tagihan (PATCH)."""
    return _apply_purchase_update(identifier, payload, session)


@router.post("/{identifier}/pay", response_model=PurchasePublic)
@router.post("/{identifier}/mark-paid", response_model=PurchasePublic, include_in_schema=False)
def mark_purchase_paid(
    identifier: str,
    session: SessionDep,
    _: EditorUserDep,
    payload: MarkPaidRequest | None = None,
) -> PurchasePublic:
    """Menandai invoice lunas atau memajukan jatuh tempo tagihan berulang ke periode berikutnya."""
    row = _find_purchase(session, identifier)
    req = payload or MarkPaidRequest()
    paid_date = req.tanggal_bayar or date.today()

    row.tanggal_bayar = paid_date
    if req.metode_pembayaran:
        row.metode_pembayaran = req.metode_pembayaran.strip()

    if row.is_recurring and req.advance_cycle and row.siklus_tagihan != "Sekali":
        base_due = row.tanggal_jatuh_tempo or paid_date
        row.tanggal_jatuh_tempo = advance_due_date(base_due, row.siklus_tagihan)
        row.status = "Belum Lunas"
    else:
        row.status = "Lunas"

    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return PurchasePublic.from_model(row)


@router.delete("/{identifier}")
def delete_purchase(
    identifier: str,
    session: SessionDep,
    _: AdminUserDep,
) -> dict[str, Any]:
    """Menghapus catatan pembelian/invoice (hanya Administrator)."""
    row = _find_purchase(session, identifier)
    deleted_code = row.kode_pembelian
    deleted_id = row.id
    session.delete(row)
    session.commit()
    return {"status": "ok", "id": deleted_id, "kode_pembelian": deleted_code}
