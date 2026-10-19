"""
Komponen Detail Drawer Generik ITAM Pro.
Lebar 440px (100% di <900px), scrim rgba(10,26,68,.35), tab, 3 grup informasi,
footer aksi, tutup dengan Escape atau klik scrim.
"""
from typing import Any

from reflex_components_radix.themes.layout.box import Box
import reflex as rx

from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Size, Space

from .badge import status_badge
from .status_badge import asset_status_badge


class DrawerBox(Box):
    """Subclass Radix Box untuk mendukung trigger event on_key_down."""

    @classmethod
    def get_event_triggers(cls) -> dict[str, Any]:
        return {
            **super().get_event_triggers(),
            "on_key_down": rx.event.key_event,
        }


def _kv_row(item: dict[str, Any]) -> rx.Component:
    """Render satu baris pasangan Label - Nilai di dalam seksi drawer."""
    return rx.hstack(
        rx.text(
            item["label"],
            font_size=FontSize.SM,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
            style=rx.Style({"width": "42%", "flex_shrink": "0"}),
        ),
        rx.text(
            item["value"],
            font_size=FontSize.SM,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
            text_align="right",
            style=rx.Style({"width": "58%", "word_break": "break-word"}),
        ),
        width="100%",
        justify="between",
        align="start",
        padding_y="8px",
        style=rx.Style({"border_bottom": f"1px solid {Color.DIVIDER}"}),
    )


