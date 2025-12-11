# BOQ Enhancement Implementation Guide
## Source Tracking & User Edits Feature

### 🎯 Overview
This guide documents the implementation of enhanced BOQ functionality with:
- Source tracking (file name + layer name for each item)
- User editing capabilities (modify quantity, price, notes)
- Soft delete functionality
- Enhanced Excel export with source information

### ✅ Completed Steps

#### 1. Database Model Created
**File:** `backend/app/models/boq_item.py`

The `BOQItem` model includes:
- Source tracking fields: `source_filename`, `source_layer`
- User modification fields: `user_notes`, `is_deleted`, `is_modified`
- All Dekel BOQ fields (chapter, item_code, quantity, unit_price, etc.)
- Foreign keys to `project` and `project_plan` (optional)

**Database Table:** Created successfully using `backend/create_boq_table.py`

#### 2. Pydantic Schemas Created
**File:** `backend/app/schemas/boq_item.py`

Schemas include:
- `BOQItemCreate` - For creating new items
- `BOQItemUpdate` - For editing existing items (quantity, price, notes, soft delete)
- `BOQItem` - For returning items to frontend

#### 3. Model Relationships Updated
- `Project.boq_items` relationship added
- `ProjectPlan.boq_items` relationship added

---

### 🚧 Remaining Implementation Steps

#### Step 4: Create BOQ Items API Endpoints

**File to create:** `backend/app/api/endpoints/boq_items.py`

```python
"""
BOQ Items CRUD API
Allows users to edit, delete, and annotate BOQ line items
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app import models, schemas

router = APIRouter()

@router.get("/{project_id}/boq/items", response_model=List[schemas.BOQItem])
def get_boq_items(
    project_id: int,
    include_deleted: bool = False,
    db: Session = Depends(deps.get_db)
):
    """Get all BOQ items for a project"""
    query = db.query(models.BOQItem).filter(models.BOQItem.project_id == project_id)

    if not include_deleted:
        query = query.filter(models.BOQItem.is_deleted == False)

    items = query.order_by(models.BOQItem.chapter_code, models.BOQItem.item_code).all()
    return items

@router.patch("/{project_id}/boq/items/{item_id}", response_model=schemas.BOQItem)
def update_boq_item(
    project_id: int,
    item_id: int,
    update: schemas.BOQItemUpdate,
    db: Session = Depends(deps.get_db)
):
    """Update BOQ item (quantity, price, notes)"""
    item = db.query(models.BOQItem).filter(
        models.BOQItem.id == item_id,
        models.BOQItem.project_id == project_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")

    # Update fields
    if update.quantity is not None:
        item.quantity = update.quantity
        item.is_modified = True

    if update.description_he is not None:
        item.description_he = update.description_he
        item.is_modified = True

    if update.unit_price is not None:
        item.unit_price = update.unit_price
        item.is_modified = True

    if update.user_notes is not None:
        item.user_notes = update.user_notes
        item.is_modified = True

    if update.is_deleted is not None:
        item.is_deleted = update.is_deleted

    # Recalculate total
    item.total_price = item.quantity * item.unit_price

    db.commit()
    db.refresh(item)
    return item

@router.delete("/{project_id}/boq/items/{item_id}")
def delete_boq_item(
    project_id: int,
    item_id: int,
    db: Session = Depends(deps.get_db)
):
    """Soft delete BOQ item"""
    item = db.query(models.BOQItem).filter(
        models.BOQItem.id == item_id,
        models.BOQItem.project_id == project_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")

    item.is_deleted = True
    db.commit()

    return {"message": "Item deleted successfully"}
```

**Add to API router:** In `backend/app/api/api.py`:
```python
from app.api.endpoints import boq_items

api_router.include_router(boq_items.router, prefix="/projects", tags=["boq-items"])
```

---

#### Step 5: Update BOQ Generation to Save to Database

**File to modify:** `backend/app/services/boq/israeli_boq_service.py`

Add a function to save BOQ items to database:

