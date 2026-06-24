from typing import TypedDict


class PreprocessingState(TypedDict):
    profile_report: dict
    target_column: str
    recommendations: dict