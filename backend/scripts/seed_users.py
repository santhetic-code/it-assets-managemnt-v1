"""Seeder pengguna awal ITAM Pro (idempoten).

Pemakaian di dalam container:
    python -m scripts.seed_users
"""

from sqlmodel import Session, select

from app.core.db import get_engine
from app.core.security import hash_password
from app.models.user import User, UserRole

INITIAL_USERS: list[tuple[str, str, str, UserRole]] = [
    ("admin", "Administrator IT", "password123", UserRole.ADMINISTRATOR),
    ("member", "Staf IT Support", "password123", UserRole.MEMBER),
    ("viewer", "Auditor Internal", "password123", UserRole.VIEWER),
]


def seed_initial_users(session: Session) -> int:
    """Menambahkan pengguna awal bila belum ada. Mengembalikan jumlah user baru."""
    created_count = 0
    for username, full_name, plain_password, role in INITIAL_USERS:
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing is None:
            session.add(
                User(
                    username=username,
                    full_name=full_name,
                    password_hash=hash_password(plain_password),
                    role=role.value,
                    is_active=True,
                )
            )
            created_count += 1
    session.commit()
    return created_count


def main() -> None:
    with Session(get_engine()) as session:
        added = seed_initial_users(session)
        print(f"Seed pengguna selesai ({added} pengguna baru ditambahkan).")


if __name__ == "__main__":
    main()

