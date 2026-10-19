"""
Komponen Tabs Reusable ITAM Pro.
Menampilkan daftar tab dengan badge jumlah unit di sebelah label.
"""
from typing import Any, TypedDict

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Space


class TabItemConfig(TypedDict):
    key: str
    label: str
    count: Any


def _tab_button(
    item: TabItemConfig,
    active_tab: Any,
    on_change: Any,
) -> rx.Component:
    """Render satu tombol tab beserta badge jumlah unit."""
    tab_key = item["key"]
    is_active = active_tab == tab_key

    return rx.el.button(
        rx.hstack(
            rx.text(
                item["label"],
                font_size=FontSize.BASE,
                font_weight=rx.cond(is_active, FontWeight.BOLD, FontWeight.SEMIBOLD),
                color=rx.cond(is_active, Color.ACCENT, Color.MUTED),
            ),
            rx.box(
                rx.text(
                    item["count"],
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=rx.cond(is_active, Color.ACCENT, Color.MUTED),
                    line_height="1",
                ),
                style=rx.Style(
                    {
                        "padding": "3px 8px",
                        "background_color": rx.cond(
                            is_active,
                            Color.INFO_BG,
                            Color.TABLE_HEADER_BG,
                        ),
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.FULL,
                        "display": "inline-flex",
                        "align_items": "center",
                        "justify_content": "center",
                    }
                ),
            ),
            spacing="2",
            align="center",
        ),
        type="button",
        on_click=on_change(tab_key),
        style=rx.Style(
            {
                "padding": "12px 18px",
                "background": "transparent",
                "border": "none",
                "border_bottom": rx.cond(
                    is_active,
                    f"2.5px solid {Color.ACCENT}",
                    "2.5px solid transparent",
                ),
                "font_family": FONT_FAMILY,
                "cursor": "pointer",
                "display": "inline-flex",
                "align_items": "center",
                "white_space": "nowrap",
                "transition": "color 0.15s ease, border-color 0.15s ease",
            }
        ),
        _hover=rx.Style(
            {
                "background_color": Color.SURFACE_HOVER,
            }
        ),
    )


def app_tabs(
    tabs: list[TabItemConfig],
    active_tab: Any,
    on_change: Any,
) -> rx.Component:
    """Baris navigasi tab di bagian atas kartu tabel."""
    return rx.box(
        rx.hstack(
            *[_tab_button(tab, active_tab, on_change) for tab in tabs],
            spacing="1",
            align="center",
            style=rx.Style({"overflow_x": "auto"}),
        ),
        style=rx.Style(
            {
                "width": "100%",
                "padding": f"0 {Space.S5}",
                "background_color": Color.SURFACE,
                "border_bottom": f"1px solid {Color.BORDER}",
            }
        ),
    )


__all__ = ["TabItemConfig", "app_tabs"]
