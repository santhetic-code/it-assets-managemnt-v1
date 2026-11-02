"""Layanan Audit Log (In-Memory) untuk ITAM Pro."""
from copy import deepcopy
from datetime import datetime
from typing import Any

MOCK_AUDIT_LOGS: list[dict[str, Any]] = [
    {
        "id": "AUD-001",
        "timestamp": "2026-10-30T08:05:00",
        "actor": "Admin IT",
        "action": "user.login",
        "target_id": "USR-01",
        "detail": "Berhasil login ke sistem ITAM Pro",
    },
    {
        "id": "AUD-002",
        "timestamp": "2026-10-30T09:15:00",
        "actor": "Admin IT",
        "action": "asset.update",
        "target_id": "SRV-0001",
        "detail": "Memperbarui spesifikasi TDP server",
    },
    {
        "id": "AUD-003",
        "timestamp": "2026-10-30T10:20:00",
        "actor": "Admin IT",
        "action": "credential.reveal",
        "target_id": "CRD-0001",
        "detail": "Membuka field secret pada kredensial CRD-0001",
    },
]


def record_audit_event(actor: str, action: str, target_id: str, detail: str) -> None:
    """Catat aktivitas ke audit log in-memory (tanpa memuat secret/password)."""
    MOCK_AUDIT_LOGS.insert(
        0,
        {
            "id": f"AUD-{len(MOCK_AUDIT_LOGS) + 1:03d}",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "actor": actor,
            "action": action,
            "target_id": target_id,
            "detail": detail,
        },
    )


def query_audit_logs(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 15,
) -> dict[str, Any]:
    """Ambil daftar Audit Log dengan filter pencarian & modul."""
    search = str(filters.get("search", "")).strip().lower()
    module = str(filters.get("module", "")).strip().lower()

    filtered: list[dict[str, Any]] = []
    for item in MOCK_AUDIT_LOGS:
        act = str(item.get("action", ""))
        if module and module != "semua" and not act.lower().startswith(module):
            continue
        if search:
            haystack = (
                f"{item.get('id', '')} {item.get('actor', '')} "
                f"{act} {item.get('target_id', '')} {item.get('detail', '')}"
            ).lower()
            if search not in haystack:
                continue

        row = deepcopy(item)
        row["time_display"] = str(row.get("timestamp", "")).replace("T", " ")
        mod_prefix = act.split(".", 1)[0].upper() if "." in act else "SYSTEM"
        row["module_badge"] = mod_prefix
        row["module_variant"] = (
            "danger"
            if "ditolak" in act or "failed" in act
            else "warning"
            if "reveal" in act or "reset" in act
            else "info"
        )
        filtered.append(row)

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    return {
        "items": filtered[start : start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


__all__ = ["MOCK_AUDIT_LOGS", "query_audit_logs", "record_audit_event"]
