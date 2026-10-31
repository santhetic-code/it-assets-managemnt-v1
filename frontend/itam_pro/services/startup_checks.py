"""
Pemeriksaan Kesehatan Pra-Booting ITAM Pro (0.2).
"""
import os
import sys

from itam_pro.config import APP_ENV, USE_MOCK


def format_fatal_message(msg: str) -> str:
    """Format pesan kesalahan fatal agar seragam."""
    return (
        f"\n\n====================\n"
        f"FATAL ERROR (STARTUP)\n"
        f"====================\n"
        f"{msg}\n"
        f"====================\n\n"
    )


def validate_production_env() -> None:
    """Tolak aplikasi berjalan di produksi bila lingkungan belum aman."""
    if APP_ENV != "production":
        return

    if USE_MOCK:
        print(
            format_fatal_message(
                "DILARANG menjalankan aplikasi di lingkungan production dengan "
                "USE_MOCK=true. Harap matikan mode mock dan sambungkan ke database nyata."
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    jwt_secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not jwt_secret or jwt_secret == "rahasia_ganti_di_produksi" or len(jwt_secret) < 32:
        print(
            format_fatal_message(
                "JWT_SECRET_KEY kosong, masih bawaan, atau kurang dari 32 karakter "
                "di mode production."
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    fernet_key = os.getenv("FERNET_MASTER_KEY", "").strip()
    # Kunci fernet yang valid adalah URL-safe base64-encoded sepanjang 32 byte (44 karakter teks)
    if (
        not fernet_key
        or fernet_key == "rahasia_ganti_di_produksi"
        or len(fernet_key) != 44
    ):
        print(
            format_fatal_message(
                "FERNET_MASTER_KEY tidak valid (harus kunci Fernet 44-karakter "
                "URL-safe base64) di mode production."
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    db_pass = os.getenv("POSTGRES_PASSWORD", "").strip()
    if not db_pass or db_pass == "rahasia":
        print(
            format_fatal_message(
                "POSTGRES_PASSWORD masih menggunakan nilai bawaan (rahasia)."
            ),
            file=sys.stderr,
        )
        sys.exit(1)


__all__ = ["format_fatal_message", "validate_production_env"]

