"""
Halaman View Rekap Pembelian & Invoice ITAM Pro (Tahap 9).
"""
import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables.data_table import reusable_data_table
from itam_pro.components.tables.filter_bar import FilterDropdownConfig, table_filter_bar
from itam_pro.components.tables.pagination import table_pagination
from itam_pro.components.ui.stat_card import stat_card
from itam_pro.components.ui.tabs import app_tabs
from itam_pro.states.finance_state import FinanceState
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


def _kpi_cards() -> rx.Component:
    """Kartu Metrik Finansial."""
    return rx.grid(
        stat_card(
            "Total Belanja (Filtered)",
            FinanceState.total_belanja_display,
            "shopping-cart",
        ),
        stat_card(
            "Belanja Terbesar",
            FinanceState.belanja_terbesar_display,
            "trending-up",
        ),
        stat_card(
            "Belum Dicatat",
            FinanceState.belum_dicatat_count,
            "circle-alert",
            tone="warning",
        ),
        columns="3",
        spacing="4",
        width="100%",
        margin_bottom=Space.S6,
    )


def _total_summary_footer() -> rx.Component:
    """Banner Total Harga yang mengikuti seluruh hasil filter, dirender di bawah tabel."""
    return rx.hstack(
        rx.text("Total Keseluruhan:", font_weight=FontWeight.BOLD, color=Color.TEXT),
        rx.text(
            FinanceState.total_belanja_display,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.ACCENT_BRIGHT,
            font_size=FontSize.BASE,
        ),
        width="100%",
        justify="end",
        align="center",
        padding="12px 20px",
        background_color=Color.TABLE_HEADER_BG,
        border_bottom_left_radius=Radius.CARD,
        border_bottom_right_radius=Radius.CARD,
        border=f"1px solid {Color.BORDER}",
        border_top="none",
    )


