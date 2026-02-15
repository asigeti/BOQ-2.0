"""
DXF Extractor for ConstructionAI Pro

Comprehensive extraction of material quantities from DXF files using ezdxf.
Parses all entity types: blocks, text, geometry, dimensions, hatches.
Classifies blocks by name pattern and scans text for material keywords.
"""

import ezdxf
import math
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Material patterns in block names (shared with dwg_extractor)
MATERIAL_PATTERNS = {
    'DOOR': ('Doors', 'units'),
    'WINDOW': ('Windows', 'units'),
    'COLUMN': ('Columns', 'units'),
    'BEAM': ('Beams', 'units'),
    'PIPE': ('Piping', 'units'),
    'VALVE': ('Valves', 'units'),
    'PUMP': ('Pumps', 'units'),
    'FIXTURE': ('Fixtures', 'units'),
    'LIGHT': ('Light Fixtures', 'units'),
    'OUTLET': ('Electrical Outlets', 'units'),
    'SWITCH': ('Switches', 'units'),
    'SINK': ('Sinks', 'units'),
    'TOILET': ('Toilets', 'units'),
    'HVAC': ('HVAC Units', 'units'),
    'STAIR': ('Stairs', 'units'),
    'ELEVATOR': ('Elevators', 'units'),
    'WALL': ('Walls', 'units'),
    'SLAB': ('Slabs', 'units'),
    'FOUNDATION': ('Foundations', 'units'),
}

# Construction material keywords (English and Hebrew)
MATERIAL_KEYWORDS = {
    # English
    'concrete': 'Concrete',
    'steel': 'Steel',
    'rebar': 'Rebar/Reinforcement',
    'brick': 'Bricks',
    'block': 'Concrete Blocks',
    'drywall': 'Drywall/Gypsum Board',
    'plywood': 'Plywood',
    'lumber': 'Lumber',
    'insulation': 'Insulation',
    'paint': 'Paint',
    'tile': 'Tiles',
    'glass': 'Glass',
    'aluminum': 'Aluminum',
    'copper': 'Copper',
    'pvc': 'PVC Pipes',
    'ceramic': 'Ceramic',
    'marble': 'Marble',
    'granite': 'Granite',
    'waterproof': 'Waterproofing',
    # Hebrew
    'בטון': 'Concrete (בטון)',
    'ברזל': 'Steel/Iron (ברזל)',
    'בלוקים': 'Blocks (בלוקים)',
    'טיח': 'Plaster (טיח)',
    'ריצוף': 'Flooring (ריצוף)',
    'צבע': 'Paint (צבע)',
    'אלומיניום': 'Aluminum (אלומיניום)',
    'גבס': 'Gypsum (גבס)',
    'קרמיקה': 'Ceramic (קרמיקה)',
    'שיש': 'Marble (שיש)',
    'איטום': 'Waterproofing (איטום)',
    'עץ': 'Wood (עץ)',
    'זכוכית': 'Glass (זכוכית)',
    'פלדה': 'Steel (פלדה)',
}

QUANTITY_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*'
    r'(m[²³2³]|sqm|cum|m|mm|cm|kg|ton|units?|pcs?|יח\'?|מ"ר|מ"ק|ק"ג|טון)',
    re.IGNORECASE
)


def extract_from_dxf(file_path: str) -> List[Dict]:
    """
    Extract material quantities from a DXF file.

    Parses all entity types and classifies them into construction materials.
    Returns a list of material dicts with name, quantity, unit, confidence_score.
    """
    try:
        doc = ezdxf.readfile(file_path)
    except Exception as e:
        logger.error(f"Failed to read DXF file {file_path}: {e}")
        return []

    msp = doc.modelspace()

    stats = {
        'blocks': {},           # block_name -> count
        'block_attributes': [], # list of {block, tag, value}
        'text_items': [],       # list of {type, layer, value}
        'layers': {},           # layer_name -> entity count
        'total_length': 0.0,
        'total_area': 0.0,
        'dimension_values': [], # list of floats
        'circle_count': 0,
        'hatch_count': 0,
        'ellipse_count': 0,
        'polyline_count': 0,
    }

    for entity in msp:
        entity_type = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else "0"

        # Layer tracking
        stats['layers'][layer] = stats['layers'].get(layer, 0) + 1

        try:
            if entity_type == "INSERT":
                _process_insert(entity, stats)
            elif entity_type in ("TEXT", "MTEXT"):
                _process_text(entity, entity_type, layer, stats)
            elif entity_type == "LINE":
                _process_line(entity, stats)
            elif entity_type in ("LWPOLYLINE", "POLYLINE"):
                _process_polyline(entity, stats)
            elif entity_type == "CIRCLE":
                _process_circle(entity, stats)
            elif entity_type == "ELLIPSE":
                _process_ellipse(entity, stats)
            elif entity_type == "HATCH":
                _process_hatch(entity, stats)
            elif entity_type == "DIMENSION":
                _process_dimension(entity, stats)
            elif entity_type == "ARC":
                _process_arc(entity, stats)
        except Exception as e:
            logger.debug(f"Error processing {entity_type} entity on layer {layer}: {e}")

    materials = _stats_to_materials(stats)

    logger.info(
        f"DXF extraction: {len(materials)} materials from "
        f"{sum(stats['layers'].values())} entities across "
        f"{len(stats['layers'])} layers"
    )

    return materials


