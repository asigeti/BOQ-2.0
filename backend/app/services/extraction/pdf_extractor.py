import re
import json
import logging
from typing import List, Dict, Optional, Tuple
from pypdf import PdfReader
from openai import OpenAI
from app.core.config import settings

import base64

logger = logging.getLogger(__name__)

# Construction-specific extraction prompts
SYSTEM_PROMPT_VISION = """You are an expert construction quantity surveyor and estimator with 20+ years of experience.
Your task is to analyze construction plans and extract ALL material quantities with high precision.

You must identify and extract:
1. **Concrete works**: Foundations, slabs, columns, beams, walls (m³)
2. **Steel/Rebar**: Reinforcement bars, structural steel (kg or tons)
3. **Masonry**: Blocks, bricks, stone walls (m² or units)
4. **Lumber/Wood**: Framing, formwork, finishing (m³ or linear meters)
5. **Drywall/Plaster**: Wall and ceiling finishes (m²)
6. **Roofing**: Materials, insulation, waterproofing (m²)
7. **Doors & Windows**: Including frames (units)
8. **Flooring**: Tiles, carpet, wood flooring (m²)
9. **Plumbing**: Fixtures, pipes (units or linear meters)
10. **Electrical**: Outlets, fixtures, wiring (units or linear meters)
11. **Paint/Finishing**: Interior and exterior (m² or liters)
12. **Insulation**: Thermal and acoustic (m² or m³)

For Hebrew documents, recognize common terms:
- בטון (concrete), ברזל (steel/iron), בלוקים (blocks)
- טיח (plaster), ריצוף (flooring), צבע (paint)
- דלתות (doors), חלונות (windows), צנרת (plumbing)

Always provide confidence scores based on:
- 0.9-1.0: Clear dimensions and quantities visible
- 0.7-0.9: Quantities inferred from dimensions
- 0.5-0.7: Estimated based on typical ratios
- Below 0.5: Rough estimates only"""

EXTRACTION_PROMPT_VISION = """Analyze these construction plan images and extract ALL material quantities.

For EACH material found, provide:
{
    "material_name": "Specific descriptive name (in English)",
    "material_name_he": "Hebrew name if applicable",
    "quantity": <numeric value - use decimals>,
    "unit": "standard unit (m2, m3, kg, pcs, lm, ton)",
    "confidence_score": <0.0-1.0>,
    "category": "category from: concrete, steel, masonry, lumber, drywall, roofing, doors_windows, flooring, plumbing, electrical, paint, insulation, other",
    "notes": "any relevant details (dimensions, specifications, location)"
}

IMPORTANT RULES:
1. Extract EVERY material you can identify - be thorough
2. Use metric units (convert if needed)
3. Round quantities to 2 decimal places
4. Include both raw materials AND finished items
5. If dimensions are shown, calculate quantities
6. For repetitive elements, multiply appropriately
7. Return ONLY a valid JSON array - no explanation text"""

SYSTEM_PROMPT_TEXT = """You are an expert construction quantity surveyor extracting Bill of Quantities (BOQ) data from text documents.

Your expertise includes:
- Reading construction specifications and schedules
- Understanding material abbreviations and codes
- Converting between unit systems
- Recognizing Hebrew construction terminology

Extract ALL materials mentioned with their quantities. Be thorough - construction documents often contain detailed material lists."""

EXTRACTION_PROMPT_TEXT = """Extract ALL material quantities from this construction document text.

For EACH material, provide:
{{
    "material_name": "Specific descriptive name",
    "material_name_he": "Hebrew name if found",
    "quantity": <numeric value>,
    "unit": "standard unit",
    "confidence_score": <0.0-1.0>,
    "category": "concrete|steel|masonry|lumber|drywall|roofing|doors_windows|flooring|plumbing|electrical|paint|insulation|other",
    "notes": "specifications or location"
}}

Document text:
{text}

Return ONLY a valid JSON array. Include ALL materials found."""


