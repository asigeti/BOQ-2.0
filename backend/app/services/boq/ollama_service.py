"""
Ollama Multi-Model Pipeline Service
====================================

This service provides a multi-model pipeline using Ollama for BOQ generation:
1. Aya Expanse 32B - Hebrew language specialist (translation & understanding)
2. Qwen 2.5 72B - Reasoning powerhouse (BOQ generation with 128k context)

The pipeline:
1. Stage 1: Aya reads Hebrew text from DWG data and translates to English
2. Stage 2: Qwen analyzes the construction data and generates BOQ
3. Stage 3: Aya translates the BOQ back to Hebrew

Benefits:
- No token truncation needed (Qwen has 128k context)
- Best Hebrew accuracy (Aya has native Hebrew support)
- Best reasoning (Qwen excels at structured data)
- Runs locally (no API costs, no data leaving your machine)
"""

import json
import logging
import httpx
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama service"""
    base_url: str = "http://localhost:11434"
    hebrew_model: str = "aya-expanse:32b-q4_K_M"  # Hebrew specialist
    reasoning_model: str = "qwen2.5:72b-instruct-q4_K_M"  # Reasoning powerhouse
    timeout: int = 600  # 10 minutes for large models
    use_multi_model: bool = True  # Use multi-model pipeline


class OllamaService:
    """
    Multi-model Ollama service for BOQ generation.

    Uses a pipeline approach:
    1. Hebrew model (Aya) for text extraction and translation
    2. Reasoning model (Qwen) for BOQ analysis and generation
    3. Hebrew model (Aya) for final Hebrew translation
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig(
            base_url=settings.OLLAMA_BASE_URL,
            hebrew_model=settings.OLLAMA_HEBREW_MODEL,
            reasoning_model=settings.OLLAMA_REASONING_MODEL,
            timeout=settings.OLLAMA_TIMEOUT,
            use_multi_model=settings.OLLAMA_USE_MULTI_MODEL
        )
        self._client = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout)
            )
        return self._client

    def is_available(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            logger.info(f"Checking Ollama availability at {self.config.base_url}")
            response = self.client.get("/api/tags")
            logger.info(f"Ollama response status: {response.status_code}")
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.info(f"Ollama available with {len(models)} models")
                return True
            else:
                logger.warning(f"Ollama returned status {response.status_code}")
                return False
        except httpx.ConnectError as e:
            logger.error(f"Ollama connection error: {e}")
            return False
        except httpx.TimeoutException as e:
            logger.error(f"Ollama timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"Ollama not available - {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def list_models(self) -> list:
        """List available models in Ollama"""
        try:
            response = self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    def check_required_models(self) -> Dict[str, bool]:
        """Check if required models are installed"""
        available = self.list_models()

        # Check for models (partial match for version tags)
        hebrew_available = any(
            self.config.hebrew_model.split(":")[0] in m
            for m in available
        )
        reasoning_available = any(
            self.config.reasoning_model.split(":")[0] in m
            for m in available
        )

        return {
            "hebrew_model": hebrew_available,
            "reasoning_model": reasoning_available,
            "hebrew_model_name": self.config.hebrew_model,
            "reasoning_model_name": self.config.reasoning_model,
            "available_models": available
        }

    def _call_model(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        format_json: bool = False
    ) -> str:
        """Call an Ollama model with the given prompt"""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 131072 if "72b" in model.lower() or "70b" in model.lower() else 32768,
            }
        }

        if format_json:
            payload["format"] = "json"

        logger.info(f"Calling Ollama model: {model}")
        start_time = datetime.now()

        try:
            response = self.client.post("/api/chat", json=payload)
            response.raise_for_status()

            result = response.json()
            content = result.get("message", {}).get("content", "")

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Model {model} responded in {elapsed:.2f}s")

            return content

        except httpx.TimeoutException:
            logger.error(f"Timeout calling model {model}")
            raise
        except Exception as e:
            logger.error(f"Error calling model {model}: {e}")
            raise

    def stage1_extract_hebrew(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 1: Use Aya to extract and translate Hebrew text from DWG data.

        This stage:
        - Identifies all Hebrew text in the data
        - Translates Hebrew to English
        - Preserves numerical data and structure
        """

        system_prompt = """You are a Hebrew-English translation expert specializing in construction and architecture.
Your task is to:
1. Find all Hebrew text in the AutoCAD data
2. Translate Hebrew text to English accurately
3. Preserve all numerical values, measurements, and coordinates exactly
4. Maintain the data structure

Important construction terms:
- קיר = wall
- דלת = door
- חלון = window
- רצפה = floor
- תקרה = ceiling
- מדרגות = stairs
- מרפסת = balcony
- חדר = room
- מטבח = kitchen
- שירותים = bathroom
- סלון = living room
- חדר שינה = bedroom

Output a JSON with the same structure, but with Hebrew translated to English."""

        prompt = f"""Analyze this AutoCAD DWG extraction data. Translate any Hebrew text to English while keeping all other data intact.

Data:
{json.dumps(raw_data, ensure_ascii=False, indent=2)}

Return the data with Hebrew translated to English in JSON format."""

        logger.info("Stage 1: Extracting and translating Hebrew text with Aya...")

        response = self._call_model(
            model=self.config.hebrew_model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            format_json=True
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Stage 1 response not valid JSON, returning original data")
            return raw_data

    def stage2_generate_boq(
        self,
        english_data: Dict[str, Any],
        dekel_prices_json: str,
        filename: str,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage 2: Use Qwen to generate BOQ from English data.

        This stage uses the powerful reasoning model with 128k context
        to analyze all construction data and generate a detailed BOQ.
        """

        system_prompt = """You are a professional Quantity Surveyor with 25 years of experience in Israeli construction.
Your expertise includes:
- Analyzing architectural and engineering plans
- Preparing professional Bills of Quantities (BOQ)
- Pricing according to Dekel price list (מחירון דקל)
- Israeli construction standards

Your task: Analyze AutoCAD extraction data and generate a professional BOQ.

Unit Conversion (AutoCAD uses mm):
- Areas: divide by 1,000,000 for m² (mm² → m²)
- Lengths: divide by 1,000 for meters (mm → m)
- If values already look reasonable (tens to hundreds), don't convert

Chapter Structure:
- Chapter 01: Earthworks
- Chapter 02: Concrete
- Chapter 03: Masonry (walls - blocks/bricks/drywall)
- Chapter 04: Waterproofing
- Chapter 05: Plastering
- Chapter 06: Flooring and Tiling
- Chapter 07: Aluminum and Glass
- Chapter 08: Carpentry (doors, cabinets)
- Chapter 09: Painting
- Chapter 10: Plumbing
- Chapter 11: Electrical
- Chapter 12: HVAC

Output JSON format:
{
  "project_name": "Project Name",
  "date": "YYYY-MM-DD",
  "chapters": [
    {
      "chapter_code": "01",
      "chapter_name_en": "Earthworks",
      "items": [
        {
          "item_code": "01.01.01",
          "dekel_code": "01.01.01",
          "description_en": "English description",
          "quantity": 100.0,
          "unit": "m³",
          "unit_price": 45.0,
          "total_price": 4500.0,
          "confidence": 0.95,
          "notes": "Notes"
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
  "notes": ["General notes"]
}"""

        prompt = f"""Analyze the following AutoCAD DWG extraction data and generate a professional Bill of Quantities (BOQ).

Filename: {filename}
Project Name: {project_name or 'Not specified'}

═══════════════════════════════════════════════════════════════
AutoCAD Extraction Data:
═══════════════════════════════════════════════════════════════

{json.dumps(english_data, ensure_ascii=False, indent=2)}

═══════════════════════════════════════════════════════════════
Dekel Price List (for pricing):
═══════════════════════════════════════════════════════════════

{dekel_prices_json}

═══════════════════════════════════════════════════════════════

Instructions:
1. Analyze all blocks, text entities, and geometry
2. Classify into appropriate chapters
3. Match to Dekel pricing codes where possible
4. Calculate quantities and totals
5. Add 17% VAT
6. Return JSON in the specified format

Important: If uncertain about an item, use low confidence (< 0.7) and add a note."""

        logger.info("Stage 2: Generating BOQ with Qwen (128k context)...")

        response = self._call_model(
            model=self.config.reasoning_model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            format_json=True
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Stage 2 response not valid JSON: {e}")
            raise ValueError(f"Failed to parse BOQ response: {e}")

    def stage3_translate_to_hebrew(self, boq_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 3: Use Aya to translate BOQ back to Hebrew.

        This stage translates all English text in the BOQ to Hebrew
        while preserving the JSON structure and numerical values.
        """

        system_prompt = """You are a Hebrew translation expert specializing in Israeli construction terminology.
Your task is to translate a Bill of Quantities (BOQ) from English to Hebrew.

Important:
1. Translate all English descriptions to Hebrew
2. Keep all numerical values, prices, and calculations exactly the same
3. Keep the JSON structure exactly the same
4. Use proper Israeli construction terminology

Chapter names in Hebrew:
- Earthworks = עבודות עפר
- Concrete = בטון
- Masonry = בניה
- Waterproofing = איטום
- Plastering = טיח
- Flooring and Tiling = ריצוף וחיפוי
- Aluminum and Glass = אלומיניום וזכוכית
- Carpentry = נגרות
- Painting = צבע
- Plumbing = אינסטלציה
- Electrical = חשמל
- HVAC = מיזוג אוויר

Unit abbreviations in Hebrew:
- m² = מ"ר
- m = מ"א (meter linear) or מטר
- m³ = מ"ק
- unit = יחידה
- kg = ק"ג

Return the complete BOQ JSON with Hebrew translations added."""

        prompt = f"""Translate this Bill of Quantities to Hebrew.
Add Hebrew fields (chapter_name_he, description_he) while keeping all English fields and numerical values.

BOQ Data:
{json.dumps(boq_data, ensure_ascii=False, indent=2)}

Return the complete JSON with Hebrew translations added to each item."""

        logger.info("Stage 3: Translating BOQ to Hebrew with Aya...")

        response = self._call_model(
            model=self.config.hebrew_model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            format_json=True
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Stage 3 response not valid JSON, returning English BOQ")
            return boq_data

    def generate_boq_multi_model(
        self,
        raw_data: Dict[str, Any],
        dekel_prices_json: str,
        filename: str,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate BOQ using the multi-model pipeline.

        Pipeline:
        1. Aya: Extract/translate Hebrew from DWG data
        2. Qwen: Generate BOQ with 128k context (no truncation!)
        3. Aya: Translate BOQ to Hebrew

        Returns:
            Complete BOQ dictionary with Hebrew and English
        """
        start_time = datetime.now()

        # Stage 1: Extract and translate Hebrew
        logger.info("=" * 60)
        logger.info("STAGE 1: Hebrew Text Extraction (Aya Expanse)")
        logger.info("=" * 60)
        english_data = self.stage1_extract_hebrew(raw_data)

        # Stage 2: Generate BOQ (with full 128k context!)
        logger.info("=" * 60)
        logger.info("STAGE 2: BOQ Generation (Qwen 72B - 128k context)")
        logger.info("=" * 60)
        boq_english = self.stage2_generate_boq(
            english_data=english_data,
            dekel_prices_json=dekel_prices_json,
            filename=filename,
            project_name=project_name
        )

        # Stage 3: Translate to Hebrew
        logger.info("=" * 60)
        logger.info("STAGE 3: Hebrew Translation (Aya Expanse)")
        logger.info("=" * 60)
        boq_hebrew = self.stage3_translate_to_hebrew(boq_english)

        # Add metadata
        processing_time = (datetime.now() - start_time).total_seconds()
        boq_hebrew["metadata"] = {
            "extraction_method": "ollama_multi_model_pipeline",
            "hebrew_model": self.config.hebrew_model,
            "reasoning_model": self.config.reasoning_model,
            "processing_time_seconds": processing_time,
            "generated_at": datetime.now().isoformat()
        }

        logger.info("=" * 60)
        logger.info(f"BOQ Generation Complete! Total time: {processing_time:.2f}s")
        logger.info("=" * 60)

        return boq_hebrew

    def generate_boq_single_model(
        self,
        raw_data: Dict[str, Any],
        dekel_prices_json: str,
        filename: str,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate BOQ using a single model (for simpler setups).
        Uses the reasoning model with a combined Hebrew prompt.
        """
        from app.services.boq.israeli_boq_service import ISRAELI_BOQ_SYSTEM_PROMPT

        prompt = f"""נתח את הנתונים הבאים שחולצו מקובץ AutoCAD DWG וצור כתב כמויות מקצועי:

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

        start_time = datetime.now()

        response = self._call_model(
            model=self.config.reasoning_model,
            prompt=prompt,
            system_prompt=ISRAELI_BOQ_SYSTEM_PROMPT,
            temperature=0.2,
            format_json=True
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        try:
            boq_data = json.loads(response)
            boq_data["metadata"] = {
                "extraction_method": "ollama_single_model",
                "model": self.config.reasoning_model,
                "processing_time_seconds": processing_time,
                "generated_at": datetime.now().isoformat()
            }
            return boq_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BOQ response: {e}")
            raise ValueError(f"Failed to parse BOQ response: {e}")

    def __del__(self):
        if self._client:
            self._client.close()


# Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create the Ollama service singleton"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
