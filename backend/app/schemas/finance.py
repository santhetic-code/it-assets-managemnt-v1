"""Skema Pydantic dan utilitas siklus tagihan untuk modul Keuangan (B5)."""

import calendar
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.master_data import LOCATION_ALIASES, LOCATIONS
from app.models.finance import Purchase

VALID_FINANCE_STATUSES = {
    "Lunas",
    "Belum Lunas",
    "Menunggu",
    "Pending",
    "Jatuh Tempo",
    "Terlambat",
    "Dibatalkan",
}

VALID_BILLING_CYCLES = {
    "Sekali": "Sekali",
    "sekali": "Sekali",
    "Mingguan": "Mingguan",
    "mingguan": "Mingguan",
    "weekly": "Mingguan",
    "Bulanan": "Bulanan",
    "bulanan": "Bulanan",
    "monthly": "Bulanan",
    "1 bulan": "Bulanan",
    "Triwulan": "Triwulan",
    "triwulan": "Triwulan",
    "quarterly": "Triwulan",
    "3 bulan": "Triwulan",
    "6 bulan": "Triwulan",
    "Tahunan": "Tahunan",
    "tahunan": "Tahunan",
    "yearly": "Tahunan",
    "1 tahun": "Tahunan",
}


def _add_months(source_date: date, months: int) -> date:
    """Menambahkan jumlah bulan ke objek date dengan aman pada akhir bulan."""
    month_index = source_date.month - 1 + months
    year = source_date.year + month_index // 12
    month = month_index % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(source_date.day, max_day))


def advance_due_date(current_due: date, siklus: str) -> date:
    """Memajukan tanggal jatuh tempo ke periode berikutnya sesuai siklus tagihan."""
    clean = VALID_BILLING_CYCLES.get(siklus.strip(), "Bulanan")
    if clean == "Mingguan":
        return current_due + timedelta(days=7)
    if clean == "Bulanan":
        return _add_months(current_due, 1)
    if clean == "Triwulan":
        return _add_months(current_due, 3)
    if clean == "Tahunan":
        return _add_months(current_due, 12)
    return current_due


def _normalize_location(val: str) -> str:
    cleaned = val.strip()
    if not cleaned:
        return "Head Office (Office Blok 14)"
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc
    if cleaned.lower() in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned.lower()]
    return cleaned


