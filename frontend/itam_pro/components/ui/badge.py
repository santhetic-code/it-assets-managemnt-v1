"""
Komponen Badge Status Reusable ITAM Pro.
Mendukung varian: success, warning, danger, info, neutral.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius


def status_badge(
    label: Any,
    variant: Any = "info",
) -> rx.Component:
    """Badge pil semantik untuk status aset, peringatan, dan kategori."""
    fg_color = rx.match(
        variant,
        ("success", Color.SUCCESS_FG),
        ("warning", Color.WARNING_FG),
        ("danger", Color.DANGER_FG),
        ("neutral", Color.NEUTRAL_FG),
        ("info", Color.INFO_FG),
        Color.INFO_FG,
    )
    bg_color = rx.match(
        variant,
        ("success", Color.SUCCESS_BG),
        ("warning", Color.WARNING_BG),
        ("danger", Color.DANGER_BG),
        ("neutral", Color.NEUTRAL_BG),
        ("info", Color.INFO_BG),
        Color.INFO_BG,
    )

    return rx.box(
        rx.text(
            label,
            font_size=FontSize.XS,
            font_weight=FontWeight.BOLD,
            color=fg_color,
            line_height="1.2",
            white_space="nowrap",
        ),
        style=rx.Style(
            {
                "padding": "4px 12px",
                "background_color": bg_color,
                "border_radius": Radius.FULL,
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "flex_shrink": "0",
            }
        ),
    )
