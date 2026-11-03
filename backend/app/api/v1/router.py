"""Router induk API v1. Semua modul tahap berikutnya didaftarkan di sini."""

from fastapi import APIRouter

from app.api.v1 import assets, auth, finance, ip_vm, maintenance, master, power

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(master.router, prefix="/master", tags=["master"])
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
