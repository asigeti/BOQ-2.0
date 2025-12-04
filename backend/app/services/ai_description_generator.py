"""
AI Description Generator for BOQ Items
=======================================

This service generates professional, detailed Hebrew descriptions for BOQ items
based on DWG extraction data, similar to Dekel standards.

It analyzes:
- Layer names and patterns
- Measured quantities (area, length, count)
- Chapter context
- Related geometry data

And generates contextual descriptions following Israeli construction standards.
"""

import logging
from typing import Dict, Optional, List
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


# Hebrew BOQ Description Enhancement Prompt
BOQ_DESCRIPTION_PROMPT = """אתה מומחה בכתיבת תיאורים מפורטים לכתבי כמויות ישראליים.
המשימה שלך היא ליצור תיאור מקצועי ומפורט בעברית לפריט בכתב כמויות, בהתבסס על:
1. נתוני שכבה (Layer) מקובץ DWG
2. מידות וכמויות שנמדדו
3. הקשר של הפרק והסעיף

══════════════════════════════════════════════════════════════════════════════
דרישות לתיאור:
══════════════════════════════════════════════════════════════════════════════
✓ בעברית בלבד, שפה מקצועית וברורה
✓ כולל פרטים טכניים רלוונטיים (עובי, מידות, חומרים)
✓ עוקב אחר מוסכמות המפרט הכללל לעבודות בנייה (הספר הכחול)
✓ דומה לסגנון מחירון דקל
✓ ללא מידע מיותר או כללי מדי
✓ מתאים לתקני מכון התקנים הישראלי (ת"י)

══════════════════════════════════════════════════════════════════════════════
דוגמאות לתיאורים מקצועיים:
══════════════════════════════════════════════════════════════════════════════

【עבודות עפר】
❌ לא טוב: "חפירה לבניין"
✓ טוב: "חפירה כללית לעומק ממוצע 1.5 מ', כולל הידוק קרקע תחתית לפי ת"י 1211, פינוי עודפי עפר מחוץ לאתר"

【עבודות בטון】
❌ לא טוב: "בטון ליסודות"
✓ טוב: "יציקת בטון מזוין B-30 ליסודות רצועה, כולל אספקת בטון, יציקה, ריטוט ואחזקה, עובי 50 ס"מ"

【עבודות בנייה】
❌ לא טוב: "קיר בלוקים"
✓ טוב: "קיר בלוקי בטון חלולים 20 ס"מ, מבנה נושא, ביצוע לפי ת"י 5, כולל מילוי בטון ואבטוח לעמודים"

【עבודות איטום】
❌ לא טוב: "איטום גג"
✓ טוב: "איטום גג שטוח בממברנה ביטומנית דו-שכבתית APP 4 מ"מ, כולל יריעת ניקוז (מסנן), לפי ת"י 1203"

【עבודות טיח】
❌ לא טוב: "טיח קירות"
✓ טוב: "טיח צמנט בהתזה (שפריץ) על קירות חוץ, עובי 2.5 ס"מ, תערובת 1:4, גמר מוחלק ומשויף"

【ריצוף וחיפוי】
❌ לא טוב: "אריחים"
✓ טוב: "ריצוף קרמיקה פורצלן מיוצר 60×60 ס"מ, דרגה A, התקנה על מצע מיישר מוכן, כולל פוגות וניקוי"

══════════════════════════════════════════════════════════════════════════════
הנחיות לייצור התיאור:
══════════════════════════════════════════════════════════════════════════════
1. נתח את שם השכבה (Layer Name) - לעיתים מכיל רמזים על החומר או היישום
2. התאם את התיאור לפרק ולסעיף הרלוונטי
3. הוסף פרטים טכניים סטנדרטיים (עובי, תקן, שיטת ביצוע)
4. השתמש במינוח מקצועי מקובל בענף הבנייה
5. ודא שהתיאור מתאים לכמות וליחידת המידה

══════════════════════════════════════════════════════════════════════════════
פורמט פלט:
══════════════════════════════════════════════════════════════════════════════
החזר JSON בפורמט הבא:
{
  "description_he": "התיאור המפורט בעברית",
  "description_en": "Detailed description in English (optional)",
  "technical_notes": "הערות טכניות נוספות (אופציונלי)",
  "confidence": 0.85
}

confidence = רמת הביטחון בתיאור (0.0-1.0):
- 0.9-1.0: תיאור מדויק מאוד, מבוסס על נתונים ברורים
- 0.7-0.9: תיאור סביר, מבוסס על הנחות סטנדרטיות
- 0.5-0.7: תיאור כללי, דורש אימות
- 0.0-0.5: תיאור לא בטוח, דורש עריכה ידנית
"""


