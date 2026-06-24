"""
security/audit_logger.py
─────────────────────────
Immutable audit logging for the SOC Alert Triage Platform.

Every significant user action is recorded with:
    - Timestamp (UTC)
    - Username
    - Role
    - Module / page
    - Action
    - Result (success / failure / error)
    - Detail (optional context)

The audit log is written to a rotating JSONL file (one JSON object per line).
This format is directly ingestible by most SIEM systems (Splunk, Elastic, etc.)

Security design:
    - Audit log is append-only in application code (no delete / update).
    - The OS file permissions should be set to write-only for the app user.
    - Each entry includes a SHA-256 integrity hash of the record content,
      allowing offline tamper detection.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger

logger = get_logger(__name__)

_AUDIT_LOG_PATH = Path("logs/audit.jsonl")
_MAX_BYTES = 20 * 1024 * 1024   # 20 MB
_BACKUP_COUNT = 10


class AuditLogger:
    """
    Append-only structured audit logger.

    Usage:
        audit = get_audit_logger()
        audit.log(
            username="analyst1",
            role="analyst",
            module="predictions",
            action="run_prediction",
            result="success",
            detail="alert_id=1234",
        )
    """

    def __init__(self, log_path: Path = _AUDIT_LOG_PATH) -> None:
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        username: str,
        role: str,
        module: str,
        action: str,
        result: str,
        detail: Optional[str] = None,
    ) -> None:
        """
        Write an audit record.

        Args:
            username: The authenticated user performing the action.
            role:     The user's role string.
            module:   Which platform module was accessed.
            action:   What the user did.
            result:   "success", "failure", or "error".
            detail:   Optional free-text context (must NOT contain raw PII).
        """
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "username":  username,
            "role":      role,
            "module":    module,
            "action":    action,
            "result":    result,
            "detail":    detail or "",
        }
        # Integrity hash over the record content (excluding the hash field itself)
        record_str = json.dumps(record, sort_keys=True)
        record["integrity_hash"] = hashlib.sha256(record_str.encode()).hexdigest()

        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            # Audit logging must never crash the application
            logger.error("Audit log write failed: %s", exc)

    def read_recent(self, n: int = 200) -> list[dict]:
        """
        Return the most recent n audit records as a list of dicts.

        Args:
            n: Number of most-recent records to return.

        Returns:
            List of record dicts (newest last).
        """
        if not self._log_path.exists():
            return []
        try:
            lines = self._log_path.read_text(encoding="utf-8").splitlines()
            records = []
            for line in lines[-n:]:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return records
        except Exception as exc:
            logger.error("Audit log read failed: %s", exc)
            return []

    def verify_integrity(self) -> list[str]:
        """
        Scan all audit records and report any tampered entries.

        Returns:
            List of timestamps where integrity checks failed.
        """
        if not self._log_path.exists():
            return []

        tampered: list[str] = []
        lines = self._log_path.read_text(encoding="utf-8").splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                stored_hash = record.pop("integrity_hash", None)
                if stored_hash is None:
                    tampered.append(f"Missing hash for record at {record.get('timestamp_utc','?')}")
                    continue
                computed = hashlib.sha256(
                    json.dumps(record, sort_keys=True).encode()
                ).hexdigest()
                if computed != stored_hash:
                    tampered.append(
                        f"Tampered record detected: {record.get('timestamp_utc','?')} "
                        f"user={record.get('username','?')}"
                    )
            except Exception:
                tampered.append(f"Unreadable audit record: {line[:80]}")

        return tampered


_audit_instance: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Return the module-level AuditLogger singleton."""
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = AuditLogger()
    return _audit_instance