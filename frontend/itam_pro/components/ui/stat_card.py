"""
Komponen Kartu KPI (Stat Card) Reusable ITAM Pro.
Dioptimalkan dengan pre-compiled static rx.Style untuk rendering kartu KPI yang cepat.
"""

import inspect
from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius, Shadow, Size, Space

_STAT_CARD_STYLE = rx.Style(
    {
        "width": "100%",
        "background_color": Color.SURFACE,
        "border": f"1px solid {Color.BORDER}",
        "border_radius": Radius.CARD,
        "padding": Space.S5,
        "display": "flex",
        "flex_direction": "column",
        "justify_content": "space-between",
        "transition": "all 0.15s ease",
        "_hover": {
            "border_color": Color.ACCENT,
            "transform": "translateY(-1px)",
            "box_shadow": Shadow.CARD_HOVER,
        },
    }
)

_STAT_CARD_PRIMARY_STYLE = rx.Style(
    {
        "width": "100%",
        "background_color": Color.BRAND,
        "border": f"1px solid {Color.BRAND}",
        "border_radius": Radius.CARD,
        "padding": Space.S5,
        "display": "flex",
        "flex_direction": "column",
        "justify_content": "space-between",
        "transition": "all 0.15s ease",
        "_hover": {
            "transform": "translateY(-1px)",
            "box_shadow": Shadow.CARD_HOVER,
        },
    }
)


def stat_card(
    item_or_label: dict[str, Any] | Any,
    value: Any = None,
    icon: str = "",
    *,
    tone: str = "info",
    value_tone: str = "default",
    note: str = "",
    description: str = "",
    note_tone: str = "neutral",
    href: str = "",
    primary: bool = False,
) -> rx.Component:
    """Render satu kartu KPI dari objek dictionary/Var state atau argumen posisional."""
    effective_note = note if (isinstance(note, rx.Var) or bool(note)) else description
    card_href = href
    is_primary: Any = primary
    val_tone: Any = value_tone

    if value is None and not isinstance(item_or_label, str):
        label = item_or_label["label"]
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
            try:
                card_href = item_or_label["href"]
            except Exception:
                card_href = href
            try:
                is_primary = item_or_label["primary"]
            except Exception:
                is_primary = primary
            try:
                val_tone = item_or_label["value_tone"]
            except Exception:
                val_tone = value_tone
    else:
        label = item_or_label
        val = value
        ic = icon
        chip_tone_val = tone
        note_val = effective_note
        note_tone_val = note_tone

    chip_fg = rx.match(
        chip_tone_val,
        ("success", Color.SUCCESS_FG),
        ("warning", Color.WARNING_FG),
        ("danger", Color.DANGER_FG),
        ("purple", Color.PURPLE_FG),
        Color.INFO_FG,
    )
    chip_bg = rx.match(
        chip_tone_val,
        ("success", Color.SUCCESS_BG),
        ("warning", Color.WARNING_BG),
        ("danger", Color.DANGER_BG),
        ("purple", Color.PURPLE_BG),
        Color.INFO_BG,
    )
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
        ("danger", Color.DANGER_FG),
        ("success", Color.SUCCESS_FG),
        ("accent", Color.ACCENT),
        Color.TEXT,
    )

    is_primary_bool = is_primary is True
    if isinstance(ic, rx.Var):
        icon_chip: rx.Component = rx.cond(
            ic != "",
            rx.center(
                rx.icon(
                    tag=ic,
                    size=Size.ICON_MD,
                    color=Color.WHITE if is_primary_bool else chip_fg,
                    stroke_width=2,
                ),
                width=Size.STAT_ICON_CHIP,
                height=Size.STAT_ICON_CHIP,
                background_color=Color.WHITE_ALPHA_16 if is_primary_bool else chip_bg,
                border_radius=Radius.CHIP,
                flex_shrink="0",
            ),
            rx.fragment(),
        )
    elif ic:
        icon_chip = rx.center(
            rx.icon(
                tag=ic,
                size=Size.ICON_MD,
                color=Color.WHITE if is_primary_bool else chip_fg,
                stroke_width=2,
            ),
            width=Size.STAT_ICON_CHIP,
            height=Size.STAT_ICON_CHIP,
            background_color=Color.WHITE_ALPHA_16 if is_primary_bool else chip_bg,
            border_radius=Radius.CHIP,
            flex_shrink="0",
        )
    else:
        icon_chip = rx.fragment()

    header_row = rx.hstack(
        rx.text(
            label,
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.WHITE_ALPHA_80 if is_primary_bool else Color.MUTED,
            line_height="1.3",
            letter_spacing="0.04em",
            style=rx.Style({"text_transform": "uppercase"}),
        ),
        icon_chip,
        width="100%",
        justify="between",
        align="center",
    )

    card_box = rx.box(
        header_row,
        rx.text(
            val,
            font_size=FontSize.KPI_VALUE,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.WHITE if is_primary_bool else value_color,
            line_height="1.15",
            letter_spacing="-0.02em",
            margin_top="10px",
            margin_bottom="6px",
            style=rx.Style({"font_variant_numeric": "tabular-nums"}),
        ),
        rx.cond(
            note_val != "",
            rx.text(
                note_val,
                font_size=FontSize.FOOTER,
                font_weight=FontWeight.MEDIUM,
                color=Color.WHITE_ALPHA_80 if is_primary_bool else note_color,
                line_height="1.3",
            ),
            rx.fragment(),
        ),
        style=_STAT_CARD_PRIMARY_STYLE if is_primary_bool else _STAT_CARD_STYLE,
    )

    return rx.cond(
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


# Sesuaikan signature agar dikenali rx.foreach(items, stat_card) sebagai 1 parameter render_fn
setattr(
    stat_card,
    "__signature__",
    inspect.Signature([inspect.Parameter("item", inspect.Parameter.POSITIONAL_OR_KEYWORD)]),
)


__all__ = ["stat_card"]
