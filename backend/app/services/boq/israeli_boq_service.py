"""
Israeli BOQ Service - כתב כמויות ישראלי
==========================================

This service generates professional Israeli Bill of Quantities (כתב כמויות)
from AutoCAD DWG files using:

AI Providers (configurable via AI_PROVIDER env var):
1. OpenAI GPT-4 - Cloud-based, fast, 128k token limit
2. Ollama Multi-Model Pipeline - Local, no token limits:
   - Aya Expanse 32B: Hebrew language specialist
   - Qwen 2.5 72B: Reasoning powerhouse (128k context)

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

from app.services.pricing.dekel_pricing import DekelPricing
from app.services.layer_categorizer import categorize_layer as smart_categorize, LayerGroup
from app.core.config import settings

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTION TYPE DETECTION - Generic BOQ Creation Support
# ══════════════════════════════════════════════════════════════════════════════

CONSTRUCTION_TYPE_KEYWORDS = {
    "residential_low": {
        "keywords": ["מגורים", "דירה", "בית פרטי", "וילה", "apartment", "house", "dwelling", "residential"],
        "max_floors": 3
    },
    "residential_high": {
        "keywords": ["מגדל", "רב קומות", "tower", "high-rise", "multi-story"],
        "min_floors": 4
    },
    "school": {
        "keywords": ["בית ספר", "כיתה", "school", "classroom", "education", "חינוך", "לימודים"],
    },
    "kindergarten": {
        "keywords": ["גן ילדים", "גנון", "מעון", "kindergarten", "preschool", "daycare"],
    },
    "office": {
        "keywords": ["משרד", "משרדים", "office", "commercial", "מסחרי"],
    },
    "infrastructure": {
        "keywords": ["כביש", "תשתית", "road", "infrastructure", "utility", "כריית", "סלילה"],
    },
    "excavation": {
        "keywords": ["חפירה", "דיפון", "excavation", "shoring", "earthwork", "יסודות"],
    },
    "industrial": {
        "keywords": ["מפעל", "מחסן", "לוגיסטי", "warehouse", "factory", "industrial", "תעשייה"],
    },
    "hotel": {
        "keywords": ["מלון", "בית מלון", "hotel", "hospitality", "אירוח"],
    },
    "renovation": {
        "keywords": ["שיפוץ", "תמ\"א", "חיזוק", "התחדשות", "renovation", "retrofit", "TAMA"],
    }
}

# Chapters to include for each construction type - aligned with הספר הכחול (Blue Book)
CHAPTER_TEMPLATES = {
    "residential_low": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "18", "36", "40", "41"],
    "residential_high": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "16", "17", "18", "26", "34", "43"],
    "school": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "16", "17", "18", "19", "26", "34", "36", "37", "40", "41", "43"],
    "kindergarten": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "18", "19", "36", "37", "40", "41"],
    "office": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "16", "17", "26", "34"],
    "infrastructure": ["01", "02", "36", "37", "40", "41", "50", "54"],  # Blue Book ch.36-41 for site development
    "excavation": ["01", "02", "05"],
    "industrial": ["01", "02", "03", "05", "07", "08", "14", "15", "16", "26", "34"],
    "hotel": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "16", "17", "26", "34"],
    "renovation": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "26", "34"],
    "default": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "36", "40"]
}

# Map extracted elements to Dekel chapters - aligned with הספר הכחול (Blue Book)
ELEMENT_TO_CHAPTER = {
    # Structural elements (פרק 02 - בטון)
    "foundation": "02",      # Concrete
    "column": "02",          # Concrete
    "beam": "02",            # Concrete
    "slab": "02",            # Concrete
    "wall_concrete": "02",   # Concrete
    "precast": "03",         # Precast concrete

    # Masonry (פרק 04 - בנייה)
    "wall_block": "04",      # Masonry
    "partition": "04",       # Masonry

    # Finishes
    "waterproofing": "05",   # Waterproofing (פרק 05 - איטום)
    "plaster": "06",         # Plastering - Blue Book chapter 09
    "floor_tile": "06",      # Flooring - Blue Book chapter 10
    "paint": "07",           # Painting - Blue Book chapter 11
    "ceiling": "06",         # Flooring & Cladding

    # Openings
    "door_wood": "08",       # Carpentry
    "door_metal": "08",      # Carpentry
    "window_aluminum": "07", # Aluminum
    "window_glass": "07",    # Aluminum & Glass

    # MEP (Mechanical, Electrical, Plumbing)
    "pipe": "10",            # Plumbing
    "fixture_sanitary": "10", # Plumbing
    "electrical": "11",      # Electrical
    "outlet": "11",          # Electrical
    "light": "11",           # Electrical
    "hvac": "12",            # HVAC
    "duct": "12",            # HVAC

    # Fire Systems (פרקים 26, 34)
    "fire_detection": "26",  # Fire Detection Systems - Blue Book
    "smoke_detector": "26",  # Fire Detection
    "fire_panel": "26",      # Fire Detection Control Panel
    "sprinkler": "34",       # Fire Suppression
    "fire_suppression": "34", # Fire Suppression Systems

    # Infrastructure (פרקים 01, 50, 54)
    "earthwork": "01",       # Earthworks
    "excavation": "01",      # Earthworks
    "road": "50",            # Road Infrastructure - Blue Book ch.50
    "parking": "36",         # Site Development - Blue Book ch.36

    # Site Development (פרקים 36, 37)
    "site_development": "36", # Site Development Works - Blue Book
    "paving": "36",          # Paving - Blue Book ch.36
    "fence": "36",           # Fences - Blue Book ch.36
    "gate": "36",            # Gates - Blue Book ch.36
    "street_furniture": "37", # Street Furniture - Blue Book ch.37
    "bench": "37",           # Benches
    "pole_light": "37",      # Light Poles

    # Landscaping (פרקים 40, 41)
    "landscaping": "40",     # Landscaping - Blue Book ch.40 (NOT ch.13!)
    "tree": "40",            # Trees
    "grass": "40",           # Grass/Lawn
    "shrub": "40",           # Shrubs
    "playground": "40",      # Playground Equipment
    "irrigation": "41",      # Irrigation Systems - Blue Book ch.41

    # Protected Structures (פרק 43)
    "protected_space": "43", # ממ"ד / מקלט
    "mamad": "43",           # Safe Room
    "shelter": "43",         # Public Shelter
}

# Required elements by construction type for gap detection - aligned with Blue Book
REQUIRED_ELEMENTS_BY_TYPE = {
    "residential_low": [
        "foundation", "slab", "wall_block", "plaster", "floor_tile",
        "door_wood", "window_aluminum", "pipe", "electrical", "landscaping"
    ],
    "residential_high": [
        "foundation", "column", "beam", "slab", "wall_block", "waterproofing",
        "plaster", "floor_tile", "door_wood", "window_aluminum", "pipe",
        "electrical", "hvac", "fire_detection", "protected_space"
    ],
    "school": [
        "foundation", "slab", "wall_block", "plaster", "floor_tile",
        "door_wood", "window_aluminum", "pipe", "electrical", "hvac",
        "fire_detection", "fire_suppression", "protected_space", "landscaping", "playground"
    ],
    "kindergarten": [
        "foundation", "slab", "wall_block", "plaster", "floor_tile",
        "door_wood", "window_aluminum", "pipe", "electrical",
        "landscaping", "playground", "irrigation"
    ],
    "infrastructure": [
        "earthwork", "excavation", "road", "paving", "site_development"
    ],
    "excavation": [
        "earthwork", "excavation"
    ],
    "office": [
        "foundation", "slab", "wall_block", "plaster", "floor_tile",
        "door_wood", "window_aluminum", "pipe", "electrical", "hvac",
        "fire_detection"
    ],
}

# Confidence level definitions
CONFIDENCE_LEVELS = {
    1.0: "גבוה - חילוץ גיאומטרי עם מידות ברורות",
    0.8: "בינוני-גבוה - התאמת תבנית משרטוט",
    0.6: "בינוני - פרשנות AI עם אימות",
    0.4: "נמוך - אומדן ברירת מחדל, נדרש עדכון ידני",
    0.2: "נמוך מאוד - מציין מיקום בלבד, חייב לעדכן ידנית",
}



# ══════════════════════════════════════════════════════════════════════════════
# DYNAMIC ESTIMATION FORMULAS
# ══════════════════════════════════════════════════════════════════════════════

ESTIMATION_FORMULAS = {
    "residential_high": {
        "foundations": "A_build × 0.15 (נפח ממוצע כולל כלונסאות/רפסודה)",
        "columns": "ספירת עמודים × (0.4×0.4 או מידה בשרטוט) × 3.0 מ' גובה",
        "ceilings": "A_build × 0.22 (תקרה מקשית עבה יותר)",
        "concrete_grade": "חפש טקסט B-40, C-50. ברירת מחדל: B-40",
        "steel_density": "110", # kg/m3
    },
    "residential_low": {
        "foundations": "A_build × 0.12",
        "columns": "ספירת עמודים × (0.25×0.25 או מידה בשרטוט) × 2.8 מ' גובה",
        "ceilings": "A_build × 0.20",
        "concrete_grade": "חפש טקסט B-30. ברירת מחדל: B-30",
        "steel_density": "100",
    },
    "public": {  # Schools, Country Clubs, Community Centers
        # Earthworks: Use Building Footprint + Margin (1.2) * Depth (0.5 for foundation trench)
        # Instead of full site scrape which overestimates by 3x.
        "earthworks_excavation": "A_build × 1.2 × 0.5 (חפירה ממוקדת ליסודות)", 
        
        "foundations": "A_build × 0.15 (רפסודות/יסודות בודדים)",
        "columns": "ספירת עמודים (מסוננת) × גאומטריה משרטוט. אם אין: (0.3×0.3) × 3.5 מ'",
        "ceilings": "A_build × 0.20",
        "concrete_grade": "חפש טקסט B-40, B-50. ברירת מחדל: B-30",
        "steel_density": "110",
    },
    "industrial": {
        "foundations": "A_build × 0.18 (רצפות תעשייתיות עבות)",
        "columns": "ספירת עמודים × גאומטריה משרטוט. אם אין: (0.5×0.5) × 5.0 מ'",
        "ceilings": "A_build × 0.15 (בד\"כ קונסטרוקציית פלדה, בטון רק ברצפה/גלריה)",
        "concrete_grade": "חפש טקסט B-40+. ברירת מחדל: B-30",
        "steel_density": "90",
    },
    "default": {
        "earthworks_excavation": "A_build × 1.2 × 0.4",
        "foundations": "A_build × 0.15 (ערך ברירת מחדל זהיר)",
        "columns": "ספירת עמודים × גאומטריה משרטוט (עדיפות עליונה). אומדן חסר: 0.3×0.3×3.0",
        "ceilings": "A_build × 0.20",
        "concrete_grade": "חפש טקסט המציין סוג בטון (ב-30, ב-40 וכו'). ברירת מחדל: B-30",
        "steel_density": "100",
    }
}


def get_system_prompt(construction_type: str = "default") -> str:
    """
    Generate a dynamic system prompt based on construction type.
    """
    # Map 'school', 'kindergarten' -> 'public' for formulas
    formula_type = "default"
    if construction_type in ["residential_high"]:
        formula_type = "residential_high"
    elif construction_type in ["residential_low", "renovation"]:
        formula_type = "residential_low"
    elif construction_type in ["school", "kindergarten", "hotel", "office", "public"]:
        formula_type = "public"
    elif construction_type in ["industrial", "infrastructure"]:
        formula_type = "industrial"
    
    formulas = ESTIMATION_FORMULAS.get(formula_type, ESTIMATION_FORMULAS["default"])

    return f"""אתה כתב כמויות (Quantity Surveyor) מקצועי ישראלי עם 25 שנות ניסיון.
