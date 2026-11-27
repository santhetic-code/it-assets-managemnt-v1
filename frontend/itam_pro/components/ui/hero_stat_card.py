"""Komponen Kartu KPI Hero (Gradien Navy -> Biru + Ring Glow + Donut Persen)."""

from typing import Any

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow


def _choose(cond: Any, true_val: Any, false_val: Any) -> Any:
    if isinstance(cond, rx.Var):
        return rx.cond(cond, true_val, false_val)
    return true_val if cond else false_val


def hero_stat_card(
    icon: str,
    label: str | rx.Var[str],
    value: Any,
    subtext: str | rx.Var[str] = "",
    percent: Any = None,
    percent_caption: str | rx.Var[str] = "",
    link_text: str | rx.Var[str] = "",
    href: str | rx.Var[str] = "",
    pill: str | rx.Var[str] | None = None,
    *,
    on_click: Any | None = None,
    is_active: bool | rx.Var[bool] = False,
    donut_gradient: Any = None,
    donut_label: Any = None,
    value_class_name: str = "",
    value_font_size: str = "34px",
    gradient: str = Color.GRADIENT_NAVY,
    glow_ring: bool = True,
) -> rx.Component:
    """Kartu KPI Hero pertama bergaya IP & Server (VM) / Credential Manager."""
    has_pill = isinstance(pill, rx.Var) or bool(pill)
    pill_comp: rx.Component = (
        rx.cond(
            pill != "",
            rx.box(
                rx.text(
                    pill,
                    font_size="10px",
                    font_weight=FontWeight.BOLD,
                    color=Color.WHITE,
                ),
                padding="2px 8px",
                border_radius=Radius.FULL,
                style=rx.Style({"background_color": Color.WHITE_ALPHA_22}),
            ),
            rx.fragment(),
        )
        if isinstance(pill, rx.Var)
        else (
            rx.box(
                rx.text(
                    pill,
                    font_size="10px",
                    font_weight=FontWeight.BOLD,
                    color=Color.WHITE,
                ),
                padding="2px 8px",
                border_radius=Radius.FULL,
                style=rx.Style({"background_color": Color.WHITE_ALPHA_22}),
            )
            if has_pill
            else rx.fragment()
        )
    )

    show_donut = (percent is not None) or (donut_gradient is not None)
    donut_block: rx.Component = rx.fragment()
    if show_donut:
        ring_bg = (
            donut_gradient
            if donut_gradient is not None
            else (
                f"conic-gradient({Color.WHITE} 0% {percent}%, "
                f"{Color.WHITE_ALPHA_20} {percent}% 100%)"
            )
        )
        center_text = donut_label if donut_label is not None else f"{percent}%"
        has_caption = isinstance(percent_caption, rx.Var) or bool(percent_caption)
        donut_ring = rx.center(
            rx.center(
                rx.text(
                    center_text,
                    font_size="12px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.WHITE,
                    style=rx.Style({"font_variant_numeric": "tabular-nums"}),
                ),
                width="48px",
                height="48px",
                border_radius="50%",
                style=rx.Style({"background_color": Color.NAVY_DONUT_INNER}),
            ),
            width="64px",
            height="64px",
            border_radius="50%",
            flex_shrink="0",
            style=rx.Style({"background": ring_bg}),
        )
        donut_block = (
            rx.vstack(
                donut_ring,
                rx.text(
                    percent_caption,
                    font_size="10.5px",
                    font_weight=FontWeight.MEDIUM,
                    color=Color.WHITE_ALPHA_80,
                    text_align="center",
                    line_height="1.15",
                ),
                spacing="1",
                align="center",
                flex_shrink="0",
            )
            if has_caption
            else donut_ring
        )

    value_kwargs: dict[str, Any] = {}
    if value_class_name:
        value_kwargs["class_name"] = value_class_name

    has_subtext = isinstance(subtext, rx.Var) or bool(subtext)
    has_link_text = isinstance(link_text, rx.Var) or bool(link_text)

    left_col = rx.vstack(
        rx.hstack(
            rx.center(
                rx.icon(tag=icon, size=17, color=Color.WHITE, stroke_width=2),
                width="34px",
                height="34px",
                border_radius=Radius.CONTROL,
                flex_shrink="0",
                style=rx.Style({"background_color": Color.WHITE_ALPHA_16}),
            ),
            rx.text(
                label,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.WHITE_ALPHA_85,
                letter_spacing="0.06em",
                style=rx.Style({"text_transform": "uppercase"}),
            ),
            pill_comp,
            spacing="2",
            align="center",
            wrap="wrap",
        ),
        rx.text(
            value,
            font_size=value_font_size,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.WHITE,
            line_height="1.1",
            margin_top="4px",
            style=rx.Style(
                {
                    "font_variant_numeric": "tabular-nums",
                    "word_break": "break-word",
                }
            ),
            **value_kwargs,
        ),
        rx.text(
            subtext,
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.MEDIUM,
            color=Color.WHITE_ALPHA_82,
            line_height="1.3",
        )
        if has_subtext
        else rx.fragment(),
        rx.text(
            link_text,
            font_size="11.5px",
            font_weight=FontWeight.BOLD,
            color=Color.WHITE_ALPHA_95,
            margin_top="2px",
        )
        if has_link_text
        else rx.fragment(),
        spacing="2",
        align="start",
        style=rx.Style({"flex": "1", "min_width": "0"}),
    )

    inner_content = (
        rx.hstack(
            left_col,
            donut_block,
            width="100%",
            justify="between",
            align="center",
            spacing="3",
        )
        if show_donut
        else left_col
    )

    default_shadow = Shadow.HERO_CARD_ACTIVE if glow_ring else Shadow.HERO_CARD
    card_style = rx.Style(
        {
            "background": gradient,
            "border": _choose(
                is_active,
                f"2px solid {Color.CHART_MONITOR}",
                "1px solid transparent",
            ),
            "border_radius": Radius.KPI_CARD,
            "padding": "16px 20px",
            "width": "100%",
            "height": "100%",
            "text_align": "left",
            "cursor": "pointer" if (on_click is not None or bool(href)) else "default",
            "font_family": FONT_FAMILY,
            "box_shadow": _choose(
                is_active,
                Shadow.HERO_CARD_ACTIVE,
                default_shadow,
            ),
            "transition": "all 150ms ease",
            "_hover": {
                "transform": "translateY(-2px)",
                "box_shadow": Shadow.HERO_CARD_HOVER,
            },
            "_focus_visible": {
                "outline": "none",
                "box_shadow": f"0 0 0 3px {Color.ACCENT}",
            },
        }
    )

    if on_click is not None:
        return rx.el.button(
            inner_content,
            type="button",
            aria_pressed=is_active,
            on_click=on_click,
            style=card_style,
        )

    card_box = rx.box(inner_content, style=card_style)
    if isinstance(href, rx.Var):
        return rx.cond(
            href != "",
            rx.link(card_box, href=href, underline="none", text_decoration="none", width="100%"),
            card_box,
        )
    if href:
        return rx.link(card_box, href=href, underline="none", text_decoration="none", width="100%")
    return card_box


__all__ = ["hero_stat_card"]
