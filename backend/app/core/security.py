"""Utilitas keamanan: hash password (bcrypt), token JWT (PyJWT), dan enkripsi Fernet."""

import base64
import binascii
import hashlib
import json
import os
from datetime import timedelta
from typing import Any

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.models.base import utcnow

MASKED_SECRET_DISPLAY = "••••••••"
AES_GCM_PREFIX = "aes256gcm"
CURRENT_KEY_VERSION = 1


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


def _derive_aes256_key(version: int = CURRENT_KEY_VERSION) -> bytes:
    """Menurunkan kunci 32-byte (256-bit) untuk AES-256-GCM dari environment/settings (B)."""
    settings = get_settings()
    env_key = os.getenv(f"CREDENTIAL_AES_KEY_V{version}") or os.getenv("CREDENTIAL_AES_KEY")
    raw_material = (env_key or settings.fernet_master_key).strip().encode("utf-8")
    return hashlib.sha256(raw_material + f":v{version}".encode()).digest()


def encrypt_aes256_gcm(plain_text: str, key_version: int = CURRENT_KEY_VERSION) -> str:
    """Enkripsi string rahasia menggunakan AES-256-GCM dengan nonce acak 12-byte per field (B)."""
    if not plain_text:
        return ""
    nonce = os.urandom(12)
    aesgcm = AESGCM(_derive_aes256_key(key_version))
    ct = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    b64_payload = base64.urlsafe_b64encode(nonce + ct).decode("ascii")
    return f"{AES_GCM_PREFIX}:v{key_version}:{b64_payload}"


def decrypt_aes256_gcm(cipher_text: str) -> str:
    """Dekripsi token AES-256-GCM (atau fallback ke Fernet untuk data lama) (B)."""
    if not cipher_text:
        return ""
    if not cipher_text.startswith(f"{AES_GCM_PREFIX}:"):
        return decrypt_secret(cipher_text)
    try:
        parts = cipher_text.split(":", 2)
        ver_str = parts[1].lstrip("v")
        version = int(ver_str) if ver_str.isdigit() else CURRENT_KEY_VERSION
        raw = base64.urlsafe_b64decode(parts[2].encode("ascii"))
        nonce, ct = raw[:12], raw[12:]
        aesgcm = AESGCM(_derive_aes256_key(version))
        return aesgcm.decrypt(nonce, ct, None).decode("utf-8")
    except Exception as exc:
        raise ValueError("Data rahasia AES-256-GCM gagal didekripsi") from exc


def encrypt_secret_dict(
    secret_map: dict[str, Any],
    key_version: int = CURRENT_KEY_VERSION,
) -> str:
    """Enkripsi setiap field rahasia dengan nonce unik per field lalu bungkus dengan AES-256-GCM."""
    per_field_encrypted: dict[str, str] = {}
    for k, v in (secret_map or {}).items():
        val_str = str(v or "").strip()
        if val_str and val_str != MASKED_SECRET_DISPLAY:
            per_field_encrypted[k] = encrypt_aes256_gcm(val_str, key_version=key_version)
    if not per_field_encrypted:
        return ""
    raw_json = json.dumps(per_field_encrypted, ensure_ascii=False)
    return encrypt_aes256_gcm(raw_json, key_version=key_version)


def decrypt_secret_dict(cipher_blob: str) -> dict[str, str]:
    """Dekripsi payload data_rahasia kembali menjadi dictionary {field_key: plain_value}."""
    if not cipher_blob:
        return {}
    outer_json = decrypt_aes256_gcm(cipher_blob)
    try:
        parsed = json.loads(outer_json)
    except Exception:
        return {"password": outer_json}
    if not isinstance(parsed, dict):
        return {}
    result: dict[str, str] = {}
    for k, enc_v in parsed.items():
        if isinstance(enc_v, str) and enc_v:
            result[k] = decrypt_aes256_gcm(enc_v)
    return result