אתה מומחה במפרט הכללי לעבודות בנייה ("הספר הכחול") ובמחירון דקל.

══════════════════════════════════════════════════════════════════════════════
תפקידך ומטרתך (CRITICAL):
══════════════════════════════════════════════════════════════════════════════
עליך לחלץ כמויות **מדויקות** מתוך הטקסט והנתונים הגאומטריים.
אל תנפח כמויות "ליתר ביטחון" מעבר ל-5% פחת מקובל. 
חפש תמיד **מידות ספציפיות** בטקסטים (למשל "עמוד 40/40", "בטון ב-40") ותן להן עדיפות על פני הנוסחאות.

סוג המבנה שזוהה: {construction_type}

══════════════════════════════════════════════════════════════════════════════
יחידות מידה - נתונים מומרים:
══════════════════════════════════════════════════════════════════════════════
הנתונים שלהלן כבר הומרו למטרים (m) ומ"ר (m²).
השדות total_area ו-total_line_length כבר מוצגים במ"ר ומטרים בהתאמה.

══════════════════════════════════════════════════════════════════════════════
נוסחאות לחישוב כמויות (מותאמות לסוג מבנה זה):
══════════════════════════════════════════════════════════════════════════════

נתונים:
1. building_area_m2 = שטח מבנה בנוי במ"ר (A_build) - לשימוש בבטון, שלד, גמרים
2. site_area_m2 = שטח פיתוח חוץ במ"ר (A_site) - לשימוש בעבודות עפר, פיתוח, גינון

