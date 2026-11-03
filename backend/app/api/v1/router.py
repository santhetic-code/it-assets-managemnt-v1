"""Router induk API v1. Semua modul tahap berikutnya didaftarkan di sini."""

from fastapi import APIRouter

from app.api.v1 import (
    assets,
    audit,
    auth,
    credentials,
    dashboard,
    finance,
    ip_vm,
    maintenance,
    master,
    power,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(master.router, prefix="/master", tags=["master"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(
    dashboard.router,
    prefix="/overview",
    tags=["dashboard"],
    include_in_schema=False,
)
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(ip_vm.router, prefix="/ip-allocations", tags=["ip-vm"])
api_router.include_router(
    ip_vm.router,
    prefix="/ip-entries",
    tags=["ip-vm"],
    include_in_schema=False,
)
api_router.include_router(
    ip_vm.router,
    prefix="/ip-vm",
    tags=["ip-vm"],
    include_in_schema=False,
)
api_router.include_router(
    ip_vm.router,
    prefix="/ips",
    tags=["ip-vm"],
    include_in_schema=False,
)
api_router.include_router(power.router, prefix="/watt-server", tags=["power"])
api_router.include_router(power.router, prefix="/power", tags=["power"], include_in_schema=False)
api_router.include_router(
    power.router,
    prefix="/server-power",
    tags=["power"],
    include_in_schema=False,
)
api_router.include_router(finance.router, prefix="/purchases", tags=["finance"])
api_router.include_router(
    finance.router,
    prefix="/finance",
    tags=["finance"],
    include_in_schema=False,
)
api_router.include_router(
    finance.router,
    prefix="/invoices",
    tags=["finance"],
    include_in_schema=False,
)
api_router.include_router(
    finance.router,
    prefix="/recurring-bills",
    tags=["finance"],
    include_in_schema=False,
)
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(
    maintenance.router,
    prefix="/maintenances",
    tags=["maintenance"],
    include_in_schema=False,
)
api_router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
api_router.include_router(
    credentials.router,
    prefix="/credential-manager",
    tags=["credentials"],
    include_in_schema=False,
)
api_router.include_router(audit.router, prefix="/audit-logs", tags=["audit"])
api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["audit"],
    include_in_schema=False,
)
api_router.include_router(
    audit.router,
    prefix="/audits",
    tags=["audit"],
    include_in_schema=False,
)
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    users.router,
    prefix="/accounts",
    tags=["users"],
    include_in_schema=False,
)
