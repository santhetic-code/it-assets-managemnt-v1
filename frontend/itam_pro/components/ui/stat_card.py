"""
Komponen Kartu KPI (Stat Card) Reusable ITAM Pro.
Mendukung pola interaktif IP & Server / Credential Manager serta kompatibilitas rx.foreach.
"""

import inspect
from typing import Any

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow


def _choose(cond: Any, true_val: Any, false_val: Any) -> Any:
    if isinstance(cond, rx.Var):
        return rx.cond(cond, true_val, false_val)
    return true_val if cond else false_val


def stat_card(
    item_or_label: dict[str, Any] | Any = None,
    value: Any = None,
    icon: str | rx.Var[str] | Any = "",
    *,
    label: str | rx.Var[str] | Any = None,
    tone: str | rx.Var[str] | Any = "info",
    value_tone: str | rx.Var[str] | Any = "default",
    note: str | rx.Var[str] | Any = "",
    subtext: str | rx.Var[str] | Any = "",
    description: str | rx.Var[str] | Any = "",
    note_tone: str | rx.Var[str] | Any = "neutral",
    progress: Any = None,
    progress_color: str | rx.Var[str] | None = None,
    status_badge: str | rx.Var[str] | None = None,
    status_badge_variant: str | rx.Var[str] = "success",
    link_text: str | rx.Var[str] = "",
    link_tone: str | rx.Var[str] = "accent",
    href: str | rx.Var[str] | Any = "",
    primary: bool | rx.Var[bool] | Any = False,
    on_click: Any | None = None,
    is_active: bool | rx.Var[bool] = False,
    disabled: bool | rx.Var[bool] = False,
    tooltip_text: str | rx.Var[str] | None = None,
    pill: str | rx.Var[str] | None = None,
    value_class_name: str = "",
) -> rx.Component:
    """Kartu KPI reusable: mendukung pola IP & Kredensial + kompatibilitas rx.foreach lama."""
    effective_note = (
        subtext
        if (isinstance(subtext, rx.Var) or bool(subtext))
        else (note if (isinstance(note, rx.Var) or bool(note)) else description)
    )
    card_href = href
    is_primary: Any = primary
    val_tone: Any = value_tone

    if (
        label is None
        and value is None
        and item_or_label is not None
        and not isinstance(item_or_label, str)
    ):
        card_label = item_or_label["label"]
        val = item_or_label["value"]
        ic = item_or_label["icon"]
        chip_tone_val = item_or_label["chip_tone"]
        note_val = item_or_label["note"]
        note_tone_val = item_or_label["note_tone"]
        if isinstance(item_or_label, dict):
            card_href = item_or_label.get("href", href)
            is_primary = item_or_label.get("primary", primary)
            val_tone = item_or_label.get("value_tone", value_tone)
        else:
            for attr_key, target in (
                ("href", "href"),
                ("primary", "primary"),
                ("value_tone", "value_tone"),
            ):
                try:
                    fetched = item_or_label[attr_key]
                    if target == "href":
                        card_href = fetched
                    elif target == "primary":
                        is_primary = fetched
                    else:
                        val_tone = fetched
                except Exception:
                    pass
    else:
        card_label = label if label is not None else item_or_label
        val = value
        ic = icon
        chip_tone_val = tone
        note_val = effective_note
        note_tone_val = note_tone

    chip_fg = rx.match(
        chip_tone_val,
        ("success", Color.GREEN_700),
        ("green", Color.GREEN_700),
        ("warning", Color.AMBER_600),
        ("amber", Color.AMBER_600),
        ("danger", Color.RED_600),
        ("red", Color.RED_600),
        ("purple", Color.PURPLE_600),
        ("sky", Color.SKY_600),
        Color.BLUE_600,
    )
    chip_bg = rx.match(
        chip_tone_val,
        ("success", Color.GREEN_100),
        ("green", Color.GREEN_100),
        ("warning", Color.AMBER_100),
        ("amber", Color.AMBER_100),
        ("danger", Color.RED_100),
        ("red", Color.RED_100),
        ("purple", Color.PURPLE_BG),
        ("sky", Color.SKY_100),
        Color.BLUE_100,
    )
    default_bar_color = rx.match(
        chip_tone_val,
        ("success", Color.GREEN_400),
        ("green", Color.GREEN_400),
        ("warning", Color.WARNING_BAR),
        ("amber", Color.WARNING_BAR),
        ("danger", Color.RED_600),
        ("red", Color.RED_600),
        ("purple", Color.PURPLE_600),
        ("sky", Color.SKY_600),
        Color.BLUE_600,
    )
    bar_fill = progress_color if progress_color is not None else default_bar_color

    note_color = rx.match(
        note_tone_val,
        ("success", Color.SUCCESS_FG),
        ("warning", Color.WARNING_FG),
        ("danger", Color.DANGER_FG),
        Color.MUTED,
    )
    value_color = rx.match(
        val_tone,
        ("warning", Color.AMBER_600),
        ("danger", Color.RED_700),
        ("success", Color.GREEN_700),
        ("accent", Color.ACCENT),
        Color.TEXT,
    )
    link_color = rx.match(
        link_tone,
        ("danger", Color.RED_600),
        ("success", Color.GREEN_700),
        ("warning", Color.AMBER_600),
        Color.ACCENT,
    )

    label_color = _choose(is_primary, Color.WHITE_ALPHA_80, Color.MUTED)
    icon_color = _choose(is_primary, Color.WHITE, chip_fg)
    icon_bg = _choose(is_primary, Color.WHITE_ALPHA_16, chip_bg)
    val_color = _choose(is_primary, Color.WHITE, value_color)
    footer_color = _choose(is_primary, Color.WHITE_ALPHA_80, note_color)

    # Chip ikon (kiri judul pada gaya modern IP & Kredensial)
    if isinstance(ic, rx.Var):
        icon_chip: rx.Component = rx.cond(
            ic != "",
            rx.center(
                rx.icon(tag=ic, size=17, color=icon_color, stroke_width=2),
                width="34px",
                height="34px",
                background_color=icon_bg,
                border_radius=Radius.CONTROL,
                flex_shrink="0",
            ),
            rx.fragment(),
        )
    elif ic:
        icon_chip = rx.center(
            rx.icon(tag=ic, size=17, color=icon_color, stroke_width=2),
            width="34px",
            height="34px",
            background_color=icon_bg,
            border_radius=Radius.CONTROL,
            flex_shrink="0",
        )
    else:
        icon_chip = rx.fragment()

    pill_comp: rx.Component = rx.fragment()
    if pill is not None:
        pill_bg = rx.match(chip_tone_val, ("danger", Color.RED_100), Color.BLUE_100)
        pill_fg = rx.match(chip_tone_val, ("danger", Color.RED_700), Color.ACCENT)
        pill_box = rx.box(
            rx.text(pill, font_size="10px", font_weight=FontWeight.BOLD, color=pill_fg),
            padding="2px 8px",
            border_radius=Radius.FULL,
            background_color=pill_bg,
            flex_shrink="0",
        )
        pill_comp = (
            rx.cond(pill != "", pill_box, rx.fragment())
            if isinstance(pill, rx.Var)
            else (pill_box if pill else rx.fragment())
        )

    header_row = rx.hstack(
        rx.hstack(
            icon_chip,
            rx.text(
                card_label,
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=label_color,
                line_height="1.3",
                letter_spacing="0.06em",
                style=rx.Style({"text_transform": "uppercase"}),
            ),
            spacing="2",
            align="center",
        ),
        pill_comp,
        width="100%",
        justify="between",
        align="center",
    )

    val_kwargs: dict[str, Any] = {}
    if value_class_name:
        val_kwargs["class_name"] = value_class_name

    value_text = rx.text(
        val,
        font_size=FontSize.KPI_VALUE,
        font_weight=FontWeight.EXTRABOLD,
        color=val_color,
        line_height="1.1",
        letter_spacing="-0.02em",
        style=rx.Style({"font_variant_numeric": "tabular-nums"}),
        **val_kwargs,
    )

    if status_badge is not None:
        sb_bg = rx.match(
            status_badge_variant,
            ("danger", Color.RED_100),
            ("warning", Color.AMBER_100),
            ("info", Color.BLUE_100),
            ("neutral", Color.SLATE_100),
            Color.GREEN_100,
        )
        sb_fg = rx.match(
            status_badge_variant,
            ("danger", Color.RED_700),
            ("warning", Color.AMBER_700),
            ("info", Color.BLUE_700),
            ("neutral", Color.MUTED),
            Color.GREEN_700,
        )
        value_row: rx.Component = rx.hstack(
            value_text,
            rx.box(
                rx.text(
                    status_badge,
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=sb_fg,
                ),
                style=rx.Style(
                    {
                        "padding": "3px 10px",
                        "border_radius": Radius.FULL,
                        "background_color": sb_bg,
                    }
                ),
            ),
            spacing="3",
            align="center",
            margin_top="4px",
        )
    else:
        value_row = rx.box(value_text, margin_top="4px")

    progress_block: rx.Component = (
        rx.box(
            rx.box(
                style=rx.Style(
                    {
                        "width": f"{progress}%",
                        "height": "100%",
                        "background_color": bar_fill,
                        "border_radius": Radius.FULL,
                        "transition": "width 0.3s ease",
                    }
                )
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "5px",
                    "background_color": Color.SLATE_200,
                    "border_radius": Radius.FULL,
                    "overflow": "hidden",
                    "margin_top": "4px",
                }
            ),
        )
        if progress is not None
        else rx.fragment()
    )

    has_link = isinstance(link_text, rx.Var) or bool(link_text)
    link_block: rx.Component = (
        rx.text(
            link_text,
            font_size="11.5px",
            font_weight=FontWeight.BOLD,
            color=_choose(is_primary, Color.WHITE_ALPHA_95, link_color),
            margin_top="2px",
        )
        if has_link
        else rx.fragment()
    )

    active_border_color = rx.match(chip_tone_val, ("danger", Color.RED_600), Color.ACCENT)
    hover_border_color = rx.match(
        chip_tone_val,
        ("danger", Color.RED_300),
        ("success", Color.GREEN_400),
        Color.ACCENT,
    )

    is_clickable = (on_click is not None) or isinstance(card_href, rx.Var) or bool(card_href)
    card_style = rx.Style(
        {
            "width": "100%",
            "height": "100%",
            "background_color": _choose(is_primary, Color.BRAND, Color.SURFACE),
            "border": _choose(
                is_primary,
                f"1px solid {Color.BRAND}",
                _choose(
                    is_active, f"2px solid {active_border_color}", f"1px solid {Color.BORDER}"
                ),
            ),
            "box_shadow": _choose(is_active, Shadow.KPI_ACTIVE_RING, Shadow.NONE),
            "border_radius": Radius.KPI_CARD,
            "padding": "16px 18px",
            "text_align": "left",
            "font_family": FONT_FAMILY,
            "display": "flex",
            "flex_direction": "column",
            "justify_content": "space-between",
            "cursor": _choose(disabled, "default", "pointer" if is_clickable else "default"),
            "transition": "all 150ms ease",
            "_hover": {
                "border_color": _choose(is_primary, Color.BRAND, hover_border_color),
                "transform": _choose(disabled, "none", "translateY(-2px)"),
                "box_shadow": _choose(disabled, Shadow.NONE, Shadow.KPI_HOVER),
            },
            "_focus_visible": {
                "outline": "none",
                "box_shadow": f"0 0 0 3px {Color.ACCENT}",
            },
        }
    )

    body = rx.vstack(
        header_row,
        value_row,
        rx.cond(
            note_val != "",
            rx.text(
                note_val,
                font_size=FontSize.FOOTER,
                font_weight=FontWeight.MEDIUM,
                color=footer_color,
                line_height="1.3",
                text_align="left",
            ),
            rx.fragment(),
        ),
        progress_block,
        link_block,
        spacing="2",
        align="start",
        width="100%",
    )

    if on_click is not None:
        widget: rx.Component = rx.el.button(
            body,
            type="button",
            disabled=disabled,
            aria_pressed=is_active,
            on_click=on_click,
            style=card_style,
        )
    else:
        card_box = rx.box(body, style=card_style)
        if isinstance(card_href, rx.Var):
            widget = rx.cond(
                card_href != "",
                rx.link(
                    card_box,
                    href=card_href,
                    underline="none",
                    text_decoration="none",
                    width="100%",
                ),
                card_box,
            )
        elif card_href:
            widget = rx.link(
                card_box,
                href=card_href,
                underline="none",
                text_decoration="none",
                width="100%",
            )
        else:
            widget = card_box

    if tooltip_text is not None:
        return rx.tooltip(widget, content=tooltip_text)
    return widget


# Sesuaikan signature agar dikenali rx.foreach(items, stat_card) sebagai 1 parameter render_fn
setattr(
    stat_card,
    "__signature__",
    inspect.Signature([inspect.Parameter("item", inspect.Parameter.POSITIONAL_OR_KEYWORD)]),
)


__all__ = ["stat_card"]