class PurchaseCreate(BaseModel):
    """Payload penambahan data pembelian, invoice, atau tagihan berulang."""

    model_config = ConfigDict(extra="allow")

    kode_pembelian: str | None = Field(default=None, max_length=30)
    id_pembelian: str | None = Field(default=None, max_length=30)
    nomor_invoice: str = Field(default="", max_length=80)
    no_invoice: str | None = Field(default=None, max_length=80)

    nama_item: str = Field(default="", max_length=150)
    nama_barang: str | None = Field(default=None, max_length=150)
    produk: str | None = Field(default=None, max_length=150)
    nama: str | None = Field(default=None, max_length=150)
    deskripsi: str | None = Field(default=None, max_length=150)
    kategori: str = Field(default="PC", max_length=50)
    jenis_transaksi: str = Field(default="Pembelian", max_length=40)
    vendor: str = Field(default="", max_length=120)
    toko: str | None = Field(default=None, max_length=120)
    nama_toko: str | None = Field(default=None, max_length=120)
    lokasi: str = Field(default="Head Office (Office Blok 14)", max_length=100)

    jumlah: int = Field(default=1, ge=1)
    qty: int | None = Field(default=None, ge=1)
    pcs: int | None = Field(default=None, ge=1)
    satuan: str = Field(default="Unit", max_length=30)
    harga_satuan: int = Field(default=0, ge=0)
    harga: int | None = Field(default=None, ge=0)
    nominal: int | None = Field(default=None, ge=0)
    total_harga: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)

    tanggal_beli: date | None = Field(default=None)
    tanggal: date | None = Field(default=None)
    tanggal_jatuh_tempo: date | None = Field(default=None)
    jatuh_tempo: date | None = Field(default=None)
    tanggal_bayar: date | None = Field(default=None)

    status: str = Field(default="Lunas", max_length=40)
    metode_pembayaran: str = Field(default="Transfer", max_length=50)

    is_recurring: bool | None = Field(default=None)
    siklus_tagihan: str = Field(default="Sekali", max_length=30)
    periode: str | None = Field(default=None, max_length=30)

    id_aset: str | None = Field(default=None, max_length=30)
    penanggung_jawab: str = Field(default="", max_length=100)
    dibeli_oleh: str | None = Field(default=None, max_length=100)
    pembayar: str | None = Field(default=None, max_length=100)
    keterangan: str = Field(default="", max_length=500)
    link_marketplace: str | None = Field(default=None, max_length=500)
    catatan: str | None = Field(default=None, max_length=500)

    @field_validator("lokasi")
    @classmethod
    def _check_loc(cls, v: str) -> str:
        return _normalize_location(v)

    @model_validator(mode="after")
    def _normalize_fields_and_totals(self) -> "PurchaseCreate":
        if not self.kode_pembelian and self.id_pembelian:
            self.kode_pembelian = self.id_pembelian.strip()

        if not self.nomor_invoice and self.no_invoice:
            self.nomor_invoice = self.no_invoice.strip()

        if not self.nama_item:
            if self.produk:
                self.nama_item = self.produk.strip()
            elif self.nama:
                self.nama_item = self.nama.strip()
            elif self.nama_barang:
                self.nama_item = self.nama_barang.strip()
            elif self.deskripsi:
                self.nama_item = self.deskripsi.strip()
        self.nama_item = self.nama_item.strip()
        if not self.nama_item:
            raise ValueError("Nama barang/item wajib diisi")

        if not self.vendor:
            if self.nama_toko:
                self.vendor = self.nama_toko.strip()
            elif self.toko:
                self.vendor = self.toko.strip()
        self.vendor = self.vendor.strip()

        if self.pcs is not None and self.jumlah == 1:
            self.jumlah = self.pcs
        elif self.qty is not None and self.jumlah == 1:
            self.jumlah = self.qty
        if self.harga is not None and self.harga_satuan == 0:
            self.harga_satuan = self.harga
        elif self.nominal is not None and self.harga_satuan == 0:
            self.harga_satuan = self.nominal

        if self.total is not None and (self.total_harga is None or self.total_harga == 0):
            self.total_harga = self.total
        elif self.total_harga is None or self.total_harga == 0:
            self.total_harga = self.jumlah * self.harga_satuan

        if self.tanggal_beli is None:
            self.tanggal_beli = self.tanggal or date.today()

        if self.tanggal_jatuh_tempo is None and self.jatuh_tempo is not None:
            self.tanggal_jatuh_tempo = self.jatuh_tempo

        if self.periode and self.siklus_tagihan == "Sekali":
            self.siklus_tagihan = self.periode

        if self.siklus_tagihan not in VALID_BILLING_CYCLES:
            raise ValueError(f"Siklus tagihan '{self.siklus_tagihan}' tidak valid")
        self.siklus_tagihan = VALID_BILLING_CYCLES[self.siklus_tagihan]

        if self.is_recurring is None:
            self.is_recurring = (
                self.siklus_tagihan != "Sekali"
                or self.jenis_transaksi.strip().lower() in ("tagihan berulang", "langganan")
            )
        elif self.is_recurring and self.siklus_tagihan == "Sekali":
            self.siklus_tagihan = "Bulanan"

        if self.is_recurring:
            self.jenis_transaksi = "Tagihan Berulang"
            if self.tanggal_jatuh_tempo is None:
                self.tanggal_jatuh_tempo = advance_due_date(
                    self.tanggal_beli,
                    self.siklus_tagihan,
                )

        matched_st = next(
            (s for s in VALID_FINANCE_STATUSES if s.lower() == self.status.strip().lower()),
            None,
        )
        if not matched_st:
            raise ValueError(f"Status keuangan '{self.status}' tidak valid")
        self.status = matched_st

        if self.status == "Lunas" and self.tanggal_bayar is None and not self.is_recurring:
            self.tanggal_bayar = self.tanggal_beli

        if not self.penanggung_jawab:
            if self.dibeli_oleh:
                self.penanggung_jawab = self.dibeli_oleh.strip()
            elif self.pembayar:
                self.penanggung_jawab = self.pembayar.strip()

        if not self.keterangan:
            if self.link_marketplace:
                self.keterangan = self.link_marketplace.strip()
            elif self.catatan:
                self.keterangan = self.catatan.strip()

        if self.id_aset:
            cleaned_id = self.id_aset.strip().upper()
            self.id_aset = cleaned_id if cleaned_id not in ("", "-", "—") else None

        return self


