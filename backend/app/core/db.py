"""Koneksi database (engine dibuat malas agar import tidak membuka koneksi)."""

from functools import lru_cache

from sqlalchemy import Engine
from sqlmodel import create_engine

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().sqlalchemy_url
    connect_args = {"check_same_thread": False} if str(url).startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)
