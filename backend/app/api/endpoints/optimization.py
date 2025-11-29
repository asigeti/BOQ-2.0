from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.api import deps

router = APIRouter()

@router.post("/supply-chain", response_model=List[dict])
def get_supply_chain_recommendations(
    plan_id: int = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get supplier recommendations for a specific plan.
    """
    plan = db.query(models.ProjectPlan).filter(models.ProjectPlan.id == plan_id, models.ProjectPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Convert SQLAlchemy models to dicts for the service
    materials_data = []
    for mat in plan.materials:
        materials_data.append({
            "material_name": mat.material_name,
            "quantity": mat.quantity,
            "unit": mat.unit
        })
    
    recommendations = services.get_supplier_recommendations(materials_data)
    return recommendations

@router.get("/weather", response_model=dict)
def get_weather(
    location: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get weather forecast for a location.
    """
    return services.get_weather_forecast(location)