class PurchaseUpdate(BaseModel):
    """Payload pembaruan data pembelian, invoice, atau tagihan berulang."""

    model_config = ConfigDict(extra="allow")

    nomor_invoice: str | None = None
    no_invoice: str | None = None
    nama_item: str | None = None
    nama_barang: str | None = None
    produk: str | None = None
    nama: str | None = None
    kategori: str | None = None
    jenis_transaksi: str | None = None
    vendor: str | None = None
    nama_toko: str | None = None
    lokasi: str | None = None
    jumlah: int | None = Field(default=None, ge=1)
    pcs: int | None = Field(default=None, ge=1)
    satuan: str | None = None
    harga_satuan: int | None = Field(default=None, ge=0)
    harga: int | None = Field(default=None, ge=0)
    nominal: int | None = Field(default=None, ge=0)
    total_harga: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)
    tanggal_beli: date | None = None
    tanggal: date | None = None
    tanggal_jatuh_tempo: date | None = None
    jatuh_tempo: date | None = None
    tanggal_bayar: date | None = None
    status: str | None = None
    metode_pembayaran: str | None = None
    is_recurring: bool | None = None
    siklus_tagihan: str | None = None
    periode: str | None = None
    id_aset: str | None = None
    penanggung_jawab: str | None = None
    dibeli_oleh: str | None = None
    pembayar: str | None = None
    keterangan: str | None = None
    link_marketplace: str | None = None


class MarkPaidRequest(BaseModel):
    """Payload opsional saat menandai invoice / tagihan berulang sebagai Lunas."""

    tanggal_bayar: date | None = None
    metode_pembayaran: str | None = None
    advance_cycle: bool = True


def _extract_domain_chip(raw_url: str) -> str:
    low = (raw_url or "").lower()
    if "tokopedia" in low:
        return "Tokopedia"
    if "shopee" in low:
        return "Shopee"
    if "blibli" in low:
        return "Blibli"
    if "http" in low:
        return "Web"
    return "Offline"


