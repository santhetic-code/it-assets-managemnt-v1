"""Modul rate limiting anti-brute-force untuk autentikasi login ITAM Pro."""

import threading
import time
from collections import defaultdict

# Konfigurasi batas percobaan login gagal
WINDOW_SECONDS = 60.0
MAX_FAILED_ATTEMPTS = 10

_lock = threading.Lock()
# Menyimpan riwayat percobaan gagal: key -> list timestamp detik
_failed_attempts: dict[str, list[float]] = defaultdict(list)


def _make_key(client_ip: str, username: str) -> str:
    """Membuat identitas unik rate limit berdasarkan kombinasi IP dan username."""
    clean_ip = client_ip.strip() or "127.0.0.1"
    clean_user = username.strip().lower()
    return f"{clean_ip}:{clean_user}"


def _prune_expired_attempts(timestamps: list[float], now: float) -> list[float]:
    """Menyaring timestamp percobaan yang masih berada dalam jendela waktu."""
    cutoff = now - WINDOW_SECONDS
    return [t for t in timestamps if t >= cutoff]


def is_login_rate_limited(client_ip: str, username: str) -> bool:
    """Memeriksa apakah percobaan login sedang diblokir sementara karena brute-force."""
    key = _make_key(client_ip, username)
    now = time.monotonic()
    with _lock:
        timestamps = _failed_attempts.get(key, [])
        active = _prune_expired_attempts(timestamps, now)
        if len(active) != len(timestamps):
            if active:
                _failed_attempts[key] = active
            else:
                _failed_attempts.pop(key, None)
        return len(active) >= MAX_FAILED_ATTEMPTS


def record_failed_login(client_ip: str, username: str) -> None:
    """Mencatat satu kegagalan login untuk IP dan username yang bersangkutan."""
    key = _make_key(client_ip, username)
    now = time.monotonic()
    with _lock:
        active = _prune_expired_attempts(_failed_attempts[key], now)
        active.append(now)
        _failed_attempts[key] = active


def clear_failed_login(client_ip: str, username: str) -> None:
    """Menghapus catatan kegagalan login saat pengguna berhasil login."""
    key = _make_key(client_ip, username)
    with _lock:
        _failed_attempts.pop(key, None)


def reset_login_rate_limiter() -> None:
    """Mengosongkan seluruh memori rate limiter (dipakai saat isolasi tes)."""
    with _lock:
        _failed_attempts.clear()
