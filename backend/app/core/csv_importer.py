"""Mesin impor data CSV idempoten untuk data operasional ITAM Pro (B9).

Mengimpor data nyata dari folder docs/data/:
1. rekap_ups_xml.csv -> tabel assets (kategori UPS)
2. rekap_watt_server.csv -> tabel assets (kategori Server)
3. ip_list_xml.csv -> tabel ip_allocations (IP Server, Addon/VM, Operasional)
4. rekap_pembelian.csv -> tabel purchases (Rekap Pembelian Aset/Perangkat)
"""

import csv
import io
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, col, select

from app.core.master_data import LOCATION_ALIASES, LOCATIONS
from app.models.asset import Asset
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation
from app.schemas.audit import record_audit_log
from app.schemas.ip_allocation import parse_and_validate_ipv4

logger = logging.getLogger(__name__)


def resolve_data_dir(custom_path: Path | str | None = None) -> Path:
    """Menemukan lokasi folder docs/data baik di lokal maupun container Docker."""
    if custom_path is not None:
        p = Path(custom_path)
        if p.exists():
            return p

    candidates = [
        Path.cwd() / "docs" / "data",
        Path(__file__).resolve().parent.parent.parent.parent / "docs" / "data",
        Path(__file__).resolve().parent.parent.parent / "docs" / "data",
        Path("/app/docs/data"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return Path.cwd() / "docs" / "data"


def _read_csv_rows(file_path: Path) -> list[dict[str, str]]:
    """Membaca baris CSV menjadi list dictionary dengan toleransi baris kosong & delimiter."""
    if not file_path.exists():
        logger.warning("File CSV tidak ditemukan: %s", file_path)
        return []

    with file_path.open("r", encoding="utf-8-sig", errors="replace") as f:
        raw_lines = f.readlines()

    header_idx = -1
    for idx, line in enumerate(raw_lines):
        clean = line.strip().replace(",", "").replace(";", "")
        if clean:
            header_idx = idx
            break

    if header_idx == -1:
        return []

    content = "".join(raw_lines[header_idx:])
    first_line = raw_lines[header_idx]
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows: list[dict[str, str]] = []
    for r in reader:
        clean_row = {
            (k.strip() if k else ""): (v.strip() if isinstance(v, str) else "")
            for k, v in r.items()
            if k is not None
        }
        if any(clean_row.values()):
            rows.append(clean_row)
    return rows


def _parse_int(val: Any) -> int:
    """Mengekstrak angka integer dari teks (contoh: '650 VA', '450W', '1.500.000')."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    text = str(val).strip()
    if not text:
        return 0
    # Ambil bagian sebelum koma desimal jika ada
    if "," in text and "." not in text:
        text = text.split(",")[0]
    digits = re.sub(r"[^\d-]", "", text)
    try:
        return int(digits)
    except ValueError:
        return 0


def _parse_rupiah(val: Any) -> int:
    """Membersihkan format Rupiah ('Rp 1.500.000', 'Rp77.500,00') menjadi angka bulat."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    text = str(val).strip()
    if not text:
        return 0
    # Hilangkan awalan Rp/IDR
    text = re.sub(r"^(?:Rp|rp|IDR|idr)\.?\s*", "", text)
    # Jika berakhiran ,00 atau desimal, buang bagian desimalnya
    if "," in text:
        parts = text.rsplit(",", 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) in (1, 2):
            text = parts[0]
    # Hapus pemisah ribuan titik
    cleaned = text.replace(".", "").replace(" ", "")
    digits = re.sub(r"[^\d-]", "", cleaned)
    try:
        return int(digits)
    except ValueError:
        return 0


def _parse_date(val: Any) -> date | None:
    """Mengonversi teks tanggal berbagai format (DD/MM/YYYY, YYYY-MM-DD, dsb.) ke date."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    text = str(val).strip()
    if not text:
        return None

    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_loc(val: str | None) -> str:
    """Menyesuaikan nama lokasi dengan standar LOCATIONS perusahaan."""
    cleaned = (val or "").strip()
    if not cleaned:
        return "Head Office (Office Blok 14)"
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc
    if cleaned.lower() in LOCATION_ALIASES:
        return LOCATION_ALIASES[cleaned.lower()]
    return "Head Office (Office Blok 14)"


def import_ups_csv(session: Session, file_path: Path) -> int:
    """Mengimpor data UPS dari rekap_ups_xml.csv secara idempoten."""
    rows = _read_csv_rows(file_path)
    imported_count = 0

    for row in rows:
        raw_id = row.get("ID UPS", "").strip()
        if not raw_id:
            continue
        # Format id_aset bersih (misal: 'UPS - 001' -> 'UPS-001')
        id_aset = re.sub(r"\s+", "", raw_id)

        # Cek idempotensi
        existing = session.exec(select(Asset).where(col(Asset.id_aset) == id_aset)).first()
        if existing is not None:
            continue

        merk = row.get("MERK UPS", "").strip()
        kategori_aki = row.get("KATEGORI AKI", "").strip()
        kapasitas_val = _parse_int(row.get("KAPASITAS (VA/WATT)", ""))
        status_ops = row.get("STATUS OPERASIONAL", "").strip().upper()
        id_server = row.get("ID SERVER", "").strip()
        keterangan = row.get("KETERANGAN", "").strip()

        status_aset = "Aktif" if status_ops == "DIGUNAKAN" else (
            "Cadangan" if status_ops == "BACKUP" else "Aktif"
        )
        beban = id_server if id_server and id_server != "BACKUP" else ""
        jumlah_aki = 2 if "DUAL" in kategori_aki.upper() else (
            1 if "SATU" in kategori_aki.upper() else 0
        )
        nama_aset = (
            f"UPS {merk} {kapasitas_val}VA"
            if merk and kapasitas_val
            else f"UPS {merk or id_aset}"
        )

        asset = Asset(
            id_aset=id_aset,
            nama_aset=nama_aset,
            kategori="UPS",
            merek=merk,
            model=kategori_aki,
            lokasi="Head Office (Office Blok 14)",
            detail_lokasi="Server Room",
            penanggung_jawab="IT Infrastructure",
            status=status_aset,
            kondisi="Baik",
            kapasitas_va=kapasitas_val,
            kapasitas_watt=int(kapasitas_val * 0.6) if kapasitas_val else 0,
            baterai=kategori_aki,
            jumlah_baterai=jumlah_aki,
            beban_perangkat=beban,
            catatan=f"Status: {keterangan}. Terhubung: {id_server}".strip(),
        )
        session.add(asset)
        imported_count += 1

    if imported_count > 0:
        session.commit()
    return imported_count


def import_watt_server_csv(session: Session, file_path: Path) -> int:
    """Mengimpor data Server dari rekap_watt_server.csv secara idempoten."""
    rows = _read_csv_rows(file_path)
    imported_count = 0

    # Ambil nomor urut server tertinggi yang sudah ada di database
    existing_srvs = session.exec(
        select(Asset.id_aset).where(col(Asset.id_aset).like("SRV-%"))
    ).all()
    max_num = 0
    for srv_id in existing_srvs:
        m = re.match(r"^SRV-(\d+)$", srv_id)
        if m:
            max_num = max(max_num, int(m.group(1)))

    for row in rows:
        id_server_raw = row.get("ID SERVER", "").strip()
        if not id_server_raw or id_server_raw.upper().startswith("ESTIMASI"):
            continue

        # Cek idempotensi berdasarkan nama aset
        existing = session.exec(
            select(Asset).where(col(Asset.nama_aset) == id_server_raw)
        ).first()
        if existing is not None:
            continue

        max_num += 1
        new_id_aset = f"SRV-{max_num:03d}"

        cpu = row.get("MODEL PROSESOR (CPU)", "").strip()
        gpu = row.get("KARTU GRAFIS (GPU)", "").strip()
        ram = row.get("KONFIGURASI RAM", "").strip()
        storage = row.get("KONFIGURASI PENYIMPANAN", "").strip()
        watt = _parse_int(row.get("TOTAL TDP (W)", "0"))
        psu_min = _parse_int(row.get("PSU MINIMUM (W)", "0"))
        psu_rek = _parse_int(row.get("PSU REKOMENDASI (W)", "0"))

        asset = Asset(
            id_aset=new_id_aset,
            nama_aset=id_server_raw,
            kategori="Server",
            merek="Rakitan Server",
            model="Rackmount / Desktop Server",
            lokasi="Head Office (Office Blok 14)",
            detail_lokasi="Server Room",
            penanggung_jawab="IT Infrastructure",
            status="Aktif",
            kondisi="Baik",
            processor=cpu,
            gpu=gpu,
            ram=ram,
            storage=storage,
            watt=watt,
            extra_specs={
                "psu_minimum_watt": psu_min,
                "psu_rekomendasi_watt": psu_rek,
            },
            catatan=f"Spesifikasi daya: TDP {watt}W (Min PSU {psu_min}W, Rekomendasi {psu_rek}W)",
        )
        session.add(asset)
        imported_count += 1

    if imported_count > 0:
        session.commit()
    return imported_count


def import_ip_list_csv(session: Session, file_path: Path) -> int:
    """Mengimpor entri IP dari ip_list_xml.csv (Server, Addon/VM, Operasional) secara idempoten."""
    if not file_path.exists():
        logger.warning("File IP list tidak ditemukan: %s", file_path)
        return 0

    with file_path.open("r", encoding="utf-8-sig", errors="replace") as f:
        reader = list(csv.reader(f))

    if len(reader) < 3:
        return 0

    imported_count = 0
    # Baris data dimulai dari indeks 2 (baris ke-3)
    for row in reader[2:]:
        # 1. Kolom 0-1: SERVER
        if len(row) > 1:
            name_server = row[0].strip()
            ip_server = row[1].strip()
            if ip_server:
                try:
                    canon_ip, ip_int = parse_and_validate_ipv4(ip_server)
                    existing = session.exec(
                        select(IPAllocation).where(col(IPAllocation.ip_address) == canon_ip)
                    ).first()
                    if existing is None:
                        session.add(
                            IPAllocation(
                                ip_address=canon_ip,
                                ip_int=ip_int,
                                subnet="255.255.255.0",
                                gateway="192.168.1.1",
                                nama_perangkat=f"Server {name_server}".strip(),
                                hostname=name_server.lower().replace(" ", "-"),
                                tipe="Fisik",
                                status="Aktif",
                                lokasi="Head Office (Office Blok 14)",
                                pengguna="IT Server",
                                keterangan="Diimpor dari daftar IP Server",
                            )
                        )
                        imported_count += 1
                except ValueError:
                    pass

        # 2. Kolom 3-5: ADDON / VM
        if len(row) > 5:
            addon_host = row[3].strip()
            addon_desc = row[4].strip()
            addon_ip = row[5].strip()
            if addon_ip:
                try:
                    canon_ip, ip_int = parse_and_validate_ipv4(addon_ip)
                    existing = session.exec(
                        select(IPAllocation).where(col(IPAllocation.ip_address) == canon_ip)
                    ).first()
                    if existing is None:
                        session.add(
                            IPAllocation(
                                ip_address=canon_ip,
                                ip_int=ip_int,
                                subnet="255.255.255.0",
                                gateway="192.168.1.1",
                                nama_perangkat=f"Addon {addon_host}".strip(),
                                hostname=addon_host.lower().replace(" ", "-"),
                                tipe="Virtual",
                                status="Aktif",
                                lokasi="Head Office (Office Blok 14)",
                                is_vm=True,
                                host_name=addon_host,
                                keterangan=addon_desc.replace("\n", ", "),
                                pengguna="IT System",
                            )
                        )
                        imported_count += 1
                except ValueError:
                    pass

        # 3. Kolom 7-8: OPERASIONAL / USER
        if len(row) > 8:
            user_name = row[7].strip()
            user_ip = row[8].strip()
            if user_ip:
                try:
                    canon_ip, ip_int = parse_and_validate_ipv4(user_ip)
                    existing = session.exec(
                        select(IPAllocation).where(col(IPAllocation.ip_address) == canon_ip)
                    ).first()
                    if existing is None:
                        session.add(
                            IPAllocation(
                                ip_address=canon_ip,
                                ip_int=ip_int,
                                subnet="255.255.255.0",
                                gateway="192.168.1.1",
                                nama_perangkat=f"PC {user_name}".strip(),
                                hostname=user_name.lower().replace(" ", "-"),
                                tipe="Fisik",
                                status="Aktif",
                                lokasi="Head Office (Office Blok 14)",
                                pengguna=user_name,
                                keterangan="Diimpor dari alokasi IP Operasional Staf",
                            )
                        )
                        imported_count += 1
                except ValueError:
                    pass

    if imported_count > 0:
        session.commit()
    return imported_count


def _classify_purchase_category(produk: str) -> str:
    """Mengklasifikasikan nama produk pembelian ke salah satu kategori resmi ITAM."""
    p = produk.lower()
    if "monitor" in p:
        return "Monitor"
    if "cctv" in p:
        return "CCTV"
    if any(k in p for k in ("switch", "router", "lan", "rj45", "converter", "media converter")):
        return "Jaringan"
    if any(k in p for k in ("ram", "ssd", "hdd", "vga", "prosesor", "fan", "psu", "thermal")):
        return "Komponen PC"
    if any(
        k in p
        for k in ("keyboard", "mouse", "logitech", "kabel", "tie", "organizer", "baterai")
    ):
        return "Periferal"
    if "printer" in p or "tinta" in p:
        return "Printer"
    if "synology" in p:
        return "Server"
    if "windows" in p or "lisensi" in p:
        return "Lainnya"
    return "Periferal"


def import_purchases_csv(session: Session, file_path: Path) -> int:
    """Mengimpor rekap pembelian perangkat dari rekap_pembelian.csv secara idempoten."""
    rows = _read_csv_rows(file_path)
    imported_count = 0

    for row in rows:
        no_str = row.get("NO", "").strip()
        if not no_str or not no_str.isdigit():
            continue

        no_val = int(no_str)
        kode_pembelian = f"PO-{no_val:03d}"

        # Cek idempotensi
        existing = session.exec(
            select(Purchase).where(col(Purchase.kode_pembelian) == kode_pembelian)
        ).first()
        if existing is not None:
            continue

        produk = row.get("PRODUK", "").strip()
        # Header harga di CSV kadang memiliki spasi di depan: ' HARGA' atau 'HARGA'
        raw_harga = row.get(" HARGA") or row.get("HARGA") or ""
        raw_pcs = row.get("PCS", "1")
        raw_total = row.get("Total", "")
        toko = row.get("NAMA TOKO", "").strip()
        link_marketplace = row.get("LINK MARKETPLACE", "").strip()
        dibeli_oleh = row.get("Dibeli Oleh", "").strip()
        raw_tanggal = row.get("TANGGAL", "").strip()

        harga_satuan = _parse_rupiah(raw_harga)
        jumlah = _parse_int(raw_pcs) or 1
        total_harga = _parse_rupiah(raw_total) or (harga_satuan * jumlah)
        tanggal_beli = _parse_date(raw_tanggal) or date(2025, 1, 1)

        kategori = _classify_purchase_category(produk)
        metode = "Marketplace" if link_marketplace else "Transfer"

        purchase = Purchase(
            kode_pembelian=kode_pembelian,
            nomor_invoice=f"INV-PO-{no_val:03d}",
            nama_item=produk,
            kategori=kategori,
            jenis_transaksi="Pembelian",
            vendor=toko,
            lokasi="Head Office (Office Blok 14)",
            jumlah=jumlah,
            satuan="Pcs" if jumlah > 1 else "Unit",
            harga_satuan=harga_satuan,
            total_harga=total_harga,
            tanggal_beli=tanggal_beli,
            tanggal_bayar=tanggal_beli,
            status="Lunas",
            metode_pembayaran=metode,
            is_recurring=False,
            siklus_tagihan="Sekali",
            penanggung_jawab=dibeli_oleh,
        )
        session.add(purchase)
        imported_count += 1

    if imported_count > 0:
        session.commit()
    return imported_count


def import_all_csv_data(
    session: Session,
    data_dir: Path | str | None = None,
    username: str = "system",
) -> dict[str, Any]:
    """Mengimpor seluruh file CSV operasional ke database secara terintegrasi dan idempoten."""
    folder = resolve_data_dir(data_dir)
    logger.info("Menjalankan impor CSV terpadu dari direktori: %s", folder)

    ups_count = import_ups_csv(session, folder / "rekap_ups_xml.csv")
    server_count = import_watt_server_csv(session, folder / "rekap_watt_server.csv")
    ip_count = import_ip_list_csv(session, folder / "ip_list_xml.csv")
    purchase_count = import_purchases_csv(session, folder / "rekap_pembelian.csv")

    total_imported = ups_count + server_count + ip_count + purchase_count

    if total_imported > 0:
        record_audit_log(
            session,
            username=username,
            nama_pengguna="System Importer" if username == "system" else username,
            role="Administrator",
            aksi="Impor CSV",
            modul="Master Data",
            target_id="CSV-DATA",
            detail=(
                f"Berhasil mengimpor {total_imported} data dari file CSV "
                f"({ups_count} UPS, {server_count} Server, {ip_count} IP, "
                f"{purchase_count} Pembelian)"
            ),
            level_risiko="Sedang",
        )

    return {
        "success": True,
        "message": "Impor data CSV berhasil diselesaikan",
        "data": {
            "ups_imported": ups_count,
            "servers_imported": server_count,
            "ips_imported": ip_count,
            "purchases_imported": purchase_count,
            "total_imported": total_imported,
        },
    }

