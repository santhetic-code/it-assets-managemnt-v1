"""
Skala Spacing, Ukuran Kontrol, Border Radius, dan Shadow ITAM Pro.
"""


class Space:
    S1 = "4px"
    S2 = "8px"
    S3 = "12px"
    S4 = "16px"
    S5 = "20px"
    S6 = "24px"
    S7 = "28px"
    S8 = "32px"


class Size:
    # Layout Dimensions
    SIDEBAR_WIDTH = "248px"
    TOPBAR_HEIGHT = "68px"
    SEARCH_WIDTH = "340px"

    # Control & Box Dimensions
    CONTROL_HEIGHT = "48px"
    TOPBAR_CONTROL_H = "44px"
    BUTTON_MD_H = "42px"
    NAV_ITEM_HEIGHT = "40px"
    SIDEBAR_LOGO_BOX = "40px"
    AVATAR_BOX = "40px"
    STAT_ICON_CHIP = "36px"     # Chip ikon 36x36px di kanan atas kartu KPI
    LOGO_BOX = "44px"

    # Icon & Indicator Sizes
    ICON_SM = 16
    ICON_MD = 18
    ICON_LG = 20
    CHECKBOX = "18px"
    NOTIF_DOT = "8px"
    LEGEND_DOT = "10px"
    PROGRESS_H = "7px"

    # Login Card Dimensions
    LOGIN_CARD_MAX_W = "1040px"
    LOGIN_CARD_H = "640px"


class Radius:
    BADGE_KBD = "6px"
    CHIP = "10px"
    CONTROL = "10px"
    LOGO_BOX = "12px"
    CARD = "14px"               # Radius kartu standar (20px padding)
    LOGIN_CARD = "24px"
    FULL = "9999px"


class Shadow:
    NONE = "none"
    LOGIN_CARD = "0 30px 80px rgba(10, 26, 68, 0.28)"
    DRAWER = "-8px 0 24px -4px rgba(15, 27, 61, 0.08)"
    POPOVER = "0 12px 32px -4px rgba(15, 27, 61, 0.12)"
