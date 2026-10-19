"""
Komponen Data Table Generik ITAM Pro.
Menerima definisi kolom dan daftar baris dari luar (reusable untuk seluruh halaman).
"""
from typing import Any, Literal, TypedDict

import reflex as rx

from itam_pro.components.ui.badge import status_badge
from itam_pro.components.ui.status_badge import asset_status_badge
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size, Space

RenderType = Literal["text", "bold_blue", "badge", "status_badge", "date"]


class ColumnDef(TypedDict, total=False):
    key: str
    header: str
    width: str
    render_type: RenderType
    badge_variant_key: str
    date_tone_key: str


def _render_cell_content(row: dict[str, Any], col: ColumnDef) -> rx.Component:
    """Render isi sel berdasarkan render_type yang didefinisikan pada kolom."""
    key = col.get("key", "")
    rtype = col.get("render_type", "text")

    if rtype == "bold_blue":
        return rx.text(
            row[key],
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.ACCENT,
            white_space="nowrap",
        )

    if rtype == "status_badge":
        return asset_status_badge(row[key])

    if rtype == "badge":
        variant_key = col.get("badge_variant_key", "")
        variant = row[variant_key] if variant_key else "neutral"
        return status_badge(label=row[key], variant=variant)

    if rtype == "date":
        tone_key = col.get("date_tone_key", "")
        if tone_key:
            date_color = rx.match(
                row[tone_key],
                ("danger", Color.DANGER_FG),
                ("warning", Color.WARNING_FG),
                Color.TEXT,
            )
            date_weight = rx.cond(
                row[tone_key] != "normal",
                FontWeight.SEMIBOLD,
                FontWeight.REGULAR,
            )
        else:
            date_color = Color.TEXT
            date_weight = FontWeight.REGULAR

        return rx.text(
            row[key],
            font_size=FontSize.SM,
            font_weight=date_weight,
            color=date_color,
            white_space="nowrap",
        )

    return rx.text(
        row[key],
        font_size=FontSize.SM,
        font_weight=FontWeight.MEDIUM,
        color=Color.TEXT,
        style=rx.Style(
            {
                "white_space": "nowrap",
                "overflow": "hidden",
                "text_overflow": "ellipsis",
            }
        ),
    )


def _header_cell(col: ColumnDef) -> rx.Component:
    """Sel header tabel: teks 12px uppercase muted, latar #F7F9FD."""
    header_text = col.get("header", "")
    return rx.el.th(
        header_text.upper(),
        style=rx.Style(
            {
                "width": col.get("width", "auto"),
                "min_width": col.get("width", "120px"),
                "height": Size.TABLE_HEADER_H,
                "padding": "0 16px",
                "text_align": "left",
                "font_size": FontSize.XS,
                "font_weight": FontWeight.BOLD,
                "color": Color.MUTED,
                "letter_spacing": "0.05em",
                "background_color": Color.TABLE_HEADER_BG,
                "border_bottom": f"1px solid {Color.BORDER}",
                "white_space": "nowrap",
            }
        ),
    )


