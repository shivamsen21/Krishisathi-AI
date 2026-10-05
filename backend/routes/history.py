import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from schemas.prediction import PredictionHistoryItem
from services.supabase_service import supabase_service
from dependencies import get_current_user

logger = logging.getLogger("agrovision.routes.history")
router = APIRouter(prefix="/api/history", tags=["Detection History"])

@router.get("", response_model=List[PredictionHistoryItem])
async def get_user_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    crop: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieve detection history for the authenticated user, supporting pagination and filters.
    """
    predictions = supabase_service.get_predictions_for_user(
        user_id=current_user["id"],
        limit=limit,
        offset=offset
    )

    results = []
    for p in predictions:
        pred_crop = p.get("crop", "Tomato")
        pred_disease = p.get("disease", "")
        disease_info = supabase_service.get_disease_by_crop_and_name(pred_crop, pred_disease)

        is_healthy = "healthy" in pred_disease.lower()
        derived_status = "Healthy" if is_healthy else "Diseased"

        if crop and crop.lower() not in pred_crop.lower():
            continue
        if status_filter and status_filter.lower() != derived_status.lower():
            continue

        results.append(PredictionHistoryItem(
            id=str(p.get("id")),
            crop=pred_crop,
            disease=pred_disease,
            confidence=float(p.get("confidence", 90.0)),
            status=derived_status,
            image_path=p.get("image_path", ""),
            created_at=p.get("created_at", ""),
            symptoms=disease_info.get("symptoms") if disease_info else None,
            prevention=disease_info.get("prevention") if disease_info else None,
            treatment=disease_info.get("treatment") if disease_info else None,
        ))

    return results

@router.get("/{id}", response_model=PredictionHistoryItem)
async def get_history_detail(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieve details of a single prediction scan.
    Users can only access their own scans unless role is 'admin'.
    """
    is_admin = current_user.get("role") == "admin"
    user_id_filter = None if is_admin else current_user["id"]

    prediction = supabase_service.get_prediction_by_id(id, user_id=user_id_filter)
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction scan with ID '{id}' not found."
        )

    pred_crop = prediction.get("crop", "Tomato")
    pred_disease = prediction.get("disease", "")
    disease_info = supabase_service.get_disease_by_crop_and_name(pred_crop, pred_disease)
    is_healthy = "healthy" in pred_disease.lower()

    return PredictionHistoryItem(
        id=str(prediction.get("id")),
        crop=pred_crop,
        disease=pred_disease,
        confidence=float(prediction.get("confidence", 90.0)),
        status="Healthy" if is_healthy else "Diseased",
        image_path=prediction.get("image_path", ""),
        created_at=prediction.get("created_at", ""),
        symptoms=disease_info.get("symptoms") if disease_info else None,
        prevention=disease_info.get("prevention") if disease_info else None,
        treatment=disease_info.get("treatment") if disease_info else None,
    )