class AIDescriptionGenerator:
    """Generate professional BOQ item descriptions using AI"""

    def __init__(self):
        self.ai_provider = settings.AI_PROVIDER
        logger.info(f"AI Description Generator initialized with provider: {self.ai_provider}")

    def generate_description(
        self,
        item_code: str,
        basic_description: str,
        layer_name: Optional[str],
        quantity: float,
        unit: str,
        chapter_code: str,
        chapter_name_he: str,
        area_m2: Optional[float] = None,
        polyline_count: Optional[int] = None,
        hatch_count: Optional[int] = None,
    ) -> Dict:
        """
        Generate enhanced description for a BOQ item based on DWG extraction data.

        Args:
            item_code: BOQ item code
            basic_description: Basic description from extraction
            layer_name: DWG layer name (may contain hints about material/usage)
            quantity: Measured quantity
            unit: Unit of measure (m², m³, m, יח')
            chapter_code: Chapter code (e.g., "02", "03")
            chapter_name_he: Chapter name in Hebrew
            area_m2: Area in square meters (if relevant)
            polyline_count: Number of polylines in layer
            hatch_count: Number of hatches in layer

        Returns:
            Dict with enhanced description and metadata
        """
        try:
            # Build context for AI
            context = {
                "item_code": item_code,
                "basic_description": basic_description,
                "layer_name": layer_name or "Unknown",
                "quantity": quantity,
                "unit": unit,
                "chapter_code": chapter_code,
                "chapter_name_he": chapter_name_he,
                "area_m2": area_m2,
                "polyline_count": polyline_count,
                "hatch_count": hatch_count,
            }

            # Create prompt
            user_prompt = f"""צור תיאור מקצועי לפריט כתב כמויות זה:

נתוני הפריט:
═══════════════════════════════════════════════════════════════
קוד סעיף: {item_code}
פרק: {chapter_code} - {chapter_name_he}
תיאור בסיסי: {basic_description}
שם שכבה (Layer): {layer_name or "לא זמין"}
כמות: {quantity:,.2f} {unit}
שטח (אם רלוונטי): {f"{area_m2:,.2f} מ״ר" if area_m2 else "לא רלוונטי"}
מספר פוליגונים: {polyline_count if polyline_count else "לא זמין"}
מספר Hatches: {hatch_count if hatch_count else "לא זמין"}

צור תיאור מפורט ומקצועי בעברית לפי המפרט הכללל לעבודות בנייה.
החזר תשובה בפורמט JSON בלבד."""

            logger.info(f"Generating AI description for item {item_code} using {self.ai_provider}")

            # Call AI based on provider
            if self.ai_provider == "openai":
                result = self._generate_with_openai(user_prompt)
            elif self.ai_provider == "ollama":
                result = self._generate_with_ollama(user_prompt)
            else:
                raise ValueError(f"Unsupported AI provider: {self.ai_provider}")

            logger.info(f"Successfully generated description for {item_code}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate AI description: {e}")
            # Return fallback result
            return {
                "description_he": basic_description,
                "description_en": "",
                "technical_notes": "AI description generation failed",
                "confidence": 0.3,
                "error": str(e)
            }

    def _generate_with_openai(self, user_prompt: str) -> Dict:
        """Generate description using OpenAI GPT-4"""
        try:
            from openai import OpenAI

            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")

            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": BOQ_DESCRIPTION_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Low temperature for consistent, professional output
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            return result

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def _generate_with_ollama(self, user_prompt: str) -> Dict:
        """Generate description using Ollama multi-model pipeline"""
        try:
            import requests

            # Use Hebrew specialist model (Aya Expanse) for Hebrew BOQ descriptions
            model = settings.OLLAMA_HEBREW_MODEL

            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": f"{BOQ_DESCRIPTION_PROMPT}\n\n{user_prompt}",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 500,
                    }
                },
                timeout=settings.OLLAMA_TIMEOUT
            )

            if response.status_code != 200:
                raise ValueError(f"Ollama returned status {response.status_code}")

            result_text = response.json()["response"]

            # Try to parse JSON from response
            # Ollama may include extra text, so extract JSON
            if "{" in result_text and "}" in result_text:
                json_start = result_text.index("{")
                json_end = result_text.rindex("}") + 1
                json_str = result_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                # Fallback if JSON parsing fails
                result = {
                    "description_he": result_text,
                    "description_en": "",
                    "technical_notes": "",
                    "confidence": 0.6
                }

            return result

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    def enhance_boq_items_batch(
        self,
        items: List[Dict],
        extraction_layers: Optional[Dict[str, Dict]] = None
    ) -> List[Dict]:
        """
        Enhance multiple BOQ items with AI-generated descriptions.

        Args:
            items: List of BOQ item dicts
            extraction_layers: Optional dict mapping layer names to extraction data

        Returns:
            List of enhanced BOQ items with AI descriptions
        """
        enhanced_items = []

        for item in items:
            try:
                # Get layer data if available
                layer_name = item.get("source_layer")
                layer_data = None
                if extraction_layers and layer_name:
                    layer_data = extraction_layers.get(layer_name, {})

                # Generate enhanced description
                ai_result = self.generate_description(
                    item_code=item.get("item_code", ""),
                    basic_description=item.get("description_he", ""),
                    layer_name=layer_name,
                    quantity=item.get("quantity", 0),
                    unit=item.get("unit", ""),
                    chapter_code=item.get("chapter_code", ""),
                    chapter_name_he=item.get("chapter_name_he", ""),
                    area_m2=layer_data.get("area_m2") if layer_data else None,
                    polyline_count=layer_data.get("polyline_count") if layer_data else None,
                    hatch_count=layer_data.get("hatch_count") if layer_data else None,
                )

                # Update item with AI-generated description
                enhanced_item = item.copy()
                enhanced_item["description_he"] = ai_result.get("description_he", item.get("description_he"))
                enhanced_item["description_en"] = ai_result.get("description_en", "")
                enhanced_item["ai_notes"] = ai_result.get("technical_notes", "")
                enhanced_item["ai_confidence"] = ai_result.get("confidence", 0.5)

                enhanced_items.append(enhanced_item)

            except Exception as e:
                logger.error(f"Failed to enhance item {item.get('item_code')}: {e}")
                # Keep original item if enhancement fails
                enhanced_items.append(item)

        return enhanced_items


# Singleton instance
_generator = None


def get_ai_description_generator() -> AIDescriptionGenerator:
    """Get or create singleton AI description generator"""
    global _generator
    if _generator is None:
        _generator = AIDescriptionGenerator()
    return _generator
