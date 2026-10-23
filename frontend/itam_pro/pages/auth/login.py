"""
Halaman Login ITAM Pro (/login).
Menggunakan desain Kartu Tengah (1040x640) dengan animasi geser Welcome -> Form.
"""
import reflex as rx

from itam_pro.components.ui import app_checkbox, form_input_field, primary_button
from itam_pro.states.auth_state import AuthState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Size

SLIDE_EASING = "cubic-bezier(0.65, 0, 0.35, 1)"


def _background_decorations() -> rx.Component:
    """4 ornamen hiasan latar belakang di luar kartu (aria-hidden)."""
    return rx.box(
        # 1. Cincin tebal 48px warna #CBDAF9 diameter 560 di pojok kiri-atas
        rx.box(
            style=rx.Style(
                {
                    "position": "absolute",
                    "top": "-150px",
                    "left": "-150px",
                    "width": "560px",
                    "height": "560px",
                    "border_radius": "50%",
                    "border": f"48px solid {Color.DECOR_RING}",
                }
            ),
        ),
        # 2. Lingkaran solid #C7D7F8 diameter 460 di pojok kanan-bawah
        rx.box(
            style=rx.Style(
                {
                    "position": "absolute",
                    "bottom": "-150px",
                    "right": "-90px",
                    "width": "460px",
                    "height": "460px",
                    "border_radius": "50%",
                    "background_color": Color.DECOR_CIRCLE,
                }
            ),
        ),
        # 3. Kotak outline 10px #CBDAF9 radius 22, diputar 18 derajat, kanan-atas
        rx.box(
            style=rx.Style(
                {
                    "position": "absolute",
                    "top": "calc(50% - 365px)",
                    "right": "calc(50% - 455px)",
                    "width": "104px",
                    "height": "104px",
                    "border": f"10px solid {Color.DECOR_RING}",
                    "border_radius": "22px",
                    "transform": "rotate(18deg)",
                }
            ),
        ),
        # 4. Lingkaran kecil #1340C7 opacity .18 di kiri-bawah
        rx.box(
            style=rx.Style(
                {
                    "position": "absolute",
                    "bottom": "calc(50% - 355px)",
                    "left": "calc(50% - 465px)",
                    "width": "60px",
                    "height": "60px",
                    "border_radius": "50%",
                    "background_color": Color.BRAND,
                    "opacity": "0.18",
                }
            ),
        ),
        aria_hidden="true",
        style=rx.Style(
            {
                "position": "fixed",
                "inset": "0",
                "overflow": "hidden",
                "pointer_events": "none",
                "z_index": "0",
            }
        ),
    )


def _panel_inner_rings() -> rx.Component:
    """3 cincin outline putih 14% sebagai hiasan di dalam panel biru."""
    ring_border = f"1.5px solid {Color.WHITE_14}"
    return rx.box(
        # Cincin 1: sekitar logo kiri-atas
        rx.box(
            style=rx.Style(
                {
                    "position": "absolute",
                    "top": "-130px",
                    "left": "-110px",
                    "width": "340px",
                    "height": "340px",
                    "border_radius": "50%",
                    "border": ring_border,
                }
            ),
        ),
        # Cincin 2: kanan-bawah lingkar luar
        rx.box(
            style=rx.Style(
                {
                    "position": "absolute",
                    "bottom": "-180px",
                    "right": "-90px",
                    "width": "460px",
                    "height": "460px",
                    "border_radius": "50%",
                    "border": ring_border,
                }
            ),
        ),
        # Cincin 3: kanan-bawah lingkar dalam
        rx.box(
            style=rx.Style(
                {
                    "position": "absolute",
                    "bottom": "-125px",
                    "right": "-35px",
                    "width": "320px",
                    "height": "320px",
                    "border_radius": "50%",
                    "border": ring_border,
                }
            ),
        ),
        aria_hidden="true",
        style=rx.Style(
            {
                "position": "absolute",
                "inset": "0",
                "overflow": "hidden",
                "pointer_events": "none",
                "z_index": "0",
            }
        ),
    )


def _brand_feature_row(text: str) -> rx.Component:
    """Item centang fitur di dalam panel biru."""
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
            white_space="nowrap",
        ),
        spacing="2",
        align="center",
    )


