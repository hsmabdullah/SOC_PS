import pandas as pd
import numpy as np
import json
from datetime import datetime


class DataProfiler:
    """
    Enterprise-level automated data profiling engine for SOC dataset understanding.
    """

    def __init__(self):
        pass

    def profile(self, df: pd.DataFrame, target_column: str = None) -> dict:
        """
        Generate full profiling report for SOC data.
        """

        report = {
            "timestamp": str(datetime.now()),
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().mean() * 100).round(2).to_dict(),
            "duplicates": int(df.duplicated().sum()),
            "cardinality": df.nunique().to_dict(),
        }

        # ----------------------------
        # NUMERIC CORRELATION MATRIX
        # ----------------------------
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.shape[1] > 1:
            report["correlation_matrix"] = numeric_df.corr().round(3).to_dict()
        else:
            report["correlation_matrix"] = {}

        # ----------------------------
        # TARGET DISTRIBUTION
        # ----------------------------
        if target_column and target_column in df.columns:
            report["target_distribution"] = (
                df[target_column]
                .value_counts(normalize=True)
                .round(4)
                .to_dict()
            )
        else:
            report["target_distribution"] = None

        # ----------------------------
        # DATA QUALITY SCORE
        # ----------------------------
        report["data_quality_score"] = self._compute_quality_score(df)

        # ----------------------------
        # FEATURE INSIGHTS
        # ----------------------------
        report["feature_summary"] = self._feature_summary(df)

        return report

    def _compute_quality_score(self, df: pd.DataFrame) -> float:
        """
        Simple SOC-grade data quality scoring system (0–100).
        """

        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()

        completeness = 1 - (missing_cells / total_cells if total_cells > 0 else 0)
        uniqueness = 1 - (duplicate_rows / df.shape[0] if df.shape[0] > 0 else 0)

        score = (0.7 * completeness + 0.3 * uniqueness) * 100
        return round(score, 2)

    def _feature_summary(self, df: pd.DataFrame) -> dict:
        """
        Generate quick statistical summary per column.
        """

        summary = {}

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                summary[col] = {
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                    "std": float(df[col].std()) if not df[col].isnull().all() else None,
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                }
            else:
                summary[col] = {
                    "top_value": df[col].mode()[0] if not df[col].mode().empty else None,
                    "unique_values": int(df[col].nunique())
                }

        return summary

    def export_report(self, report: dict, output_path: str = "reports/data_profile.json"):
        """
        Export profiling report to JSON file.
        """

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)

        return output_path
