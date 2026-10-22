"""
Komponen Topbar ITAM Pro.
Tinggi 68px, putih, border bawah #E1E8F5, padding 0 32px.
"""
import reflex as rx

from itam_pro.states.auth_state import AuthState
from itam_pro.states.nav_state import NavState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size


def _mobile_menu_trigger() -> rx.Component:
    """Tombol pembuka drawer sidebar khusus layar <900px."""
    return rx.el.button(
        rx.icon(tag="menu", size=Size.ICON_LG, color=Color.TEXT, stroke_width=2),
        type="button",
        aria_label="Buka menu navigasi",
        on_click=NavState.toggle_mobile_sidebar,
        style=rx.Style(
            {
                "width": "40px",
                "height": "40px",
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CONTROL,
                "background_color": Color.SURFACE,
                "display": "none",
                "align_items": "center",
                "justify_content": "center",
                "cursor": "pointer",
                "flex_shrink": "0",
                "@media (max-width: 899px)": {
                    "display": "inline-flex",
                },
            }
        ),
    )


def _breadcrumb(group: str | rx.Var[str], page: str | rx.Var[str]) -> rx.Component:
    """Breadcrumb kiri: 'Grup / Halaman'."""
    return rx.hstack(
        _mobile_menu_trigger(),
        rx.hstack(
            rx.text(
                group,
                font_size=FontSize.BASE,
                font_weight=FontWeight.MEDIUM,
                color=Color.MUTED,
            ),
            rx.text(
                "/",
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
                margin_x="2px",
            ),
            rx.text(
                page,
                font_size=FontSize.BASE,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            spacing="2",
            align="center",
        ),
        spacing="3",
        align="center",
    )


def _search_box() -> rx.Component:
    """Kotak pencarian tengah 340px tinggi 44px dengan badge 'Ctrl K'."""
    return rx.hstack(
        rx.icon(
            tag="search",
            size=Size.ICON_SM,
            color=Color.MUTED,
            stroke_width=2,
            flex_shrink="0",
        ),
        rx.el.input(
            type="text",
            placeholder="Cari aset, IP, serial number...",
            value=NavState.global_search_query,
            on_change=NavState.set_global_search_query,
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "100%",
                    "border": "none",
                    "outline": "none",
                    "background": "transparent",
                    "color": Color.TEXT,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.REGULAR,
                }
            ),
        ),
        rx.box(
            "Ctrl K",
            style=rx.Style(
                {
                    "padding": "3px 7px",
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.BADGE_KBD,
                    "font_size": FontSize.GROUP_LABEL,
                    "font_weight": FontWeight.SEMIBOLD,
                    "color": Color.MUTED,
                    "white_space": "nowrap",
                    "line_height": "1",
                    "flex_shrink": "0",
                }
            ),
        ),
        spacing="2",
        align="center",
        style=rx.Style(
            {
                "width": Size.SEARCH_WIDTH,
                "height": Size.TOPBAR_CONTROL_H,
                "padding": "0 12px 0 14px",
                "background_color": Color.SEARCH_BG,
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": Radius.CONTROL,
                "transition": "border-color 0.15s ease, box-shadow 0.15s ease",
                "@media (max-width: 767px)": {
                    "display": "none",
                },
                "&:focus-within": {
                    "background_color": Color.SURFACE,
                    "border_color": Color.ACCENT,
                    "box_shadow": Color.FOCUS_RING,
                },
            }
        ),
    )


def _notification_button() -> rx.Component:
    """Tombol lonceng 44x44 dengan indikator titik merah."""
    return rx.el.button(
        rx.box(
            rx.icon(
                tag="bell",
                size=Size.ICON_MD,
                color=Color.TEXT,
                stroke_width=2,
            ),
            # Titik merah di pojok kanan-atas ikon lonceng
            rx.box(
                style=rx.Style(
                    {
                        "position": "absolute",
                        "top": "-2px",
                        "right": "-2px",
                        "width": Size.NOTIF_DOT,
                        "height": Size.NOTIF_DOT,
                        "background_color": Color.NOTIFICATION_DOT,
                        "border": f"1.5px solid {Color.SURFACE}",
                        "border_radius": Radius.FULL,
                    }
                ),
            ),
            style=rx.Style(
                {
                    "position": "relative",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
                }
            ),
        ),
        type="button",
        aria_label="Notifikasi sistem",
        style=rx.Style(
            {
                "width": Size.TOPBAR_CONTROL_H,
                "height": Size.TOPBAR_CONTROL_H,
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CONTROL,
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "cursor": "pointer",
                "flex_shrink": "0",
                "transition": "background-color 0.15s ease",
                "&:hover": {"background_color": Color.SURFACE_HOVER},
            }
        ),
    )


def _profile_menu() -> rx.Component:
    """Avatar bulat + nama + role dari AuthState.current_user dengan menu aksi 'Keluar'."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.el.button(
                rx.hstack(
                    rx.center(
                        rx.text(
                            AuthState.user_initials,
                            font_size=FontSize.SM,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.WHITE,
                        ),
                        width=Size.AVATAR_BOX,
                        height=Size.AVATAR_BOX,
                        background_color=Color.ACCENT,
                        border_radius=Radius.FULL,
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            AuthState.user_display_name,
                            font_size=FontSize.BASE,
                            font_weight=FontWeight.BOLD,
                            color=Color.TEXT,
                            line_height="1.2",
                        ),
                        rx.text(
                            AuthState.user_role_label,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.REGULAR,
                            color=Color.MUTED,
                            line_height="1.2",
                        ),
                        spacing="0",
                        style=rx.Style({"gap": "2px"}),
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                ),
                type="button",
                style=rx.Style(
                    {
                        "background": "transparent",
                        "border": "none",
                        "padding": "4px 6px",
                        "border_radius": Radius.CONTROL,
                        "cursor": "pointer",
                        "display": "inline-flex",
                        "align_items": "center",
                        "transition": "background-color 0.15s ease",
                        "&:hover": {"background_color": Color.SURFACE_HOVER},
                    }
                ),
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.hstack(
                    rx.icon(tag="user", size=Size.ICON_SM, color=Color.TEXT),
                    rx.text(
                        "Pengaturan Akun",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.MEDIUM,
                        color=Color.TEXT,
                    ),
                    spacing="2",
                    align="center",
                ),
                on_click=NavState.select_menu(
                    "Admin", "Pengaturan Akun", "/admin/account-settings", False
                ),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.hstack(
                    rx.icon(tag="log-out", size=Size.ICON_SM, color=Color.DANGER_FG),
                    rx.text(
                        "Keluar",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.DANGER_FG,
                    ),
                    spacing="2",
                    align="center",
                ),
                on_click=AuthState.logout,
            ),
            align="end",
        ),
    )


def topbar(
    breadcrumb: tuple[str | rx.Var[str], str | rx.Var[str]] = ("Overview", "Dashboard"),
) -> rx.Component:
    """Bar navigasi atas setinggi 68px."""
    group, page = breadcrumb
    return rx.box(
        _breadcrumb(group, page),
        _search_box(),
        rx.hstack(
            _notification_button(),
            _profile_menu(),
            spacing="3",
            align="center",
        ),
        as_="header",
        style=rx.Style(
            {
                "width": "100%",
                "height": Size.TOPBAR_HEIGHT,
                "background_color": Color.SURFACE,
                "border_bottom": f"1px solid {Color.BORDER}",
                "padding": "0 32px",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "position": "sticky",
                "top": "0",
                "z_index": "20",
                "@media (max-width: 899px)": {
                    "padding": "0 20px",
                },
            }
        ),
    )
