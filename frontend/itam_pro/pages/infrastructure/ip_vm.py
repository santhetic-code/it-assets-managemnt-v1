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
                    rx.menu.item(
                        rx.hstack(
                            rx.icon(tag="file-spreadsheet", size=15),
                            rx.text("Excel (.xlsx)"),
                            spacing="2",
                            align="center",
                        ),
                        on_click=IPState.export_excel,
                    ),
                    rx.menu.item(
                        rx.hstack(
                            rx.icon(tag="file-text", size=15),
                            rx.text("PDF (.pdf)"),
                            spacing="2",
                            align="center",
                        ),
                        on_click=IPState.export_pdf,
                    ),
                    rx.menu.separator(),
                    rx.menu.item(
                        rx.hstack(
                            rx.icon(tag="printer", size=15),
                            rx.text("Cetak"),
                            spacing="2",
                            align="center",
                        ),
                        on_click=IPState.open_print_modal,
                    ),
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


def _interactive_stat_card(
    card_key: str,
    title: str,
    icon_tag: str,
    icon_bg: str,
    icon_color: str,
    value_var: Any,
    subtitle_var: Any,
    percent_var: Any,
    bar_color: str,
    action_label: str,
) -> rx.Component:
    is_active = IPState.active_stat_card == card_key
    return rx.el.button(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.center(
                        rx.icon(tag=icon_tag, size=17, color=icon_color, stroke_width=2),
                        width="34px",
                        height="34px",
                        background_color=icon_bg,
                        border_radius="10px",
                        flex_shrink="0",
                    ),
                    rx.text(
                        title,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    is_active,
                    rx.box(
                        rx.text(
                            "Ditampilkan",
                            font_size="10px",
                            font_weight=FontWeight.BOLD,
                            color=Color.ACCENT,
                        ),
                        padding="2px 8px",
                        border_radius=Radius.FULL,
                        background_color=Color.BLUE_100,
                    ),
                    rx.fragment(),
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            rx.text(
                value_var,
                class_name="itam-kpi-countup",
                font_size="32px",
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.1",
                margin_top="4px",
                style=rx.Style({"font_variant_numeric": "tabular-nums"}),
            ),
            rx.text(
                subtitle_var,
                font_size=FontSize.FOOTER,
                font_weight=FontWeight.MEDIUM,
                color=Color.MUTED,
                text_align="left",
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
                        "height": "5px",
                        "background_color": Color.SLATE_200,
                        "border_radius": Radius.FULL,
                        "overflow": "hidden",
                        "margin_top": "4px",
                    }
                ),
            ),
            rx.text(
                action_label,
                font_size="11.5px",
                font_weight=FontWeight.BOLD,
                color=Color.ACCENT,
                margin_top="2px",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        type="button",
        aria_pressed=is_active,
        on_click=IPState.click_stat_card(card_key),
        style=rx.Style(
            {
                "background_color": Color.SURFACE,
                "border": rx.cond(
                    is_active,
                    f"2px solid {Color.ACCENT}",
                    f"1px solid {Color.BORDER}",
                ),
                "box_shadow": rx.cond(
                    is_active,
                    "0 0 0 3px rgba(37, 99, 235, 0.14)",
                    "none",
                ),
                "border_radius": "16px",
                "padding": "16px 18px",
                "width": "100%",
                "text_align": "left",
                "cursor": "pointer",
                "font_family": FONT_FAMILY,
                "transition": "all 150ms ease",
                "_hover": {
                    "transform": "translateY(-2px)",
                    "box_shadow": "0 8px 20px rgba(15, 23, 42, 0.07)",
                    "border_color": Color.ACCENT,
                },
                "_focus_visible": {
                    "outline": "none",
                    "box_shadow": f"0 0 0 3px {Color.ACCENT}",
                },
            }
        ),
    )


