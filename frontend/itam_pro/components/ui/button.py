"""
Komponen Tombol Reusable ITAM Pro.
"""
from typing import Any, Literal

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size


def primary_button(
    label: str | rx.Var[str],
    on_click: Any | None = None,
    is_loading: Any = False,
    button_type: Literal["button", "reset", "submit"] = "button",
    full_width: bool = True,
    margin_top: str = "0px",
) -> rx.Component:
    """Tombol aksi utama (tinggi 48px) dengan dukungan state loading."""
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


def secondary_button(
    label: str | rx.Var[str],
    on_click: Any | None = None,
    icon_tag: str | None = None,
) -> rx.Component:
    """Tombol sekunder putih dengan border Color.INPUT_BORDER (contoh: 'Export Laporan')."""
    return rx.el.button(
        rx.hstack(
            rx.icon(tag=icon_tag, size=Size.ICON_SM, color=Color.TEXT)
            if icon_tag
            else rx.fragment(),
            rx.text(
                label,
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            spacing="2",
            align="center",
        ),
        type="button",
        on_click=on_click,
        style=rx.Style(
            {
                "height": Size.BUTTON_MD_H,
                "padding": "0 18px",
                "background_color": Color.SURFACE,
                "color": Color.TEXT,
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": Radius.CONTROL,
                "font_family": FONT_FAMILY,
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "cursor": "pointer",
                "white_space": "nowrap",
                "transition": "background-color 0.15s ease, border-color 0.15s ease",
            }
        ),
        _hover=rx.Style(
            {
                "background_color": Color.SURFACE_HOVER,
                "border_color": Color.ACCENT,
            }
        ),
    )


def action_primary_button(
    label: str | rx.Var[str],
    on_click: Any | None = None,
) -> rx.Component:
    """Tombol utama di header halaman (tinggi 42px, warna Color.ACCENT, contoh: '+ Tambah Aset')."""
    return rx.el.button(
        rx.text(
            label,
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.WHITE,
        ),
        type="button",
        on_click=on_click,
        style=rx.Style(
            {
                "height": Size.BUTTON_MD_H,
                "padding": "0 18px",
                "background_color": Color.ACCENT,
                "color": Color.WHITE,
                "border": "none",
                "border_radius": Radius.CONTROL,
                "font_family": FONT_FAMILY,
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "cursor": "pointer",
                "white_space": "nowrap",
                "transition": "background-color 0.15s ease",
            }
        ),
        _hover=rx.Style(
            {
                "background_color": Color.ACCENT_BRIGHT,
            }
        ),
    )
