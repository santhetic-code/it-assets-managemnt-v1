"""Komponen Header Halaman Standar ITAM Pro (pola IP & Server / Credential Manager)."""

import reflex as rx

from itam_pro.styles import Color, FontSize, FontWeight, Radius, Shadow, Space


def page_header(
    icon: str,
    title: str | rx.Var[str],
    subtitle: str | rx.Var[str] = "",
    actions: list[rx.Component] | rx.Component | None = None,
    *,
    badge: rx.Component | None = None,
    icon_size: int = 24,
    subtitle_size: str = FontSize.BASE,
    margin_bottom: str = "0px",
) -> rx.Component:
    """Header halaman: kotak ikon gradien biru 52px + judul + subjudul di kiri; aksi di kanan."""
    title_row = (
        rx.hstack(
            rx.heading(
                title,
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.15",
                letter_spacing="-0.02em",
            ),
            badge,
            spacing="3",
            align="center",
            wrap="wrap",
        )
        if badge is not None
        else rx.heading(
            title,
            font_size=FontSize.TITLE,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.TEXT,
            line_height="1.15",
            letter_spacing="-0.02em",
        )
    )

    if isinstance(actions, list):
        actions_block: rx.Component = rx.hstack(
            *actions,
            spacing="3",
            align="center",
            wrap="wrap",
        )
    elif actions is not None:
        actions_block = actions
    else:
        actions_block = rx.fragment()

    has_subtitle = isinstance(subtitle, rx.Var) or bool(subtitle)
    subtitle_comp: rx.Component = (
        rx.text(
            subtitle,
            font_size=subtitle_size,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
        )
        if has_subtitle
        else rx.fragment()
    )

    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(tag=icon, size=icon_size, color=Color.WHITE, stroke_width=2),
                width="52px",
                height="52px",
                border_radius=Radius.ICON_HEADER,
                flex_shrink="0",
                style=rx.Style(
                    {
                        "background": Color.GRADIENT_BLUE,
                        "box_shadow": Shadow.HEADER_ICON,
                    }
                ),
            ),
            rx.vstack(
                title_row,
                subtitle_comp,
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
        ),
        actions_block,
        style=rx.Style(
            {
                "width": "100%",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S4,
                "margin_bottom": margin_bottom,
            }
        ),
    )


__all__ = ["page_header"]
