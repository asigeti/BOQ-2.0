"""
Smart Layer Categorization Service
Automatically groups DWG layers by purpose to help users make informed selections.
"""
import re
from typing import Dict, List, Tuple
from enum import Enum


class LayerGroup(str, Enum):
    """Layer group categories"""
    BUILDING = "building"  # Walls, rooms, floors - INCLUDE by default
    STRUCTURAL = "structural"  # Foundations, columns - REVIEW
    SITE_BOUNDARY = "site_boundary"  # Property lines, setbacks - EXCLUDE
    INFRASTRUCTURE = "infrastructure"  # Roads, parking - EXCLUDE
    LANDSCAPE = "landscape"  # Gardens, planting - EXCLUDE
    UTILITIES = "utilities"  # MEP systems - REVIEW
    ANNOTATIONS = "annotations"  # Text, dims, xrefs - EXCLUDE
    UNKNOWN = "unknown"  # Unclassified - REVIEW


# Hebrew/English keywords for each group
LAYER_PATTERNS = {
    LayerGroup.BUILDING: [
        # Hebrew
        r"חדר", r"קיר", r"קירות", r"רצפה", r"תקרה", r"דלת", r"חלון",
        r"פנים", r"ממ[דמ]", r"ממ\"ד",
        # English
        r"room", r"wall", r"floor", r"ceiling", r"door", r"window",
        r"interior", r"apartment", r"unit", r"space",
        # Common codes
        r"^[aA]-", r"^arch", r"^1[0-9]{3}$",  # A-WALL, ARCH-, 1602 etc
    ],

    LayerGroup.STRUCTURAL: [
        r"יסוד", r"עמוד", r"קורה", r"תקרה", r"בטון", r"זיון",
        r"foundation", r"column", r"beam", r"slab", r"concrete", r"rebar",
        r"^[sS]-", r"^str", r"^m[0-9]{4}$",  # S-BEAM, STR-, M1200
    ],

    LayerGroup.SITE_BOUNDARY: [
        r"קו.*מגרש", r"קו.*בניין", r"קו.*בינוי", r"גבול", r"תחום",
        r"kav[-_]?migrash", r"kav[-_]?bin", r"boundary", r"property",
        r"setback", r"strip[-_]?\d+", r"^strip", r"^border", r"^site[-_]?line",
    ],

    LayerGroup.INFRASTRUCTURE: [
        r"כביש", r"דרך", r"חניה", r"מדרכה", r"שביל",
        r"road", r"street", r"parking", r"driveway", r"pavement",
        r"sidewalk", r"path", r"curb", r"paving",
        r"^[cC]-", r"^civil", r"^infra",
    ],

    LayerGroup.LANDSCAPE: [
        r"גינון", r"נטיעה", r"דשא", r"צמחיה", r"השקיה",
        r"landscape", r"garden", r"planting", r"lawn", r"grass",
        r"irrigation", r"tree", r"shrub", r"green",
        r"^[lL]-", r"^land", r"^plant", r"ginun", r"pituah",
    ],

    LayerGroup.UTILITIES: [
        r"אינסטלציה", r"חשמל", r"מיזוג", r"תקשורת", r"ניקוז",
        r"plumbing", r"electrical", r"hvac", r"mep", r"drainage",
        r"pipe", r"duct", r"cable", r"ac", r"water", r"sewer",
        r"^[eEpPmM]-", r"^elec", r"^mech",
    ],

    LayerGroup.ANNOTATIONS: [
        r"טקסט", r"מידות", r"ביאור", r"סימון", r"כותרת",
        r"text", r"dim", r"note", r"label", r"title", r"legend",
        r"hatch", r"pattern", r"symbol", r"tag", r"anno",
        r"^xref", r"^\|", r"^defpoints", r"^vp", r"viewport",
        r"^0$",  # Layer "0" is often annotations/blocks
    ],
}


