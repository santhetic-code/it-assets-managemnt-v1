"""
Konfigurasi Tipografi ITAM Pro (Plus Jakarta Sans).
"""
from .colors import Color

FONT_FAMILY = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
)


class FontWeight:
    REGULAR = "400"
    MEDIUM = "500"
    SEMIBOLD = "600"
    BOLD = "700"
    EXTRABOLD = "800"


class FontSize:
    GROUP_LABEL = "11px"        # Label uppercase grup menu di sidebar & Ctrl K
    XS = "12px"                 # Subjudul brand sidebar & role user di topbar
    FOOTER = "12.5px"
    SM = "13px"
    BASE = "14px"
    MD = "15px"
    SUBTITLE = "16px"
    LOGO = "18px"
    TITLE = "28px"
    HERO_FORM = "34px"          # Headline panel biru saat state form
    HERO_WELCOME = "42px"       # Headline panel biru saat state welcome


BASE_STYLE: dict = {
    **{
        "font_family": FONT_FAMILY,
        "background_color": Color.BG,
        "color": Color.TEXT,
        "box_sizing": "border-box",
        "-webkit-font-smoothing": "antialiased",
        "-moz-osx-font-smoothing": "grayscale",
        "input, button, select, textarea": {
            "font_family": FONT_FAMILY,
        },
        "input::placeholder": {
            "color": Color.MUTED,
            "opacity": "0.75",
        },
    }
}
