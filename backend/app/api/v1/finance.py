"""Endpoint CRUD Pembelian, Invoice, dan Tagihan Berulang (/api/v1/purchases)."""

import re
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, PageParamsDep, SessionDep
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
        1
        for i in public_items
        if i.nomor_invoice != "-" or i.jenis_transaksi.lower() == "invoice"
    )
    lunas_count = sum(1 for i in public_items if i.status.lower() == "lunas")
    unpaid_count = sum(
        1 for i in public_items if i.status.lower() not in ("lunas", "dibatalkan")
    )
    overdue_count = sum(1 for i in public_items if i.is_overdue)
    due_soon_count = sum(1 for i in public_items if i.is_due_soon)

    total_pengeluaran = sum(
        i.total_harga for i in public_items if i.status.lower() != "dibatalkan"
    )
    total_lunas = sum(
        i.total_harga for i in public_items if i.status.lower() == "lunas"
    )
    total_belum_lunas = sum(
        i.total_harga
        for i in public_items
        if i.status.lower() not in ("lunas", "dibatalkan")
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

    summary: dict[str, Any] = {
        "total_transaksi": total_count,
        "total_pembelian": pembelian_count,
        "total_invoice": invoice_count,
        "total_tagihan_berulang": recurring_count,
        "total_pengeluaran": total_pengeluaran,
        "total_nilai": total_pengeluaran,
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
            select(Purchase).where(
                func.lower(col(Purchase.kode_pembelian)) == cleaned.lower()
            )
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
    is_recurring: bool | None = Query(default=None),
    overdue_only: bool = Query(default=False),
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
    all_public = [PurchasePublic.from_model(r, today=today) for r in all_rows]

    filtered = all_public

    keyword = (search or q or "").strip().lower()
    if keyword:
        filtered = [
            i
            for i in filtered
            if keyword in i.kode_pembelian.lower()
            or keyword in i.nomor_invoice.lower()
            or keyword in i.nama_item.lower()
            or keyword in i.vendor.lower()
            or keyword in i.kategori.lower()
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
                if i.nomor_invoice != "-" or i.jenis_transaksi.lower() == "invoice"
            ]
        elif active_tab == "belum lunas":
            filtered = [
                i for i in filtered if i.status.lower() not in ("lunas", "dibatalkan")
            ]
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

    if status_filter and status_filter.strip().lower() not in ("semua", "all", ""):
        st_clean = status_filter.strip().lower()
        if st_clean in ("jatuh tempo", "overdue"):
            filtered = [i for i in filtered if i.is_overdue]
        else:
            filtered = [
                i
                for i in filtered
                if i.status.lower() == st_clean or i.status_efektif.lower() == st_clean
            ]

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
            select(Purchase).where(
                func.lower(col(Purchase.kode_pembelian)) == final_code.lower()
            )
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


def _apply_purchase_update(
    identifier: str,
    payload: PurchaseUpdate,
    session: Session,
) -> PurchasePublic:
    row = _find_purchase(session, identifier)
    data = payload.model_dump(exclude_unset=True)

    if "nama_barang" in data and "nama_item" not in data:
        data["nama_item"] = data.pop("nama_barang")
    else:
        data.pop("nama_barang", None)

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
