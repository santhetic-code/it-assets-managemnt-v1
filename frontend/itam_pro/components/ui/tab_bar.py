"""Komponen Tab Bar (dengan badge hitungan) & Segmented View Toggle ITAM Pro."""

from typing import Any, TypedDict

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Space


class ViewToggleOption(TypedDict, total=False):
    value: str
    label: str
    icon: str
    min_width: str


def view_toggle(
    options: list[ViewToggleOption],
    active: Any,
    on_change: Any,
) -> rx.Component:
    """Segmented control kanan (mis. Tabel | Peta IP) bergaya IP & Server (VM)."""
    buttons: list[rx.Component] = []
    for opt in options:
        val = opt["value"]
        is_sel = active == val
        ic = opt.get("icon")
        min_w = opt.get("min_width", "84px")
        buttons.append(
            rx.el.button(
                rx.hstack(
                    rx.icon(tag=ic, size=14, flex_shrink="0") if ic else rx.fragment(),
                    rx.text(
                        opt["label"],
                        font_size=FontSize.SM,
                        font_weight=FontWeight.BOLD,
                        style=rx.Style({"white_space": "nowrap"}),
                    ),
                    spacing="2",
                    align="center",
                ),
                type="button",
                aria_pressed=is_sel,
                on_click=on_change(val),
                style=rx.Style(
                    {
                        "height": "32px",
                        "min_width": min_w,
                        "padding": "0 12px",
                        "border_radius": "8px",
                        "border": "none",
                        "white_space": "nowrap",
                        "display": "inline-flex",
                        "align_items": "center",
                        "justify_content": "center",
                        "background_color": rx.cond(is_sel, Color.WHITE, "transparent"),
                        "color": rx.cond(is_sel, Color.TEXT, Color.MUTED),
                        "box_shadow": rx.cond(is_sel, Shadow.SEGMENT_ACTIVE, "none"),
                        "cursor": "pointer",
                        "font_family": FONT_FAMILY,
                        "transition": "all 0.15s ease",
                    }
                ),
            )
        )

    return rx.hstack(
        *buttons,
        spacing="1",
        align="center",
        padding="3px",
        flex_shrink="0",
        background_color=Color.SLATE_100,
        border_radius=Radius.CONTROL,
        border=f"1px solid {Color.BORDER}",
    )


def _tab_bar_button(item: dict[str, Any] | Any, active: Any, on_change: Any) -> rx.Component:
    tab_key = item.get("key") or item.get("value", "") if isinstance(item, dict) else item["key"]
    is_active = active == tab_key
    has_count = isinstance(item, dict) and "count" in item and item["count"] is not None

    badge_elem = (
        rx.box(
            rx.text(
                item["count"],
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=rx.cond(is_active, Color.ACCENT, Color.MUTED),
                line_height="1",
                style=rx.Style({"font_variant_numeric": "tabular-nums"}),
            ),
            style=rx.Style(
                {
                    "padding": "3px 8px",
                    "background_color": rx.cond(is_active, Color.INFO_BG, Color.TABLE_HEADER_BG),
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
                "min_height": "44px",
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
        _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
    )


def tab_bar(
    tabs_with_count: list[dict[str, Any]] | Any,
    active: Any,
    on_change: Any,
    *,
    right_slot: rx.Component | None = None,
    card_container: bool = False,
) -> rx.Component:
    """Bar tab dengan badge hitungan + slot kanan opsional (view_toggle)."""
    tab_nodes = (
        [rx.foreach(tabs_with_count, lambda t: _tab_bar_button(t, active, on_change))]
        if isinstance(tabs_with_count, rx.Var)
        else [_tab_bar_button(t, active, on_change) for t in (tabs_with_count or [])]
    )

    base_style: dict[str, Any] = {
        "width": "100%",
        "padding": f"0 {Space.S4}",
        "background_color": Color.SURFACE,
        "display": "flex",
        "align_items": "center",
        "justify_content": "space-between",
        "gap": Space.S3,
    }
    if card_container:
        base_style.update(
            {
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CARD,
                "box_shadow": Shadow.TABLE_CARD,
            }
        )
    else:
        base_style["border_bottom"] = f"1px solid {Color.BORDER}"

    return rx.box(
        rx.hstack(
            *tab_nodes,
            spacing="1",
            align="center",
            style=rx.Style({"overflow_x": "auto", "flex": "1", "min_width": "0"}),
        ),
        right_slot if right_slot is not None else rx.fragment(),
        style=rx.Style(base_style),
    )


__all__ = ["ViewToggleOption", "tab_bar", "view_toggle"]
