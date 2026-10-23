"""
Komponen Status Badge & Condition Badge Semantik ITAM Pro.
Mendukung status Aset (Digunakan, Backup, Tidak Digunakan)
serta status IP (Aktif, Nonaktif, Bentrok).
"""
from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius


def asset_status_badge(status_var: Any) -> rx.Component:
    """Render badge status untuk Aset maupun entri IP."""
    bg_color = rx.match(
        status_var,
        ("Digunakan", Color.SUCCESS_BG),
        ("Aktif", Color.SUCCESS_BG),
        ("Backup", Color.BACKUP_BG),
        ("Tidak Digunakan", Color.WARNING_BG),
        ("Nonaktif", Color.NEUTRAL_BG),
        ("Bentrok", Color.DANGER_BG),
        Color.NEUTRAL_BG,
    )
    fg_color = rx.match(
        status_var,
        ("Digunakan", Color.SUCCESS_FG),
        ("Aktif", Color.SUCCESS_FG),
        ("Backup", Color.BACKUP_FG),
        ("Tidak Digunakan", Color.WARNING_FG),
        ("Nonaktif", Color.NEUTRAL_FG),
        ("Bentrok", Color.DANGER_FG),
        Color.NEUTRAL_FG,
    )
    return rx.box(
        rx.text(
            status_var,
            font_size=FontSize.XS,
            font_weight=FontWeight.BOLD,
            color=fg_color,
            white_space="nowrap",
        ),
        style=rx.Style(
            {
                "display": "inline-flex",
                "align_items": "center",
                "padding": "3px 10px",
                "border_radius": Radius.FULL,
                "background_color": bg_color,
            }
        ),
    )


def asset_condition_badge(condition_var: Any) -> rx.Component:
    """Render badge kondisi fisik aset."""
    bg_color = rx.match(
        condition_var,
        ("Baru", Color.SUCCESS_BG),
        ("Bekas", Color.NEUTRAL_BG),
        ("Tidak Terpakai / Rusak", Color.DANGER_BG),
        Color.NEUTRAL_BG,
    )
    fg_color = rx.match(
        condition_var,
        ("Baru", Color.SUCCESS_FG),
        ("Bekas", Color.NEUTRAL_FG),
        ("Tidak Terpakai / Rusak", Color.DANGER_FG),
        Color.NEUTRAL_FG,
    )
    return rx.box(
        rx.text(
            condition_var,
            font_size=FontSize.XS,
            font_weight=FontWeight.BOLD,
            color=fg_color,
            white_space="nowrap",
        ),
        style=rx.Style(
            {
                "display": "inline-flex",
                "align_items": "center",
                "padding": "3px 10px",
                "border_radius": Radius.FULL,
                "background_color": bg_color,
            }
        ),
    )


__all__ = ["asset_condition_badge", "asset_status_badge"]
