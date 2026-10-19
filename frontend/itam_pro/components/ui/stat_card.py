"""
Komponen Kartu KPI (Stat Card) Reusable ITAM Pro.
Label 13px muted, angka 32px weight 800, keterangan 12.5px, chip ikon 36px di kanan atas.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius, Size, Space


def stat_card(item: dict[str, Any]) -> rx.Component:
    """Render satu kartu KPI dari objek dictionary state."""
    chip_fg = rx.match(
        item["chip_tone"],
        ("success", Color.SUCCESS_FG),
        ("warning", Color.WARNING_FG),
        ("danger", Color.DANGER_FG),
        ("purple", Color.PURPLE_FG),
        Color.INFO_FG,
    )
    chip_bg = rx.match(
        item["chip_tone"],
        ("success", Color.SUCCESS_BG),
        ("warning", Color.WARNING_BG),
        ("danger", Color.DANGER_BG),
        ("purple", Color.PURPLE_BG),
        Color.INFO_BG,
    )
    note_color = rx.match(
        item["note_tone"],
        ("success", Color.SUCCESS_FG),
        ("warning", Color.WARNING_FG),
        ("danger", Color.DANGER_FG),
        Color.MUTED,
    )

    return rx.box(
        # Baris Atas: Label 13px muted + Chip Ikon 36px
        rx.hstack(
            rx.text(
                item["label"],
                font_size=FontSize.SM,
                font_weight=FontWeight.MEDIUM,
                color=Color.MUTED,
                line_height="1.3",
            ),
            rx.center(
                rx.icon(
                    tag=item["icon"],
                    size=Size.ICON_MD,
                    color=chip_fg,
                    stroke_width=2,
                ),
                width=Size.STAT_ICON_CHIP,
                height=Size.STAT_ICON_CHIP,
                background_color=chip_bg,
                border_radius=Radius.CHIP,
                flex_shrink="0",
            ),
            width="100%",
            justify="between",
            align="center",
        ),
        # Angka Utama 32px weight 800
        rx.text(
            item["value"],
            font_size=FontSize.KPI_VALUE,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.TEXT,
            line_height="1.15",
            letter_spacing="-0.02em",
            margin_top="10px",
            margin_bottom="6px",
        ),
        # Keterangan Bawah 12.5px
        rx.text(
            item["note"],
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.SEMIBOLD,
            color=note_color,
            line_height="1.3",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CARD,
                "padding": Space.S5,
                "display": "flex",
                "flex_direction": "column",
                "justify_content": "space-between",
            }
        ),
    )
