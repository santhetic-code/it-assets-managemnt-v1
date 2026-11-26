"""
Halaman View Rekap Pembelian & Invoice ITAM Pro (Tahap 9).
"""

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables.data_table import reusable_data_table
from itam_pro.components.tables.filter_bar import FilterDropdownConfig, table_filter_bar
from itam_pro.components.tables.pagination import table_pagination
from itam_pro.components.ui.button import action_primary_button, secondary_button
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
    """4 Kartu Metrik Finansial Rekap Pembelian (kartu pertama Color.BRAND)."""
    return rx.grid(
        stat_card(
            "TOTAL BELANJA (FILTER AKTIF)",
            FinanceState.total_belanja_display,
            note=FinanceState.filtered_purchases_note,
            primary=True,
        ),
        stat_card(
            "BELANJA TERBESAR",
            FinanceState.belanja_terbesar_display,
            note="satu transaksi",
        ),
        stat_card(
            "BELUM DIDAFTARKAN SEBAGAI ASET",
            FinanceState.belum_dicatat_count,
            value_tone="warning",
            note=FinanceState.belum_dicatat_note,
        ),
        stat_card(
            "TAGIHAN BERULANG TERDEKAT",
            FinanceState.nearest_bill_name,
            note=FinanceState.nearest_bill_note,
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="4"),
        spacing="4",
        width="100%",
    )


