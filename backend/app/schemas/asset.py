"""Skema Pydantic untuk request, validasi, dan response modul Aset."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.master_data import (
    ASSET_CONDITIONS,
    ASSET_STATUSES,
    CATEGORY_PREFIXES,
    LOCATION_ALIASES,
    LOCATIONS,
)
from app.models.asset import Asset

FORBIDDEN_FIELDS = {
    "power_supply",
    "psu",
    "casing",
    "cassing",
    "vendor",
    "nilai_perolehan",
    "batas_garansi",
}


def _clean_serial_number(val: str | None) -> str | None:
    """Menormalisasi SN: string kosong atau '-' dianggap None (tidak punya SN)."""
    if val is None:
        return None
    cleaned = val.strip()
    if not cleaned or cleaned in ("-", "N/A", "n/a", "Tidak Ada"):
        return None
    return cleaned


def _validate_category(val: str) -> str:
    cleaned = val.strip()
    if not cleaned:
        raise ValueError("Kategori aset wajib diisi")
    valid_map = {k.lower(): k for k in CATEGORY_PREFIXES}
    if cleaned.lower() not in valid_map:
        raise ValueError(f"Kategori '{cleaned}' tidak valid")
    return valid_map[cleaned.lower()]


def _validate_location(val: str) -> str:
    cleaned = val.strip()
    if not cleaned:
        raise ValueError("Lokasi aset wajib diisi")
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc
    if cleaned.lower() in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned.lower()]
    raise ValueError(f"Lokasi '{cleaned}' tidak terdaftar di data master")


def _validate_status(val: str) -> str:
    cleaned = val.strip()
    for st in ASSET_STATUSES:
        if st.lower() == cleaned.lower():
            return st
    raise ValueError(f"Status aset '{cleaned}' tidak valid")


_MONTH_SHORT_ID = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "Mei",
    6: "Jun",
    7: "Jul",
    8: "Agu",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Des",
}


def format_date_id(iso_date: str | None) -> str:
    """Konversi 'YYYY-MM-DD' menjadi 'DD MMM YYYY' (mis. '10 Jan 2025')."""
    if not iso_date or not iso_date.strip() or iso_date.strip() in ("—", "-"):
        return "—"
    raw = iso_date.strip()
    parts = raw.split("-")
    if len(parts) != 3:
        return raw
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{day:02d} {_MONTH_SHORT_ID.get(month, str(month))} {year}"
    except ValueError:
        return raw


def _derive_asset_jenis(asset: Asset, extra: dict[str, Any]) -> str:
    explicit = str(extra.get("jenis") or "").strip()
    if explicit in ("Operasional", "Server", "Backup"):
        return explicit
    if (
        asset.status.strip().lower() in ("backup", "cadangan")
        or "BACKUP" in asset.nama_aset.upper()
    ):
        return "Backup"
    if asset.kategori.strip().lower() == "server":
        return "Server"
    return "Operasional"


class AssetCreate(BaseModel):
    """Payload pembuatan aset baru."""

    model_config = ConfigDict(extra="allow")

    id_aset: str | None = Field(default=None, max_length=30)
    nama_aset: str = Field(min_length=1, max_length=150)
    kategori: str = Field(min_length=1, max_length=50)
    merek: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    sn_pid: str | None = Field(default=None, max_length=100)
    kepemilikan: str = Field(default="XML", max_length=50)
    lokasi: str = Field(min_length=1, max_length=100)
    detail_lokasi: str = Field(default="", max_length=150)
    ruangan: str | None = Field(default=None, max_length=150)
    penanggung_jawab: str = Field(default="", max_length=100)
    pengguna: str | None = Field(default=None, max_length=100)
    digunakan_oleh: str | None = Field(default=None, max_length=100)
    status: str = Field(default="Aktif", max_length=40)
    kondisi: str = Field(default="Baik", max_length=40)
    tanggal_masuk: date | None = Field(default=None)
    tanggal_masuk_gudang: date | None = Field(default=None)
    tanggal_keluar_gudang: str | None = Field(default=None)
    attributes: dict[str, Any] | None = Field(default=None)

    processor: str = Field(default="", max_length=120)
    motherboard: str = Field(default="", max_length=120)
    ram: str = Field(default="", max_length=80)
    storage: str = Field(default="", max_length=120)
    gpu: str = Field(default="", max_length=120)
    os: str = Field(default="", max_length=80)
    watt: int = Field(default=0, ge=0)

    ukuran_layar: str = Field(default="", max_length=50)
    resolusi: str = Field(default="", max_length=50)
    panel: str = Field(default="", max_length=50)
    port_display: str = Field(default="", max_length=100)

    kapasitas_va: int = Field(default=0, ge=0)
    kapasitas_watt: int = Field(default=0, ge=0)
    baterai: str = Field(default="", max_length=120)
    jumlah_baterai: int = Field(default=0, ge=0)
    beban_perangkat: str = Field(default="", max_length=255)

    ip_address: str = Field(default="", max_length=50)
    mac_address: str = Field(default="", max_length=50)
    koneksi: str = Field(default="", max_length=80)
    catatan: str = Field(default="", max_length=500)

    @field_validator("tanggal_masuk", "tanggal_masuk_gudang", mode="before")
    @classmethod
    def _empty_date_to_none(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("nama_aset")
    @classmethod
    def _check_nama(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Nama aset tidak boleh kosong")
        return cleaned

    @field_validator("kategori")
    @classmethod
    def _check_kategori(cls, v: str) -> str:
        return _validate_category(v)

    @field_validator("lokasi")
    @classmethod
    def _check_lokasi(cls, v: str) -> str:
        return _validate_location(v)

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        return _validate_status(v)

    @field_validator("serial_number", mode="before")
    @classmethod
    def _normalize_sn(cls, v: Any) -> str | None:
        return _clean_serial_number(str(v)) if v is not None else None

    @model_validator(mode="after")
    def _sync_aliases_and_strip_forbidden(self) -> "AssetCreate":
        if self.serial_number is None and self.sn_pid:
            self.serial_number = _clean_serial_number(self.sn_pid)
        if not self.detail_lokasi and self.ruangan:
            self.detail_lokasi = self.ruangan.strip()
        if not self.penanggung_jawab:
            if self.digunakan_oleh:
                self.penanggung_jawab = self.digunakan_oleh.strip()
            elif self.pengguna:
                self.penanggung_jawab = self.pengguna.strip()
        if self.tanggal_masuk is None and self.tanggal_masuk_gudang is not None:
            self.tanggal_masuk = self.tanggal_masuk_gudang
        if self.kondisi:
            matched = next(
                (c for c in ASSET_CONDITIONS if c.lower() == self.kondisi.strip().lower()),
                None,
            )
            if matched:
                self.kondisi = matched

        attrs = self.attributes or {}
        if attrs:
            if not self.processor and attrs.get("cpu"):
                self.processor = str(attrs["cpu"]).strip()
            if not self.motherboard and attrs.get("mainboard"):
                self.motherboard = str(attrs["mainboard"]).strip()
            if not self.ram and attrs.get("ram"):
                self.ram = str(attrs["ram"]).strip()
            if not self.storage and attrs.get("hdd_ssd"):
                self.storage = str(attrs["hdd_ssd"]).strip()
            if not self.gpu and attrs.get("vga"):
                self.gpu = str(attrs["vga"]).strip()
            if not self.os and (attrs.get("os") or attrs.get("operasi_system")):
                self.os = str(attrs.get("os") or attrs.get("operasi_system")).strip()
            if not self.merek and attrs.get("merk"):
                self.merek = str(attrs["merk"]).strip()
            if not self.model and attrs.get("tipe_model"):
                self.model = str(attrs["tipe_model"]).strip()
            if not self.ukuran_layar and attrs.get("ukuran_layar"):
                self.ukuran_layar = str(attrs["ukuran_layar"]).strip()
            if not self.resolusi and attrs.get("resolusi_layar"):
                self.resolusi = str(attrs["resolusi_layar"]).strip()
            if not self.port_display and attrs.get("konektivitas"):
                kon = attrs["konektivitas"]
                if isinstance(kon, list):
                    self.port_display = ", ".join(str(x) for x in kon)
                else:
                    self.port_display = str(kon)
        return self


class AssetUpdate(BaseModel):
    """Payload pembaruan aset (semua field opsional untuk mendukung PUT/PATCH)."""

    model_config = ConfigDict(extra="allow")

    nama_aset: str | None = Field(default=None, max_length=150)
    kategori: str | None = Field(default=None, max_length=50)
    merek: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    sn_pid: str | None = Field(default=None, max_length=100)
    kepemilikan: str | None = Field(default=None, max_length=50)
    lokasi: str | None = Field(default=None, max_length=100)
    detail_lokasi: str | None = Field(default=None, max_length=150)
    ruangan: str | None = Field(default=None, max_length=150)
    penanggung_jawab: str | None = Field(default=None, max_length=100)
    pengguna: str | None = Field(default=None, max_length=100)
    digunakan_oleh: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=40)
    kondisi: str | None = Field(default=None, max_length=40)
    tanggal_masuk: date | None = Field(default=None)
    tanggal_masuk_gudang: date | None = Field(default=None)
    tanggal_keluar_gudang: str | None = Field(default=None)
    attributes: dict[str, Any] | None = Field(default=None)

    processor: str | None = None
    motherboard: str | None = None
    ram: str | None = None
    storage: str | None = None
    gpu: str | None = None
    os: str | None = None
    watt: int | None = Field(default=None, ge=0)

    ukuran_layar: str | None = None
    resolusi: str | None = None
    panel: str | None = None
    port_display: str | None = None

    kapasitas_va: int | None = Field(default=None, ge=0)
    kapasitas_watt: int | None = Field(default=None, ge=0)
    baterai: str | None = None
    jumlah_baterai: int | None = Field(default=None, ge=0)
    beban_perangkat: str | None = None

    ip_address: str | None = None
    mac_address: str | None = None
    koneksi: str | None = None
    catatan: str | None = None

    @field_validator("tanggal_masuk", "tanggal_masuk_gudang", mode="before")
    @classmethod
    def _empty_date_to_none(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("kategori")
    @classmethod
    def _check_kategori(cls, v: str | None) -> str | None:
        return _validate_category(v) if v is not None else None

    @field_validator("lokasi")
    @classmethod
    def _check_lokasi(cls, v: str | None) -> str | None:
        return _validate_location(v) if v is not None else None

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        return _validate_status(v) if v is not None else None


class AssetPublic(BaseModel):
    """Representasi JSON aset yang dikembalikan ke frontend."""

    id: int
    id_aset: str
    nama_aset: str
    kategori: str
    merek: str
    merk: str
    model: str
    tipe_model: str
    serial_number: str
    sn_pid: str
    kepemilikan: str
    lokasi: str
    detail_lokasi: str
    ruangan: str
    penanggung_jawab: str
    pengguna: str
    digunakan_oleh: str
    status: str
    kondisi: str
    tanggal_masuk: str | None
    tanggal_masuk_gudang: str | None
    tanggal_keluar_gudang: str
    tanggal_masuk_display: str
    tanggal_keluar_display: str

    jenis: str
    processor: str
    cpu: str
    motherboard: str
    mainboard: str
    ram: str
    storage: str
    hdd_ssd: str
    gpu: str
    vga: str
    os: str
    operasi_system: str
    monitor: str
    keyboard: str
    mouse: str
    watt: int

    ukuran_layar: str
    ukuran_layar_display: str
    resolusi: str
    resolusi_layar: str
    panel: str
    port_display: str
    konektivitas: list[str]

    kapasitas_va: int
    kapasitas_watt: int
    baterai: str
    jumlah_baterai: int
    beban_perangkat: str

    ip_address: str
    mac_address: str
    koneksi: str
    catatan: str
    attributes: dict[str, Any]

    @classmethod
    def from_asset(cls, asset: Asset) -> "AssetPublic":
        extra: dict[str, Any] = dict(asset.extra_specs or {})
        tgl = (
            asset.tanggal_masuk.isoformat()
            if asset.tanggal_masuk
            else (str(extra.get("tanggal_masuk_gudang") or "") or None)
        )
        tgl_keluar = str(extra.get("tanggal_keluar_gudang") or "")
        sn_val = asset.serial_number or str(extra.get("sn_pid") or "-")
        kepemilikan_val = str(extra.get("kepemilikan") or "XML")
        pemakai_val = asset.penanggung_jawab or str(extra.get("digunakan_oleh") or "") or "—"
        jenis_val = _derive_asset_jenis(asset, extra)
        cpu_val = asset.processor or str(extra.get("cpu") or "—")
        mb_val = asset.motherboard or str(extra.get("mainboard") or "—")
        ram_val = asset.ram or str(extra.get("ram") or "—")
        storage_val = asset.storage or str(extra.get("hdd_ssd") or "—")
        gpu_val = asset.gpu or str(extra.get("vga") or "—")
        os_val = asset.os or str(extra.get("os") or extra.get("operasi_system") or "—")
        mon_val = str(extra.get("monitor") or "—")
        kbd_val = str(extra.get("keyboard") or "—")
        mouse_val = str(extra.get("mouse") or "—")

        merk_val = asset.merek or str(extra.get("merk") or "—")
        tipe_val = asset.model or str(extra.get("tipe_model") or "—")
        ukuran_raw = asset.ukuran_layar or str(extra.get("ukuran_layar") or "")
        ukuran_clean = ukuran_raw.replace('"', "").replace("inch", "").strip()
        ukuran_disp = f'{ukuran_clean}"' if ukuran_clean else "—"
        res_val = asset.resolusi or str(extra.get("resolusi_layar") or "—")

        raw_kon = extra.get("konektivitas")
        if isinstance(raw_kon, list):
            konektivitas_list = [str(x).strip() for x in raw_kon if str(x).strip()]
        elif asset.port_display:
            konektivitas_list = [p.strip() for p in asset.port_display.split(",") if p.strip()]
        else:
            konektivitas_list = []

        attrs_out: dict[str, Any] = {
            **extra,
            "jenis": jenis_val,
            "os": os_val if os_val != "—" else "",
            "operasi_system": os_val if os_val != "—" else "",
            "ram": ram_val if ram_val != "—" else "",
            "vga": gpu_val if gpu_val != "—" else "",
            "cpu": cpu_val if cpu_val != "—" else "",
            "mainboard": mb_val if mb_val != "—" else "",
            "hdd_ssd": storage_val if storage_val != "—" else "",
            "monitor": mon_val if mon_val != "—" else "",
            "keyboard": kbd_val if kbd_val != "—" else "",
            "mouse": mouse_val if mouse_val != "—" else "",
            "merk": merk_val if merk_val != "—" else "",
            "tipe_model": tipe_val if tipe_val != "—" else "",
            "ukuran_layar": ukuran_clean,
            "resolusi_layar": res_val if res_val != "—" else "",
            "konektivitas": konektivitas_list,
        }

        return cls(
            id=asset.id or 0,
            id_aset=asset.id_aset,
            nama_aset=asset.nama_aset,
            kategori=asset.kategori,
            merek=asset.merek,
            merk=merk_val,
            model=asset.model,
            tipe_model=tipe_val,
            serial_number=sn_val,
            sn_pid=sn_val if sn_val != "-" else "—",
            kepemilikan=kepemilikan_val,
            lokasi=asset.lokasi,
            detail_lokasi=asset.detail_lokasi,
            ruangan=asset.detail_lokasi,
            penanggung_jawab=asset.penanggung_jawab,
            pengguna=asset.penanggung_jawab,
            digunakan_oleh=pemakai_val,
            status=asset.status,
            kondisi=asset.kondisi,
            tanggal_masuk=tgl,
            tanggal_masuk_gudang=tgl,
            tanggal_keluar_gudang=tgl_keluar,
            tanggal_masuk_display=format_date_id(tgl),
            tanggal_keluar_display=format_date_id(tgl_keluar),
            jenis=jenis_val,
            processor=asset.processor,
            cpu=cpu_val,
            motherboard=asset.motherboard,
            mainboard=mb_val,
            ram=ram_val,
            storage=asset.storage,
            hdd_ssd=storage_val,
            gpu=asset.gpu,
            vga=gpu_val,
            os=os_val,
            operasi_system=os_val,
            monitor=mon_val,
            keyboard=kbd_val,
            mouse=mouse_val,
            watt=asset.watt,
            ukuran_layar=ukuran_clean,
            ukuran_layar_display=ukuran_disp,
            resolusi=asset.resolusi,
            resolusi_layar=res_val,
            panel=asset.panel,
            port_display=asset.port_display,
            konektivitas=konektivitas_list,
            kapasitas_va=asset.kapasitas_va,
            kapasitas_watt=asset.kapasitas_watt,
            baterai=asset.baterai,
            jumlah_baterai=asset.jumlah_baterai,
            beban_perangkat=asset.beban_perangkat,
            ip_address=asset.ip_address,
            mac_address=asset.mac_address,
            koneksi=asset.koneksi,
            catatan=asset.catatan,
            attributes=attrs_out,
        )


class AssetPageResponse(BaseModel):
    """Respons daftar aset berhalaman beserta tab_counts, category_counts, dan summary."""

    items: list[AssetPublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    category_counts: dict[str, int] = Field(default_factory=dict)
    summary: dict[str, int]