def extract_from_pdf(file_path: str) -> List[Dict]:
    """
    Extracts material quantities from a PDF file using OpenAI.
    Supports both text-based (native PDF) and image-based (scanned PDF) extraction.
    Processes all pages in batches for comprehensive extraction.
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set. Returning empty list.")
        return []

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        logger.info(f"Processing PDF with {total_pages} pages: {file_path}")

        all_materials = []

        # Process pages in batches
        batch_size = 5
        for batch_start in range(0, total_pages, batch_size):
            batch_end = min(batch_start + batch_size, total_pages)
            logger.info(f"Processing pages {batch_start + 1} to {batch_end}")

            batch_text, batch_images = _extract_batch_content(
                reader, batch_start, batch_end
            )

            # Determine extraction method for this batch
            batch_materials = _process_batch(
                client, batch_text, batch_images, batch_start + 1
            )

            all_materials.extend(batch_materials)

        # Merge and deduplicate materials
        merged_materials = _merge_duplicate_materials(all_materials)

        logger.info(f"Extraction complete. Found {len(merged_materials)} unique materials.")
        return merged_materials

    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return []


def _extract_batch_content(
    reader: PdfReader,
    start: int,
    end: int
) -> Tuple[str, List[bytes]]:
    """Extract text and images from a batch of pages"""
    text = ""
    images = []

    for i in range(start, end):
        page = reader.pages[i]

        # Extract text
        page_text = page.extract_text()
        if page_text:
            text += f"\n--- Page {i + 1} ---\n{page_text}"

        # Extract images (limit per page to avoid memory issues)
        try:
            for j, image_obj in enumerate(page.images):
                if j >= 3:  # Max 3 images per page
                    break
                images.append(image_obj.data)
        except Exception as e:
            logger.debug(f"Could not extract images from page {i + 1}: {e}")

    return text.strip(), images


def _process_batch(
    client: OpenAI,
    text: str,
    images: List[bytes],
    batch_number: int
) -> List[Dict]:
    """Process a batch of content using appropriate extraction method"""

    # Decide: use vision if little text but images available
    use_vision = len(text) < 100 and len(images) > 0

    if use_vision:
        return _extract_with_vision(client, images, batch_number)
    elif text:
        return _extract_with_text(client, text, batch_number)
    else:
        logger.warning(f"Batch {batch_number}: No content to process")
        return []


def _extract_with_vision(
    client: OpenAI,
    images: List[bytes],
    batch_number: int
) -> List[Dict]:
    """Extract materials using GPT-4 Vision"""
    logger.info(f"Batch {batch_number}: Using Vision API with {len(images)} images")

    try:
        content_payload = [
            {"type": "text", "text": EXTRACTION_PROMPT_VISION}
        ]

        # Add images (limit to 5 per request)
        for img_bytes in images[:5]:
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            content_payload.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                }
            })

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_VISION},
                {"role": "user", "content": content_payload}
            ],
            temperature=0.1,
            max_tokens=4000
        )

        return _parse_response(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Vision extraction failed: {e}")
        return []


def _extract_with_text(
    client: OpenAI,
    text: str,
    batch_number: int
) -> List[Dict]:
    """Extract materials from text using GPT-3.5/4"""
    logger.info(f"Batch {batch_number}: Using Text API with {len(text)} characters")

    try:
        # Use GPT-4 for better accuracy if text is complex
        model = "gpt-4o-mini" if len(text) < 2000 else "gpt-4o-mini"

        # Truncate very long text
        truncated_text = text[:8000] if len(text) > 8000 else text

        prompt = EXTRACTION_PROMPT_TEXT.format(text=truncated_text)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_TEXT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )

        return _parse_response(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return []


def _parse_response(content: str) -> List[Dict]:
    """Parse OpenAI response and extract JSON materials list"""
    logger.debug(f"Parsing response: {content[:500]}...")

    try:
        # Try to find JSON block if wrapped in markdown
        json_match = re.search(r"```json\s*(.*?)```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find array brackets
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content

        materials = json.loads(json_str)

        # Validate and clean materials
        validated = []
        for mat in materials:
            if _validate_material(mat):
                validated.append(_clean_material(mat))

        return validated

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.debug(f"Failed content: {content}")
        return []


def _validate_material(mat: Dict) -> bool:
    """Validate that material has required fields"""
    required = ['material_name', 'quantity', 'unit']
    return all(key in mat for key in required)


def _clean_material(mat: Dict) -> Dict:
    """Clean and standardize material data"""
    return {
        'material_name': str(mat.get('material_name', '')).strip(),
        'material_name_he': str(mat.get('material_name_he', '')).strip() if mat.get('material_name_he') else None,
        'quantity': float(mat.get('quantity', 0)),
        'unit': str(mat.get('unit', '')).strip().lower(),
        'confidence_score': min(1.0, max(0.0, float(mat.get('confidence_score', 0.7)))),
        'category': str(mat.get('category', 'other')).strip().lower(),
        'notes': str(mat.get('notes', '')).strip() if mat.get('notes') else None
    }


def _merge_duplicate_materials(materials: List[Dict]) -> List[Dict]:
    """Merge duplicate materials by summing quantities"""
    merged = {}

    for mat in materials:
        # Create key from name and unit
        key = (
            mat['material_name'].lower(),
            mat['unit'].lower()
        )

        if key in merged:
            # Sum quantities
            merged[key]['quantity'] += mat['quantity']
            # Average confidence scores
            merged[key]['confidence_score'] = (
                merged[key]['confidence_score'] + mat['confidence_score']
            ) / 2
            # Append notes if different
            if mat.get('notes') and mat['notes'] not in (merged[key].get('notes') or ''):
                existing_notes = merged[key].get('notes') or ''
                merged[key]['notes'] = f"{existing_notes}; {mat['notes']}" if existing_notes else mat['notes']
        else:
            merged[key] = mat.copy()

    return list(merged.values())