def _welcome_outline_button() -> rx.Component:
    """Tombol 'Masuk' outline putih yang hanya tampil saat State Welcome."""
    return rx.cond(
        AuthState.is_form_state,
        rx.fragment(),
        rx.el.button(
            "Masuk",
            type="button",
            on_click=AuthState.open_login_form,
            style=rx.Style(
                {
                    "margin_top": "32px",
                    "height": "46px",
                    "padding": "0 44px",
                    "background_color": "rgba(255, 255, 255, 0.06)",
                    "color": Color.WHITE,
                    "border": "1.5px solid rgba(255, 255, 255, 0.72)",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.MD,
                    "font_weight": FontWeight.BOLD,
                    "cursor": "pointer",
                    "transition": "background-color 0.15s ease, border-color 0.15s ease",
                }
            ),
            _hover=rx.Style(
                {
                    "background_color": "rgba(255, 255, 255, 0.16)",
                    "border_color": Color.WHITE,
                }
            ),
        ),
    )


def _blue_sliding_panel() -> rx.Component:
    """
    Panel biru (#1340C7) di dalam kartu:
    - State Welcome: lebar 100%, konten rata tengah, headline 42px, 3 poin horizontal.
    - State Form: menyusut ke 52.4%, konten rata kiri, headline 34px, 3 poin vertikal.
    """
    return rx.box(
        _panel_inner_rings(),
        # Baris Atas: Logo ITAM Pro (klik logo untuk kembali ke welcome saat preview)
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
            on_click=AuthState.reset_welcome_state,
            style=rx.Style({"position": "relative", "z_index": "1", "cursor": "pointer"}),
        ),
        # Bagian Tengah: Headline, Subjudul, 3 Poin Centang, & Tombol Welcome
        rx.box(
            rx.heading(
                "Kelola aset IT dalam satu tempat.",
                style=rx.Style(
                    {
                        "font_size": rx.cond(
                            AuthState.is_form_state,
                            FontSize.HERO_FORM,
                            FontSize.HERO_WELCOME,
                        ),
                        "line_height": "1.15",
                        "font_weight": FontWeight.EXTRABOLD,
                        "color": Color.WHITE,
                        "letter_spacing": "-0.02em",
                        "margin_bottom": "16px",
                        "max_width": rx.cond(AuthState.is_form_state, "420px", "580px"),
                        "transition": f"font-size 0.7s {SLIDE_EASING}",
                    }
                ),
            ),
            rx.text(
                "Inventaris, infrastruktur, dan maintenance yang terpantau rapi.",
                font_size=FontSize.SUBTITLE,
                line_height="1.6",
                font_weight=FontWeight.REGULAR,
                color=Color.WHITE_85,
                margin_bottom="26px",
                max_width=rx.cond(AuthState.is_form_state, "420px", "540px"),
            ),
            # 3 Poin Centang: Horizontal (gap 22px) saat Welcome, Vertikal (gap 12px) saat Form
            rx.box(
                _brand_feature_row("Inventaris terpusat"),
                _brand_feature_row("Audit terekam otomatis"),
                _brand_feature_row("Kredensial terenkripsi"),
                style=rx.Style(
                    {
                        "display": "flex",
                        "flex_direction": rx.cond(AuthState.is_form_state, "column", "row"),
                        "flex_wrap": "wrap",
                        "justify_content": rx.cond(
                            AuthState.is_form_state, "flex-start", "center"
                        ),
                        "align_items": rx.cond(AuthState.is_form_state, "flex-start", "center"),
                        "gap": rx.cond(AuthState.is_form_state, "12px", "22px"),
                    }
                ),
            ),
            _welcome_outline_button(),
            style=rx.Style(
                {
                    "position": "relative",
                    "z_index": "1",
                    "width": "100%",
                    "display": "flex",
                    "flex_direction": "column",
                    "align_items": rx.cond(AuthState.is_form_state, "flex-start", "center"),
                    "text_align": rx.cond(AuthState.is_form_state, "left", "center"),
                }
            ),
        ),
        # Baris Bawah: Footer Hak Cipta (kiri) & Status Sistem (kanan, hanya di Welcome)
        rx.hstack(
            rx.text(
                "© 2026 ITAM Pro · Khusus penggunaan internal",
                font_size=FontSize.FOOTER,
                font_weight=FontWeight.REGULAR,
                color=Color.WHITE_75,
            ),
            rx.cond(
                AuthState.is_form_state,
                rx.fragment(),
                rx.text(
                    "Sistem normal · v1.0.0",
                    font_size=FontSize.FOOTER,
                    font_weight=FontWeight.REGULAR,
                    color=Color.WHITE_75,
                ),
            ),
            width="100%",
            justify="between",
            align="center",
            style=rx.Style({"position": "relative", "z_index": "1"}),
        ),
        style=rx.Style(
            {
                "position": "relative",
                "z_index": "2",
                "width": rx.cond(AuthState.is_form_state, "52.4%", "100%"),
                "height": "100%",
                "background_color": Color.BRAND,
                "color": Color.WHITE,
                "padding": "40px 48px",
                "display": "flex",
                "flex_direction": "column",
                "justify_content": "space-between",
                "transition": f"width 0.7s {SLIDE_EASING}",
                "@media (prefers-reduced-motion: reduce)": {
                    "transition": "none",
                },
                "@media (max-width: 799px)": {
                    "width": "100%",
                    "min_height": "540px",
                    "padding": "36px 28px",
                    "display": rx.cond(AuthState.is_form_state, "none", "flex"),
                },
            }
        ),
    )


