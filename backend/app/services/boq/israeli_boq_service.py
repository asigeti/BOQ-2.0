"""
Israeli BOQ Service - כתב כמויות ישראלי
==========================================

This service generates professional Israeli Bill of Quantities (כתב כמויות)
from AutoCAD DWG files using:
1. AutoCAD COM interface for accurate data extraction
2. OpenAI GPT-4 for intelligent material classification
3. Dekel Pricing (מחירון דקל) for accurate Israeli construction prices

The output follows Israeli construction standards and includes:
- Proper chapter structure (פרקים)
- Hebrew material names
- Dekel pricing codes
- VAT calculations (מע"מ)
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from openai import OpenAI

from app.services.pricing.dekel_pricing import DekelPricing

logger = logging.getLogger(__name__)


# Israeli BOQ Expert System Prompt
ISRAELI_BOQ_SYSTEM_PROMPT = """אתה כתב כמויות (Quantity Surveyor) מקצועי ישראלי עם 25 שנות ניסיון.
המומחיות שלך כוללת:
- ניתוח תוכניות אדריכליות והנדסיות
- הכנת כתבי כמויות מקצועיים
- תמחור לפי מחירון דקל
- תקני בנייה ישראליים

משימתך: לנתח נתונים שחולצו מקובץ AutoCAD DWG וליצור כתב כמויות מקצועי.

