"""
Alert data access for the dashboard API.

Two implementations behind one interface:

- `SqlAlertRepository`  — reads the real alerts table from SQL Server via
  the existing `database.connector.DatabaseConnector`. The table and
  column names are configurable through environment variables (see
  `.env`), so it adapts to whatever schema the SOC database uses.
- `DemoAlertRepository` — a seeded, deterministic in-memory population
  used automatically when `DB_SERVER` is not configured, so the API (and
  the Angular frontend) work end-to-end without a database.

`get_repository()` picks the right one at startup.
"""

from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Domain record ────────────────────────────────────────────────────────────


@dataclass
class AlertRecord:
    id: str
    timestamp: datetime
    title: str
    severity: str  # critical | high | medium | low
    category: str
    source: str
    location: str
    status: str  # open | investigating | contained | resolved
    analyst: str | None
    resolved_at: datetime | None


# ── Value normalisation (DB values → dashboard vocabulary) ──────────────────

SEVERITY_MAP = {
    "critical": "critical", "crit": "critical", "sev1": "critical", "p1": "critical", "4": "critical",
    "high": "high", "sev2": "high", "p2": "high", "3": "high",
    "medium": "medium", "med": "medium", "moderate": "medium", "sev3": "medium", "p3": "medium", "2": "medium",
    "low": "low", "info": "low", "informational": "low", "sev4": "low", "p4": "low", "1": "low",
}

STATUS_MAP = {
    "open": "open", "new": "open", "triage": "open",
    "investigating": "investigating", "in progress": "investigating", "in_progress": "investigating",
    "assigned": "investigating",
    "contained": "contained", "mitigated": "contained",
    "resolved": "resolved", "closed": "resolved", "done": "resolved", "false positive": "resolved",
}


def normalize_severity(value: object) -> str:
    return SEVERITY_MAP.get(str(value).strip().lower(), "medium")


def normalize_status(value: object) -> str:
    return STATUS_MAP.get(str(value).strip().lower(), "open")


# ── SQL Server repository ────────────────────────────────────────────────────


class SqlAlertRepository:
    """Reads alerts from SQL Server. Read-only, parameterised time window."""

    def __init__(self) -> None:
        # Imported lazily so demo mode works without pyodbc installed.
        from database.connector import DatabaseConnector

        self.connector = DatabaseConnector()
        self.table = os.getenv("SOC_ALERTS_TABLE", "alerts")
        col = lambda env, default: os.getenv(env, default)  # noqa: E731
        self.c_id = col("SOC_COL_ID", "id")
        self.c_ts = col("SOC_COL_TIMESTAMP", "created_at")
        self.c_title = col("SOC_COL_TITLE", "title")
        self.c_sev = col("SOC_COL_SEVERITY", "severity")
        self.c_cat = col("SOC_COL_CATEGORY", "category")
        self.c_src = col("SOC_COL_SOURCE", "source_ip")
        self.c_status = col("SOC_COL_STATUS", "status")
        self.c_analyst = col("SOC_COL_ANALYST", "analyst")  # optional, '' to disable
        self.c_resolved = col("SOC_COL_RESOLVED_AT", "resolved_at")  # optional, '' to disable

    def fetch(self, start: datetime, end: datetime) -> list[AlertRecord]:
        from sqlalchemy import text

        optional = []
        if self.c_analyst:
            optional.append(f"[{self.c_analyst}] AS analyst")
        if self.c_resolved:
            optional.append(f"[{self.c_resolved}] AS resolved_at")
        optional_sql = (", " + ", ".join(optional)) if optional else ""

        query = text(
            f"SELECT [{self.c_id}] AS id, [{self.c_ts}] AS ts, [{self.c_title}] AS title, "
            f"[{self.c_sev}] AS severity, [{self.c_cat}] AS category, [{self.c_src}] AS source, "
            f"[{self.c_status}] AS status{optional_sql} "
            f"FROM [{self.table}] "
            f"WHERE [{self.c_ts}] >= :start AND [{self.c_ts}] < :end"
        )
        with self.connector.get_connection() as conn:
            rows = conn.execute(query, {"start": start, "end": end}).mappings().all()

        records: list[AlertRecord] = []
        for r in rows:
            records.append(
                AlertRecord(
                    id=str(r["id"]),
                    timestamp=r["ts"],
                    title=str(r["title"]),
                    severity=normalize_severity(r["severity"]),
                    category=str(r["category"]),
                    source=str(r["source"]),
                    location="",
                    status=normalize_status(r["status"]),
                    analyst=(str(r["analyst"]) if r.get("analyst") else None),
                    resolved_at=r.get("resolved_at"),
                )
            )
        return records

    def health(self) -> tuple[bool, int]:
        """(reachable, latency_ms) of a trivial round-trip."""
        from sqlalchemy import text

        started = time.perf_counter()
        try:
            with self.connector.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            return True, int((time.perf_counter() - started) * 1000)
        except Exception:  # noqa: BLE001 — any driver error means "down"
            logger.exception("Database health check failed")
            return False, 0