def _jadikan_aset_dialog() -> rx.Component:
    """Modal Dialog untuk otomatisasi konversi data pembelian menjadi aset fisik."""
    return rx.cond(
        FinanceState.is_asset_modal_open,
        rx.box(
            # Backdrop Overlay
            rx.box(
                on_click=FinanceState.close_asset_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            # Modal Content Box
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.center(
                            rx.icon(tag="package-plus", size=20, color=Color.ACCENT_BRIGHT),
                            width="36px",
                            height="36px",
                            background_color=Color.INFO_BG,
                            border_radius=Radius.CHIP,
                            flex_shrink="0",
                        ),
                        rx.vstack(
                            rx.heading(
                                "Jadikan Aset Fisik",
                                font_size=FontSize.SUBTITLE,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                FinanceState.selected_purchase_title,
                                font_size=FontSize.SM,
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                            type="button",
                            on_click=FinanceState.close_asset_modal,
                            style=rx.Style(
                                {
                                    "width": "32px",
                                    "height": "32px",
                                    "background": "transparent",
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "display": "inline-flex",
                                    "align_items": "center",
                                    "justify_content": "center",
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    # Form Input: Kategori & Lokasi
                    rx.vstack(
                        rx.text(
                            "Kategori Aset",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.TEXT,
                        ),
                        rx.el.select(
                            rx.foreach(
                                FinanceState.kategori_options,
                                lambda opt: rx.el.option(opt, value=opt),
                            ),
                            value=FinanceState.asset_form_kategori,
                            on_change=FinanceState.set_asset_form_kategori,
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": Size.FILTER_CONTROL_H,
                                    "padding": "0 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "background_color": Color.SURFACE,
                                    "color": Color.TEXT,
                                    "font_family": FONT_FAMILY,
                                }
                            ),
                        ),
                        rx.text(
                            "Lokasi Penempatan",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.TEXT,
                        ),
                        rx.el.select(
                            rx.foreach(
                                FinanceState.lokasi_options,
                                lambda opt: rx.el.option(opt, value=opt),
                            ),
                            value=FinanceState.asset_form_lokasi,
                            on_change=FinanceState.set_asset_form_lokasi,
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": Size.FILTER_CONTROL_H,
                                    "padding": "0 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "background_color": Color.SURFACE,
                                    "color": Color.TEXT,
                                    "font_family": FONT_FAMILY,
                                }
                            ),
                        ),
                        rx.box(
                            rx.text(
                                "Aset akan otomatis dibuat dengan status 'Tidak Digunakan' "
                                "dan kondisi 'Baru' sebanyak jumlah Pcs pada pembelian.",
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                            ),
                            padding="10px 12px",
                            background_color=Color.TABLE_HEADER_BG,
                            border_radius=Radius.CONTROL,
                            border=f"1px solid {Color.BORDER}",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                        margin_top="16px",
                        margin_bottom="16px",
                    ),
                    # Tombol Aksi Dialog
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=FinanceState.close_asset_modal,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 16px",
                                    "background": "transparent",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.SEMIBOLD,
                                    "color": Color.TEXT,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Simpan & Buat Aset",
                            type="button",
                            on_click=FinanceState.submit_jadikan_aset,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 20px",
                                    "background_color": Color.ACCENT,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.WHITE,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        width="100%",
                        justify="end",
                        spacing="3",
                    ),
                    width="100%",
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "90%",
                        "max_width": "460px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _pagination() -> rx.Component:
    return table_pagination(
        summary_text=FinanceState.summary_text,
        current_page=FinanceState.page,
        current_page_str=FinanceState.current_page_str,
        total_pages=FinanceState.total_pages,
        page_tokens=FinanceState.page_tokens,
        on_prev=FinanceState.go_to_previous_page,
        on_next=FinanceState.go_to_next_page,
        on_page_select=FinanceState.select_page,
        page=FinanceState.page,
        total_items=FinanceState.total_items,
        page_size=FinanceState.page_size,
    )


def _table_card(*children: rx.Component) -> rx.Component:
    return rx.box(
        *children,
        width="100%",
        border=f"1px solid {Color.BORDER}",
        border_radius=Radius.CARD,
        background_color=Color.SURFACE,
    )


def _invoice_tab() -> rx.Component:
    """Tab 2: arsip bukti pembayaran (Invoice)."""
    link_dropdown: FilterDropdownConfig = {
        "label": "Semua status tautan",
        "value": FinanceState.invoice_link_filter,
        "options": FinanceState.invoice_link_options,
        "on_change": FinanceState.set_invoice_link_filter,
    }
    return rx.vstack(
        rx.grid(
            stat_card("Total Invoice", FinanceState.invoices_summary["total_invoice"], "file-text"),
            stat_card(
                "Sudah ditautkan", FinanceState.invoices_summary["sudah_ditautkan"], "link"
            ),
            stat_card(
                "Belum ditautkan",
                FinanceState.invoices_summary["belum_ditautkan"],
                "link-2-off",
                tone="warning",
            ),
            stat_card(
                "Pembelian tanpa bukti",
                FinanceState.invoices_summary["tanpa_bukti"],
                "circle-alert",
                tone="danger",
            ),
            columns="4",
            spacing="4",
            width="100%",
            margin_bottom=Space.S6,
        ),
        _table_card(
            table_filter_bar(
                search_value=FinanceState.search_query,
                on_search_change=FinanceState.set_search_query,
                search_placeholder="Cari no. invoice, vendor, atau tautan...",
                dropdowns=[link_dropdown],
                on_reset=FinanceState.reset_filters,
                result_count_text=FinanceState.result_count_label,
            ),
            reusable_data_table(
                items=FinanceState.invoices,
                id_key="no_invoice",
                columns=[
                    {
                        "header": "No. Invoice",
                        "accessor": "no_invoice",
                        "render_type": "bold",
                        "width": "220px",
                    },
                    {
                        "header": "Tanggal",
                        "accessor": "tanggal",
                        "render_type": "date",
                        "width": "110px",
                    },
                    {"header": "Vendor", "accessor": "vendor", "width": "190px"},
                    {"header": "Total", "accessor": "total_display", "width": "130px"},
                    {"header": "Berkas", "accessor": "berkas", "width": "120px"},
                    {"header": "Terkait", "accessor": "terkait_label", "width": "280px"},
                ],
                empty_message="Tidak ada invoice yang cocok",
                on_empty_action=FinanceState.reset_filters,
            ),
            _pagination(),
        ),
        spacing="4",
        width="100%",
    )


def _bills_tab() -> rx.Component:
    """Tab 3: Tagihan Berulang (siklus langganan & pengingat)."""
    status_dropdown: FilterDropdownConfig = {
        "label": "Semua status",
        "value": FinanceState.bill_status_filter,
        "options": FinanceState.bill_status_options,
        "on_change": FinanceState.set_bill_status_filter,
    }
    return rx.vstack(
        rx.grid(
            stat_card(
                "Terlambat",
                FinanceState.bills_summary["terlambat"],
                "triangle-alert",
                tone="danger",
            ),
            stat_card(
                "Segera dibayar",
                FinanceState.bills_summary["segera"],
                "clock",
                tone="warning",
            ),
            stat_card(
                "Tagihan aktif", FinanceState.bills_summary["tagihan_aktif"], "circle-check"
            ),
            stat_card(
                "Perlu dibayar ≤ 30 hari",
                FinanceState.bills_perlu_dibayar_display,
                "wallet",
            ),
            columns="4",
            spacing="4",
            width="100%",
            margin_bottom=Space.S6,
        ),
        _table_card(
            table_filter_bar(
                search_value=FinanceState.search_query,
                on_search_change=FinanceState.set_search_query,
                search_placeholder="Cari tagihan atau vendor...",
                dropdowns=[status_dropdown],
                on_reset=FinanceState.reset_filters,
                result_count_text=FinanceState.result_count_label,
            ),
            reusable_data_table(
                items=FinanceState.bills,
                id_key="id",
                columns=[
                    {
                        "header": "Tagihan",
                        "accessor": "nama",
                        "render_type": "bold",
                        "width": "240px",
                    },
                    {"header": "Vendor", "accessor": "vendor", "width": "140px"},
                    {"header": "Kategori", "accessor": "kategori", "width": "110px"},
                    {"header": "Periode", "accessor": "periode", "width": "100px"},
                    {"header": "Nominal", "accessor": "nominal_display", "width": "120px"},
                    {
                        "header": "Jatuh Tempo",
                        "accessor": "jatuh_tempo",
                        "render_type": "name_with_sub",
                        "sub_key": "status_label",
                        "width": "150px",
                    },
                    {
                        "header": "Pengingat",
                        "accessor": "pengingat_display",
                        "width": "140px",
                    },
                    {"header": "Pembayar", "accessor": "pembayar", "width": "100px"},
                    {
                        "header": "Status",
                        "accessor": "status",
                        "render_type": "badge",
                        "badge_variant_key": "status_variant",
                        "width": "110px",
                    },
                ],
                on_duplicate_row=FinanceState.open_pay_bill_modal,
                duplicate_action_label="Tandai Dibayar",
                empty_message="Tidak ada tagihan yang cocok",
                on_empty_action=FinanceState.reset_filters,
            ),
            _pagination(),
        ),
        spacing="4",
        width="100%",
    )


def _modal_input_style() -> rx.Style:
    return rx.Style(
        {
            "width": "100%",
            "height": Size.FILTER_CONTROL_H,
            "padding": "0 12px",
            "border": f"1px solid {Color.INPUT_BORDER}",
            "border_radius": Radius.CONTROL,
            "background_color": Color.SURFACE,
            "color": Color.TEXT,
            "font_family": FONT_FAMILY,
        }
    )


def _pay_bill_dialog() -> rx.Component:
    """Modal 'Tandai Dibayar': simpan riwayat & geser jatuh tempo otomatis."""
    return rx.cond(
        FinanceState.is_pay_modal_open,
        rx.box(
            rx.box(
                on_click=FinanceState.close_pay_modal,
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
                        "Tandai Dibayar",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        FinanceState.pay_bill_title,
                        font_size=FontSize.SM,
                        color=Color.MUTED,
                    ),
                    rx.cond(
                        FinanceState.pay_error != "",
                        rx.text(
                            FinanceState.pay_error,
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.DANGER_FG,
                        ),
                    ),
                    rx.text(
                        "Tanggal Bayar",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.input(
                        type="date",
                        value=FinanceState.pay_date,
                        on_change=FinanceState.set_pay_date,
                        style=_modal_input_style(),
                    ),
                    rx.text(
                        "Nominal Dibayar (Rp)",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.input(
                        type="text",
                        value=FinanceState.pay_nominal,
                        on_change=FinanceState.set_pay_nominal,
                        style=_modal_input_style(),
                    ),
                    rx.text(
                        "Jatuh tempo akan digeser otomatis sesuai periode tagihan.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=FinanceState.close_pay_modal,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 16px",
                                    "background": "transparent",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.SEMIBOLD,
                                    "color": Color.TEXT,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Simpan Pembayaran",
                            type="button",
                            on_click=FinanceState.submit_pay_bill,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 20px",
                                    "background_color": Color.ACCENT,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.WHITE,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        width="100%",
                        justify="end",
                        spacing="3",
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "90%",
                        "max_width": "460px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def purchases_view_page() -> rx.Component:
    """Pusat pengeluaran IT: Rekap Pembelian, Invoice, Tagihan Berulang."""
    status_dropdown: FilterDropdownConfig = {
        "label": "Semua status aset",
        "value": FinanceState.status_filter,
        "options": FinanceState.status_options,
        "on_change": FinanceState.set_status_filter,
    }

    return base_layout(
        rx.vstack(
            app_tabs(
                items=[
                    {"label": "Rekap Pembelian", "value": "pembelian"},
                    {"label": "Invoice", "value": "invoice"},
                    {"label": "Tagihan Berulang", "value": "tagihan"},
                ],
                active_value=FinanceState.active_tab,
                on_change=FinanceState.set_tab,
            ),
            rx.match(
                FinanceState.active_tab,
                ("invoice", _invoice_tab()),
                ("tagihan", _bills_tab()),
                rx.vstack(
                    _kpi_cards(),
                    rx.box(
                        table_filter_bar(
                            search_value=FinanceState.search_query,
                            on_search_change=FinanceState.set_search_query,
                            search_placeholder="Cari produk, toko, atau pembeli...",
                            dropdowns=[status_dropdown],
                            on_reset=FinanceState.reset_filters,
                            result_count_text=FinanceState.result_count_label,
                        ),
                        reusable_data_table(
                            items=FinanceState.purchases,
                            id_key="id_pembelian",
                            columns=[
                                {"header": "No", "accessor": "no", "width": "50px"},
                                {
                                    "header": "Tanggal",
                                    "accessor": "tanggal",
                                    "render_type": "date",
                                    "width": "110px",
                                },
                                {
                                    "header": "Produk",
                                    "accessor": "produk",
                                    "render_type": "bold",
                                    "width": "240px",
                                },
                                {
                                    "header": "Harga Satuan",
                                    "accessor": "harga",
                                    "width": "120px",
                                },
                                {"header": "Pcs", "accessor": "pcs", "width": "60px"},
                                {"header": "Total", "accessor": "total", "width": "130px"},
                                {
                                    "header": "Marketplace",
                                    "accessor": "domain_chip",
                                    "width": "120px",
                                },
                                {
                                    "header": "Status Aset",
                                    "accessor": "aset_status",
                                    "width": "140px",
                                },
                            ],
                            on_row_click=FinanceState.open_jadikan_aset_modal,
                            on_edit_row=FinanceState.open_jadikan_aset_modal,
                            on_duplicate_row=FinanceState.open_jadikan_aset_modal,
                            duplicate_action_label="Jadikan Aset",
                            show_action_header=True,
                        ),
                        _total_summary_footer(),
                        table_pagination(
                            summary_text=FinanceState.summary_text,
                            current_page=FinanceState.page,
                            current_page_str=FinanceState.current_page_str,
                            total_pages=FinanceState.total_pages,
                            page_tokens=FinanceState.page_tokens,
                            on_prev=FinanceState.go_to_previous_page,
                            on_next=FinanceState.go_to_next_page,
                            on_page_select=FinanceState.select_page,
                            page=FinanceState.page,
                            total_items=FinanceState.total_items,
                            page_size=FinanceState.page_size,
                        ),
                        _jadikan_aset_dialog(),
                        width="100%",
                        border=f"1px solid {Color.BORDER}",
                        border_radius=Radius.CARD,
                        background_color=Color.SURFACE,
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
            _pay_bill_dialog(),
            spacing="5",
            width="100%",
        )
    )


__all__ = ["purchases_view_page"]
