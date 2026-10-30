"""
Konfigurasi lingkungan terpusat ITAM Pro.
Satu-satunya tempat yang memanggil load_dotenv() dan memvalidasi APP_ENV/USE_MOCK.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

_raw_env = os.getenv("APP_ENV", "dev").lower().strip()

# Validasi nilai APP_ENV secara ketat
if _raw_env not in ["dev", "production"]:
    print(
        f"FATAL ERROR: Nilai APP_ENV='{_raw_env}' tidak valid. Harus 'dev' atau 'production'.",
        file=sys.stderr,
    )
    sys.exit(1)

APP_ENV = _raw_env
USE_MOCK = os.getenv("USE_MOCK", "true").lower().strip() == "true"


def validate_production_env():
    if APP_ENV == "production" and USE_MOCK:
        print(
            "FATAL ERROR: DILARANG menjalankan aplikasi di lingkungan production "
            "dengan USE_MOCK=true. Harap sambungkan ke database nyata.",
            file=sys.stderr,
        )
        sys.exit(1)


validate_production_env()

__all__ = ["APP_ENV", "USE_MOCK", "validate_production_env"]
