"""Skema Pydantic untuk validasi dan kontrak respons modul IP & VM."""

import ipaddress
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.master_data import LOCATION_ALIASES, LOCATIONS
from app.models.ip_allocation import IPAllocation

VALID_IP_STATUSES = {"Aktif", "Digunakan", "Bebas", "Tersedia", "Reserved", "Konflik", "Nonaktif"}


def parse_and_validate_ipv4(ip_str: str) -> tuple[str, int]:
    """Memvalidasi string IPv4 dan mengembalikan (ip_canonical, ip_int)."""
    cleaned = ip_str.strip()
    if "/" in cleaned:
        cleaned = cleaned.split("/", 1)[0].strip()
    try:
        addr = ipaddress.IPv4Address(cleaned)
    except (ipaddress.AddressValueError, ValueError) as exc:
        raise ValueError(f"Format alamat IPv4 '{ip_str}' tidak valid") from exc
    return str(addr), int(addr)


def _normalize_location_optional(val: str) -> str:
    cleaned = val.strip()
    if not cleaned:
        return "Head Office (Office Blok 14)"
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc
    if cleaned.lower() in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned.lower()]
    return cleaned


class IPAllocationCreate(BaseModel):
    """Payload penambahan alokasi IP atau VM baru."""

    model_config = ConfigDict(extra="allow")

    ip_address: str = Field(min_length=7, max_length=45)
    subnet: str = Field(default="255.255.255.0", max_length=45)
    gateway: str = Field(default="", max_length=45)

    nama_perangkat: str = Field(default="", max_length=150)
    nama: str | None = Field(default=None, max_length=150)
    hostname: str = Field(default="", max_length=150)
    nama_vm: str | None = Field(default=None, max_length=150)
    tipe: str = Field(default="Fisik", max_length=30)
    jenis: str | None = Field(default=None, max_length=30)
    grup: str | None = Field(default="", max_length=50)
    kategori: str | None = Field(default=None, max_length=30)
    status: str = Field(default="Aktif", max_length=30)

    lokasi: str = Field(default="Head Office (Office Blok 14)", max_length=100)
    id_aset: str | None = Field(default=None, max_length=30)
    asset_id: str | None = Field(default=None, max_length=30)

    is_vm: bool | None = Field(default=None)
    host_name: str = Field(default="", max_length=150)
    host: str | None = Field(default=None, max_length=150)
    id_aset_host: str | None = Field(default=None, max_length=30)
    host_asset_id: str | None = Field(default=None, max_length=30)
    allow_orphan_vm: bool = Field(default=False)

    os: str = Field(default="", max_length=80)
    vcpu: int = Field(default=0, ge=0)
    ram: str = Field(default="", max_length=50)
    storage: str = Field(default="", max_length=80)
    port_servis: str = Field(default="", max_length=120)

    mac_address: str = Field(default="", max_length=50)
    pengguna: str = Field(default="", max_length=100)
    penanggung_jawab: str | None = Field(default=None, max_length=100)
    keterangan: str = Field(default="", max_length=500)
    fungsi: str | None = Field(default=None, max_length=500)
    catatan: str | None = Field(default=None, max_length=500)

    @field_validator("ip_address")
    @classmethod
    def _validate_ip(cls, v: str) -> str:
        canonical, _ = parse_and_validate_ipv4(v)
        return canonical

    @field_validator("lokasi")
    @classmethod
    def _validate_loc(cls, v: str) -> str:
        return _normalize_location_optional(v)

    @model_validator(mode="after")
    def _normalize_and_validate_vm(self) -> "IPAllocationCreate":
        if not self.nama_perangkat:
            if self.nama:
                self.nama_perangkat = self.nama.strip()
            elif self.nama_vm:
                self.nama_perangkat = self.nama_vm.strip()
            elif self.hostname:
                self.nama_perangkat = self.hostname.strip()
        self.nama_perangkat = self.nama_perangkat.strip()
        if not self.nama_perangkat:
            raise ValueError("Nama perangkat atau VM wajib diisi")

        if not self.hostname:
            self.hostname = self.nama_perangkat

        if self.jenis and self.tipe == "Fisik":
            self.tipe = self.jenis.strip()
        elif self.kategori and self.tipe == "Fisik":
            self.tipe = self.kategori.strip()

        if self.is_vm is None:
            self.is_vm = self.tipe.strip().upper() == "VM" or (
                bool(self.grup) and "vm" in self.grup.lower()
            )
        elif self.is_vm:
            self.tipe = "VM"

        if self.is_vm:
            self.tipe = "VM"
            self.jenis = "VM"
            if not self.grup:
                self.grup = "Addon (VM)"
        else:
            self.tipe = "Fisik"
            self.jenis = "Fisik"
            self.is_vm = False
            self.id_aset_host = None
            self.host_name = ""
            if not self.grup:
                self.grup = "Operasional"

        # Turunkan subnet /24 otomatis dari 3 oktet pertama IPv4
        parts = self.ip_address.strip().split(".")
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            self.subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

        if not self.host_name and self.host:
            self.host_name = self.host.strip()
        self.host_name = self.host_name.strip()

        if not self.id_aset_host and self.host_asset_id:
            self.id_aset_host = self.host_asset_id

        if self.id_aset_host:
            cleaned_host_id = self.id_aset_host.strip().upper()
            self.id_aset_host = cleaned_host_id if cleaned_host_id not in ("", "-", "—") else None

        if not self.id_aset and self.asset_id:
            self.id_aset = self.asset_id

        if self.id_aset:
            cleaned_asset_id = self.id_aset.strip().upper()
            self.id_aset = cleaned_asset_id if cleaned_asset_id not in ("", "-", "—") else None

        if not self.pengguna and self.penanggung_jawab:
            self.pengguna = self.penanggung_jawab.strip()
        if not self.keterangan and self.fungsi:
            self.keterangan = self.fungsi.strip()
        elif not self.keterangan and self.catatan:
            self.keterangan = self.catatan.strip()

        # Validasi status
        matched_status = next(
            (s for s in VALID_IP_STATUSES if s.lower() == self.status.strip().lower()),
            None,
        )
        if not matched_status:
            raise ValueError(f"Status IP '{self.status}' tidak valid")
        self.status = matched_status

        # Bila entri adalah VM dan tidak sengaja diizinkan orphan, wajib punya host
        if self.is_vm and not self.allow_orphan_vm and not self.host_name and not self.id_aset_host:
            raise ValueError("VM wajib memiliki host induk (host_name atau id_aset_host)")

        return self