def _ip_kpi_row() -> rx.Component:
    is_total_active = IPState.active_stat_card == "total"
    is_bentrok_active = IPState.active_stat_card == "bentrok"
    has_conflict = IPState.kpi_bentrok > 0

    return rx.box(
        rx.el.style(
            """
            @keyframes itamCountFadeUp {
                0% { opacity: 0.25; transform: translateY(5px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            @media (prefers-reduced-motion: no-preference) {
                .itam-kpi-countup {
                    animation: itamCountFadeUp 400ms cubic-bezier(0.16, 1, 0.3, 1);
                }
            }
            """
        ),
        # 1. Kartu Hero Total IP dengan Cincin Donut Komposisi (B5)
        rx.el.button(
            rx.hstack(
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
                        rx.cond(
                            is_total_active,
                            rx.box(
                                rx.text(
                                    "Ditampilkan",
                                    font_size="10px",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.WHITE,
                                ),
                                padding="2px 8px",
                                border_radius=Radius.FULL,
                                style=rx.Style({"background_color": "rgba(255,255,255,0.22)"}),
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        IPState.kpi_total_ip,
                        class_name="itam-kpi-countup",
                        font_size="34px",
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.WHITE,
                        line_height="1.1",
                        margin_top="4px",
                        style=rx.Style({"font_variant_numeric": "tabular-nums"}),
                    ),
                    rx.text(
                        "Semua entri terdaftar",
                        font_size=FontSize.FOOTER,
                        font_weight=FontWeight.MEDIUM,
                        color="rgba(255, 255, 255, 0.82)",
                    ),
                    rx.text(
                        "Lihat semua IP ->",
                        font_size="11.5px",
                        font_weight=FontWeight.BOLD,
                        color="rgba(255, 255, 255, 0.95)",
                        margin_top="2px",
                    ),
                    spacing="2",
                    align="start",
                ),
                # Cincin Donut Komposisi Fisik / VM / Kosong + Persentase Terpakai di tengah
                rx.center(
                    rx.center(
                        rx.text(
                            f"{IPState.used_subnet_percent}%",
                            font_size="12px",
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.WHITE,
                            style=rx.Style({"font_variant_numeric": "tabular-nums"}),
                        ),
                        width="48px",
                        height="48px",
                        border_radius="50%",
                        style=rx.Style({"background_color": Color.NAVY_DONUT_INNER}),
                    ),
                    width="64px",
                    height="64px",
                    border_radius="50%",
                    flex_shrink="0",
                    style=rx.Style(
                        {
                            "background": (
                                f"conic-gradient({Color.BLUE_500} 0% {IPState.fisik_percent}%, "
                                f"{Color.PURPLE_500} {IPState.fisik_percent}% "
                                f"{IPState.fisik_percent + IPState.vm_percent}%, "
                                f"rgba(255,255,255,0.2) "
                                f"{IPState.fisik_percent + IPState.vm_percent}% 100%)"
                            )
                        }
                    ),
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            type="button",
            aria_pressed=is_total_active,
            on_click=IPState.click_stat_card("total"),
            style=rx.Style(
                {
                    "background": Color.GRADIENT_NAVY,
                    "border": rx.cond(
                        is_total_active,
                        f"2px solid {Color.CHART_MONITOR}",
                        "1px solid transparent",
                    ),
                    "border_radius": "16px",
                    "padding": "16px 20px",
                    "width": "100%",
                    "text_align": "left",
                    "cursor": "pointer",
                    "font_family": FONT_FAMILY,
                    "box_shadow": rx.cond(
                        is_total_active,
                        "0 0 0 3px rgba(59, 130, 246, 0.35), 0 8px 20px rgba(15, 23, 42, 0.18)",
                        "0 8px 20px rgba(15, 23, 42, 0.14)",
                    ),
                    "transition": "all 150ms ease",
                    "_hover": {
                        "transform": "translateY(-2px)",
                        "box_shadow": "0 12px 24px rgba(29, 78, 216, 0.28)",
                    },
                    "_focus_visible": {
                        "outline": "none",
                        "box_shadow": f"0 0 0 3px {Color.ACCENT}",
                    },
                }
            ),
        ),
        # 2. Kartu Server Fisik
        _interactive_stat_card(
            "fisik",
            "SERVER FISIK",
            "monitor",
            Color.BLUE_100,
            Color.BLUE_600,
            IPState.kpi_fisik,
            f"PC & server fisik · {IPState.fisik_percent}%",
            IPState.fisik_percent,
            Color.BLUE_600,
            "Lihat IP Fisik ->",
        ),
        # 3. Kartu VM
        _interactive_stat_card(
            "vm",
            "VM",
            "layers",
            Color.PURPLE_BG,
            Color.PURPLE_600,
            IPState.kpi_vm,
            f"Mesin virtual · {IPState.vm_percent}%",
            IPState.vm_percent,
            Color.PURPLE_600,
            "Lihat IP VM ->",
        ),
        # 4. Kartu IP Bentrok (B3 & B5: hijau jika 0 + tooltip "Tidak ada konflik", merah jika > 0)
        rx.tooltip(
            rx.el.button(
                rx.vstack(
                    rx.hstack(
                        rx.hstack(
                            rx.center(
                                rx.icon(
                                    tag=rx.cond(has_conflict, "triangle-alert", "shield-check"),
                                    size=17,
                                    color=rx.cond(has_conflict, Color.RED_600, Color.GREEN_700),
                                    stroke_width=2,
                                ),
                                width="34px",
                                height="34px",
                                background_color=rx.cond(
                                    has_conflict, Color.RED_100, Color.GREEN_100
                                ),
                                border_radius="10px",
                            ),
                            rx.text(
                                "IP BENTROK",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.06em",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.cond(
                            is_bentrok_active,
                            rx.box(
                                rx.text(
                                    "Ditampilkan",
                                    font_size="10px",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.RED_700,
                                ),
                                padding="2px 8px",
                                border_radius=Radius.FULL,
                                background_color=Color.RED_100,
                            ),
                            rx.fragment(),
                        ),
                        width="100%",
                        justify="between",
                        align="center",
                    ),
                    rx.hstack(
                        rx.text(
                            IPState.kpi_bentrok,
                            class_name="itam-kpi-countup",
                            font_size="32px",
                            font_weight=FontWeight.EXTRABOLD,
                            color=rx.cond(has_conflict, Color.RED_700, Color.GREEN_700),
                            line_height="1.1",
                            style=rx.Style({"font_variant_numeric": "tabular-nums"}),
                        ),
                        rx.box(
                            rx.text(
                                rx.cond(has_conflict, "Bentrok", "Aman"),
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=rx.cond(has_conflict, Color.RED_700, Color.GREEN_700),
                            ),
                            style=rx.Style(
                                {
                                    "padding": "3px 10px",
                                    "border_radius": Radius.FULL,
                                    "background_color": rx.cond(
                                        has_conflict, Color.RED_100, Color.GREEN_100
                                    ),
                                }
                            ),
                        ),
                        spacing="3",
                        align="center",
                        margin_top="4px",
                    ),
                    rx.text(
                        rx.cond(has_conflict, "Memakai IPv4 yang sama", "Tidak ada konflik IP"),
                        font_size=FontSize.FOOTER,
                        font_weight=FontWeight.MEDIUM,
                        color=Color.MUTED,
                    ),
                    rx.text(
                        rx.cond(has_conflict, "Lihat konflik ->", "Status jaringan aman"),
                        font_size="11.5px",
                        font_weight=FontWeight.BOLD,
                        color=rx.cond(has_conflict, Color.RED_600, Color.GREEN_700),
                        margin_top="6px",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                type="button",
                disabled=IPState.kpi_bentrok <= 0,
                aria_pressed=is_bentrok_active,
                on_click=IPState.click_stat_card("bentrok"),
                style=rx.Style(
                    {
                        "background_color": Color.SURFACE,
                        "border": rx.cond(
                            is_bentrok_active,
                            f"2px solid {Color.RED_600}",
                            f"1px solid {Color.BORDER}",
                        ),
                        "border_radius": "16px",
                        "padding": "16px 18px",
                        "width": "100%",
                        "text_align": "left",
                        "font_family": FONT_FAMILY,
                        "cursor": rx.cond(has_conflict, "pointer", "default"),
                        "transition": "all 150ms ease",
                        "_hover": {
                            "transform": rx.cond(has_conflict, "translateY(-2px)", "none"),
                            "border_color": rx.cond(has_conflict, Color.RED_300, Color.GREEN_400),
                        },
                        "_focus_visible": {
                            "outline": "none",
                            "box_shadow": f"0 0 0 3px {Color.ACCENT}",
                        },
                    }
                ),
            ),
            content=rx.cond(has_conflict, "Filter IP yang mengalami bentrok", "Tidak ada konflik"),
        ),
        # 5. Kartu IP Kosong -> Buka Peta IP
        _interactive_stat_card(
            "kosong",
            "IP KOSONG",
            "database",
            Color.GREEN_100,
            Color.GREEN_700,
            IPState.kpi_kosong_count,
            f"Tersedia · {IPState.kosong_percent}% dari 254",
            IPState.kosong_percent,
            Color.GREEN_400,
            "Buka Peta IP ->",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "1.5fr 1fr 1fr 1fr 1fr",
                "gap": "16px",
                "@media (max-width: 1150px)": {
                    "grid_template_columns": "repeat(2, minmax(0, 1fr))"
                },
                "@media (max-width: 600px)": {"grid_template_columns": "1fr"},
            }
        ),
    )


def _futuristic_filter_bar() -> rx.Component:
    """Filter bar dengan debounce 300ms (C2) & dropdown Host cerdas (A3)."""

    def _pill_select(
        opts: Any,
        val: Any,
        on_change: Any,
        placeholder: str,
        disabled: Any = False,
    ) -> rx.Component:
        return rx.box(
            rx.el.select(
                rx.el.option(placeholder, value=""),
                rx.foreach(opts, lambda o: rx.el.option(o, value=o)),
                value=val,
                disabled=disabled,
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
                        "cursor": rx.cond(disabled, "not-allowed", "pointer"),
                        "opacity": rx.cond(disabled, "0.55", "1"),
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
            rx.debounce_input(
                rx.el.input(
                    placeholder="Cari IP, pengguna, os...",
                    value=IPState.search_query,
                    on_change=IPState.set_search_query,
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
                debounce_timeout=300,
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
        # A3: Nonaktifkan dan beri tooltip "Belum ada VM" jika belum ada host VM terhubung
        rx.cond(
            IPState.has_connected_vm_hosts,
            _pill_select(
                IPState.clean_host_options,
                IPState.host_filter,
                IPState.set_host_filter,
                "Semua host",
            ),
            rx.tooltip(
                _pill_select(
                    IPState.clean_host_options,
                    IPState.host_filter,
                    IPState.set_host_filter,
                    "Semua host",
                    disabled=True,
                ),
                content="Belum ada VM",
            ),
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
    """A4: Beri white-space: nowrap dan lebar minimal agar 'Peta IP' tidak pecah 2 baris."""
    return rx.hstack(
        rx.el.button(
            rx.hstack(
                rx.icon(tag="table", size=14, flex_shrink="0"),
                rx.text(
                    "Tabel",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    style=rx.Style({"white_space": "nowrap"}),
                ),
                spacing="2",
                align="center",
            ),
            type="button",
            on_click=IPState.set_view_mode("table"),
            style=rx.Style(
                {
                    "height": "32px",
                    "min_width": "84px",
                    "padding": "0 12px",
                    "border_radius": "8px",
                    "border": "none",
                    "white_space": "nowrap",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
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
                rx.icon(tag="network", size=14, flex_shrink="0"),
                rx.text(
                    "Peta IP",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    style=rx.Style({"white_space": "nowrap"}),
                ),
                spacing="2",
                align="center",
            ),
            type="button",
            on_click=IPState.set_view_mode("map"),
            style=rx.Style(
                {
                    "height": "32px",
                    "min_width": "92px",
                    "padding": "0 12px",
                    "border_radius": "8px",
                    "border": "none",
                    "white_space": "nowrap",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
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
        flex_shrink="0",
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
    def _subnet_badge_or_select() -> rx.Component:
        return rx.cond(
            IPState.has_multiple_subnets,
            rx.box(
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
                style=rx.Style(
                    {
                        "position": "relative",
                        "background_color": Color.SLATE_50,
                        "border_radius": "20px",
                        "border": f"1px solid {Color.BORDER}",
                    }
                ),
            ),
            rx.hstack(
                rx.icon(tag="network", size=14, color=Color.BLUE_700),
                rx.text(
                    "192.168.1.0/24",
                    font_family="monospace",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
                spacing="2",
                align="center",
                padding="6px 14px",
                background_color=Color.SLATE_100,
                border=f"1px solid {Color.BORDER}",
                border_radius="20px",
            ),
        )

    return rx.hstack(
        rx.hstack(
            _subnet_badge_or_select(),
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
            on_click=IPState.select_map_cell(cell),
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
                            on_click=IPState.open_add_from_map(IPState.map_selected_ip_display),
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
                                on_click=IPState.open_detail_drawer_by_id(
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
                IPState.map_suggested_ips,
                rx.box(
                    rx.foreach(
                        IPState.map_suggested_ips,
                        lambda ip: rx.el.button(
                            ip,
                            type="button",
                            on_click=IPState.open_add_from_map(ip),
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
        id="ip-main-content-card",
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


def _col_chip(label: str, required: bool = False) -> rx.Component:
    return rx.box(
        rx.text(
            f"{label} *" if required else label,
            font_size="11.5px",
            font_weight=FontWeight.BOLD if required else FontWeight.MEDIUM,
            color=Color.BLUE_700 if required else Color.MUTED,
        ),
        padding="3px 10px",
        border_radius=Radius.FULL,
        background_color=Color.BLUE_100 if required else Color.SLATE_100,
        border=f"1px solid {Color.BLUE_BORDER if required else Color.BORDER}",
    )


def _ip_import_modal() -> rx.Component:
    """B1: Modal Import Artboard 3b (2 kondisi: sebelum & sesudah file dipilih)."""
    return rx.cond(
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
                # Header Artboard 3b
                rx.hstack(
                    rx.hstack(
                        rx.center(
                            rx.icon(tag="upload", size=22, color=Color.WHITE, stroke_width=2),
                            width="44px",
                            height="44px",
                            border_radius="12px",
                            flex_shrink="0",
                            style=rx.Style({"background": Color.GRADIENT_BLUE}),
                        ),
                        rx.vstack(
                            rx.heading(
                                "Import Data IP & Server (VM)",
                                font_size="19px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                "Tambahkan banyak IP sekaligus dari file Excel atau CSV.",
                                font_size=FontSize.SM,
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=18, color=Color.MUTED),
                        type="button",
                        on_click=IPState.close_import_modal,
                        style=rx.Style(
                            {
                                "width": "34px",
                                "height": "34px",
                                "border_radius": Radius.CONTROL,
                                "border": f"1px solid {Color.BORDER}",
                                "background_color": Color.SURFACE,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    width="100%",
                    justify="between",
                    align="start",
                    padding="20px 24px 16px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body Scrollable
                rx.box(
                    rx.vstack(
                        # Langkah 1: Template & Chip Kolom
                        rx.vstack(
                            rx.hstack(
                                rx.center(
                                    rx.text(
                                        "1",
                                        font_size="12px",
                                        font_weight=FontWeight.BOLD,
                                        color=Color.WHITE,
                                    ),
                                    width="24px",
                                    height="24px",
                                    border_radius="50%",
                                    background_color=Color.ACCENT,
                                ),
                                rx.text(
                                    "Siapkan file sesuai kolom template standar",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                rx.spacer(),
                                rx.el.button(
                                    rx.hstack(
                                        rx.icon(tag="download", size=14, color=Color.ACCENT),
                                        rx.text(
                                            "Unduh template .xlsx",
                                            font_size=FontSize.XS,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.ACCENT,
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    type="button",
                                    on_click=IPState.download_import_template,
                                    style=rx.Style(
                                        {
                                            "padding": "6px 12px",
                                            "background_color": Color.INFO_BG,
                                            "border": f"1px solid {Color.BLUE_BORDER}",
                                            "border_radius": "8px",
                                            "cursor": "pointer",
                                        }
                                    ),
                                ),
                                width="100%",
                                align="center",
                            ),
                            rx.hstack(
                                _col_chip("IP Address", required=True),
                                _col_chip("Nama Server/VM", required=True),
                                _col_chip("Jenis (Fisik/VM)", required=True),
                                _col_chip("Host Server (wajib VM)", required=False),
                                _col_chip("Status", required=False),
                                _col_chip("Fungsi", required=False),
                                _col_chip("OS", required=False),
                                _col_chip("Keterangan", required=False),
                                spacing="2",
                                wrap="wrap",
                                padding_left="32px",
                            ),
                            spacing="2",
                            width="100%",
                            padding="14px",
                            background_color=Color.SLATE_50,
                            border=f"1px solid {Color.BORDER}",
                            border_radius="12px",
                        ),
                        # Langkah 2: Zona Unggah / Pratinjau File
                        rx.vstack(
                            rx.hstack(
                                rx.center(
                                    rx.text(
                                        "2",
                                        font_size="12px",
                                        font_weight=FontWeight.BOLD,
                                        color=Color.WHITE,
                                    ),
                                    width="24px",
                                    height="24px",
                                    border_radius="50%",
                                    background_color=Color.ACCENT,
                                ),
                                rx.text(
                                    "Unggah & validasi data",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.cond(
                                IPState.import_has_preview,
                                # Kondisi 2: Setelah File Dipilih
                                rx.vstack(
                                    # Kartu Nama File + Ganti File
                                    rx.hstack(
                                        rx.hstack(
                                            rx.center(
                                                rx.icon(
                                                    tag="file-spreadsheet",
                                                    size=18,
                                                    color=Color.BLUE_700,
                                                ),
                                                width="36px",
                                                height="36px",
                                                border_radius="8px",
                                                background_color=Color.BLUE_100,
                                            ),
                                            rx.vstack(
                                                rx.text(
                                                    IPState.import_filename,
                                                    font_size=FontSize.SM,
                                                    font_weight=FontWeight.BOLD,
                                                    color=Color.TEXT,
                                                ),
                                                rx.text(
                                                    IPState.import_summary_text,
                                                    font_size=FontSize.XS,
                                                    color=Color.MUTED,
                                                ),
                                                spacing="0",
                                                align="start",
                                            ),
                                            spacing="3",
                                            align="center",
                                        ),
                                        rx.el.button(
                                            "Ganti file",
                                            type="button",
                                            on_click=IPState.clear_import_file,
                                            style=rx.Style(
                                                {
                                                    "padding": "6px 12px",
                                                    "background_color": Color.SURFACE,
                                                    "border": f"1px solid {Color.BORDER}",
                                                    "border_radius": "8px",
                                                    "font_size": FontSize.XS,
                                                    "font_weight": FontWeight.BOLD,
                                                    "color": Color.TEXT,
                                                    "cursor": "pointer",
                                                }
                                            ),
                                        ),
                                        width="100%",
                                        justify="between",
                                        align="center",
                                        padding="10px 14px",
                                        background_color=Color.SLATE_50,
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                    ),
                                    # 3 Kotak Ringkasan: Total, Valid, Error
                                    rx.box(
                                        rx.vstack(
                                            rx.text(
                                                "TOTAL BARIS",
                                                font_size="10px",
                                                font_weight=FontWeight.BOLD,
                                                color=Color.MUTED,
                                            ),
                                            rx.text(
                                                IPState.import_total_count,
                                                font_size="22px",
                                                font_weight=FontWeight.EXTRABOLD,
                                                color=Color.TEXT,
                                            ),
                                            spacing="0",
                                            align="start",
                                            padding="10px 14px",
                                            background_color=Color.SLATE_50,
                                            border=f"1px solid {Color.BORDER}",
                                            border_radius="10px",
                                        ),
                                        rx.vstack(
                                            rx.text(
                                                "VALID",
                                                font_size="10px",
                                                font_weight=FontWeight.BOLD,
                                                color=Color.GREEN_700,
                                            ),
                                            rx.text(
                                                IPState.import_valid_count,
                                                font_size="22px",
                                                font_weight=FontWeight.EXTRABOLD,
                                                color=Color.GREEN_700,
                                            ),
                                            spacing="0",
                                            align="start",
                                            padding="10px 14px",
                                            background_color=Color.GREEN_50,
                                            border=f"1px solid {Color.GREEN_BORDER}",
                                            border_radius="10px",
                                        ),
                                        rx.vstack(
                                            rx.hstack(
                                                rx.text(
                                                    "ERROR",
                                                    font_size="10px",
                                                    font_weight=FontWeight.BOLD,
                                                    color=Color.RED_700,
                                                ),
                                                rx.cond(
                                                    IPState.import_error_count > 0,
                                                    rx.el.button(
                                                        "Unduh laporan error",
                                                        type="button",
                                                        on_click=IPState.download_import_error_report,
                                                        style=rx.Style(
                                                            {
                                                                "font_size": "10px",
                                                                "font_weight": FontWeight.BOLD,
                                                                "color": Color.RED_700,
                                                                "background": "transparent",
                                                                "border": "none",
                                                                "text_decoration": "underline",
                                                                "cursor": "pointer",
                                                                "padding": "0",
                                                            }
                                                        ),
                                                    ),
                                                    rx.fragment(),
                                                ),
                                                width="100%",
                                                justify="between",
                                                align="center",
                                            ),
                                            rx.text(
                                                IPState.import_error_count,
                                                font_size="22px",
                                                font_weight=FontWeight.EXTRABOLD,
                                                color=Color.RED_700,
                                            ),
                                            spacing="0",
                                            align="start",
                                            padding="10px 14px",
                                            background_color=Color.RED_100,
                                            border=f"1px solid {Color.DANGER_BORDER}",
                                            border_radius="10px",
                                        ),
                                        style=rx.Style(
                                            {
                                                "display": "grid",
                                                "grid_template_columns": "repeat(3, 1fr)",
                                                "gap": "10px",
                                                "width": "100%",
                                            }
                                        ),
                                    ),
                                    # Tabel Pratinjau (Error lebih dulu dengan latar merah muda)
                                    rx.box(
                                        rx.table.root(
                                            rx.table.header(
                                                rx.table.row(
                                                    rx.table.column_header_cell("Baris"),
                                                    rx.table.column_header_cell("IP Address"),
                                                    rx.table.column_header_cell("Pengguna"),
                                                    rx.table.column_header_cell("Jenis"),
                                                    rx.table.column_header_cell("Status Validasi"),
                                                )
                                            ),
                                            rx.table.body(
                                                rx.foreach(
                                                    IPState.import_preview_rows,
                                                    lambda r: rx.table.row(
                                                        rx.table.cell(r["row"]),
                                                        rx.table.cell(
                                                            rx.text(
                                                                r["ip_address"],
                                                                font_family="monospace",
                                                                font_weight=FontWeight.BOLD,
                                                            )
                                                        ),
                                                        rx.table.cell(r["pengguna"]),
                                                        rx.table.cell(r["jenis"]),
                                                        rx.table.cell(
                                                            rx.text(
                                                                r["status_label"],
                                                                font_size=FontSize.XS,
                                                                font_weight=FontWeight.BOLD,
                                                                color=rx.cond(
                                                                    r["is_error"],
                                                                    Color.RED_700,
                                                                    Color.GREEN_700,
                                                                ),
                                                            )
                                                        ),
                                                        style=rx.Style(
                                                            {
                                                                "background_color": rx.cond(
                                                                    r["is_error"],
                                                                    Color.ROSE_50,
                                                                    "transparent",
                                                                )
                                                            }
                                                        ),
                                                    ),
                                                )
                                            ),
                                            size="1",
                                            width="100%",
                                        ),
                                        style=rx.Style(
                                            {
                                                "max_height": "190px",
                                                "overflow_y": "auto",
                                                "border": f"1px solid {Color.BORDER}",
                                                "border_radius": "10px",
                                                "width": "100%",
                                            }
                                        ),
                                    ),
                                    spacing="3",
                                    width="100%",
                                ),
                                # Kondisi 1: Zona Unggah
                                rx.upload(
                                    rx.vstack(
                                        rx.center(
                                            rx.icon(
                                                tag="cloud-upload",
                                                size=24,
                                                color=Color.ACCENT,
                                            ),
                                            width="48px",
                                            height="48px",
                                            border_radius="50%",
                                            background_color=Color.BLUE_100,
                                        ),
                                        rx.text(
                                            "Tarik file ke sini atau pilih file",
                                            font_size=FontSize.SM,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                        ),
                                        rx.text(
                                            ".xlsx atau .csv · maks. 5 MB · maks. 1.000 baris",
                                            font_size=FontSize.XS,
                                            color=Color.MUTED,
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    id="ip-import",
                                    multiple=False,
                                    on_drop=IPState.handle_import_upload(
                                        rx.upload_files("ip-import")
                                    ),
                                    style=rx.Style(
                                        {
                                            "width": "100%",
                                            "padding": "28px 20px",
                                            "border": f"2px dashed {Color.BLUE_BORDER}",
                                            "border_radius": "12px",
                                            "background_color": Color.SLATE_50,
                                            "cursor": "pointer",
                                            "transition": "all 0.15s ease",
                                            "_hover": {
                                                "background_color": Color.INFO_BG,
                                                "border_color": Color.ACCENT,
                                            },
                                        }
                                    ),
                                ),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        # Segmented Control Mode Lewati / Perbarui
                        rx.hstack(
                            rx.text(
                                "Jika IP sudah terdaftar:",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.hstack(
                                rx.el.button(
                                    "Lewati duplikat",
                                    type="button",
                                    on_click=IPState.set_import_duplicate_mode("skip"),
                                    style=rx.Style(
                                        {
                                            "padding": "6px 12px",
                                            "border_radius": "7px",
                                            "border": "none",
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "cursor": "pointer",
                                            "background_color": rx.cond(
                                                IPState.import_duplicate_mode == "skip",
                                                Color.WHITE,
                                                "transparent",
                                            ),
                                            "color": rx.cond(
                                                IPState.import_duplicate_mode == "skip",
                                                Color.ACCENT,
                                                Color.MUTED,
                                            ),
                                            "box_shadow": rx.cond(
                                                IPState.import_duplicate_mode == "skip",
                                                "0 1px 3px rgba(0,0,0,0.08)",
                                                "none",
                                            ),
                                        }
                                    ),
                                ),
                                rx.el.button(
                                    "Perbarui data",
                                    type="button",
                                    on_click=IPState.set_import_duplicate_mode("update"),
                                    style=rx.Style(
                                        {
                                            "padding": "6px 12px",
                                            "border_radius": "7px",
                                            "border": "none",
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "cursor": "pointer",
                                            "background_color": rx.cond(
                                                IPState.import_duplicate_mode == "update",
                                                Color.WHITE,
                                                "transparent",
                                            ),
                                            "color": rx.cond(
                                                IPState.import_duplicate_mode == "update",
                                                Color.ACCENT,
                                                Color.MUTED,
                                            ),
                                            "box_shadow": rx.cond(
                                                IPState.import_duplicate_mode == "update",
                                                "0 1px 3px rgba(0,0,0,0.08)",
                                                "none",
                                            ),
                                        }
                                    ),
                                ),
                                spacing="1",
                                padding="3px",
                                background_color=Color.SLATE_100,
                                border_radius="9px",
                                border=f"1px solid {Color.BORDER}",
                            ),
                            width="100%",
                            justify="between",
                            align="center",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    style=rx.Style(
                        {
                            "padding": "20px 24px",
                            "overflow_y": "auto",
                            "max_height": "calc(90vh - 148px)",
                        }
                    ),
                ),
                # Footer
                rx.hstack(
                    rx.el.button(
                        "Batal",
                        type="button",
                        on_click=IPState.close_import_modal,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 18px",
                                "background_color": Color.SURFACE,
                                "border": f"1px solid {Color.BORDER}",
                                "border_radius": "10px",
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "color": Color.TEXT,
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
                        type="button",
                        on_click=IPState.commit_import_data,
                        disabled=(IPState.import_valid_count == 0) | IPState.import_is_processing,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 20px",
                                "background_color": Color.ACCENT,
                                "color": Color.WHITE,
                                "border": "none",
                                "border_radius": "10px",
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "cursor": rx.cond(
                                    (IPState.import_valid_count == 0)
                                    | IPState.import_is_processing,
                                    "not-allowed",
                                    "pointer",
                                ),
                                "opacity": rx.cond(
                                    (IPState.import_valid_count == 0)
                                    | IPState.import_is_processing,
                                    "0.55",
                                    "1",
                                ),
                            }
                        ),
                    ),
                    spacing="3",
                    justify="end",
                    align="center",
                    width="100%",
                    padding="16px 24px",
                    background_color=Color.SLATE_50,
                    style=rx.Style({"border_top": f"1px solid {Color.BORDER}"}),
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "94%",
                        "max_width": "640px",
                        "max_height": "90vh",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": "16px",
                        "box_shadow": Shadow.POPOVER,
                        "display": "flex",
                        "flex_direction": "column",
                        "overflow": "hidden",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _print_col_checkbox(label: str, checked_var: Any, col_key: str) -> rx.Component:
    return rx.hstack(
        rx.el.input(
            type="checkbox",
            checked=checked_var,
            on_change=IPState.toggle_print_col(col_key),
            style=rx.Style({"cursor": "pointer", "accent_color": Color.ACCENT}),
        ),
        rx.text(
            label,
            font_size=FontSize.SM,
            font_weight=FontWeight.MEDIUM,
            color=Color.TEXT,
            cursor="pointer",
            on_click=IPState.toggle_print_col(col_key),
        ),
        spacing="2",
        align="center",
    )


def _ip_print_modal() -> rx.Component:
    """B2: Modal Cetak Data IP (Artboard 6) dengan opsi kolom & pratinjau halaman di sisi kanan."""
    return rx.cond(
        IPState.print_modal_open,
        rx.box(
            rx.box(
                on_click=IPState.close_print_modal,
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
                # Header
                rx.hstack(
                    rx.hstack(
                        rx.center(
                            rx.icon(tag="printer", size=20, color=Color.WHITE),
                            width="42px",
                            height="42px",
                            border_radius="12px",
                            style=rx.Style({"background": Color.GRADIENT_BLUE}),
                        ),
                        rx.vstack(
                            rx.heading(
                                "Cetak Data IP & Server (VM)",
                                font_size="19px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                "Siapkan laporan cetak A4 Landscape atau unduh sebagai PDF.",
                                font_size=FontSize.SM,
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=18, color=Color.MUTED),
                        type="button",
                        on_click=IPState.close_print_modal,
                        style=rx.Style(
                            {
                                "width": "34px",
                                "height": "34px",
                                "border_radius": Radius.CONTROL,
                                "border": f"1px solid {Color.BORDER}",
                                "background_color": Color.SURFACE,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    padding="18px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body 2 Kolom: Pengaturan Kiri & Pratinjau Kanan
                rx.box(
                    # Kiri: Opsi Cetak & Kolom
                    rx.vstack(
                        rx.vstack(
                            rx.text(
                                "UKURAN & ORIENTASI KERTAS",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.05em",
                            ),
                            rx.hstack(
                                rx.icon(tag="file-check", size=16, color=Color.ACCENT),
                                rx.text(
                                    "A4 Landscape (297 × 210 mm)",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                spacing="2",
                                align="center",
                                padding="10px 12px",
                                width="100%",
                                background_color=Color.SLATE_50,
                                border=f"1px solid {Color.BORDER}",
                                border_radius="10px",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text(
                                "CAKUPAN DATA",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.05em",
                            ),
                            rx.hstack(
                                rx.el.input(
                                    type="checkbox",
                                    checked=IPState.print_follow_filter,
                                    on_change=IPState.toggle_print_follow_filter,
                                    style=rx.Style(
                                        {"cursor": "pointer", "accent_color": Color.ACCENT}
                                    ),
                                ),
                                rx.text(
                                    f"Ikuti filter aktif ({IPState.print_total_count} baris)",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.MEDIUM,
                                    color=Color.TEXT,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text(
                                "PILIH KOLOM CETAK",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.05em",
                            ),
                            _print_col_checkbox("IP Address", IPState.print_col_ip, "ip"),
                            _print_col_checkbox("Pengguna", IPState.print_col_pengguna, "pengguna"),
                            _print_col_checkbox(
                                "Jenis (Fisik/VM)", IPState.print_col_jenis, "jenis"
                            ),
                            _print_col_checkbox("Host Server", IPState.print_col_host, "host"),
                            _print_col_checkbox("Kategori", IPState.print_col_kategori, "kategori"),
                            _print_col_checkbox("Fungsi", IPState.print_col_fungsi, "fungsi"),
                            _print_col_checkbox("Operating System", IPState.print_col_os, "os"),
                            _print_col_checkbox("Status", IPState.print_col_status, "status"),
                            _print_col_checkbox(
                                "Keterangan (data internal)",
                                IPState.print_col_keterangan,
                                "keterangan",
                            ),
                            spacing="2",
                            align="start",
                            width="100%",
                        ),
                        spacing="4",
                        align="start",
                        width="260px",
                        flex_shrink="0",
                    ),
                    # Kanan: Pratinjau Halaman A4 Landscape
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                "PRATINJAU HALAMAN CETAK",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.05em",
                            ),
                            rx.text(
                                f"Total: {IPState.print_total_count} baris",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.ACCENT,
                            ),
                            width="100%",
                            justify="between",
                            align="center",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.vstack(
                                    rx.text(
                                        "Daftar IP & Server (VM)",
                                        font_size="14px",
                                        font_weight=FontWeight.EXTRABOLD,
                                        color=Color.TEXT,
                                    ),
                                    rx.text(
                                        f"Subnet: {IPState.active_subnet} · "
                                        f"Filter: {IPState.print_filter_label} · "
                                        f"Dicetak: {IPState.print_date_label}",
                                        font_size="10px",
                                        color=Color.MUTED,
                                    ),
                                    spacing="0",
                                    align="start",
                                ),
                                rx.text(
                                    "ITAM Pro",
                                    font_size="12px",
                                    font_weight=FontWeight.EXTRABOLD,
                                    color=Color.ACCENT,
                                ),
                                width="100%",
                                justify="between",
                                align="start",
                                padding_bottom="8px",
                                margin_bottom="8px",
                                style=rx.Style({"border_bottom": f"2px solid {Color.TEXT}"}),
                            ),
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.cond(
                                            IPState.print_col_ip,
                                            rx.table.column_header_cell("IP Address"),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            IPState.print_col_pengguna,
                                            rx.table.column_header_cell("Pengguna"),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            IPState.print_col_jenis,
                                            rx.table.column_header_cell("Jenis"),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            IPState.print_col_host,
                                            rx.table.column_header_cell("Host"),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            IPState.print_col_fungsi,
                                            rx.table.column_header_cell("Fungsi"),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            IPState.print_col_os,
                                            rx.table.column_header_cell("OS"),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            IPState.print_col_status,
                                            rx.table.column_header_cell("Status"),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            IPState.print_col_keterangan,
                                            rx.table.column_header_cell("Keterangan"),
                                            rx.fragment(),
                                        ),
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        IPState.print_preview_rows,
                                        lambda r: rx.table.row(
                                            rx.cond(
                                                IPState.print_col_ip,
                                                rx.table.cell(
                                                    rx.text(
                                                        r["ip_address"],
                                                        font_family="monospace",
                                                        font_size="11px",
                                                        font_weight=FontWeight.BOLD,
                                                    )
                                                ),
                                                rx.fragment(),
                                            ),
                                            rx.cond(
                                                IPState.print_col_pengguna,
                                                rx.table.cell(
                                                    rx.text(r["pengguna"], font_size="11px")
                                                ),
                                                rx.fragment(),
                                            ),
                                            rx.cond(
                                                IPState.print_col_jenis,
                                                rx.table.cell(
                                                    rx.text(r["jenis"], font_size="11px")
                                                ),
                                                rx.fragment(),
                                            ),
                                            rx.cond(
                                                IPState.print_col_host,
                                                rx.table.cell(
                                                    rx.text(r["host_display"], font_size="11px")
                                                ),
                                                rx.fragment(),
                                            ),
                                            rx.cond(
                                                IPState.print_col_fungsi,
                                                rx.table.cell(
                                                    rx.text(r["fungsi"], font_size="11px")
                                                ),
                                                rx.fragment(),
                                            ),
                                            rx.cond(
                                                IPState.print_col_os,
                                                rx.table.cell(rx.text(r["os"], font_size="11px")),
                                                rx.fragment(),
                                            ),
                                            rx.cond(
                                                IPState.print_col_status,
                                                rx.table.cell(
                                                    rx.text(r["status"], font_size="11px")
                                                ),
                                                rx.fragment(),
                                            ),
                                            rx.cond(
                                                IPState.print_col_keterangan,
                                                rx.table.cell(
                                                    rx.text(r["keterangan"], font_size="11px")
                                                ),
                                                rx.fragment(),
                                            ),
                                        ),
                                    )
                                ),
                                size="1",
                                width="100%",
                            ),
                            padding="16px",
                            background_color=Color.WHITE,
                            border=f"1px solid {Color.BORDER}",
                            border_radius="10px",
                            width="100%",
                            style=rx.Style(
                                {
                                    "max_height": "340px",
                                    "overflow_y": "auto",
                                    "box_shadow": "0 2px 8px rgba(0,0,0,0.04)",
                                }
                            ),
                        ),
                        spacing="2",
                        flex="1",
                        width="100%",
                    ),
                    style=rx.Style(
                        {
                            "display": "flex",
                            "gap": "20px",
                            "padding": "20px 24px",
                            "overflow_y": "auto",
                            "max_height": "calc(90vh - 144px)",
                            "@media (max-width: 768px)": {"flex_direction": "column"},
                        }
                    ),
                ),
                # Footer
                rx.hstack(
                    rx.el.button(
                        "Batal",
                        type="button",
                        on_click=IPState.close_print_modal,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 18px",
                                "background_color": Color.SURFACE,
                                "border": f"1px solid {Color.BORDER}",
                                "border_radius": "10px",
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "color": Color.TEXT,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="download", size=15, color=Color.ACCENT),
                            rx.text(
                                "Unduh PDF",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.ACCENT,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=IPState.download_print_pdf,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 18px",
                                "background_color": Color.INFO_BG,
                                "border": f"1px solid {Color.BLUE_BORDER}",
                                "border_radius": "10px",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="printer", size=15, color=Color.WHITE),
                            rx.text(
                                "Cetak",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.WHITE,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=IPState.execute_direct_print,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 22px",
                                "background_color": Color.ACCENT,
                                "border": "none",
                                "border_radius": "10px",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    spacing="3",
                    justify="end",
                    align="center",
                    width="100%",
                    padding="16px 24px",
                    background_color=Color.SLATE_50,
                    style=rx.Style({"border_top": f"1px solid {Color.BORDER}"}),
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "95%",
                        "max_width": "880px",
                        "max_height": "90vh",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": "16px",
                        "box_shadow": Shadow.POPOVER,
                        "display": "flex",
                        "flex_direction": "column",
                        "overflow": "hidden",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
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
            _ip_import_modal(),
            _ip_print_modal(),
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