【פרק 01 - עבודות עפר】
• חפירה ליסודות = {formulas.get('earthworks_excavation', 'A_build × 1.2 × 0.5')}
• יישור ופילוס מגרש = A_site × 0.1 (רק יישור עליון, לא חפירה מלאה)
• מילוי חוזר = נפח חפירה יסודות × 0.4
• פינוי עודפי עפר = נפח חפירה יסודות × 0.6 + יישור מגרש קטן (פילוס בלבד)

【פרק 02 - עבודות בטון】
★ סוג בטון (חוזק): {formulas['concrete_grade']}
• בטון רזה B-10: A_build × 0.10 עובי
• בטון יסודות: {formulas['foundations']}
• בטון עמודים: {formulas['columns']}
  -> חשוב: השתמש אך ורק בעמודים שעברו סינון גודל (0.04-2.0 מ"ר). אל תספור טקסטים כעמודים.
• בטון תקרה/גג: {formulas['ceilings']}
• ברזל זיון: נפח בטון משוקלל × {formulas.get('steel_density', '100')} ק"ג/מ"ק
  (אם ניתן: יסודות 100 ק"ג/מ"ק, עמודים 120 ק"ג/מ"ק, תקרות 90 ק"ג/מ"ק)
• טפסות: שטח בטון × 2.0 (או לפי מעטפת האלמנטים)

【פרק 03 - עבודות בנייה】
• אורך קירות משוער = √A_build × 8 (פנים+חוץ)
• שטח קירות (ללא פתחים) = אורך קירות × הגובה בקומה (2.8 - 3.5 מ')

(שאר הפרקים לחישוב לפי שטח רצפה A_build כמקובל)

══════════════════════════════════════════════════════════════════════════════
דרישות לתיאורים (חשוב מאוד):
══════════════════════════════════════════════════════════════════════════════
1. אם זיהית בטון ב-40 או ב-50 בטקסט - ציין זאת בתיאור! (אל תכתוב סתם B-30).
2. אם זיהית מידות עמודים (למשל 20/50), חשב לפי המידות והשתמש בהן בתיאור.
3. אל תבצע "כפל ספירה" (Double Counting): אם חישבת בטון ברצפה, אל תחשיב אותו שוב ביסודות אלא אם אלו אלמנטים נפרדים בבירור.

══════════════════════════════════════════════════════════════════════════════
פורמט התשובה (JSON):
══════════════════════════════════════════════════════════════════════════════
{{
  "project_name": "שם הפרויקט",
  "construction_type_detected": "{construction_type}",
  "date": "תאריך",
  "chapters": [
    {{
      "chapter_code": "01",
      "chapter_name_he": "עבודות עפר",
      "chapter_name_en": "Earthworks",
      "items": [
        {{
          "item_code": "01.01.01",
          "dekel_code": "01.01.01",
          "description_he": "תיאור מפורט...",
          "description_en": "English description...",
          "quantity": 100.0,
          "unit": "מ\"ק",
          "unit_price": 45.0,
          "total_price": 4500.0,
          "confidence": 0.95,
          "notes": "הערה"
        }}
      ],
      "chapter_total": 4500.0
    }}
  ],
  "summary": {{
    "subtotal": 0.0,
    "vat_rate": 0.17,
    "vat_amount": 0.0,
    "grand_total": 0.0
  }},
  "notes": ["הערות כלליות"]
}}"""



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

    Supports two AI providers:
    1. OpenAI (GPT-4): Cloud-based, fast, requires API key
    2. Ollama (Multi-Model): Local, no token limits, uses Aya + Qwen pipeline

    Flow:
    1. Detect construction type from project/file name
    2. Extract raw data from AutoCAD (blocks, text, geometry)
    3. Send to AI (OpenAI or Ollama) with Israeli construction expert prompt
    4. Match items to Dekel pricing codes
    5. Validate BOQ completeness
    6. Generate structured BOQ report
    """

    def __init__(self):
        self.ai_provider = settings.AI_PROVIDER.lower()
        self.dekel_pricing = DekelPricing()

        # Initialize the appropriate AI client
        if self.ai_provider == "ollama":
            from app.services.boq.ollama_service import get_ollama_service
            self.ollama_service = get_ollama_service()
            self.openai_client = None
            logger.info("Using Ollama multi-model pipeline for BOQ generation")
        else:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.ollama_service = None
            logger.info("Using OpenAI GPT-4 for BOQ generation")

    def detect_construction_type(
        self,
        project_name: Optional[str] = None,
        filename: Optional[str] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Detect construction type from project name, filename, and extracted data.

        Returns one of: residential_low, residential_high, school, kindergarten,
        office, infrastructure, excavation, industrial, hotel, renovation, default

        Args:
            project_name: Project name (if provided)
            filename: Source filename
            raw_data: Raw extraction data with text entities and layers

        Returns:
            Detected construction type string
        """
        import re

        # Combine all text sources for analysis
        search_text = ""
        if project_name:
            search_text += f" {project_name}"
        if filename:
            search_text += f" {filename}"

        # Add text entities from raw data
        if raw_data:
            text_entities = raw_data.get("text_entities", [])
            for text_item in text_entities[:100]:  # Sample first 100
                if isinstance(text_item, dict):
                    search_text += f" {text_item.get('text', '')} {text_item.get('content', '')}"
                else:
                    search_text += f" {text_item}"

            # Add layer names
            layers = raw_data.get("layers", [])
            for layer in layers:
                if isinstance(layer, dict):
                    search_text += f" {layer.get('name', '')}"
                else:
                    search_text += f" {layer}"

        search_text = search_text.lower()
        logger.info(f"Detecting construction type from: {search_text[:200]}...")

        # Score each construction type
        scores = {}
        for ctype, config in CONSTRUCTION_TYPE_KEYWORDS.items():
            keywords = config.get("keywords", config) if isinstance(config, dict) else config
            if isinstance(config, dict):
                keywords = config.get("keywords", [])

            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Count occurrences with word boundary awareness
                pattern = re.escape(keyword_lower)
                matches = len(re.findall(pattern, search_text))
                score += matches * 2  # Weight each match

            scores[ctype] = score

        # Find best match
        best_type = max(scores, key=scores.get) if scores else "default"
        best_score = scores.get(best_type, 0)

        if best_score > 0:
            logger.info(f"Detected construction type: {best_type} (score: {best_score})")
            return best_type
        else:
            logger.info("No construction type detected, using default")
            return "default"

    def get_chapters_for_type(self, construction_type: str) -> List[str]:
        """
        Get list of relevant chapters for a construction type.

        Args:
            construction_type: Detected or specified construction type

        Returns:
            List of chapter codes (e.g., ["01", "02", "03", ...])
        """
        chapters = CHAPTER_TEMPLATES.get(construction_type, CHAPTER_TEMPLATES["default"])
        logger.info(f"Chapters for {construction_type}: {chapters}")
        return chapters

    def detect_missing_elements(
        self,
        boq: 'IsraeliBOQ',
        construction_type: str
    ) -> List[Dict[str, str]]:
        """
        Detect missing required elements for a construction type.

        Args:
            boq: Generated BOQ
            construction_type: Detected construction type

        Returns:
            List of missing elements with descriptions
        """
        required = REQUIRED_ELEMENTS_BY_TYPE.get(construction_type, [])
        if not required:
            return []

        # Get all chapter codes present in BOQ
        present_chapters = set()
        for chapter in boq.chapters:
            present_chapters.add(chapter.chapter_code)

        # Check which required elements are missing based on chapter presence
        missing = []
        for element in required:
            expected_chapter = ELEMENT_TO_CHAPTER.get(element)
            if expected_chapter and expected_chapter not in present_chapters:
                missing.append({
                    "element": element,
                    "expected_chapter": expected_chapter,
                    "description_he": f"פריט חסר: {element}",
                    "severity": "warning"
                })

        if missing:
            logger.warning(f"Detected {len(missing)} missing elements for {construction_type}: {[m['element'] for m in missing]}")

        return missing

    def validate_boq(self, boq: 'IsraeliBOQ') -> Dict[str, Any]:
        """
        Validate generated BOQ for completeness and accuracy.

        Returns validation results with pass/fail for each check.
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }

        # Check 1: All items have chapter
        items_without_chapter = 0
        for chapter in boq.chapters:
            if not chapter.chapter_code:
                items_without_chapter += 1
        if items_without_chapter > 0:
            validation_results["errors"].append(f"{items_without_chapter} items missing chapter code")
            validation_results["valid"] = False

        # Check 2: All items have unit
        items_without_unit = 0
        for chapter in boq.chapters:
            for item in chapter.items:
                if not item.unit:
                    items_without_unit += 1
        if items_without_unit > 0:
            validation_results["warnings"].append(f"{items_without_unit} items missing unit")

        # Check 3: All items have description
        items_without_desc = 0
        for chapter in boq.chapters:
            for item in chapter.items:
                if not item.description_he:
                    items_without_desc += 1
        if items_without_desc > 0:
            validation_results["warnings"].append(f"{items_without_desc} items missing Hebrew description")

        # Check 4: Quantities non-negative
        negative_qty = 0
        for chapter in boq.chapters:
            for item in chapter.items:
                if item.quantity < 0:
                    negative_qty += 1
        if negative_qty > 0:
            validation_results["errors"].append(f"{negative_qty} items have negative quantity")
            validation_results["valid"] = False

        # Check 5: Totals calculated correctly
        calculated_subtotal = sum(ch.chapter_total for ch in boq.chapters)
        if abs(calculated_subtotal - boq.subtotal) > 1:
            validation_results["warnings"].append(
                f"Subtotal mismatch: calculated={calculated_subtotal:.2f}, stated={boq.subtotal:.2f}"
            )

        # Check 6: Low confidence items
        low_confidence_items = 0
        for chapter in boq.chapters:
            for item in chapter.items:
                if item.confidence < 0.5:
                    low_confidence_items += 1
        if low_confidence_items > 0:
            validation_results["warnings"].append(
                f"{low_confidence_items} items have low confidence (<0.5) - review recommended"
            )

        # Stats
        total_items = sum(len(ch.items) for ch in boq.chapters)
        validation_results["stats"] = {
            "total_chapters": len(boq.chapters),
            "total_items": total_items,
            "subtotal": boq.subtotal,
            "grand_total": boq.grand_total,
            "low_confidence_items": low_confidence_items
        }

        logger.info(f"BOQ validation: valid={validation_results['valid']}, "
                   f"errors={len(validation_results['errors'])}, "
                   f"warnings={len(validation_results['warnings'])}")

        return validation_results

    def _preprocess_raw_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess raw AutoCAD data to convert units to meters.

        Auto-detects drawing units based on:
        1. Block scale factors (100x100 suggests 1:100 scale = cm units)
        2. Coordinate magnitudes (millions = mm, hundred thousands = cm)

        Israeli drawings commonly use:
        - Millimeters (1 unit = 1mm) with ITM coordinates
        - Centimeters (1 unit = 1cm) at 1:100 scale
        """
        processed = raw_data.copy()

        # Detect drawing units from context
        drawing_unit = self._detect_drawing_units(processed)
        logger.info(f"Detected drawing units: {drawing_unit}")

        # Set conversion factors based on detected units
        if drawing_unit == "cm":
            # Centimeters: cm² → m² = ÷10,000, cm → m = ÷100
            area_divisor = 10_000
            length_divisor = 100
        elif drawing_unit == "mm":
            # Millimeters: mm² → m² = ÷1,000,000, mm → m = ÷1,000
            area_divisor = 1_000_000
            length_divisor = 1_000
        else:
            # Assume meters - no conversion needed
            area_divisor = 1
            length_divisor = 1

        if "geometry" in processed:
            geometry = processed["geometry"]

            # Store original values and detected unit
            geometry["detected_unit"] = drawing_unit
            geometry["area_divisor"] = area_divisor
            geometry["length_divisor"] = length_divisor

            # Convert area (or use override if provided)
            if "total_area_m2_override" in geometry:
                # User provided area override - use it directly (already in m²)
                geometry["total_area_m2"] = geometry["total_area_m2_override"]
                geometry["total_area"] = geometry["total_area_m2_override"]
                logger.info(f"Using user area override: {geometry['total_area_m2']:,.2f} m²")
            elif "total_area" in geometry and geometry["total_area"] > 0:
                original_area = geometry["total_area"]
                geometry["total_area_original"] = original_area
                geometry["total_area_m2"] = original_area / area_divisor
                geometry["total_area"] = geometry["total_area_m2"]
                logger.info(f"Area conversion: {original_area:,.0f} {drawing_unit}² → {geometry['total_area_m2']:,.2f} m²")

            # --- NEW: Breakdown area by layer category ---
            raw_area_by_layer = raw_data.get("area_by_layer", {})
            building_area_m2 = 0.0
            site_area_m2 = 0.0
            
            for layer_name, layer_data in raw_area_by_layer.items():
                # Convert this layer's area to m² using the SAME divisor
                raw_layer_area = layer_data.get("area", 0.0)
                layer_area_m2 = raw_layer_area / area_divisor
                
                # Smart categorize
                cat_group, _ = smart_categorize(layer_name, layer_area_m2, layer_data.get("polyline_count", 0))
                
                if cat_group in [LayerGroup.BUILDING, LayerGroup.STRUCTURAL, LayerGroup.UTILITIES]:
                    building_area_m2 += layer_area_m2
                elif cat_group in [LayerGroup.SITE_BOUNDARY, LayerGroup.INFRASTRUCTURE, LayerGroup.LANDSCAPE]:
                    site_area_m2 += layer_area_m2
            
            # Store split areas in geometry
            geometry["building_area_m2"] = building_area_m2
            geometry["site_area_m2"] = site_area_m2
            
            # Sanity check: If building area is 0 but we have total area, use fallback
            if building_area_m2 < 1.0 and geometry.get("total_area_m2", 0) > 10:
                logger.warning("No building layers detected. Falling back to 50% of total area for building.")
                geometry["building_area_m2"] = geometry["total_area_m2"] * 0.5
                geometry["site_area_m2"] = geometry["total_area_m2"] * 0.5
            
            logger.info(f"Area Split: Building={geometry['building_area_m2']:.2f} m², Site={geometry['site_area_m2']:.2f} m²")

            # Convert length
            if "total_line_length" in geometry and geometry["total_line_length"] > 0:
                original_length = geometry["total_line_length"]
                geometry["total_line_length_original"] = original_length
                geometry["total_line_length_m"] = original_length / length_divisor
                geometry["total_line_length"] = geometry["total_line_length_m"]
                logger.info(f"Length conversion: {original_length:,.0f} {drawing_unit} → {geometry['total_line_length_m']:,.2f} m")

        # CRITICAL FIX: Replace raw layer counts with filtered structural counts
        # This prevents the AI from using inflated counts (which include text/dims/hatches)
        if "area_by_layer" in processed and processed["area_by_layer"]:
            filtered_layers = {}
            for layer_name, layer_info in processed["area_by_layer"].items():
                # Use structural_count if available (filtered valid geometry only)
                # Otherwise fall back to polyline_count (still better than raw count)
                filtered_count = layer_info.get("structural_count", layer_info.get("polyline_count", 0))
                if filtered_count > 0:
                    filtered_layers[layer_name] = filtered_count
            
            # Replace the inflated raw counts with filtered counts
            if filtered_layers:
                processed["layers"] = filtered_layers
                logger.info(f"Replaced raw layer counts with filtered structural counts: {len(filtered_layers)} layers")
        
        return processed

    def _detect_drawing_units(self, raw_data: Dict[str, Any]) -> str:
        """
        Dynamically detect drawing units using multiple signals.

        Analyzes:
        1. Coordinate magnitudes (ITM coords suggest mm or cm)
        2. Block scale factors (100x = 1:100 scale)
        3. Dimension values (actual measurements shown)
        4. Text content (unit mentions like mm, cm, m)
        5. Geometry sanity check (reasonable building sizes)

        Returns: 'mm', 'cm', or 'm'
        """
        # Initialize scoring for each unit type
        scores = {"mm": 0, "cm": 0, "m": 0}
        signals = []

        blocks = raw_data.get("blocks", [])
        geometry = raw_data.get("geometry", {})
        dimensions = raw_data.get("dimensions", [])
        text_entities = raw_data.get("text_entities", [])

        # === Signal 1: Block Scale Analysis ===
        scale_100_count = 0
        scale_1_count = 0
        scale_1000_count = 0

        for block in blocks[:100]:
            scale = block.get("scale", {})
            x_scale = abs(scale.get("x", 1))
            y_scale = abs(scale.get("y", 1))
            avg_scale = (x_scale + y_scale) / 2

            if 99 <= avg_scale <= 101:
                scale_100_count += 1
            elif 999 <= avg_scale <= 1001:
                scale_1000_count += 1
            elif 0.9 <= avg_scale <= 1.1:
                scale_1_count += 1

        if scale_100_count >= 3:
            scores["cm"] += 30
            signals.append(f"scale_100x: {scale_100_count} blocks → cm")
        if scale_1000_count >= 2:
            scores["mm"] += 30
            signals.append(f"scale_1000x: {scale_1000_count} blocks → mm")
        if scale_1_count >= 10 and scale_100_count < 3:
            scores["m"] += 20
            signals.append(f"scale_1x: {scale_1_count} blocks → m")

        # === Signal 2: Coordinate Magnitude Analysis ===
        max_coord = 0
        min_nonzero_coord = float('inf')
        coord_samples = []

        for block in blocks[:50]:
            pos = block.get("position", {})
            x = abs(pos.get("x", 0))
            y = abs(pos.get("y", 0))
            if x > 0:
                coord_samples.append(x)
                min_nonzero_coord = min(min_nonzero_coord, x)
            if y > 0:
                coord_samples.append(y)
                min_nonzero_coord = min(min_nonzero_coord, y)
            max_coord = max(max_coord, x, y)

        # ITM coordinates in Israel: E ~130,000-280,000m, N ~370,000-800,000m
        # In mm: E ~130M-280M, N ~370M-800M
        # In cm: E ~13M-28M, N ~37M-80M
        if max_coord > 100_000_000:  # > 100 million
            scores["mm"] += 40
            signals.append(f"max_coord {max_coord:,.0f} → mm (ITM in mm)")
        elif max_coord > 10_000_000:  # 10-100 million
            scores["cm"] += 35
            scores["mm"] += 15
            signals.append(f"max_coord {max_coord:,.0f} → likely cm")
        elif max_coord > 100_000:  # 100k - 10M
            scores["cm"] += 25
            scores["m"] += 15
            signals.append(f"max_coord {max_coord:,.0f} → cm or m")
        elif max_coord > 1_000:  # 1k - 100k
            scores["m"] += 40
            signals.append(f"max_coord {max_coord:,.0f} → m")
        else:
            scores["m"] += 30
            signals.append(f"max_coord {max_coord:,.0f} → small, assume m")

        # === Signal 3: Dimension Values Analysis ===
        if dimensions:
            dim_values = []
            for dim in dimensions[:50]:
                val = dim.get("measurement") or dim.get("value", 0)
                if isinstance(val, (int, float)) and val > 0:
                    dim_values.append(val)

            if dim_values:
                avg_dim = sum(dim_values) / len(dim_values)
                max_dim = max(dim_values)

                # Typical room dimensions: 3-10m, walls: 0.1-0.5m
                # In mm: 3000-10000, walls: 100-500
                # In cm: 300-1000, walls: 10-50
                if avg_dim > 1000:
                    scores["mm"] += 25
                    signals.append(f"avg_dimension {avg_dim:.0f} → mm")
                elif avg_dim > 100:
                    scores["cm"] += 25
                    signals.append(f"avg_dimension {avg_dim:.0f} → cm")
                else:
                    scores["m"] += 25
                    signals.append(f"avg_dimension {avg_dim:.2f} → m")

        # === Signal 4: Text Content Analysis ===
        unit_mentions = {"mm": 0, "cm": 0, "m": 0, "מ\"ר": 0, "מטר": 0}
        import re

        for text_item in text_entities[:200]:
            text = ""
            if isinstance(text_item, dict):
                text = str(text_item.get("text", "") or text_item.get("value", ""))
            else:
                text = str(text_item)
            text_lower = text.lower()

            # Count unit mentions
            if re.search(r'\bmm\b|מ"מ|מילימטר', text_lower):
                unit_mentions["mm"] += 1
            if re.search(r'\bcm\b|ס"מ|סנטימטר', text_lower):
                unit_mentions["cm"] += 1
            if re.search(r'\bm\b(?!m)|מטר(?!ים)|מ\'(?!מ)', text_lower):
                unit_mentions["m"] += 1
            if re.search(r'מ"ר|m²|sqm', text_lower):
                unit_mentions["מ\"ר"] += 1

        total_mentions = sum(unit_mentions.values())
        if total_mentions > 0:
            if unit_mentions["mm"] > unit_mentions["cm"] and unit_mentions["mm"] > unit_mentions["m"]:
                scores["mm"] += 15
                signals.append(f"text mentions mm: {unit_mentions['mm']}")
            elif unit_mentions["cm"] > unit_mentions["mm"] and unit_mentions["cm"] > unit_mentions["m"]:
                scores["cm"] += 15
                signals.append(f"text mentions cm: {unit_mentions['cm']}")
            elif unit_mentions["m"] > 0:
                scores["m"] += 15
                signals.append(f"text mentions m: {unit_mentions['m']}")

        # === Signal 5: Geometry Sanity Check ===
        total_area = geometry.get("total_area", 0)
        total_length = geometry.get("total_line_length", 0)

        if total_area > 0:
            # Typical building: 100-50,000 m²
            # In mm²: 100M - 50B
            # In cm²: 1M - 500M
            if total_area > 1_000_000_000:  # > 1 billion
                scores["mm"] += 20
                signals.append(f"area {total_area:,.0f} → mm² (very large)")
            elif total_area > 10_000_000:  # 10M - 1B
                scores["cm"] += 20
                signals.append(f"area {total_area:,.0f} → cm²")
            elif total_area > 100_000:  # 100k - 10M
                scores["cm"] += 15
                scores["m"] += 10
                signals.append(f"area {total_area:,.0f} → cm² or m²")
            else:
                scores["m"] += 20
                signals.append(f"area {total_area:,.0f} → m²")

        if total_length > 0:
            # Typical building lines: 500-50,000 m
            # In mm: 500k - 50M
            # In cm: 50k - 5M
            if total_length > 1_000_000:  # > 1M
                scores["mm"] += 15
                signals.append(f"length {total_length:,.0f} → mm")
            elif total_length > 50_000:  # 50k - 1M
                scores["cm"] += 15
                signals.append(f"length {total_length:,.0f} → cm")
            else:
                scores["m"] += 15
                signals.append(f"length {total_length:,.0f} → m")

        # === Final Decision ===
        detected_unit = max(scores, key=scores.get)
        confidence = scores[detected_unit] / max(sum(scores.values()), 1) * 100

        logger.info("=" * 50)
        logger.info("DYNAMIC UNIT DETECTION")
        logger.info("=" * 50)
        for signal in signals:
            logger.info(f"  • {signal}")
        logger.info(f"Scores: mm={scores['mm']}, cm={scores['cm']}, m={scores['m']}")
        logger.info(f"Detected: {detected_unit} (confidence: {confidence:.0f}%)")
        logger.info("=" * 50)

        return detected_unit

    def _truncate_data_for_context(self, data: Dict[str, Any], max_chars: int = 80000) -> Dict[str, Any]:
        """
        Truncate/summarize raw data to fit within GPT-4 context limits.
        Preserves the most important information while reducing size.
        """
        truncated = {}

        # Always keep geometry summary - it's small and important
        if "geometry" in data:
            truncated["geometry"] = data["geometry"]

        # Keep layer information - usually small
        if "layers" in data:
            truncated["layers"] = data["layers"]

        # Keep extraction metadata
        for key in ["extraction_success", "extraction_method", "errors"]:
            if key in data:
                truncated[key] = data[key]

        # Limit blocks - keep first N blocks, group by type
        if "blocks" in data and data["blocks"]:
            blocks = data["blocks"]
            if len(blocks) > 100:
                # Group blocks by name and count them
                block_counts = {}
                block_samples = {}
                for block in blocks:
                    name = block.get("name", "Unknown")
                    if name not in block_counts:
                        block_counts[name] = 0
                        block_samples[name] = block
                    block_counts[name] += 1

                truncated["blocks_summary"] = {
                    "total_blocks": len(blocks),
                    "block_types": block_counts,
                    "sample_blocks": list(block_samples.values())[:50]
                }
            else:
                truncated["blocks"] = blocks

        # Limit text entities - keep unique texts with counts
        if "text_entities" in data and data["text_entities"]:
            texts = data["text_entities"]
            if len(texts) > 200:
                # Count unique text values
                text_counts = {}
                for text in texts:
                    content = text.get("content", "") if isinstance(text, dict) else str(text)
                    if content:
                        text_counts[content] = text_counts.get(content, 0) + 1

                # Keep top 100 most frequent texts
                sorted_texts = sorted(text_counts.items(), key=lambda x: x[1], reverse=True)[:100]
                truncated["text_summary"] = {
                    "total_text_entities": len(texts),
                    "unique_texts": len(text_counts),
                    "top_texts": dict(sorted_texts)
                }
            else:
                truncated["text_entities"] = texts

        # Check final size and further truncate if needed
        json_str = json.dumps(truncated, ensure_ascii=False)
        if len(json_str) > max_chars:
            logger.warning(f"Data still too large ({len(json_str)} chars), further truncating...")
            # Remove sample blocks if still too large
            if "blocks_summary" in truncated and "sample_blocks" in truncated["blocks_summary"]:
                truncated["blocks_summary"]["sample_blocks"] = truncated["blocks_summary"]["sample_blocks"][:20]
            if "text_summary" in truncated and "top_texts" in truncated["text_summary"]:
                top_texts = truncated["text_summary"]["top_texts"]
                truncated["text_summary"]["top_texts"] = dict(list(top_texts.items())[:50])

        return truncated

    def generate_boq_from_raw_data(
        self,
        raw_data: Dict[str, Any],
        filename: str,
        project_name: Optional[str] = None,
        override_area_m2: Optional[float] = None
    ) -> IsraeliBOQ:
        """
        Generate Israeli BOQ from raw AutoCAD extraction data.

        Uses either OpenAI or Ollama based on AI_PROVIDER setting.

        Args:
            raw_data: Raw data extracted from AutoCAD (blocks, text, geometry, layers)
            filename: Original filename
            project_name: Optional project name
            override_area_m2: Optional area override in m² (from user layer selection)

        Returns:
            IsraeliBOQ object with full pricing
        """
        start_time = datetime.now()

        # If user provided an area override, inject it into raw_data
        if override_area_m2 is not None:
            logger.info(f"Using user-confirmed area override: {override_area_m2:.2f} m²")
            # Make a copy to avoid mutating the original
            raw_data = raw_data.copy()
            if "geometry" not in raw_data:
                raw_data["geometry"] = {}
            raw_data["geometry"] = raw_data["geometry"].copy()
            # Set the area in m² - _preprocess_raw_data will detect this
            raw_data["geometry"]["total_area_m2_override"] = override_area_m2

        # Route to appropriate provider
        if self.ai_provider == "ollama":
            return self._generate_boq_with_ollama(raw_data, filename, project_name, start_time)
        else:
            return self._generate_boq_with_openai(raw_data, filename, project_name, start_time)

    def _generate_boq_with_ollama(
        self,
        raw_data: Dict[str, Any],
        filename: str,
        project_name: Optional[str],
        start_time: datetime
    ) -> IsraeliBOQ:
        """
        Generate BOQ using Ollama multi-model pipeline.
        No truncation needed - Qwen has 128k context!
        """
        logger.info("=" * 60)
        logger.info("OLLAMA MULTI-MODEL PIPELINE")
        logger.info("=" * 60)

        # Preprocess raw data to convert units (but NO truncation!)
        processed_data = self._preprocess_raw_data(raw_data)

        # Get Dekel price list for AI context
        dekel_prices_json = self.dekel_pricing.export_price_list_json()

        try:
            # Check if Ollama is available
            if not self.ollama_service.is_available():
                raise RuntimeError(
                    "Ollama is not running. Please start Ollama with: ollama serve"
                )

            # Check required models
            models = self.ollama_service.check_required_models()
            if not models["hebrew_model"] or not models["reasoning_model"]:
                missing = []
                if not models["hebrew_model"]:
                    missing.append(f"ollama pull {models['hebrew_model_name']}")
                if not models["reasoning_model"]:
                    missing.append(f"ollama pull {models['reasoning_model_name']}")
                raise RuntimeError(
                    f"Required Ollama models not installed. Run:\n" +
                    "\n".join(missing)
                )

            # Generate BOQ using multi-model pipeline
            if settings.OLLAMA_USE_MULTI_MODEL:
                boq_json = self.ollama_service.generate_boq_multi_model(
                    raw_data=processed_data,
                    dekel_prices_json=dekel_prices_json,
                    filename=filename,
                    project_name=project_name
                )
            else:
                boq_json = self.ollama_service.generate_boq_single_model(
                    raw_data=processed_data,
                    dekel_prices_json=dekel_prices_json,
                    filename=filename,
                    project_name=project_name
                )

            # Build the BOQ object
            processing_time = (datetime.now() - start_time).total_seconds()
            boq = self._build_boq_from_json(boq_json, filename, processing_time)
            boq.extraction_method = "ollama_multi_model" if settings.OLLAMA_USE_MULTI_MODEL else "ollama_single_model"

            logger.info(f"Generated Israeli BOQ with {len(boq.chapters)} chapters, total: {boq.grand_total:.2f} ILS")
            return boq

        except Exception as e:
            logger.error(f"Failed to generate BOQ with Ollama: {e}")
            raise

    def _generate_boq_with_openai(
        self,
        raw_data: Dict[str, Any],
        filename: str,
        project_name: Optional[str],
        start_time: datetime
    ) -> IsraeliBOQ:
        """
        Generate BOQ using OpenAI GPT-4.
        Includes data truncation for token limit.
        """
        # Preprocess raw data to convert units
        processed_data = self._preprocess_raw_data(raw_data)

        # Truncate data if too large for GPT-4 context
        processed_data = self._truncate_data_for_context(processed_data)

        # Get Dekel price list for AI context
        dekel_prices_json = self.dekel_pricing.export_price_list_json()

        # Prepare the prompt for GPT-4
        user_prompt = f"""נתח את הנתונים הבאים שחולצו מקובץ AutoCAD DWG וצור כתב כמויות מקצועי:

שם הקובץ: {filename}
שם הפרויקט: {project_name or 'לא צוין'}

═══════════════════════════════════════════════════════════════
נתוני AutoCAD שחולצו:
═══════════════════════════════════════════════════════════════

{json.dumps(processed_data, ensure_ascii=False, indent=2)}

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
            
            # Detect construction type to select correct formulas
            construction_type = self.detect_construction_type(project_name=project_name, filename=filename, raw_data=raw_data)
            logger.info(f"Generating dynamic system prompt for type: {construction_type}")
            
            system_prompt = get_system_prompt(construction_type)

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
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
            logger.error(f"Failed to generate BOQ with OpenAI: {e}")
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

    def save_boq_to_database(
        self,
        project_id: int,
        plan_id: int,
        boq: IsraeliBOQ,
        selected_layers: List[str],
        db
    ):
        """
        Save generated BOQ items to database with source tracking.

        Args:
            project_id: Project ID
            plan_id: Plan ID (source file)
            boq: Generated IsraeliBOQ object
            selected_layers: List of selected layer names from the extraction
            db: Database session (SQLAlchemy Session)
        """
        from app.models.boq_item import BOQItem as DBBOQItem

        logger.info(f"Saving BOQ to database for project {project_id}, plan {plan_id}")

        # Clear existing items for THIS PLAN only (not entire project)
        db.query(DBBOQItem).filter(
            DBBOQItem.project_id == project_id,
            DBBOQItem.plan_id == plan_id
        ).delete()
        logger.info(f"Cleared existing BOQ items for project {project_id}, plan {plan_id}")

        # Prepare source layer info
        source_layer = ", ".join(selected_layers[:5]) if selected_layers else "All layers"
        if len(selected_layers) > 5:
            source_layer += f" (+ {len(selected_layers) - 5} more)"

        # Save each BOQ item to database
        items_created = 0
        for chapter in boq.chapters:
            for item in chapter.items:
                db_item = DBBOQItem(
                    project_id=project_id,
                    plan_id=plan_id,
                    chapter_code=chapter.chapter_code,
                    chapter_name_he=chapter.chapter_name_he,
                    chapter_name_en=chapter.chapter_name_en,
                    item_code=item.item_code,
                    description_he=item.description_he,
                    description_en=item.description_en,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    source_filename=boq.filename,
                    source_layer=source_layer,
                    confidence=item.confidence,
                    is_deleted=False,
                    is_modified=False
                )
                db.add(db_item)
                items_created += 1

        db.commit()
        logger.info(f"[OK] Saved {items_created} BOQ items to database")

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
