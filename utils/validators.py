"""
utils/validators.py
────────────────────
Pydantic v2 models for validating all LLM API responses.

Every response from an external LLM is validated before use.
This prevents prompt injection-via-response and malformed data
from corrupting the platform state.

Models defined here:
    - AlertAnalysisResponse    : Copilot's analysis of a single alert
    - TriageSummaryResponse    : Copilot's batch triage summary
    - EDAInsightResponse       : AI-generated EDA insights
    - ReportSectionResponse    : Generic report section from the LLM
    - PredictionExplanation    : SHAP + LLM explanation of a model decision
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ClassificationLabel(str, Enum):
    TP = "TP"
    FP = "FP"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"
    UNKNOWN  = "UNKNOWN"


# ── Alert-level responses ─────────────────────────────────────────────────────

class AlertAnalysisResponse(BaseModel):
    """
    Structured response from the Copilot when analysing a single SOC alert.
    """
    classification:  ClassificationLabel = Field(description="TP or FP prediction reasoning")
    confidence:      float = Field(ge=0.0, le=1.0, description="Confidence 0–1")
    risk_level:      RiskLevel
    summary:         str = Field(max_length=1000, description="Plain-English alert summary")
    key_indicators:  list[str] = Field(max_length=10, description="Top evidence points")
    recommendation:  str = Field(max_length=500, description="Analyst action recommendation")
    mitre_context:   Optional[str] = Field(None, max_length=200)

    @field_validator("key_indicators")
    @classmethod
    def cap_indicators(cls, v: list[str]) -> list[str]:
        return v[:10]

    @field_validator("summary", "recommendation")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class TriageSummaryResponse(BaseModel):
    """Batch triage summary for multiple alerts."""
    total_alerts:      int
    tp_count:          int
    fp_count:          int
    high_risk_alerts:  list[int] = Field(description="alert_ids requiring immediate attention")
    summary_narrative: str = Field(max_length=2000)
    recommendations:   list[str] = Field(max_length=10)

    @field_validator("high_risk_alerts")
    @classmethod
    def cap_alerts(cls, v: list[int]) -> list[int]:
        return v[:50]


# ── EDA responses ─────────────────────────────────────────────────────────────

class EDAInsightResponse(BaseModel):
    """AI-generated insight from exploratory data analysis."""
    finding:        str = Field(max_length=500)
    severity:       RiskLevel = Field(default=RiskLevel.MEDIUM)
    recommendation: str = Field(max_length=300)
    affected_feature: Optional[str] = None


class EDAReportResponse(BaseModel):
    """Full EDA report from the AI EDA Agent."""
    data_quality_score:      float = Field(ge=0.0, le=100.0)
    class_imbalance_detected: bool
    top_insights:             list[EDAInsightResponse]
    cybersecurity_findings:   list[str] = Field(max_length=20)
    preprocessing_recommendations: list[str] = Field(max_length=20)
    executive_summary:        str = Field(max_length=2000)

    @field_validator("top_insights")
    @classmethod
    def cap_insights(cls, v: list) -> list:
        return v[:15]


# ── Report generation ─────────────────────────────────────────────────────────

class ReportSectionResponse(BaseModel):
    """A single section of an AI-generated report."""
    section_title:   str = Field(max_length=100)
    content:         str = Field(max_length=5000)
    key_findings:    list[str] = Field(default_factory=list, max_length=10)


# ── Explainability ────────────────────────────────────────────────────────────

class PredictionExplanation(BaseModel):
    """
    Human-readable explanation of a model prediction, combining
    SHAP values and an LLM-generated narrative.
    """
    alert_id:          int
    predicted_label:   ClassificationLabel
    confidence:        float = Field(ge=0.0, le=1.0)
    top_features:      list[dict[str, float]] = Field(description="[{feature: shap_value}]")
    narrative:         str = Field(max_length=1500)
    analyst_guidance:  str = Field(max_length=500)

    @field_validator("top_features")
    @classmethod
    def cap_features(cls, v: list) -> list:
        return v[:15]


# ── LLM response parser ───────────────────────────────────────────────────────

def parse_llm_response(raw: str, model_class: type[BaseModel]) -> BaseModel | None:
    """
    Parse and validate a JSON string from the LLM into a Pydantic model.

    Args:
        raw:         Raw string from the LLM (may be JSON or markdown-wrapped JSON).
        model_class: The Pydantic model class to validate against.

    Returns:
        Validated model instance, or None if parsing fails.
    """
    import json
    import re

    # Strip markdown code fences if present
    json_match = re.search(r"(?:json)?\s*(\{.*?\})\s*", raw, re.DOTALL)
    json_str = json_match.group(1) if json_match else raw.strip()

    try:
        data = json.loads(json_str)
        return model_class.model_validate(data)
    except Exception as exc:
        from config.logging_config import get_logger
        get_logger(__name__).warning(
            "LLM response validation failed (%s): %s", model_class.__name__, exc
        )
        return None
