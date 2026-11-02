"""Utilitas keamanan: hash password (bcrypt) dan token JWT (PyJWT)."""

from datetime import timedelta
from typing import Any

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.models.base import utcnow


def hash_password(plain_password: str) -> str:
    """Menghasilkan hash bcrypt dari password teks biasa."""
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memeriksa kecocokan password teks biasa dengan hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Membuat JWT access token dengan klaim sub (username), role, iat, dan exp."""
    settings = get_settings()
    now = utcnow()
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Membaca dan memvalidasi JWT access token. Menaikkan InvalidTokenError bila tidak sah."""
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    if not isinstance(payload, dict) or not payload.get("sub"):
        raise InvalidTokenError("Payload token tidak memiliki sub")
    return payload

