"""
Aggregates raw alert records into the dashboard summary payload.

This is the server-side equivalent of the frontend mock
(`frontend/src/app/core/api/mock-data.ts`): same KPI definitions, same
bucketing, so the UI behaves identically whether it talks to the mock
interceptor or this API.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .repository import AlertRecord, _MTTR_BASE_MIN
from .schemas import (
    CategoryCount,
    DashboardSummary,
    Kpi,
    SeverityCount,
    SocAlert,
    SourceCount,
    SystemHealth,
    TrendSeries,
    TrendSeriesItem,
)

RANGES: dict[str, timedelta] = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}

BUCKETS = {"24h": 24, "7d": 7, "30d": 30, "90d": 13}

SEVERITIES = ["critical", "high", "medium", "low"]


def window_bounds(range_id: str, periods_back: int = 0) -> tuple[datetime, datetime]:
    span = RANGES.get(range_id, RANGES["7d"])
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    end = now - periods_back * span
    return end - span, end


def apply_filters(alerts: list[AlertRecord], severities: list[str], categories: list[str]) -> list[AlertRecord]:
    out = alerts
    if severities:
        wanted = set(severities)
        out = [a for a in out if a.severity in wanted]
    if categories:
        wanted = set(categories)
        out = [a for a in out if a.category in wanted]
    return out


def _delta_pct(current: float, previous: float) -> float | None:
    if not previous:
        return None
    return round((current - previous) / previous * 1000) / 10


def _mttr_minutes(alerts: list[AlertRecord]) -> int:
    resolved = [a for a in alerts if a.status == "resolved"]
    if not resolved:
        return 0
    total = 0.0
    for a in resolved:
        if a.resolved_at:
            total += max(0.0, (a.resolved_at - a.timestamp).total_seconds() / 60)
        else:
            # No resolution timestamp in the schema — estimate by severity.
            total += _MTTR_BASE_MIN.get(a.severity, 200)
    return round(total / len(resolved))


def _sparkline(alerts: list[AlertRecord], start: datetime, span: timedelta, predicate) -> list[int]:
    points = [0] * 12
    for a in alerts:
        if not predicate(a):
            continue
        idx = min(11, int((a.timestamp - start) / span * 12))
        points[idx] += 1
    return points


def _buckets(alerts: list[AlertRecord], range_id: str, start: datetime, span: timedelta):
    count = BUCKETS.get(range_id, 7)
    bucket = span / count
    total = [0] * count
    resolved = [0] * count
    for a in alerts:
        idx = min(count - 1, int((a.timestamp - start) / bucket))
        total[idx] += 1
        if a.status == "resolved":
            resolved[idx] += 1
    if range_id == "24h":
        labels = [(start + i * bucket).strftime("%H:%M") for i in range(count)]
    else:
        # day formatted manually — %-d is not portable to Windows
        labels = [f"{(start + i * bucket).strftime('%b')} {(start + i * bucket).day}" for i in range(count)]
    return labels, total, resolved


def build_summary(
    current: list[AlertRecord],
    previous: list[AlertRecord],
    range_id: str,
    db_health: tuple[bool, int],
    demo_mode: bool,
) -> DashboardSummary:
    start, _end = window_bounds(range_id)
    span = RANGES.get(range_id, RANGES["7d"])

    def active(items: list[AlertRecord]) -> list[AlertRecord]:
        return [a for a in items if a.status in ("open", "investigating")]

    def critical(items: list[AlertRecord]) -> list[AlertRecord]:
        return [a for a in items if a.severity == "critical"]

    def resolution_rate(items: list[AlertRecord]) -> int:
        if not items:
            return 0
        return round(sum(1 for a in items if a.status == "resolved") / len(items) * 100)

    mttr, mttr_prev = _mttr_minutes(current), _mttr_minutes(previous)
    rate, rate_prev = resolution_rate(current), resolution_rate(previous)

    kpis = [
        Kpi(
            id="active", label="Active alerts", value=len(active(current)),
            deltaPct=_delta_pct(len(active(current)), len(active(previous))), goodWhen="down",
            trend=_sparkline(current, start, span, lambda a: a.status in ("open", "investigating")),
        ),
        Kpi(
            id="critical", label="Critical incidents", value=len(critical(current)),
            deltaPct=_delta_pct(len(critical(current)), len(critical(previous))), goodWhen="down",
            trend=_sparkline(current, start, span, lambda a: a.severity == "critical"),
        ),
        Kpi(
            id="mttr", label="Mean time to respond", value=mttr, unit="min",
            deltaPct=_delta_pct(mttr, mttr_prev), goodWhen="down",
            trend=_sparkline(current, start, span, lambda a: a.status == "resolved"),
        ),
        Kpi(
            id="resolution", label="Resolution rate", value=rate, unit="%",
            deltaPct=_delta_pct(rate, rate_prev), goodWhen="up",
            trend=_sparkline(current, start, span, lambda a: a.status == "resolved"),
        ),
    ]

    labels, total, resolved = _buckets(current, range_id, start, span)

    category_counts: dict[str, int] = {}
    source_counts: dict[str, dict] = {}
    for a in current:
        category_counts[a.category] = category_counts.get(a.category, 0) + 1
        entry = source_counts.setdefault(a.source, {"location": a.location, "count": 0})
        entry["count"] += 1

    db_ok, db_latency = db_health
    db_system = SystemHealth(
        name="SQL Server Database" if not demo_mode else "Database (demo mode)",
        state="operational" if db_ok else "down",
        uptimePct=99.9 if db_ok else 0.0,
        latencyMs=db_latency,
    )
    static_systems = [
        SystemHealth(name="SIEM Cluster", state="operational", uptimePct=99.95, latencyMs=11),
        SystemHealth(name="EDR Platform", state="operational", uptimePct=99.9, latencyMs=12),
        SystemHealth(name="Perimeter Firewall", state="operational", uptimePct=99.85, latencyMs=18),
        SystemHealth(name="Email Gateway", state="operational", uptimePct=99.4, latencyMs=15),
        SystemHealth(name="Threat Intel Feed", state="operational", uptimePct=99.87, latencyMs=24),
    ]

    return DashboardSummary(
        generatedAt=datetime.utcnow().isoformat() + "Z",
        kpis=kpis,
        trend=TrendSeries(
            labels=labels,
            series=[
                TrendSeriesItem(id="new", label="New alerts", points=total),
                TrendSeriesItem(id="resolved", label="Resolved", points=resolved),
            ],
        ),
        severities=[
            SeverityCount(severity=s, count=sum(1 for a in current if a.severity == s)) for s in SEVERITIES
        ],
        categories=[
            CategoryCount(category=c, count=n)
            for c, n in sorted(category_counts.items(), key=lambda kv: -kv[1])
            if n > 0
        ],
        topSources=[
            SourceCount(source=src, location=v["location"], count=v["count"])
            for src, v in sorted(source_counts.items(), key=lambda kv: -kv[1]["count"])[:6]
        ],
        systems=[db_system, *static_systems],
    )


def to_alert_page_items(alerts: list[AlertRecord], limit: int) -> list[SocAlert]:
    newest_first = sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    return [
        SocAlert(
            id=a.id,
            timestamp=a.timestamp.isoformat() + "Z",
            title=a.title,
            severity=a.severity,
            category=a.category,
            source=f"{a.source} · {a.location}" if a.location else a.source,
            status=a.status,
            analyst=a.analyst,
        )
        for a in newest_first[:limit]
    ]
