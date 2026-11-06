"""Halaman Infrastructure -> IP & Server (VM) (/infrastructure/ip)."""

from typing import Any

import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.forms import ip_form_modal
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    reusable_data_table,
    table_pagination,
)
from itam_pro.components.ui import TabItemConfig, app_tabs, detail_drawer
from itam_pro.states.ip_state import IPState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Space

IP_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "ip_address",
        "header": "IP Address",
        "width": "155px",
        "min_width": "145px",
        "render_type": "ip_address",
        "sticky_left": True,
        "sortable": True,
        "sort_key": "ip_address",
    },
    {
        "key": "pengguna",
        "header": "Pengguna",
        "width": "220px",
        "min_width": "190px",
        "render_type": "name_with_sub",
        "sub_key": "sub_label",
        "sortable": True,
        "sort_key": "pengguna",
    },
    {
        "key": "jenis",
        "header": "Jenis",
        "width": "80px",
        "min_width": "80px",
        "render_type": "jenis_chip",
    },
    {
        "key": "host_display",
        "header": "Host",
        "width": "150px",
        "min_width": "130px",
        "render_type": "text",
    },
    {
        "key": "kategori",
        "header": "Kategori",
        "width": "130px",
        "min_width": "120px",
        "render_type": "badge",
    },
    {
        "key": "fungsi",
        "header": "Fungsi",
        "width": "220px",
        "min_width": "200px",
        "render_type": "text",
    },
    {
        "key": "os",
        "header": "OS",
        "width": "150px",
        "min_width": "140px",
        "render_type": "text",
    },
    {
        "key": "status",
        "header": "Status",
        "width": "110px",
        "min_width": "100px",
        "render_type": "status_badge",
    },
]


def _ip_header() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(tag="server", size=26, color=Color.WHITE, stroke_width=2),
                width="52px",
                height="52px",
                border_radius="15px",
                flex_shrink="0",
                style=rx.Style(
                    {
                        "background": Color.GRADIENT_BLUE,
                        "box_shadow": "0 6px 16px rgba(37, 99, 235, 0.24)",
                    }
                ),
            ),
            rx.vstack(
                rx.heading(
                    "IP & Server (VM)",
                    font_size="28px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                    line_height="1.15",
                    letter_spacing="-0.02em",
                ),
                rx.text(
                    "Pemetaan IPv4, server fisik, dan VM.",
                    font_size=FontSize.BASE,
                    font_weight=FontWeight.REGULAR,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
        ),
        rx.hstack(
            rx.el.button(
                rx.hstack(
                    rx.icon(tag="upload", size=16, color=Color.TEXT, stroke_width=2),
                    rx.text(
                        "Import",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.BOLD,
                        color=Color.TEXT,
                    ),
                    spacing="2",
                    align="center",
                ),
                type="button",
                on_click=IPState.open_import_modal,
                style=rx.Style(
                    {
                        "height": "42px",
                        "padding": "0 16px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": "11px",
                        "font_family": FONT_FAMILY,
                        "cursor": "pointer",
                        "transition": "all 0.15s ease",
                        "&:hover": {"background_color": Color.SURFACE_HOVER},
                    }
                ),
            ),
            rx.menu.root(
                rx.menu.trigger(
                    rx.el.button(
                        rx.hstack(
                            rx.text(
                                "Export",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.TEXT,
                            ),
                            rx.icon(tag="chevron-down", size=16, color=Color.TEXT),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        style=rx.Style(
                            {
                                "height": "42px",
                                "padding": "0 16px",
                                "background_color": Color.SURFACE,
                                "border": f"1px solid {Color.BORDER}",
                                "border_radius": "11px",
                                "font_family": FONT_FAMILY,
                                "cursor": "pointer",
                                "transition": "all 0.15s ease",
                                "&:hover": {"background_color": Color.SURFACE_HOVER},
                            }
                        ),
                    )
                ),
                rx.menu.content(
                    rx.menu.item("Excel (.xlsx)", on_click=IPState.export_excel),
                    rx.menu.item("PDF (.pdf)", on_click=IPState.export_pdf),
                    align="end",
                ),
            ),
            rx.el.button(
                "+ Tambah IP",
                type="button",
                on_click=IPState.open_add_modal,
                style=rx.Style(
                    {
                        "height": "42px",
                        "padding": "0 20px",
                        "background": Color.GRADIENT_PRIMARY,
                        "color": Color.WHITE,
                        "border": "none",
                        "border_radius": "11px",
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "box_shadow": "0 6px 16px rgba(29, 78, 216, 0.28)",
                        "transition": "all 0.15s ease",
                    }
                ),
            ),
            spacing="3",
            align="center",
            wrap="wrap",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S4,
            }
        ),
    )


