"""Skema Pydantic untuk Jadwal, Riwayat, dan Jadwal Massal Maintenance (B6)."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.master_data import ASSET_CONDITIONS, LOCATION_ALIASES, LOCATIONS
from app.models.maintenance import Maintenance
from app.schemas.finance import VALID_BILLING_CYCLES

VALID_MAINTENANCE_TYPES = {
    "Preventif",
    "Rutin",
    "Korektif",
    "Perbaikan",
    "Pembersihan",
    "Upgrade",
    "Penggantian Baterai",
    "Inspeksi",
}

VALID_PRIORITIES = {"Rendah", "Normal", "Sedang", "Tinggi", "Kritis", "Darurat"}

VALID_MAINTENANCE_STATUSES = {
    "Terjadwal",
    "Dijadwalkan",
    "Dalam Proses",
    "Sedang Dikerjakan",
    "Selesai",
    "Terlambat",
    "Dibatalkan",
}


def _normalize_location_opt(val: str | None) -> str | None:
    if val is None:
        return None
    cleaned = val.strip()
    if not cleaned or cleaned.lower() in ("semua", "all"):
        return None
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc
    if cleaned.lower() in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned.lower()]
    return cleaned


class MaintenanceCreate(BaseModel):
    """Payload pembuatan satu jadwal atau catatan riwayat maintenance."""

    model_config = ConfigDict(extra="allow")

    kode_maintenance: str | None = Field(default=None, max_length=30)
    id_maintenance: str | None = Field(default=None, max_length=30)

    id_aset: str = Field(min_length=1, max_length=30)
    nama_aset: str = Field(default="", max_length=150)
    kategori: str = Field(default="", max_length=50)
    lokasi: str = Field(default="", max_length=100)

    jenis_maintenance: str = Field(default="Preventif", max_length=50)
    jenis: str | None = Field(default=None, max_length=50)
    prioritas: str = Field(default="Normal", max_length=30)
    judul: str = Field(default="", max_length=150)
    deskripsi: str = Field(default="", max_length=500)
    tindakan: str = Field(default="", max_length=500)

    teknisi: str = Field(default="", max_length=100)
    penanggung_jawab: str | None = Field(default=None, max_length=100)
    vendor_servis: str = Field(default="", max_length=120)
    biaya: int = Field(default=0, ge=0)

    tanggal_jadwal: date | None = Field(default=None)
    tanggal: date | None = Field(default=None)
    tanggal_selesai: date | None = Field(default=None)

    status: str = Field(default="Terjadwal", max_length=40)
    kondisi_setelah: str = Field(default="Baik", max_length=40)

    is_recurring: bool | None = Field(default=None)
    siklus: str = Field(default="Sekali", max_length=30)
    catatan: str = Field(default="", max_length=500)
    keterangan: str | None = Field(default=None, max_length=500)

    @field_validator("id_aset")
    @classmethod
    def _clean_asset_code(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("id_aset wajib diisi")
        return cleaned

    @model_validator(mode="after")
    def _normalize_fields(self) -> "MaintenanceCreate":
        if not self.kode_maintenance and self.id_maintenance:
            self.kode_maintenance = self.id_maintenance.strip()

        if self.jenis and self.jenis_maintenance == "Preventif":
            self.jenis_maintenance = self.jenis.strip()

        matched_type = next(
            (
                t
                for t in VALID_MAINTENANCE_TYPES
                if t.lower() == self.jenis_maintenance.strip().lower()
            ),
            None,
        )
        if not matched_type:
            raise ValueError(f"Jenis maintenance '{self.jenis_maintenance}' tidak valid")
        self.jenis_maintenance = matched_type

        matched_prio = next(
            (p for p in VALID_PRIORITIES if p.lower() == self.prioritas.strip().lower()),
            None,
        )
        if not matched_prio:
            raise ValueError(f"Prioritas '{self.prioritas}' tidak valid")
        self.prioritas = matched_prio

        matched_st = next(
            (s for s in VALID_MAINTENANCE_STATUSES if s.lower() == self.status.strip().lower()),
            None,
        )
        if not matched_st:
            raise ValueError(f"Status maintenance '{self.status}' tidak valid")
        if matched_st == "Dijadwalkan":
            matched_st = "Terjadwal"
        self.status = matched_st

        if self.tanggal_jadwal is None:
            self.tanggal_jadwal = self.tanggal or date.today()

        if self.status == "Selesai" and self.tanggal_selesai is None:
            self.tanggal_selesai = self.tanggal_jadwal

        if not self.teknisi and self.penanggung_jawab:
            self.teknisi = self.penanggung_jawab.strip()
        self.teknisi = self.teknisi.strip()

        if not self.catatan and self.keterangan:
            self.catatan = self.keterangan.strip()

        if not self.judul:
            self.judul = self.deskripsi or f"Maintenance {self.jenis_maintenance}"

        if self.siklus not in VALID_BILLING_CYCLES:
            raise ValueError(f"Siklus jadwal '{self.siklus}' tidak valid")
        self.siklus = VALID_BILLING_CYCLES[self.siklus]

        if self.is_recurring is None:
            self.is_recurring = self.siklus != "Sekali"
        elif self.is_recurring and self.siklus == "Sekali":
            self.siklus = "Bulanan"

        return self


class MaintenanceUpdate(BaseModel):
    """Payload pembaruan jadwal atau riwayat maintenance."""

    model_config = ConfigDict(extra="allow")

    jenis_maintenance: str | None = None
    prioritas: str | None = None
    judul: str | None = None
    deskripsi: str | None = None
    tindakan: str | None = None
    teknisi: str | None = None
    vendor_servis: str | None = None
    biaya: int | None = Field(default=None, ge=0)
    tanggal_jadwal: date | None = None
    tanggal_selesai: date | None = None
    status: str | None = None
    kondisi_setelah: str | None = None
    is_recurring: bool | None = None
    siklus: str | None = None
    catatan: str | None = None


class MaintenanceCompleteRequest(BaseModel):
    """Payload saat menandai jadwal maintenance sebagai Selesai."""

    model_config = ConfigDict(extra="allow")

    tanggal_selesai: date | None = None
    tindakan: str | None = None
    hasil: str | None = None
    teknisi: str | None = None
    pic: str | None = None
    dikerjakan_oleh: str | None = None
    biaya: int | None = Field(default=None, ge=0)
    kondisi_setelah: str = Field(default="Baik")
    status_aset_setelah: str = Field(default="Aktif")
    catatan: str | None = None
    create_next_schedule: bool = True

    @field_validator("kondisi_setelah")
    @classmethod
    def _validate_cond(cls, v: str) -> str:
        matched = next(
            (c for c in ASSET_CONDITIONS if c.lower() == v.strip().lower()),
            None,
        )
        return matched or v.strip()


class BulkMaintenanceRequest(BaseModel):
    """Payload pembuatan Jadwal Massal (berdasarkan id_assets atau filter kategori/lokasi)."""

    model_config = ConfigDict(extra="allow")

    id_assets: list[str] | None = Field(default=None)
    asset_ids: list[str] | None = Field(default=None)
    kategori: str | None = Field(default=None)
    lokasi: str | None = Field(default=None)
    only_active_assets: bool = Field(default=True)

    jenis_maintenance: str = Field(default="Preventif", max_length=50)
    jenis: str | None = Field(default=None, max_length=50)
    prioritas: str = Field(default="Normal", max_length=30)
    judul: str = Field(default="", max_length=150)
    kegiatan: str | None = Field(default=None, max_length=150)
    deskripsi: str = Field(default="Pemeliharaan berkala terjadwal", max_length=500)
    teknisi: str = Field(default="Tim IT Support", max_length=100)
    pic: str | None = Field(default=None, max_length=100)
    tanggal_jadwal: date | None = Field(default=None)
    tgl_mulai: date | None = Field(default=None)
    is_recurring: bool = Field(default=False)
    siklus: str = Field(default="Sekali", max_length=30)
    frekuensi: str | None = Field(default=None, max_length=30)
    catatan: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _validate_bulk_criteria(self) -> "BulkMaintenanceRequest":
        if self.asset_ids and not self.id_assets:
            self.id_assets = self.asset_ids

        clean_ids = [
            code.strip().upper() for code in (self.id_assets or []) if code and code.strip()
        ]
        self.id_assets = clean_ids if clean_ids else None
        self.lokasi = _normalize_location_opt(self.lokasi)
        if self.kategori and self.kategori.strip().lower() in ("semua", "all", ""):
            self.kategori = None

        if not self.id_assets and not self.kategori and not self.lokasi:
            raise ValueError(
                "Jadwal massal wajib menyertakan minimal satu kriteria: "
                "id_assets, kategori, atau lokasi"
            )

        if self.jenis and self.jenis_maintenance == "Preventif":
            matched_t = next(
                (t for t in VALID_MAINTENANCE_TYPES if t.lower() == self.jenis.strip().lower()),
                None,
            )
            if matched_t:
                self.jenis_maintenance = matched_t

        if self.pic and self.teknisi == "Tim IT Support":
            self.teknisi = self.pic.strip()

        if self.tanggal_jadwal is None:
            self.tanggal_jadwal = self.tgl_mulai or date.today()

        if self.frekuensi and self.siklus == "Sekali":
            self.siklus = self.frekuensi.strip()

        if self.siklus not in VALID_BILLING_CYCLES:
            raise ValueError(f"Siklus jadwal '{self.siklus}' tidak valid")
        self.siklus = VALID_BILLING_CYCLES[self.siklus]
        if self.siklus != "Sekali":
            self.is_recurring = True
        elif self.is_recurring:
            self.siklus = "Bulanan"

        if not self.judul:
            self.judul = (
                (self.kegiatan or "").strip()
                or self.deskripsi
                or f"Maintenance {self.jenis_maintenance}"
            )

        return self


class MaintenancePublic(BaseModel):
    """Representasi JSON jadwal/riwayat maintenance sesuai kontrak frontend."""

    id: int
    kode_maintenance: str
    id_maintenance: str
    id_aset: str
    nama_aset: str
    objek_display: str = ""
    kategori: str
    lokasi: str

    jenis_maintenance: str
    jenis: str
    prioritas: str
    judul: str
    kegiatan: str = ""
    deskripsi: str
    tindakan: str
    terakhir_hasil: str = "—"
    hasil: str = "Normal"

    teknisi: str
    pic: str = "Ridho"
    dikerjakan_oleh: str = "Ridho"
    penanggung_jawab: str
    vendor_servis: str
    biaya: int

    tanggal_jadwal: str
    jadwal_berikutnya: str = ""
    tanggal: str
    tanggal_selesai: str | None

    status: str
    status_efektif: str
    status_variant: str = "info"
    is_overdue: bool
    is_history: bool
    hari_menuju_jadwal: int

    kondisi_setelah: str
    is_recurring: bool
    siklus: str
    frekuensi: str = "Bulanan"
    catatan: str
    keterangan: str

    @classmethod
    def from_model(
        cls,
        row: Maintenance,
        today: date | None = None,
    ) -> "MaintenancePublic":
        ref_today = today or date.today()
        days_diff = (row.tanggal_jadwal - ref_today).days
        is_history = row.status.lower() in ("selesai", "dibatalkan")
        is_overdue = (not is_history) and days_diff < 0
        is_soon = (not is_history) and (0 <= days_diff <= 7)
        if is_overdue:
            effective_status = "Terlambat"
            st_variant = "danger"
        elif is_soon:
            effective_status = "Segera"
            st_variant = "warning"
        elif is_history:
            effective_status = row.status
            st_variant = "success" if row.status.lower() == "selesai" else "neutral"
        else:
            effective_status = row.status
            st_variant = "info"

        tgl_str = row.tanggal_jadwal.isoformat()
        kegiatan_str = row.judul or row.deskripsi or f"Maintenance {row.jenis_maintenance}"
        pic_str = row.teknisi or "Ridho"
        hasil_str = "Normal" if row.kondisi_setelah in ("Baik", "Baru") else "Perlu Tindak Lanjut"

        return cls(
            id=row.id or 0,
            kode_maintenance=row.kode_maintenance,
            id_maintenance=row.kode_maintenance,
            id_aset=row.id_aset,
            nama_aset=row.nama_aset,
            objek_display=f"{row.id_aset} · {row.nama_aset}",
            kategori=row.kategori,
            lokasi=row.lokasi,
            jenis_maintenance=row.jenis_maintenance,
            jenis=row.jenis_maintenance,
            prioritas=row.prioritas,
            judul=kegiatan_str,
            kegiatan=kegiatan_str,
            deskripsi=row.deskripsi,
            tindakan=row.tindakan or "-",
            terakhir_hasil=row.tindakan or "Normal",
            hasil=hasil_str,
            teknisi=pic_str,
            pic=pic_str,
            dikerjakan_oleh=pic_str,
            penanggung_jawab=pic_str,
            vendor_servis=row.vendor_servis or "-",
            biaya=row.biaya,
            tanggal_jadwal=tgl_str,
            jadwal_berikutnya=tgl_str,
            tanggal=tgl_str,
            tanggal_selesai=(
                row.tanggal_selesai.isoformat() if row.tanggal_selesai else tgl_str
            ),
            status=effective_status,
            status_efektif=effective_status,
            status_variant=st_variant,
            is_overdue=is_overdue,
            is_history=is_history,
            hari_menuju_jadwal=days_diff,
            kondisi_setelah=row.kondisi_setelah,
            is_recurring=row.is_recurring,
            siklus=row.siklus,
            frekuensi=row.siklus,
            catatan=row.catatan,
            keterangan=row.catatan,
        )


class BulkMaintenanceResponse(BaseModel):
    """Respons hasil eksekusi pembuatan jadwal maintenance massal."""

    created_count: int
    items: list[MaintenancePublic]


class MaintenancePageResponse(BaseModel):
    """Respons berhalaman daftar jadwal & riwayat maintenance untuk frontend."""

    items: list[MaintenancePublic]
    total: int
    page: int
    page_size: int
    tab_counts: dict[str, int]
    summary: dict[str, Any]
    kpi: dict[str, Any]
