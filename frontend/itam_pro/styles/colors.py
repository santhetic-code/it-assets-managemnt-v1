"""
Token Warna Semantik ITAM Pro (Light Theme v1).
"""


class Color:
    # Primary & Brand Tokens
    ACCENT = "#1D4ED8"          # Tombol utama, tautan, bar bulan terakhir, donut PC
    ACCENT_BRIGHT = "#2563EB"   # Menu aktif sidebar, progress bar <70%, hover tombol
    BRAND = "#1340C7"           # Panel branding login & teks logo mobile

    # Sidebar Tokens
    SIDEBAR = "#0A1A44"         # Latar sidebar navy & donut kategori Server
    SIDEBAR_TEXT = "#C7D4F5"    # Teks & ikon item menu nonaktif di sidebar
    SIDEBAR_MUTED = "#8EA3D6"   # Subjudul brand & label grup uppercase di sidebar
    SIDEBAR_HOVER_BG = "rgba(255, 255, 255, 0.08)"
    SIDEBAR_DIVIDER = "rgba(255, 255, 255, 0.08)"

    # Login Page & Ornaments Tokens
    LOGIN_BG = "#DCE6FB"
    DECOR_RING = "#CBDAF9"
    DECOR_CIRCLE = "#C7D7F8"

    # Neutral & Surface Tokens
    BG = "#F2F5FB"              # Latar halaman utama aplikasi
    SURFACE = "#FFFFFF"         # Latar topbar, kartu, panel form, input
    SEARCH_BG = "#F6F8FC"       # Latar kotak pencarian di topbar
    SURFACE_HOVER = "#F8FAFC"   # Latar hover tombol sekunder/ikon
    BORDER = "#E1E8F5"          # Garis batas bawah topbar, kartu, & tabel
    DIVIDER = "#EEF2F9"         # Garis pemisah tipis antar baris daftar di dalam kartu
    INPUT_BORDER = "#D5DEEE"    # Garis batas khusus field input & tombol sekunder
    OVERLAY_BACKDROP = "rgba(10, 26, 68, 0.45)"

    # Focus Ring Token
    FOCUS_RING = "0 0 0 3px rgba(29, 78, 216, 0.15)"

    # Typography & Overlay Tokens
    TEXT = "#0F1B3D"            # Teks utama (judul, angka KPI, nama user)
    MUTED = "#55627F"           # Teks sekunder (subjudul, label KPI, waktu relatif)
    WHITE = "#FFFFFF"
    WHITE_85 = "rgba(255, 255, 255, 0.85)"
    WHITE_75 = "rgba(255, 255, 255, 0.75)"
    WHITE_14 = "rgba(255, 255, 255, 0.14)"

    # Status & Chip Semantic Tokens (Foreground & Background)
    SUCCESS_FG = "#15803D"
    SUCCESS_BG = "#DCFCE7"

    WARNING_FG = "#92400E"
    WARNING_BG = "#FEF3C7"

    DANGER_FG = "#B91C1C"
    DANGER_BG = "#FEE2E2"

    INFO_FG = "#1D4ED8"
    INFO_BG = "#DBEAFE"

    PURPLE_FG = "#6D28D9"       # Chip ikon Garansi <= 30 Hari
    PURPLE_BG = "#EDE9FE"

    NOTIFICATION_DOT = "#DC2626"

    # Chart & Progress Bar Tokens
    CHART_BAR = "#6EA2F7"       # Batang bulan biasa pada grafik Pembelian per Bulan
    CHART_GRID = "#EEF2FA"      # Garis bantu horizontal grafik
    CHART_MONITOR = "#60A5FA"   # Kategori Monitor pada donut chart
    CHART_UPS = "#F59E0B"       # Kategori UPS pada donut chart
    CHART_OTHER = "#94A3B8"     # Kategori Lainnya pada donut chart

    PROGRESS_TRACK = "#E8EEF8"  # Latar belakang track progress bar
    PROGRESS_LOW = "#2563EB"    # Beban UPS < 70% (Biru)
    PROGRESS_MED = "#F59E0B"    # Beban UPS 70% - 85% (Amber)
    PROGRESS_HIGH = "#DC2626"   # Beban UPS > 85% (Merah)
