"""
PDF Plan Extractor for ConstructionAI Pro

Extracts detailed construction data from PDF plans using Vision AI.
Supports multiple plan types:
- Construction/Architectural plans
- Electrical plans
- Plumbing plans
- Windows & doors schedules
- Structural plans
- HVAC plans

Provider Priority: Gemini -> OpenAI -> Claude -> Ollama
"""

import os
import io
import re
import json
import base64
import logging
import tempfile
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from enum import Enum
from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Check for pdf2image
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
    logger.warning("pdf2image not installed. High-res PDF extraction will be limited.")

# Poppler path for Windows (installed via winget)
POPPLER_PATH = r"C:\poppler\poppler-25.11.0\Library\bin"

# Check for PyMuPDF (fitz) - better fallback that doesn't require poppler
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
    logger.info("PyMuPDF available for PDF rendering")
except ImportError:
    HAS_PYMUPDF = False
    logger.warning("PyMuPDF not installed. PDF rendering may be limited.")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class PlanType(str, Enum):
    """Types of construction plans"""
    ARCHITECTURAL = "architectural"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    STRUCTURAL = "structural"
    HVAC = "hvac"
    WINDOWS_DOORS = "windows_doors"
    FINISHING = "finishing"
    LANDSCAPE = "landscape"
    SITE_DEVELOPMENT = "site_development"
    TRAFFIC = "traffic"  # Traffic plans (סימון, תמרורים, חניות, מדרכות)
    BOQ_TABLE = "boq_table"  # Written BOQ documents with tables
    GENERAL = "general"


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails"""
    pass


# Common instructions for analyzing legends, comments, and side annotations
SIDE_ANNOTATIONS_INSTRUCTIONS = """
חשוב מאוד! סרוק את כל התכנית כולל:

📋 מקרא/לגנדה (Legend):
- סמלים וסימונים עם הסברים
- קודי צבעים ומשמעותם
- סימני קנה מידה
- מפתח סימונים (symbol key)

📝 הערות וטקסט בצדדים:
- הערות טכניות
- מפרטי חומרים
- הנחיות ביצוע
- הערות המתכנן
- דרישות מיוחדות

📊 טבלאות ורשימות:
- טבלאות כמויות
- רשימות חומרים (Bill of Materials)
- לוחות זמנים
- טבלאות דלתות/חלונות
- מפרטי גמרים

🏷️ כותרת ופרטי תכנית:
- שם הפרויקט
- מספר גיליון
- תאריך וגרסה
- קנה מידה
- שם המתכנן/משרד

📌 הערות שוליים והפניות:
- הפניות לתקנים
- הערות תיקונים (revisions)
- הפניות לתכניות אחרות
- הערות קבלן/מפקח

כלול את כל המידע הזה בתשובה שלך!

"""

# Detailed extraction prompts for each plan type (Hebrew + English)
EXTRACTION_PROMPTS = {
    PlanType.ARCHITECTURAL: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מומחה לכתבי כמויות בנייה המנתח תכנית אדריכלית/בנייה.

חלץ את כל הכמויות והמידות בפירוט מירבי. עבור כל פריט שנמצא, ספק:
- מידות מדויקות (אורך, רוחב, גובה, שטח)
- מפרטי חומרים אם נראים
- ספירה/כמות
- התייחסות למיקום/חדר

חלץ את הפרטים הבאים (היה ממצה):

1. חדרים ומרחבים:
   - שמות חדרים ומידות (א x ר)
   - שטחי רצפה במ"ר
   - גובהי תקרה אם מוצגים
   - היקפי חדרים

2. קירות:
   - אורכי קירות (פנימיים וחיצוניים)
   - עובי קירות
   - סוגי קירות (בטון, לבנים, גבס וכו')
   - גדלי פתחים (לדלתות/חלונות)

3. רצפות:
   - שטח רצפה כולל לכל חדר
   - סוגי גמר רצפה
   - שטחי רצפה מוגבהת
   - מדרגות/שינויי מפלסים

4. תקרות:
   - שטחי תקרה
   - סוגי תקרה (תלויה, צמודה וכו')
   - גובהי תקרה

5. דלתות:
   - ספירת דלתות לפי גודל (רוחב x גובה)
   - סוגי דלתות (בודדת, כפולה, הזזה וכו')
   - סוגי משקופים
   - כמות מכל סוג

6. חלונות:
   - ספירת חלונות לפי גודל
   - סוגי חלונות
   - גובהי אדן
   - חומרי מסגרת

7. מדרגות ורמפות:
   - מידות מדרגות
   - מספר שלחים/מדרכים
   - אורכי ושיפועי רמפות

8. עמודים וקורות (אם נראים):
   - גדלי וכמות עמודים
   - מידות קורות

החזר כ-JSON עם המבנה הבא:
{
    "plan_type": "architectural",
    "scale": "קנה מידה שזוהה או 'לא צוין'",
    "total_area_m2": מספר,
    "rooms": [{"name": "", "area_m2": 0, "dimensions": "", "perimeter_m": 0}],
    "walls": [{"type": "", "length_m": 0, "height_m": 0, "thickness_mm": 0, "area_m2": 0}],
    "floors": [{"room": "", "area_m2": 0, "finish": ""}],
    "ceilings": [{"room": "", "area_m2": 0, "type": "", "height_m": 0}],
    "doors": [{"size": "", "type": "", "quantity": 0, "material": ""}],
    "windows": [{"size": "", "type": "", "quantity": 0, "sill_height_m": 0}],
    "stairs": [{"type": "", "risers": 0, "width_m": 0, "length_m": 0}],
    "columns": [{"size": "", "quantity": 0, "height_m": 0}],
    "beams": [{"size": "", "length_m": 0, "quantity": 0}],
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "color_codes": [{"color": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "designer": "",
        "scale": ""
    },
    "schedules": [{"type": "", "items": []}],
    "material_specs": [{"material": "", "specification": "", "location": ""}],
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "references": ["הפניות לתקנים או תכניות אחרות"],
    "notes": ["הערות חשובות"],
    "confidence": 0.0 עד 1.0
}""",

    PlanType.ELECTRICAL: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מהנדס חשמל מומחה המנתח תכנית חשמל.

חלץ את כל רכיבי החשמל והכמויות בפירוט מירבי:

1. תאורה:
   - סוגי גופי תאורה וכמויות
   - ספירת תאורה שקועה
   - תאורה צמודת תקרה
   - נברשות/מנורות תלויות
   - תאורת חירום
   - שלטי יציאה
   - תאורת חוץ/נוף

2. שקעי חשמל:
   - שקעים רגילים (כמות)
   - שקעים כפולים
   - שקעי רצפה
   - שקעי חוץ (עמידים למים)
   - שקעי USB
   - שקעים ייעודיים (למכשירים)

3. מפסקים:
   - מפסקים בודדים
   - מפסקים כפולים
   - מפסקים משולשים
   - דימרים
   - מפסקים חכמים
   - מפסקי תנועה
   - מפסקי חוץ

4. לוחות חשמל:
   - גודל לוח ראשי (אמפר)
   - לוחות משניים
   - כמות מעגלים

5. הערכת אורכי כבלים:
   - אורכי כבלים משוערים
   - סוגי כבלים
   - אורכי תעלות

6. מערכות מיוחדות:
   - נקודות אינטרקום
   - מיקומי פעמון דלת
   - גלאי עשן
   - גלאי פחמן חד-חמצני
   - רכיבי מערכת אזעקה
   - נקודות רשת/נתונים
   - נקודות טלוויזיה/כבלים
   - נקודות טלפון

