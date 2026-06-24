from pydantic import BaseModel


class PreprocessingDecision(BaseModel):
    missing_strategy: str
    encoding_method: str
    scaling_method: str
    transformation_method: str
    apply_smote: bool