class IPAllocationUpdate(BaseModel):
    """Payload pembaruan alokasi IP / VM."""

    model_config = ConfigDict(extra="allow")

    ip_address: str | None = Field(default=None, max_length=45)
    subnet: str | None = None
    gateway: str | None = None
    nama_perangkat: str | None = None
    nama: str | None = None
    hostname: str | None = None
    tipe: str | None = None
    jenis: str | None = None
    grup: str | None = None
    status: str | None = None
    lokasi: str | None = None
    id_aset: str | None = None
    asset_id: str | None = None

    is_vm: bool | None = None
    host_name: str | None = None
    host: str | None = None
    id_aset_host: str | None = None
    host_asset_id: str | None = None

    os: str | None = None
    vcpu: int | None = Field(default=None, ge=0)
    ram: str | None = None
    storage: str | None = None
    port_servis: str | None = None
    mac_address: str | None = None
    pengguna: str | None = None
    keterangan: str | None = None
    fungsi: str | None = None

    @field_validator("ip_address")
    @classmethod
    def _validate_ip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        canonical, _ = parse_and_validate_ipv4(v)
        return canonical


def _compute_cidr_subnet(ip_address: str, raw_subnet: str) -> str:
    """Mengembalikan format subnet CIDR /24 untuk UI frontend (misal 192.168.1.0/24)."""
    cleaned = (raw_subnet or "").strip()
    if "/" in cleaned:
        return cleaned
    parts = (ip_address or "").strip().split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    return cleaned or "192.168.1.0/24"


