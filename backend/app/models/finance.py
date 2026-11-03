"""Model database untuk Pembelian, Invoice, dan Tagihan Berulang (purchases)."""

from datetime import date
from typing import Any

from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class Purchase(TimestampMixin, SQLModel, table=True):
    """Tabel rekap pembelian aset, invoice vendor, dan tagihan rutin berulang."""

    __tablename__: Any = "purchases"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    kode_pembelian: str = Field(index=True, unique=True, max_length=30, nullable=False)
    nomor_invoice: str = Field(default="", index=True, max_length=80, nullable=False)

    nama_item: str = Field(index=True, max_length=150, nullable=False)
    kategori: str = Field(default="PC", index=True, max_length=50, nullable=False)
    jenis_transaksi: str = Field(
        default="Pembelian",
        index=True,
        max_length=40,
        nullable=False,
    )
    vendor: str = Field(default="", index=True, max_length=120, nullable=False)
    lokasi: str = Field(
        default="Head Office (Office Blok 14)",
        index=True,
        max_length=100,
        nullable=False,
    )

    jumlah: int = Field(default=1, nullable=False)
    satuan: str = Field(default="Unit", max_length=30, nullable=False)
    harga_satuan: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
    )
    total_harga: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
    )

    tanggal_beli: date = Field(index=True, nullable=False)
    tanggal_jatuh_tempo: date | None = Field(default=None, index=True, nullable=True)
    tanggal_bayar: date | None = Field(default=None, nullable=True)

    status: str = Field(default="Lunas", index=True, max_length=40, nullable=False)
    metode_pembayaran: str = Field(default="Transfer", max_length=50, nullable=False)

    # Atribut Tagihan Berulang (Recurring Bills)
    is_recurring: bool = Field(default=False, index=True, nullable=False)
    siklus_tagihan: str = Field(default="Sekali", max_length=30, nullable=False)

    id_aset: str | None = Field(default=None, index=True, max_length=30, nullable=True)
    penanggung_jawab: str = Field(default="", max_length=100, nullable=False)
    keterangan: str = Field(default="", max_length=500, nullable=False)
