"""
Komponen Badge & Chip Konektor ITAM Pro.
Seluruh warna menggunakan token dari styles/colors.py.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius


def app_badge(label: Any, variant: Any = "neutral") -> rx.Component:
    """Badge semantik dengan varian warna dari token Color."""
    bg_map = {
        "success": Color.SUCCESS_BG,
        "warning": Color.WARNING_BG,
        "danger": Color.DANGER_BG,
        "info": Color.BACKUP_BG,
        "backup": Color.BACKUP_BG,
        "neutral": Color.NEUTRAL_BG,
    }
    fg_map = {
        "success": Color.SUCCESS_FG,
        "warning": Color.WARNING_FG,
        "danger": Color.DANGER_FG,
        "info": Color.BACKUP_FG,
        "backup": Color.BACKUP_FG,
        "neutral": Color.NEUTRAL_FG,
    }

    if isinstance(variant, rx.Var):
        bg_color = rx.match(
            variant,
            ("success", Color.SUCCESS_BG),
            ("warning", Color.WARNING_BG),
            ("danger", Color.DANGER_BG),
            ("info", Color.BACKUP_BG),
            ("backup", Color.BACKUP_BG),
            ("neutral", Color.NEUTRAL_BG),
            Color.NEUTRAL_BG,
        )
        fg_color = rx.match(
            variant,
            ("success", Color.SUCCESS_FG),
            ("warning", Color.WARNING_FG),
            ("danger", Color.DANGER_FG),
            ("info", Color.BACKUP_FG),
            ("backup", Color.BACKUP_FG),
            ("neutral", Color.NEUTRAL_FG),
            Color.NEUTRAL_FG,
        )
    else:
        bg_color = bg_map.get(str(variant), Color.NEUTRAL_BG)
        fg_color = fg_map.get(str(variant), Color.NEUTRAL_FG)

    return rx.box(
        rx.text(
            label,
            title=label,
            font_size=FontSize.XS,
            font_weight=FontWeight.BOLD,
            color=fg_color,
            style=rx.Style(
                {
                    "white_space": "nowrap",
                    "overflow": "hidden",
                    "text_overflow": "ellipsis",
                }
            ),
        ),
        style=rx.Style(
            {
                "display": "inline-flex",
                "align_items": "center",
                "max_width": "100%",
                "padding": "3px 10px",
                "border_radius": Radius.FULL,
                "background_color": bg_color,
            }
        ),
    )


def connector_chip(label: Any) -> rx.Component:
    """Chip kecil (Konektivitas, Jenis, Host) dengan pemotongan elipsis + tooltip."""
    return rx.box(
        rx.text(
            label,
            title=label,
            font_size=FontSize.XS,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
            style=rx.Style(
                {
                    "white_space": "nowrap",
                    "overflow": "hidden",
                    "text_overflow": "ellipsis",
                    "max_width": "185px",
                }
            ),
        ),
        title=label,
        style=rx.Style(
            {
                "display": "inline-flex",
                "align_items": "center",
                "max_width": "100%",
                "padding": "2px 8px",
                "background_color": Color.TABLE_HEADER_BG,
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": Radius.CHIP,
                "overflow": "hidden",
            }
        ),
    )


__all__ = ["app_badge", "connector_chip"]