# ── Demo repository (no database configured) ─────────────────────────────────

_CATEGORIES = [
    ("Malware", 26), ("Phishing", 24), ("Intrusion Attempt", 20),
    ("Policy Violation", 14), ("Data Exfiltration", 9), ("DDoS", 7),
]

_TITLES = {
    "Malware": ["Trojan signature detected on endpoint", "Ransomware behaviour blocked by EDR",
                "Suspicious binary executed from temp directory", "Known C2 beacon pattern observed"],
    "Phishing": ["Credential-harvesting email reported by user", "Spoofed executive domain in inbound mail",
                 "Malicious attachment quarantined at gateway", "Mass phishing campaign targeting finance dept"],
    "Intrusion Attempt": ["Multiple failed SSH logins from single source", "Port scan detected against DMZ segment",
                          "Exploit attempt against public web server", "Brute-force attack on VPN concentrator"],
    "Data Exfiltration": ["Unusual outbound transfer volume from file server", "Sensitive data pattern in outbound traffic",
                          "Large upload to unsanctioned cloud storage", "Database dump copied to removable media"],
    "Policy Violation": ["Unauthorized software installation detected", "Privileged account used outside change window",
                         "USB mass-storage device connected on plant floor", "Shadow-IT SaaS access from corporate network"],
    "DDoS": ["Volumetric flood against dealer portal", "SYN flood mitigated at edge",
             "Application-layer flood on API gateway", "Amplification attack traffic observed"],
}

_SOURCES = [
    ("203.99.176.14", "Karachi, PK"), ("91.242.218.90", "Bucharest, RO"),
    ("45.155.204.7", "Amsterdam, NL"), ("118.91.130.66", "Singapore, SG"),
    ("185.220.101.34", "Frankfurt, DE"), ("103.148.20.211", "Lahore, PK"),
    ("64.62.197.152", "Fremont, US"), ("180.178.94.19", "Tokyo, JP"),
]

_ANALYSTS = ["A. Rehman", "S. Khan", "M. Iqbal", "F. Ahmed", None, None]

_MTTR_BASE_MIN = {"critical": 45, "high": 90, "medium": 220, "low": 420}


def _weighted(rnd: random.Random, entries: list[tuple[str, int]]) -> str:
    total = sum(w for _, w in entries)
    roll = rnd.random() * total
    for item, w in entries:
        roll -= w
        if roll <= 0:
            return item
    return entries[-1][0]


class DemoAlertRepository:
    """Deterministic seeded population spanning 180 days (no DB required)."""

    SPAN_DAYS = 180

    def __init__(self) -> None:
        rnd = random.Random(0x50C0)
        anchor = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        self._alerts: list[AlertRecord] = []
        for i in range(4200):
            age_days = (rnd.random() ** 1.35) * self.SPAN_DAYS
            ts = anchor - timedelta(days=age_days)
            severity = _weighted(rnd, [("low", 38), ("medium", 32), ("high", 21), ("critical", 9)])
            category = _weighted(rnd, _CATEGORIES)
            resolved_bias = min(0.92, 0.35 + age_days * 0.05)
            status = _weighted(
                rnd,
                [("resolved", int(resolved_bias * 100)), ("contained", 12), ("investigating", 14), ("open", 16)],
            )
            source, location = _SOURCES[int(rnd.random() * len(_SOURCES))]
            mttr = _MTTR_BASE_MIN[severity] + int(rnd.random() * _MTTR_BASE_MIN[severity])
            self._alerts.append(
                AlertRecord(
                    id=f"AL-{100000 + i:X}",
                    timestamp=ts,
                    title=_TITLES[category][int(rnd.random() * 4)],
                    severity=severity,
                    category=category,
                    source=source,
                    location=location,
                    status=status,
                    analyst=_ANALYSTS[int(rnd.random() * len(_ANALYSTS))],
                    resolved_at=(ts + timedelta(minutes=mttr)) if status == "resolved" else None,
                )
            )
        self._alerts.sort(key=lambda a: a.timestamp, reverse=True)

    def fetch(self, start: datetime, end: datetime) -> list[AlertRecord]:
        return [a for a in self._alerts if start <= a.timestamp < end]

    def health(self) -> tuple[bool, int]:
        return True, 1


# ── Factory ──────────────────────────────────────────────────────────────────

_repository = None


def get_repository():
    """SQL repository when DB_SERVER is configured, demo data otherwise."""
    global _repository
    if _repository is None:
        if os.getenv("DB_SERVER"):
            logger.info("Dashboard API using SQL Server repository (table=%s)", os.getenv("SOC_ALERTS_TABLE", "alerts"))
            _repository = SqlAlertRepository()
        else:
            logger.warning("DB_SERVER not set — dashboard API serving built-in demo data")
            _repository = DemoAlertRepository()
    return _repository


def is_demo_mode() -> bool:
    return not os.getenv("DB_SERVER")
