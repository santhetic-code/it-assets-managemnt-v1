"""
Komponen Data Table Generik ITAM Pro (Tahap 6d).
Mendukung line-clamp 2 baris + tooltip, visibilitas kolom dinamis (Atur kolom),
lebar minimum anti-overlap, serta seluruh warna dari token Color.
"""
from typing import Any, Literal, Required, TypedDict

import reflex as rx

from itam_pro.components.ui.badge import app_badge, connector_chip
from itam_pro.components.ui.status_badge import asset_condition_badge, asset_status_badge
from itam_pro.styles import (
    FONT_FAMILY,
    Color,
    FontSize,
    FontWeight,
    Radius,
    Size,
    Space,
)

RenderType = Literal[
    "text",
    "bold",
    "bold_blue",
    "ip_address",
    "name_with_sub",
    "chip",
    "badge",
    "condition_badge",
    "status_badge",
    "chips",
    "date",
]


class ColumnDef(TypedDict, total=False):
    key: Required[str]
    header: Required[Any]
    width: str
    min_width: str
    render_type: RenderType
    sub_key: str
    sticky_left: bool
    sortable: bool
    sort_key: str
    badge_variant_key: str
    date_tone_key: str


_TWO_LINE_CLAMP_STYLE: dict[str, Any] = {
    "display": "-webkit-box",
    "-webkit-line-clamp": "2",
    "-webkit-box-orient": "vertical",
    "overflow": "hidden",
    "text_overflow": "ellipsis",
    "white_space": "normal",
    "word_break": "break-word",
    "line_height": "1.35",
}


