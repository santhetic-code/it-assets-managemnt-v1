"""Konfigurasi terpusat backend ITAM Pro.

Semua nilai dibaca dari environment (di Docker lewat `env_file: .env`).
Untuk menjalankan tanpa Docker, file .env di root repo juga ikut dibaca.
"""

import base64
import binascii
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

DEFAULT_SECRET = "rahasia_ganti_di_produksi"
DEFAULT_DB_PASSWORD = "rahasia"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",  # variabel milik frontend (USE_MOCK, dll.) diabaikan
    )

    app_env: Literal["dev", "production"] = "dev"
    log_level: str = "INFO"

    jwt_secret_key: str = DEFAULT_SECRET
    fernet_master_key: str = DEFAULT_SECRET

    postgres_user: str = "itam"
    postgres_password: str = DEFAULT_DB_PASSWORD
    postgres_db: str = "itam"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Opsional: bila diisi, menggantikan rakitan POSTGRES_* (dipakai untuk tes/SQLite).
    database_url: str | None = None

    @field_validator("app_env", mode="before")
    @classmethod
    def _normalize_env(cls, value: object) -> object:
        return value.lower().strip() if isinstance(value, str) else value

    @field_validator("database_url", mode="before")
    @classmethod
    def _empty_url_is_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def sqlalchemy_url(self) -> URL:
        """URL database sebagai objek (aman untuk password berisi karakter khusus)."""
        if self.database_url:
            return make_url(self.database_url)
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @model_validator(mode="after")
    def _enforce_production_safety(self) -> "Settings":
        """Tolak start di production bila secret masih bawaan/lemah (meniru frontend)."""
        if not self.is_production:
            return self

        problems: list[str] = []
        if (
            self.jwt_secret_key.strip() == DEFAULT_SECRET
            or len(self.jwt_secret_key.strip()) < 32
        ):
            problems.append("JWT_SECRET_KEY kosong/bawaan/kurang dari 32 karakter")
        if not _is_valid_fernet_key(self.fernet_master_key):
            problems.append("FERNET_MASTER_KEY bukan kunci Fernet yang valid")
        if self.postgres_password.strip() in ("", DEFAULT_DB_PASSWORD):
            problems.append("POSTGRES_PASSWORD masih nilai bawaan")

        if problems:
            raise ValueError("Konfigurasi production tidak aman: " + "; ".join(problems))
        return self


def _is_valid_fernet_key(key: str) -> bool:
    """Kunci Fernet = base64 URL-safe dari tepat 32 byte (44 karakter)."""
    try:
        return len(base64.urlsafe_b64decode(key.strip().encode())) == 32
    except (binascii.Error, ValueError):
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()