החזר כ-JSON:
{
    "plan_type": "electrical",
    "lighting": [{"type": "", "quantity": 0, "wattage": 0, "location": ""}],
    "outlets": [{"type": "", "quantity": 0, "amperage": 0, "location": ""}],
    "switches": [{"type": "", "quantity": 0, "gang": 0}],
    "panels": [{"type": "", "amperage": 0, "circuits": 0}],
    "wiring": [{"type": "", "estimated_length_m": 0}],
    "smoke_detectors": {"quantity": 0},
    "data_points": {"quantity": 0},
    "special_systems": [{"type": "", "quantity": 0}],
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "circuit_codes": [{"code": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "designer": ""
    },
    "schedules": [{"type": "", "items": []}],
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "notes": [],
    "confidence": 0.0 עד 1.0
}""",

    PlanType.PLUMBING: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מהנדס אינסטלציה מומחה המנתח תכנית אינסטלציה.

חלץ את כל רכיבי האינסטלציה והכמויות:

1. אביזרים סניטריים:
   - אסלות (סוג, כמות)
   - כיורים (סוג, כמות)
   - אמבטיות
   - מקלחות
   - בידה
   - משתנות
   - כיורי מטבח
   - כיורי כביסה
   - ניקוזי רצפה
   - ניקוזי גג

2. אספקת מים:
   - נקודות מים חמים
   - נקודות מים קרים
   - מיקומי דוד מים
   - גדלי צינורות ואורכים משוערים
   - שסתומים (שער, כדור, חד-כיווני)
   - מיקום שעון מים

3. ניקוז:
   - גדלי צינורות ניקוז
   - מיקומי צינורות אוורור
   - מיקומי פתחי ניקוי
   - מפריד שומן
   - חיבור לביוב

4. גז (אם רלוונטי):
   - נקודות גז
   - מיקום שעון גז
   - מסלולי צינורות גז

5. מיוחדים:
   - ראשי ספרינקלר
   - ברזי חוץ
   - חיבורי השקיה

החזר כ-JSON:
{
    "plan_type": "plumbing",
    "fixtures": {
        "toilets": [{"type": "", "quantity": 0}],
        "sinks": [{"type": "", "quantity": 0}],
        "bathtubs": {"quantity": 0},
        "showers": {"quantity": 0},
        "floor_drains": {"quantity": 0}
    },
    "water_supply": {
        "hot_water_points": 0,
        "cold_water_points": 0,
        "pipe_lengths_m": {"size_mm": 0, "length_m": 0}
    },
    "drainage": {
        "drain_points": 0,
        "vent_points": 0,
        "cleanouts": 0
    },
    "water_heaters": [{"type": "", "capacity_l": 0}],
    "special": [{"type": "", "quantity": 0}],
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "pipe_codes": [{"code": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "designer": ""
    },
    "schedules": [{"type": "", "items": []}],
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "notes": [],
    "confidence": 0.0 עד 1.0
}""",

    PlanType.WINDOWS_DOORS: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מומחה המנתח לוח זמנים/תכנית חלונות ודלתות.

חלץ את כל מפרטי החלונות והדלתות:

1. דלתות:
   - סימון/מספר דלת
   - רוחב x גובה (מ"מ או מ')
   - סוג דלת (בודדת, כפולה, הזזה, מתקפלת, מסתובבת)
   - חומר (עץ, מתכת, זכוכית, אלומיניום)
   - דירוג אש אם צוין
   - דרישות אביזרים
   - סוג מסגרת
   - גמר/צבע
   - זיגוג אם יש
   - כמות מכל סוג

2. חלונות:
   - סימון/מספר חלון
   - רוחב x גובה (מ"מ או מ')
   - סוג חלון (אלומיניום, ציר, קבוע, הזזה, ציר עליון)
   - חומר מסגרת (אלומיניום, PVC, עץ, פלדה)
   - סוג זיגוג (בודד, כפול, משולש, מרובד, מחוסם)
   - כיוון פתיחה
   - גובה אדן מהרצפה
   - כמות מכל סוג

3. קירות מסך/חזיתות חנויות:
   - שטח כולל
   - סוג מסגרת
   - מפרטי זכוכית

החזר כ-JSON:
{
    "plan_type": "windows_doors",
    "doors": [
        {
            "tag": "",
            "width_mm": 0,
            "height_mm": 0,
            "type": "",
            "material": "",
            "fire_rating": "",
            "hardware": "",
            "quantity": 0
        }
    ],
    "windows": [
        {
            "tag": "",
            "width_mm": 0,
            "height_mm": 0,
            "type": "",
            "frame_material": "",
            "glazing": "",
            "sill_height_mm": 0,
            "quantity": 0
        }
    ],
    "curtain_walls": [{"area_m2": 0, "type": ""}],
    "summary": {
        "total_doors": 0,
        "total_windows": 0,
        "total_door_area_m2": 0,
        "total_window_area_m2": 0
    },
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "type_codes": [{"code": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "designer": ""
    },
    "door_schedule": [{"tag": "", "specs": {}}],
    "window_schedule": [{"tag": "", "specs": {}}],
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "notes": [],
    "confidence": 0.0 עד 1.0
}""",

    PlanType.STRUCTURAL: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מהנדס קונסטרוקציה המנתח תכנית קונסטרוקציה.

חלץ את כל האלמנטים הקונסטרוקטיביים:

1. יסודות:
   - גדלי ועומקי כפות
   - קורות יסוד
   - מיקומי כלונסאות
   - שטחי רפסודה/משטח

2. עמודים:
   - גדלי עמודים (רוחב x עומק)
   - גובהי עמודים
   - כמות עמודים
   - זיון אם מוצג

3. קורות:
   - גדלי קורות
   - טווחי קורות
   - סוגי קורות (נסתרת, חשופה, קונזולית)

4. תקרות:
   - עובי תקרה
   - שטחי תקרה
   - סוגי תקרות (מלאה, צלעות, וופל)
   - רשת זיון

5. קירות:
   - מיקומי קירות גזירה
   - מידות קירות תומכים
   - עובי קירות

6. פלדה (אם רלוונטי):
   - גדלי קורות פלדה
   - גדלי עמודי פלדה
   - סוגי חיבורים

החזר כ-JSON:
{
    "plan_type": "structural",
    "foundations": [{"type": "", "dimensions": "", "depth_m": 0, "quantity": 0}],
    "columns": [{"size": "", "height_m": 0, "quantity": 0, "reinforcement": ""}],
    "beams": [{"size": "", "span_m": 0, "quantity": 0, "type": ""}],
    "slabs": [{"thickness_mm": 0, "area_m2": 0, "type": "", "reinforcement": ""}],
    "shear_walls": [{"length_m": 0, "height_m": 0, "thickness_mm": 0}],
    "retaining_walls": [{"length_m": 0, "height_m": 0, "thickness_mm": 0}],
    "steel_elements": [{"type": "", "size": "", "length_m": 0, "quantity": 0}],
    "concrete_volume_m3": 0,
    "reinforcement_tons": 0,
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "reinforcement_codes": [{"code": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "structural_engineer": ""
    },
    "schedules": {
        "column_schedule": [{"mark": "", "specs": {}}],
        "beam_schedule": [{"mark": "", "specs": {}}],
        "slab_schedule": [{"mark": "", "specs": {}}]
    },
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "design_standards": [""],
    "notes": [],
    "confidence": 0.0 עד 1.0
}""",

    PlanType.HVAC: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מהנדס מיזוג אוויר המנתח תכנית מיזוג.

חלץ את כל רכיבי המיזוג:

1. מיזוג אוויר:
   - יחידות פנימיות (סוג, הספק, כמות)
   - יחידות חיצוניות (סוג, הספק, כמות)
   - יחידות מפוצלות
   - יחידות מרכזיות
   - מערכות VRF/VRV

2. אוורור:
   - מפזרי אוויר
   - סורגי חזרה
   - מאווררי שאיבה
   - כניסות אוויר צח
   - תעלות (גדלים, אורכים)

3. חימום:
   - מחממים (סוג, כמות)
   - רדיאטורים
   - שטחי חימום תת-רצפתי
   - משאבות חום

4. בקרות:
   - תרמוסטטים
   - לוחות בקרה
   - חיישנים

5. תעלות:
   - גדלי תעלות
   - אורכי תעלות משוערים
   - דרישות בידוד

החזר כ-JSON:
{
    "plan_type": "hvac",
    "air_conditioning": {
        "indoor_units": [{"type": "", "capacity_kw": 0, "quantity": 0}],
        "outdoor_units": [{"type": "", "capacity_kw": 0, "quantity": 0}]
    },
    "ventilation": {
        "supply_diffusers": [{"size": "", "quantity": 0}],
        "return_grilles": [{"size": "", "quantity": 0}],
        "exhaust_fans": [{"cfm": 0, "quantity": 0}]
    },
    "heating": {
        "heaters": [{"type": "", "capacity_kw": 0, "quantity": 0}],
        "underfloor_area_m2": 0
    },
    "ductwork": {
        "estimated_length_m": 0,
        "sizes": []
    },
    "controls": {
        "thermostats": 0,
        "sensors": 0
    },
    "total_cooling_capacity_kw": 0,
    "total_heating_capacity_kw": 0,
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "duct_codes": [{"code": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "mechanical_engineer": ""
    },
    "schedules": {
        "equipment_schedule": [{"tag": "", "specs": {}}],
        "diffuser_schedule": [{"tag": "", "specs": {}}]
    },
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "notes": [],
    "confidence": 0.0 עד 1.0
}""",

    PlanType.FINISHING: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מומחה גמרים/פנים המנתח תכנית גמרים.

חלץ את כל מפרטי הגמרים:

1. ריצוף:
   - שטחי אריחים (סוג, גודל, שטח)
   - שטחי פרקט
   - שטחי שטיחים
   - שטחי ויניל/LVT
   - שטחי אפוקסי
   - שטחי אבן

2. גמרי קירות:
   - שטחי צבע
   - שטחי טפט
   - שטחי אריחים (חיפויים, קירות דגש)
   - שטחי חיפוי
   - פאנלים אקוסטיים

3. גמרי תקרה:
   - שטחי תקרה צבועה
   - שטחי תקרה תלויה
   - שטחי תקרה אקוסטית
   - מאפיינים מיוחדים

4. אלמנטים מובנים:
   - ארונות מטבח (מטר ליניארי)
   - ארונות (מטר ליניארי)
   - ארונות כיור
   - מדפים

5. פרזולים:
   - פנלים (מטר ליניארי)
   - קרניזים (מטר ליניארי)
   - אדנים (מטר ליניארי)
   - אדני חלונות

החזר כ-JSON:
{
    "plan_type": "finishing",
    "flooring": [{"type": "", "area_m2": 0, "specification": ""}],
    "wall_finishes": [{"type": "", "area_m2": 0, "specification": ""}],
    "ceiling_finishes": [{"type": "", "area_m2": 0}],
    "cabinetry": {
        "kitchen_cabinets_lm": 0,
        "wardrobes_lm": 0,
        "vanities": 0
    },
    "trims": {
        "skirting_lm": 0,
        "cornice_lm": 0,
        "architrave_lm": 0
    },
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "finish_codes": [{"code": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "designer": ""
    },
    "finish_schedule": [{"room": "", "floor": "", "walls": "", "ceiling": ""}],
    "material_specs": [{"material": "", "manufacturer": "", "specification": ""}],
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "notes": [],
    "confidence": 0.0 עד 1.0
}""",

    PlanType.SITE_DEVELOPMENT: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מומחה לכתבי כמויות (BOQ) ומפרטים טכניים לפרויקטי פיתוח שטח בישראל.

🎯 המשימה: חלץ כתב כמויות מלא מתכנית הפיתוח!

⚠️ חשוב מאוד! בתכנית פיתוח יש הרבה יותר מ-2 פריטים!
סרוק את כל התכנית וחלץ כל אחד מהפריטים הבאים:

═══════════════════════════════════════════════════
📋 שלב 1: קרא את המקרא (לגנדה) בקפידה!
═══════════════════════════════════════════════════
כל סמל, צבע, או קו במקרא = פריט נפרד בכתב הכמויות!

═══════════════════════════════════════════════════
📋 שלב 2: חפש וחלץ את כל הקטגוריות הבאות:
═══════════════════════════════════════════════════

🔴 09.01 - משטחים וריצוף (לפי סוג!):
   • משטחי בטיחות גומי (גמיש, יצוק באתר)
   • ריצוף משתלב (אינטרלוק) - כל צבע בנפרד!
   • מרצפות בטון
   • דשא סינתטי / טבעי
   • משטחי EPDM / גומי בלימה
   • אספלט
   • חצץ / חלוקי נחל

🔵 09.02 - מתקני משחק וספורט:
   • מתקני טיפוס (סולם, קיר, רשת)
   • נדנדות (מושב בודד/כפול)
   • מגלשות
   • קרוסלות
   • מתקנים משולבים (קומפלקס)
   • מתקני כושר
   • מתקני ספורט (כדורסל, כדורגל)

🟢 09.03 - ריהוט גן וחוץ:
   • ספסלים (עם/בלי משענת)
   • שולחנות פיקניק
   • אשפתונים
   • ברזייה / שתייניה
   • מעמדי אופניים
   • עמודי קשירה

🟡 09.04 - הצללה ומבנים:
   • סככות צל (ממברנה/בד)
   • פרגולות עץ/מתכת
   • מבנה שירותים
   • מחסן/צריף

🟣 09.05 - גדרות ומעקות:
   • גדר רשת
   • גדר עץ
   • גדר מתכת
   • מעקה בטיחות
   • שערים

🟤 09.06 - גינון ונוף:
   • עצים (לפי סוג וגודל)
   • שיחים
   • צמחי כיסוי קרקע
   • דשא טבעי
   • מערכת השקיה

⚪ 09.07 - תשתיות:
   • תאורה (עמודים, בולרדים)
   • ניקוז (תעלות, מרזבים)
   • אבני שפה/גבול
   • מגבילי חניה

═══════════════════════════════════════════════════
📋 שלב 3: מדוד כמויות!
═══════════════════════════════════════════════════
חפש מספרים בתכנית:
• שטחים: XXX מ"ר / m²
• אורכים: XX.XX מ' / מ"ל
• כמויות: ספירת יחידות

═══════════════════════════════════════════════════
📤 פורמט הפלט - JSON מפורט:
═══════════════════════════════════════════════════
{
    "plan_type": "site_development",
    "scale": "קנה מידה",
    "project_name": "שם הפרויקט",
    "surfaces": [
        {"type": "משטח בטיחות גומי גמיש", "area_m2": 143.6, "specification": "עובי 45 מ\"מ"},
        {"type": "ריצוף משתלב אדום", "area_m2": 225.6, "specification": "6 ס\"מ"},
        {"type": "דשא סינתטי", "area_m2": 80.0, "specification": "גובה 35 מ\"מ"}
    ],
    "play_equipment": [
        {"type": "מתקן טיפוס משולב", "quantity": 1, "specification": "גילאי 3-12"},
        {"type": "נדנדה כפולה", "quantity": 2, "specification": ""},
        {"type": "מגלשה", "quantity": 1, "specification": "גובה 1.5 מ'"}
    ],
    "site_furniture": [
        {"type": "ספסל עם משענת", "quantity": 6, "specification": "עץ טיק"},
        {"type": "אשפתון", "quantity": 4, "specification": ""},
        {"type": "ברזייה", "quantity": 2, "specification": "נירוסטה"}
    ],
    "shade_structures": [
        {"type": "סככת צל ממברנה", "area_m2": 120.0, "specification": ""}
    ],
    "fencing": [
        {"type": "גדר רשת ירוקה", "length_m": 85.0, "height_m": 1.5},
        {"type": "שער כניסה", "quantity": 2, "width_m": 1.2}
    ],
    "landscaping": {
        "trees": [{"type": "עץ צל בוגר", "quantity": 8}],
        "shrubs": [{"type": "שיח נוי", "quantity": 25}],
        "grass_area_m2": 150.0,
        "irrigation_points": 12
    },
    "infrastructure": {
        "lighting": [{"type": "עמוד תאורה", "quantity": 6}],
        "drainage": [{"type": "תעלת ניקוז", "length_m": 45.0}],
        "borders": [{"type": "אבן שפה בטון", "length_m": 120.0}]
    },
    "legend_items": ["רשימת כל הפריטים מהמקרא"],
    "extracted_items": [
        {"item_code": "09.001", "description": "משטח בטיחות גומי גמיש לחצרות משחקים", "quantity": 143.6, "unit": "מ\"ר", "category": "surfaces"},
        {"item_code": "09.002", "description": "ריצוף משתלב צבעוני עם תשתית", "quantity": 225.6, "unit": "מ\"ר", "category": "surfaces"},
        {"item_code": "09.010", "description": "מתקן משחק משולב לגילאי 3-12", "quantity": 1, "unit": "יח'", "category": "play_equipment"},
        {"item_code": "09.020", "description": "ספסל ישיבה עם משענת גב", "quantity": 6, "unit": "יח'", "category": "furniture"}
    ],
    "confidence": 0.85
}

═══════════════════════════════════════════════════
⚠️ הנחיות חשובות:
═══════════════════════════════════════════════════
1. כל פריט מהמקרא = שורה נפרדת ב-extracted_items!
2. חפש מספרים ליד כל אזור בתכנית
3. אם אין מספר מדויק - נסה לחשב לפי קנה מידה
4. כל צבע שונה של ריצוף = פריט נפרד!
5. השתמש בקודי פריט: 09.XXX

🎯 המטרה: לייצר כתב כמויות מלא שאפשר לתמחר!""",

    PlanType.TRAFFIC: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מומחה לכתבי כמויות (BOQ) ותמחור עבודות תנועה וכבישים בישראל.

🎯 המשימה: חלץ כתב כמויות מלא מתכנית תנועה/כבישים!

⚠️ חשוב מאוד! תכנית תנועה כוללת הרבה רכיבים - סרוק הכל!

═══════════════════════════════════════════════════
📋 שלב 1: קרא את המקרא (לגנדה) בקפידה!
═══════════════════════════════════════════════════
כל סמל, צבע, או קו במקרא = פריט נפרד בכתב הכמויות!
- סמני סימון כביש (קווים, חצים, פסים)
- סמלי תמרורים (סוג, מיקום)
- סמלי תאורה (עמודים, גוף תאורה)
- סמלי מעקות ומחסומים

═══════════════════════════════════════════════════
📋 שלב 2: חפש וחלץ את כל הקטגוריות הבאות:
═══════════════════════════════════════════════════

🔴 14.01 - סימון אופקי (Road Markings):
   • קו הפרדה רציף (לבן/צהוב) - אורך במ"ל
   • קו הפרדה מקוטע - אורך במ"ל
   • קו שפה - אורך במ"ל
   • פסי חציה (zebra) - מספר מעברים
   • חץ ישר/פניה - כמות יחידות
   • סימון "עצור" / "האט" - כמות
   • סימון חניה (לבן/כחול/נכה) - כמות תאים
   • שטח צבוע (אדום/צהוב) - שטח במ"ר

🔵 14.02 - תמרורים ושילוט (Signs & Signage):
   • תמרורי אזהרה (משולש) - כמות
   • תמרורי איסור (עיגול אדום) - כמות
   • תמרורי חובה (עיגול כחול) - כמות
   • תמרורי הדרכה (מלבן ירוק/כחול) - כמות
   • שלטי כיוון - כמות
   • עמודי תמרור - כמות וגובה

🟢 14.03 - מעקות בטיחות (Safety Barriers):
   • מעקה W-beam פלדה - אורך במ"ל
   • מעקה בטון (New Jersey) - אורך במ"ל
   • מעקה כבלים - אורך במ"ל
   • מחסומי בטון - כמות
   • בולרדים/עמודונים - כמות
   • סופי מעקה (terminals) - כמות

🟡 14.04 - פסי האטה ובליטות (Speed Control):
   • פס האטה גומי - כמות
   • פס האטה אספלט - כמות
   • בליטה מרוצפת - כמות
   • כרית האטה (speed cushion) - כמות
   • שולחן תנועה - שטח במ"ר

🟣 14.05 - תאורת רחוב (Street Lighting):
   • עמודי תאורה (גובה) - כמות
   • גופי תאורה LED - כמות
   • בולרדי תאורה - כמות
   • פרוז'קטורים - כמות
   • כבלי חשמל - אורך במ"ל

🟤 14.06 - איי תנועה (Traffic Islands):
   • אי תנועה מוגבה - שטח במ"ר
   • אי מפריד מרוצף - שטח במ"ר
   • כיכר תנועה - שטח כולל במ"ר
   • אבני שפה עגולות - אורך במ"ל
   • עמודי הכוונה גמישים - כמות

⚪ 14.07 - חניות (Parking):
   • חניה רגילה - כמות תאים
   • חניית נכים - כמות
   • חניית אופניים - כמות
   • מחסומי חניה - כמות
   • תשלום חניה (פרקומט) - כמות
   • סימון תאי חניה - שטח במ"ר

🔷 14.08 - מדרכות ושבילים (Sidewalks & Paths):
   • מדרכה בטון - שטח במ"ר
   • מדרכה מרוצפת - שטח במ"ר
   • שביל אופניים - שטח במ"ר
   • רמפת נכים - כמות
   • אבני שפה שקועות - אורך במ"ל
   • ריצוף טקטילי (לעיוורים) - שטח במ"ר
   • גדרות מדרכה - אורך במ"ל

🔶 14.09 - ניקוז כבישים (Road Drainage):
   • תעלת ניקוז בטון - אורך במ"ל
   • תא ניקוז (catch basin) - כמות
   • צינור ניקוז - אורך וקוטר
   • סכר עילי - כמות
   • מפריד שמנים - כמות

═══════════════════════════════════════════════════
📋 שלב 3: מדוד כמויות!
═══════════════════════════════════════════════════
חפש מספרים בתכנית:
• אורכים: XX.XX מ' / מ"ל
• שטחים: XXX מ"ר / m²
• כמויות: ספירת יחידות

═══════════════════════════════════════════════════
📤 פורמט הפלט - JSON מפורט:
═══════════════════════════════════════════════════
{
    "plan_type": "traffic",
    "scale": "קנה מידה",
    "project_name": "שם הפרויקט",
    "road_markings": [
        {"type": "קו הפרדה רציף לבן", "length_m": 250.0, "width_cm": 15},
        {"type": "פסי חציה", "quantity": 4, "width_m": 4.0},
        {"type": "חץ ישר", "quantity": 12}
    ],
    "signs": [
        {"type": "תמרור עצור", "code": "301", "quantity": 2},
        {"type": "תמרור מהירות 50", "code": "420", "quantity": 4},
        {"type": "עמוד תמרור 3 מטר", "quantity": 6}
    ],
    "barriers": [
        {"type": "מעקה W-beam", "length_m": 120.0, "height_m": 0.75},
        {"type": "בולרד פלדה", "quantity": 15}
    ],
    "speed_control": [
        {"type": "פס האטה גומי", "quantity": 3},
        {"type": "שולחן תנועה", "area_m2": 45.0}
    ],
    "lighting": [
        {"type": "עמוד תאורה 8 מטר", "quantity": 12},
        {"type": "גוף תאורה LED 100W", "quantity": 12}
    ],
    "traffic_islands": [
        {"type": "אי תנועה מוגבה", "area_m2": 25.0},
        {"type": "אבן שפה עגולה", "length_m": 35.0}
    ],
    "parking": [
        {"type": "חניה רגילה", "quantity": 45},
        {"type": "חניית נכים", "quantity": 3},
        {"type": "סימון תאי חניה", "area_m2": 560.0}
    ],
    "sidewalks": [
        {"type": "מדרכה מרוצפת", "area_m2": 320.0},
        {"type": "שביל אופניים", "area_m2": 180.0, "length_m": 90.0},
        {"type": "רמפת נכים", "quantity": 6}
    ],
    "drainage": [
        {"type": "תעלת ניקוז בטון", "length_m": 85.0},
        {"type": "תא ניקוז", "quantity": 8}
    ],
    "extracted_items": [
        {"item_code": "14.001", "description": "קו הפרדה רציף לבן רוחב 15 ס\"מ", "quantity": 250.0, "unit": "מ\"ל"},
        {"item_code": "14.002", "description": "פסי חציה רוחב 4 מ'", "quantity": 4, "unit": "יח'"},
        {"item_code": "14.010", "description": "תמרור עצור על עמוד", "quantity": 2, "unit": "יח'"},
        {"item_code": "14.020", "description": "מעקה בטיחות W-beam", "quantity": 120.0, "unit": "מ\"ל"},
        {"item_code": "14.050", "description": "עמוד תאורה LED גובה 8 מ'", "quantity": 12, "unit": "יח'"},
        {"item_code": "14.080", "description": "מדרכה מרוצפת אבן משתלבת", "quantity": 320.0, "unit": "מ\"ר"}
    ],
    "legend_items": ["רשימת כל הסמלים מהמקרא"],
    "confidence": 0.85
}

═══════════════════════════════════════════════════
⚠️ הנחיות חשובות:
═══════════════════════════════════════════════════
1. כל פריט מהמקרא = שורה נפרדת ב-extracted_items!
2. חפש אורכים של קווי סימון בתכנית
3. ספור תמרורים, עמודי תאורה, בולרדים
4. מדוד שטחי חניה, מדרכות, איי תנועה
5. השתמש בקודי פריט: 14.XXX
6. תקנים רלוונטיים: ת"י 920, ת"י 933, ת"י 1227

🎯 המטרה: לייצר כתב כמויות מלא לתכנית תנועה שאפשר לתמחר!""",

    PlanType.BOQ_TABLE: """אתה מומחה לכתבי כמויות בנייה המנתח מסמך כתב כמויות (BOQ).

זהו מסמך טבלאי עם פריטי עבודה וכמויות - לא תכנית גרפית!

חלץ את כל הפריטים מהטבלה. לכל שורה בטבלה חלץ:
- מספר סעיף (אם קיים)
- תאור הפריט/עבודה (בעברית)
- יחידה (מ"ר, מ"ל, יח', מ"ק, ק"ג, טון וכו')
- כמות (מספר)
- מחיר יחידה (אם קיים)
- סה"כ מחיר (אם קיים)

חשוב מאוד:
- קרא כל שורה בטבלה!
- אם יש כותרות פרקים/סעיפים - רשום אותם גם
- שים לב למידות בתוך התיאור (למשל "קיר 20 ס"מ")

החזר כ-JSON:
{
    "plan_type": "boq_table",
    "document_title": "כותרת המסמך",
    "chapter": "שם הפרק אם יש",
    "items": [
        {
            "item_number": "מספר סעיף",
            "description": "תיאור מלא בעברית",
            "unit": "יחידה",
            "quantity": 0,
            "unit_price": 0,
            "total_price": 0,
            "dimensions_in_description": "מידות שנמצאו בתיאור"
        }
    ],
    "subtotal": 0,
    "notes": ["הערות מהמסמך"],
    "confidence": 0.0
}""",

    PlanType.GENERAL: SIDE_ANNOTATIONS_INSTRUCTIONS + """אתה מומחה לכתבי כמויות בנייה המנתח תכנית בנייה.

זו נראית תכנית בנייה כללית. חלץ את כל הכמויות והמידות הנראות:

1. זהה מהו סוג התכנית (תכנית קומה, חזית, חתך, פרט וכו')
2. חלץ את כל המידות הנראות
3. ספור את כל הסמלים והאלמנטים
4. רשום את כל הערות הטקסט
5. זהה כל לוחות או טבלאות
6. חלץ כל מפרטים שמוזכרים

היה מפורט ככל האפשר. כלול:
- שמות ושטחי חדרים
- אורכי קירות
- ספירות דלתות וחלונות
- כל אביזרים המוצגים
- כל אלמנטים קונסטרוקטיביים
- כל אלמנטי מערכות
- מפרטי חומרים
- רשימות מידות

החזר כ-JSON:
{
    "plan_type": "general",
    "detected_plan_type": "",
    "scale": "",
    "rooms": [{"name": "", "area_m2": 0, "dimensions": ""}],
    "walls": [{"type": "", "length_m": 0}],
    "doors": [{"type": "", "size": "", "quantity": 0}],
    "windows": [{"type": "", "size": "", "quantity": 0}],
    "fixtures": [{"type": "", "quantity": 0}],
    "dimensions_noted": [],
    "text_annotations": [],
    "legend": {
        "symbols": [{"symbol": "", "description": ""}],
        "codes": [{"code": "", "meaning": ""}],
        "abbreviations": [{"abbr": "", "full_text": ""}]
    },
    "title_block": {
        "project_name": "",
        "sheet_number": "",
        "date": "",
        "revision": "",
        "designer": "",
        "scale": ""
    },
    "schedules": [],
    "material_specs": [{"material": "", "specification": ""}],
    "technical_notes": [""],
    "revision_notes": [{"rev": "", "date": "", "description": ""}],
    "references": [""],
    "notes": [],
    "confidence": 0.0 עד 1.0
}"""
}


def image_to_base64(image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def fix_json_string(json_str: str) -> str:
    """Fix common JSON issues from AI responses.

    - Removes trailing commas before } or ]
    - Handles other common malformations
    """
    # Remove trailing commas before } or ]
    fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
    return fixed


def parse_json_response(text: str) -> Dict:
    """Extract and parse JSON from AI response text.

    Handles common issues like trailing commas.
    """
    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        return {"raw_response": text, "error": "No JSON found in response"}

    raw_json = json_match.group()

    # Try parsing as-is first
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        pass

    # Try with fixes
    try:
        fixed_json = fix_json_string(raw_json)
        return json.loads(fixed_json)
    except json.JSONDecodeError as e:
        return {"raw_response": text[:500], "error": f"JSON parse error: {e}"}


def resize_image_for_api(image, max_size: int = 4096):
    """Resize image if too large for API.
    Using 4096 max for construction plans to preserve detail.
    Gemini and GPT-4o can handle larger images well.
    """
    if not HAS_PIL:
        return image
    width, height = image.size
    if width > max_size or height > max_size:
        from PIL import Image as PILImage
        ratio = min(max_size / width, max_size / height)
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, PILImage.Resampling.LANCZOS)
    return image


class VisionAIProvider:
    """Abstract base for vision AI providers"""
    def is_available(self) -> bool:
        return False

    def analyze_image(self, image, prompt: str) -> Dict:
        raise NotImplementedError


class GeminiVisionProvider(VisionAIProvider):
    """Google Gemini 3 Pro Vision API provider - PRIMARY

    Uses the NEW google-genai SDK with:
    - thinking_level=low for 5-10x faster responses
    - media_resolution for optimized image processing
    - Retry logic with exponential backoff
    - Streaming for better timeout handling
    """

    def __init__(self):
        from app.core.config import settings
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = None
        self.model_name = None

        if self.api_key:
            try:
                # NEW SDK - google-genai (not deprecated google-generativeai)
                from google import genai
                from google.genai import types

                # Initialize client with v1alpha API for Gemini 3 features
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        api_version='v1alpha',  # Required for thinking_level, media_resolution
                    )
                )

                self.model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-3-pro-preview')
                logger.info(f"Gemini Vision provider initialized with NEW SDK: {self.model_name} (PRIMARY)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
                import traceback
                logger.warning(f"Traceback: {traceback.format_exc()}")

    def is_available(self) -> bool:
        return self.client is not None

    def analyze_image(self, image, prompt: str) -> Dict:
        if not self.is_available():
            raise PDFExtractionError("Gemini not available")

        from google import genai
        from google.genai import types
        import time
        import random

        # Retry configuration
        max_retries = 3
        base_delay = 2  # seconds

        # Resize image for faster processing (1536px max)
        image = resize_image_for_api(image, max_size=1536)

        # Convert PIL image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        for attempt in range(max_retries):
            try:
                logger.info(f"Gemini 3 Pro attempt {attempt + 1}/{max_retries}")

                # Create image part with MEDIUM resolution for balance of speed/quality
                image_part = types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/png',
                )

                # Configure generation with Gemini 3 specific settings
                # NOTE: Gemini 3 Pro REQUIRES thinking mode, so we use minimal budget (1024)
                config = types.GenerateContentConfig(
                    temperature=0.2,  # Low temp for structured output
                    max_output_tokens=8192,
                    # Use minimal thinking for faster responses (model requires thinking)
                    thinking_config=types.ThinkingConfig(
                        thinkingBudget=1024,  # Minimal thinking (model requires > 0)
                    ),
                )

                # Generate content with streaming for better timeout handling
                response = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=[prompt, image_part],
                    config=config
                )

                # Collect streamed response chunks
                text_parts = []
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        text_parts.append(chunk.text)

                text = ''.join(text_parts)

                if not text or len(text) < 10:
                    raise PDFExtractionError("Empty response from Gemini 3 Pro")

                logger.info(f"Gemini 3 Pro SUCCESS on attempt {attempt + 1}")
                return parse_json_response(text)

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Gemini 3 Pro attempt {attempt + 1} failed: {error_msg}")

                # Check if it's a timeout/504 error
                is_timeout = "504" in error_msg or "Deadline" in error_msg or "timeout" in error_msg.lower() or "cancelled" in error_msg.lower()

                # If last attempt, raise
                if attempt == max_retries - 1:
                    logger.error(f"Gemini 3 Pro failed after {max_retries} attempts: {e}")
                    raise PDFExtractionError(f"Gemini 3 Pro failed after {max_retries} attempts: {e}")

                # Exponential backoff with jitter
                if is_timeout:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Timeout detected, waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                else:
                    # Non-timeout error, small delay before retry
                    time.sleep(1)
                continue

        raise PDFExtractionError("Gemini 3 Pro: All retry attempts exhausted")


class GeminiFlashProvider(VisionAIProvider):
    """Google Gemini 2.5 Flash - FAST FALLBACK before OpenAI

    Uses the NEW google-genai SDK with streaming and retry logic.
    NOTE: Uses v1 API (not v1alpha) since Flash doesn't need ThinkingConfig.
    """

    def __init__(self):
        from app.core.config import settings
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = None
        self.model_name = "gemini-2.0-flash"  # Stable version - fast & consistent

        if self.api_key:
            try:
                from google import genai
                from google.genai import types

                # Use v1 API (not v1alpha) - Flash doesn't need thinking features
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        api_version='v1',  # v1 for Flash (stable API)
                    )
                )
                logger.info(f"Gemini Flash provider initialized: {self.model_name} (PRIMARY - consistent results)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Flash: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def analyze_image(self, image, prompt: str) -> Dict:
        if not self.is_available():
            raise PDFExtractionError("Gemini Flash not available")

        from google import genai
        from google.genai import types
        import time
        import random

        max_retries = 2  # Flash is faster, fewer retries needed
        base_delay = 1

        # Resize for faster processing
        image = resize_image_for_api(image, max_size=1536)

        # Convert PIL image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        for attempt in range(max_retries):
            try:
                logger.info(f"Gemini Flash attempt {attempt + 1}/{max_retries}")

                image_part = types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/png',
                )

                config = types.GenerateContentConfig(
                    temperature=0.1,  # Very low for consistent extraction results
                    max_output_tokens=8192,
                )

                # Use streaming for better timeout handling
                response = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=[prompt, image_part],
                    config=config
                )

                text_parts = []
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        text_parts.append(chunk.text)

                text = ''.join(text_parts)

                if not text or len(text) < 10:
                    raise PDFExtractionError("Empty response from Gemini Flash")

                logger.info(f"Gemini Flash SUCCESS on attempt {attempt + 1}")
                return parse_json_response(text)

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Gemini Flash attempt {attempt + 1} failed: {error_msg}")

                if attempt == max_retries - 1:
                    logger.error(f"Gemini Flash failed after {max_retries} attempts: {e}")
                    raise PDFExtractionError(f"Gemini Flash failed: {e}")

                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.info(f"Waiting {delay:.1f}s before retry...")
                time.sleep(delay)
                continue

        raise PDFExtractionError("Gemini Flash: All retry attempts exhausted")


