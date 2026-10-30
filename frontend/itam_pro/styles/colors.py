"""
Token Warna Semantik ITAM Pro (Single Source of Truth).
Dilarang menggunakan nilai hex atau rgba secara langsung di luar modul styles/.
"""


class Color:
    # Brand & Primary Accent
    ACCENT = "#1D4ED8"
    ACCENT_BRIGHT = "#2563EB"
    BRAND = "#1340C7"
    INFO_FG = "#1D4ED8"
    INFO_BG = "#EFF6FF"
    FOCUS_RING = "0 0 0 3px rgba(29, 78, 216, 0.15)"

    # Sidebar
    SIDEBAR = "#0A1A44"
    SIDEBAR_TEXT = "#C7D4F5"
    SIDEBAR_MUTED = "#8EA3D6"
    SIDEBAR_HOVER = "rgba(255, 255, 255, 0.06)"
    SIDEBAR_HOVER_BG = "rgba(255, 255, 255, 0.06)"
    SIDEBAR_BADGE_BG = "rgba(255, 255, 255, 0.08)"
    SIDEBAR_BADGE_ACTIVE_BG = "rgba(255, 255, 255, 0.22)"
    SIDEBAR_DIVIDER = "rgba(255, 255, 255, 0.08)"

    # Login Page & Ornaments
    LOGIN_BG = "#DCE6FB"
    DECOR_RING = "#CBDAF9"
    DECOR_CIRCLE = "#C7D7F8"
    WHITE = "#FFFFFF"
    WHITE_ALPHA_06 = "rgba(255, 255, 255, 0.06)"
    WHITE_ALPHA_14 = "rgba(255, 255, 255, 0.14)"
    WHITE_ALPHA_16 = "rgba(255, 255, 255, 0.16)"
    WHITE_ALPHA_20 = "rgba(255, 255, 255, 0.20)"
    WHITE_ALPHA_72 = "rgba(255, 255, 255, 0.72)"
    WHITE_ALPHA_75 = "rgba(255, 255, 255, 0.75)"
    WHITE_14 = "rgba(255, 255, 255, 0.14)"
    WHITE_75 = "rgba(255, 255, 255, 0.75)"
    WHITE_85 = "rgba(255, 255, 255, 0.85)"

    # Surfaces & Borders
    BG = "#F2F5FB"
    SURFACE = "#FFFFFF"
    SURFACE_HOVER = "#F8FAFC"
    TABLE_HEADER_BG = "#F7F9FD"
    ROW_HOVER = "#F7F9FD"
    ROW_SELECTED = "#EEF3FF"
    CONFLICT_ROW_BG = "#FEF2F2"
    BORDER = "#E1E8F5"
    DIVIDER = "#EEF2F9"
    INPUT_BORDER = "#D5DEEE"
    SKELETON = "#E2E8F0"
    SCRIM = "rgba(10, 26, 68, 0.35)"
    OVERLAY_BACKDROP = "rgba(10, 26, 68, 0.45)"
    SEARCH_BG = "#F6F8FC"

    # Typography
    TEXT = "#0F1B3D"
    MUTED = "#55627F"

    # Semantic Status & Badges
    SUCCESS_FG = "#15803D"
    SUCCESS_BG = "#DCFCE7"
    BACKUP_FG = "#1E40AF"
    BACKUP_BG = "#DBEAFE"
    WARNING_FG = "#92400E"
    WARNING_BG = "#FEF3C7"
    WARNING_BAR = "#F59E0B"
    DANGER_FG = "#B91C1C"
    DANGER_BG = "#FEE2E2"
    DANGER_BAR = "#DC2626"
    NEUTRAL_FG = "#475569"
    NEUTRAL_BG = "#F1F5F9"
    PURPLE_FG = "#6D28D9"
    PURPLE_BG = "#EDE9FE"
    NOTIFICATION_DOT = "#DC2626"

    # Chart & Progress Bar Tokens
    CHART_BAR = "#6EA2F7"
    CHART_GRID = "#EEF2FA"
    CHART_MONITOR = "#60A5FA"
    CHART_UPS = "#F59E0B"
    CHART_OTHER = "#94A3B8"
    PROGRESS_TRACK = "#E8EEF8"
    PROGRESS_LOW = "#2563EB"
    PROGRESS_MED = "#F59E0B"
    PROGRESS_HIGH = "#DC2626"

    # Common UI & Neutral Palette
    GRAY_100 = "#F3F4F6"
    GRAY_200 = "#E5E7EB"
    BLUE_500 = "#3B82F6"


__all__ = ["Color"]
