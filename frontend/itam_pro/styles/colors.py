"""
Token Warna Semantik ITAM Pro (Light Theme v1).
"""


class Color:
    # Primary & Brand Tokens
    ACCENT = "#1D4ED8"          # Tombol utama, tautan, bar aktif, checkbox
    ACCENT_BRIGHT = "#2563EB"   # Menu aktif, hover tombol utama, fokus
    BRAND = "#1340C7"           # Panel branding login & teks logo mobile

    # Sidebar Tokens
    SIDEBAR = "#0A1A44"         # Latar sidebar navy
    SIDEBAR_TEXT = "#C7D4F5"    # Teks & ikon item menu nonaktif di sidebar
    SIDEBAR_MUTED = "#8EA3D6"   # Subjudul brand & label grup uppercase di sidebar
    SIDEBAR_HOVER_BG = "rgba(255, 255, 255, 0.08)"  # Latar hover item sidebar
    SIDEBAR_DIVIDER = "rgba(255, 255, 255, 0.08)"   # Garis pemisah halus di sidebar

    # Login Page & Ornaments Tokens
    LOGIN_BG = "#DCE6FB"        # Latar halaman login di belakang kartu
    DECOR_RING = "#CBDAF9"      # Cincin kiri-atas & kotak kanan-atas
    DECOR_CIRCLE = "#C7D7F8"    # Lingkaran solid kanan-bawah

    # Neutral & Surface Tokens
    BG = "#F2F5FB"              # Latar halaman utama aplikasi
    SURFACE = "#FFFFFF"         # Latar topbar, kartu, panel form, input
    SEARCH_BG = "#F6F8FC"       # Latar kotak pencarian di topbar
    SURFACE_HOVER = "#F8FAFC"   # Latar hover tombol sekunder/ikon di topbar
    BORDER = "#E1E8F5"          # Garis batas bawah topbar, kartu, & tabel
    INPUT_BORDER = "#D5DEEE"    # Garis batas khusus field input
    OVERLAY_BACKDROP = "rgba(10, 26, 68, 0.45)"  # Backdrop drawer mobile

    # Focus Ring Token
    FOCUS_RING = "0 0 0 3px rgba(29, 78, 216, 0.15)"

    # Typography & Overlay Tokens
    TEXT = "#0F1B3D"            # Teks utama (judul, label, isi input)
    MUTED = "#55627F"           # Teks sekunder, ikon input, placeholder
    WHITE = "#FFFFFF"           # Teks putih murni
    WHITE_85 = "rgba(255, 255, 255, 0.85)"  # Subjudul panel branding
    WHITE_75 = "rgba(255, 255, 255, 0.75)"  # Copyright & status di panel biru
    WHITE_14 = "rgba(255, 255, 255, 0.14)"  # 3 cincin hiasan di dalam panel biru

    # Status Semantic Tokens
    SUCCESS_FG = "#15803D"
    SUCCESS_BG = "#DCFCE7"

    WARNING_FG = "#92400E"
    WARNING_BG = "#FEF3C7"

    DANGER_FG = "#B91C1C"
    DANGER_BG = "#FEE2E2"
    NOTIFICATION_DOT = "#DC2626"  # Titik merah notifikasi pada ikon lonceng
