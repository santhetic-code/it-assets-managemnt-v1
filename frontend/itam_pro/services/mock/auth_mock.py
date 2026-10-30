"""Data Mock Autentikasi untuk pengembangan Frontend (USE_MOCK=true)."""
from typing import Any

MOCK_CREDENTIAL_PERMISSIONS: dict[str, dict[str, str]] = {
    "admin": {
        k: "edit"
        for k in [
            "website",
            "detail_pc",
            "sql_server",
            "mikrotik",
            "internet_kantor",
            "email",
            "sosmed",
            "lainnya",
        ]
    },
    "member": {
        "website": "reveal",
        "mikrotik": "view",
    },
    "viewer": {},
}

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
        "access_token": "mock-token-admin",
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
        "access_token": "mock-token-member",
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
        "access_token": "mock-token-viewer",
    },
}


def verify_mock_login(username: str, password: str) -> dict[str, Any] | None:
    """Verifikasi login menggunakan data mock."""
    uname = username.strip().lower()
    record = MOCK_USERS.get(uname)
    if not record or record["password"] != password:
        return None

    permissions = MOCK_CREDENTIAL_PERMISSIONS.get(uname, {})
    return {
        "token": record["access_token"],
        "access_token": record["access_token"],
        "token_type": "bearer",
        "user": record["user"],
        "credential_permissions": permissions,
    }
