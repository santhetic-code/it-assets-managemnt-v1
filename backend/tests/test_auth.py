from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jwt import InvalidTokenError
from sqlmodel import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.deps import AdminUserDep, CurrentUserDep, EditorUserDep, get_session
from app.models.user import User, UserRole


def _create_user(
    session: Session,
    username: str = "admin",
    password: str = "password123",
    role: UserRole = UserRole.ADMINISTRATOR,
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        full_name=f"User {username.capitalize()}",
        password_hash=hash_password(password),
        role=role.value,
        is_active=is_active,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_password_hash_and_verify() -> None:
    hashed = hash_password("rahasia123")
    assert hashed != "rahasia123"
    assert verify_password("rahasia123", hashed)
    assert not verify_password("salah", hashed)
    assert not verify_password("rahasia123", "hash-tidak-valid")


def test_jwt_create_and_decode() -> None:
    token = create_access_token(subject="admin", role=UserRole.ADMINISTRATOR.value)
    payload = decode_access_token(token)
    assert payload["sub"] == "admin"
    assert payload["role"] == "Administrator"


def test_jwt_expired_token_rejected() -> None:
    expired = create_access_token(
        subject="admin",
        role=UserRole.ADMINISTRATOR.value,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(expired)


def test_login_success_and_me_endpoint(client: TestClient, session: Session) -> None:
    _create_user(session, "admin", "password123", UserRole.ADMINISTRATOR)

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "Administrator"
    assert "password" not in res.text
    assert "password_hash" not in res.text

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"


def test_login_wrong_password_returns_401(client: TestClient, session: Session) -> None:
    _create_user(session, "admin", "password123", UserRole.ADMINISTRATOR)

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "salah"},
    )
    assert res.status_code == 401
    assert res.json() == {"detail": "Username atau password salah"}


def test_login_unknown_user_returns_401(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "tidakada", "password": "password123"},
    )
    assert res.status_code == 401
    assert res.json() == {"detail": "Username atau password salah"}


def test_login_inactive_user_returns_403(client: TestClient, session: Session) -> None:
    _create_user(session, "nonaktif", "password123", UserRole.MEMBER, is_active=False)

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "nonaktif", "password": "password123"},
    )
    assert res.status_code == 403
    assert res.json() == {"detail": "Akun pengguna tidak aktif"}


def test_me_without_or_invalid_token_returns_401(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer token-palsu"},
    )
    assert res.status_code == 401


def test_role_permissions_matrix(session: Session) -> None:
    admin = _create_user(session, "u_admin", "pw", UserRole.ADMINISTRATOR)
    member = _create_user(session, "u_member", "pw", UserRole.MEMBER)
    viewer = _create_user(session, "u_viewer", "pw", UserRole.VIEWER)

    rbac_app = FastAPI()
    rbac_app.dependency_overrides[get_session] = lambda: session

    @rbac_app.get("/only-admin")
    def _admin_ep(u: AdminUserDep) -> dict[str, str]:
        return {"user": u.username}

    @rbac_app.get("/editor")
    def _editor_ep(u: EditorUserDep) -> dict[str, str]:
        return {"user": u.username}

    @rbac_app.get("/viewer")
    def _viewer_ep(u: CurrentUserDep) -> dict[str, str]:
        return {"user": u.username}

    c = TestClient(rbac_app)
    t_admin = create_access_token(admin.username, admin.role)
    t_member = create_access_token(member.username, member.role)
    t_viewer = create_access_token(viewer.username, viewer.role)

    # Administrator boleh mengakses semua
    assert c.get("/only-admin", headers={"Authorization": f"Bearer {t_admin}"}).status_code == 200
    assert c.get("/editor", headers={"Authorization": f"Bearer {t_admin}"}).status_code == 200
    assert c.get("/viewer", headers={"Authorization": f"Bearer {t_admin}"}).status_code == 200

    # Member boleh editor dan viewer, tetapi ditolak (403) di only-admin
    assert c.get("/only-admin", headers={"Authorization": f"Bearer {t_member}"}).status_code == 403
    assert c.get("/editor", headers={"Authorization": f"Bearer {t_member}"}).status_code == 200
    assert c.get("/viewer", headers={"Authorization": f"Bearer {t_member}"}).status_code == 200

    # Viewer hanya boleh viewer, ditolak (403) di editor dan only-admin
    assert c.get("/only-admin", headers={"Authorization": f"Bearer {t_viewer}"}).status_code == 403
    assert c.get("/editor", headers={"Authorization": f"Bearer {t_viewer}"}).status_code == 403
    assert c.get("/viewer", headers={"Authorization": f"Bearer {t_viewer}"}).status_code == 200
