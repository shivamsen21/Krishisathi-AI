import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from schemas.prediction import (
    DiseaseCreate,
    DiseaseUpdate,
    DiseaseResponse
)
from services.supabase_service import supabase_service
from dependencies import get_current_admin

logger = logging.getLogger("agrovision.routes.admin")
router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

@router.get("/stats")
async def get_admin_stats(
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Platform-wide metrics for the Admin Dashboard:
    - Total Farmers count
    - Total Predictions count
    - Disease detections count
    - Healthy scans count
    Requires role = admin.
    """
    stats = supabase_service.get_admin_stats()
    return stats

@router.get("/users")
async def get_admin_users(
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Retrieve all registered platform users with their scan metrics.
    Requires role = admin.
    """
    users = supabase_service.get_admin_users()
    return users

@router.get("/predictions")
async def get_all_predictions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Retrieve all predictions submitted across all farmers.
    Requires role = admin.
    """
    predictions = supabase_service.get_all_predictions(limit=limit, offset=offset)

    formatted = []
    for p in predictions:
        pred_disease = p.get("disease", "")
        is_healthy = "healthy" in pred_disease.lower()
        formatted.append({
            "id": f"#{str(p.get('id', ''))[:8]}",
            "full_id": str(p.get("id")),
            "farmer": p.get("farmer") or (p.get("profiles", {}).get("full_name") if isinstance(p.get("profiles"), dict) else "Farmer"),
            "crop": p.get("crop", "Tomato"),
            "disease": pred_disease,
            "confidence": f"{float(p.get('confidence', 90.0)):.1f}%",
            "status": "Healthy" if is_healthy else "Diseased",
            "date": p.get("created_at", "")[:10],
            "image_path": p.get("image_path", "")
        })
    return formatted

@router.post("/diseases", response_model=DiseaseResponse, status_code=status.HTTP_201_CREATED)
async def create_disease(
    data: DiseaseCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Create a new disease entry in the agricultural catalog.
    Requires role = admin.
    """
    try:
        created = supabase_service.create_disease(data.model_dump())
        return DiseaseResponse(**created)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create disease: {str(e)}"
        )

@router.put("/diseases/{id}", response_model=DiseaseResponse)
async def update_disease(
    id: str,
    data: DiseaseUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Update an existing disease entry in the catalog.
    Requires role = admin.
    """
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided."
        )

    updated = supabase_service.update_disease(id, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease record '{id}' not found."
        )
    return DiseaseResponse(**updated)

@router.delete("/diseases/{id}")
async def delete_disease(
    id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Delete a disease entry from the catalog.
    Requires role = admin.
    """
    deleted = supabase_service.delete_disease(id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease record '{id}' not found."
        )
    return {"message": f"Disease '{id}' deleted successfully."}
