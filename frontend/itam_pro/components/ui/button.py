"""
Komponen Tombol Utama Reusable ITAM Pro.
Tinggi 48px, radius 10px, warna #1D4ED8, teks putih 15px weight 700.
"""
from typing import Any, Literal

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size


def primary_button(
    label: str,
    on_click: Any | None = None,
    is_loading: Any = False,
    button_type: Literal["button", "reset", "submit"] = "button",
    full_width: bool = True,
    margin_top: str = "0px",
) -> rx.Component:
    """Tombol aksi utama dengan dukungan state loading."""
    return rx.el.button(
        rx.cond(
            is_loading,
            rx.hstack(
                rx.spinner(size="2", color=Color.WHITE),
                rx.text("Memproses...", font_size=FontSize.MD, font_weight=FontWeight.BOLD),
                spacing="2",
                align="center",
                justify="center",
            ),
            rx.text(
                label,
                font_size=FontSize.MD,
                font_weight=FontWeight.BOLD,
                color=Color.WHITE,
            ),
        ),
        type=button_type,
        on_click=on_click,
        disabled=is_loading,
        style=rx.Style(
            {
                "width": "100%" if full_width else "auto",
                "height": Size.CONTROL_HEIGHT,
                "margin_top": margin_top,
                "padding_left": "20px",
                "padding_right": "20px",
                "background_color": Color.ACCENT,
                "color": Color.WHITE,
                "border": "none",
                "border_radius": Radius.CONTROL,
                "font_family": FONT_FAMILY,
                "font_size": FontSize.MD,
                "font_weight": FontWeight.BOLD,
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "cursor": rx.cond(is_loading, "not-allowed", "pointer"),
                "opacity": rx.cond(is_loading, "0.8", "1"),
                "transition": "background-color 0.15s ease, opacity 0.15s ease",
            }
        ),
        _hover=rx.Style(
            {
                "background_color": Color.ACCENT_BRIGHT,
            }
        ),
    )
