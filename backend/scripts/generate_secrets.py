"""Generator kredensial & rahasia produksi ITAM Pro (B9).

Menghasilkan JWT_SECRET_KEY, FERNET_MASTER_KEY, dan POSTGRES_PASSWORD
yang memenuhi standar keamanan produksi.

Pemakaian:
    python -m scripts.generate_secrets
"""

import secrets

from cryptography.fernet import Fernet


def generate_production_secrets() -> dict[str, str]:
    """Menghasilkan kunci dan rahasia produksi acak berstandar keamanan tinggi."""
    jwt_secret = secrets.token_urlsafe(48)
    fernet_key = Fernet.generate_key().decode()
    db_password = secrets.token_urlsafe(24)

    # Validasi ketat terhadap rahasia yang dihasilkan
    if len(jwt_secret) < 32:
        raise ValueError("JWT_SECRET_KEY terlalu pendek")
    # Memastikan kunci Fernet valid
    Fernet(fernet_key.encode())

    return {
        "JWT_SECRET_KEY": jwt_secret,
        "FERNET_MASTER_KEY": fernet_key,
        "POSTGRES_PASSWORD": db_password,
    }


def main() -> None:
    sec = generate_production_secrets()
    print("=" * 60)
    print(" ITAM PRO - KUNCI & RAHASIA PRODUKSI GENERATED")
    print("=" * 60)
    print(f"JWT_SECRET_KEY={sec['JWT_SECRET_KEY']}")
    print(f"FERNET_MASTER_KEY={sec['FERNET_MASTER_KEY']}")
    print(f"POSTGRES_PASSWORD={sec['POSTGRES_PASSWORD']}")
    print("=" * 60)
    print("[!] Simpan nilai di atas pada berkas .env produksi.")


if __name__ == "__main__":
    main()

