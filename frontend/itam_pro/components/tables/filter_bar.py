"""
Komponen Filter Bar Generik ITAM Pro.
Kotak pencarian 320px + N dropdown master + tautan 'Reset filter' + jumlah hasil di kanan.
"""
from typing import Any, TypedDict

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size, Space


class FilterDropdownConfig(TypedDict):
    label: str
    value: Any
    options: Any
    on_change: Any


def _filter_dropdown(cfg: FilterDropdownConfig) -> rx.Component:
    """Render satu dropdown filter dari konfigurasi master."""
    return rx.box(
        rx.el.select(
            rx.el.option(cfg["label"], value="Semua"),
            rx.foreach(
                cfg["options"],
                lambda opt: rx.el.option(opt, value=opt),
            ),
            value=cfg["value"],
            on_change=cfg["on_change"],
            aria_label=cfg["label"],
            style=rx.Style(
                {
                    "height": Size.FILTER_CONTROL_H,
                    "padding": "0 32px 0 12px",
                    "background_color": Color.SURFACE,
                    "color": Color.TEXT,
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.MEDIUM,
                    "cursor": "pointer",
                    "outline": "none",
                    "appearance": "none",
                    "-webkit-appearance": "none",
                }
            ),
        ),
        rx.icon(
            tag="chevron-down",
            size=15,
            color=Color.MUTED,
            style=rx.Style(
                {
                    "position": "absolute",
                    "right": "10px",
                    "top": "50%",
                    "transform": "translateY(-50%)",
                    "pointer_events": "none",
                }
            ),
        ),
        style=rx.Style({"position": "relative", "display": "inline-flex"}),
    )


def table_filter_bar(
    search_value: Any,
    on_search_change: Any,
    search_placeholder: str,
    dropdowns: list[FilterDropdownConfig],
    on_reset: Any,
    result_count_text: Any,
) -> rx.Component:
    """Bar filter generik untuk halaman bertabel."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon(
                    tag="search",
                    size=Size.ICON_SM,
                    color=Color.MUTED,
                    stroke_width=2,
                    flex_shrink="0",
                ),
                rx.el.input(
                    type="text",
                    placeholder=search_placeholder,
                    value=search_value,
                    on_change=on_search_change,
                    style=rx.Style(
                        {
                            "width": "100%",
                            "height": "100%",
                            "border": "none",
                            "outline": "none",
                            "background": "transparent",
                            "color": Color.TEXT,
                            "font_family": FONT_FAMILY,
                            "font_size": FontSize.SM,
                            "font_weight": FontWeight.REGULAR,
                        }
                    ),
                ),
                spacing="2",
                align="center",
                style=rx.Style(
                    {
                        "width": Size.FILTER_SEARCH_W,
                        "max_width": "100%",
                        "height": Size.FILTER_CONTROL_H,
                        "padding": "0 12px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.INPUT_BORDER}",
                        "border_radius": Radius.CONTROL,
                    }
                ),
                _focus_within=rx.Style(
                    {
                        "border_color": Color.ACCENT,
                        "box_shadow": Color.FOCUS_RING,
                    }
                ),
            ),
            *[_filter_dropdown(d) for d in dropdowns],
            rx.el.button(
                "Reset filter",
                type="button",
                on_click=on_reset,
                style=rx.Style(
                    {
                        "background": "transparent",
                        "border": "none",
                        "padding": "0 6px",
                        "height": Size.FILTER_CONTROL_H,
                        "color": Color.ACCENT,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.SEMIBOLD,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
                _hover=rx.Style({"color": Color.ACCENT_BRIGHT}),
            ),
            spacing="3",
            align="center",
            wrap="wrap",
        ),
        rx.text(
            result_count_text,
            font_size=FontSize.SM,
            font_weight=FontWeight.MEDIUM,
            color=Color.MUTED,
            white_space="nowrap",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "padding": "16px 20px",
                "border_bottom": f"1px solid {Color.BORDER}",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S3,
            }
        ),
    )


__all__ = [
    "FilterDropdownConfig",
    "table_filter_bar",
]
