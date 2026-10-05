import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status

from schemas.prediction import (
    PredictionResponse,
    DiseaseResponse,
    TopPrediction
)
from services.model_service import model_service
from services.supabase_service import supabase_service
from dependencies import get_optional_user

logger = logging.getLogger("agrovision.routes.prediction")
router = APIRouter(prefix="/api", tags=["Prediction & Diseases"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_crop_disease(
    image: UploadFile = File(..., description="Crop leaf image (JPG, JPEG, PNG, WEBP, max 10MB)"),
    crop: Optional[str] = Form(None, description="Optional target crop type (e.g. Tomato, Potato, Wheat, Rice, Corn)"),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Perform disease classification on an uploaded leaf image:
    1. Validates file extension, MIME type, size, and PIL image format integrity.
    2. Saves the image securely into backend/uploads/.
    3. Runs MobileNetV2 inference for disease classification.
    4. Returns prediction with confidence, top-3 predictions, and disease information.
    5. Saves prediction record to Supabase if user is authenticated.
    """
    # 1 & 2. Image validation and saving
    saved_path, saved_filename, pil_image = await model_service.validate_and_save_image(image)

    # 3 & 4. Run model service prediction
    pred_result = model_service.predict(pil_image, crop=crop, saved_filename=saved_filename)

    # 5. Persist prediction to Supabase
    user_id = current_user.get("id") if current_user else "anonymous"
    created_record = supabase_service.create_prediction(
        user_id=user_id,
        crop=pred_result["crop"],
        disease=pred_result["disease"],
        confidence=pred_result["confidence"],
        image_path=pred_result["image_path"]
    )

    top_predictions = [
        TopPrediction(disease=p["disease"], confidence=p["confidence"])
        for p in pred_result.get("top_predictions", [])
    ]

    return PredictionResponse(
        id=created_record.get("id", str(uuid.uuid4())),
        crop=pred_result["crop"],
        disease=pred_result["disease"],
        confidence=pred_result["confidence"],
        status=pred_result["status"],
        symptoms=pred_result["symptoms"],
        cause=pred_result["cause"],
        prevention=pred_result["prevention"],
        treatment=pred_result["treatment"],
        image_url=pred_result["image_path"],
        created_at=created_record.get("created_at", datetime.now(timezone.utc).isoformat()),
        is_temporary_model=pred_result.get("is_temporary_model", False),
        model_notice=pred_result.get("model_notice", "MobileNetV2 Crop Disease Detection"),
        top_predictions=top_predictions,
        low_confidence_warning=pred_result.get("low_confidence_warning", False),
    )


@router.get("/diseases", response_model=List[DiseaseResponse])
async def list_diseases(crop: Optional[str] = None):
    """
    Retrieve the crop disease catalog, optionally filtered by crop name.
    """
    diseases = supabase_service.get_diseases(crop=crop)
    return [DiseaseResponse(**d) for d in diseases]


@router.get("/diseases/{id}", response_model=DiseaseResponse)
async def get_disease(id: str):
    """
    Retrieve full details for a specific disease record by ID.
    """
    disease = supabase_service.get_disease_by_id(id)
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease with ID '{id}' not found."
        )
    return DiseaseResponse(**disease)