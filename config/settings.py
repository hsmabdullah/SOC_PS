"""
config/settings.py
──────────────────
Central configuration module for the SOC Alert Triage Platform.

Uses pydantic-settings to load all values from environment variables / .env
file.  A single settings singleton is imported across the codebase —
no other module ever reads os.environ directly, and no secret is hardcoded.

Architecture decision:
    Pydantic BaseSettings validates types at startup so a misconfigured
    deployment fails loudly rather than silently misbehaving at runtime.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """SQL Server connection parameters."""

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", extra="ignore")

    server: str = Field(..., description="SQL Server hostname or IP")
    port: int = Field(1433, description="TCP port")
    name: str = Field(..., description="Database name")
    user: str = Field(..., description="Read-only SQL login")
    password: SecretStr = Field(..., description="SQL login password")
    driver: str = Field("ODBC Driver 18 for SQL Server")
    encrypt: str = Field("yes", description="TLS encryption flag")
    trust_server_cert: str = Field("no")
    connection_timeout: int = Field(30)

    @property
    def connection_string(self) -> str:
        """Build pyodbc connection string (never logged)."""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.name};"
            f"UID={self.user};"
            f"PWD={self.password.get_secret_value()};"
            f"Encrypt={self.encrypt};"
            f"TrustServerCertificate={self.trust_server_cert};"
            f"Connection Timeout={self.connection_timeout};"
        )

    @property
    def sqlalchemy_url(self) -> str:
        """Build SQLAlchemy mssql+pyodbc URL using connection string passthrough."""
        import urllib.parse
        params = urllib.parse.quote_plus(self.connection_string)
        return f"mssql+pyodbc:///?odbc_connect={params}"


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Literal["openrouter", "grok"] = Field("openrouter")

    openrouter_api_key: SecretStr = Field(default=SecretStr(""), alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openrouter_model: str = Field("openai/gpt-4o", alias="OPENROUTER_MODEL")

    grok_api_key: SecretStr = Field(default=SecretStr(""), alias="GROK_API_KEY")
    grok_base_url: str = Field("https://api.x.ai/v1", alias="GROK_BASE_URL")
    grok_model: str = Field("grok-2-latest", alias="GROK_MODEL")

    @property
    def active_api_key(self) -> str:
        if self.llm_provider == "openrouter":
            return self.openrouter_api_key.get_secret_value()
        return self.grok_api_key.get_secret_value()

    @property
    def active_base_url(self) -> str:
        if self.llm_provider == "openrouter":
            return self.openrouter_base_url
        return self.grok_base_url

    @property
    def active_model(self) -> str:
        if self.llm_provider == "openrouter":
            return self.openrouter_model
        return self.grok_model


class AppSettings(BaseSettings):
    """Application-level settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_secret_key: SecretStr = Field(..., alias="APP_SECRET_KEY")
    session_expiry_minutes: int = Field(60, alias="SESSION_EXPIRY_MINUTES")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: str = Field("logs/soc_triage.log", alias="LOG_FILE")

    model_artifact_path: Path = Field(Path("artifacts/models"), alias="MODEL_ARTIFACT_PATH")
    scaler_artifact_path: Path = Field(Path("artifacts/scalers"), alias="SCALER_ARTIFACT_PATH")
    encoder_artifact_path: Path = Field(Path("artifacts/encoders"), alias="ENCODER_ARTIFACT_PATH")

    @field_validator("model_artifact_path", "scaler_artifact_path", "encoder_artifact_path", mode="after")
    @classmethod
    def ensure_dirs_exist(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


class Settings:
    """
    Unified settings façade.

    Usage anywhere in the codebase:
        from config.settings import get_settings
        cfg = get_settings()
        cfg.db.connection_string
        cfg.llm.active_api_key
        cfg.app.log_level
    """

    def __init__(self) -> None:
        self.db = DatabaseSettings()
        self.llm = LLMSettings()
        self.app = AppSettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.  Reads .env on first call only."""
    return Settings()