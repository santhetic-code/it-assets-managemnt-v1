"""
Halaman Login ITAM Pro (/login).
Mengikuti referensi desain Login_2x.png secara presisi.
"""
import reflex as rx

from itam_pro.components.ui import app_checkbox, form_input_field, primary_button
from itam_pro.states.auth_state import AuthState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Size


def _brand_feature_row(text: str) -> rx.Component:
    """Baris item centang di panel branding kiri."""
    return rx.hstack(
        rx.icon(
            tag="circle-check",
            size=Size.ICON_MD,
            color=Color.WHITE,
            stroke_width=2,
            flex_shrink="0",
        ),
        rx.text(
            text,
            font_size=FontSize.MD,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.WHITE,
            line_height="1.4",
        ),
        spacing="3",
        align="center",
    )


def _left_branding_panel() -> rx.Component:
    """Panel kiri biru (#1340C7) dengan logo, headline, 3 poin fitur, dan copyright."""
    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(
                    tag="box",
                    size=22,
                    color=Color.BRAND,
                    stroke_width=2.2,
                ),
                width=Size.LOGO_BOX,
                height=Size.LOGO_BOX,
                background_color=Color.WHITE,
                border_radius=Radius.LOGO_BOX,
                flex_shrink="0",
            ),
            rx.text(
                "ITAM Pro",
                font_size=FontSize.LOGO,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.WHITE,
                letter_spacing="-0.01em",
            ),
            spacing="3",
            align="center",
        ),
        rx.box(
            rx.heading(
                "Kelola aset IT dalam satu tempat.",
                font_size=FontSize.HERO,
                line_height="1.12",
                font_weight=FontWeight.EXTRABOLD,
                color=Color.WHITE,
                letter_spacing="-0.02em",
                margin_bottom="18px",
            ),
            rx.text(
                "Inventaris, infrastruktur, dan maintenance yang terpantau rapi.",
                font_size=FontSize.SUBTITLE,
                line_height="1.6",
                font_weight=FontWeight.REGULAR,
                color=Color.WHITE_85,
                margin_bottom="28px",
            ),
            rx.vstack(
                _brand_feature_row("Inventaris terpusat"),
                _brand_feature_row("Audit terekam otomatis"),
                _brand_feature_row("Kredensial terenkripsi"),
                spacing="0",
                style=rx.Style({"gap": "14px"}),
                align="start",
            ),
            max_width="460px",
            width="100%",
        ),
        rx.text(
            "© 2026 ITAM Pro · Khusus penggunaan internal",
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.REGULAR,
            color=Color.WHITE_75,
        ),
        style=rx.Style(
            {
                "background_color": Color.BRAND,
                "color": Color.WHITE,
                "padding": "48px 64px",
                "display": "flex",
                "flex_direction": "column",
                "justify_content": "space-between",
                "min_height": "100vh",
                "@media (max-width: 899px)": {
                    "display": "none",
                },
            }
        ),
    )


def _mobile_brand_header() -> rx.Component:
    """Logo ITAM Pro biru (#1340C7) yang hanya tampil di layar < 900px."""
    return rx.hstack(
        rx.center(
            rx.icon(tag="box", size=20, color=Color.WHITE, stroke_width=2.2),
            width="36px",
            height="36px",
            background_color=Color.BRAND,
            border_radius="10px",
        ),
        rx.text(
            "ITAM Pro",
            font_size=FontSize.LOGO,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.BRAND,
        ),
        spacing="3",
        align="center",
        margin_bottom="28px",
        style=rx.Style(
            {
                "display": "none",
                "@media (max-width: 899px)": {
                    "display": "flex",
                },
            }
        ),
    )


