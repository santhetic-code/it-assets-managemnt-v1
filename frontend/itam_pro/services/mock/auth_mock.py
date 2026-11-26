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


# TODO(backend): ganti MOCK_ACTIVE_SESSIONS dengan endpoint GET/DELETE /api/v1/auth/sessions.
MOCK_ACTIVE_SESSIONS: dict[str, list[dict[str, Any]]] = {
    "admin": [
        {
            "id": "SES-ADMIN-01",
            "device": "Chrome · Windows",
            "ip_address": "192.168.1.111",
            "last_active": "aktif sekarang",
            "is_current": True,
        },
        {
            "id": "SES-ADMIN-02",
            "device": "Firefox · Linux",
            "ip_address": "10.20.5.19",
            "last_active": "aktif 2 jam lalu",
            "is_current": False,
        },
    ],
    "member": [
        {
            "id": "SES-MEM-01",
            "device": "Chrome · Windows",
            "ip_address": "10.20.5.41",
            "last_active": "aktif sekarang",
            "is_current": True,
        }
    ],
    "viewer": [
        {
            "id": "SES-VWR-01",
            "device": "Edge · Windows",
            "ip_address": "10.20.5.52",
            "last_active": "aktif sekarang",
            "is_current": True,
        }
    ],
}


def get_mock_active_sessions(username: str) -> list[dict[str, Any]]:
    """Ambil daftar sesi aktif mock milik pengguna."""
    uname = username.strip().lower()
    sessions = MOCK_ACTIVE_SESSIONS.get(uname)
    if sessions:
        return [dict(s) for s in sessions]
    return [
        {
            "id": f"SES-{uname.upper()}-01",
            "device": "Chrome · Windows",
            "ip_address": "127.0.0.1",
            "last_active": "aktif sekarang",
            "is_current": True,
        }
    ]


def revoke_other_mock_sessions(username: str) -> int:
    """Keluarkan seluruh sesi selain sesi aktif saat ini. Kembalikan jumlah sesi dicabut."""
    uname = username.strip().lower()
    sessions = MOCK_ACTIVE_SESSIONS.get(uname, [])
    kept = [s for s in sessions if s.get("is_current")]
    removed = len(sessions) - len(kept)
    MOCK_ACTIVE_SESSIONS[uname] = kept
    return removed


def toggle_mock_user_active(username: str) -> tuple[bool, str]:
    """Aktifkan/nonaktifkan pengguna dengan guard Administrator aktif terakhir."""
    uname = username.strip().lower()
    rec = MOCK_USERS.get(uname)
    if not rec:
        return (False, "Pengguna tidak ditemukan.")
    user = rec["user"]
    currently_active = bool(user.get("is_active", True))
    if currently_active and str(user.get("role", "")).lower() == "administrator":
        active_admins = sum(
            1
            for item in MOCK_USERS.values()
            if item["user"].get("is_active", True)
            and str(item["user"].get("role", "")).lower() == "administrator"
        )
        if active_admins <= 1:
            return (False, "Administrator aktif terakhir tidak boleh dinonaktifkan.")
    user["is_active"] = not currently_active
    status_lbl = "diaktifkan" if user["is_active"] else "dinonaktifkan"
    return (True, f"Akun '{uname}' berhasil {status_lbl}.")