class IPAllocationPublic(BaseModel):
    """Representasi JSON alokasi IP / VM yang dikembalikan ke frontend."""

    model_config = ConfigDict(extra="allow")

    id: int
    ip_address: str
    ip_int: int
    subnet: str
    gateway: str
    nama_perangkat: str
    nama: str = ""
    hostname: str
    nama_vm: str
    tipe: str
    jenis: str = "Fisik"
    grup: str = "Operasional"
    status: str
    lokasi: str
    id_aset: str | None
    asset_id: str = ""
    sub_label: str = ""

    is_vm: bool
    host_name: str
    host: str
    id_aset_host: str | None
    host_asset_id: str = ""
    host_label: str = "—"
    vm_tanpa_host: bool
    is_orphan_vm: bool
    konflik_ip: bool
    is_conflict: bool = False

    os: str
    vcpu: int
    ram: str
    storage: str
    port_servis: str
    mac_address: str
    pengguna: str
    keterangan: str
    fungsi: str = ""

    @classmethod
    def from_model(
        cls,
        row: IPAllocation,
        *,
        is_orphan: bool = False,
        is_conflict: bool = False,
    ) -> "IPAllocationPublic":
        host_display = row.host_name or (row.id_aset_host or "-")
        jenis_val = "VM" if row.is_vm else "Fisik"
        grup_val = "Addon (VM)" if row.is_vm else "Operasional"
        asset_id_str = (row.id_aset or "").strip()
        host_asset_id_str = (row.id_aset_host or "").strip()
        ket_raw = (row.keterangan or "").strip()
        has_kendala = bool(ket_raw and ket_raw not in ("—", "-"))
        if has_kendala:
            sub_lbl = "● Ada kendala (lihat keterangan)"
        elif row.is_vm:
            sub_lbl = f"Host: {host_asset_id_str}" if host_asset_id_str else "Tanpa host"
        else:
            sub_lbl = f"Aset: {asset_id_str}" if asset_id_str else "Server / PC fisik"

        if row.is_vm:
            if is_orphan:
                host_lbl = "Tanpa host"
            elif host_asset_id_str and row.host_name:
                host_lbl = f"{host_asset_id_str} ({row.host_name})"
            else:
                host_lbl = host_asset_id_str or row.host_name or "—"
        else:
            host_lbl = "—"

        fungsi_val = (row.keterangan or row.port_servis or "Operasional").strip()
        subnet_cidr = _compute_cidr_subnet(row.ip_address, row.subnet)

        return cls(
            id=row.id or 0,
            ip_address=row.ip_address,
            ip_int=row.ip_int,
            subnet=subnet_cidr,
            gateway=row.gateway,
            nama_perangkat=row.nama_perangkat,
            nama=row.nama_perangkat,
            hostname=row.hostname or row.nama_perangkat,
            nama_vm=row.nama_perangkat if row.is_vm else "",
            tipe=row.tipe,
            jenis=jenis_val,
            grup=grup_val,
            status="Konflik" if is_conflict else row.status,
            lokasi=row.lokasi,
            id_aset=row.id_aset,
            asset_id=asset_id_str,
            sub_label=sub_lbl,
            is_vm=row.is_vm,
            host_name=row.host_name,
            host=host_display,
            id_aset_host=row.id_aset_host,
            host_asset_id=host_asset_id_str,
            host_label=host_lbl,
            vm_tanpa_host=is_orphan,
            is_orphan_vm=is_orphan,
            konflik_ip=is_conflict,
            is_conflict=is_conflict,
            os=row.os or "—",
            vcpu=row.vcpu,
            ram=row.ram,
            storage=row.storage,
            port_servis=row.port_servis,
            mac_address=row.mac_address,
            pengguna=row.pengguna,
            keterangan=row.keterangan,
            fungsi=fungsi_val,
        )


class IPAllocationPageResponse(BaseModel):
    """Respons daftar IP & VM berhalaman sesuai kontrak frontend."""

    items: list[IPAllocationPublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, int] = {}
    conflict_banner: str = ""
    subnet_options: list[str] = ["Semua"]
    host_options: list[str] = ["Semua"]
    server_asset_ids: list[str] = ["—"]
    os_suggestions: list[str] = []
