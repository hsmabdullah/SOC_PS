"""
security/auth.py
─────────────────
Authentication and Role-Based Access Control (RBAC) for the SOC Platform.

Roles (in ascending privilege order):
    viewer  – Read-only: dashboard, alerts list
    analyst – All viewer permissions + predictions, copilot, exports
    admin   – Full access including model training, audit logs, settings

Architecture decisions:
    - Passwords are stored as bcrypt hashes (never plaintext).
    - Sessions are signed HMAC tokens (itsdangerous TimestampSigner) so
      Streamlit's session_state cannot be trivially forged.
    - Users are stored in a simple in-memory dict for this platform.
      In production, integrate with the organisation's Active Directory
      or LDAP using the ldap3 library.
    - Session expiry is enforced on every page load.

Note on Streamlit security:
    Streamlit does not have a true server-side session store.  We store the
    signed token in st.session_state and re-validate on every rerun.
    This is appropriate for an internal SOC tool on a trusted network.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from config.logging_config import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


# ── Role hierarchy ────────────────────────────────────────────────────────────

class Role(IntEnum):
    VIEWER  = 1
    ANALYST = 2
    ADMIN   = 3

    @classmethod
    def from_str(cls, role_str: str) -> "Role":
        mapping = {"viewer": cls.VIEWER, "analyst": cls.ANALYST, "admin": cls.ADMIN}
        return mapping.get(role_str.lower(), cls.VIEWER)


# ── User model ────────────────────────────────────────────────────────────────

@dataclass
class User:
    username: str
    role: Role
    department: str = "SOC"
    full_name: str = ""


# ── In-memory user store (replace with LDAP/DB in production) ─────────────────
# Passwords are bcrypt hashed.  To generate: bcrypt.hashpw(b"password", bcrypt.gensalt())
# Default credentials for demo only — change before any real deployment.
_USER_STORE: dict[str, dict] = {
    "admin": {
        "password_hash": bcrypt.hashpw(b"Admin@SOC2024!", bcrypt.gensalt()),
        "role": Role.ADMIN,
        "full_name": "SOC Administrator",
        "department": "Security Operations",
    },
    "analyst1": {
        "password_hash": bcrypt.hashpw(b"Analyst@SOC!", bcrypt.gensalt()),
        "role": Role.ANALYST,
        "full_name": "L1 Analyst",
        "department": "SOC",
    },
    "viewer1": {
        "password_hash": bcrypt.hashpw(b"Viewer@SOC!", bcrypt.gensalt()),
        "role": Role.VIEWER,
        "full_name": "SOC Viewer",
        "department": "Management",
    },
}


# ── Auth service ──────────────────────────────────────────────────────────────

class AuthService:
    """
    Handles login, session token creation, and permission checking.

    Usage:
        auth = AuthService()
        token = auth.login("analyst1", "password")
        user  = auth.validate_token(token)
        auth.require_role(user, Role.ANALYST)
    """

    def __init__(self) -> None:
        cfg = get_settings()
        self._signer = TimestampSigner(
            cfg.app.app_secret_key.get_secret_value(),
            salt="soc-triage-session",
        )
        self._session_expiry = cfg.app.session_expiry_minutes * 60  # seconds

    def login(self, username: str, password: str) -> Optional[str]:
        """
        Verify credentials and return a signed session token.

        Args:
            username: Plain-text username.
            password: Plain-text password.

        Returns:
            Signed token string on success, None on failure.
        """
        user_record = _USER_STORE.get(username.lower())
        if not user_record:
            logger.warning("Login failed: unknown user '%s'", username)
            return None

        pw_bytes = password.encode("utf-8")
        stored_hash = user_record["password_hash"]

        if not bcrypt.checkpw(pw_bytes, stored_hash):
            logger.warning("Login failed: bad password for user '%s'", username)
            return None

        # Embed username in the signed token payload
        payload = f"{username}:{user_record['role'].value}"
        token = self._signer.sign(payload).decode("utf-8")

        logger.info(
            "Login successful | user=%s | role=%s",
            username,
            user_record["role"].name,
        )
        return token

    def validate_token(self, token: str) -> Optional[User]:
        """
        Validate a session token and return the associated User.

        Args:
            token: Signed token from login().

        Returns:
            User dataclass on success, None if expired or invalid.
        """
        try:
            payload = self._signer.unsign(
                token.encode("utf-8"),
                max_age=self._session_expiry,
            ).decode("utf-8")

            username, role_value = payload.rsplit(":", 1)
            user_record = _USER_STORE.get(username)
            if not user_record:
                return None

            return User(
                username=username,
                role=user_record["role"],
                full_name=user_record.get("full_name", ""),
                department=user_record.get("department", "SOC"),
            )

        except SignatureExpired:
            logger.info("Session token expired.")
            return None
        except BadSignature:
            logger.warning("Invalid session token detected — possible tampering.")
            return None

    def require_role(self, user: Optional[User], minimum_role: Role) -> bool:
        """
        Check that user has at least the required role level.

        Args:
            user:         User from validate_token(), or None if not logged in.
            minimum_role: Minimum Role required.

        Returns:
            True if authorised, False otherwise.
        """
        if user is None:
            return False
        return user.role >= minimum_role

    def get_allowed_pages(self, user: User) -> list[str]:
        """Return list of page names this user can access."""
        base = ["dashboard", "alerts", "profiling", "eda"]
        if self.require_role(user, Role.ANALYST):
            base += ["preprocessing", "feature_engineering", "predictions", "explainability", "copilot", "reports"]
        if self.require_role(user, Role.ADMIN):
            base += ["model_training", "evaluation", "database_explorer", "audit_logs", "settings"]
        return base


# Module-level singleton
_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
