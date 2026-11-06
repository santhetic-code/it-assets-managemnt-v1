"""Cek endpoint backend dari dalam container (tanpa curl).

Pemakaian: python scripts/healthcheck.py /health
Exit code 0 bila HTTP 200, selain itu 1. Dipakai oleh healthcheck Docker.
"""

import sys
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8001"


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "/health"
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=5) as resp:
            print(resp.read().decode())
            return 0 if resp.status == 200 else 1
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read().decode()}")
        return 1
    except Exception as exc:
        print(f"GAGAL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
