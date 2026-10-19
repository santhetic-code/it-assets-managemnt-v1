"""
Komponen Status Badge Siklus Hidup Aset ITAM Pro.
In Use (hijau), Maintenance (amber), In Storage (abu), Disposed (merah).
"""
from typing import Any

import reflex as rx

from .badge import status_badge


def asset_status_badge(status: Any) -> rx.Component:
    """Render badge status aset otomatis berdasarkan teks status."""
    variant = rx.match(
        status,
        ("In Use", "success"),
        ("Maintenance", "warning"),
        ("In Storage", "neutral"),
        ("Disposed", "danger"),
        "neutral",
    )
    return status_badge(label=status, variant=variant)
