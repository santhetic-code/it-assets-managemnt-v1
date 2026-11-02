from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlmodel import Field, Session, SQLModel, select

from app.deps import PageParamsDep
from app.models.base import NAMING_CONVENTION, TimestampMixin, utcnow
from app.schemas.common import Page


@pytest.fixture(scope="module")
def dummy_model():
    """Tabel khusus tes; dicabut dari metadata agar tidak mengotori tes migrasi."""

    class Dummy(TimestampMixin, SQLModel, table=True):
        __tablename__ = "tes_dummy"
        id: int | None = Field(default=None, primary_key=True)
        nama: str

    yield Dummy
    SQLModel.metadata.remove(Dummy.__table__)  # type: ignore[arg-type]


def test_naming_convention_is_registered() -> None:
    assert SQLModel.metadata.naming_convention == NAMING_CONVENTION


def test_timestamp_mixin_sets_and_updates(session: Session, dummy_model) -> None:
    row = dummy_model(nama="a")
    session.add(row)
    session.commit()
    session.refresh(row)
    assert row.created_at is not None
    first = row.updated_at

    row.nama = "b"
    session.add(row)
    session.commit()
    session.refresh(row)
    assert row.updated_at >= first
    assert session.exec(select(dummy_model)).one().nama == "b"


def test_utcnow_is_timezone_aware_utc() -> None:
    assert utcnow().utcoffset() == timedelta(0)


def test_page_schema_matches_frontend_contract() -> None:
    page = Page[int](items=[1, 2], total=2, page=1, page_size=10)
    assert set(page.model_dump()) == {"items", "total", "page", "page_size"}
    with pytest.raises(ValidationError):
        Page[int](items=["x"], total=1, page=1, page_size=10)


def _paging_app() -> FastAPI:
    tmp = FastAPI()

    @tmp.get("/p")
    def p(params: PageParamsDep) -> dict[str, int]:
        return {
            "page": params.page,
            "page_size": params.page_size,
            "offset": params.offset,
        }

    return tmp


def test_page_params_defaults_and_offset() -> None:
    c = TestClient(_paging_app())
    assert c.get("/p").json() == {"page": 1, "page_size": 10, "offset": 0}
    assert c.get("/p?page=3&page_size=20").json()["offset"] == 40


@pytest.mark.parametrize("qs", ["page=0", "page_size=0", "page_size=101", "page=abc"])
def test_page_params_rejects_invalid(qs: str) -> None:
    assert TestClient(_paging_app()).get(f"/p?{qs}").status_code == 422