class OpenAIVisionProvider(VisionAIProvider):
    """OpenAI GPT-4 Vision API provider - FALLBACK 1"""

    def __init__(self):
        from app.core.config import settings
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get("OPENAI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI Vision provider initialized (FALLBACK 1)")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def analyze_image(self, image, prompt: str) -> Dict:
        if not self.is_available():
            raise PDFExtractionError("OpenAI not available")

        try:
            # Resize and convert to base64
            image = resize_image_for_api(image)
            base64_image = image_to_base64(image)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )

            text = response.choices[0].message.content

            # Extract and parse JSON with error handling
            return parse_json_response(text)

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise PDFExtractionError(f"OpenAI analysis failed: {e}")


class ClaudeVisionProvider(VisionAIProvider):
    """Anthropic Claude Vision API provider - FALLBACK 2"""

    def __init__(self):
        from app.core.config import settings
        self.api_key = getattr(settings, 'ANTHROPIC_API_KEY', None) or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude Vision provider initialized (FALLBACK 2)")
            except Exception as e:
                logger.warning(f"Failed to initialize Claude: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def analyze_image(self, image, prompt: str) -> Dict:
        if not self.is_available():
            raise PDFExtractionError("Claude not available")

        try:
            image = resize_image_for_api(image)
            base64_image = image_to_base64(image)

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            )

            text = response.content[0].text

            # Extract and parse JSON with error handling
            return parse_json_response(text)

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            raise PDFExtractionError(f"Claude analysis failed: {e}")


