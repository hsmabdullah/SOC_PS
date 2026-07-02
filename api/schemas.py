"""
Pydantic response models for the dashboard API.

Field names are camelCase on purpose: they mirror the TypeScript
interfaces in `frontend/src/app/core/models/soc.models.ts` — keep the
two files in sync.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

Severity = Literal["critical", "high", "medium", "low"]
AlertStatus = Literal["open", "investigating", "contained", "resolved"]
SystemState = Literal["operational", "degraded", "down"]


class Kpi(BaseModel):
    id: str
    label: str
    value: float
    unit: Optional[str] = None
    deltaPct: Optional[float] = None
    goodWhen: Literal["up", "down"]
    trend: list[int]


class TrendSeriesItem(BaseModel):
    id: str
    label: str
    points: list[int]


class TrendSeries(BaseModel):
    labels: list[str]
    series: list[TrendSeriesItem]


class SeverityCount(BaseModel):
    severity: Severity
    count: int


class CategoryCount(BaseModel):
    category: str
    count: int


class SourceCount(BaseModel):
    source: str
    location: str
    count: int


class SystemHealth(BaseModel):
    name: str
    state: SystemState
    uptimePct: float
    latencyMs: int


class SocAlert(BaseModel):
    id: str
    timestamp: str  # ISO 8601
    title: str
    severity: Severity
    category: str
    source: str
    status: AlertStatus
    analyst: Optional[str] = None


class DashboardSummary(BaseModel):
    generatedAt: str
    kpis: list[Kpi]
    trend: TrendSeries
    severities: list[SeverityCount]
    categories: list[CategoryCount]
    topSources: list[SourceCount]
    systems: list[SystemHealth]


class AlertPage(BaseModel):
    total: int
    items: list[SocAlert]
