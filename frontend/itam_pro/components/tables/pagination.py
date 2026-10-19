"""
Komponen Pagination Generik ITAM Pro.
'Menampilkan X-Y dari N', tombol prev/next, halaman aktif #1D4ED8, dukungan elipsis.
"""
from typing import Any

import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size, Space


def _page_token_button(
    token: Any,
    current_page_str: Any,
    on_page_select: Any,
) -> rx.Component:
    """Render satu nomor halaman atau tanda elipsis '...'."""
    is_active = token == current_page_str
    return rx.cond(
        token == "...",
        rx.center(
            rx.text(
                "...",
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
            ),
            width=Size.PAGINATION_BTN,
            height=Size.PAGINATION_BTN,
        ),
        rx.el.button(
            token,
            type="button",
            on_click=on_page_select(token),
            style=rx.Style(
                {
                    "min_width": Size.PAGINATION_BTN,
                    "height": Size.PAGINATION_BTN,
                    "padding": "0 10px",
                    "background_color": rx.cond(is_active, Color.ACCENT, Color.SURFACE),
                    "color": rx.cond(is_active, Color.WHITE, Color.TEXT),
                    "border": rx.cond(
                        is_active,
                        f"1px solid {Color.ACCENT}",
                        f"1px solid {Color.INPUT_BORDER}",
                    ),
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.BOLD,
                    "cursor": "pointer",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
                    "transition": "background-color 0.15s ease",
                }
            ),
            _hover=rx.Style(
                {
                    "background_color": rx.cond(
                        is_active,
                        Color.ACCENT_BRIGHT,
                        Color.SURFACE_HOVER,
                    ),
                }
            ),
        ),
    )


def table_pagination(
    summary_text: Any,
    current_page: Any,
    current_page_str: Any,
    total_pages: Any,
    page_tokens: Any,
    on_prev: Any,
    on_next: Any,
    on_page_select: Any,
) -> rx.Component:
    """Footer paginasi generik untuk komponen tabel."""
    is_first = current_page <= 1
    is_last = current_page >= total_pages

    return rx.box(
        rx.text(
            summary_text,
            font_size=FontSize.SM,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
        ),
        rx.hstack(
            # Tombol Sebelumnya
            rx.el.button(
                rx.hstack(
                    rx.icon(tag="chevron-left", size=15, color=Color.TEXT),
                    rx.text(
                        "Sebelumnya",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    spacing="1",
                    align="center",
                ),
                type="button",
                disabled=is_first,
                on_click=on_prev,
                style=rx.Style(
                    {
                        "height": Size.PAGINATION_BTN,
                        "padding": "0 12px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.INPUT_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "cursor": rx.cond(is_first, "not-allowed", "pointer"),
                        "opacity": rx.cond(is_first, "0.45", "1"),
                        "display": "inline-flex",
                        "align_items": "center",
                    }
                ),
            ),
            # Daftar Nomor Halaman + Elipsis
            rx.hstack(
                rx.foreach(
                    page_tokens,
                    lambda tok: _page_token_button(tok, current_page_str, on_page_select),
                ),
                spacing="1",
                align="center",
            ),
            # Tombol Berikutnya
            rx.el.button(
                rx.hstack(
                    rx.text(
                        "Berikutnya",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.icon(tag="chevron-right", size=15, color=Color.TEXT),
                    spacing="1",
                    align="center",
                ),
                type="button",
                disabled=is_last,
                on_click=on_next,
                style=rx.Style(
                    {
                        "height": Size.PAGINATION_BTN,
                        "padding": "0 12px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.INPUT_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "cursor": rx.cond(is_last, "not-allowed", "pointer"),
                        "opacity": rx.cond(is_last, "0.45", "1"),
                        "display": "inline-flex",
                        "align_items": "center",
                    }
                ),
            ),
            spacing="2",
            align="center",
            wrap="wrap",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "padding": "14px 20px",
                "border_top": f"1px solid {Color.BORDER}",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S3,
            }
        ),
    )