def _drawer_section(title: str, items_var: Any) -> rx.Component:
    """Bagian bergrup di dalam drawer (contoh: Informasi umum / Spesifikasi / Terkait)."""
    return rx.vstack(
        rx.text(
            title.upper(),
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            letter_spacing="0.06em",
        ),
        rx.vstack(
            rx.foreach(items_var, _kv_row),
            spacing="0",
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.TABLE_HEADER_BG,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CONTROL,
                    "padding": "4px 14px",
                }
            ),
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _history_row(item: dict[str, Any]) -> rx.Component:
    """Render satu baris riwayat/aktivitas pada tab kedua drawer."""
    return rx.vstack(
        rx.hstack(
            rx.text(
                item["event"],
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            rx.text(
                item["date"],
                font_size=FontSize.XS,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            width="100%",
            justify="between",
            align="center",
        ),
        rx.text(
            item["note"],
            font_size=FontSize.SM,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
        ),
        spacing="1",
        align="start",
        width="100%",
        padding="12px 14px",
        style=rx.Style(
            {
                "background_color": Color.TABLE_HEADER_BG,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CONTROL,
            }
        ),
    )


def _drawer_tab_button(
    label: str,
    tab_key: str,
    active_tab: Any,
    on_tab_change: Any,
) -> rx.Component:
    """Tombol tab di dalam Detail Drawer."""
    is_active = active_tab == tab_key
    return rx.el.button(
        label,
        type="button",
        on_click=on_tab_change(tab_key),
        style=rx.Style(
            {
                "padding": "10px 16px",
                "background": "transparent",
                "border": "none",
                "border_bottom": rx.cond(
                    is_active,
                    f"2px solid {Color.ACCENT}",
                    "2px solid transparent",
                ),
                "color": rx.cond(is_active, Color.ACCENT, Color.MUTED),
                "font_family": FONT_FAMILY,
                "font_size": FontSize.SM,
                "font_weight": rx.cond(is_active, FontWeight.BOLD, FontWeight.MEDIUM),
                "cursor": "pointer",
                "transition": "color 0.15s ease, border-color 0.15s ease",
            }
        ),
    )


def detail_drawer(
    is_open: Any,
    on_close: Any,
    on_key_down: Any,
    code_var: Any,
    title_var: Any,
    category_var: Any,
    status_var: Any,
    active_tab: Any,
    on_tab_change: Any,
    general_items: Any,
    spec_items: Any,
    related_items: Any,
    history_items: Any,
    on_edit: Any,
    on_delete: Any,
    tabs: tuple[tuple[str, str], tuple[str, str]] = (
        ("detail", " Rincian Aset"),
        ("history", "Riwayat & Log"),
    ),
) -> rx.Component:
    """
    Komponen Drawer Kanan Generik (440px).
    Menampilkan Informasi umum, Spesifikasi, dan Terkait, serta mendukung Escape & klik scrim.
    """
    tab1_key, tab1_label = tabs[0]
    tab2_key, tab2_label = tabs[1]

    return rx.cond(
        is_open,
        rx.box(
            # Scrim rgba(10, 26, 68, 0.35)
            rx.box(
                on_click=on_close,
                aria_hidden="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "60",
                    }
                ),
            ),
            # Panel Drawer Kanan 440px (Layar penuh di <900px)
            DrawerBox.create(
                # 1. Header Drawer + Tombol Tutup Berlabel
                rx.vstack(
                    rx.hstack(
                        rx.hstack(
                            rx.text(
                                code_var,
                                font_size=FontSize.SM,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.ACCENT,
                            ),
                            status_badge(label=category_var, variant="neutral"),
                            asset_status_badge(status_var),
                            spacing="2",
                            align="center",
                        ),
                        rx.el.button(
                            rx.hstack(
                                rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                                rx.text(
                                    "Tutup",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.MUTED,
                                ),
                                spacing="1",
                                align="center",
                            ),
                            type="button",
                            aria_label="Tutup panel detail",
                            on_click=on_close,
                            style=rx.Style(
                                {
                                    "padding": "6px 10px",
                                    "background_color": Color.TABLE_HEADER_BG,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "cursor": "pointer",
                                    "display": "inline-flex",
                                    "align_items": "center",
                                }
                            ),
                            _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
                        ),
                        width="100%",
                        justify="between",
                        align="center",
                    ),
                    rx.heading(
                        title_var,
                        font_size=FontSize.LOGO,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                        line_height="1.3",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                    padding="20px 24px 14px 24px",
                ),
                # 2. Baris Tab
                rx.hstack(
                    _drawer_tab_button(
                        label=tab1_label.strip(),
                        tab_key=tab1_key,
                        active_tab=active_tab,
                        on_tab_change=on_tab_change,
                    ),
                    _drawer_tab_button(
                        label=tab2_label.strip(),
                        tab_key=tab2_key,
                        active_tab=active_tab,
                        on_tab_change=on_tab_change,
                    ),
                    spacing="2",
                    width="100%",
                    padding_x="24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # 3. Body Drawer (Scrollable)
                rx.box(
                    rx.cond(
                        active_tab == tab1_key,
                        rx.vstack(
                            _drawer_section("Informasi umum", general_items),
                            _drawer_section("Spesifikasi", spec_items),
                            _drawer_section("Terkait", related_items),
                            spacing="5",
                            width="100%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.foreach(history_items, _history_row),
                            spacing="3",
                            width="100%",
                            align="start",
                        ),
                    ),
                    style=rx.Style(
                        {
                            "padding": "20px 24px",
                            "overflow_y": "auto",
                            "flex": "1",
                            "width": "100%",
                        }
                    ),
                ),
                # 4. Footer Tombol Aksi
                rx.hstack(
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="pencil", size=Size.ICON_SM, color=Color.TEXT),
                            rx.text(
                                "Edit Aset",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.TEXT,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=on_edit,
                        style=rx.Style(
                            {
                                "flex": "1",
                                "height": Size.FILTER_CONTROL_H,
                                "background_color": Color.SURFACE,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                        _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="trash-2", size=Size.ICON_SM, color=Color.DANGER_FG),
                            rx.text(
                                "Hapus",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.DANGER_FG,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=on_delete,
                        style=rx.Style(
                            {
                                "height": Size.FILTER_CONTROL_H,
                                "padding": "0 18px",
                                "background_color": Color.DANGER_BG,
                                "border": "none",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    spacing="3",
                    width="100%",
                    padding="16px 24px",
                    style=rx.Style(
                        {
                            "border_top": f"1px solid {Color.BORDER}",
                            "background_color": Color.SURFACE,
                        }
                    ),
                ),
                id="global-detail-drawer",
                role="dialog",
                aria_modal="true",
                aria_label="Detail item",
                tab_index=-1,
                on_key_down=on_key_down,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "0",
                        "right": "0",
                        "bottom": "0",
                        "width": Size.DRAWER_WIDTH,
                        "background_color": Color.SURFACE,
                        "box_shadow": Shadow.DRAWER,
                        "display": "flex",
                        "flex_direction": "column",
                        "z_index": "70",
                        "outline": "none",
                        "@media (max-width: 899px)": {
                            "width": "100%",
                        },
                    }
                ),
            ),
            style=rx.Style({"position": "relative", "z_index": "60"}),
        ),
        rx.fragment(),
    )
