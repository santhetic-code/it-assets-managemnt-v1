"""
Komponen Progress Bar Reusable ITAM Pro.
Warna otomatis berdasarkan persentase: <70% biru, 70-85% amber, >85% merah.
"""

from typing import Any

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius, Size


def metric_progress_bar(
    label: Any,
    percent: Any,
    percent_label: Any,
) -> rx.Component:
    """Bar persentase dengan warna otomatis berdasarkan ambang batas beban."""
    bar_color = rx.cond(
        percent >= 80,
        Color.PROGRESS_HIGH,
        rx.cond(
            percent >= 70,
            Color.PROGRESS_MED,
            Color.PROGRESS_LOW,
        ),
    )
    text_color = rx.cond(
        percent >= 80,
        Color.DANGER_FG,
        rx.cond(
            percent >= 70,
            Color.AMBER_600,
            Color.PROGRESS_LOW,
        ),
    )
    clamped_width = rx.cond(percent > 100, "100%", f"{percent}%")

    return rx.vstack(
        rx.hstack(
            rx.text(
                label,
                font_size=FontSize.SM,
                font_weight=FontWeight.MEDIUM,
                color=Color.TEXT,
            ),
            rx.text(
                percent_label,
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=text_color,
                style=rx.Style({"font_variant_numeric": "tabular-nums"}),
            ),
            width="100%",
            justify="between",
            align="center",
        ),
        rx.box(
            rx.box(
                style=rx.Style(
                    {
                        "width": clamped_width,
                        "height": "100%",
                        "background_color": bar_color,
                        "border_radius": Radius.FULL,
                        "transition": "width 0.35s ease",
                    }
                ),
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "height": Size.PROGRESS_H,
                    "background_color": Color.PROGRESS_TRACK,
                    "border_radius": Radius.FULL,
                    "overflow": "hidden",
                }
            ),
        ),
        spacing="2",
        width="100%",
    )