def _proportion_kpi_card(
    title: str,
    icon_tag: str,
    icon_bg: str,
    icon_color: str,
    value_var: Any,
    subtitle_var: Any,
    percent_var: Any,
    bar_color: str,
) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.center(
                rx.icon(tag=icon_tag, size=17, color=icon_color, stroke_width=2),
                width="34px",
                height="34px",
                background_color=icon_bg,
                border_radius="10px",
            ),
            rx.text(
                title,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            spacing="3",
            align="center",
        ),
        rx.text(
            value_var,
            font_size="34px",
            font_weight=FontWeight.EXTRABOLD,
            color=Color.TEXT,
            line_height="1.1",
            margin_top="4px",
        ),
        rx.text(
            subtitle_var,
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.MEDIUM,
            color=Color.MUTED,
        ),
        rx.box(
            rx.box(
                style=rx.Style(
                    {
                        "width": f"{percent_var}%",
                        "height": "100%",
                        "background_color": bar_color,
                        "border_radius": Radius.FULL,
                        "transition": "width 0.3s ease",
                    }
                )
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "6px",
                    "background_color": Color.SLATE_200,
                    "border_radius": Radius.FULL,
                    "overflow": "hidden",
                    "margin_top": "4px",
                }
            ),
        ),
        spacing="2",
        align="start",
        padding="18px 20px",
        style=rx.Style(
            {
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": "16px",
                "width": "100%",
                "transition": "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                "_hover": {
                    "transform": "translateY(-3px)",
                    "box_shadow": "0 8px 20px rgba(0,0,0,0.06)",
                    "border_color": Color.ACCENT,
                },
            }
        ),
    )


def _ip_kpi_row() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon(tag="globe", size=17, color=Color.WHITE, stroke_width=2),
                    width="34px",
                    height="34px",
                    border_radius="10px",
                    style=rx.Style({"background_color": "rgba(255, 255, 255, 0.16)"}),
                ),
                rx.text(
                    "TOTAL IP",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color="rgba(255, 255, 255, 0.85)",
                    letter_spacing="0.06em",
                ),
                spacing="3",
                align="center",
            ),
            rx.text(
                IPState.kpi_total_ip,
                font_size="34px",
                font_weight=FontWeight.EXTRABOLD,
                color=Color.WHITE,
                line_height="1.1",
                margin_top="6px",
            ),
            rx.text(
                "Seluruh entri terdaftar",
                font_size=FontSize.FOOTER,
                font_weight=FontWeight.MEDIUM,
                color="rgba(255, 255, 255, 0.8)",
            ),
            spacing="2",
            align="start",
            padding="18px 20px",
            style=rx.Style(
                {
                    "background": Color.GRADIENT_NAVY,
                    "border_radius": "16px",
                    "width": "100%",
                    "box_shadow": "0 8px 20px rgba(15, 23, 42, 0.14)",
                    "transition": "all 0.2s",
                    "_hover": {
                        "transform": "translateY(-3px)",
                        "box_shadow": "0 12px 24px rgba(29,78,216,0.3)",
                    },
                }
            ),
        ),
        _proportion_kpi_card(
            "SERVER FISIK",
            "monitor",
            Color.BLUE_100,
            Color.BLUE_600,
            IPState.kpi_fisik,
            rx.cond(
                IPState.fisik_percent >= 0, f"PC & server fisik · {IPState.fisik_percent}%", ""
            ),
            IPState.fisik_percent,
            Color.BLUE_600,
        ),
        _proportion_kpi_card(
            "VM",
            "layers",
            Color.PURPLE_BG,
            Color.PURPLE_600,
            IPState.kpi_vm,
            rx.cond(IPState.vm_percent >= 0, f"Mesin virtual · {IPState.vm_percent}%", ""),
            IPState.vm_percent,
            Color.PURPLE_600,
        ),
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon(tag="triangle-alert", size=17, color=Color.RED_600, stroke_width=2),
                    width="34px",
                    height="34px",
                    background_color=Color.RED_100,
                    border_radius="10px",
                ),
                rx.text(
                    "IP BENTROK",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                    letter_spacing="0.06em",
                ),
                spacing="3",
                align="center",
            ),
            rx.hstack(
                rx.text(
                    IPState.kpi_bentrok,
                    font_size="34px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=rx.cond(IPState.kpi_bentrok == 0, Color.TEXT, Color.RED_700),
                    line_height="1.1",
                ),
                rx.box(
                    rx.text(
                        rx.cond(IPState.kpi_bentrok == 0, "Aman", "Bentrok"),
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=rx.cond(IPState.kpi_bentrok == 0, Color.GREEN_700, Color.RED_700),
                    ),
                    style=rx.Style(
                        {
                            "padding": "3px 10px",
                            "border_radius": Radius.FULL,
                            "background_color": rx.cond(
                                IPState.kpi_bentrok == 0, Color.GREEN_100, Color.RED_100
                            ),
                        }
                    ),
                ),
                spacing="3",
                align="center",
                margin_top="4px",
            ),
            rx.text(
                "Memakai IPv4 yang sama",
                font_size=FontSize.FOOTER,
                font_weight=FontWeight.MEDIUM,
                color=Color.MUTED,
            ),
            spacing="2",
            align="start",
            padding="18px 20px",
            on_click=IPState.toggle_conflict_only,
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": "16px",
                    "width": "100%",
                    "cursor": "pointer",
                    "transition": "all 0.2s",
                    "_hover": {
                        "transform": "translateY(-3px)",
                        "border_color": Color.RED_300,
                        "box_shadow": "0 8px 16px rgba(220,38,38,0.1)",
                    },
                }
            ),
        ),
        _proportion_kpi_card(
            "IP KOSONG",
            "database",
            Color.GREEN_100,
            Color.GREEN_700,
            IPState.kpi_kosong_count,
            rx.cond(
                IPState.kosong_percent >= 0,
                f"Tersedia · {IPState.kosong_percent}% dari 254",
                "",
            ),
            IPState.kosong_percent,
            Color.GREEN_400,
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(5, minmax(0, 1fr))",
                "gap": Space.S4,
                "@media (max-width: 1100px)": {
                    "grid_template_columns": "repeat(2, minmax(0, 1fr))"
                },
                "@media (max-width: 600px)": {"grid_template_columns": "1fr"},
            }
        ),
    )


