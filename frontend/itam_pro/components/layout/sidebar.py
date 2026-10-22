"""
Komponen Sidebar Navigasi ITAM Pro.
Lebar 248px, latar #0A1A44, padding 20px 14px, grup menu dinamis sesuai spesifikasi Tahap 6c-1.
"""
from typing import Any

import reflex as rx

from itam_pro.services.category_config import get_pinned_categories
from itam_pro.states.asset_state import AssetState
from itam_pro.states.nav_state import NavState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Size

# Definisi struktur grup menu di luar Inventory: (label, icon_tag, route, is_ready)
SIDEBAR_GROUPS: list[tuple[str, list[tuple[str, str, str, bool]]]] = [
    (
        "Overview",
        [
            ("Dashboard", "layout-grid", "/dashboard", True),
        ],
    ),
    (
        "Infrastructure",
        [
            ("IP & Server (VM)", "server", "/infrastructure/ip-vm", False),
            ("Rekap Watt Server", "zap", "/infrastructure/watt-server", False),
        ],
    ),
    (
        "Operations",
        [
            ("Jadwal Maintenance", "calendar", "/operations/maintenance", False),
        ],
    ),
    (
        "Finance",
        [
            ("Rekap Pembelian", "shopping-cart", "/finance/purchases", False),
            ("Invoice", "file-text", "/finance/invoices", False),
        ],
    ),
    (
        "Security",
        [
            ("Credential Manager", "lock", "/security/credentials", False),
            ("Audit Log", "circle-check", "/security/audit-log", False),
        ],
    ),
    (
        "Admin",
        [
            ("Pengaturan Akun", "sun", "/admin/account-settings", False),
        ],
    ),
]


def _sidebar_brand() -> rx.Component:
    """Header atas sidebar: kotak logo 40x40 #2563EB + ITAM Pro & IT Assets Management."""
    return rx.hstack(
        rx.center(
            rx.icon(
                tag="box",
                size=Size.ICON_LG,
                color=Color.WHITE,
                stroke_width=2.2,
            ),
            width=Size.SIDEBAR_LOGO_BOX,
            height=Size.SIDEBAR_LOGO_BOX,
            background_color=Color.ACCENT_BRIGHT,
            border_radius=Radius.CONTROL,
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                "ITAM Pro",
                font_size=FontSize.SUBTITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.WHITE,
                line_height="1.15",
                letter_spacing="-0.01em",
            ),
            rx.text(
                "IT Assets Management",
                font_size=FontSize.XS,
                font_weight=FontWeight.REGULAR,
                color=Color.SIDEBAR_MUTED,
                line_height="1.2",
            ),
            spacing="0",
            style=rx.Style({"gap": "2px"}),
            align="start",
        ),
        spacing="3",
        align="center",
        padding_x="6px",
        margin_bottom="24px",
        width="100%",
    )


def _sidebar_item(
    group_name: str,
    label: str,
    icon_tag: str,
    route: str,
    is_ready: bool,
) -> rx.Component:
    """Item navigasi non-inventory dengan handler NavState."""
    is_active = NavState.active_menu == label

    return rx.el.button(
        rx.hstack(
            rx.icon(
                tag=icon_tag,
                size=Size.ICON_MD,
                color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_TEXT),
                stroke_width=rx.cond(is_active, 2.2, 1.85),
                flex_shrink="0",
            ),
            rx.text(
                label,
                font_size=FontSize.BASE,
                font_weight=rx.cond(is_active, FontWeight.BOLD, FontWeight.MEDIUM),
                color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_TEXT),
                line_height="1.2",
                white_space="nowrap",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        type="button",
        on_click=NavState.select_menu(group_name, label, route, is_ready),
        style=rx.Style(
            {
                "width": "100%",
                "height": Size.NAV_ITEM_HEIGHT,
                "padding": "0 12px",
                "border": "none",
                "border_radius": Radius.CONTROL,
                "background_color": rx.cond(is_active, Color.ACCENT_BRIGHT, "transparent"),
                "cursor": "pointer",
                "display": "flex",
                "align_items": "center",
                "text_align": "left",
                "transition": "background-color 0.15s ease, color 0.15s ease",
            }
        ),
        _hover=rx.Style(
            {
                "background_color": rx.cond(
                    is_active,
                    Color.ACCENT_BRIGHT,
                    Color.SIDEBAR_HOVER,
                ),
            }
        ),
    )