def _render_cell_content(row: dict[str, Any], col: ColumnDef | dict[str, Any]) -> rx.Component:
    """Render isi sel berdasarkan render_type dengan dukungan 2-line clamp + tooltip."""
    raw_key = col.get("key") or col.get("accessor", "")
    key: str = str(raw_key) if raw_key else ""
    rtype = str(col.get("render_type", "text"))
    is_sticky = bool(col.get("sticky_left", False))

    if rtype == "ip_address":
        return rx.hstack(
            rx.text(
                row[key],
                title=row[key],
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=rx.cond(row["is_conflict"], Color.DANGER_FG, Color.ACCENT),
                style=rx.Style(
                    {
                        "font_family": (
                            "ui-monospace, SFMono-Regular, Menlo, "
                            "Monaco, Consolas, monospace"
                        ),
                        "white_space": "nowrap",
                    }
                ),
            ),
            rx.cond(
                row["is_conflict"],
                asset_status_badge("Bentrok"),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
        )

    if rtype == "name_with_sub":
        sub_k = str(col.get("sub_key", "sub_label"))
        return rx.vstack(
            rx.text(
                row[key],
                title=row[key],
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
                style=rx.Style(_TWO_LINE_CLAMP_STYLE),
            ),
            rx.text(
                row[sub_k],
                title=row[sub_k],
                font_size=FontSize.XS,
                font_weight=FontWeight.MEDIUM,
                color=rx.cond(
                    row[sub_k] == "Tanpa host",
                    Color.WARNING_FG,
                    Color.MUTED,
                ),
                style=rx.Style(
                    {
                        "line_height": "1.15",
                        "white_space": "nowrap",
                        "overflow": "hidden",
                        "text_overflow": "ellipsis",
                        "max_width": "100%",
                    }
                ),
            ),
            spacing="1",
            align="start",
            width="100%",
        )

    if rtype == "chip":
        return connector_chip(row[key])

    if rtype == "bold_blue":
        return rx.text(
            row[key],
            title=row[key],
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.ACCENT,
            style=rx.Style(_TWO_LINE_CLAMP_STYLE),
        )

    if rtype == "bold":
        return rx.text(
            row[key],
            title=row[key],
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.TEXT,
            style=rx.Style(_TWO_LINE_CLAMP_STYLE),
        )

    if rtype == "chips":
        val = row[key]
        chips_var = val.to(list[str]) if hasattr(val, "to") else val
        return rx.hstack(
            rx.foreach(chips_var, connector_chip),
            spacing="1",
            align="center",
            wrap="wrap",
        )

    if rtype == "status_badge":
        return asset_status_badge(row[key])

    if rtype == "condition_badge":
        return asset_condition_badge(row[key])

    if rtype == "badge":
        variant_key = str(col.get("badge_variant_key", ""))
        variant = row[variant_key] if variant_key else "neutral"
        return app_badge(label=row[key], variant=variant)

    if rtype == "date":
        return rx.text(
            row[key],
            title=row[key],
            font_size=FontSize.SM,
            font_weight=FontWeight.REGULAR,
            color=rx.cond(row[key] == "—", Color.MUTED, Color.TEXT),
            white_space="nowrap",
        )

    return rx.text(
        row[key],
        title=row[key],
        font_size=FontSize.SM,
        font_weight=FontWeight.BOLD if is_sticky else FontWeight.MEDIUM,
        color=rx.cond(row[key] == "—", Color.MUTED, Color.TEXT),
        style=rx.Style(_TWO_LINE_CLAMP_STYLE),
    )


def _header_cell(
    col: ColumnDef | dict[str, Any],
    sort_by: Any = "",
    sort_dir: Any = "asc",
    on_sort: Any | None = None,
    hidden_columns: Any | None = None,
) -> rx.Component:
    """Sel header tabel dengan dukungan sort ↕ dan visibilitas kolom dinamis."""
    raw_key = col.get("key") or col.get("accessor", "")
    key: str = str(raw_key) if raw_key else ""
    is_sticky = bool(col.get("sticky_left", False))
    is_sortable = bool(col.get("sortable", False)) and (on_sort is not None)
    s_key = str(col.get("sort_key", key))
    min_w = col.get("min_width", col.get("width", "110px"))

    header_style: dict[str, Any] = {
        "width": col.get("width", "auto"),
        "min_width": min_w,
        "height": Size.TABLE_HEADER_H,
        "padding": "0 16px",
        "text_align": "left",
        "font_size": FontSize.XS,
        "font_weight": FontWeight.BOLD,
        "color": Color.MUTED,
        "letter_spacing": "0.05em",
        "text_transform": "uppercase",
        "background_color": Color.TABLE_HEADER_BG,
        "border_bottom": f"1px solid {Color.BORDER}",
        "white_space": "nowrap",
        "box_sizing": "border-box",
    }
    if hidden_columns is not None:
        header_style["display"] = rx.cond(
            hidden_columns.contains(key),
            "none",
            "table-cell",
        )
    if is_sticky:
        header_style.update(
            {
                "position": "sticky",
                "left": "48px",
                "z_index": "4",
                "border_right": f"1px solid {Color.BORDER}",
            }
        )

    if is_sortable and on_sort is not None:
        is_active_sort = sort_by == s_key
        arrow_symbol = rx.cond(
            is_active_sort,
            rx.cond(sort_dir == "asc", "↑", "↓"),
            "↕",
        )
        return rx.el.th(
            rx.el.button(
                rx.hstack(
                    rx.text(
                        col["header"],
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=rx.cond(is_active_sort, Color.ACCENT, Color.MUTED),
                        letter_spacing="0.05em",
                        style=rx.Style({"text_transform": "uppercase"}),
                    ),
                    rx.text(
                        arrow_symbol,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=rx.cond(is_active_sort, Color.ACCENT, Color.MUTED),
                    ),
                    spacing="1",
                    align="center",
                ),
                type="button",
                on_click=on_sort(s_key),
                style=rx.Style(
                    {
                        "background": "transparent",
                        "border": "none",
                        "padding": "0",
                        "font_family": FONT_FAMILY,
                        "cursor": "pointer",
                        "display": "inline-flex",
                        "align_items": "center",
                    }
                ),
            ),
            style=rx.Style(header_style),
        )

    return rx.el.th(
        col["header"],
        style=rx.Style(header_style),
    )


def _row_action_menu(
    row_id: Any,
    on_view: Any = None,
    on_edit: Any = None,
    on_duplicate: Any = None,
    on_delete: Any = None,
    duplicate_label: str = "Duplikat x N",
) -> rx.Component:
    menu_items: list[rx.Component] = []
    if on_view is not None:
        menu_items.append(rx.menu.item("Lihat Rincian", on_click=on_view(row_id)))
    if on_edit is not None:
        menu_items.append(rx.menu.item("Edit", on_click=on_edit(row_id)))
    if on_duplicate is not None:
        menu_items.append(rx.menu.item(duplicate_label, on_click=on_duplicate(row_id)))
    if on_delete is not None:
        menu_items.append(rx.menu.separator())
        menu_items.append(rx.menu.item("Hapus", color="red", on_click=on_delete(row_id)))

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
                        "font_size": FontSize.LOGO,
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
            *menu_items,
            align="end",
        ),
    )


