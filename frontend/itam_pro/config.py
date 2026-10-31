"""
Konfigurasi Lingkungan Global ITAM Pro.
"""
import os

from dotenv import load_dotenv

# Hanya panggil dotenv satu kali di seluruh aplikasi
load_dotenv()

_raw_env = os.getenv("APP_ENV", "dev").lower().strip()
APP_ENV = _raw_env if _raw_env in ["dev", "production"] else "dev"
USE_MOCK = os.getenv("USE_MOCK", "true").lower().strip() == "true"

__all__ = ["APP_ENV", "USE_MOCK"]