class OllamaVisionProvider(VisionAIProvider):
    """Ollama local vision model provider (LLaVA) - FALLBACK 3"""

    def __init__(self):
        from app.core.config import settings
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', None) or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "llava"
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                self._available = any("llava" in m.get("name", "").lower() for m in models)
            else:
                self._available = False
        except:
            self._available = False

        if self._available:
            logger.info("Ollama LLaVA provider initialized (FALLBACK 3)")
        return self._available

    def analyze_image(self, image, prompt: str) -> Dict:
        if not self.is_available():
            raise PDFExtractionError("Ollama LLaVA not available")

        import requests

        try:
            image = resize_image_for_api(image, max_size=1024)
            base64_image = image_to_base64(image)

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [base64_image],
                    "stream": False
                },
                timeout=120
            )

            if response.status_code != 200:
                raise PDFExtractionError(f"Ollama error: {response.text}")

            text = response.json().get("response", "")

            # Extract and parse JSON with error handling
            return parse_json_response(text)

        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            raise PDFExtractionError(f"Ollama analysis failed: {e}")


class PDFPlanExtractor:
    """
    Main PDF plan extractor with multi-provider fallback.
    Priority: Gemini 2.5 Flash -> Gemini 3 Pro -> OpenAI -> Claude -> Ollama

    NOTE: Flash is now PRIMARY because Gemini 3 Pro with ThinkingConfig is non-deterministic
    and produces inconsistent results on the same PDF.
    """

    def __init__(self):
        self.providers = [
            GeminiFlashProvider(),       # Gemini 2.5 Flash (FAST, CONSISTENT - PRIMARY)
            GeminiVisionProvider(),      # Gemini 3 Pro (better quality but non-deterministic)
            OpenAIVisionProvider(),      # GPT-4o (reliable fallback)
            ClaudeVisionProvider(),
            OllamaVisionProvider()
        ]

        # Log available providers
        available = [p.__class__.__name__ for p in self.providers if p.is_available()]
        logger.info(f"Available vision providers: {available}")

    def get_available_provider(self) -> Optional[VisionAIProvider]:
        """Get first available provider"""
        for provider in self.providers:
            if provider.is_available():
                return provider
        return None

    def extract_from_pdf(
        self,
        pdf_path: str,
        plan_type: PlanType = PlanType.GENERAL,
        pages: Optional[List[int]] = None
    ) -> Dict:
        """
        Extract construction data from PDF plan using Vision AI.

        Args:
            pdf_path: Path to PDF file
            plan_type: Type of plan for specialized extraction
            pages: Specific pages to process (None for all)

        Returns:
            Dict with extracted data
        """
        logger.info(f"Extracting from PDF: {pdf_path}, type: {plan_type.value}")

        # Get provider
        provider = self.get_available_provider()
        if not provider:
            raise PDFExtractionError(
                "No vision AI provider available. Please configure:\n"
                "- GEMINI_API_KEY for Gemini (preferred)\n"
                "- OPENAI_API_KEY for OpenAI\n"
                "- ANTHROPIC_API_KEY for Claude\n"
                "- Or run Ollama with LLaVA model"
            )

        logger.info(f"Using provider: {provider.__class__.__name__}")

        # Convert PDF to images - try multiple methods
        images = []

        # Method 1: Try pdf2image (requires poppler)
        if HAS_PDF2IMAGE and not images:
            try:
                # Use explicit poppler path on Windows
                if os.path.exists(POPPLER_PATH):
                    images = convert_from_path(pdf_path, dpi=200, poppler_path=POPPLER_PATH)
                    logger.info(f"Converted {len(images)} pages from PDF using pdf2image with poppler")
                else:
                    images = convert_from_path(pdf_path, dpi=200)
                    logger.info(f"Converted {len(images)} pages from PDF using pdf2image (system poppler)")
            except Exception as e:
                logger.warning(f"pdf2image failed: {e}")

        # Method 2: Try PyMuPDF (no external dependencies)
        if HAS_PYMUPDF and not images:
            try:
                images = self._extract_images_with_pymupdf(pdf_path)
                logger.info(f"Converted {len(images)} pages from PDF using PyMuPDF")
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}")

        # Method 3: Fallback to pypdf embedded images only
        if not images:
            images = self._extract_images_from_pypdf(pdf_path)
            if images:
                logger.info(f"Extracted {len(images)} embedded images from PDF using pypdf")

        if not images:
            raise PDFExtractionError("Could not extract images from PDF")

        # Filter pages if specified
        if pages:
            images = [images[i-1] for i in pages if 0 < i <= len(images)]

        # Get appropriate prompt
        prompt = EXTRACTION_PROMPTS.get(plan_type, EXTRACTION_PROMPTS[PlanType.GENERAL])

        # Process each page with fallback
        all_results = []
        for i, image in enumerate(images):
            logger.info(f"Processing page {i+1}/{len(images)}")

            result = self._analyze_with_fallback(image, prompt)
            result["page_number"] = i + 1
            all_results.append(result)

        # Aggregate results
        aggregated = self._aggregate_results(all_results, plan_type)
        aggregated["source_file"] = os.path.basename(pdf_path)
        aggregated["plan_type"] = plan_type.value
        aggregated["pages_processed"] = len(images)

        # Get actual provider used from results (not the initial selection)
        actual_provider = None
        for result in all_results:
            if "provider" in result:
                actual_provider = result["provider"]
                break
        aggregated["provider_used"] = actual_provider or provider.__class__.__name__
        print(f"[PDF_EXTRACTOR] Final provider_used: {aggregated['provider_used']}")

        return aggregated

    def _extract_images_with_pymupdf(self, pdf_path: str, dpi: int = 200) -> List:
        """Convert PDF pages to images using PyMuPDF (fitz)"""
        from PIL import Image as PILImage

        images = []
        try:
            doc = fitz.open(pdf_path)
            zoom = dpi / 72  # 72 is the default PDF DPI
            mat = fitz.Matrix(zoom, zoom)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=mat)

                # Convert to PIL Image
                img = PILImage.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)

            doc.close()
            logger.info(f"PyMuPDF rendered {len(images)} pages at {dpi} DPI")

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise

        return images

    def _extract_images_from_pypdf(self, pdf_path: str) -> List:
        """Extract images from PDF using pypdf as fallback"""
        from PIL import Image as PILImage

        images = []
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                for image_obj in page.images:
                    try:
                        img_bytes = image_obj.data
                        img = PILImage.open(io.BytesIO(img_bytes))
                        images.append(img)
                    except Exception as e:
                        logger.debug(f"Could not extract image from page {page_num}: {e}")
        except Exception as e:
            logger.error(f"pypdf extraction failed: {e}")

        return images

    def _analyze_with_fallback(self, image, prompt: str) -> Dict:
        """Analyze image with provider fallback"""
        errors = []

        print(f"[PDF_EXTRACTOR] _analyze_with_fallback called with {len(self.providers)} providers")
        for i, p in enumerate(self.providers):
            print(f"[PDF_EXTRACTOR]   Provider {i}: {p.__class__.__name__}, available: {p.is_available()}")

        for provider in self.providers:
            if not provider.is_available():
                print(f"[PDF_EXTRACTOR] Provider {provider.__class__.__name__} is not available, skipping")
                logger.info(f"Provider {provider.__class__.__name__} is not available, skipping")
                continue

            print(f"[PDF_EXTRACTOR] Trying provider: {provider.__class__.__name__}")
            logger.info(f"Trying provider: {provider.__class__.__name__}")
            try:
                result = provider.analyze_image(image, prompt)
                result["provider"] = provider.__class__.__name__
                print(f"[PDF_EXTRACTOR] Provider {provider.__class__.__name__} SUCCEEDED")
                logger.info(f"Provider {provider.__class__.__name__} succeeded")
                return result
            except Exception as e:
                errors.append(f"{provider.__class__.__name__}: {e}")
                print(f"[PDF_EXTRACTOR] Provider {provider.__class__.__name__} FAILED: {e}")
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                import traceback
                tb = traceback.format_exc()
                print(f"[PDF_EXTRACTOR] Traceback: {tb[:500]}")
                logger.warning(f"Traceback: {tb}")
                continue

        return {
            "error": "All providers failed",
            "details": errors
        }

    def _aggregate_results(self, results: List[Dict], plan_type: PlanType) -> Dict:
        """Aggregate results from multiple pages"""
        aggregated = {
            "pages": results,
            "summary": {},
            "all_items": []
        }

        # Collect all items from all pages
        for page in results:
            if "error" in page:
                continue

            # Different aggregation based on plan type
            if plan_type == PlanType.ARCHITECTURAL:
                aggregated["all_items"].extend(page.get("rooms", []))
                aggregated["all_items"].extend(page.get("doors", []))
                aggregated["all_items"].extend(page.get("windows", []))

            elif plan_type == PlanType.ELECTRICAL:
                aggregated["all_items"].extend(page.get("lighting", []))
                aggregated["all_items"].extend(page.get("outlets", []))
                aggregated["all_items"].extend(page.get("switches", []))

            elif plan_type == PlanType.PLUMBING:
                fixtures = page.get("fixtures", {})
                for fixture_type, items in fixtures.items():
                    if isinstance(items, list):
                        aggregated["all_items"].extend(items)
                    elif isinstance(items, dict):
                        aggregated["all_items"].append({fixture_type: items})

            elif plan_type == PlanType.BOQ_TABLE:
                # Extract items from BOQ table format
                for item in page.get("items", []):
                    if isinstance(item, dict):
                        aggregated["all_items"].append({
                            "type": item.get("item_number", ""),
                            "description": item.get("description", ""),
                            "quantity": item.get("quantity", 0),
                            "unit": item.get("unit", "יח'"),
                            "unit_price": item.get("unit_price", 0),
                            "total_price": item.get("total_price", 0),
                            "dimensions": item.get("dimensions_in_description", ""),
                            "category": "boq_table"
                        })

            elif plan_type == PlanType.TRAFFIC:
                # Traffic plan aggregation - סימון, תמרורים, חניות, מדרכות
                extracted_descriptions = set()

                def is_duplicate(item_type: str) -> bool:
                    item_lower = item_type.lower()
                    for desc in extracted_descriptions:
                        if item_lower in desc or desc in item_lower:
                            return True
                    return False

                # Primary: extracted_items (direct BOQ line items)
                for item in page.get("extracted_items", []):
                    if isinstance(item, dict) and item.get("description"):
                        desc = item.get("description", "")
                        extracted_descriptions.add(desc.lower() if desc else "")
                        aggregated["all_items"].append({
                            "item_code": item.get("item_code", ""),
                            "type": item.get("type", desc),
                            "description": desc,
                            "quantity": item.get("quantity") or 0,
                            "unit": item.get("unit") or "יח'",
                            "category": item.get("category", "traffic")
                        })

                # Road markings (סימון אופקי)
                for marking in page.get("road_markings", []):
                    if isinstance(marking, dict) and marking.get("type"):
                        mark_type = marking.get("type", "סימון")
                        if is_duplicate(mark_type):
                            continue
                        qty = marking.get("length_m") or marking.get("quantity") or 0
                        unit = "מ\"ל" if marking.get("length_m") else "יח'"
                        aggregated["all_items"].append({
                            "type": mark_type,
                            "description": mark_type,
                            "quantity": qty,
                            "unit": unit,
                            "category": "road_markings"
                        })

                # Traffic signs (תמרורים)
                for sign in page.get("signs", []):
                    if isinstance(sign, dict) and sign.get("type"):
                        sign_type = sign.get("type", "תמרור")
                        if is_duplicate(sign_type):
                            continue
                        aggregated["all_items"].append({
                            "type": sign_type,
                            "description": sign_type + (f" קוד {sign.get('code')}" if sign.get("code") else ""),
                            "quantity": sign.get("quantity") or 0,
                            "unit": "יח'",
                            "category": "signs"
                        })

                # Safety barriers (מעקות בטיחות)
                for barrier in page.get("barriers", []):
                    if isinstance(barrier, dict) and barrier.get("type"):
                        barrier_type = barrier.get("type", "מעקה")
                        if is_duplicate(barrier_type):
                            continue
                        qty = barrier.get("length_m") or barrier.get("quantity") or 0
                        unit = "מ\"ל" if barrier.get("length_m") else "יח'"
                        aggregated["all_items"].append({
                            "type": barrier_type,
                            "description": barrier_type,
                            "quantity": qty,
                            "unit": unit,
                            "category": "barriers"
                        })

                # Speed control (פסי האטה)
                for speed in page.get("speed_control", []):
                    if isinstance(speed, dict) and speed.get("type"):
                        speed_type = speed.get("type", "פס האטה")
                        if is_duplicate(speed_type):
                            continue
                        qty = speed.get("area_m2") or speed.get("quantity") or 0
                        unit = "מ\"ר" if speed.get("area_m2") else "יח'"
                        aggregated["all_items"].append({
                            "type": speed_type,
                            "description": speed_type,
                            "quantity": qty,
                            "unit": unit,
                            "category": "speed_control"
                        })

                # Street lighting (תאורת רחוב)
                for light in page.get("lighting", []):
                    if isinstance(light, dict) and light.get("type"):
                        light_type = light.get("type", "תאורה")
                        if is_duplicate(light_type):
                            continue
                        aggregated["all_items"].append({
                            "type": light_type,
                            "description": light_type,
                            "quantity": light.get("quantity") or 0,
                            "unit": "יח'",
                            "category": "lighting"
                        })

                # Traffic islands (איי תנועה)
                for island in page.get("traffic_islands", []):
                    if isinstance(island, dict) and island.get("type"):
                        island_type = island.get("type", "אי תנועה")
                        if is_duplicate(island_type):
                            continue
                        qty = island.get("area_m2") or island.get("length_m") or 0
                        unit = "מ\"ר" if island.get("area_m2") else "מ\"ל"
                        aggregated["all_items"].append({
                            "type": island_type,
                            "description": island_type,
                            "quantity": qty,
                            "unit": unit,
                            "category": "traffic_islands"
                        })

                # Parking (חניות)
                for parking in page.get("parking", []):
                    if isinstance(parking, dict) and parking.get("type"):
                        parking_type = parking.get("type", "חניה")
                        if is_duplicate(parking_type):
                            continue
                        qty = parking.get("area_m2") or parking.get("quantity") or 0
                        unit = "מ\"ר" if parking.get("area_m2") else "יח'"
                        aggregated["all_items"].append({
                            "type": parking_type,
                            "description": parking_type,
                            "quantity": qty,
                            "unit": unit,
                            "category": "parking"
                        })

                # Sidewalks (מדרכות ושבילים)
                for sidewalk in page.get("sidewalks", []):
                    if isinstance(sidewalk, dict) and sidewalk.get("type"):
                        sidewalk_type = sidewalk.get("type", "מדרכה")
                        if is_duplicate(sidewalk_type):
                            continue
                        qty = sidewalk.get("area_m2") or sidewalk.get("length_m") or sidewalk.get("quantity") or 0
                        unit = "מ\"ר" if sidewalk.get("area_m2") else ("מ\"ל" if sidewalk.get("length_m") else "יח'")
                        aggregated["all_items"].append({
                            "type": sidewalk_type,
                            "description": sidewalk_type,
                            "quantity": qty,
                            "unit": unit,
                            "category": "sidewalks"
                        })

                # Drainage (ניקוז כבישים)
                for drain in page.get("drainage", []):
                    if isinstance(drain, dict) and drain.get("type"):
                        drain_type = drain.get("type", "ניקוז")
                        if is_duplicate(drain_type):
                            continue
                        qty = drain.get("length_m") or drain.get("quantity") or 0
                        unit = "מ\"ל" if drain.get("length_m") else "יח'"
                        aggregated["all_items"].append({
                            "type": drain_type,
                            "description": drain_type,
                            "quantity": qty,
                            "unit": unit,
                            "category": "drainage"
                        })

            elif plan_type == PlanType.SITE_DEVELOPMENT:
                # PRIORITY: Use extracted_items as main BOQ source (comprehensive list from AI)
                # These are the most important - direct BOQ line items with proper structure!
                extracted_descriptions = set()

                # Helper function to check if item type is already covered by extracted_items
                def is_duplicate(item_type: str) -> bool:
                    """Check if item type is a substring of any extracted description or vice versa"""
                    item_lower = item_type.lower()
                    for desc in extracted_descriptions:
                        # Check both directions: item in desc, or desc in item
                        if item_lower in desc or desc in item_lower:
                            return True
                    return False

                # NEW: Handle Gemini 3 Pro's `extracted_boq` structure (dict with category keys)
                extracted_boq = page.get("extracted_boq", {})
                if isinstance(extracted_boq, dict):
                    for category_key, items in extracted_boq.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    desc = item.get("description", item.get("type", ""))
                                    extracted_descriptions.add(desc.lower() if desc else "")
                                    # Determine quantity and unit from various possible fields
                                    qty = (item.get("quantity") or
                                           item.get("estimated_area_m2") or
                                           item.get("estimated_length_m") or 0)
                                    unit = item.get("unit", "מ\"ר" if "area" in str(item) else "יח'")
                                    if item.get("estimated_area_m2"):
                                        unit = "מ\"ר"
                                    elif item.get("estimated_length_m"):
                                        unit = "מ\"ל"
                                    aggregated["all_items"].append({
                                        "item_code": item.get("item_code", ""),
                                        "type": item.get("type", desc),
                                        "description": desc,
                                        "quantity": qty,
                                        "unit": unit,
                                        "category": category_key.replace("09.", "").replace("_", " ")
                                    })

                for item in page.get("extracted_items", []):
                    if isinstance(item, dict) and item.get("description"):
                        desc = item.get("description", "")
                        extracted_descriptions.add(desc.lower() if desc else "")
                        aggregated["all_items"].append({
                            "item_code": item.get("item_code", ""),
                            "type": item.get("type", item.get("description", "")),
                            "description": desc,
                            "quantity": item.get("quantity") or 0,  # Handle None
                            "unit": item.get("unit") or "יח'",
                            "category": item.get("category", "extracted")
                        })

                # Extract surfaces ONLY if not already in extracted_items
                surfaces = page.get("surfaces", [])
                for surface in surfaces:
                    if isinstance(surface, dict) and surface.get("type"):
                        surface_type = surface.get("type", "משטח")
                        # Skip if already in extracted_items (substring match)
                        if is_duplicate(surface_type):
                            continue
                        aggregated["all_items"].append({
                            "type": surface_type,
                            "description": surface_type + (" - " + surface.get("specification", "") if surface.get("specification") else ""),
                            "quantity": surface.get("area_m2") or 0,  # Handle None
                            "unit": "מ\"ר",
                            "category": "surfaces"
                        })

                # Extract shade structures (skip if in extracted_items)
                for shade in page.get("shade_structures", []):
                    if isinstance(shade, dict) and shade.get("type"):
                        shade_type = shade.get("type", "סככת צל")
                        if is_duplicate(shade_type):
                            continue
                        aggregated["all_items"].append({
                            "type": shade_type,
                            "description": shade_type,
                            "quantity": shade.get("area_m2") or 0,
                            "unit": "מ\"ר",
                            "category": "structures"
                        })

                # Extract landscaping (skip if in extracted_items)
                landscaping = page.get("landscaping", {})
                # Handle case where AI returns landscaping as list instead of dict
                if not isinstance(landscaping, dict):
                    landscaping = {}
                for tree in landscaping.get("trees", []):
                    if isinstance(tree, dict) and tree.get("type"):
                        tree_type = tree.get("type", "עץ חדש")
                        if is_duplicate(tree_type) or is_duplicate("עץ"):
                            continue
                        aggregated["all_items"].append({
                            "type": "עץ",
                            "description": tree_type,
                            "quantity": tree.get("quantity") or 0,
                            "unit": "יח'",
                            "category": "landscaping"
                        })

                # Garden faucets (skip if in extracted_items)
                faucet_qty = landscaping.get("garden_faucets") or 0
                if faucet_qty > 0 or landscaping.get("irrigation_system"):
                    if not is_duplicate("ברז גינה"):
                        aggregated["all_items"].append({
                            "type": "ברז גינה",
                            "description": "ברז גינה",
                            "quantity": faucet_qty,
                            "unit": "יח'",
                            "category": "landscaping"
                        })

                # Grass area (skip if in extracted_items)
                grass_area = landscaping.get("grass_area_m2") or 0
                if grass_area > 0 and not is_duplicate("דשא") and not is_duplicate("גינון"):
                    aggregated["all_items"].append({
                        "type": "דשא",
                        "description": "גינון ושתילת דשא",
                        "quantity": grass_area,
                        "unit": "מ\"ר",
                        "category": "landscaping"
                    })

                # Extract fencing (skip if in extracted_items)
                for fence in page.get("fencing", []):
                    if isinstance(fence, dict) and fence.get("type"):
                        fence_type = fence.get("type", "גדר")
                        if is_duplicate(fence_type) or is_duplicate("גדר"):
                            continue
                        aggregated["all_items"].append({
                            "type": "גדר",
                            "description": fence_type,
                            "quantity": fence.get("length_m") or 0,
                            "unit": "מ\"ל",
                            "category": "fencing"
                        })

                # Extract site furniture (skip if in extracted_items)
                for furniture in page.get("site_furniture", []):
                    if isinstance(furniture, dict) and furniture.get("type"):
                        furn_type = furniture.get("type", "ריהוט חוץ")
                        if is_duplicate(furn_type):
                            continue
                        aggregated["all_items"].append({
                            "type": furn_type,
                            "description": furn_type,
                            "quantity": furniture.get("quantity") or 0,
                            "unit": "יח'",
                            "category": "furniture"
                        })

                # Extract play equipment (skip if in extracted_items)
                for equipment in page.get("play_equipment", []):
                    if isinstance(equipment, dict) and equipment.get("type"):
                        equip_type = equipment.get("type", "מתקן משחק")
                        if is_duplicate(equip_type) or is_duplicate("מתקן"):
                            continue
                        aggregated["all_items"].append({
                            "type": equip_type,
                            "description": equip_type + (" - " + equipment.get("specification", "") if equipment.get("specification") else ""),
                            "quantity": equipment.get("quantity") or 1,
                            "unit": "יח'",
                            "category": "play_equipment"
                        })

                # Extract infrastructure (skip if in extracted_items)
                infrastructure = page.get("infrastructure", {})
                # Handle case where AI returns infrastructure as list instead of dict
                if not isinstance(infrastructure, dict):
                    infrastructure = {}

                # Lighting
                for light in infrastructure.get("lighting", []):
                    if isinstance(light, dict) and light.get("type"):
                        light_type = light.get("type", "תאורה")
                        if is_duplicate(light_type) or is_duplicate("תאורה"):
                            continue
                        aggregated["all_items"].append({
                            "type": light_type,
                            "description": light_type,
                            "quantity": light.get("quantity") or 0,
                            "unit": "יח'",
                            "category": "infrastructure"
                        })

                # Drainage
                for drain in infrastructure.get("drainage", []):
                    if isinstance(drain, dict) and drain.get("type"):
                        drain_type = drain.get("type", "ניקוז")
                        if is_duplicate(drain_type) or is_duplicate("ניקוז"):
                            continue
                        aggregated["all_items"].append({
                            "type": drain_type,
                            "description": drain_type,
                            "quantity": drain.get("length_m") or 0,
                            "unit": "מ\"ל",
                            "category": "infrastructure"
                        })

                # Borders/curbs
                for border in infrastructure.get("borders", []):
                    if isinstance(border, dict) and border.get("type"):
                        border_type = border.get("type", "אבן שפה")
                        if is_duplicate(border_type) or is_duplicate("שפה"):
                            continue
                        aggregated["all_items"].append({
                            "type": border_type,
                            "description": border_type,
                            "quantity": border.get("length_m") or 0,
                            "unit": "מ\"ל",
                            "category": "infrastructure"
                        })

                # Extract landscaping shrubs (skip if in extracted_items)
                for shrub in landscaping.get("shrubs", []):
                    if isinstance(shrub, dict) and shrub.get("type"):
                        shrub_type = shrub.get("type", "שיח נוי")
                        if is_duplicate(shrub_type) or is_duplicate("שיח"):
                            continue
                        aggregated["all_items"].append({
                            "type": "שיח",
                            "description": shrub_type,
                            "quantity": shrub.get("quantity") or 0,
                            "unit": "יח'",
                            "category": "landscaping"
                        })

                # Irrigation points (skip if in extracted_items)
                irrigation_pts = landscaping.get("irrigation_points") or 0
                if irrigation_pts > 0 and not is_duplicate("השקיה"):
                    aggregated["all_items"].append({
                        "type": "נקודת השקיה",
                        "description": "נקודת השקיה",
                        "quantity": irrigation_pts,
                        "unit": "נק'",
                        "category": "landscaping"
                    })

                # NOTE: extracted_items are now processed FIRST at the beginning of SITE_DEVELOPMENT block
                # to avoid duplicates with category-specific arrays (surfaces, play_equipment, etc.)

                # Extract earthworks (skip if in extracted_items)
                earthworks = page.get("earthworks", {})
                # Handle case where AI returns earthworks as list instead of dict
                if not isinstance(earthworks, dict):
                    earthworks = {}
                excavation = earthworks.get("excavation_m3") or 0
                if excavation > 0 and not is_duplicate("חפירה"):
                    aggregated["all_items"].append({
                        "type": "חפירה",
                        "description": "חפירה כללית",
                        "quantity": excavation,
                        "unit": "מ\"ק",
                        "category": "earthworks"
                    })

        # Calculate summary statistics
        aggregated["summary"]["total_pages"] = len(results)
        aggregated["summary"]["successful_pages"] = sum(1 for r in results if "error" not in r)

        # DEDUPLICATION: Merge items with very similar descriptions
        deduplicated_items = self._deduplicate_items(aggregated["all_items"])
        aggregated["all_items"] = deduplicated_items
        aggregated["summary"]["total_items_extracted"] = len(deduplicated_items)

        return aggregated

    def _deduplicate_items(self, items: List[Dict]) -> List[Dict]:
        """
        Deduplicate BOQ items by merging similar descriptions.
        Uses fuzzy matching to detect near-duplicates and merges quantities.

        Returns deduplicated list with merged quantities.
        """
        if not items:
            return items

        def normalize_desc(desc: str) -> str:
            """Normalize description for comparison"""
            if not desc:
                return ""
            # Remove common variations
            normalized = desc.lower().strip()
            # Remove punctuation and extra spaces
            import re
            normalized = re.sub(r'[^\w\s]', '', normalized)
            normalized = re.sub(r'\s+', ' ', normalized)
            return normalized

        def are_similar(desc1: str, desc2: str) -> bool:
            """Check if two descriptions are similar enough to merge"""
            n1, n2 = normalize_desc(desc1), normalize_desc(desc2)
            if not n1 or not n2:
                return False
            # Exact match after normalization
            if n1 == n2:
                return True
            # One contains the other (e.g., "משטח גומי" vs "משטח בטיחות גומי יצוק")
            if len(n1) > 10 and len(n2) > 10:
                if n1 in n2 or n2 in n1:
                    return True
            # Check word overlap (at least 70% common words)
            words1 = set(n1.split())
            words2 = set(n2.split())
            if words1 and words2:
                common = words1 & words2
                overlap = len(common) / min(len(words1), len(words2))
                if overlap >= 0.7:
                    return True
            return False

        # Group similar items
        merged = []
        used_indices = set()

        for i, item in enumerate(items):
            if i in used_indices:
                continue

            current = item.copy()
            current_qty = float(current.get("quantity") or 0)

            # Find all similar items
            for j, other in enumerate(items):
                if j <= i or j in used_indices:
                    continue

                # Check if same unit and similar description
                if (current.get("unit") == other.get("unit") and
                    are_similar(current.get("description", ""), other.get("description", ""))):

                    other_qty = float(other.get("quantity") or 0)

                    # If quantities are very similar (within 5%), it's likely a duplicate - take max
                    if current_qty > 0 and other_qty > 0:
                        if abs(current_qty - other_qty) / max(current_qty, other_qty) < 0.05:
                            # Same item duplicated - take max quantity
                            current_qty = max(current_qty, other_qty)
                        else:
                            # Different quantities - could be different areas, sum them
                            # But if one is much larger, it's probably the correct one
                            if other_qty > current_qty * 1.5:
                                current_qty = other_qty
                                current["description"] = other.get("description", current["description"])
                            elif current_qty <= other_qty * 1.5:
                                # Similar quantities, sum them only if it makes sense
                                pass  # Keep the first one's quantity
                    elif other_qty > current_qty:
                        current_qty = other_qty
                        current["description"] = other.get("description", current["description"])

                    # Keep the longer/more detailed description
                    if len(other.get("description", "")) > len(current.get("description", "")):
                        current["description"] = other["description"]

                    used_indices.add(j)
                    logger.debug(f"Merged duplicate: '{other.get('description', '')[:40]}' into '{current.get('description', '')[:40]}'")

            current["quantity"] = current_qty
            merged.append(current)
            used_indices.add(i)

        logger.info(f"Deduplication: {len(items)} items -> {len(merged)} items ({len(items) - len(merged)} duplicates removed)")
        return merged


