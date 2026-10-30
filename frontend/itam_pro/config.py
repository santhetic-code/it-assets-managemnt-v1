"""
Konfigurasi lingkungan terpusat ITAM Pro.
Satu-satunya tempat yang memanggil load_dotenv() dan memvalidasi APP_ENV/USE_MOCK.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "dev").lower()
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

if APP_ENV == "production" and USE_MOCK:
    print(
        "FATAL ERROR: DILARANG menjalankan aplikasi di lingkungan production "
        "dengan USE_MOCK=true. Harap sambungkan ke database nyata.",
        file=sys.stderr,
    )
    sys.exit(1)

__all__ = ["APP_ENV", "USE_MOCK"]
