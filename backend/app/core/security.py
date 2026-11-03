"""Utilitas keamanan: hash password (bcrypt), token JWT (PyJWT), dan enkripsi Fernet."""

import base64
import binascii
import hashlib
from datetime import timedelta
from typing import Any

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.models.base import utcnow

MASKED_SECRET_DISPLAY = "••••••••"


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


def _derive_fernet_key(raw_key: str) -> bytes:
    """Mengambil kunci Fernet 32-byte base64, atau menurunkan via SHA-256 untuk mode dev."""
    cleaned = raw_key.strip().encode("utf-8")
    try:
        decoded = base64.urlsafe_b64decode(cleaned)
        if len(decoded) == 32:
            return cleaned
    except (binascii.Error, ValueError):
        pass
    digest = hashlib.sha256(cleaned).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    """Mengembalikan instance Fernet berdasarkan FERNET_MASTER_KEY aktif."""
    settings = get_settings()
    return Fernet(_derive_fernet_key(settings.fernet_master_key))


def encrypt_secret(plain_secret: str) -> str:
    """Mengenkripsi string rahasia menjadi token Fernet (ciphertext UTF-8)."""
    if not plain_secret:
        return ""
    token = get_fernet().encrypt(plain_secret.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(cipher_secret: str) -> str:
    """Mendekripsi token Fernet kembali menjadi string rahasia asli."""
    if not cipher_secret:
        return ""
    try:
        plain = get_fernet().decrypt(cipher_secret.encode("utf-8"))
        return plain.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Data kredensial gagal didekripsi dengan kunci aktif") from exc


def mask_secret(value: str | None = None) -> str:
    """Mengembalikan tampilan tersamar standar untuk respons non-reveal."""
    return MASKED_SECRET_DISPLAY
