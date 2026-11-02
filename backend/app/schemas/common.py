"""Skema umum. Bentuk Page identik dengan kontrak mock frontend."""

from pydantic import BaseModel


class Page[T](BaseModel):
    """Respons daftar berhalaman: {items, total, page, page_size}."""

    items: list[T]
    total: int
    page: int
    page_size: int