כללי עבודה:
1. סווג כל פריט לפרק המתאים (01-עפר, 02-בטון, 03-בניה, וכו')
2. השתמש במונחים מקצועיים בעברית
3. התאם לקודי מחירון דקל כאשר אפשרי
4. חשב כמויות במדויק לפי יחידות מידה תקניות
5. הוסף הערות מקצועיות לפריטים מיוחדים
6. אם יש חוסר מידע - ציין זאת והערך בזהירות

מבנה הפרקים הסטנדרטי:
- פרק 01: עבודות עפר
- פרק 02: בטון
- פרק 03: בניה (קירות בלוקים/לבנים/גבס)
- פרק 04: איטום
- פרק 05: טיח
- פרק 06: ריצוף וחיפוי
- פרק 07: אלומיניום וזכוכית
- פרק 08: נגרות (דלתות, ארונות)
- פרק 09: צבע
- פרק 10: אינסטלציה
- פרק 11: חשמל
- פרק 12: מיזוג אוויר

פורמט התשובה (JSON):
{
  "project_name": "שם הפרויקט",
  "date": "תאריך",
  "chapters": [
    {
      "chapter_code": "01",
      "chapter_name_he": "עבודות עפר",
      "chapter_name_en": "Earthworks",
      "items": [
        {
          "item_code": "01.01.01",
          "dekel_code": "01.01.01",
          "description_he": "תיאור בעברית",
          "description_en": "English description",
          "quantity": 100.0,
          "unit": "מ\"ק",
          "unit_price": 45.0,
          "total_price": 4500.0,
          "confidence": 0.95,
          "notes": "הערות"
        }
      ],
      "chapter_total": 4500.0
    }
  ],
  "summary": {
    "subtotal": 0.0,
    "vat_rate": 0.17,
    "vat_amount": 0.0,
    "grand_total": 0.0
  },
  "notes": ["הערות כלליות"]
}"""


@dataclass
class BOQItem:
    """Single BOQ line item"""
    item_code: str
    dekel_code: Optional[str]
    description_he: str
    description_en: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    confidence: float
    notes: Optional[str] = None


@dataclass
class BOQChapter:
    """BOQ Chapter (פרק)"""
    chapter_code: str
    chapter_name_he: str
    chapter_name_en: str
    items: List[BOQItem]
    chapter_total: float


@dataclass
class IsraeliBOQ:
    """Complete Israeli BOQ document"""
    project_name: str
    filename: str
    date: str
    chapters: List[BOQChapter]
    subtotal: float
    vat_rate: float
    vat_amount: float
    grand_total: float
    notes: List[str]
    extraction_method: str
    processing_time: float


class IsraeliBOQService:
    """
    Service for generating Israeli BOQ from CAD files.

    Flow:
    1. Extract raw data from AutoCAD (blocks, text, geometry)
    2. Send to GPT-4 with Israeli construction expert prompt
    3. Match items to Dekel pricing codes
    4. Generate structured BOQ report
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.dekel_pricing = DekelPricing()

    def generate_boq_from_raw_data(
        self,
        raw_data: Dict[str, Any],
        filename: str,
        project_name: Optional[str] = None
    ) -> IsraeliBOQ:
        """
        Generate Israeli BOQ from raw AutoCAD extraction data.

        Args:
            raw_data: Raw data extracted from AutoCAD (blocks, text, geometry, layers)
            filename: Original filename
            project_name: Optional project name

        Returns:
            IsraeliBOQ object with full pricing
        """
        start_time = datetime.now()

        # Get Dekel price list for AI context
        dekel_prices_json = self.dekel_pricing.export_price_list_json()

        # Prepare the prompt for GPT-4
        user_prompt = f"""נתח את הנתונים הבאים שחולצו מקובץ AutoCAD DWG וצור כתב כמויות מקצועי:

שם הקובץ: {filename}
שם הפרויקט: {project_name or 'לא צוין'}

═══════════════════════════════════════════════════════════════
נתוני AutoCAD שחולצו:
═══════════════════════════════════════════════════════════════

{json.dumps(raw_data, ensure_ascii=False, indent=2)}

═══════════════════════════════════════════════════════════════
מחירון דקל (לתמחור):
═══════════════════════════════════════════════════════════════

{dekel_prices_json}

═══════════════════════════════════════════════════════════════

הנחיות:
1. נתח את כל הבלוקים, הטקסטים והגאומטריות
2. סווג לפרקים המתאימים
3. התאם קודי מחירון דקל
4. חשב כמויות וסכומים
5. הוסף מע"מ 17%
6. החזר JSON בפורמט שצוין

חשוב: אם אינך בטוח בפריט, השתמש בביטחון נמוך (confidence < 0.7) והוסף הערה."""

        try:
            # Call GPT-4 for intelligent BOQ generation
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": ISRAELI_BOQ_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,  # Low temperature for consistency
                max_tokens=8000
            )

            # Parse the response
            boq_json = json.loads(response.choices[0].message.content)

            # Build the BOQ object
            processing_time = (datetime.now() - start_time).total_seconds()
            boq = self._build_boq_from_json(boq_json, filename, processing_time)

            logger.info(f"Generated Israeli BOQ with {len(boq.chapters)} chapters, total: {boq.grand_total:.2f} ILS")

            return boq

        except Exception as e:
            logger.error(f"Failed to generate BOQ: {e}")
            raise

    def _build_boq_from_json(self, boq_json: Dict, filename: str, processing_time: float) -> IsraeliBOQ:
        """Build IsraeliBOQ object from GPT response JSON"""

        chapters = []
        for ch_data in boq_json.get("chapters", []):
            items = []
            for item_data in ch_data.get("items", []):
                item = BOQItem(
                    item_code=item_data.get("item_code", ""),
                    dekel_code=item_data.get("dekel_code"),
                    description_he=item_data.get("description_he", ""),
                    description_en=item_data.get("description_en", ""),
                    quantity=float(item_data.get("quantity", 0)),
                    unit=item_data.get("unit", ""),
                    unit_price=float(item_data.get("unit_price", 0)),
                    total_price=float(item_data.get("total_price", 0)),
                    confidence=float(item_data.get("confidence", 0.5)),
                    notes=item_data.get("notes")
                )
                items.append(item)

            chapter = BOQChapter(
                chapter_code=ch_data.get("chapter_code", ""),
                chapter_name_he=ch_data.get("chapter_name_he", ""),
                chapter_name_en=ch_data.get("chapter_name_en", ""),
                items=items,
                chapter_total=float(ch_data.get("chapter_total", 0))
            )
            chapters.append(chapter)

        summary = boq_json.get("summary", {})

        return IsraeliBOQ(
            project_name=boq_json.get("project_name", ""),
            filename=filename,
            date=boq_json.get("date", datetime.now().strftime("%Y-%m-%d")),
            chapters=chapters,
            subtotal=float(summary.get("subtotal", 0)),
            vat_rate=float(summary.get("vat_rate", 0.17)),
            vat_amount=float(summary.get("vat_amount", 0)),
            grand_total=float(summary.get("grand_total", 0)),
            notes=boq_json.get("notes", []),
            extraction_method="autocad_com_gpt4",
            processing_time=processing_time
        )

    def boq_to_dict(self, boq: IsraeliBOQ) -> Dict:
        """Convert IsraeliBOQ to dictionary for JSON serialization"""
        return {
            "project_name": boq.project_name,
            "filename": boq.filename,
            "date": boq.date,
            "chapters": [
                {
                    "chapter_code": ch.chapter_code,
                    "chapter_name_he": ch.chapter_name_he,
                    "chapter_name_en": ch.chapter_name_en,
                    "items": [asdict(item) for item in ch.items],
                    "chapter_total": ch.chapter_total
                }
                for ch in boq.chapters
            ],
            "summary": {
                "subtotal": boq.subtotal,
                "vat_rate": boq.vat_rate,
                "vat_amount": boq.vat_amount,
                "grand_total": boq.grand_total
            },
            "notes": boq.notes,
            "metadata": {
                "extraction_method": boq.extraction_method,
                "processing_time_seconds": boq.processing_time,
                "generated_at": datetime.now().isoformat()
            }
        }

    def export_to_excel(self, boq: IsraeliBOQ, output_path: str):
        """Export BOQ to Excel file"""
        import pandas as pd

        # Create writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                "פרט": ["שם פרויקט", "שם קובץ", "תאריך", "סה\"כ לפני מע\"מ", "מע\"מ (17%)", "סה\"כ כולל מע\"מ"],
                "ערך": [boq.project_name, boq.filename, boq.date,
                        f"₪{boq.subtotal:,.2f}", f"₪{boq.vat_amount:,.2f}", f"₪{boq.grand_total:,.2f}"]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="סיכום", index=False)

            # Each chapter as a sheet
            for chapter in boq.chapters:
                if chapter.items:
                    items_data = []
                    for item in chapter.items:
                        items_data.append({
                            "קוד": item.item_code,
                            "קוד דקל": item.dekel_code or "",
                            "תיאור": item.description_he,
                            "Description": item.description_en,
                            "כמות": item.quantity,
                            "יחידה": item.unit,
                            "מחיר יחידה": item.unit_price,
                            "סה\"כ": item.total_price,
                            "ביטחון": f"{item.confidence*100:.0f}%",
                            "הערות": item.notes or ""
                        })

                    sheet_name = f"{chapter.chapter_code}-{chapter.chapter_name_he}"[:31]  # Excel limit
                    pd.DataFrame(items_data).to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Exported BOQ to Excel: {output_path}")


def generate_israeli_boq(raw_data: Dict, filename: str, project_name: str = None) -> Dict:
    """
    Convenience function to generate Israeli BOQ.

    Args:
        raw_data: Raw AutoCAD extraction data
        filename: Source filename
        project_name: Optional project name

    Returns:
        BOQ as dictionary
    """
    service = IsraeliBOQService()
    boq = service.generate_boq_from_raw_data(raw_data, filename, project_name)
    return service.boq_to_dict(boq)
