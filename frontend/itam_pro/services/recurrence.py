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


__all__ = ["PERIODE_MONTHS", "add_months", "calculate_bill_status", "next_due"]
