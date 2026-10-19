"""
Data Mock Autentikasi untuk pengembangan Frontend (USE_MOCK=true).
"""
from typing import Any

MOCK_USERS: dict[str, dict[str, Any]] = {
    "admin": {
        "password": "password123",
        "user": {
            "id": 1,
            "username": "admin",
            "full_name": "Admin IT",
            "role": "Administrator",
            "is_active": True,
        },
        "access_token": "mock-jwt-token-admin-itam-pro",
    },
    "member": {
        "password": "password123",
        "user": {
            "id": 2,
            "username": "member",
            "full_name": "Teknisi 1",
            "role": "Member",
            "is_active": True,
        },
        "access_token": "mock-jwt-token-member-itam-pro",
    },
    "viewer": {
        "password": "password123",
        "user": {
            "id": 3,
            "username": "viewer",
            "full_name": "Auditor Internal",
            "role": "Viewer",
            "is_active": True,
        },
        "access_token": "mock-jwt-token-viewer-itam-pro",
    },
}


def verify_mock_login(username: str, password: str) -> dict[str, Any] | None:
    """Verifikasi login menggunakan data mock."""
    record = MOCK_USERS.get(username.strip().lower())
    if not record or record["password"] != password:
        return None
    return {
        "access_token": record["access_token"],
        "token_type": "bearer",
        "user": record["user"],
    }