# --- Entity processors ---

def _process_insert(entity, stats: Dict):
    """Process INSERT (block reference) entity"""
    block_name = entity.dxf.name
    stats['blocks'][block_name] = stats['blocks'].get(block_name, 0) + 1

    # Extract block attributes
    if hasattr(entity, 'attribs'):
        for attrib in entity.attribs:
            try:
                tag = attrib.dxf.tag
                value = attrib.dxf.text
                if value:
                    stats['block_attributes'].append({
                        'block': block_name,
                        'tag': tag,
                        'value': value,
                    })
                    stats['text_items'].append({
                        'type': 'block_attribute',
                        'block': block_name,
                        'layer': entity.dxf.layer if hasattr(entity.dxf, 'layer') else "0",
                        'value': value,
                    })
            except Exception:
                pass


def _process_text(entity, entity_type: str, layer: str, stats: Dict):
    """Process TEXT or MTEXT entity"""
    try:
        if entity_type == "TEXT":
            text_value = entity.dxf.text
        else:
            text_value = entity.text
        if text_value and text_value.strip():
            stats['text_items'].append({
                'type': 'text',
                'layer': layer,
                'value': text_value.strip(),
            })
    except Exception:
        pass


def _process_line(entity, stats: Dict):
    """Process LINE entity - add to total length"""
    start = entity.dxf.start
    end = entity.dxf.end
    length = math.sqrt(
        (end.x - start.x) ** 2 +
        (end.y - start.y) ** 2 +
        (end.z - start.z) ** 2
    )
    stats['total_length'] += length


def _process_polyline(entity, stats: Dict):
    """Process LWPOLYLINE or POLYLINE entity"""
    stats['polyline_count'] += 1
    try:
        length = entity.length if hasattr(entity, 'length') else 0
        stats['total_length'] += length
    except Exception:
        pass
    # Closed polylines contribute area
    try:
        if entity.closed and hasattr(entity, 'length'):
            # Approximate area for closed polylines
            # ezdxf doesn't expose .area on LWPOLYLINE directly,
            # but we can try the shoelace formula for 2D
            if entity.dxftype() == "LWPOLYLINE":
                points = list(entity.get_points(format='xy'))
                if len(points) >= 3:
                    area = _shoelace_area(points)
                    stats['total_area'] += area
    except Exception:
        pass


def _process_circle(entity, stats: Dict):
    """Process CIRCLE entity"""
    stats['circle_count'] += 1
    try:
        radius = entity.dxf.radius
        stats['total_area'] += math.pi * radius ** 2
    except Exception:
        pass


def _process_ellipse(entity, stats: Dict):
    """Process ELLIPSE entity"""
    stats['ellipse_count'] += 1
    try:
        # Ellipse area = pi * a * b
        major_axis = entity.dxf.major_axis
        ratio = entity.dxf.ratio
        a = math.sqrt(major_axis.x ** 2 + major_axis.y ** 2 + major_axis.z ** 2)
        b = a * ratio
        stats['total_area'] += math.pi * a * b
    except Exception:
        pass


def _process_hatch(entity, stats: Dict):
    """Process HATCH entity"""
    stats['hatch_count'] += 1
    try:
        # ezdxf Hatch entities have paths, try to get area
        for path in entity.paths:
            if hasattr(path, 'vertices') and len(path.vertices) >= 3:
                points = [(v[0], v[1]) for v in path.vertices]
                stats['total_area'] += abs(_shoelace_area(points))
    except Exception:
        pass


def _process_dimension(entity, stats: Dict):
    """Process DIMENSION entity - extract measurement values"""
    try:
        # Try to get actual measurement value
        if hasattr(entity.dxf, 'actual_measurement'):
            stats['dimension_values'].append(entity.dxf.actual_measurement)
        elif hasattr(entity.dxf, 'text') and entity.dxf.text:
            text = entity.dxf.text
            # Try to parse numeric value from dimension text
            match = re.search(r'(\d+(?:\.\d+)?)', text)
            if match:
                stats['dimension_values'].append(float(match.group(1)))
    except Exception:
        pass


