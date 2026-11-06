from fastapi.testclient import TestClient

from app.deps import get_session
from app.main import app


def test_health_ok(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_health_db_ok(client: TestClient) -> None:
    res = client.get("/health/db")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "ok"}


def test_health_db_returns_503_without_leaking_detail() -> None:
    class BrokenSession:
        def execute(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError("password=rahasia host=db")

    app.dependency_overrides[get_session] = lambda: BrokenSession()
    try:
        with TestClient(app) as c:
            res = c.get("/health/db")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 503
    assert res.json() == {"detail": "Database tidak dapat dijangkau"}
    assert "rahasia" not in res.text


def test_api_v1_prefix_is_mounted(client: TestClient) -> None:
    # Router v1 masih kosong: path tak dikenal -> 404 JSON standar FastAPI.
    res = client.get("/api/v1/tidak-ada")
    assert res.status_code == 404
    assert res.json() == {"detail": "Not Found"}
