"""
Dekel Pricing Reference for Israeli Construction BOQ
מחירון דקל - מחירי בניה בישראל

This module provides reference pricing based on the Dekel Price Index,
the standard pricing reference for Israeli construction industry.

Prices are approximate and should be updated regularly.
Last update: 2024
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PriceItem:
    """Single price item from Dekel catalog"""
    code: str           # Dekel item code
    name_he: str        # Hebrew name
    name_en: str        # English name
    unit: str           # Unit of measurement
    price: float        # Price in ILS (שקלים)
    chapter: str        # פרק (chapter)
    category: str       # Category
    includes_labor: bool = True  # כולל עבודה
    includes_materials: bool = True  # כולל חומרים


# Dekel Price Database - מחירון דקל 2024
# Organized by chapters (פרקים) according to Israeli standards
DEKEL_PRICES: Dict[str, PriceItem] = {
    # ═══════════════════════════════════════════════════════════════
    # פרק 01 - עבודות עפר (Earthworks)
    # ═══════════════════════════════════════════════════════════════
    "01.01.01": PriceItem("01.01.01", "חפירה בקרקע רגילה", "Regular soil excavation", "מ\"ק", 45.0, "01", "עבודות עפר"),
    "01.01.02": PriceItem("01.01.02", "חפירה בסלע", "Rock excavation", "מ\"ק", 180.0, "01", "עבודות עפר"),
    "01.02.01": PriceItem("01.02.01", "מילוי חול", "Sand fill", "מ\"ק", 85.0, "01", "עבודות עפר"),
    "01.02.02": PriceItem("01.02.02", "מילוי חצץ", "Gravel fill", "מ\"ק", 95.0, "01", "עבודות עפר"),
    "01.03.01": PriceItem("01.03.01", "פינוי עודפי חפירה", "Excavation disposal", "מ\"ק", 65.0, "01", "עבודות עפר"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 02 - בטון (Concrete)
    # ═══════════════════════════════════════════════════════════════
    "02.01.01": PriceItem("02.01.01", "בטון יסודות B30", "Foundation concrete B30", "מ\"ק", 850.0, "02", "בטון"),
    "02.01.02": PriceItem("02.01.02", "בטון רצפה B25", "Floor concrete B25", "מ\"ק", 780.0, "02", "בטון"),
    "02.02.01": PriceItem("02.02.01", "בטון עמודים B30", "Column concrete B30", "מ\"ק", 950.0, "02", "בטון"),
    "02.02.02": PriceItem("02.02.02", "בטון קורות B30", "Beam concrete B30", "מ\"ק", 920.0, "02", "בטון"),
    "02.03.01": PriceItem("02.03.01", "בטון תקרה B30", "Ceiling concrete B30", "מ\"ק", 880.0, "02", "בטון"),
    "02.04.01": PriceItem("02.04.01", "ברזל זיון", "Reinforcement steel", "טון", 6500.0, "02", "בטון"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 03 - בניה (Masonry)
    # ═══════════════════════════════════════════════════════════════
    "03.01.01": PriceItem("03.01.01", "קיר בלוקים 20 ס\"מ", "Block wall 20cm", "מ\"ר", 185.0, "03", "בניה"),
    "03.01.02": PriceItem("03.01.02", "קיר בלוקים 15 ס\"מ", "Block wall 15cm", "מ\"ר", 165.0, "03", "בניה"),
    "03.01.03": PriceItem("03.01.03", "קיר בלוקים 10 ס\"מ", "Block wall 10cm", "מ\"ר", 145.0, "03", "בניה"),
    "03.02.01": PriceItem("03.02.01", "קיר לבנים", "Brick wall", "מ\"ר", 320.0, "03", "בניה"),
    "03.03.01": PriceItem("03.03.01", "קיר גבס 10 ס\"מ", "Drywall 10cm", "מ\"ר", 165.0, "03", "בניה"),
    "03.03.02": PriceItem("03.03.02", "קיר גבס כפול", "Double drywall", "מ\"ר", 220.0, "03", "בניה"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 04 - איטום (Waterproofing)
    # ═══════════════════════════════════════════════════════════════
    "04.01.01": PriceItem("04.01.01", "איטום ביטומני יסודות", "Bitumen foundation waterproofing", "מ\"ר", 85.0, "04", "איטום"),
    "04.01.02": PriceItem("04.01.02", "איטום גגות שטוחים", "Flat roof waterproofing", "מ\"ר", 120.0, "04", "איטום"),
    "04.02.01": PriceItem("04.02.01", "איטום חדרים רטובים", "Wet room waterproofing", "מ\"ר", 95.0, "04", "איטום"),
    "04.02.02": PriceItem("04.02.02", "איטום מרפסות", "Balcony waterproofing", "מ\"ר", 110.0, "04", "איטום"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 05 - טיח (Plaster)
    # ═══════════════════════════════════════════════════════════════
    "05.01.01": PriceItem("05.01.01", "טיח פנים", "Interior plaster", "מ\"ר", 65.0, "05", "טיח"),
    "05.01.02": PriceItem("05.01.02", "טיח חוץ", "Exterior plaster", "מ\"ר", 85.0, "05", "טיח"),
    "05.02.01": PriceItem("05.02.01", "שפכטל Q3", "Putty Q3", "מ\"ר", 45.0, "05", "טיח"),
    "05.02.02": PriceItem("05.02.02", "שפכטל Q4", "Putty Q4", "מ\"ר", 65.0, "05", "טיח"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 06 - ריצוף (Flooring)
    # ═══════════════════════════════════════════════════════════════
    "06.01.01": PriceItem("06.01.01", "ריצוף קרמיקה 60x60", "Ceramic tiles 60x60", "מ\"ר", 180.0, "06", "ריצוף"),
    "06.01.02": PriceItem("06.01.02", "ריצוף פורצלן 60x60", "Porcelain tiles 60x60", "מ\"ר", 220.0, "06", "ריצוף"),
    "06.02.01": PriceItem("06.02.01", "ריצוף שיש טבעי", "Natural marble flooring", "מ\"ר", 450.0, "06", "ריצוף"),
    "06.02.02": PriceItem("06.02.02", "ריצוף גרניט", "Granite flooring", "מ\"ר", 380.0, "06", "ריצוף"),
    "06.03.01": PriceItem("06.03.01", "פרקט למינציה", "Laminate flooring", "מ\"ר", 145.0, "06", "ריצוף"),
    "06.03.02": PriceItem("06.03.02", "פרקט עץ טבעי", "Natural wood flooring", "מ\"ר", 350.0, "06", "ריצוף"),
    "06.04.01": PriceItem("06.04.01", "חיפוי קירות קרמיקה", "Ceramic wall tiles", "מ\"ר", 165.0, "06", "ריצוף"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 07 - אלומיניום וזכוכית (Aluminum & Glass)
    # ═══════════════════════════════════════════════════════════════
    "07.01.01": PriceItem("07.01.01", "חלון אלומיניום רגיל", "Standard aluminum window", "מ\"ר", 850.0, "07", "אלומיניום"),
    "07.01.02": PriceItem("07.01.02", "חלון אלומיניום תרמי", "Thermal aluminum window", "מ\"ר", 1200.0, "07", "אלומיניום"),
    "07.02.01": PriceItem("07.02.01", "דלת אלומיניום כניסה", "Aluminum entrance door", "יח'", 4500.0, "07", "אלומיניום"),
    "07.02.02": PriceItem("07.02.02", "דלת אלומיניום מרפסת", "Aluminum balcony door", "יח'", 3200.0, "07", "אלומיניום"),
    "07.03.01": PriceItem("07.03.01", "מעקה אלומיניום", "Aluminum railing", "מ\"א", 650.0, "07", "אלומיניום"),
    "07.03.02": PriceItem("07.03.02", "מעקה זכוכית", "Glass railing", "מ\"א", 1100.0, "07", "אלומיניום"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 08 - נגרות (Carpentry)
    # ═══════════════════════════════════════════════════════════════
    "08.01.01": PriceItem("08.01.01", "דלת פנים עץ מלא", "Solid wood interior door", "יח'", 1800.0, "08", "נגרות"),
    "08.01.02": PriceItem("08.01.02", "דלת פנים HDF", "HDF interior door", "יח'", 950.0, "08", "נגרות"),
    "08.01.03": PriceItem("08.01.03", "דלת כניסה מעוצבת", "Designer entrance door", "יח'", 6500.0, "08", "נגרות"),
    "08.02.01": PriceItem("08.02.01", "ארון קיר", "Built-in closet", "מ\"א", 1200.0, "08", "נגרות"),
    "08.02.02": PriceItem("08.02.02", "ארון מטבח", "Kitchen cabinet", "מ\"א", 1800.0, "08", "נגרות"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 09 - צבע (Painting)
    # ═══════════════════════════════════════════════════════════════
    "09.01.01": PriceItem("09.01.01", "צבע פנים אקרילי", "Interior acrylic paint", "מ\"ר", 35.0, "09", "צבע"),
    "09.01.02": PriceItem("09.01.02", "צבע חוץ סיליקוני", "Exterior silicone paint", "מ\"ר", 55.0, "09", "צבע"),
    "09.02.01": PriceItem("09.02.01", "צבע אפוקסי לרצפה", "Epoxy floor paint", "מ\"ר", 85.0, "09", "צבע"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 10 - אינסטלציה (Plumbing)
    # ═══════════════════════════════════════════════════════════════
    "10.01.01": PriceItem("10.01.01", "נקודת מים קרים", "Cold water point", "יח'", 450.0, "10", "אינסטלציה"),
    "10.01.02": PriceItem("10.01.02", "נקודת מים חמים", "Hot water point", "יח'", 550.0, "10", "אינסטלציה"),
    "10.02.01": PriceItem("10.02.01", "נקודת ביוב", "Sewage point", "יח'", 650.0, "10", "אינסטלציה"),
    "10.03.01": PriceItem("10.03.01", "אסלה סטנדרטית", "Standard toilet", "יח'", 1200.0, "10", "אינסטלציה"),
    "10.03.02": PriceItem("10.03.02", "אסלה תלויה", "Wall-hung toilet", "יח'", 2500.0, "10", "אינסטלציה"),
    "10.04.01": PriceItem("10.04.01", "כיור רחצה", "Bathroom sink", "יח'", 850.0, "10", "אינסטלציה"),
    "10.04.02": PriceItem("10.04.02", "כיור מטבח", "Kitchen sink", "יח'", 1100.0, "10", "אינסטלציה"),
    "10.05.01": PriceItem("10.05.01", "אמבטיה אקרילית", "Acrylic bathtub", "יח'", 1800.0, "10", "אינסטלציה"),
    "10.05.02": PriceItem("10.05.02", "מקלחון זכוכית", "Glass shower enclosure", "יח'", 3500.0, "10", "אינסטלציה"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 11 - חשמל (Electrical)
    # ═══════════════════════════════════════════════════════════════
    "11.01.01": PriceItem("11.01.01", "נקודת חשמל רגילה", "Standard electrical point", "יח'", 180.0, "11", "חשמל"),
    "11.01.02": PriceItem("11.01.02", "נקודת חשמל כוח", "Power outlet", "יח'", 250.0, "11", "חשמל"),
    "11.02.01": PriceItem("11.02.01", "נקודת תאורה", "Lighting point", "יח'", 220.0, "11", "חשמל"),
    "11.02.02": PriceItem("11.02.02", "ספוט שקוע", "Recessed spotlight", "יח'", 180.0, "11", "חשמל"),
    "11.03.01": PriceItem("11.03.01", "לוח חשמל 24 מודולים", "24-module electrical panel", "יח'", 2800.0, "11", "חשמל"),
    "11.03.02": PriceItem("11.03.02", "לוח חשמל 36 מודולים", "36-module electrical panel", "יח'", 3500.0, "11", "חשמל"),

    # ═══════════════════════════════════════════════════════════════
    # פרק 12 - מיזוג אוויר (HVAC)
    # ═══════════════════════════════════════════════════════════════
    "12.01.01": PriceItem("12.01.01", "מזגן עילי 1.5 כ\"ס", "Split AC 1.5HP", "יח'", 3500.0, "12", "מיזוג"),
    "12.01.02": PriceItem("12.01.02", "מזגן עילי 2 כ\"ס", "Split AC 2HP", "יח'", 4500.0, "12", "מיזוג"),
    "12.02.01": PriceItem("12.02.01", "צנרת מיזוג", "AC piping", "מ\"א", 120.0, "12", "מיזוג"),
}


class DekelPricing:
    """
    Interface to Dekel pricing database.
    מחירון דקל - ממשק למחירי בניה
    """

    def __init__(self):
        self.prices = DEKEL_PRICES

    def get_price(self, code: str) -> Optional[PriceItem]:
        """Get price item by Dekel code"""
        return self.prices.get(code)

    def search_by_name(self, search_term: str, language: str = "he") -> List[PriceItem]:
        """Search prices by name (Hebrew or English)"""
        results = []
        search_lower = search_term.lower()

        for item in self.prices.values():
            if language == "he" and search_lower in item.name_he.lower():
                results.append(item)
            elif language == "en" and search_lower in item.name_en.lower():
                results.append(item)
            elif search_lower in item.name_he.lower() or search_lower in item.name_en.lower():
                results.append(item)

        return results

    def get_chapter(self, chapter_code: str) -> List[PriceItem]:
        """Get all items in a chapter"""
        return [item for item in self.prices.values() if item.chapter == chapter_code]

    def get_all_chapters(self) -> Dict[str, str]:
        """Get all chapter codes and names"""
        return {
            "01": "עבודות עפר - Earthworks",
            "02": "בטון - Concrete",
            "03": "בניה - Masonry",
            "04": "איטום - Waterproofing",
            "05": "טיח - Plaster",
            "06": "ריצוף - Flooring",
            "07": "אלומיניום וזכוכית - Aluminum & Glass",
            "08": "נגרות - Carpentry",
            "09": "צבע - Painting",
            "10": "אינסטלציה - Plumbing",
            "11": "חשמל - Electrical",
            "12": "מיזוג אוויר - HVAC",
        }

    def calculate_total(self, items: List[Dict]) -> Dict:
        """
        Calculate total price for a list of items.

        Args:
            items: List of dicts with 'code' and 'quantity' keys

        Returns:
            Dict with item details and totals
        """
        result = {
            "items": [],
            "subtotal": 0.0,
            "vat": 0.0,
            "total": 0.0
        }

        for item in items:
            code = item.get("code")
            quantity = item.get("quantity", 0)

            price_item = self.get_price(code)
            if price_item:
                line_total = price_item.price * quantity
                result["items"].append({
                    "code": code,
                    "name_he": price_item.name_he,
                    "name_en": price_item.name_en,
                    "unit": price_item.unit,
                    "unit_price": price_item.price,
                    "quantity": quantity,
                    "line_total": line_total
                })
                result["subtotal"] += line_total

        # VAT 17% (מע"מ)
        result["vat"] = result["subtotal"] * 0.17
        result["total"] = result["subtotal"] + result["vat"]

        return result

    def export_price_list_json(self) -> str:
        """Export full price list as JSON for AI context"""
        import json

        export_data = []
        for code, item in self.prices.items():
            export_data.append({
                "code": code,
                "name_he": item.name_he,
                "name_en": item.name_en,
                "unit": item.unit,
                "price_ils": item.price,
                "chapter": item.chapter,
                "category": item.category
            })

        return json.dumps(export_data, ensure_ascii=False, indent=2)


def get_dekel_price(code: str) -> Optional[PriceItem]:
    """Convenience function to get a price by code"""
    return DekelPricing().get_price(code)
