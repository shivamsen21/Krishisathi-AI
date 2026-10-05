from pydantic import BaseModel, Field
from typing import Optional, List


class TopPrediction(BaseModel):
    disease: str
    confidence: float


class PredictionResponse(BaseModel):
    id: str
    crop: str
    disease: str
    confidence: float
    status: str
    symptoms: Optional[str] = None
    cause: Optional[str] = None
    prevention: Optional[str] = None
    treatment: Optional[str] = None
    image_url: str
    created_at: str
    is_temporary_model: bool = True
    model_notice: str = "Temporary Model Prediction [MobileNetV2 Pending Next Phase]"
    top_predictions: List[TopPrediction] = []
    low_confidence_warning: bool = False


class PredictionHistoryItem(BaseModel):
    id: str
    crop: str
    disease: str
    confidence: float
    status: str
    image_path: str
    created_at: str
    symptoms: Optional[str] = None
    prevention: Optional[str] = None
    treatment: Optional[str] = None


class DiseaseBase(BaseModel):
    crop: str = Field(..., min_length=2, max_length=100)
    disease_name: str = Field(..., min_length=2, max_length=100)
    symptoms: str = Field(..., min_length=5)
    cause: Optional[str] = ""
    prevention: str = Field(..., min_length=5)
    treatment: str = Field(..., min_length=5)


class DiseaseCreate(DiseaseBase):
    pass


class DiseaseUpdate(BaseModel):
    crop: Optional[str] = None
    disease_name: Optional[str] = None
    symptoms: Optional[str] = None
    cause: Optional[str] = None
    prevention: Optional[str] = None
    treatment: Optional[str] = None


class DiseaseResponse(DiseaseBase):
    id: str
    created_at: str
    updated_at: str