class PurchasePublic(BaseModel):
    """Representasi JSON item Pembelian / Invoice / Tagihan Berulang untuk frontend."""

    id: int
    no: int = 1
    kode_pembelian: str
    id_pembelian: str
    nomor_invoice: str
    no_invoice: str
    nama_item: str
    nama_barang: str
    produk: str = ""
    nama: str = ""
    kategori: str
    jenis_transaksi: str
    vendor: str
    toko: str
    nama_toko: str = ""
    lokasi: str

    jumlah: int
    qty: int
    pcs: int = 1
    satuan: str
    harga_satuan: int
    harga: int = 0
    nominal: int = 0
    total_harga: int
    total: int = 0
    total_display: str = ""
    nominal_display: str = ""

    tanggal_beli: str
    tanggal: str
    tanggal_jatuh_tempo: str | None
    jatuh_tempo: str = ""
    tanggal_bayar: str | None

    status: str
    status_efektif: str
    status_label: str = ""
    status_variant: str = "info"
    is_overdue: bool
    is_due_soon: bool
    hari_menuju_jatuh_tempo: int | None
    pengingat_hari: int = 7
    pengingat_display: str = "H-7"

    metode_pembayaran: str
    is_recurring: bool
    aktif: bool = True
    siklus_tagihan: str
    periode: str = "Sekali"
    id_aset: str | None
    aset_status: str = "Belum didaftarkan"
    registered_count: int = 0
    registered_assets: list[str] = Field(default_factory=list)
    penanggung_jawab: str
    dibeli_oleh: str = "Ridho"
    pembayar: str = "Finance"
    keterangan: str
    link_marketplace: str = ""
    domain_chip: str = "Offline"

    berkas: str = "Ada PDF"
    terkait_tipe: str = "pembelian"
    terkait_id: str = ""
    terkait_label: str = "Belum Ditautkan"

    @classmethod
    def from_model(
        cls,
        row: Purchase,
        today: date | None = None,
        seq_no: int | None = None,
    ) -> "PurchasePublic":
        ref_today = today or date.today()
        due = row.tanggal_jatuh_tempo
        days_left: int | None = None
        is_overdue = False
        is_due_soon = False

        unpaid = row.status.lower() not in ("lunas", "dibatalkan")
        if due is not None:
            days_left = (due - ref_today).days
            if unpaid and days_left < 0:
                is_overdue = True
            elif unpaid and 0 <= days_left <= 7:
                is_due_soon = True

        effective_status = "Jatuh Tempo" if is_overdue else row.status
        tgl_beli = row.tanggal_beli.isoformat()
        due_str = due.isoformat() if due else tgl_beli

        if is_overdue:
            st_lbl = f"Terlambat ({abs(days_left or 0)}h)"
            st_var = "danger"
        elif is_due_soon:
            st_lbl = f"Segera (H-{days_left or 0})"
            st_var = "warning"
        elif row.status.lower() == "lunas":
            st_lbl = "Lunas"
            st_var = "success"
        else:
            st_lbl = "Aktif" if row.is_recurring else row.status
            st_var = "info"

        total_rp = f"Rp {row.total_harga:,}".replace(",", ".")
        link_val = row.keterangan if "http" in (row.keterangan or "").lower() else ""
        domain_val = _extract_domain_chip(link_val)
        raw_id_aset = (row.id_aset or "").strip()
        if raw_id_aset.upper() == "BUKAN-ASET" or row.is_recurring:
            reg_assets: list[str] = []
            reg_count = 0
            aset_st = "Bukan aset"
        elif raw_id_aset:
            reg_assets = [x.strip() for x in raw_id_aset.split(",") if x.strip()]
            reg_count = len(reg_assets)
            if reg_count >= row.jumlah:
                aset_st = f"Terdaftar ({reg_count} aset)"
            else:
                aset_st = f"Sebagian ({reg_count}/{row.jumlah})"
        else:
            reg_assets = []
            reg_count = 0
            aset_st = "Belum didaftarkan"
        inv_code = row.nomor_invoice if row.nomor_invoice else f"INV-{row.kode_pembelian}"

        return cls(
            id=row.id or 0,
            no=seq_no or (row.id or 1),
            kode_pembelian=row.kode_pembelian,
            id_pembelian=row.kode_pembelian,
            nomor_invoice=row.nomor_invoice or "-",
            no_invoice=inv_code,
            nama_item=row.nama_item,
            nama_barang=row.nama_item,
            produk=row.nama_item,
            nama=row.nama_item,
            kategori=row.kategori,
            jenis_transaksi=row.jenis_transaksi,
            vendor=row.vendor or "-",
            toko=row.vendor or "-",
            nama_toko=row.vendor or "-",
            lokasi=row.lokasi,
            jumlah=row.jumlah,
            qty=row.jumlah,
            pcs=row.jumlah,
            satuan=row.satuan,
            harga_satuan=row.harga_satuan,
            harga=row.harga_satuan,
            nominal=row.total_harga,
            total_harga=row.total_harga,
            total=row.total_harga,
            total_display=total_rp,
            nominal_display=total_rp,
            tanggal_beli=tgl_beli,
            tanggal=tgl_beli,
            tanggal_jatuh_tempo=due.isoformat() if due else None,
            jatuh_tempo=due_str,
            tanggal_bayar=row.tanggal_bayar.isoformat() if row.tanggal_bayar else None,
            status=row.status,
            status_efektif=effective_status,
            status_label=st_lbl,
            status_variant=st_var,
            is_overdue=is_overdue,
            is_due_soon=is_due_soon,
            hari_menuju_jatuh_tempo=days_left,
            pengingat_hari=7,
            pengingat_display="H-7",
            metode_pembayaran=row.metode_pembayaran,
            is_recurring=row.is_recurring,
            aktif=row.status.lower() != "dibatalkan",
            siklus_tagihan=row.siklus_tagihan,
            periode=row.siklus_tagihan,
            id_aset=row.id_aset,
            aset_status=aset_st,
            registered_count=reg_count,
            registered_assets=reg_assets,
            penanggung_jawab=row.penanggung_jawab or "Ridho",
            dibeli_oleh=row.penanggung_jawab or "Ridho",
            pembayar=row.penanggung_jawab or "Finance",
            keterangan=row.keterangan,
            link_marketplace=link_val,
            domain_chip=domain_val,
            berkas="Ada PDF",
            terkait_tipe="tagihan" if row.is_recurring else "pembelian",
            terkait_id=row.kode_pembelian,
            terkait_label=f"{row.kode_pembelian} · {row.nama_item[:24]}",
        )


class PurchasePageResponse(BaseModel):
    """Respons berhalaman untuk daftar Pembelian, Invoice, dan Tagihan Berulang."""

    items: list[PurchasePublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, Any]
