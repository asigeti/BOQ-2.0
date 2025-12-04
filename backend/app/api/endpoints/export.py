from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
import json

from app import models
from app.api import deps

router = APIRouter()


@router.get("/projects/{project_id}/excel")
def export_project_to_excel(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Export all BOQ results from a project to a single Excel file with multiple sheets.
    """
    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all completed plans for this project
    plans = db.query(models.ProjectPlan).filter(
        models.ProjectPlan.project_id == project_id,
        models.ProjectPlan.processing_status == 'completed'
    ).all()

    if not plans:
        raise HTTPException(status_code=404, detail="No completed plans found for this project")

    # Create Excel file with multiple sheets
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        all_items = []

        for plan in plans:
            # Try to get BOQ data from the plan
            if plan.boq_data:
                try:
                    boq_data = json.loads(plan.boq_data) if isinstance(plan.boq_data, str) else plan.boq_data

                    # Extract items from chapters
                    for chapter in boq_data.get('chapters', []):
                        for item in chapter.get('items', []):
                            all_items.append({
                                'קובץ': plan.filename,
                                'פרק': chapter.get('name', ''),
                                'קוד פריט': item.get('code', ''),
                                'קוד דקל': item.get('dekel_code', ''),
                                'תיאור': item.get('description', ''),
                                'כמות': item.get('quantity', 0),
                                'יחידה': item.get('unit', ''),
                                'מחיר יחידה': item.get('unit_price', 0),
                                'סה"כ': item.get('total', 0),
                                'ביטחון': f"{item.get('confidence', 0) * 100:.0f}%"
                            })
                except (json.JSONDecodeError, TypeError):
                    pass

            # Also get materials from MaterialQuantity table
            materials = db.query(models.MaterialQuantity).filter(
                models.MaterialQuantity.plan_id == plan.id
            ).all()

            if materials and not all_items:
                for mat in materials:
                    all_items.append({
                        'קובץ': plan.filename,
                        'פרק': '',
                        'קוד פריט': '',
                        'קוד דקל': '',
                        'תיאור': mat.material_name,
                        'כמות': mat.quantity,
                        'יחידה': mat.unit,
                        'מחיר יחידה': 0,
                        'סה"כ': 0,
                        'ביטחון': f"{mat.confidence_score * 100:.0f}%"
                    })

        if all_items:
            df = pd.DataFrame(all_items)
            df.to_excel(writer, index=False, sheet_name='כתב כמויות מאוחד')

        # Add summary sheet
        summary_data = []
        for plan in plans:
            summary_data.append({
                'קובץ': plan.filename,
                'סה"כ לפני מע"מ': plan.boq_subtotal or 0,
                'מע"מ': plan.boq_vat_amount or 0,
                'סה"כ כולל מע"מ': plan.boq_grand_total or 0,
                'סטטוס': plan.processing_status
            })

        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, index=False, sheet_name='סיכום')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=BOQ_Project_{project.name}.xlsx"
        }
    )

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
