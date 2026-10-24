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
    item: TabItemConfig | Any,
    active_tab: Any,
    on_change: Any,
) -> rx.Component:
    if isinstance(item, dict):
        tab_key = item.get("key") or item.get("value", "")
    else:
        tab_key = item["key"]
    is_active = active_tab == tab_key
    has_count = isinstance(item, dict) and "count" in item and item["count"] is not None

    badge_elem = (
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
        )
        if has_count
        else rx.fragment()
    )

    return rx.el.button(
        rx.hstack(
            rx.text(
                item["label"],
                font_size=FontSize.BASE,
                font_weight=rx.cond(is_active, FontWeight.BOLD, FontWeight.SEMIBOLD),
                color=rx.cond(is_active, Color.ACCENT, Color.MUTED),
            ),
            badge_elem,
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
    tabs: (
        list[TabItemConfig]
        | rx.Var[list[dict[str, Any]]]
        | rx.Var[list[TabItemConfig]]
        | Any
    ) = None,
    active_tab: Any = None,
    on_change: Any = None,
    *,
    items: Any = None,
    active_value: Any = None,
) -> rx.Component:
    """Baris navigasi tab di bagian atas kartu tabel."""
    target_tabs = items if tabs is None and items is not None else tabs
    target_active = active_value if active_tab is None and active_value is not None else active_tab

    tab_children = (
        rx.foreach(target_tabs, lambda tab: _tab_button(tab, target_active, on_change))
        if isinstance(target_tabs, rx.Var)
        else [_tab_button(tab, target_active, on_change) for tab in (target_tabs or [])]
    )
    children = [tab_children] if isinstance(tab_children, rx.Component) else tab_children
    return rx.box(
        rx.hstack(
            *children,
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
