"""Layanan Audit Log (In-Memory) untuk ITAM Pro."""
from datetime import datetime
from typing import Any

MOCK_AUDIT_LOGS: list[dict[str, Any]] = []


def record_audit_event(actor: str, action: str, target_id: str, detail: str) -> None:
    """Catat aktivitas akses kredensial ke audit log in-memory."""
    MOCK_AUDIT_LOGS.insert(
        0,
        {
            "id": f"AUD-{len(MOCK_AUDIT_LOGS) + 1}",
            "timestamp": datetime.now().isoformat(),
            "actor": actor,
            "action": action,
            "target_id": target_id,
            "detail": detail,
        },
    )