# Main extraction function - backwards compatible
def extract_from_pdf(
    file_path: str,
    plan_type: str = "general"
) -> List[Dict]:
    """
    Extract construction data from a PDF plan.
    Backwards compatible with existing code.

    Args:
        file_path: Path to PDF file
        plan_type: Type of plan (architectural, electrical, plumbing, etc.)

    Returns:
        List of extracted materials (for compatibility)
    """
    # Convert string to enum
    try:
        plan_type_enum = PlanType(plan_type.lower())
    except ValueError:
        plan_type_enum = PlanType.GENERAL

    extractor = PDFPlanExtractor()
    result = extractor.extract_from_pdf(file_path, plan_type_enum)

    # Convert to legacy format for backwards compatibility
    materials = []
    for item in result.get("all_items", []):
        if isinstance(item, dict):
            materials.append({
                "material_name": item.get("type", item.get("name", "Unknown")),
                "quantity": item.get("quantity", item.get("area_m2", 1)),
                "unit": item.get("unit", "pcs"),
                "confidence_score": item.get("confidence", 0.7),
                "category": plan_type,
                "notes": str(item)
            })

    return materials


def extract_from_pdf_detailed(
    file_path: str,
    plan_type: str = "general"
) -> Dict:
    """
    Extract detailed construction data from a PDF plan.
    Returns full structured data instead of flat materials list.

    Args:
        file_path: Path to PDF file
        plan_type: Type of plan (architectural, electrical, plumbing, etc.)

    Returns:
        Dict with detailed extraction results
    """
    try:
        plan_type_enum = PlanType(plan_type.lower())
    except ValueError:
        plan_type_enum = PlanType.GENERAL

    extractor = PDFPlanExtractor()
    return extractor.extract_from_pdf(file_path, plan_type_enum)
