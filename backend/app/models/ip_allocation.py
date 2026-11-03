"""Model database untuk alokasi IP Address dan Virtual Machine (ip_allocations)."""

from typing import Any

from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class IPAllocation(TimestampMixin, SQLModel, table=True):
    """Tabel alokasi IP Address perangkat fisik dan Virtual Machine (VM)."""

    __tablename__: Any = "ip_allocations"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    ip_address: str = Field(index=True, max_length=45, nullable=False)
    ip_int: int = Field(
        sa_column=Column(BigInteger, index=True, nullable=False),
    )
    subnet: str = Field(default="255.255.255.0", max_length=45, nullable=False)
    gateway: str = Field(default="", max_length=45, nullable=False)

    nama_perangkat: str = Field(index=True, max_length=150, nullable=False)
    hostname: str = Field(default="", max_length=150, nullable=False)
    tipe: str = Field(default="Fisik", index=True, max_length=30, nullable=False)
    status: str = Field(default="Aktif", index=True, max_length=30, nullable=False)

    lokasi: str = Field(
        default="Head Office (Office Blok 14)",
        index=True,
        max_length=100,
        nullable=False,
    )
    id_aset: str | None = Field(default=None, index=True, max_length=30, nullable=True)

    # Atribut khusus Virtual Machine (VM)
    is_vm: bool = Field(default=False, index=True, nullable=False)
    host_name: str = Field(default="", max_length=150, nullable=False)
    id_aset_host: str | None = Field(default=None, index=True, max_length=30, nullable=True)
    os: str = Field(default="", max_length=80, nullable=False)
    vcpu: int = Field(default=0, nullable=False)
    ram: str = Field(default="", max_length=50, nullable=False)
    storage: str = Field(default="", max_length=80, nullable=False)
    port_servis: str = Field(default="", max_length=120, nullable=False)

    mac_address: str = Field(default="", max_length=50, nullable=False)
    pengguna: str = Field(default="", max_length=100, nullable=False)
    keterangan: str = Field(default="", max_length=500, nullable=False)