def _mobile_brand_header() -> rx.Component:
    """Logo ITAM Pro biru (#1340C7) di atas form saat layar mobile (<800px)."""
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
        margin_bottom="24px",
        style=rx.Style(
            {
                "display": "none",
                "@media (max-width: 799px)": {
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
    """
    Panel form di sisi kanan kartu (47.6% lebar kartu, padding 40px 48px).
    Muncul dengan animasi fade + translateX(24px -> 0) dan delay 0.25 dtk.
    """
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
                margin_bottom="6px",
            ),
            rx.text(
                "Gunakan akun yang diberikan administrator.",
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
                margin_bottom="28px",
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
                    padding="10px 14px",
                    margin_bottom="16px",
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
                        input_id="login-username-input",
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
            width="100%",
            max_width="380px",
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
                "position": "absolute",
                "top": "0",
                "right": "0",
                "bottom": "0",
                "width": "47.6%",
                "background_color": Color.SURFACE,
                "padding": "40px 48px",
                "display": "flex",
                "flex_direction": "column",
                "justify_content": "space-between",
                "align_items": "center",
                "opacity": rx.cond(AuthState.is_form_state, "1", "0"),
                "transform": rx.cond(
                    AuthState.is_form_state, "translateX(0px)", "translateX(24px)"
                ),
                "visibility": rx.cond(AuthState.is_form_state, "visible", "hidden"),
                "pointer_events": rx.cond(AuthState.is_form_state, "auto", "none"),
                "transition": rx.cond(
                    AuthState.is_form_state,
                    "opacity 0.45s ease 0.25s, transform 0.45s ease 0.25s, visibility 0s linear 0s",
                    "opacity 0.2s ease 0s, transform 0.2s ease 0s, visibility 0s linear 0.2s",
                ),
                "@media (prefers-reduced-motion: reduce)": {
                    "transition": "none",
                    "transform": "none",
                },
                "@media (max-width: 799px)": {
                    "position": "relative",
                    "width": "100%",
                    "padding": "36px 24px",
                    "min_height": "540px",
                    "display": rx.cond(AuthState.is_form_state, "flex", "none"),
                },
            }
        ),
    )


def login_page() -> rx.Component:
    """
    Halaman utama /login:
    Latar #DCE6FB, min-height 100vh, flex center, padding 48px 24px,
    dengan satu Kartu Tengah (maks 1040px, tinggi 640px, radius 24).
    """
    return rx.box(
        _background_decorations(),
        # Kartu Tengah
        rx.box(
            _blue_sliding_panel(),
            _right_form_panel(),
            style=rx.Style(
                {
                    "position": "relative",
                    "z_index": "1",
                    "width": "100%",
                    "max_width": Size.LOGIN_CARD_MAX_W,
                    "height": Size.LOGIN_CARD_H,
                    "background_color": Color.SURFACE,
                    "border_radius": Radius.LOGIN_CARD,
                    "box_shadow": Shadow.LOGIN_CARD,
                    "overflow": "hidden",
                    "@media (max-width: 799px)": {
                        "height": "auto",
                    },
                }
            ),
        ),
        style=rx.Style(
            {
                "position": "relative",
                "min_height": "100vh",
                "width": "100%",
                "background_color": Color.LOGIN_BG,
                "padding": "48px 24px",
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "overflow": "hidden",
            }
        ),
    )
