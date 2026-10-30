"""
Komponen Pagination Generik ITAM Pro.
'Menampilkan X-Y dari N', tombol prev/next, halaman aktif Color.ACCENT, dukungan elipsis.
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
            on_click=on_page_select(token) if on_page_select is not None else None,
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
    summary_text: Any = "",
    current_page: Any = 1,
    current_page_str: Any = "1",
    total_pages: Any = 1,
    page_tokens: Any = None,
    on_prev: Any = None,
    on_next: Any = None,
    on_page_select: Any = None,
    *,
    page: Any = None,
    total_items: Any = None,
    page_size: Any = None,
) -> rx.Component:
    """Footer paginasi generik untuk komponen tabel."""
    act_page = page if page is not None else current_page
    if page is None:
        act_page_str = current_page_str
    else:
        act_page_str = act_page.to(str) if hasattr(act_page, "to") else str(act_page)
    act_tokens = page_tokens if page_tokens is not None else [act_page_str]
    act_prev = on_prev
    act_next = on_next
    act_select = on_page_select

    if isinstance(summary_text, str) and summary_text == "" and total_items is not None:
        act_summary = rx.cond(
            total_items > 0,
            f"Total {total_items} item",
            "0 item",
        )
    else:
        act_summary = summary_text

    is_first = act_page <= 1
    is_last = act_page >= total_pages

    return rx.box(
        rx.text(
            act_summary,
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
                on_click=act_prev,
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
                    act_tokens,
                    lambda tok: _page_token_button(tok, act_page_str, act_select),
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
                on_click=act_next,
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