def _sidebar_group(
    group_name: str,
    items: list[tuple[str, str, str, bool]],
) -> rx.Component:
    """Grup menu umum dengan label uppercase."""
    return rx.vstack(
        rx.text(
            group_name.upper(),
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.SIDEBAR_MUTED,
            letter_spacing="0.06em",
            padding_x="12px",
            margin_bottom="4px",
        ),
        rx.vstack(
            *[
                _sidebar_item(group_name, label, icon_tag, route, is_ready)
                for label, icon_tag, route, is_ready in items
            ],
            spacing="0",
            style=rx.Style({"gap": "2px"}),
            width="100%",
        ),
        spacing="0",
        align="start",
        width="100%",
    )


def _inventory_nav_item(
    label: str,
    href: str,
    icon_tag: str,
    count_var: Any,
    is_active: Any,
) -> rx.Component:
    """Item menu grup Inventory dengan badge jumlah unit di kanan."""
    return rx.el.a(
        rx.hstack(
            rx.hstack(
                rx.icon(
                    tag=icon_tag,
                    size=Size.ICON_MD,
                    color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_TEXT),
                ),
                rx.text(
                    label,
                    font_size=FontSize.BASE,
                    font_weight=rx.cond(is_active, FontWeight.BOLD, FontWeight.MEDIUM),
                    color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_TEXT),
                ),
                spacing="3",
                align="center",
            ),
            rx.text(
                count_var,
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_MUTED),
                style=rx.Style(
                    {
                        "padding": "2px 8px",
                        "border_radius": Radius.FULL,
                        "background_color": rx.cond(
                            is_active,
                            "rgba(255, 255, 255, 0.22)",
                            "rgba(255, 255, 255, 0.08)",
                        ),
                    }
                ),
            ),
            width="100%",
            justify="between",
            align="center",
        ),
        href=href,
        style=rx.Style(
            {
                "width": "100%",
                "padding": "10px 12px",
                "border_radius": Radius.CONTROL,
                "text_decoration": "none",
                "background_color": rx.cond(
                    is_active, Color.ACCENT_BRIGHT, "transparent"
                ),
                "display": "block",
            }
        ),
        _hover=rx.Style(
            {
                "background_color": rx.cond(
                    is_active, Color.ACCENT_BRIGHT, Color.SIDEBAR_HOVER
                )
            }
        ),
    )


def render_inventory_sidebar_group(current_path: Any) -> rx.Component:
    """Render grup menu INVENTORY secara dinamis dari category_config (pinned=True)."""
    icon_map = {
        "pc": "monitor-speaker",
        "monitor": "monitor",
        "ups": "battery-charging",
    }
    pinned_items = get_pinned_categories()

    return rx.vstack(
        rx.text(
            "INVENTORY",
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.SIDEBAR_MUTED,
            letter_spacing="0.08em",
            padding_x="12px",
        ),
        _inventory_nav_item(
            label="Semua Aset",
            href="/assets",
            icon_tag="boxes",
            count_var=AssetState.sidebar_counts["all"],
            is_active=current_path == "/assets",
        ),
        *[
            _inventory_nav_item(
                label=cfg["name"],
                href=f"/assets/c/{cfg['slug']}",
                icon_tag=icon_map.get(cfg["slug"], "box"),
                count_var=AssetState.sidebar_counts[cfg["slug"]],
                is_active=current_path == f"/assets/c/{cfg['slug']}",
            )
            for cfg in pinned_items
        ],
        spacing="1",
        align="start",
        width="100%",
    )


def sidebar() -> rx.Component:
    """Komponen utama Sidebar berukuran 248px."""
    current_path = rx.State.router.page.path
    overview_items = next(items for name, items in SIDEBAR_GROUPS if name == "Overview")
    other_groups = [(name, items) for name, items in SIDEBAR_GROUPS if name != "Overview"]

    return rx.box(
        _sidebar_brand(),
        rx.vstack(
            _sidebar_group("Overview", overview_items),
            render_inventory_sidebar_group(current_path),
            *[_sidebar_group(name, items) for name, items in other_groups],
            spacing="0",
            style=rx.Style({"gap": "18px"}),
            width="100%",
            align="start",
        ),
        as_="aside",
        style=rx.Style(
            {
                "width": Size.SIDEBAR_WIDTH,
                "min_height": "100vh",
                "height": "100%",
                "background_color": Color.SIDEBAR,
                "padding": "20px 14px",
                "display": "flex",
                "flex_direction": "column",
                "flex_shrink": "0",
                "user_select": "none",
                "overflow_y": "auto",
            }
        ),
    )


__all__ = ["render_inventory_sidebar_group", "sidebar"]
