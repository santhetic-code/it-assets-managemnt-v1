"""Halaman Security -> Audit Log (/audit-log), khusus Administrator (append-only)."""

from typing import Any

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    FilterDropdownConfig,
    reusable_data_table,
    table_filter_bar,
    table_pagination,
)
from itam_pro.components.ui.badge import app_badge, connector_chip
from itam_pro.components.ui.detail_drawer import detail_drawer
from itam_pro.components.ui.tabs import TabItemConfig, app_tabs
from itam_pro.states.audit_state import AuditState
from itam_pro.states.auth_state import AuthState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size, Space


def _cell_waktu_wib(row: dict[str, Any]) -> rx.Component:
    return rx.vstack(
        rx.text(
            row["tanggal_wib"],
            font_size=FontSize.SM,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
            white_space="nowrap",
            line_height="1.25",
        ),
        rx.text(
            row["jam_wib"],
            font_size=FontSize.XS,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
            white_space="nowrap",
            line_height="1.2",
        ),
        spacing="0",
        align="start",
    )


def _cell_pelaku(row: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.center(
            rx.text(
                row["actor_initials"],
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.ACCENT,
            ),
            width="30px",
            height="30px",
            border_radius=Radius.FULL,
            background_color=Color.INFO_BG,
            border=f"1px solid {Color.BLUE_BORDER}",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                row["nama_pengguna"],
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
                line_height="1.25",
            ),
            rx.text(
                row["role"],
                font_size=FontSize.XS,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
                line_height="1.2",
            ),
            spacing="0",
            align="start",
        ),
        spacing="2",
        align="center",
    )


def _cell_modul(row: dict[str, Any]) -> rx.Component:
    return connector_chip(row["modul"])


def _cell_aksi(row: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(
            row["aksi_label"],
            font_size=FontSize.SM,
            font_weight=FontWeight.MEDIUM,
            color=Color.TEXT,
        ),
        rx.cond(
            row["group_badge"] != "",
            app_badge(label=row["group_badge"], variant="neutral"),
            rx.fragment(),
        ),
        app_badge(label=row["tingkat"], variant=row["tingkat_variant"]),
        spacing="2",
        align="center",
        wrap="wrap",
    )


AUDIT_COLUMNS: list[ColumnDef] = [
    {
        "key": "waktu_wib",
        "header": "Waktu (WIB)",
        "width": "140px",
        "min_width": "130px",
        "accessor": _cell_waktu_wib,
    },
    {
        "key": "nama_pengguna",
        "header": "Pelaku",
        "width": "200px",
        "min_width": "175px",
        "accessor": _cell_pelaku,
    },
    {
        "key": "modul",
        "header": "Modul",
        "width": "130px",
        "min_width": "115px",
        "accessor": _cell_modul,
    },
    {
        "key": "aksi_label",
        "header": "Aksi",
        "width": "280px",
        "min_width": "230px",
        "accessor": _cell_aksi,
    },
    {
        "key": "target_id",
        "header": "Target",
        "width": "135px",
        "min_width": "115px",
        "render_type": "chip",
    },
    {
        "key": "detail",
        "header": "Ringkasan",
        "width": "280px",
        "min_width": "210px",
        "render_type": "text",
    },
]


