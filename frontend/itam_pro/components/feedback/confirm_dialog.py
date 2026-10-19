"""
Komponen Dialog Konfirmasi Hapus Reusable ITAM Pro.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Size, Space


def confirm_delete_dialog(
    is_open: Any,
    title: str,
    description: Any,
    on_cancel: Any,
    on_confirm: Any,
) -> rx.Component:
    """Dialog modal konfirmasi sebelum menghapus data."""
    return rx.cond(
        is_open,
        rx.box(
            rx.box(
                on_click=on_cancel,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.center(
                            rx.icon(
                                tag="triangle-alert",
                                size=Size.ICON_MD,
                                color=Color.DANGER_FG,
                            ),
                            width="40px",
                            height="40px",
                            background_color=Color.DANGER_BG,
                            border_radius=Radius.CONTROL,
                            flex_shrink="0",
                        ),
                        rx.vstack(
                            rx.text(
                                title,
                                font_size=FontSize.SUBTITLE,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                description,
                                font_size=FontSize.SM,
                                font_weight=FontWeight.REGULAR,
                                color=Color.MUTED,
                                line_height="1.45",
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=on_cancel,
                            style=rx.Style(
                                {
                                    "height": Size.FILTER_CONTROL_H,
                                    "padding": "0 18px",
                                    "background_color": Color.SURFACE,
                                    "color": Color.TEXT,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Ya, Hapus",
                            type="button",
                            on_click=on_confirm,
                            style=rx.Style(
                                {
                                    "height": Size.FILTER_CONTROL_H,
                                    "padding": "0 18px",
                                    "background_color": Color.DANGER_FG,
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                        margin_top=Space.S3,
                    ),
                    spacing="4",
                    width="100%",
                ),
                role="alertdialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "92%",
                        "max_width": "420px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": Space.S6,
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )
