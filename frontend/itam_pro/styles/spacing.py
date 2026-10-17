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
    S8 = "32px"


class Size:
    CONTROL_HEIGHT = "48px"     # Tinggi standar input dan tombol utama
    LOGO_BOX = "44px"           # Ukuran kotak putih logo di panel login
    ICON_MD = 18                # Ukuran ikon standar input, centang, mata
    CHECKBOX = "18px"           # Ukuran kotak checkbox


class Radius:
    CONTROL = "10px"            # Input dan tombol
    LOGO_BOX = "12px"           # Kotak ikon logo ITAM Pro
    CARD = "14px"               # Kartu umum
    LOGIN_CARD = "18px"         # Kartu login


class Shadow:
    NONE = "none"
    SUBTLE_LOGIN = "0 10px 30px -5px rgba(15, 27, 61, 0.07), 0 4px 12px -2px rgba(15, 27, 61, 0.04)"
    DRAWER = "-8px 0 24px -4px rgba(15, 27, 61, 0.08)"
