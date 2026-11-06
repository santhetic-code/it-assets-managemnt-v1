"""Skrip CLI untuk mengimpor seluruh data CSV operasional ke database (B9).

Pemakaian:
    python -m scripts.import_csv
"""

from sqlmodel import Session

from app.core.csv_importer import import_all_csv_data, resolve_data_dir
from app.core.db import get_engine


def main() -> None:
    data_dir = resolve_data_dir()
    print(f"[*] Menjalankan impor CSV idempoten dari direktori: {data_dir}")

    engine = get_engine()
    with Session(engine) as session:
        result = import_all_csv_data(session, data_dir=data_dir, username="cli_admin")
        data = result["data"]
        print(f"[+] Total data diimpor : {data['total_imported']}")
        print(f"    - UPS              : {data['ups_imported']}")
        print(f"    - Server           : {data['servers_imported']}")
        print(f"    - Alokasi IP       : {data['ips_imported']}")
        print(f"    - Rekap Pembelian  : {data['purchases_imported']}")
        print("[✓] Selesai.")


if __name__ == "__main__":
    main()