def categorize_layer(
    layer_name: str,
    area_m2: float,
    polyline_count: int,
    from_xref: bool = False
) -> Tuple[LayerGroup, float]:
    """
    Categorize a layer based on name, area, and characteristics.

    Returns:
        Tuple[LayerGroup, confidence]: Category and confidence score (0-1)
    """
    layer_lower = layer_name.lower()

    # Rule 1: XREFs and external references -> ANNOTATIONS
    if from_xref or "|" in layer_name or layer_name.startswith("xref"):
        return LayerGroup.ANNOTATIONS, 0.95

    # Rule 2: Extremely large areas (>10,000 m²) -> likely SITE_BOUNDARY
    if area_m2 > 10000:
        return LayerGroup.SITE_BOUNDARY, 0.90

    # Rule 3: Pattern matching with confidence scoring
    scores = {}
    
    # BLACKLIST: Explicitly reject annotation layers even if they contain valid keywords
    # e.g. "S-COLUMN-TEXT" should NOT be structural.
    BLACKLIST_KEYWORDS = [
        "TEXT", "DIM", "DIMENSION", "NOTE", "TAG", "LABEL", "LEGEND", 
        "TITLE", "SHEET", "GRID", "AXIS", "HATCH", "PATTERN", "SYMB"
    ]
    
    is_blacklisted = False
    for bad_word in BLACKLIST_KEYWORDS:
        if bad_word in layer_name.upper():
            # If it's a blacklist word, we force it to ANNOTATIONS or ignore
            # But let's just penalize other scores or return ANNO immediately?
            # User wants to "drop" them or categorize as NON-structural.
            # Best is to return ANNOTATIONS with high confidence.
            return LayerGroup.ANNOTATIONS, 0.99

    for group, patterns in LAYER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, layer_lower, re.IGNORECASE):
                scores[group] = scores.get(group, 0) + 0.3

    # Get best match
    if scores:
        best_group = max(scores, key=scores.get)
        confidence = min(scores[best_group], 1.0)
        return best_group, confidence

    # Rule 4: Area-based heuristics for unknown layers
    if area_m2 > 5000:
        return LayerGroup.SITE_BOUNDARY, 0.60
    elif area_m2 > 1000:
        return LayerGroup.INFRASTRUCTURE, 0.50
    elif area_m2 < 10 and polyline_count > 20:
        return LayerGroup.ANNOTATIONS, 0.60

    # Default: Unknown (requires review)
    return LayerGroup.UNKNOWN, 0.30


def get_group_metadata(group: LayerGroup) -> Dict:
    """Get display metadata for a layer group"""
    metadata = {
        LayerGroup.BUILDING: {
            "name_he": "אלמנטים מבנה",
            "name_en": "Building Elements",
            "icon": "📦",
            "default_selected": True,
            "description_he": "קירות, חדרים, רצפות - חלק מהמבנה",
            "description_en": "Walls, rooms, floors - part of the building",
            "color": "#4CAF50",  # Green
        },
        LayerGroup.STRUCTURAL: {
            "name_he": "מבנה קונסטרוקטיבי",
            "name_en": "Structural",
            "icon": "🏗️",
            "default_selected": True,
            "description_he": "יסודות, עמודים, קורות - בדוק בעיון",
            "description_en": "Foundations, columns, beams - review carefully",
            "color": "#FF9800",  # Orange
        },
        LayerGroup.SITE_BOUNDARY: {
            "name_he": "גבולות מגרש",
            "name_en": "Site Boundaries",
            "icon": "🚧",
            "default_selected": False,
            "description_he": "קווי מגרש, קווי בניין - לא כלול בכמויות",
            "description_en": "Property lines, building lines - exclude from quantities",
            "color": "#F44336",  # Red
        },
        LayerGroup.INFRASTRUCTURE: {
            "name_he": "תשתיות",
            "name_en": "Infrastructure",
            "icon": "🚗",
            "default_selected": False,
            "description_he": "כבישים, חניה, מדרכות - פיתוח חיצוני",
            "description_en": "Roads, parking, pathways - external development",
            "color": "#9E9E9E",  # Gray
        },
        LayerGroup.LANDSCAPE: {
            "name_he": "גינון ונוף",
            "name_en": "Landscape",
            "icon": "🌳",
            "default_selected": False,
            "description_he": "גינון, נטיעות, השקיה",
            "description_en": "Gardens, planting, irrigation",
            "color": "#8BC34A",  # Light green
        },
        LayerGroup.UTILITIES: {
            "name_he": "מערכות",
            "name_en": "Utilities",
            "icon": "🔧",
            "default_selected": True,
            "description_he": "אינסטלציה, חשמל, מיזוג - בדוק בעיון",
            "description_en": "Plumbing, electrical, HVAC - review carefully",
            "color": "#2196F3",  # Blue
        },
        LayerGroup.ANNOTATIONS: {
            "name_he": "הערות ותיאורים",
            "name_en": "Annotations",
            "icon": "📝",
            "default_selected": False,
            "description_he": "טקסט, מידות, הערות - לא כלול",
            "description_en": "Text, dimensions, notes - exclude",
            "color": "#607D8B",  # Blue gray
        },
        LayerGroup.UNKNOWN: {
            "name_he": "לא מזוהה",
            "name_en": "Unknown",
            "icon": "❓",
            "default_selected": False,
            "description_he": "שכבות לא מזוהות - דורש בדיקה",
            "description_en": "Unclassified layers - requires review",
            "color": "#9C27B0",  # Purple
        },
    }
    return metadata.get(group, {})


