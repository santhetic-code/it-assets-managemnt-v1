"""
Komponen Sidebar Navigasi ITAM Pro.
Lebar 248px, latar #0A1A44, padding 20px 14px, 7 grup menu sesuai spesifikasi.
"""
import reflex as rx

from itam_pro.states.nav_state import NavState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Size

# Definisi struktur grup & item menu: (label, icon_tag, route, is_ready)
SIDEBAR_GROUPS: list[tuple[str, list[tuple[str, str, str, bool]]]] = [
    (
        "Overview",
        [
            ("Dashboard", "layout-grid", "/dashboard", True),
        ],
    ),
    (
        "Inventory",
        [
            ("Assets Inventory", "box", "/assets", True),
            ("Daftar PC", "hard-drive", "/pc", True),
            ("Rekap Monitor", "monitor", "/inventory/monitors", False),
            ("Rekap UPS", "battery", "/inventory/ups", False),
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
    """
    Item navigasi sidebar:
    Tinggi 40px, radius 10px, ikon 18px + teks 14px, warna nonaktif #C7D4F5,
    hover bg putih 8%, aktif bg #2563EB + teks putih weight 700.
    """
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
                    Color.SIDEBAR_HOVER_BG,
                ),
            }
        ),
    )


def _sidebar_group(
    group_name: str,
    items: list[tuple[str, str, str, bool]],
) -> rx.Component:
    """Grup menu dengan label uppercase 11px #8EA3D6."""
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


def sidebar() -> rx.Component:
    """Komponen utama Sidebar berukuran 248px."""
    return rx.box(
        _sidebar_brand(),
        rx.vstack(
            *[_sidebar_group(group_name, items) for group_name, items in SIDEBAR_GROUPS],
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
