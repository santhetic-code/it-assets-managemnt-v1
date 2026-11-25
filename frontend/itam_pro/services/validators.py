"""
Fungsi Validasi Logika Bisnis Murni ITAM Pro.
Digunakan oleh State Reflex dan diuji langsung melalui pytest.
"""

import re
from datetime import date, datetime
from typing import Any


def validate_asset_business_rules(payload: dict[str, Any]) -> str | None:
    """
    Validasi aturan bisnis inti aset:
    1. Jika status == 'Digunakan' (selain Monitor), field 'digunakan_oleh' wajib diisi.
    2. Jika tanggal_masuk_gudang dan tanggal_keluar_gudang diisi,
       tanggal_keluar_gudang harus >= tanggal_masuk_gudang.
    Kembalikan pesan error (str) jika tidak valid, atau None jika valid.
    """
    kategori = str(payload.get("kategori", "")).strip()
    nama_aset = str(payload.get("nama_aset", "")).strip()
    status = str(payload.get("status", "Digunakan")).strip()
    digunakan_oleh = str(payload.get("digunakan_oleh", "")).strip()
    tgl_masuk = str(payload.get("tanggal_masuk_gudang", "")).strip()
    tgl_keluar = str(payload.get("tanggal_keluar_gudang", "")).strip()

    if kategori != "Monitor" and not nama_aset:
        return "Nama Aset / Hostname wajib diisi."

    if status == "Digunakan" and not digunakan_oleh:
        return "Field 'Digunakan Oleh' wajib diisi bila status Digunakan."

    if tgl_masuk and tgl_keluar and tgl_keluar < tgl_masuk:
        return "Tanggal Keluar Gudang tidak boleh sebelum Tanggal Masuk Gudang."

    return None


_BULAN_ID = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
)


def format_rupiah(value: Any) -> str:
    """Format nominal angka ke format Rupiah Indonesia: 'Rp 1.533.700'."""
    if value is None or value == "":
        return "Rp 0"
    if isinstance(value, bool):
        return "Rp 0"
    if isinstance(value, (int, float)):
        num = round(value)
    else:
        raw = str(value).strip()
        if not raw:
            return "Rp 0"
        negative = raw.startswith("-")
        cleaned = re.sub(r"[^\d,.]", "", raw)
        if not cleaned:
            return "Rp 0"
        if "," in cleaned and "." in cleaned:
            # Format ID "1.533.700,00" -> buang desimal & titik ribuan
            cleaned = cleaned.split(",")[0].replace(".", "")
        elif "." in cleaned and len(cleaned.rsplit(".", 1)[-1]) == 3:
            cleaned = cleaned.replace(".", "")
        elif "," in cleaned and len(cleaned.rsplit(",", 1)[-1]) == 3:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
        try:
            num = round(float(cleaned))
            if negative:
                num = -num
        except ValueError:
            return "Rp 0"
    prefix = "-Rp " if num < 0 else "Rp "
    return f"{prefix}{abs(num):,}".replace(",", ".")


def format_tanggal(value: Any, *, empty: str = "—") -> str:
    """Format tanggal ISO/date/datetime ke format Indonesia: '20 Nov 2026'."""
    if value is None:
        return empty
    if isinstance(value, datetime):
        dt = value.date()
        return f"{dt.day} {_BULAN_ID[dt.month]} {dt.year}"
    if isinstance(value, date):
        return f"{value.day} {_BULAN_ID[value.month]} {value.year}"

    raw = str(value).strip()
    if not raw or raw in ("—", "-"):
        return empty

    date_part = raw.split("T", 1)[0].split(" ", 1)[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            parsed = datetime.strptime(date_part, fmt).date()
            return f"{parsed.day} {_BULAN_ID[parsed.month]} {parsed.year}"
        except ValueError:
            continue
    return raw


__all__ = ["format_rupiah", "format_tanggal", "validate_asset_business_rules"]
