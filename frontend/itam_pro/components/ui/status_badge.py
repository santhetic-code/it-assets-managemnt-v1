"""
Komponen Badge Kondisi & Status Aset ITAM Pro.
- Kondisi: Baru (biru/info), Bekas (abu/neutral), Tidak Terpakai / Rusak (merah/danger).
- Status : Digunakan (hijau/success), Backup (biru #DBEAFE / #1E40AF), Tidak Digunakan (amber).
"""
from typing import Any

import reflex as rx

from .badge import app_badge


def asset_status_badge(status: Any) -> rx.Component:
    """Render badge Status aset (Digunakan = hijau, Backup = biru, Tidak Digunakan = amber)."""
    variant = rx.match(
        status,
        ("Digunakan", "success"),
        ("Backup", "backup"),
        ("Tidak Digunakan", "warning"),
        ("In Use", "success"),
        ("Maintenance", "warning"),
        ("In Storage", "neutral"),
        ("Disposed", "danger"),
        "neutral",
    )
    return app_badge(label=status, variant=variant)


def asset_condition_badge(kondisi: Any) -> rx.Component:
    """Render badge Kondisi aset (Baru = biru, Bekas = abu, Tidak Terpakai / Rusak = merah)."""
    variant = rx.match(
        kondisi,
        ("Baru", "info"),
        ("Bekas", "neutral"),
        ("Tidak Terpakai / Rusak", "danger"),
        "neutral",
    )
    return app_badge(label=kondisi, variant=variant)


__all__ = [
    "asset_condition_badge",
    "asset_status_badge",
]