```python
def save_boq_to_database(
    project_id: int,
    plan_id: int,
    boq_response: Dict,
    filename: str,
    selected_layers: List[str],
    db: Session
):
    """
    Save generated BOQ items to database with source tracking.

    Args:
        project_id: Project ID
        plan_id: Plan ID (source file)
        boq_response: AI-generated BOQ response
        filename: Source DWG filename
        selected_layers: List of selected layer names
        db: Database session
    """
    from app.models import BOQItem

    # Clear existing items for this project
    db.query(BOQItem).filter(BOQItem.project_id == project_id).delete()

    # Parse BOQ response and create items
    for chapter in boq_response.get("chapters", []):
        chapter_code = chapter["chapter_code"]
        chapter_name_he = chapter["chapter_name_he"]
        chapter_name_en = chapter.get("chapter_name_en", "")

        for item in chapter.get("items", []):
            # Determine source layer (simplified - you may want more sophisticated logic)
            source_layer = ", ".join(selected_layers[:3]) if selected_layers else "Multiple layers"

            boq_item = BOQItem(
                project_id=project_id,
                plan_id=plan_id,
                chapter_code=chapter_code,
                chapter_name_he=chapter_name_he,
                chapter_name_en=chapter_name_en,
                item_code=item["item_code"],
                description_he=item["description_he"],
                description_en=item.get("description_en", ""),
                quantity=item["quantity"],
                unit=item["unit"],
                unit_price=item["unit_price"],
                total_price=item["total_price"],
                source_filename=filename,
                source_layer=source_layer,
                confidence=item.get("confidence", 0.8),
                is_deleted=False,
                is_modified=False
            )
            db.add(boq_item)

    db.commit()
```

**Call this function** in the BOQ generation code after AI generates the BOQ.

---

#### Step 6: Update GET `/projects/{id}/boq` Endpoint

**File to modify:** `backend/app/api/endpoints/projects.py`

Change the `/boq` endpoint to return data from database instead of JSON blob:

```python
@router.get("/{project_id}/boq")
def get_project_boq(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Get project BOQ from database with source tracking"""
    from app.models import BOQItem

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all non-deleted items
    items = db.query(BOQItem).filter(
        BOQItem.project_id == project_id,
        BOQItem.is_deleted == False
    ).order_by(BOQItem.chapter_code, BOQItem.item_code).all()

    # Group by chapter
    chapters = {}
    for item in items:
        if item.chapter_code not in chapters:
            chapters[item.chapter_code] = {
                "chapter_code": item.chapter_code,
                "chapter_name_he": item.chapter_name_he,
                "chapter_name_en": item.chapter_name_en,
                "items": [],
                "chapter_total": 0
            }

        chapters[item.chapter_code]["items"].append({
            "id": item.id,  # Include ID for editing
            "item_code": item.item_code,
            "description_he": item.description_he,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "source_filename": item.source_filename,  # NEW
            "source_layer": item.source_layer,  # NEW
            "confidence": item.confidence,
            "user_notes": item.user_notes,  # NEW
            "is_modified": item.is_modified  # NEW
        })
        chapters[item.chapter_code]["chapter_total"] += item.total_price

    # Calculate totals
    subtotal = sum(ch["chapter_total"] for ch in chapters.values())
    vat_amount = subtotal * 0.17
    grand_total = subtotal + vat_amount

    return {
        "project_name": project.name,
        "chapters": list(chapters.values()),
        "summary": {
            "subtotal": round(subtotal, 2),
            "vat_rate": 0.17,
            "vat_amount": round(vat_amount, 2),
            "grand_total": round(grand_total, 2),
            "total_files": len(project.plans),
            "total_items": len(items)
        },
        "source_files": [plan.filename for plan in project.plans]
    }
```

---

#### Step 7: Update Excel Export

**File to modify:** `backend/app/api/endpoints/export.py`

Add source columns to Excel export:

