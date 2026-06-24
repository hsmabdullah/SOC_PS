"""
utils/helpers.py
─────────────────
Shared utility functions used across the SOC Triage Platform.

Includes:
    - DataFrame serialisation / deserialisation helpers
    - Artifact save / load (joblib) with consistent paths
    - Timing decorator
    - Safe JSON serialiser for numpy types
    - Report export helpers (CSV, JSON)
"""

from __future__ import annotations

import functools
import json
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

import joblib
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


# ── Timing decorator ──────────────────────────────────────────────────────────

def timeit(func: F) -> F:
    """Log execution time of any function."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug("%s completed in %.3f seconds.", func.__qualname__, elapsed)
        return result
    return wrapper  # type: ignore[return-value]


# ── Artifact persistence ──────────────────────────────────────────────────────

def save_artifact(obj: Any, name: str, artifact_type: str = "model") -> Path:
    """
    Persist a Python object using joblib.

    Args:
        obj:           The object to save (model, scaler, encoder, etc.).
        name:          Filename without extension.
        artifact_type: "model", "scaler", or "encoder".

    Returns:
        Path where the artifact was saved.
    """
    cfg = get_settings()
    dirs = {
        "model":   cfg.app.model_artifact_path,
        "scaler":  cfg.app.scaler_artifact_path,
        "encoder": cfg.app.encoder_artifact_path,
    }
    base_dir = dirs.get(artifact_type, cfg.app.model_artifact_path)
    path = base_dir / f"{name}.joblib"
    joblib.dump(obj, path, compress=3)
    logger.info("Artifact saved: %s", path)
    return path


def load_artifact(name: str, artifact_type: str = "model") -> Any:
    """
    Load a persisted artifact.

    Args:
        name:          Filename without extension.
        artifact_type: "model", "scaler", or "encoder".

    Returns:
        The deserialised Python object.

    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    cfg = get_settings()
    dirs = {
        "model":   cfg.app.model_artifact_path,
        "scaler":  cfg.app.scaler_artifact_path,
        "encoder": cfg.app.encoder_artifact_path,
    }
    base_dir = dirs.get(artifact_type, cfg.app.model_artifact_path)
    path = base_dir / f"{name}.joblib"

    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")

    obj = joblib.load(path)
    logger.info("Artifact loaded: %s", path)
    return obj


# ── JSON serialisation ────────────────────────────────────────────────────────

class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types (int64, float32, ndarray, etc.)."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialise obj to JSON, handling numpy types."""
    return json.dumps(obj, cls=NumpyEncoder, indent=indent, ensure_ascii=False)


# ── Export helpers ────────────────────────────────────────────────────────────

def export_dataframe(
    df: pd.DataFrame,
    filename: str,
    export_dir: str = "exports",
    fmt: str = "csv",
) -> Path:
    """
    Export a DataFrame to CSV or JSON in the exports directory.

    Args:
        df:         DataFrame to export.
        filename:   Base filename without extension.
        export_dir: Target directory.
        fmt:        "csv" or "json".

    Returns:
        Path to the exported file.
    """
    out_dir = Path(export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{filename}.{fmt}"

    if fmt == "csv":
        df.to_csv(path, index=False)
    elif fmt == "json":
        df.to_json(path, orient="records", indent=2, force_ascii=False)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")

    logger.info("Exported %d rows to %s", len(df), path)
    return path


# ── DataFrame utilities ───────────────────────────────────────────────────────

def memory_usage_mb(df: pd.DataFrame) -> float:
    """Return DataFrame memory usage in MB."""
    return df.memory_usage(deep=True).sum() / (1024 ** 2)


def downcast_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Downcast numeric columns to reduce memory usage.
    Useful after loading large tables from SQL Server.
    """
    result = df.copy()
    for col in result.select_dtypes(include=["float64"]).columns:
        result[col] = pd.to_numeric(result[col], downcast="float")
    for col in result.select_dtypes(include=["int64"]).columns:
        result[col] = pd.to_numeric(result[col], downcast="integer")
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Return numerator/denominator, or default if denominator is zero."""
    return numerator / denominator if denominator != 0 else default
