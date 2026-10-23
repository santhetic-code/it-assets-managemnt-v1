"""
Komponen Filter Bar Tabel Generik ITAM Pro.
Mendukung kotak pencarian, N dropdown filter, tombol Reset, popover 'Atur kolom',
serta label jumlah unit.
"""
from typing import Any, Required, TypedDict

import reflex as rx

from itam_pro.styles import (
    FONT_FAMILY,
    Color,
    FontSize,
    FontWeight,
    Radius,
    Shadow,
    Size,
    Space,
)


class FilterDropdownConfig(TypedDict, total=False):
    label: Required[str]
    value: Required[Any]
    options: Required[Any]
    on_change: Required[Any]


class ColumnToggleOption(TypedDict):
    key: str
    label: str


def _filter_select(cfg: FilterDropdownConfig) -> rx.Component:
    return rx.box(
        rx.el.select(
            rx.el.option(cfg["label"], value=""),
            rx.foreach(
                cfg["options"],
                lambda opt: rx.el.option(opt, value=opt),
            ),
            value=cfg["value"],
            on_change=cfg["on_change"],
            style=rx.Style(
                {
                    "height": Size.FILTER_CONTROL_H,
                    "padding": "0 30px 0 12px",
                    "background_color": Color.SURFACE,
                    "color": Color.TEXT,
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.MEDIUM,
                    "outline": "none",
                    "cursor": "pointer",
                    "appearance": "none",
                    "-webkit-appearance": "none",
                }
            ),
        ),
        rx.icon(
            tag="chevron-down",
            size=14,
            color=Color.MUTED,
            style=rx.Style(
                {
                    "position": "absolute",
                    "right": "10px",
                    "top": "50%",
                    "transform": "translateY(-50%)",
                    "pointer_events": "none",
                }
            ),
        ),
        style=rx.Style({"position": "relative", "display": "inline-block"}),
    )


def _column_visibility_popover(
    column_options: list[ColumnToggleOption],
    hidden_columns: Any,
    on_toggle_column: Any,
    on_reset_columns: Any | None = None,
) -> rx.Component:
    """Popover 'Atur kolom' dengan daftar checkbox per kolom."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.el.button(
                rx.hstack(
                    rx.icon(tag="columns-3", size=15, color=Color.TEXT),
                    rx.text(
                        "Atur kolom",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    spacing="2",
                    align="center",
                ),
                type="button",
                style=rx.Style(
                    {
                        "height": Size.FILTER_CONTROL_H,
                        "padding": "0 12px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.INPUT_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "cursor": "pointer",
                        "display": "inline-flex",
                        "align_items": "center",
                    }
                ),
                _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
            ),
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "TAMPILKAN KOLOM",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                    ),
                    rx.el.button(
                        "Default",
                        type="button",
                        on_click=on_reset_columns,
                        style=rx.Style(
                            {
                                "background": "transparent",
                                "border": "none",
                                "padding": "0",
                                "color": Color.ACCENT,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.XS,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    )
                    if on_reset_columns is not None
                    else rx.fragment(),
                    width="100%",
                    justify="between",
                    align="center",
                    padding_bottom="6px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.DIVIDER}"}),
                ),
                *[
                    rx.el.label(
                        rx.hstack(
                            rx.el.input(
                                type="checkbox",
                                checked=~hidden_columns.contains(col_opt["key"]),
                                on_change=on_toggle_column(col_opt["key"]),
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
                            rx.text(
                                col_opt["label"],
                                font_size=FontSize.SM,
                                font_weight=FontWeight.MEDIUM,
                                color=Color.TEXT,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        style=rx.Style(
                            {
                                "width": "100%",
                                "padding": "4px 2px",
                                "cursor": "pointer",
                                "display": "flex",
                                "align_items": "center",
                            }
                        ),
                    )
                    for col_opt in column_options
                ],
                spacing="1",
                width="210px",
                align="start",
            ),
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CONTROL,
                    "box_shadow": Shadow.POPOVER,
                    "padding": "12px 14px",
                }
            ),
        ),
    )


def table_filter_bar(
    search_value: Any,
    on_search_change: Any,
    search_placeholder: str,
    dropdowns: list[FilterDropdownConfig],
    on_reset: Any,
    result_count_text: Any,
    column_options: list[ColumnToggleOption] | None = None,
    hidden_columns: Any | None = None,
    on_toggle_column: Any | None = None,
    on_reset_columns: Any | None = None,
) -> rx.Component:
    """Bar filter standar di atas tabel dengan dukungan tombol 'Atur kolom'."""
    return rx.box(
        rx.hstack(
            # Kotak Pencarian
            rx.box(
                rx.icon(
                    tag="search",
                    size=15,
                    color=Color.MUTED,
                    style=rx.Style(
                        {
                            "position": "absolute",
                            "left": "12px",
                            "top": "50%",
                            "transform": "translateY(-50%)",
                            "pointer_events": "none",
                        }
                    ),
                ),
                rx.el.input(
                    type="text",
                    value=search_value,
                    on_change=on_search_change,
                    placeholder=search_placeholder,
                    style=rx.Style(
                        {
                            "width": Size.FILTER_SEARCH_W,
                            "max_width": "100%",
                            "height": Size.FILTER_CONTROL_H,
                            "padding": "0 12px 0 36px",
                            "background_color": Color.SURFACE,
                            "color": Color.TEXT,
                            "border": f"1px solid {Color.INPUT_BORDER}",
                            "border_radius": Radius.CONTROL,
                            "font_family": FONT_FAMILY,
                            "font_size": FontSize.SM,
                            "outline": "none",
                        }
                    ),
                ),
                style=rx.Style({"position": "relative"}),
            ),
            # Dropdown Filter
            *[_filter_select(d) for d in dropdowns],
            # Tombol Reset Filter
            rx.el.button(
                "Reset filter",
                type="button",
                on_click=on_reset,
                style=rx.Style(
                    {
                        "height": Size.FILTER_CONTROL_H,
                        "padding": "0 12px",
                        "background": "transparent",
                        "border": "none",
                        "color": Color.ACCENT,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                    }
                ),
            ),
            spacing="2",
            align="center",
            wrap="wrap",
        ),
        rx.hstack(
            _column_visibility_popover(
                column_options=column_options,
                hidden_columns=hidden_columns,
                on_toggle_column=on_toggle_column,
                on_reset_columns=on_reset_columns,
            )
            if (
                column_options is not None
                and hidden_columns is not None
                and on_toggle_column is not None
            )
            else rx.fragment(),
            rx.text(
                result_count_text,
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                white_space="nowrap",
            ),
            spacing="3",
            align="center",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "padding": "14px 20px",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S3,
                "border_bottom": f"1px solid {Color.BORDER}",
                "background_color": Color.SURFACE,
            }
        ),
    )


__all__ = ["ColumnToggleOption", "FilterDropdownConfig", "table_filter_bar"]
