"""Halaman Security -> Audit Log (/audit-log)."""
import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    FilterDropdownConfig,
    reusable_data_table,
    table_filter_bar,
    table_pagination,
)
from itam_pro.states.audit_state import AuditState
from itam_pro.styles import Color, FontSize, FontWeight, Radius

AUDIT_COLUMNS: list[ColumnDef] = [
    {"key": "time_display", "header": "Waktu", "width": "175px", "render_type": "text"},
    {"key": "actor", "header": "Pelaku", "width": "150px", "render_type": "bold"},
    {
        "key": "module_badge",
        "header": "Modul",
        "width": "120px",
        "render_type": "badge",
        "badge_variant_key": "module_variant",
    },
    {"key": "action", "header": "Aksi", "width": "190px", "render_type": "text"},
    {"key": "target_id", "header": "Target ID", "width": "130px", "render_type": "chip"},
    {"key": "detail", "header": "Rincian Aktivitas", "width": "340px", "render_type": "text"},
]


def audit_view_page() -> rx.Component:
    dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua modul",
            "value": AuditState.module_filter,
            "options": AuditState.module_options,
            "on_change": AuditState.set_module_filter,
        }
    ]

    content = rx.vstack(
        rx.vstack(
            rx.heading(
                "Audit Log",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
            ),
            rx.text(
                "Rekam jejak seluruh perubahan data, autentikasi, dan akses kredensial.",
                font_size=FontSize.BASE,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        rx.box(
            table_filter_bar(
                search_value=AuditState.search_query,
                on_search_change=AuditState.set_search_query,
                search_placeholder="Cari pelaku, aksi, target ID, atau rincian...",
                dropdowns=dropdowns,
                on_reset=AuditState.reset_filters,
                result_count_text=AuditState.result_count_label,
            ),
            reusable_data_table(
                columns=AUDIT_COLUMNS,
                rows=AuditState.logs,
                id_key="id",
                show_action_header=False,
                empty_message="Tidak ada catatan audit yang cocok",
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
        spacing="4",
        width="100%",
    )
    return base_layout(content=content, breadcrumb=("Security", "Audit Log"))


__all__ = ["audit_view_page"]