```python
# In the Excel generation function, add new columns:
worksheet.cell(row=row_num, column=1, value=item["item_code"])
worksheet.cell(row=row_num, column=2, value=item["description_he"])
worksheet.cell(row=row_num, column=3, value=item["quantity"])
worksheet.cell(row=row_num, column=4, value=item["unit"])
worksheet.cell(row=row_num, column=5, value=item["unit_price"])
worksheet.cell(row=row_num, column=6, value=item["total_price"])
worksheet.cell(row=row_num, column=7, value=item.get("source_filename", ""))  # NEW
worksheet.cell(row=row_num, column=8, value=item.get("source_layer", ""))  # NEW
worksheet.cell(row=row_num, column=9, value=item.get("user_notes", ""))  # NEW
worksheet.cell(row=row_num, column=10, value=f"{item['confidence']*100:.0f}%")
```

Update headers accordingly.

---

#### Step 8: Frontend - Update BOQ Display

**File to modify:** `frontend/src/app/dashboard/projects/[id]/page.tsx`

Add new columns to the BOQ table:

```typescript
<TableCell>קוד</TableCell>
<TableCell>תיאור</TableCell>
<TableCell align="right">כמות</TableCell>
<TableCell>יחידה</TableCell>
<TableCell align="right">מחיר יח׳</TableCell>
<TableCell align="right">סה״כ</TableCell>
<TableCell>קובץ מקור</TableCell>  {/* NEW */}
<TableCell>שכבה</TableCell>  {/* NEW */}
<TableCell>הערות</TableCell>  {/* NEW */}
<TableCell align="center">אמינות</TableCell>
<TableCell align="center">פעולות</TableCell>  {/* NEW */}
```

In the table rows:

```typescript
<TableCell>{item.source_filename || '-'}</TableCell>
<TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
  {item.source_layer || '-'}
</TableCell>
<TableCell>
  <TextField
    size="small"
    multiline
    value={item.user_notes || ''}
    onChange={(e) => handleUpdateNotes(item.id, e.target.value)}
    placeholder="הוסף הערה..."
  />
</TableCell>
```

---

#### Step 9: Frontend - Add Inline Editing

Create an editable BOQ table component with:
- Inline editing for quantity and price
- Notes text field
- Delete button with confirmation
- Save changes to backend via API

---

### 📝 Testing Checklist

After completing all steps:

- [ ] Create new project and generate BOQ
- [ ] Verify source file and layer appear in BOQ
- [ ] Test editing quantity - recalculates total
- [ ] Test editing price - recalculates total
- [ ] Test adding notes
- [ ] Test soft delete (item disappears but not from DB)
- [ ] Test Excel export includes source info and notes
- [ ] Test that edits persist after page refresh

---

### 🔄 Migration Path for Existing Projects

For existing projects with BOQ data in JSON format:

```python
# Migration script to populate boq_items from existing JSON data
def migrate_existing_boqs(db: Session):
    projects = db.query(Project).all()

    for project in projects:
        for plan in project.plans:
            if plan.boq_data:
                boq_json = json.loads(plan.boq_data)
                # Parse and create BOQItem records
                # (Similar to save_boq_to_database function)
```

---

### 💡 Future Enhancements

1. **Bulk Operations**: Select multiple items and apply changes
2. **Change History**: Track all modifications with timestamps
3. **Templates**: Save common adjustments as templates
4. **Comparison**: Compare original AI-generated vs user-modified values
5. **Comments**: Allow multiple comments per item with threading

---

###Need Help?

This guide provides the complete structure. The key files that need updates are:
1. `backend/app/api/endpoints/boq_items.py` (create new)
2. `backend/app/api/endpoints/projects.py` (modify /boq endpoint)
3. `backend/app/services/boq/israeli_boq_service.py` (add save_boq_to_database)
4. `backend/app/api/endpoints/export.py` (add columns)
5. `frontend/src/app/dashboard/projects/[id]/page.tsx` (add columns + editing UI)

Each section above has code snippets you can use directly.