def _skeleton_row(col_count: int) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.box(
                style=rx.Style(
                    {
                        "width": "16px",
                        "height": "16px",
                        "background_color": Color.SKELETON,
                        "border_radius": Radius.BADGE_KBD,
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
                            "border_radius": Radius.BADGE_KBD,
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
                        "border_radius": Radius.BADGE_KBD,
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
    empty_message: Any,
    empty_subtitle: Any,
    action_label: Any,
    on_action: Any,
) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.center(
                rx.icon(tag="inbox", size=24, color=Color.MUTED),
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
                empty_subtitle,
                font_size=FontSize.SM,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            rx.el.button(
                action_label,
                type="button",
                on_click=on_action,
                style=rx.Style(
                    {
                        "margin_top": Space.S2,
                        "height": Size.FILTER_CONTROL_H,
                        "padding": "0 18px",
                        "background_color": Color.ACCENT,
                        "color": Color.WHITE,
                        "border": "none",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                    }
                ),
                _hover=rx.Style({"background_color": Color.ACCENT_BRIGHT}),
            ),
            spacing="2",
            align="center",
            padding_y="48px",
            padding_x="24px",
        ),
        width="100%",
    )


def reusable_data_table(
    columns: list[ColumnDef] | list[dict[str, Any]],
    rows: Any = None,
    id_key: str = "id",
    selected_ids: Any = None,
    active_row_id: Any = None,
    all_selected: Any = None,
    is_loading: Any = None,
    on_toggle_all: Any = None,
    on_toggle_row: Any = None,
    on_row_click: Any = None,
    on_edit_row: Any = None,
    on_delete_row: Any = None,
    on_reset_filter: Any = None,
    on_duplicate_row: Any | None = None,
    duplicate_action_label: str = "Duplikat x N",
    sort_by: Any = "",
    sort_dir: Any = "asc",
    on_sort: Any | None = None,
    hidden_columns: Any | None = None,
    show_action_header: bool = True,
    empty_message: Any = "Tidak ada aset yang cocok",
    empty_subtitle: Any = "Coba ubah kata kunci pencarian atau atur ulang kriteria filter Anda.",
    empty_action_label: Any = "Reset filter",
    on_empty_action: Any | None = None,
    *,
    items: Any = None,
) -> rx.Component:
    target_rows: Any = items if items is not None else rows
    actual_rows: Any = target_rows
    actual_loading: Any = is_loading if is_loading is not None else False
    show_checkbox = selected_ids is not None and on_toggle_row is not None
    show_actions = show_action_header and any(
        h is not None for h in (on_edit_row, on_duplicate_row, on_delete_row)
    )
    dup_handler = on_duplicate_row if on_duplicate_row is not None else on_edit_row
    empty_handler = on_empty_action if on_empty_action is not None else on_reset_filter

    def _render_data_cell(
        row: dict[str, Any],
        col: ColumnDef | dict[str, Any],
        row_bg: Any,
    ) -> rx.Component:
        key = col.get("key") or col.get("accessor", "")
        is_sticky = col.get("sticky_left", False)
        min_w = col.get("min_width", col.get("width", "110px"))
        cell_style: dict[str, Any] = {
            "width": col.get("width", "auto"),
            "min_width": min_w,
            "max_width": col.get("width", "260px"),
            "min_height": Size.TABLE_ROW_H,
            "padding": "8px 16px",
            "border_bottom": f"1px solid {Color.DIVIDER}",
            "overflow": "hidden",
            "vertical_align": "middle",
            "box_sizing": "border-box",
        }
        if hidden_columns is not None:
            cell_style["display"] = rx.cond(
                hidden_columns.contains(key),
                "none",
                "table-cell",
            )
        if is_sticky:
            cell_style.update(
                {
                    "background_color": row_bg,
                    "position": "sticky",
                    "left": "48px",
                    "z_index": "2",
                    "border_right": f"1px solid {Color.DIVIDER}",
                }
            )
        return rx.el.td(
            _render_cell_content(row, col),
            style=rx.Style(cell_style),
        )

    has_ip_col = any(col.get("render_type") == "ip_address" for col in columns)

    def _render_row(row: dict[str, Any]) -> rx.Component:
        row_id = row[id_key]
        is_highlighted = (
            (selected_ids.contains(row_id) | (active_row_id == row_id))
            if selected_ids is not None and active_row_id is not None
            else False
        )
        is_conflict = (row["is_conflict"] == True) if has_ip_col else False  # noqa: E712
        row_bg = rx.cond(
            is_highlighted,
            Color.ROW_SELECTED,
            rx.cond(is_conflict, Color.CONFLICT_ROW_BG, Color.SURFACE),
        )

        cb_td_props = {}
        if on_toggle_row is not None:
            cb_td_props["on_change"] = on_toggle_row(row_id)

        checkbox_td = (
            rx.el.td(
                rx.el.input(
                    type="checkbox",
                    checked=selected_ids.contains(row_id) if selected_ids is not None else False,
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
                    **cb_td_props,
                ),
                on_click=rx.stop_propagation,
                style=rx.Style(
                    {
                        "width": "48px",
                        "min_width": "48px",
                        "height": Size.TABLE_ROW_H,
                        "padding": "0 16px",
                        "border_bottom": f"1px solid {Color.DIVIDER}",
                        "background_color": row_bg,
                        "position": "sticky",
                        "left": "0",
                        "z_index": "2",
                    }
                ),
            )
            if show_checkbox
            else rx.fragment()
        )

        action_td = (
            rx.el.td(
                _row_action_menu(
                    row_id=row_id,
                    on_view=on_row_click,
                    on_edit=on_edit_row,
                    on_duplicate=dup_handler,
                    on_delete=on_delete_row,
                    duplicate_label=duplicate_action_label,
                ),
                on_click=rx.stop_propagation,
                style=rx.Style(
                    {
                        "width": "52px",
                        "min_width": "52px",
                        "height": Size.TABLE_ROW_H,
                        "padding": "0 12px",
                        "text_align": "right",
                        "border_bottom": f"1px solid {Color.DIVIDER}",
                    }
                ),
            )
            if show_actions
            else rx.fragment()
        )

        tr_props = {}
        if on_row_click is not None:
            tr_props["on_click"] = on_row_click(row_id)

        return rx.el.tr(
            checkbox_td,
            *[_render_data_cell(row, col, row_bg) for col in columns],
            action_td,
            id=f"table-row-{row_id}",
            tab_index=0,
            style=rx.Style(
                {
                    "min_height": Size.TABLE_ROW_H,
                    "background_color": row_bg,
                    "cursor": "pointer" if on_row_click is not None else "default",
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
            **tr_props,
        )

    cb_th_props = {}
    if on_toggle_all is not None:
        cb_th_props["on_change"] = on_toggle_all

    checkbox_th = (
        rx.el.th(
            rx.el.input(
                type="checkbox",
                checked=all_selected if all_selected is not None else False,
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
                **cb_th_props,
            ),
            style=rx.Style(
                {
                    "width": "48px",
                    "min_width": "48px",
                    "height": Size.TABLE_HEADER_H,
                    "padding": "0 16px",
                    "text_align": "left",
                    "background_color": Color.TABLE_HEADER_BG,
                    "border_bottom": f"1px solid {Color.BORDER}",
                    "position": "sticky",
                    "left": "0",
                    "z_index": "4",
                }
            ),
        )
        if show_checkbox
        else rx.fragment()
    )

    action_th = (
        rx.el.th(
            "AKSI" if show_action_header else "",
            style=rx.Style(
                {
                    "width": "52px",
                    "min_width": "52px",
                    "height": Size.TABLE_HEADER_H,
                    "padding": "0 12px",
                    "text_align": "right",
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
        if show_actions
        else rx.fragment()
    )

    table_element = rx.box(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    checkbox_th,
                    *[
                        _header_cell(
                            col,
                            sort_by=sort_by,
                            sort_dir=sort_dir,
                            on_sort=on_sort,
                            hidden_columns=hidden_columns,
                        )
                        for col in columns
                    ],
                    action_th,
                ),
            ),
            rx.el.tbody(
                rx.cond(
                    actual_loading,
                    rx.fragment(*[_skeleton_row(len(columns)) for _ in range(6)]),
                    rx.foreach(actual_rows, _render_row),
                ),
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "border_collapse": "separate",
                    "border_spacing": "0",
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
            (~actual_loading) & (actual_rows.length() == 0),
            _empty_table_state(
                empty_message=empty_message,
                empty_subtitle=empty_subtitle,
                action_label=empty_action_label,
                on_action=empty_handler,
            ),
            table_element,
        ),
        width="100%",
    )


__all__ = ["ColumnDef", "RenderType", "reusable_data_table"]
