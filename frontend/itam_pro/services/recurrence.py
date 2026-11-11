"""
Mesin kalkulasi siklus (recurrence) Tagihan Berulang ITAM Pro.
Murni stdlib: aman untuk tahun kabisat dan akhir bulan 28/29/30/31.
"""

import calendar
import datetime

PERIODE_MONTHS: dict[str, int] = {
    "Bulanan": 1,
    "3 bulan": 3,
    "6 bulan": 6,
    "Tahunan": 12,
}


def _to_date(value: datetime.date | str) -> datetime.date:
    if isinstance(value, str):
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    return value


def add_months(
    sourcedate: datetime.date,
    months: int,
    anchor_day: int | None = None,
) -> datetime.date:
    """Tambah N bulan dengan aman (hari dijepit ke akhir bulan target).

    `anchor_day` (opsional) = tanggal asli siklus. Bila diberikan, hari target
    dihitung dari anchor, sehingga 31 Jan -> 28 Feb -> 31 Mar (tidak melorot ke 28).
    """
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    desired_day = anchor_day if anchor_day is not None else sourcedate.day
    day = min(desired_day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def next_due(
    current_due: datetime.date | str,
    periode: str,
    anchor_day: int | None = None,
) -> datetime.date | None:
    """Jatuh tempo berikutnya dari jatuh tempo LAMA. None = 'Sekali' (nonaktifkan)."""
    due = _to_date(current_due)
    if periode == "Sekali":
        return None
    if periode == "Mingguan":
        return due + datetime.timedelta(days=7)
    months = PERIODE_MONTHS.get(periode)
    if months is None:
        return due
    return add_months(due, months, anchor_day)


def calculate_bill_status(
    jatuh_tempo: datetime.date | str,
    pengingat_hari: int = 7,
    today: datetime.date | None = None,
) -> dict[str, str]:
    """Status tagihan: Terlambat, Segera, atau Terjadwal."""
    due = _to_date(jatuh_tempo)
    ref = today or datetime.date.today()
    diff_days = (due - ref).days

    if diff_days < 0:
        return {"status": "Terlambat", "label": f"Terlambat {abs(diff_days)} hari"}
    if diff_days == 0:
        return {"status": "Segera", "label": "Hari ini"}
    if diff_days <= pengingat_hari:
        return {"status": "Segera", "label": f"{diff_days} hari lagi"}
    return {"status": "Terjadwal", "label": f"{diff_days} hari lagi"}


def parse_date_flexible(raw: datetime.date | str | None) -> datetime.date | None:
    """Parse tanggal format YYYY-MM-DD atau DD/MM/YYYY (Google Sheet AC) dengan aman."""
    if raw is None:
        return None
    if isinstance(raw, datetime.date):
        return raw
    text = str(raw).strip()
    if not text or text in ("—", "-"):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def add_interval_clamped(
    base_date: datetime.date | str,
    interval_nilai: int,
    interval_satuan: str = "bulan",
    anchor_day: int | None = None,
) -> datetime.date:
    """Tambah interval (hari|minggu|bulan) dengan clamp akhir bulan (31 Jan + 1 bln = 28/29 Feb)."""
    d = parse_date_flexible(base_date) or datetime.date.today()
    val = max(1, int(interval_nilai or 1))
    unit = (interval_satuan or "bulan").strip().lower()
    if unit in ("hari", "day", "days", "harian"):
        return d + datetime.timedelta(days=val)
    if unit in ("minggu", "week", "weeks", "mingguan"):
        return d + datetime.timedelta(days=val * 7)
    if unit in ("tahun", "year", "years", "tahunan"):
        return add_months(d, val * 12, anchor_day=anchor_day)
    return add_months(d, val, anchor_day=anchor_day)


def compute_next_due_from_rule(
    *,
    last_done_at: datetime.date | str | None,
    previous_due_at: datetime.date | str | None,
    interval_nilai: int,
    interval_satuan: str = "bulan",
    hitung_dari: str = "tanggal_selesai",
    anchor_day: int | None = None,
) -> datetime.date:
    """Hitung next_due_at berdasarkan aturan hitung_dari."""
    mode = (hitung_dari or "tanggal_selesai").strip().lower()
    if mode == "jatuh_tempo_sebelumnya" and previous_due_at:
        base = parse_date_flexible(previous_due_at) or datetime.date.today()
    else:
        base = (
            parse_date_flexible(last_done_at)
            or parse_date_flexible(previous_due_at)
            or datetime.date.today()
        )
    return add_interval_clamped(
        base, interval_nilai, interval_satuan, anchor_day=anchor_day
    )


__all__ = [
    "PERIODE_MONTHS",
    "add_interval_clamped",
    "add_months",
    "calculate_bill_status",
    "compute_next_due_from_rule",
    "next_due",
    "parse_date_flexible",
]
