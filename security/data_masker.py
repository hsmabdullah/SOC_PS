"""
security/data_masker.py
────────────────────────
PII / sensitive data masking layer.

CRITICAL SECURITY REQUIREMENT:
    NO raw SOC data is ever sent to an external LLM API.
    All usernames, hostnames, IP addresses, and email addresses are replaced
    with deterministic tokens before leaving this system.

Design decisions:
    - Deterministic masking: same input always produces the same token within
      a session. This allows the LLM response to reference the token and the
      SOC analyst can mentally reverse it.
    - Masking is applied at the DataFrame level (column-aware) AND at the
      free-text level (regex-based) for prompt strings.
    - The reverse-map is stored in memory only — never persisted or logged.
    - Token format: USER_001, HOST_002, IP_003, EMAIL_004 — unique per session.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


class DataMasker:
    """
    Masks sensitive fields in DataFrames and free-text strings.

    Usage:
        masker = DataMasker()
        masked_df  = masker.mask_dataframe(df)
        masked_text = masker.mask_text(some_prompt)
        # Later: masker.reverse_map shows original → token mapping
    """

    # Regex patterns for free-text masking
    _IP_PATTERN    = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9.%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
    # Hostname pattern: matches XYZV850800L style and generic server names
    _HOST_PATTERN  = re.compile(r"\bXYZ[A-Z0-9]+L\b|\b[A-Za-z0-9\-]{4,}(?:\.XYZ\.COM\.PK)\b")

    # Columns that contain sensitive PII
    _PII_COLUMNS: dict[str, str] = {
        "hostname":   "HOST",
        "user":       "USER",
        "username":   "USER",
        "user_name":  "USER",
        "source_ip":  "IP",
        "destination_ip": "IP",
        "device_ip":  "IP",
        "device_public_ip": "IP",
        "device_mac": "MAC",
    }

    def __init__(self) -> None:
        self._user_map:  dict[str, str] = {}
        self._host_map:  dict[str, str] = {}
        self._ip_map:    dict[str, str] = {}
        self._email_map: dict[str, str] = {}
        self._mac_map:   dict[str, str] = {}

        self._user_counter  = 0
        self._host_counter  = 0
        self._ip_counter    = 0
        self._email_counter = 0
        self._mac_counter   = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def mask_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a copy of df with sensitive columns masked.

        Args:
            df: Input DataFrame (may contain any columns).

        Returns:
            Masked DataFrame copy — original is not modified.
        """
        masked = df.copy()
        for col, category in self._PII_COLUMNS.items():
            if col in masked.columns:
                masked[col] = masked[col].apply(
                    lambda val: self._mask_value(val, category)
                )
        logger.debug("DataFrame masked: %d rows, %d PII columns processed.", len(df), len([c for c in self._PII_COLUMNS if c in df.columns]))
        return masked

    def mask_text(self, text: str) -> str:
        """
        Apply regex-based masking to a free-text string (e.g., a prompt).

        Args:
            text: Raw text that may contain IPs, emails, hostnames.

        Returns:
            Masked text with tokens substituted.
        """
        # Order matters: email before IP (emails contain dots)
        text = self._EMAIL_PATTERN.sub(self._replace_email, text)
        text = self._IP_PATTERN.sub(self._replace_ip, text)
        text = self._HOST_PATTERN.sub(self._replace_host, text)
        return text

    @property
    def reverse_map(self) -> dict[str, dict[str, str]]:
        """Return the token → original value mappings (for analyst reference only)."""
        # Flip all maps: token → original
        def flip(m: dict[str, str]) -> dict[str, str]:
            return {v: k for k, v in m.items()}

        return {
            "users":  flip(self._user_map),
            "hosts":  flip(self._host_map),
            "ips":    flip(self._ip_map),
            "emails": flip(self._email_map),
            "macs":   flip(self._mac_map),
        }

    def reset(self) -> None:
        """Reset all maps and counters (call between sessions if needed)."""
        self.__init__()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _mask_value(self, value: Any, category: str) -> str:
        """Dispatch a single value to the right masking map."""
        if pd.isna(value) or value is None:
            return value  # type: ignore[return-value]
        s = str(value)
        if category == "USER":
            return self._get_or_create(s, self._user_map, "USER", self._next_user)
        if category == "HOST":
            return self._get_or_create(s, self._host_map, "HOST", self._next_host)
        if category == "IP":
            return self._get_or_create(s, self._ip_map, "IP", self._next_ip)
        if category == "MAC":
            return self._get_or_create(s, self._mac_map, "MAC", self._next_mac)
        return s

    def _get_or_create(
        self,
        value: str,
        store: dict[str, str],
        prefix: str,
        counter_fn: Any,
    ) -> str:
        if value not in store:
            store[value] = f"{prefix}_{counter_fn():04d}"
        return store[value]

    def _next_user(self) -> int:
        self._user_counter += 1
        return self._user_counter

    def _next_host(self) -> int:
        self._host_counter += 1
        return self._host_counter

    def _next_ip(self) -> int:
        self._ip_counter += 1
        return self._ip_counter

    def _next_email(self) -> int:
        self._email_counter += 1
        return self._email_counter

    def _next_mac(self) -> int:
        self._mac_counter += 1
        return self._mac_counter

    def _replace_ip(self, match: re.Match) -> str:  # type: ignore[type-arg]
        original = match.group(0)
        return self._get_or_create(original, self._ip_map, "IP", self._next_ip)

    def _replace_email(self, match: re.Match) -> str:  # type: ignore[type-arg]
        original = match.group(0)
        return self._get_or_create(original, self._email_map, "EMAIL", self._next_email)

    def _replace_host(self, match: re.Match) -> str:  # type: ignore[type-arg]
        original = match.group(0)
        return self._get_or_create(original, self._host_map, "HOST", self._next_host)


# Module-level singleton
_masker_instance: DataMasker | None = None


def get_masker() -> DataMasker:
    """Return the session-scoped DataMasker singleton."""
    global _masker_instance
    if _masker_instance is None:
        _masker_instance = DataMasker()
    return _masker_instance
