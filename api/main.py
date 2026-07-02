"""
FastAPI layer for the Angular SOC dashboard.

Run (from the repository root):

    uvicorn api.main:app --reload --port 8000

Endpoints (consumed by frontend/src/app/core/api/soc-api.service.ts):

    GET /api/v1/health
    GET /api/v1/dashboard/summary?range=7d&severities=critical,high&categories=Malware
    GET /api/v1/alerts?range=7d&severities=&categories=&limit=8

Data source: the SQL Server alerts table (configure DB_* and SOC_* vars
in `.env`); falls back to a deterministic demo dataset when DB_SERVER is
empty, so the stack runs end-to-end without a database.
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .aggregation import apply_filters, build_summary, to_alert_page_items, window_bounds
from .repository import get_repository, is_demo_mode
from .schemas import AlertPage, DashboardSummary

app = FastAPI(title="Pak Suzuki SOC — Dashboard API", version="1.0.0")

# The Angular dev server (ng serve) proxies /api to this process, but CORS
# is enabled too so a directly-opened frontend build also works.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# NOTE: endpoint signatures use Optional[...] (not `str | None`) on purpose —
# FastAPI evaluates these annotations at runtime, and PEP 604 unions need
# Python 3.10+, while this project must run on Python 3.9 (Anaconda).
def _split(value: Optional[str]) -> list[str]:
    return [v for v in (value or "").split(",") if v]


@app.get("/api/v1/health")
def health() -> dict:
    ok, latency_ms = get_repository().health()
    return {"status": "ok" if ok else "degraded", "database": ok, "latencyMs": latency_ms, "demoMode": is_demo_mode()}


@app.get("/api/v1/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    range: str = Query("7d", pattern="^(24h|7d|30d|90d)$"),
    severities: Optional[str] = None,
    categories: Optional[str] = None,
) -> DashboardSummary:
    repo = get_repository()
    sev, cat = _split(severities), _split(categories)

    cur_start, cur_end = window_bounds(range)
    prev_start, _ = window_bounds(range, periods_back=1)

    # One fetch covers both windows; slice in memory.
    records = repo.fetch(prev_start, cur_end)
    current = apply_filters([a for a in records if a.timestamp >= cur_start], sev, cat)
    previous = apply_filters([a for a in records if a.timestamp < cur_start], sev, cat)

    return build_summary(current, previous, range, repo.health(), is_demo_mode())


@app.get("/api/v1/alerts", response_model=AlertPage)
def alerts(
    range: str = Query("7d", pattern="^(24h|7d|30d|90d)$"),
    severities: Optional[str] = None,
    categories: Optional[str] = None,
    limit: int = Query(8, ge=1, le=100),
) -> AlertPage:
    repo = get_repository()
    start, end = window_bounds(range)
    matching = apply_filters(repo.fetch(start, end), _split(severities), _split(categories))
    return AlertPage(total=len(matching), items=to_alert_page_items(matching, limit))