def _row_action_menu(
    row_id: Any,
    on_view: Any,
    on_edit: Any,
    on_delete: Any,
) -> rx.Component:
    """Menu aksi '⋯' per baris."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.el.button(
                "⋯",
                type="button",
                aria_label="Menu aksi baris",
                on_click=rx.stop_propagation,
                style=rx.Style(
                    {
                        "width": "32px",
                        "height": "32px",
                        "background": "transparent",
                        "border": "none",
                        "border_radius": Radius.BADGE_KBD,
                        "color": Color.MUTED,
                        "font_size": "18px",
                        "font_weight": FontWeight.EXTRABOLD,
                        "cursor": "pointer",
                        "display": "inline-flex",
                        "align_items": "center",
                        "justify_content": "center",
                    }
                ),
                _hover=rx.Style(
                    {
                        "background_color": Color.BORDER,
                        "color": Color.TEXT,
                    }
                ),
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                "Lihat Detail",
                on_click=on_view(row_id),
            ),
            rx.menu.item(
                "Edit",
                on_click=on_edit(row_id),
            ),
            rx.menu.separator(),
            rx.menu.item(
                "Hapus",
                color="red",
                on_click=on_delete(row_id),
            ),
            align="end",
        ),
    )


def _skeleton_row(col_count: int) -> rx.Component:
    """Baris skeleton loading dengan tinggi seragam 52px."""
    return rx.el.tr(
        rx.el.td(
            rx.box(
                style=rx.Style(
                    {
                        "width": "16px",
                        "height": "16px",
                        "background_color": Color.SKELETON,
                        "border_radius": "4px",
                    }
                )
            ),
            style=rx.Style(
                {
                    "height": Size.TABLE_ROW_H,
                    "padding": "0 16px",
                    "border_bottom": f"1px solid {Color.DIVIDER}",
                }
            ),
        ),
        *[
            rx.el.td(
                rx.box(
                    style=rx.Style(
                        {
                            "width": "75%",
                            "height": "14px",
                            "background_color": Color.SKELETON,
                            "border_radius": "6px",
                        }
                    )
                ),
                style=rx.Style(
                    {
                        "height": Size.TABLE_ROW_H,
                        "padding": "0 16px",
                        "border_bottom": f"1px solid {Color.DIVIDER}",
                    }
                ),
            )
            for _ in range(col_count)
        ],
        rx.el.td(
            rx.box(
                style=rx.Style(
                    {
                        "width": "24px",
                        "height": "14px",
                        "background_color": Color.SKELETON,
                        "border_radius": "6px",
                    }
                )
            ),
            style=rx.Style(
                {
                    "height": Size.TABLE_ROW_H,
                    "padding": "0 16px",
                    "border_bottom": f"1px solid {Color.DIVIDER}",
                }
            ),
        ),
    )


def _empty_table_state(
    empty_message: str,
    on_reset: Any,
) -> rx.Component:
    """Tampilan kosong dengan pesan dan tombol Reset filter."""
    return rx.center(
        rx.vstack(
            rx.center(
                rx.icon(tag="search-x", size=24, color=Color.MUTED),
                width="48px",
                height="48px",
                background_color=Color.TABLE_HEADER_BG,
                border_radius=Radius.FULL,
            ),
            rx.text(
                empty_message,
                font_size=FontSize.SUBTITLE,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            rx.text(
                "Coba ubah kata kunci pencarian atau atur ulang kriteria filter Anda.",
                font_size=FontSize.SM,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            rx.el.button(
                "Reset filter",
                type="button",
                on_click=on_reset,
                style=rx.Style(
                    {
                        "margin_top": Space.S2,
                        "height": Size.FILTER_CONTROL_H,
                        "padding": "0 18px",
                        "background_color": Color.SURFACE,
                        "color": Color.ACCENT,
                        "border": f"1px solid {Color.INPUT_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                    }
                ),
                _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
            ),
            spacing="2",
            align="center",
            padding_y="48px",
            padding_x="24px",
        ),
        width="100%",
    )


def reusable_data_table(
    columns: list[ColumnDef],
    rows: Any,
    id_key: str,
    selected_ids: Any,
    active_row_id: Any,
    all_selected: Any,
    is_loading: Any,
    on_toggle_all: Any,
    on_toggle_row: Any,
    on_row_click: Any,
    on_edit_row: Any,
    on_delete_row: Any,
    on_reset_filter: Any,
    empty_message: str = "Tidak ada aset yang cocok",
) -> rx.Component:
    """
    Komponen Tabel Data Generik ITAM Pro.
    """

    def _render_row(row: dict[str, Any]) -> rx.Component:
        row_id = row[id_key]
        is_highlighted = selected_ids.contains(row_id) | (active_row_id == row_id)

        return rx.el.tr(
            # Kolom 1: Checkbox Pilih Baris
            rx.el.td(
                rx.el.input(
                    type="checkbox",
                    checked=selected_ids.contains(row_id),
                    on_change=lambda _: on_toggle_row(row_id),
                    on_click=rx.stop_propagation,
                    aria_label="Pilih baris",
                    style=rx.Style(
                        {
                            "width": Size.TABLE_CHECKBOX,
                            "height": Size.TABLE_CHECKBOX,
                            "accent_color": Color.ACCENT,
                            "cursor": "pointer",
                            "margin": "0",
                        }
                    ),
                ),
                on_click=rx.stop_propagation,
                style=rx.Style(
                    {
                        "width": "48px",
                        "height": Size.TABLE_ROW_H,
                        "padding": "0 16px",
                        "border_bottom": f"1px solid {Color.DIVIDER}",
                    }
                ),
            ),
            # Kolom-kolom Data Dinamis
            *[
                rx.el.td(
                    _render_cell_content(row, col),
                    style=rx.Style(
                        {
                            "width": col.get("width", "auto"),
                            "max_width": col.get("width", "260px"),
                            "height": Size.TABLE_ROW_H,
                            "padding": "0 16px",
                            "border_bottom": f"1px solid {Color.DIVIDER}",
                        }
                    ),
                )
                for col in columns
            ],
            # Kolom Terakhir: Menu Aksi '⋯'
            rx.el.td(
                _row_action_menu(
                    row_id=row_id,
                    on_view=on_row_click,
                    on_edit=on_edit_row,
                    on_delete=on_delete_row,
                ),
                on_click=rx.stop_propagation,
                style=rx.Style(
                    {
                        "width": "56px",
                        "height": Size.TABLE_ROW_H,
                        "padding": "0 12px",
                        "text_align": "right",
                        "border_bottom": f"1px solid {Color.DIVIDER}",
                    }
                ),
            ),
            id=f"table-row-{row_id}",
            tab_index=0,
            on_click=on_row_click(row_id),
            style=rx.Style(
                {
                    "height": Size.TABLE_ROW_H,
                    "background_color": rx.cond(
                        is_highlighted,
                        Color.ROW_SELECTED,
                        Color.SURFACE,
                    ),
                    "cursor": "pointer",
                    "transition": "background-color 0.12s ease",
                }
            ),
            _hover=rx.Style(
                {
                    "background_color": rx.cond(
                        is_highlighted,
                        Color.ROW_SELECTED,
                        Color.ROW_HOVER,
                    ),
                }
            ),
        )

    table_element = rx.box(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th(
                        rx.el.input(
                            type="checkbox",
                            checked=all_selected,
                            on_change=on_toggle_all,
                            aria_label="Pilih semua baris",
                            style=rx.Style(
                                {
                                    "width": Size.TABLE_CHECKBOX,
                                    "height": Size.TABLE_CHECKBOX,
                                    "accent_color": Color.ACCENT,
                                    "cursor": "pointer",
                                    "margin": "0",
                                }
                            ),
                        ),
                        style=rx.Style(
                            {
                                "width": "48px",
                                "height": Size.TABLE_HEADER_H,
                                "padding": "0 16px",
                                "text_align": "left",
                                "background_color": Color.TABLE_HEADER_BG,
                                "border_bottom": f"1px solid {Color.BORDER}",
                            }
                        ),
                    ),
                    *[_header_cell(col) for col in columns],
                    rx.el.th(
                        "",
                        style=rx.Style(
                            {
                                "width": "56px",
                                "height": Size.TABLE_HEADER_H,
                                "padding": "0 12px",
                                "background_color": Color.TABLE_HEADER_BG,
                                "border_bottom": f"1px solid {Color.BORDER}",
                            }
                        ),
                    ),
                ),
            ),
            rx.el.tbody(
                rx.cond(
                    is_loading,
                    rx.fragment(*[_skeleton_row(len(columns)) for _ in range(6)]),
                    rx.foreach(rows, _render_row),
                ),
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "border_collapse": "collapse",
                    "font_family": FONT_FAMILY,
                }
            ),
        ),
        style=rx.Style(
            {
                "width": "100%",
                "overflow_x": "auto",
            }
        ),
    )

    return rx.box(
        rx.cond(
            (~is_loading) & (rows.length() == 0),
            _empty_table_state(empty_message=empty_message, on_reset=on_reset_filter),
            table_element,
        ),
        width="100%",
    )
