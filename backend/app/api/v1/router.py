"""Router induk API v1. Semua modul tahap berikutnya didaftarkan di sini."""

from fastapi import APIRouter

from app.api.v1 import assets, auth, ip_vm, master

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