def _warning_banner() -> rx.Component:
    return rx.cond(
        AuditState.warning_banner_visible,
        rx.box(
            rx.hstack(
                rx.icon(
                    tag="triangle-alert",
                    size=18,
                    color=Color.DANGER_FG,
                    flex_shrink="0",
                ),
                rx.text(
                    AuditState.warning_banner_summary,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.DANGER_FG,
                ),
                spacing="3",
                align="center",
            ),
            rx.el.button(
                "Tampilkan",
                type="button",
                on_click=AuditState.show_warnings_from_banner,
                style=rx.Style(
                    {
                        "min_height": "44px",
                        "padding": "0 16px",
                        "background_color": Color.SURFACE,
                        "color": Color.DANGER_FG,
                        "border": f"1px solid {Color.DANGER_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
                _hover=rx.Style({"background_color": Color.DANGER_BG}),
            ),
            role="alert",
            style=rx.Style(
                {
                    "width": "100%",
                    "padding": "10px 16px",
                    "background_color": Color.RED_50,
                    "border": f"1px solid {Color.DANGER_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "display": "flex",
                    "align_items": "center",
                    "justify_content": "space-between",
                    "flex_wrap": "wrap",
                    "gap": Space.S3,
                }
            ),
        ),
        rx.fragment(),
    )


def _extra_filter_controls() -> rx.Component:
    date_input_style = rx.Style(
        {
            "height": Size.FILTER_CONTROL_H,
            "min_height": "44px",
            "padding": "0 10px",
            "background_color": Color.SURFACE,
            "color": Color.TEXT,
            "border": f"1px solid {Color.INPUT_BORDER}",
            "border_radius": Radius.CONTROL,
            "font_family": FONT_FAMILY,
            "font_size": FontSize.SM,
        }
    )
    return rx.hstack(
        rx.cond(
            AuditState.is_custom_date_range,
            rx.hstack(
                rx.el.input(
                    type="date",
                    aria_label="Tanggal mulai",
                    value=AuditState.date_from,
                    on_change=AuditState.set_date_from,
                    style=date_input_style,
                ),
                rx.text("–", color=Color.MUTED, font_size=FontSize.SM),
                rx.el.input(
                    type="date",
                    aria_label="Tanggal selesai",
                    value=AuditState.date_to,
                    on_change=AuditState.set_date_to,
                    style=date_input_style,
                ),
                spacing="2",
                align="center",
            ),
            rx.fragment(),
        ),
        rx.el.label(
            rx.hstack(
                rx.el.input(
                    type="checkbox",
                    checked=AuditState.hide_login_success,
                    on_change=AuditState.toggle_hide_login_success,
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
                    "Sembunyikan login berhasil",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.MEDIUM,
                    color=Color.TEXT,
                    white_space="nowrap",
                ),
                spacing="2",
                align="center",
            ),
            style=rx.Style(
                {
                    "min_height": "44px",
                    "padding": "0 8px",
                    "display": "inline-flex",
                    "align_items": "center",
                    "cursor": "pointer",
                }
            ),
        ),
        spacing="2",
        align="center",
        wrap="wrap",
    )


def _drawer_info_row(label: str, content: rx.Component) -> rx.Component:
    return rx.hstack(
        rx.text(
            label,
            font_size=FontSize.SM,
            color=Color.MUTED,
            style=rx.Style({"width": "34%", "flex_shrink": "0"}),
        ),
        rx.box(content, style=rx.Style({"width": "66%"})),
        width="100%",
        align="center",
        padding_y="6px",
    )


def _audit_detail_drawer() -> rx.Component:
    custom_header = rx.vstack(
        rx.hstack(
            rx.text(
                AuditState.selected_kode_audit,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.ACCENT,
                letter_spacing="0.04em",
            ),
            rx.el.button(
                rx.icon(tag="x", size=18, color=Color.MUTED),
                id="drawer-close-btn",
                type="button",
                aria_label="Tutup panel detail kejadian",
                on_click=AuditState.close_detail_drawer,
                style=rx.Style(
                    {
                        "min_width": "44px",
                        "min_height": "44px",
                        "border_radius": Radius.CONTROL,
                        "border": f"1px solid {Color.BORDER}",
                        "background_color": Color.SURFACE,
                        "display": "inline-flex",
                        "align_items": "center",
                        "justify_content": "center",
                        "cursor": "pointer",
                    }
                ),
                _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
            ),
            width="100%",
            justify="between",
            align="center",
        ),
        rx.heading(
            AuditState.selected_aksi_label,
            font_size=FontSize.LOGO,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.TEXT,
            line_height="1.25",
        ),
        rx.text(
            AuditState.selected_waktu_lengkap,
            font_size=FontSize.SM,
            color=Color.MUTED,
        ),
        rx.hstack(
            app_badge(
                label=AuditState.selected_tingkat,
                variant=AuditState.selected_tingkat_variant,
            ),
            app_badge(
                label=AuditState.selected_hasil,
                variant=AuditState.selected_hasil_variant,
            ),
            spacing="2",
            align="center",
            padding_top="4px",
        ),
        spacing="1",
        align="start",
        width="100%",
        padding="20px 24px 16px 24px",
        style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
    )

    target_cell = rx.hstack(
        connector_chip(AuditState.selected_target_id),
        rx.cond(
            AuthState.is_admin & (AuditState.selected_target_url != ""),
            rx.link(
                AuditState.selected_target_link_label,
                href=AuditState.selected_target_url,
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.ACCENT,
                underline="hover",
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
        wrap="wrap",
    )

    changes_table = rx.cond(
        AuditState.has_selected_changes,
        rx.vstack(
            rx.text(
                "PERUBAHAN",
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            rx.box(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th(
                                "FIELD",
                                style=rx.Style(
                                    {
                                        "padding": "10px 12px",
                                        "text_align": "left",
                                        "font_size": FontSize.XS,
                                        "color": Color.MUTED,
                                        "background_color": Color.TABLE_HEADER_BG,
                                        "border_bottom": f"1px solid {Color.BORDER}",
                                    }
                                ),
                            ),
                            rx.el.th(
                                "SEBELUM",
                                style=rx.Style(
                                    {
                                        "padding": "10px 12px",
                                        "text_align": "left",
                                        "font_size": FontSize.XS,
                                        "color": Color.MUTED,
                                        "background_color": Color.TABLE_HEADER_BG,
                                        "border_bottom": f"1px solid {Color.BORDER}",
                                    }
                                ),
                            ),
                            rx.el.th(
                                "SESUDAH",
                                style=rx.Style(
                                    {
                                        "padding": "10px 12px",
                                        "text_align": "left",
                                        "font_size": FontSize.XS,
                                        "color": Color.MUTED,
                                        "background_color": Color.TABLE_HEADER_BG,
                                        "border_bottom": f"1px solid {Color.BORDER}",
                                    }
                                ),
                            ),
                        )
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            AuditState.selected_changes,
                            lambda ch: rx.el.tr(
                                rx.el.td(
                                    ch["field"],
                                    style=rx.Style(
                                        {
                                            "padding": "10px 12px",
                                            "font_size": FontSize.SM,
                                            "font_weight": FontWeight.BOLD,
                                            "color": Color.TEXT,
                                            "border_bottom": f"1px solid {Color.DIVIDER}",
                                        }
                                    ),
                                ),
                                rx.el.td(
                                    ch["before"],
                                    style=rx.Style(
                                        {
                                            "padding": "10px 12px",
                                            "font_size": FontSize.SM,
                                            "color": Color.MUTED,
                                            "border_bottom": f"1px solid {Color.DIVIDER}",
                                        }
                                    ),
                                ),
                                rx.el.td(
                                    ch["after"],
                                    style=rx.Style(
                                        {
                                            "padding": "10px 12px",
                                            "font_size": FontSize.SM,
                                            "font_weight": FontWeight.BOLD,
                                            "color": Color.TEXT,
                                            "border_bottom": f"1px solid {Color.DIVIDER}",
                                        }
                                    ),
                                ),
                            ),
                        )
                    ),
                    style=rx.Style({"width": "100%", "border_collapse": "collapse"}),
                ),
                style=rx.Style(
                    {
                        "width": "100%",
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CONTROL,
                        "overflow": "hidden",
                    }
                ),
            ),
            rx.text(
                "Untuk kejadian Kredensial, nilai rahasia tidak pernah disimpan atau "
                "ditampilkan; hanya nama field yang dicatat.",
                font_size=FontSize.XS,
                color=Color.MUTED,
                line_height="1.45",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.fragment(),
    )

    grouped_times_block = rx.cond(
        AuditState.is_selected_grouped,
        rx.vstack(
            rx.text(
                "SEMUA WAKTU KEJADIAN DALAM GRUP (60 DETIK)",
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            rx.vstack(
                rx.foreach(
                    AuditState.selected_grouped_timestamps,
                    lambda ts: rx.hstack(
                        rx.text(
                            ts["kode_audit"],
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.ACCENT,
                        ),
                        rx.text(
                            ts["waktu_lengkap"],
                            font_size=FontSize.XS,
                            color=Color.TEXT,
                        ),
                        width="100%",
                        justify="between",
                        align="center",
                        padding="6px 10px",
                        style=rx.Style(
                            {
                                "border_bottom": f"1px solid {Color.DIVIDER}",
                            }
                        ),
                    ),
                ),
                spacing="0",
                width="100%",
                style=rx.Style(
                    {
                        "background_color": Color.TABLE_HEADER_BG,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CONTROL,
                    }
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.fragment(),
    )

    custom_body = rx.vstack(
        rx.vstack(
            rx.text(
                "SIAPA DAN DI MANA",
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            _drawer_info_row(
                "Pelaku",
                rx.text(
                    AuditState.selected_actor_display,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
            ),
            _drawer_info_row(
                "Peran",
                rx.text(
                    AuditState.selected_role,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
            ),
            _drawer_info_row(
                "Modul",
                rx.text(
                    AuditState.selected_modul,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
            ),
            _drawer_info_row("Target", target_cell),
            _drawer_info_row(
                "Alamat IP",
                rx.text(
                    AuditState.selected_ip_address,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                    font_family="monospace",
                ),
            ),
            _drawer_info_row(
                "Perangkat",
                rx.text(
                    AuditState.selected_perangkat,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
            ),
            _drawer_info_row(
                "Ringkasan",
                rx.text(
                    AuditState.selected_detail,
                    font_size=FontSize.SM,
                    color=Color.TEXT,
                    line_height="1.4",
                ),
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        grouped_times_block,
        changes_table,
        spacing="5",
        align="start",
        width="100%",
    )

    custom_footer = rx.hstack(
        rx.el.button(
            "Salin ID kejadian",
            type="button",
            on_click=AuditState.copy_selected_event_id,
            style=rx.Style(
                {
                    "min_height": "44px",
                    "padding": "0 16px",
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
            _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
        ),
        rx.text(
            "Log hanya-baca",
            font_size=FontSize.XS,
            font_weight=FontWeight.MEDIUM,
            color=Color.MUTED,
        ),
        width="100%",
        justify="between",
        align="center",
        padding="14px 24px",
        style=rx.Style(
            {
                "border_top": f"1px solid {Color.BORDER}",
                "background_color": Color.SURFACE,
            }
        ),
    )

    return detail_drawer(
        is_open=AuditState.drawer_open,
        on_close=AuditState.close_detail_drawer,
        custom_header=custom_header,
        custom_body=custom_body,
        custom_footer=custom_footer,
        show_tabs=False,
        aria_label="Detail kejadian Audit Log",
    )


def audit_view_page() -> rx.Component:
    severity_tabs: list[TabItemConfig] = [
        {"key": "Semua", "label": "Semua", "count": AuditState.tab_counts["Semua"]},
        {"key": "Peringatan", "label": "Peringatan", "count": AuditState.tab_counts["Peringatan"]},
        {"key": "Penting", "label": "Penting", "count": AuditState.tab_counts["Penting"]},
        {"key": "Info", "label": "Info", "count": AuditState.tab_counts["Info"]},
    ]

    dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua modul",
            "value": AuditState.module_filter,
            "options": AuditState.module_options,
            "on_change": AuditState.set_module_filter,
        },
        {
            "label": "Semua pelaku",
            "value": AuditState.actor_filter,
            "options": AuditState.actor_options,
            "on_change": AuditState.set_actor_filter,
        },
        {
            "label": "Semua periode",
            "value": AuditState.period_filter,
            "options": AuditState.period_options,
            "on_change": AuditState.set_period_filter,
        },
    ]

    header_row = rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "Audit Log",
                    font_size=FontSize.TITLE,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                    line_height="1.2",
                ),
                app_badge(label="Hanya Administrator", variant="neutral"),
                spacing="3",
                align="center",
                wrap="wrap",
            ),
            rx.text(
                "Rekam jejak perubahan data, autentikasi, dan akses kredensial. "
                "Hanya-baca: tidak dapat diubah atau dihapus.",
                font_size=FontSize.BASE,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
        ),
        rx.el.button(
            rx.hstack(
                rx.icon(tag="download", size=15, color=Color.TEXT),
                rx.text(
                    "Export CSV",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
                spacing="2",
                align="center",
            ),
            type="button",
            on_click=AuditState.export_csv,
            style=rx.Style(
                {
                    "min_height": "44px",
                    "padding": "0 16px",
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "cursor": "pointer",
                    "display": "inline-flex",
                    "align_items": "center",
                    "white_space": "nowrap",
                }
            ),
            _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "flex",
                "align_items": "flex-start",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S4,
            }
        ),
    )

    content = rx.vstack(
        header_row,
        _warning_banner(),
        rx.box(
            app_tabs(
                tabs=severity_tabs,
                active_tab=AuditState.severity_tab,
                on_change=AuditState.set_severity_tab,
            ),
            table_filter_bar(
                search_value=AuditState.search_query,
                on_search_change=AuditState.set_search_query,
                search_placeholder="Cari pelaku, aksi, target, ringkasan...",
                dropdowns=dropdowns,
                extra_controls=_extra_filter_controls(),
                on_reset=AuditState.reset_filters,
                result_count_text=AuditState.result_count_label,
            ),
            reusable_data_table(
                columns=AUDIT_COLUMNS,
                rows=AuditState.logs,
                id_key="kode_audit",
                active_row_id=AuditState.active_row_id,
                is_loading=AuditState.is_loading,
                on_row_click=AuditState.open_detail_drawer,
                danger_row_key="tingkat",
                danger_row_value="Peringatan",
                show_action_header=False,
                empty_message="Tidak ada kejadian audit yang cocok",
                on_empty_action=AuditState.reset_filters,
            ),
            table_pagination(
                summary_text=AuditState.pagination_summary,
                current_page=AuditState.page,
                current_page_str=AuditState.current_page_str,
                total_pages=AuditState.total_pages,
                page_tokens=AuditState.page_tokens,
                on_prev=AuditState.prev_page,
                on_next=AuditState.next_page,
                on_page_select=AuditState.select_page,
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                    "overflow": "hidden",
                }
            ),
        ),
        rx.text(
            "Waktu ditampilkan dalam WIB (disimpan UTC). Kejadian yang sama dalam 1 menit "
            "digabung (×N); data mentah tetap tersimpan satu per satu.",
            font_size=FontSize.XS,
            color=Color.MUTED,
        ),
        _audit_detail_drawer(),
        spacing="4",
        width="100%",
    )
    return base_layout(content=content, breadcrumb=("Security", "Audit Log"))


__all__ = ["audit_view_page"]
