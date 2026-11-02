import base64

import pytest
from pydantic import ValidationError

from app.core.config import Settings

STRONG_JWT = "a" * 40
# Kunci Fernet valid = base64 URL-safe dari 32 byte (tanpa perlu paket cryptography)
VALID_FERNET_KEY = base64.urlsafe_b64encode(b"0" * 32).decode()


def make(**kwargs: object) -> Settings:
    return Settings(_env_file=None, **kwargs)  # type: ignore[arg-type]


def test_defaults_are_dev() -> None:
    s = make()
    assert s.app_env == "dev"
    assert not s.is_production


def test_app_env_is_normalized() -> None:
    assert make(
        app_env=" Production ",
        jwt_secret_key=STRONG_JWT,
        fernet_master_key=VALID_FERNET_KEY,
        postgres_password="x" * 12,
    ).is_production


def test_invalid_app_env_rejected() -> None:
    with pytest.raises(ValidationError):
        make(app_env="staging")


def test_database_url_built_from_parts_and_hides_password() -> None:
    s = make(
        postgres_user="u",
        postgres_password="p@ss:w/rd",
        postgres_db="d",
        postgres_host="db",
        postgres_port=5432,
    )
    url = s.sqlalchemy_url
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss:w/rd"
    assert "p@ss" not in url.render_as_string(hide_password=True)


def test_database_url_override_and_blank_is_ignored() -> None:
    assert make(database_url="sqlite://").sqlalchemy_url.drivername == "sqlite"
    assert make(database_url="  ").sqlalchemy_url.drivername == "postgresql+psycopg"


@pytest.mark.parametrize(
    "overrides",
    [
        {},  # semua masih bawaan
        {
            "jwt_secret_key": "pendek",
            "fernet_master_key": VALID_FERNET_KEY,
            "postgres_password": "kuat-sekali-123",
        },
        {
            "jwt_secret_key": STRONG_JWT,
            "fernet_master_key": "bukan-kunci-fernet",
            "postgres_password": "kuat-sekali-123",
        },
        {
            "jwt_secret_key": STRONG_JWT,
            "fernet_master_key": VALID_FERNET_KEY,
            "postgres_password": "rahasia",
        },
    ],
)
def test_production_rejects_unsafe_config(overrides: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        make(app_env="production", **overrides)


def test_production_accepts_safe_config() -> None:
    s = make(
        app_env="production",
        jwt_secret_key=STRONG_JWT,
        fernet_master_key=VALID_FERNET_KEY,
        postgres_password="kuat-sekali-123",
    )
    assert s.is_production

