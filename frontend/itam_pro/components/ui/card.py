"""
Komponen Card Standar Reusable ITAM Pro.
Putih, border Color.BORDER, radius 14px, padding 20px, dengan slot judul + tautan kanan.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius, Space


def app_card(
    *children: rx.Component,
    title: str | None = None,
    subtitle: Any | None = None,
    action_label: str | None = None,
    on_action_click: Any | None = None,
    padding: str = Space.S5,
) -> rx.Component:
    """Pembungkus kartu standar dengan header judul dan tautan aksi opsional."""
    has_header = title is not None or action_label is not None

    header_block = (
        rx.hstack(
            rx.vstack(
                rx.text(
                    title or "",
                    font_size=FontSize.SUBTITLE,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                    line_height="1.25",
                ),
                rx.text(
                    subtitle,
                    font_size=FontSize.FOOTER,
                    font_weight=FontWeight.REGULAR,
                    color=Color.MUTED,
                    line_height="1.3",
                )
                if subtitle is not None
                else rx.fragment(),
                spacing="1",
                align="start",
            ),
            rx.el.button(
                action_label,
                type="button",
                on_click=on_action_click,
                style=rx.Style(
                    {
                        "background": "transparent",
                        "border": "none",
                        "padding": "0",
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.SEMIBOLD,
                        "color": Color.ACCENT,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
                _hover=rx.Style({"color": Color.ACCENT_BRIGHT}),
            )
            if action_label is not None
            else rx.fragment(),
            width="100%",
            justify="between",
            align="start",
            margin_bottom=Space.S4,
        )
        if has_header
        else rx.fragment()
    )

    return rx.box(
        header_block,
        *children,
        style=rx.Style(
            {
                "width": "100%",
                "height": "100%",
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CARD,
                "padding": padding,
                "display": "flex",
                "flex_direction": "column",
            }
        ),
    )