def _process_arc(entity, stats: Dict):
    """Process ARC entity - add arc length"""
    try:
        radius = entity.dxf.radius
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        angle = end_angle - start_angle
        if angle < 0:
            angle += 2 * math.pi
        arc_length = radius * angle
        stats['total_length'] += arc_length
    except Exception:
        pass


# --- Conversion helpers ---

def _shoelace_area(points: list) -> float:
    """Calculate area of a polygon using the shoelace formula"""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0


def _stats_to_materials(stats: Dict) -> List[Dict]:
    """Convert collected statistics into material quantity list"""
    materials = []

    # --- Classify blocks by name pattern ---
    for block_name, count in stats['blocks'].items():
        block_upper = block_name.upper()
        matched = False

        for pattern, (material_name, unit) in MATERIAL_PATTERNS.items():
            if pattern in block_upper:
                existing = next((m for m in materials if m['material_name'] == material_name), None)
                if existing:
                    existing['quantity'] += count
                else:
                    materials.append({
                        'material_name': material_name,
                        'quantity': count,
                        'unit': unit,
                        'confidence_score': 0.90,
                        'source': 'dxf_blocks',
                    })
                matched = True
                break

        # Unmatched blocks with count > 1 as generic items
        if not matched and count > 1:
            materials.append({
                'material_name': f"Block: {block_name}",
                'quantity': count,
                'unit': 'units',
                'confidence_score': 0.80,
                'source': 'dxf_blocks',
            })

    # --- Linear elements ---
    if stats['total_length'] > 0:
        materials.append({
            'material_name': 'Linear Elements (walls/pipes/conduit)',
            'quantity': round(stats['total_length'], 2),
            'unit': 'm',
            'confidence_score': 0.85,
            'source': 'dxf_geometry',
        })

    # --- Area elements ---
    if stats['total_area'] > 0:
        materials.append({
            'material_name': 'Area Elements (flooring/ceiling/hatches)',
            'quantity': round(stats['total_area'], 2),
            'unit': 'm²',
            'confidence_score': 0.85,
            'source': 'dxf_geometry',
        })

    # --- Dimension measurements ---
    if stats['dimension_values']:
        avg_dim = sum(stats['dimension_values']) / len(stats['dimension_values'])
        materials.append({
            'material_name': 'Dimension Measurements',
            'quantity': len(stats['dimension_values']),
            'unit': 'dimensions',
            'confidence_score': 0.75,
            'source': 'dxf_dimensions',
            'note': f"Avg value: {avg_dim:.2f}, range: {min(stats['dimension_values']):.2f}-{max(stats['dimension_values']):.2f}",
        })

    # --- Text-based material detection ---
    text_materials = _parse_text_for_materials(stats['text_items'])
    materials.extend(text_materials)

    # --- Layer-based fallback (if no other materials found) ---
    if not materials and stats['layers']:
        materials = _layer_fallback(stats['layers'])

    return materials


def _parse_text_for_materials(text_items: List[Dict]) -> List[Dict]:
    """Scan text entities for material keywords and quantities"""
    materials = []
    found_materials = {}  # material_name -> {quantity, unit}

    for item in text_items:
        text = item.get('value', '')
        text_lower = text.lower()

        for keyword, material_name in MATERIAL_KEYWORDS.items():
            if keyword.lower() in text_lower:
                # Try to extract an explicit quantity
                match = QUANTITY_PATTERN.search(text)
                if match:
                    quantity = float(match.group(1))
                    unit = match.group(2)
                    key = material_name
                    if key in found_materials:
                        found_materials[key]['quantity'] += quantity
                    else:
                        found_materials[key] = {
                            'quantity': quantity,
                            'unit': unit,
                        }
                else:
                    # No quantity, just note the mention
                    key = material_name
                    if key not in found_materials:
                        found_materials[key] = {
                            'quantity': 1,
                            'unit': 'mention',
                        }

    for material_name, info in found_materials.items():
        confidence = 0.80 if info['unit'] != 'mention' else 0.50
        materials.append({
            'material_name': material_name,
            'quantity': info['quantity'],
            'unit': info['unit'],
            'confidence_score': confidence,
            'source': 'dxf_text',
        })

    return materials


def _layer_fallback(layers: Dict[str, int]) -> List[Dict]:
    """Generate materials from layer names as last-resort fallback"""
    materials = []
    for layer_name, count in sorted(layers.items(), key=lambda x: -x[1]):
        if count < 2:
            continue
        # Skip default/system layers
        if layer_name in ("0", "Defpoints", "DEFPOINTS"):
            continue
        materials.append({
            'material_name': f"Layer: {layer_name}",
            'quantity': count,
            'unit': 'entities',
            'confidence_score': 0.40,
            'source': 'dxf_layer_fallback',
        })
    return materials
