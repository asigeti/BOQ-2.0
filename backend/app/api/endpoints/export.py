from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io

from app import models
from app.api import deps

router = APIRouter()

@router.get("/plans/{plan_id}/excel")
def export_plan_to_excel(
    plan_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Export BOQ results to Excel file (no auth required).
    """
    plan = db.query(models.ProjectPlan).filter(
        models.ProjectPlan.id == plan_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get materials
    materials = db.query(models.MaterialQuantity).filter(
        models.MaterialQuantity.plan_id == plan_id
    ).all()
    
    if not materials:
        raise HTTPException(status_code=404, detail="No materials found for this plan")
    
    # Create DataFrame
    data = []
    for mat in materials:
        data.append({
            "חומר": mat.material_name,  # Material (Hebrew)
            "כמות": mat.quantity,  # Quantity
            "יחידה": mat.unit,  # Unit
            "רמת ביטחון": f"{mat.confidence_score * 100:.1f}%"  # Confidence
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='כתב כמויות')
    
    output.seek(0)
    
    # Return as downloadable file
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=BOQ_{plan.filename}.xlsx"
        }
    )