def _futuristic_filter_bar() -> rx.Component:
    """Filter bar modern mengambang dengan efek glassmorphism."""

    def _pill_select(opts: Any, val: Any, on_change: Any, placeholder: str) -> rx.Component:
        return rx.box(
            rx.el.select(
                rx.el.option(placeholder, value=""),
                rx.foreach(opts, lambda o: rx.el.option(o, value=o)),
                value=val,
                on_change=on_change,
                style=rx.Style(
                    {
                        "height": "36px",
                        "padding": "0 30px 0 14px",
                        "background_color": "transparent",
                        "border": "none",
                        "color": Color.TEXT,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.MEDIUM,
                        "cursor": "pointer",
                        "appearance": "none",
                        "outline": "none",
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
            style=rx.Style(
                {
                    "position": "relative",
                    "background_color": Color.SLATE_50,
                    "border_radius": "20px",
                    "border": f"1px solid {Color.BORDER}",
                    "transition": "all 0.2s",
                    "&:focus-within": {
                        "border_color": Color.ACCENT,
                        "box_shadow": Color.FOCUS_RING,
                    },
                }
            ),
        )

    return rx.hstack(
        rx.hstack(
            rx.icon(tag="search", size=16, color=Color.MUTED),
            rx.el.input(
                value=IPState.search_query,
                on_change=IPState.set_search_query,
                placeholder="Cari IP, pengguna, os...",
                style=rx.Style(
                    {
                        "width": "220px",
                        "height": "36px",
                        "border": "none",
                        "background": "transparent",
                        "color": Color.TEXT,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "outline": "none",
                    }
                ),
            ),
            style=rx.Style(
                {
                    "padding": "0 12px",
                    "background_color": Color.SLATE_50,
                    "border_radius": "20px",
                    "border": f"1px solid {Color.BORDER}",
                    "display": "flex",
                    "align_items": "center",
                    "transition": "all 0.2s",
                    "&:focus-within": {
                        "border_color": Color.ACCENT,
                        "box_shadow": Color.FOCUS_RING,
                    },
                }
            ),
        ),
        _pill_select(
            ["Fisik", "VM"], IPState.jenis_filter, IPState.set_jenis_filter, "Semua jenis"
        ),
        _pill_select(
            IPState.host_options, IPState.host_filter, IPState.set_host_filter, "Semua host"
        ),
        _pill_select(
            ["IP Operasional", "IP Server", "IP VM"],
            IPState.kategori_filter,
            IPState.set_kategori_filter,
            "Semua kategori",
        ),
        rx.el.button(
            rx.icon(tag="rotate-ccw", size=14),
            type="button",
            on_click=IPState.reset_filters,
            aria_label="Reset",
            style=rx.Style(
                {
                    "width": "36px",
                    "height": "36px",
                    "border_radius": "50%",
                    "background_color": Color.SLATE_100,
                    "color": Color.TEXT,
                    "border": "none",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
                    "cursor": "pointer",
                    "&:hover": {"background_color": Color.SLATE_200},
                }
            ),
        ),
        width="100%",
        spacing="3",
        align="center",
        padding="12px",
        wrap="wrap",
        style=rx.Style(
            {
                "background_color": "rgba(255,255,255,0.75)",
                "backdrop_filter": "blur(16px)",
                "border_bottom": f"1px solid {Color.BORDER}",
            }
        ),
    )


def _view_mode_toggle() -> rx.Component:
    return rx.hstack(
        rx.el.button(
            rx.hstack(
                rx.icon(tag="table", size=14),
                rx.text("Tabel", font_size=FontSize.SM, font_weight=FontWeight.BOLD),
                spacing="2",
                align="center",
            ),
            type="button",
            on_click=lambda: IPState.set_view_mode("table"),
            style=rx.Style(
                {
                    "height": "32px",
                    "padding": "0 12px",
                    "border_radius": "8px",
                    "border": "none",
                    "background_color": rx.cond(IPState.is_map_view, "transparent", Color.WHITE),
                    "color": rx.cond(IPState.is_map_view, Color.MUTED, Color.TEXT),
                    "box_shadow": rx.cond(
                        IPState.is_map_view, "none", "0 1px 3px rgba(0,0,0,0.08)"
                    ),
                    "cursor": "pointer",
                    "font_family": FONT_FAMILY,
                    "transition": "all 0.15s ease",
                }
            ),
        ),
        rx.el.button(
            rx.hstack(
                rx.icon(tag="network", size=14),
                rx.text("Peta IP", font_size=FontSize.SM, font_weight=FontWeight.BOLD),
                spacing="2",
                align="center",
            ),
            type="button",
            on_click=lambda: IPState.set_view_mode("map"),
            style=rx.Style(
                {
                    "height": "32px",
                    "padding": "0 12px",
                    "border_radius": "8px",
                    "border": "none",
                    "background_color": rx.cond(IPState.is_map_view, Color.WHITE, "transparent"),
                    "color": rx.cond(IPState.is_map_view, Color.TEXT, Color.MUTED),
                    "box_shadow": rx.cond(
                        IPState.is_map_view, "0 1px 3px rgba(0,0,0,0.08)", "none"
                    ),
                    "cursor": "pointer",
                    "font_family": FONT_FAMILY,
                    "transition": "all 0.15s ease",
                }
            ),
        ),
        spacing="1",
        align="center",
        padding="3px",
        background_color=Color.SLATE_100,
        border_radius="10px",
        border=f"1px solid {Color.BORDER}",
    )


def _map_legend_pill(
    label: str, bg: str, fg: str, border: str = "", is_dashed: bool = False
) -> rx.Component:
    border_val = f"1px {'dashed' if is_dashed else 'solid'} {border}" if border else "none"
    return rx.hstack(
        rx.box(
            width="12px",
            height="12px",
            border_radius="3px",
            background_color=bg,
            border=border_val,
        ),
        rx.text(
            label,
            font_size=FontSize.XS,
            font_weight=FontWeight.MEDIUM,
            color=Color.MUTED,
        ),
        spacing="2",
        align="center",
    )


def _ip_map_top_bar() -> rx.Component:
    def _subnet_select() -> rx.Component:
        return rx.box(
            rx.el.select(
                rx.foreach(
                    IPState.subnet_options,
                    lambda o: rx.el.option(o, value=o),
                ),
                value=IPState.active_subnet,
                on_change=IPState.set_active_subnet,
                style=rx.Style(
                    {
                        "height": "36px",
                        "padding": "0 30px 0 14px",
                        "background_color": "transparent",
                        "border": "none",
                        "color": Color.TEXT,
                        "font_family": "monospace",
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "appearance": "none",
                        "outline": "none",
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
            style=rx.Style(
                {
                    "position": "relative",
                    "background_color": Color.SLATE_50,
                    "border_radius": "20px",
                    "border": f"1px solid {Color.BORDER}",
                    "transition": "all 0.2s",
                    "&:focus-within": {
                        "border_color": Color.ACCENT,
                        "box_shadow": Color.FOCUS_RING,
                    },
                }
            ),
        )

    return rx.hstack(
        rx.hstack(
            _subnet_select(),
            rx.hstack(
                rx.el.input(
                    type="checkbox",
                    checked=IPState.map_only_empty,
                    on_change=IPState.toggle_map_only_empty,
                    style=rx.Style({"cursor": "pointer", "accent_color": Color.ACCENT}),
                ),
                rx.text(
                    "Hanya IP Kosong",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.MEDIUM,
                    color=Color.TEXT,
                    cursor="pointer",
                    on_click=IPState.toggle_map_only_empty,
                ),
                spacing="2",
                align="center",
                padding="0 8px",
            ),
            spacing="3",
            align="center",
        ),
        rx.hstack(
            _map_legend_pill("Network / Broadcast", Color.SLATE_200, Color.MUTED, Color.SLATE_300),
            _map_legend_pill("Fisik", Color.BLUE_100, Color.BLUE_700, Color.BLUE_BORDER),
            _map_legend_pill("VM", Color.PURPLE_100, Color.PURPLE_700, Color.PURPLE_500),
            _map_legend_pill("Bentrok", Color.RED_100, Color.RED_700, Color.RED_300),
            _map_legend_pill("Kosong", Color.WHITE, Color.MUTED, Color.SLATE_300, is_dashed=True),
            spacing="3",
            align="center",
            wrap="wrap",
        ),
        width="100%",
        justify="between",
        align="center",
        padding="12px 16px",
        wrap="wrap",
        style=rx.Style(
            {
                "background_color": "rgba(255,255,255,0.75)",
                "backdrop_filter": "blur(16px)",
                "border_bottom": f"1px solid {Color.BORDER}",
                "gap": "12px",
            }
        ),
    )


def _map_cell(cell: dict[str, Any]) -> rx.Component:
    status = cell["status"]
    octet = cell["octet"]
    ip_addr = cell["ip_address"]

    bg_color = rx.match(
        status,
        ("network", Color.SLATE_200),
        ("broadcast", Color.SLATE_200),
        ("bentrok", Color.RED_100),
        ("fisik", Color.BLUE_100),
        ("vm", Color.PURPLE_100),
        Color.WHITE,
    )
    text_color = rx.match(
        status,
        ("network", Color.MUTED),
        ("broadcast", Color.MUTED),
        ("bentrok", Color.RED_700),
        ("fisik", Color.BLUE_700),
        ("vm", Color.PURPLE_700),
        Color.MUTED,
    )
    border_color = rx.match(
        status,
        ("bentrok", Color.RED_500),
        ("fisik", Color.BLUE_BORDER),
        ("vm", Color.PURPLE_500),
        Color.SLATE_300,
    )
    border_style = rx.cond(status == "kosong", "dashed", "solid")
    is_selected = IPState.map_selected_octet == octet
    is_dimmed = IPState.map_only_empty & (status != "kosong")

    tooltip_content = rx.cond(
        cell["is_reserved"],
        f"IP: {ip_addr} · Reservasi Network",
        rx.cond(
            status == "kosong",
            f"IP: {ip_addr} · Tersedia",
            f"IP: {ip_addr} · {cell['pengguna']} ({cell['jenis']})",
        ),
    )

    return rx.tooltip(
        rx.box(
            rx.text(
                octet,
                font_size="10px",
                font_family="monospace",
                font_weight=FontWeight.BOLD,
                color=text_color,
            ),
            on_click=lambda: IPState.select_map_cell(cell),
            style=rx.Style(
                {
                    "height": "32px",
                    "display": "flex",
                    "align_items": "center",
                    "justify_content": "center",
                    "background_color": bg_color,
                    "border_width": "1px",
                    "border_style": border_style,
                    "border_color": border_color,
                    "border_radius": "6px",
                    "cursor": rx.cond(cell["is_reserved"], "not-allowed", "pointer"),
                    "opacity": rx.cond(is_dimmed, "0.18", "1"),
                    "box_shadow": rx.cond(
                        is_selected,
                        f"0 0 0 2px {Color.ACCENT}",
                        "none",
                    ),
                    "transition": "all 0.12s ease",
                    "_hover": {
                        "transform": "scale(1.08)",
                        "z_index": "5",
                        "box_shadow": "0 2px 8px rgba(0,0,0,0.12)",
                    },
                }
            ),
        ),
        content=tooltip_content,
    )


def _ip_map_sidebar() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.text(
                "RINGKASAN SUBNET",
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            rx.heading(
                IPState.active_subnet,
                font_size="16px",
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
            ),
            rx.box(
                rx.box(
                    width=f"{IPState.map_stats['fisik_percent']}%",
                    height="100%",
                    background_color=Color.BLUE_600,
                ),
                rx.box(
                    width=f"{IPState.map_stats['vm_percent']}%",
                    height="100%",
                    background_color=Color.PURPLE_600,
                ),
                rx.box(
                    width=f"{IPState.map_stats['bentrok_percent']}%",
                    height="100%",
                    background_color=Color.RED_600,
                ),
                rx.box(
                    width=f"{IPState.map_stats['kosong_percent']}%",
                    height="100%",
                    background_color=Color.GREEN_400,
                ),
                style=rx.Style(
                    {
                        "width": "100%",
                        "height": "8px",
                        "border_radius": Radius.FULL,
                        "background_color": Color.SLATE_200,
                        "overflow": "hidden",
                        "display": "flex",
                        "margin_top": "6px",
                    }
                ),
            ),
            rx.box(
                rx.hstack(
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", bg=Color.BLUE_600),
                        rx.text(
                            f"Fisik: {IPState.map_stats['fisik']}",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", bg=Color.PURPLE_600),
                        rx.text(
                            f"VM: {IPState.map_stats['vm']}",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", bg=Color.RED_600),
                        rx.text(
                            f"Bentrok: {IPState.map_stats['bentrok']}",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", bg=Color.GREEN_400),
                        rx.text(
                            f"Kosong: {IPState.map_stats['kosong']}",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    spacing="3",
                    wrap="wrap",
                    margin_top="6px",
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
            padding_bottom="16px",
            style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
        ),
        rx.vstack(
            rx.text(
                "ALAMAT TERPILIH",
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            rx.cond(
                IPState.map_selected_octet >= 0,
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            IPState.map_selected_ip_display,
                            font_size="15px",
                            font_weight=FontWeight.BOLD,
                            font_family="monospace",
                            color=Color.TEXT,
                        ),
                        rx.cond(
                            IPState.has_map_selected_empty,
                            rx.box(
                                rx.text(
                                    "Tersedia",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.GREEN_700,
                                ),
                                padding="2px 8px",
                                border_radius=Radius.FULL,
                                background_color=Color.GREEN_100,
                            ),
                            rx.box(
                                rx.text(
                                    IPState.map_selected_cell["status"],
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.BLUE_700,
                                ),
                                padding="2px 8px",
                                border_radius=Radius.FULL,
                                background_color=Color.BLUE_100,
                            ),
                        ),
                        justify="between",
                        align="center",
                        width="100%",
                    ),
                    rx.cond(
                        IPState.has_map_selected_empty,
                        rx.el.button(
                            "+ Tambah IP di Alamat Ini",
                            type="button",
                            on_click=lambda: IPState.open_add_from_map(
                                IPState.map_selected_ip_display
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": "36px",
                                    "background": Color.GRADIENT_PRIMARY,
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": "8px",
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                    "margin_top": "6px",
                                }
                            ),
                        ),
                        rx.vstack(
                            rx.text(
                                f"Pengguna: {IPState.map_selected_cell['pengguna']}",
                                font_size=FontSize.SM,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                f"Jenis: {IPState.map_selected_cell['jenis']}",
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                            ),
                            rx.el.button(
                                "Buka Detail Drawer",
                                type="button",
                                on_click=lambda: IPState.open_detail_drawer_by_id(
                                    IPState.map_selected_cell["entry_id"]
                                ),
                                style=rx.Style(
                                    {
                                        "width": "100%",
                                        "height": "34px",
                                        "background_color": Color.SURFACE,
                                        "border": f"1px solid {Color.BORDER}",
                                        "color": Color.TEXT,
                                        "border_radius": "8px",
                                        "font_family": FONT_FAMILY,
                                        "font_size": FontSize.SM,
                                        "font_weight": FontWeight.MEDIUM,
                                        "cursor": "pointer",
                                        "margin_top": "6px",
                                    }
                                ),
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                    padding="12px",
                    background_color=Color.SURFACE,
                    border=f"1px solid {Color.BORDER}",
                    border_radius="10px",
                ),
                rx.box(
                    rx.text(
                        "Klik salah satu kotak IP pada peta untuk melihat "
                        "rincian alokasi atau mendaftarkan IP baru.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                        line_height="1.5",
                    ),
                    padding="12px",
                    background_color=Color.SURFACE,
                    border=f"1px solid {Color.BORDER}",
                    border_radius="10px",
                    width="100%",
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
            padding_bottom="16px",
            style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
        ),
        rx.vstack(
            rx.text(
                "SARAN IP KOSONG",
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            rx.cond(
                IPState.map_suggested_ips.length() > 0,
                rx.box(
                    rx.foreach(
                        IPState.map_suggested_ips,
                        lambda ip: rx.el.button(
                            ip,
                            type="button",
                            on_click=lambda: IPState.open_add_from_map(ip),
                            style=rx.Style(
                                {
                                    "padding": "4px 10px",
                                    "background_color": Color.GREEN_50,
                                    "border": f"1px solid {Color.GREEN_BORDER}",
                                    "color": Color.GREEN_800,
                                    "border_radius": "6px",
                                    "font_family": "monospace",
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                    "margin": "2px",
                                    "transition": "all 0.15s ease",
                                    "&:hover": {
                                        "background_color": Color.GREEN_100,
                                        "transform": "translateY(-1px)",
                                    },
                                }
                            ),
                        ),
                    ),
                    display="flex",
                    flex_wrap="wrap",
                    gap="4px",
                    width="100%",
                ),
                rx.text("Tidak ada saran IP kosong.", font_size=FontSize.XS, color=Color.MUTED),
            ),
            spacing="2",
            align="start",
            width="100%",
            padding_bottom="16px",
            style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
        ),
        rx.vstack(
            rx.text(
                "BLOK KOSONG TERPANJANG",
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            rx.cond(
                IPState.map_largest_empty_range != "",
                rx.box(
                    rx.hstack(
                        rx.icon(tag="circle-check", size=16, color=Color.GREEN_700),
                        rx.text(
                            IPState.map_largest_empty_range,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.GREEN_800,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    padding="10px 12px",
                    background_color=Color.GREEN_50,
                    border=f"1px solid {Color.GREEN_BORDER}",
                    border_radius="8px",
                    width="100%",
                ),
                rx.text("Tidak ada blok kosong.", font_size=FontSize.XS, color=Color.MUTED),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="300px",
        min_width="280px",
        max_width="320px",
        spacing="4",
        align="start",
        padding="20px",
        background_color=Color.SLATE_50,
        style=rx.Style({"border_left": f"1px solid {Color.BORDER}"}),
    )


def _ip_map_view() -> rx.Component:
    return rx.vstack(
        _ip_map_top_bar(),
        rx.hstack(
            rx.box(
                rx.box(
                    rx.foreach(IPState.map_cells, _map_cell),
                    style=rx.Style(
                        {
                            "display": "grid",
                            "grid_template_columns": "repeat(16, minmax(0, 1fr))",
                            "gap": "5px",
                            "width": "100%",
                        }
                    ),
                ),
                width="100%",
                padding="20px",
                overflow_x="auto",
            ),
            _ip_map_sidebar(),
            width="100%",
            spacing="0",
            align="stretch",
        ),
        spacing="0",
        width="100%",
    )


def _ip_table_card() -> rx.Component:
    tabs_config: list[TabItemConfig] = [
        {"key": "Semua", "label": "Semua", "count": IPState.kpi_total_ip},
        {"key": "Fisik", "label": "Fisik", "count": IPState.kpi_fisik},
        {"key": "VM", "label": "VM", "count": IPState.kpi_vm},
    ]
    return rx.box(
        rx.hstack(
            app_tabs(
                tabs=tabs_config,
                active_tab=IPState.active_jenis_tab,
                on_change=IPState.set_jenis_tab,
            ),
            _view_mode_toggle(),
            width="100%",
            justify="between",
            align="center",
            padding_right="16px",
            style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
        ),
        rx.cond(
            IPState.is_map_view,
            _ip_map_view(),
            rx.vstack(
                _futuristic_filter_bar(),
                reusable_data_table(
                    columns=IP_TABLE_COLUMNS,
                    rows=IPState.items,
                    id_key="id",
                    active_row_id=IPState.active_entry_id,
                    is_loading=IPState.is_loading,
                    on_row_click=IPState.open_drawer,
                    on_edit_row=IPState.open_edit_modal,
                    on_duplicate_row=IPState.open_duplicate_modal,
                    duplicate_action_label="Duplikat",
                    on_delete_row=IPState.confirm_delete_entry,
                    on_reset_filter=IPState.reset_filters,
                    sort_by=IPState.sort_by,
                    sort_dir=IPState.sort_dir,
                    on_sort=IPState.toggle_sort,
                    empty_message="Tidak ada entri IP yang cocok",
                    empty_subtitle="Ubah kata kunci pencarian atau reset filter.",
                    empty_action_label="Reset filter",
                    on_empty_action=IPState.reset_filters,
                ),
                table_pagination(
                    summary_text=IPState.pagination_summary,
                    current_page=IPState.page,
                    current_page_str=IPState.current_page_str,
                    total_pages=IPState.total_pages,
                    page_tokens=IPState.page_tokens,
                    on_prev=IPState.prev_page,
                    on_next=IPState.next_page,
                    on_page_select=IPState.select_page,
                ),
                spacing="0",
                width="100%",
            ),
        ),
        style=rx.Style(
            {
                "width": "100%",
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": "16px",
                "overflow": "hidden",
                "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
            }
        ),
    )


def ip_vm_page() -> rx.Component:
    return base_layout(
        content=rx.vstack(
            _ip_header(),
            _ip_kpi_row(),
            rx.cond(
                IPState.has_conflict_banner,
                rx.hstack(
                    rx.hstack(
                        rx.icon(tag="triangle-alert", size=18, color=Color.DANGER_FG),
                        rx.text(
                            IPState.conflict_banner_text,
                            font_size=FontSize.SM,
                            font_weight=FontWeight.BOLD,
                            color=Color.DANGER_FG,
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.el.button(
                        rx.cond(IPState.only_conflict_filter, "Tampilkan Semua", "Tampilkan"),
                        type="button",
                        on_click=IPState.toggle_conflict_only,
                        style=rx.Style(
                            {
                                "height": "34px",
                                "padding": "0 14px",
                                "background_color": Color.SURFACE,
                                "color": Color.DANGER_FG,
                                "border": f"1px solid {Color.DANGER_FG}",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.XS,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                                "white_space": "nowrap",
                            }
                        ),
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    padding="12px 18px",
                    style=rx.Style(
                        {
                            "background_color": Color.DANGER_BG,
                            "border": f"1px solid {Color.DANGER_FG}",
                            "border_radius": Radius.CARD,
                        }
                    ),
                ),
                rx.fragment(),
            ),
            _ip_table_card(),
            detail_drawer(
                is_open=IPState.drawer_open,
                on_close=IPState.close_drawer,
                code_var=IPState.active_ip_code,
                title_var=IPState.active_pengguna_title,
                category_var=IPState.active_kategori_badge,
                status_var=IPState.active_status_badge,
                active_tab=IPState.drawer_tab,
                on_tab_change=IPState.set_drawer_tab,
                section1_title="Data entri IP",
                general_items=IPState.active_general_items,
                section2_title="Aset fisik & VM",
                usage_items=IPState.active_relation_items,
                history_items=IPState.active_history_items,
                duplicate_label="Duplikat",
                on_edit=lambda: IPState.open_edit_modal(""),
                on_duplicate=lambda: IPState.open_duplicate_modal(""),
                on_delete=lambda: IPState.confirm_delete_entry(""),
                tabs=(("detail", "Rincian IP & Host"), ("history", "Riwayat & Log")),
            ),
            ip_form_modal(),
            rx.cond(
                IPState.import_modal_open,
                rx.box(
                    rx.box(
                        on_click=IPState.close_import_modal,
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
                            rx.heading(
                                "Import Data IP",
                                font_size="20px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                "Gunakan template Excel standar.",
                                font_size=FontSize.SM,
                                color=Color.MUTED,
                            ),
                            padding="22px 24px",
                            style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                        ),
                        rx.vstack(
                            rx.hstack(
                                rx.center(
                                    rx.text("1", color=Color.WHITE, font_weight="bold"),
                                    width="26px",
                                    height="26px",
                                    bg=Color.BLUE_700,
                                    border_radius="50%",
                                ),
                                rx.vstack(
                                    rx.text("Unduh template", font_weight="bold"),
                                    rx.el.button(
                                        "Unduh template .xlsx",
                                        on_click=IPState.download_import_template,
                                        style=rx.Style(
                                            {
                                                "padding": "8px 16px",
                                                "border": f"1px solid {Color.SLATE_200}",
                                                "border_radius": "8px",
                                                "cursor": "pointer",
                                            }
                                        ),
                                    ),
                                ),
                                spacing="3",
                            ),
                            rx.hstack(
                                rx.center(
                                    rx.text("2", color=Color.WHITE, font_weight="bold"),
                                    width="26px",
                                    height="26px",
                                    bg=Color.BLUE_700,
                                    border_radius="50%",
                                ),
                                rx.vstack(
                                    rx.text("Unggah file", font_weight="bold"),
                                    rx.upload(
                                        rx.text(
                                            "Tarik file ke sini .xlsx / .csv",
                                            color=Color.MUTED,
                                            font_size="13px",
                                        ),
                                        id="ip-import",
                                        on_drop=IPState.handle_import_upload(
                                            rx.upload_files("ip-import")
                                        ),
                                        style=rx.Style(
                                            {
                                                "padding": "20px",
                                                "border": f"1.5px dashed {Color.SLATE_300}",
                                                "border_radius": "12px",
                                            }
                                        ),
                                    ),
                                    spacing="1",
                                ),
                                spacing="3",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Jika IP sudah terdaftar di database:",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                rx.radio(
                                    ["Lewati duplikat", "Perbarui data jika IP ada"],
                                    value=IPState.import_duplicate_mode_label,
                                    on_change=IPState.set_import_duplicate_mode,
                                    direction="row",
                                    spacing="4",
                                ),
                                spacing="2",
                                align="start",
                                width="100%",
                                padding="12px 14px",
                                background_color=Color.SLATE_50,
                                border=f"1px solid {Color.BORDER}",
                                border_radius="10px",
                            ),
                            rx.cond(
                                IPState.import_has_preview,
                                rx.hstack(
                                    rx.text(
                                        IPState.import_summary_text,
                                        color=Color.GREEN_700,
                                        font_size="13px",
                                    ),
                                    rx.cond(
                                        IPState.import_error_count > 0,
                                        rx.el.button(
                                            "Unduh error",
                                            on_click=IPState.download_import_error_report,
                                            style=rx.Style(
                                                {
                                                    "color": Color.DANGER_FG,
                                                    "background": "none",
                                                    "border": "none",
                                                    "cursor": "pointer",
                                                }
                                            ),
                                        ),
                                        rx.fragment(),
                                    ),
                                    justify="between",
                                    padding="12px",
                                    bg=Color.GREEN_50,
                                    border_radius="8px",
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            padding="24px",
                            spacing="4",
                        ),
                        rx.hstack(
                            rx.el.button(
                                "Batal",
                                on_click=IPState.close_import_modal,
                                style=rx.Style(
                                    {
                                        "padding": "8px 16px",
                                        "border": f"1px solid {Color.SLATE_200}",
                                        "border_radius": "8px",
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            rx.el.button(
                                rx.cond(
                                    IPState.import_is_processing,
                                    "Memproses...",
                                    IPState.import_button_label,
                                ),
                                on_click=IPState.commit_import_data,
                                disabled=rx.cond(
                                    IPState.import_valid_count == 0,
                                    True,
                                    IPState.import_is_processing,
                                ),
                                style=rx.Style(
                                    {
                                        "padding": "8px 16px",
                                        "background": Color.ACCENT,
                                        "color": Color.WHITE,
                                        "border_radius": "8px",
                                        "cursor": rx.cond(
                                            IPState.import_is_processing,
                                            "not-allowed",
                                            "pointer",
                                        ),
                                        "opacity": rx.cond(
                                            IPState.import_is_processing,
                                            "0.7",
                                            "1",
                                        ),
                                    }
                                ),
                            ),
                            justify="end",
                            padding="16px",
                            bg=Color.SLATE_50,
                            style=rx.Style({"border_top": f"1px solid {Color.BORDER}"}),
                        ),
                        style=rx.Style(
                            {
                                "position": "fixed",
                                "top": "50%",
                                "left": "50%",
                                "transform": "translate(-50%, -50%)",
                                "width": "500px",
                                "background": Color.WHITE,
                                "border_radius": "16px",
                                "z_index": "90",
                                "box_shadow": Shadow.POPOVER,
                            }
                        ),
                    ),
                ),
                rx.fragment(),
            ),
            confirm_delete_dialog(
                is_open=IPState.delete_dialog_open,
                title="Hapus Entri IP?",
                description=f"Apakah Anda yakin ingin menghapus {IPState.entry_to_delete_label}?",
                on_cancel=IPState.cancel_delete,
                on_confirm=IPState.execute_delete_entry,
            ),
            spacing="0",
            style=rx.Style({"gap": Space.S4}),
            align="start",
            width="100%",
        ),
        breadcrumb=("Infrastructure", "IP & Server (VM)"),
    )


__all__ = ["IP_TABLE_COLUMNS", "ip_vm_page"]
