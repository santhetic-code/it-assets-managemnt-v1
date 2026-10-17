"""
Komponen Checkbox Reusable ITAM Pro.
Kotak 18px, accent #1D4ED8, label teks muted #55627F.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Size


def app_checkbox(
    label: str,
    checked: Any,
    on_change: Any,
) -> rx.Component:
    """Checkbox standar dengan ukuran 18x18px dan warna aksen #1D4ED8."""
    return rx.el.label(
        rx.hstack(
            rx.el.input(
                type="checkbox",
                checked=checked,
                on_change=on_change,
                style=rx.Style(
                    {
                        "width": Size.CHECKBOX,
                        "height": Size.CHECKBOX,
                        "accent_color": Color.ACCENT,
                        "border": f"1.5px solid {Color.MUTED}",
                        "border_radius": "4px",
                        "cursor": "pointer",
                        "margin": "0",
                    }
                ),
            ),
            rx.text(
                label,
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
                user_select="none",
            ),
            spacing="2",
            align="center",
        ),
        style=rx.Style(
            {
                "cursor": "pointer",
                "display": "inline-flex",
                "align_items": "center",
            }
        ),
    )
