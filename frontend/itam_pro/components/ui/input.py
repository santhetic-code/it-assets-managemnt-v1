"""
Komponen Input Field Reusable ITAM Pro.
Tinggi 48px, radius 10px, border #D5DEEE, ikon kiri/kanan 18px #55627F.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size


def form_input_field(
    label: str,
    placeholder: str,
    icon_tag: str,
    value: Any,
    on_change: Any,
    input_type: Any = "text",
    name: str | None = None,
    right_element: rx.Component | None = None,
    required: bool = False,
) -> rx.Component:
    """Field input standar dengan label di atas, ikon kiri, dan slot elemen kanan."""
    return rx.vstack(
        rx.text(
            label,
            font_size=FontSize.BASE,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
            line_height="1.2",
        ),
        rx.hstack(
            rx.icon(
                tag=icon_tag,
                size=Size.ICON_MD,
                color=Color.MUTED,
                stroke_width=1.75,
                flex_shrink="0",
            ),
            rx.el.input(
                type=input_type,
                name=name,
                placeholder=placeholder,
                value=value,
                on_change=on_change,
                required=required,
                style=rx.Style(
                    {
                        "width": "100%",
                        "height": "100%",
                        "border": "none",
                        "outline": "none",
                        "background": "transparent",
                        "color": Color.TEXT,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.BASE,
                        "font_weight": FontWeight.REGULAR,
                    }
                ),
            ),
            right_element if right_element is not None else rx.fragment(),
            width="100%",
            height=Size.CONTROL_HEIGHT,
            padding_x="14px",
            spacing="3",
            align="center",
            background_color=Color.SURFACE,
            border=f"1px solid {Color.INPUT_BORDER}",
            border_radius=Radius.CONTROL,
            transition="border-color 0.15s ease, box-shadow 0.15s ease",
            _focus_within=rx.Style(
                {
                    "border_color": Color.ACCENT,
                    "box_shadow": Color.FOCUS_RING,
                }
            ),
        ),
        spacing="2",
        align="start",
        width="100%",
    )
