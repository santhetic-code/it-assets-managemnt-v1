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
    GROUP_LABEL = "11px"
    XS = "12px"
    FOOTER = "12.5px"           # Keterangan bawah KPI & waktu relatif
    SM = "13px"                 # Label kartu KPI & tautan kartu
    BASE = "14px"
    MD = "15px"
    SUBTITLE = "16px"           # Judul dalam kartu (Card Title)
    LOGO = "18px"
    DONUT_TOTAL = "24px"        # Angka total di tengah donut chart
    TITLE = "28px"              # Judul halaman
    KPI_VALUE = "32px"          # Angka utama kartu KPI (weight 800)
    HERO_FORM = "34px"
    HERO_WELCOME = "42px"


BASE_STYLE: dict = {
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

