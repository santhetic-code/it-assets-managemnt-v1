"""Komponen Filter Bar Pill ('Futuristik') Reusable ITAM Pro (diambil dari IP & Server)."""

from typing import Any, TypedDict

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius


class PillSelectConfig(TypedDict, total=False):
    placeholder: str
    options: Any
    value: Any
    on_change: Any
    disabled: Any
    tooltip: Any


def pill_select(
    options: Any,
    value: Any,
    on_change: Any,
    placeholder: str,
    *,
    disabled: Any = False,
    tooltip: Any = None,
) -> rx.Component:
    """Dropdown berbentuk pill penuh dengan ikon chevron di dalam."""
    is_dis_var = isinstance(disabled, rx.Var)
    cursor_val = (
        rx.cond(disabled, "not-allowed", "pointer")
        if is_dis_var
        else ("not-allowed" if disabled else "pointer")
    )
    opacity_val = (
        rx.cond(disabled, "0.55", "1") if is_dis_var else ("0.55" if disabled else "1")
    )

    select_box = rx.box(
        rx.el.select(
            rx.el.option(placeholder, value=""),
            rx.foreach(options, lambda o: rx.el.option(o, value=o)),
            value=value,
            disabled=disabled,
            on_change=on_change,
            style=rx.Style(
                {
                    "height": "36px",
                    "padding": "0 30px 0 14px",
                    "background_color": "transparent",
                    "border": "none",
                    "color": Color.TEXT,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.MEDIUM,
                    "cursor": cursor_val,
                    "opacity": opacity_val,
                    "appearance": "none",
                    "-webkit-appearance": "none",
                    "outline": "none",
                }
            ),
        ),
        rx.icon(
            tag="chevron-down",
            size=14,
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
        style=rx.Style(
            {
                "position": "relative",
                "background_color": Color.SLATE_50,
                "border_radius": Radius.PILL,
                "border": f"1px solid {Color.BORDER}",
                "transition": "all 0.2s",
                "&:focus-within": {
                    "border_color": Color.ACCENT,
                    "box_shadow": Color.FOCUS_RING,
                },
            }
        ),
    )

    if tooltip is not None:
        return rx.tooltip(select_box, content=tooltip)
    return select_box


def pill_filter_bar(
    search_placeholder: str = "Cari...",
    selects: list[PillSelectConfig | rx.Component] | None = None,
    on_reset: Any | None = None,
    *,
    search_value: Any = "",
    on_search_change: Any = None,
    search_width: str = "220px",
    use_debounce: bool = True,
    extra_controls: rx.Component | None = None,
    right_slot: rx.Component | None = None,
    reset_aria_label: str = "Reset",
) -> rx.Component:
    """Bar filter pill penuh dengan pencarian berikon, dropdown pill, dan tombol reset bulat."""
    raw_input = rx.el.input(
        placeholder=search_placeholder,
        value=search_value,
        on_change=on_search_change,
        style=rx.Style(
            {
                "width": search_width,
                "max_width": "100%",
                "height": "36px",
                "border": "none",
                "background": "transparent",
                "color": Color.TEXT,
                "font_family": FONT_FAMILY,
                "font_size": FontSize.SM,
                "outline": "none",
            }
        ),
    )
    search_input = (
        rx.debounce_input(raw_input, debounce_timeout=300) if use_debounce else raw_input
    )

    select_nodes: list[rx.Component] = []
    for item in selects or []:
        if isinstance(item, dict):
            select_nodes.append(
                pill_select(
                    options=item["options"],
                    value=item["value"],
                    on_change=item["on_change"],
                    placeholder=item["placeholder"],
                    disabled=item.get("disabled", False),
                    tooltip=item.get("tooltip"),
                )
            )
        else:
            select_nodes.append(item)

    reset_btn: rx.Component = (
        rx.el.button(
            rx.icon(tag="rotate-ccw", size=14),
            type="button",
            on_click=on_reset,
            aria_label=reset_aria_label,
            style=rx.Style(
                {
                    "width": "36px",
                    "height": "36px",
                    "border_radius": "50%",
                    "background_color": Color.SLATE_100,
                    "color": Color.TEXT,
                    "border": "none",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
                    "cursor": "pointer",
                    "flex_shrink": "0",
                    "&:hover": {"background_color": Color.SLATE_200},
                }
            ),
        )
        if on_reset is not None
        else rx.fragment()
    )

    left_group = rx.hstack(
        rx.hstack(
            rx.icon(tag="search", size=16, color=Color.MUTED, flex_shrink="0"),
            search_input,
            spacing="2",
            align="center",
            style=rx.Style(
                {
                    "padding": "0 12px",
                    "background_color": Color.SLATE_50,
                    "border_radius": Radius.PILL,
                    "border": f"1px solid {Color.BORDER}",
                    "display": "flex",
                    "align_items": "center",
                    "transition": "all 0.2s",
                    "&:focus-within": {
                        "border_color": Color.ACCENT,
                        "box_shadow": Color.FOCUS_RING,
                    },
                }
            ),
        ),
        *select_nodes,
        extra_controls if extra_controls is not None else rx.fragment(),
        reset_btn,
        spacing="3",
        align="center",
        wrap="wrap",
    )

    return rx.hstack(
        left_group,
        right_slot if right_slot is not None else rx.fragment(),
        width="100%",
        justify="between" if right_slot is not None else "start",
        align="center",
        spacing="3",
        padding="12px",
        wrap="wrap",
        style=rx.Style(
            {
                "background_color": Color.FILTER_BAR_BG,
                "backdrop_filter": "blur(16px)",
                "border_bottom": f"1px solid {Color.BORDER}",
            }
        ),
    )


__all__ = ["PillSelectConfig", "pill_filter_bar", "pill_select"]
