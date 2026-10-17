"""
Token Warna Semantik ITAM Pro (Light Theme v1).
"""


class Color:
    # Primary & Brand Tokens
    ACCENT = "#1D4ED8"          # Tombol utama, tautan, bar aktif, checkbox
    ACCENT_BRIGHT = "#2563EB"   # Menu aktif, hover tombol utama, fokus
    BRAND = "#1340C7"           # Panel branding login & teks logo mobile
    SIDEBAR = "#0A1A44"         # Latar sidebar navy

    # Neutral & Surface Tokens
    BG = "#F2F5FB"              # Latar halaman aplikasi
    SURFACE = "#FFFFFF"         # Latar panel form, kartu, input
    BORDER = "#E1E8F5"          # Garis batas kartu & tabel
    INPUT_BORDER = "#D5DEEE"    # Garis batas khusus field input

    # Focus Ring Token
    FOCUS_RING = "0 0 0 3px rgba(29, 78, 216, 0.15)"

    # Typography Tokens
    TEXT = "#0F1B3D"            # Teks utama (judul, label, isi input)
    MUTED = "#55627F"           # Teks sekunder, ikon input, placeholder
    WHITE = "#FFFFFF"           # Teks putih murni
    WHITE_85 = "rgba(255, 255, 255, 0.85)"  # Subjudul panel branding
    WHITE_75 = "rgba(255, 255, 255, 0.75)"  # Copyright panel branding

    # Status Semantic Tokens
    SUCCESS_FG = "#15803D"
    SUCCESS_BG = "#DCFCE7"

    WARNING_FG = "#92400E"
    WARNING_BG = "#FEF3C7"

    DANGER_FG = "#B91C1C"
    DANGER_BG = "#FEE2E2"