def _password_toggle_button() -> rx.Component:
    """Tombol ikon mata untuk tampilkan/sembunyikan password dengan aria-label."""
    return rx.el.button(
        rx.cond(
            AuthState.show_password,
            rx.icon(tag="eye-off", size=Size.ICON_MD, color=Color.MUTED, stroke_width=1.75),
            rx.icon(tag="eye", size=Size.ICON_MD, color=Color.MUTED, stroke_width=1.75),
        ),
        type="button",
        aria_label="Tampilkan atau sembunyikan password",
        on_click=AuthState.toggle_password_visibility,
        style=rx.Style(
            {
                "background": "transparent",
                "border": "none",
                "padding": "4px",
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "cursor": "pointer",
                "flex_shrink": "0",
            }
        ),
    )


def _right_form_panel() -> rx.Component:
    """Panel kanan putih berisi form masuk (maks lebar 380px) dan footer di dasar panel."""
    return rx.box(
        rx.box(),
        rx.box(
            _mobile_brand_header(),
            rx.heading(
                "Masuk",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.2",
                letter_spacing="-0.02em",
                margin_bottom="8px",
            ),
            rx.text(
                "Gunakan akun yang diberikan administrator.",
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
                margin_bottom="32px",
            ),
            rx.cond(
                AuthState.error_message != "",
                rx.hstack(
                    rx.icon(tag="circle-alert", size=16, color=Color.DANGER_FG, flex_shrink="0"),
                    rx.text(
                        AuthState.error_message,
                        font_size="13px",
                        font_weight=FontWeight.MEDIUM,
                        color=Color.DANGER_FG,
                    ),
                    width="100%",
                    padding="12px 14px",
                    margin_bottom="20px",
                    background_color=Color.DANGER_BG,
                    border_radius=Radius.CONTROL,
                    spacing="2",
                    align="center",
                ),
            ),
            rx.el.form(
                rx.vstack(
                    form_input_field(
                        label="Username",
                        placeholder="Username",
                        icon_tag="user",
                        name="username",
                        value=AuthState.username,
                        on_change=AuthState.set_username,
                    ),
                    form_input_field(
                        label="Password",
                        placeholder="Password",
                        icon_tag="lock",
                        name="password",
                        input_type=rx.cond(AuthState.show_password, "text", "password"),
                        value=AuthState.password,
                        on_change=AuthState.set_password,
                        right_element=_password_toggle_button(),
                    ),
                    rx.hstack(
                        app_checkbox(
                            label="Ingat saya",
                            checked=AuthState.remember_me,
                            on_change=AuthState.set_remember_me,
                        ),
                        rx.link(
                            "Lupa password?",
                            href="#",
                            on_click=AuthState.handle_forgot_password,
                            font_size=FontSize.BASE,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.ACCENT,
                            text_decoration="none",
                            _hover=rx.Style(
                                {
                                    "text_decoration": "none",
                                    "color": Color.ACCENT_BRIGHT,
                                }
                            ),
                        ),
                        width="100%",
                        justify="between",
                        align="center",
                    ),
                    primary_button(
                        label="Masuk",
                        button_type="submit",
                        is_loading=AuthState.is_loading,
                        margin_top="4px",
                    ),
                    spacing="0",
                    style=rx.Style({"gap": "20px"}),
                    width="100%",
                ),
                on_submit=AuthState.submit_login,
                reset_on_submit=False,
            ),
            max_width="380px",
            width="100%",
            margin_x="auto",
        ),
        rx.text(
            "Sistem normal · v1.0.0",
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
            text_align="center",
            width="100%",
        ),
        style=rx.Style(
            {
                "background_color": Color.SURFACE,
                "padding": "48px 24px",
                "display": "flex",
                "flex_direction": "column",
                "justify_content": "space-between",
                "align_items": "center",
                "min_height": "100vh",
                "width": "100%",
            }
        ),
    )


def login_page() -> rx.Component:
    """Halaman utama /login dengan grid 2 kolom (1.1fr dan 1fr)."""
    return rx.box(
        _left_branding_panel(),
        _right_form_panel(),
        style=rx.Style(
            {
                "display": "grid",
                "grid_template_columns": "1.1fr 1fr",
                "min_height": "100vh",
                "width": "100%",
                "background_color": Color.SURFACE,
                "@media (max-width: 899px)": {
                    "grid_template_columns": "1fr",
                },
            }
        ),
    )