def validate_selection(layers: List[Dict], selected_layers: List[str]) -> Dict:
    """
    Validate user's layer selection and provide warnings.

    Args:
        layers: List of layer dicts with categorization
        selected_layers: List of selected layer names

    Returns:
        Dict with validation results and warnings
    """
    warnings = []
    total_area = 0
    building_area = 0
    site_boundary_area = 0

    for layer in layers:
        area = layer.get("area_m2", 0)
        name = layer.get("layer_name")
        group = layer.get("group")
        is_selected = name in selected_layers

        if is_selected:
            total_area += area
            if group == LayerGroup.BUILDING:
                building_area += area
            elif group == LayerGroup.SITE_BOUNDARY:
                site_boundary_area += area

    # Warning 1: Site boundary included in selection
    if site_boundary_area > 0:
        warnings.append({
            "severity": "error",
            "message_en": f"Site boundary layers included ({site_boundary_area:,.0f} m²). This will inflate quantities!",
            "message_he": f"שכבות גבול מגרש כלולות ({site_boundary_area:,.0f} מ\"ר). זה יגדיל את הכמויות!",
            "suggestion_en": "Uncheck site boundary layers (property lines, building lines)",
            "suggestion_he": "בטל סימון שכבות גבול (קווי מגרש, קווי בניין)",
        })

    # Warning 2: Unrealistic building area (too large)
    if building_area > 5000:
        warnings.append({
            "severity": "warning",
            "message_en": f"Large building area detected ({building_area:,.0f} m²). Verify this is correct.",
            "message_he": f"שטח מבנה גדול מאוד ({building_area:,.0f} מ\"ר). אמת שזה נכון.",
            "suggestion_en": "Check if non-building layers are included",
            "suggestion_he": "בדוק אם שכבות שאינן מבנה כלולות",
        })

    # Warning 3: No building layers selected
    if building_area == 0 or not any(l.get("group") == LayerGroup.BUILDING and l.get("layer_name") in selected_layers for l in layers):
        warnings.append({
            "severity": "error",
            "message_en": "No building layers selected. BOQ will be empty!",
            "message_he": "לא נבחרו שכבות מבנה. כתב הכמויות יהיה ריק!",
            "suggestion_en": "Select at least one building layer (walls, rooms, floors)",
            "suggestion_he": "בחר לפחות שכבת מבנה אחת (קירות, חדרים, רצפות)",
        })

    # Warning 4: Area ratio check (building vs total)
    if total_area > 0:
        building_ratio = building_area / total_area
        if building_ratio < 0.3:
            warnings.append({
                "severity": "warning",
                "message_en": f"Building area is only {building_ratio*100:.0f}% of total. Most area is non-building.",
                "message_he": f"שטח המבנה הוא רק {building_ratio*100:.0f}% מהסך. רוב השטח אינו מבנה.",
                "suggestion_en": "Review selection - infrastructure/landscape may be included",
                "suggestion_he": "בדוק את הבחירה - ייתכן שתשתיות/גינון כלולים",
            })

    return {
        "valid": len([w for w in warnings if w["severity"] == "error"]) == 0,
        "warnings": warnings,
        "total_area_m2": round(total_area, 2),
        "building_area_m2": round(building_area, 2),
        "site_boundary_area_m2": round(site_boundary_area, 2),
    }
