"""Koneksi database (engine dibuat malas agar import tidak membuka koneksi)."""

from functools import lru_cache

from sqlalchemy import Engine
from sqlmodel import create_engine

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().sqlalchemy_url, pool_pre_ping=True)
