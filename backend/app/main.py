from fastapi import FastAPI

app = FastAPI(title="ITAM Pro API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
