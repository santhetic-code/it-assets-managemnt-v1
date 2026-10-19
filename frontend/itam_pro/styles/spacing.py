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
    SIDEBAR_WIDTH = "248px"     # Lebar tetap sidebar desktop
    TOPBAR_HEIGHT = "68px"      # Tinggi topbar
    SEARCH_WIDTH = "340px"      # Lebar kotak pencarian di topbar

    # Control & Box Dimensions
    CONTROL_HEIGHT = "48px"     # Tinggi standar input dan tombol form login
    TOPBAR_CONTROL_H = "44px"   # Tinggi kotak pencarian & tombol lonceng topbar
    BUTTON_MD_H = "42px"        # Tinggi tombol aksi header halaman
    NAV_ITEM_HEIGHT = "40px"    # Tinggi item menu di sidebar
    SIDEBAR_LOGO_BOX = "40px"   # Ukuran kotak biru logo di sidebar
    AVATAR_BOX = "40px"         # Ukuran lingkaran avatar di topbar
    LOGO_BOX = "44px"           # Ukuran kotak putih logo di panel login

    # Icon & Indicator Sizes
    ICON_SM = 16
    ICON_MD = 18                # Ukuran ikon standar sidebar, input, topbar
    ICON_LG = 20
    CHECKBOX = "18px"           # Ukuran kotak checkbox
    NOTIF_DOT = "8px"           # Ukuran titik merah lonceng notifikasi

    # Login Card Dimensions
    LOGIN_CARD_MAX_W = "1040px"
    LOGIN_CARD_H = "640px"


class Radius:
    BADGE_KBD = "6px"           # Badge shortcut Ctrl K
    CONTROL = "10px"            # Input, tombol, item sidebar, logo sidebar
    LOGO_BOX = "12px"           # Kotak ikon logo ITAM Pro di login
    CARD = "14px"               # Kartu umum
    LOGIN_CARD = "24px"         # Kartu tengah halaman login
    FULL = "9999px"             # Lingkaran penuh (avatar, titik notifikasi)


class Shadow:
    NONE = "none"
    LOGIN_CARD = "0 30px 80px rgba(10, 26, 68, 0.28)"
    DRAWER = "-8px 0 24px -4px rgba(15, 27, 61, 0.08)"
    POPOVER = "0 12px 32px -4px rgba(15, 27, 61, 0.12)"
