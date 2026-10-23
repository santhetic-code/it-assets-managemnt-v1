"""
Fungsi Validasi Logika Bisnis Murni ITAM Pro.
Digunakan oleh State Reflex dan diuji langsung melalui pytest.
"""
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


__all__ = ["validate_asset_business_rules"]