def _column_chooser_menu() -> rx.Component:
    """Popover 'Atur kolom' untuk kolom opsional (Link Marketplace & Dibeli Oleh)."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.el.button(
                rx.hstack(
                    rx.icon(tag="sliders-horizontal", size=14, color=Color.TEXT),
                    rx.text(
                        "Atur kolom",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
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
                        "color": Color.TEXT,
                        "border": f"1px solid {Color.INPUT_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
            )
        ),
        rx.menu.content(
            rx.menu.item(
                rx.hstack(
                    rx.el.input(
                        type="checkbox",
                        checked=FinanceState.is_link_col_visible,
                        read_only=True,
                    ),
                    rx.text("Link Marketplace", font_size=FontSize.SM),
                    spacing="2",
                    align="center",
                ),
                on_click=FinanceState.toggle_column_visibility("link_marketplace"),
            ),
            rx.menu.item(
                rx.hstack(
                    rx.el.input(
                        type="checkbox",
                        checked=FinanceState.is_buyer_col_visible,
                        read_only=True,
                    ),
                    rx.text("Dibeli Oleh", font_size=FontSize.SM),
                    spacing="2",
                    align="center",
                ),
                on_click=FinanceState.toggle_column_visibility("dibeli_oleh"),
            ),
            align="end",
        ),
    )


def _purchases_toolbar_actions() -> rx.Component:
    """Tombol kanan toolbar: Atur kolom, Import, Export, + Catat Pembelian."""
    return rx.hstack(
        _column_chooser_menu(),
        secondary_button("Import", on_click=FinanceState.open_import_modal),
        secondary_button("Export", on_click=FinanceState.export_purchases_csv),
        action_primary_button(
            "+ Catat Pembelian", on_click=FinanceState.open_add_purchase_modal
        ),
        spacing="2",
        align="center",
        wrap="wrap",
    )


def _bulk_selection_bar() -> rx.Component:
    """Bar biru seleksi massal: 'N pembelian dipilih' + 'Daftarkan sebagai aset'."""
    return rx.cond(
        FinanceState.has_selected_purchases,
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.text(
                        FinanceState.selected_purchases_label,
                        font_size=FontSize.SM,
                        font_weight=FontWeight.BOLD,
                        color=Color.ACCENT,
                    ),
                    rx.el.button(
                        "Batal",
                        type="button",
                        on_click=FinanceState.clear_purchase_selection,
                        style=rx.Style(
                            {
                                "background": "transparent",
                                "border": "none",
                                "color": Color.MUTED,
                                "font_size": FontSize.XS,
                                "font_weight": FontWeight.SEMIBOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    spacing="3",
                    align="center",
                ),
                action_primary_button(
                    "Daftarkan sebagai aset",
                    on_click=FinanceState.open_bulk_asset_modal,
                ),
                width="100%",
                justify="between",
                align="center",
                wrap="wrap",
                spacing="3",
            ),
            padding="10px 16px",
            margin_x="16px",
            margin_bottom="12px",
            style=rx.Style(
                {
                    "background_color": Color.INFO_BG,
                    "border": f"1px solid {Color.BLUE_BORDER}",
                    "border_radius": Radius.CONTROL,
                }
            ),
        ),
        rx.fragment(),
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
                    # Form Input: Prefill, Kategori & Lokasi
                    rx.vstack(
                        rx.cond(
                            FinanceState.asset_form_error != "",
                            rx.text(
                                FinanceState.asset_form_error,
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.DANGER_FG,
                            ),
                        ),
                        rx.box(
                            rx.hstack(
                                rx.vstack(
                                    rx.text(
                                        "Harga Satuan",
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                    ),
                                    rx.text(
                                        FinanceState.asset_form_harga_display,
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.TEXT,
                                    ),
                                    spacing="0",
                                    align="start",
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Tanggal Beli",
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                    ),
                                    rx.text(
                                        FinanceState.asset_form_tanggal_display,
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.TEXT,
                                    ),
                                    spacing="0",
                                    align="start",
                                ),
                                width="100%",
                                justify="between",
                            ),
                            padding="10px 12px",
                            background_color=Color.INFO_BG,
                            border=f"1px solid {Color.BLUE_BORDER}",
                            border_radius=Radius.CONTROL,
                            width="100%",
                        ),
                        rx.cond(
                            ~FinanceState.is_bulk_register_mode,
                            rx.vstack(
                                rx.text(
                                    "Nama Produk / Aset",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="text",
                                    value=FinanceState.asset_form_nama,
                                    on_change=FinanceState.set_asset_form_nama,
                                    style=_modal_input_style(),
                                ),
                                spacing="1",
                                width="100%",
                                align="start",
                            ),
                            rx.fragment(),
                        ),
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
                            style=_modal_input_style(),
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
                            style=_modal_input_style(),
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    "Jumlah Unit Didaftarkan (N)",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="number",
                                    value=FinanceState.asset_form_qty,
                                    on_change=FinanceState.set_asset_form_qty,
                                    style=_modal_input_style(),
                                ),
                                width="50%",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Garansi Sampai (Opsional)",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="date",
                                    value=FinanceState.asset_form_garansi,
                                    on_change=FinanceState.set_asset_form_garansi,
                                    style=_modal_input_style(),
                                ),
                                width="50%",
                                align="start",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.box(
                            rx.text(
                                "Aset akan otomatis dibuat dengan status 'Cadangan' untuk komponen "
                                "atau 'Digunakan' untuk unit utama sesuai jumlah Pcs.",
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
                            "Tandai Habis Pakai",
                            type="button",
                            on_click=FinanceState.submit_bukan_aset,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 14px",
                                    "background_color": Color.WARNING_BG,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.WARNING_FG,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.spacer(),
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


def _add_purchase_dialog() -> rx.Component:
    """Modal + Catat Pembelian baru."""
    return rx.cond(
        FinanceState.is_add_purchase_modal_open,
        rx.box(
            rx.box(
                on_click=FinanceState.close_add_purchase_modal,
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
                        "Catat Pembelian",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.cond(
                        FinanceState.new_purchase_error != "",
                        rx.text(
                            FinanceState.new_purchase_error,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.DANGER_FG,
                        ),
                    ),
                    rx.text("Produk *", font_size=FontSize.SM, font_weight=FontWeight.SEMIBOLD),
                    rx.el.input(
                        type="text",
                        value=FinanceState.new_purchase_produk,
                        on_change=FinanceState.set_new_purchase_produk,
                        style=_modal_input_style(),
                    ),
                    rx.grid(
                        rx.vstack(
                            rx.text(
                                "Tanggal",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                            ),
                            rx.el.input(
                                type="date",
                                value=FinanceState.new_purchase_tanggal,
                                on_change=FinanceState.set_new_purchase_tanggal,
                                style=_modal_input_style(),
                            ),
                            align="start",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text(
                                "Harga Satuan (Rp) *",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                            ),
                            rx.el.input(
                                type="number",
                                value=FinanceState.new_purchase_harga,
                                on_change=FinanceState.set_new_purchase_harga,
                                style=_modal_input_style(),
                            ),
                            align="start",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text(
                                "Pcs *",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                            ),
                            rx.el.input(
                                type="number",
                                value=FinanceState.new_purchase_pcs,
                                on_change=FinanceState.set_new_purchase_pcs,
                                style=_modal_input_style(),
                            ),
                            align="start",
                            width="100%",
                        ),
                        columns="3",
                        spacing="3",
                        width="100%",
                    ),
                    rx.grid(
                        rx.vstack(
                            rx.text(
                                "Nama Toko",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                            ),
                            rx.el.input(
                                type="text",
                                value=FinanceState.new_purchase_toko,
                                on_change=FinanceState.set_new_purchase_toko,
                                style=_modal_input_style(),
                            ),
                            align="start",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text(
                                "Dibeli Oleh",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                            ),
                            rx.el.select(
                                rx.el.option("Ridho", value="Ridho"),
                                rx.el.option("Surya", value="Surya"),
                                value=FinanceState.new_purchase_pembeli,
                                on_change=FinanceState.set_new_purchase_pembeli,
                                style=_modal_input_style(),
                            ),
                            align="start",
                            width="100%",
                        ),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),
                    rx.text(
                        "Link Marketplace (opsional)",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                    ),
                    rx.el.input(
                        type="url",
                        value=FinanceState.new_purchase_link,
                        on_change=FinanceState.set_new_purchase_link,
                        style=_modal_input_style(),
                    ),
                    rx.text(
                        "Status Aset Awal",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                    ),
                    rx.el.select(
                        rx.el.option("Belum didaftarkan", value="Belum didaftarkan"),
                        rx.el.option(
                            "Habis pakai · tidak perlu aset",
                            value="Habis pakai · tidak perlu aset",
                        ),
                        value=FinanceState.new_purchase_status,
                        on_change=FinanceState.set_new_purchase_status,
                        style=_modal_input_style(),
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=FinanceState.close_add_purchase_modal),
                        action_primary_button(
                            "Simpan Pembelian",
                            on_click=FinanceState.submit_new_purchase,
                        ),
                        width="100%",
                        justify="end",
                        spacing="2",
                        margin_top="8px",
                    ),
                    spacing="2",
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
                        "width": "92%",
                        "max_width": "520px",
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


def _import_purchase_dialog() -> rx.Component:
    """Modal Import CSV Pembelian."""
    return rx.cond(
        FinanceState.is_import_modal_open,
        rx.box(
            rx.box(
                on_click=FinanceState.close_import_modal,
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
                        "Import Data Pembelian (CSV)",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        "Format kolom: Tanggal, Produk, Harga, Pcs, Toko, "
                        "Link Marketplace, Dibeli Oleh",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.cond(
                        FinanceState.import_error != "",
                        rx.text(
                            FinanceState.import_error,
                            font_size=FontSize.XS,
                            color=Color.DANGER_FG,
                        ),
                    ),
                    rx.cond(
                        FinanceState.import_success != "",
                        rx.text(
                            FinanceState.import_success,
                            font_size=FontSize.XS,
                            color=Color.SUCCESS_FG,
                        ),
                    ),
                    rx.el.textarea(
                        value=FinanceState.import_csv_text,
                        on_change=FinanceState.set_import_csv_text,
                        style=rx.Style(
                            {
                                "width": "100%",
                                "height": "150px",
                                "padding": "10px 12px",
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                                "background_color": Color.SURFACE,
                                "color": Color.TEXT,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.XS,
                            }
                        ),
                    ),
                    rx.hstack(
                        secondary_button("Tutup", on_click=FinanceState.close_import_modal),
                        action_primary_button(
                            "Import Sekarang", on_click=FinanceState.submit_import_csv
                        ),
                        width="100%",
                        justify="end",
                        spacing="2",
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
                        "width": "92%",
                        "max_width": "540px",
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
            stat_card(
                "TOTAL INVOICE",
                FinanceState.invoices_summary["total_invoice"],
                note="arsip tersimpan",
                primary=True,
            ),
            stat_card("SUDAH DITAUTKAN", FinanceState.invoices_summary["sudah_ditautkan"]),
            stat_card(
                "BELUM DITAUTKAN",
                FinanceState.invoices_summary["belum_ditautkan"],
                value_tone="warning",
            ),
            stat_card(
                "PEMBELIAN TANPA BUKTI",
                FinanceState.invoices_summary["tanpa_bukti"],
                value_tone="danger",
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
                        "accessor": "tanggal_display",
                        "render_type": "date",
                        "width": "120px",
                    },
                    {"header": "Vendor", "accessor": "vendor", "width": "190px"},
                    {
                        "header": "Total",
                        "accessor": "total_rp_display",
                        "render_type": "currency_bold",
                        "align": "right",
                        "width": "140px",
                    },
                    {"header": "Berkas", "accessor": "berkas", "width": "120px"},
                    {
                        "header": "Terkait",
                        "accessor": "terkait_label",
                        "render_type": "badge",
                        "badge_variant_key": "tautan_variant",
                        "width": "260px",
                    },
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
                "PERLU DIBAYAR ≤ 30 HARI",
                FinanceState.bills_perlu_dibayar_display,
                note="termasuk terlambat",
                primary=True,
            ),
            stat_card(
                "TERLAMBAT",
                FinanceState.bills_summary["terlambat"],
                value_tone="danger",
                note="melewati jatuh tempo",
            ),
            stat_card(
                "SEGERA DIBAYAR (≤ 7 HARI)",
                FinanceState.bills_summary["segera"],
                value_tone="warning",
                note="mendekati jatuh tempo",
            ),
            stat_card(
                "TAGIHAN AKTIF",
                FinanceState.bills_summary["tagihan_aktif"],
                note="siklus berjalan",
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
                        "width": "220px",
                    },
                    {"header": "Vendor", "accessor": "vendor", "width": "135px"},
                    {
                        "header": "Kategori",
                        "accessor": "kategori",
                        "render_type": "chip",
                        "width": "110px",
                    },
                    {"header": "Periode", "accessor": "periode", "width": "95px"},
                    {
                        "header": "Nominal",
                        "accessor": "nominal_rp_display",
                        "render_type": "currency_bold",
                        "align": "right",
                        "width": "135px",
                    },
                    {
                        "header": "Jatuh Tempo",
                        "accessor": "jatuh_tempo_display",
                        "render_type": "date",
                        "width": "125px",
                    },
                    {
                        "header": "Pengingat",
                        "accessor": "pengingat_display",
                        "width": "145px",
                    },
                    {"header": "Pembayar", "accessor": "pembayar", "width": "95px"},
                    {
                        "header": "Status",
                        "accessor": "status_label",
                        "render_type": "badge",
                        "badge_variant_key": "status_variant",
                        "width": "140px",
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
    dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua marketplace",
            "value": FinanceState.marketplace_filter,
            "options": FinanceState.marketplace_options,
            "on_change": FinanceState.set_marketplace_filter,
        },
        {
            "label": "Semua status aset",
            "value": FinanceState.status_filter,
            "options": FinanceState.status_options,
            "on_change": FinanceState.set_status_filter,
        },
        {
            "label": "Periode",
            "value": FinanceState.period_filter,
            "options": FinanceState.period_options,
            "on_change": FinanceState.set_period_filter,
        },
    ]

    return base_layout(
        content=rx.vstack(
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
                            dropdowns=dropdowns,
                            extra_controls=_purchases_toolbar_actions(),
                            on_reset=FinanceState.reset_filters,
                        ),
                        _bulk_selection_bar(),
                        reusable_data_table(
                            items=FinanceState.purchases,
                            id_key="id_pembelian",
                            selected_ids=FinanceState.selected_purchase_ids,
                            all_selected=FinanceState.all_purchases_selected,
                            on_toggle_row=FinanceState.toggle_purchase_selection,
                            on_toggle_all=FinanceState.toggle_select_all_purchases,
                            hidden_columns=FinanceState.hidden_columns,
                            columns=[
                                {
                                    "key": "tanggal_display",
                                    "header": "Tanggal",
                                    "accessor": "tanggal_display",
                                    "render_type": "date",
                                    "width": "120px",
                                },
                                {
                                    "key": "produk",
                                    "header": "Produk",
                                    "accessor": "produk",
                                    "render_type": "bold",
                                    "width": "270px",
                                },
                                {
                                    "key": "harga_display",
                                    "header": "Harga Satuan",
                                    "accessor": "harga_display",
                                    "render_type": "currency",
                                    "align": "right",
                                    "width": "135px",
                                },
                                {
                                    "key": "pcs",
                                    "header": "Pcs",
                                    "accessor": "pcs",
                                    "render_type": "number",
                                    "align": "right",
                                    "width": "64px",
                                },
                                {
                                    "key": "total_display",
                                    "header": "Total",
                                    "accessor": "total_display",
                                    "render_type": "currency_bold",
                                    "align": "right",
                                    "width": "140px",
                                },
                                {
                                    "key": "toko_chip",
                                    "header": "Toko",
                                    "accessor": "toko_chip",
                                    "render_type": "chip",
                                    "width": "115px",
                                },
                                {
                                    "key": "link_marketplace",
                                    "header": "Link Marketplace",
                                    "accessor": "link_marketplace",
                                    "render_type": "link_icon",
                                    "align": "center",
                                    "width": "110px",
                                },
                                {
                                    "key": "dibeli_oleh",
                                    "header": "Dibeli Oleh",
                                    "accessor": "dibeli_oleh",
                                    "render_type": "text",
                                    "width": "115px",
                                },
                                {
                                    "key": "aset_status_label",
                                    "header": "Status Aset",
                                    "accessor": "aset_status_label",
                                    "render_type": "badge",
                                    "badge_variant_key": "aset_status_variant",
                                    "width": "195px",
                                },
                            ],
                            on_row_click=FinanceState.open_jadikan_aset_modal,
                            on_edit_row=FinanceState.open_jadikan_aset_modal,
                            on_duplicate_row=FinanceState.open_jadikan_aset_modal,
                            duplicate_action_label="Daftarkan sebagai aset",
                            show_action_header=True,
                        ),
                        _pagination(),
                        width="100%",
                        border=f"1px solid {Color.BORDER}",
                        border_radius=Radius.CARD,
                        background_color=Color.SURFACE,
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
            _jadikan_aset_dialog(),
            _add_purchase_dialog(),
            _import_purchase_dialog(),
            _pay_bill_dialog(),
            spacing="5",
            width="100%",
        ),
        breadcrumb=("Finance", "Pembelian & Invoice"),
    )


__all__ = ["purchases_view_page"]
