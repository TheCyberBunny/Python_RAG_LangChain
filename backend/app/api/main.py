"""
FastAPI application entrypoint.
Run from the backend/ directory (with the venv active):
    fastapi dev app/api/main.py
"""

import time

from fastapi import FastAPI, Request

from app.api.routers import documents, tickets, analytics, ask

app = FastAPI(title="DevMate", version="0.1.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Runs for EVERY request, before it reaches any route function below.
    Purely observational - authorization is handled separately, as a
    per-router dependency (see Step 4's api/security.py), so FastAPI's
    auto-generated docs know a key is required and Swagger UI can
    prompt for it directly.
    """
    start = time.perf_counter()

    # call_next actually invokes the matching route (after any
    # dependencies on it have run, including require_api_key) and
    # gives back its response - this is the "pass control forward" step.
    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
    return response


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "DevMate"}


app.include_router(documents.router)
app.include_router(tickets.router)
app.include_router(analytics.router)
app.include_router(ask.router)