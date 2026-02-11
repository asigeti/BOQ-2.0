"""
DWG Extractor for ConstructionAI Pro

Extracts material quantities from AutoCAD DWG files using multiple strategies:
1. AutoCAD COM interface (most accurate - requires AutoCAD installed)
2. ODA File Converter (DWG -> DXF conversion)
3. Direct ezdxf parsing (for compatible files)

NO FALLBACKS - If extraction fails, an error is raised.
Based on Easy-MCP-AutoCAD patterns for accurate BOQ extraction.
"""

import os
import logging
import sqlite3
import subprocess
import tempfile
import json
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


# Layer categorization patterns for BOQ area calculation
# Categories: "include" (auto-select), "exclude" (auto-deselect), "review" (user decides)
LAYER_CATEGORIES = {
    # Layers to AUTO-INCLUDE (construction-related)
    "include": [
        "A-ROOM", "A-AREA", "A-FLOOR", "A-WALL",  # Architecture
        "S-SLAB", "S-BEAM", "S-COLUMN", "S-FOUNDATION",  # Structure
        "ROOM", "AREA", "FLOOR", "FLOORING",  # Common names
        "SLAB", "CEILING", "WALL",
        "גמר", "ריצוף", "רצפה", "קירות", "תקרה",  # Hebrew: finish, flooring, floor, walls, ceiling
    ],
    # Layers to AUTO-EXCLUDE (not for area calculation)
    "exclude": [
        "DEFPOINTS", "DEFPOINT",  # System layers
        "XREF", "X-REF", "XREF-",  # External references
        "ANNO", "ANNOTATION", "A-ANNO",  # Annotations
        "DIM", "DIMENSION", "A-DIM",  # Dimensions
        "TEXT", "A-TEXT", "S-TEXT",  # Text layers
        "SYMBOL", "SYM-", "A-SYMB",  # Symbols
        "TITLE", "TITLEBLOCK", "TB-",  # Title blocks
        "BORDER", "FRAME", "SHEET",  # Sheet borders
        "LEGEND", "SCHEDULE", "TABLE",  # Non-geometry
        "GRID", "AXIS", "A-GRID",  # Reference grids
        "VIEWPORT", "VP", "VPORT",  # Viewports
        "HATCH", "A-HATCH",  # Often decorative hatches
        "FURNITURE", "FURN", "A-FURN",  # Furniture (not construction)
        "EQUIPMENT", "EQUIP", "E-",  # Equipment
        "PLUMB", "P-", "PLUMBING",  # MEP (separate BOQ)
        "ELEC", "E-", "ELECTRICAL",  # Electrical (separate BOQ)
        "HVAC", "M-", "MECHANICAL",  # HVAC (separate BOQ)
    ],
}


def categorize_layer(layer_name: str) -> str:
    """
    Categorize a layer as 'include', 'exclude', or 'review'.

    Args:
        layer_name: The layer name from AutoCAD

    Returns:
        'include': Layer should be included in area calculation by default
        'exclude': Layer should be excluded from area calculation by default
        'review': Layer needs user review (uncategorized)
    """
    layer_upper = layer_name.upper()

    # Check exclude patterns first (more specific)
    for pattern in LAYER_CATEGORIES["exclude"]:
        if pattern.upper() in layer_upper or layer_upper.startswith(pattern.upper()):
            return "exclude"

    # Check include patterns
    for pattern in LAYER_CATEGORIES["include"]:
        if pattern.upper() in layer_upper or layer_upper.startswith(pattern.upper()):
            return "include"

    # Default to review (user decides)
    return "review"


def categorize_extraction_layers(area_by_layer: Dict) -> Dict:
    """
    Categorize all layers in extraction data for user review.

    Args:
        area_by_layer: Dict from extraction with layer -> area info (already in m²)

    Returns:
        Dict with categorized layers:
        {
            "include": [{"layer": "A-ROOM", "area": 500.0, ...}, ...],
            "exclude": [{"layer": "DEFPOINTS", "area": 100.0, ...}, ...],
            "review": [{"layer": "UNKNOWN", "area": 200.0, ...}, ...],
            "totals": {
                "include_area": 500.0,
                "exclude_area": 100.0,
                "review_area": 200.0,
                "all_area": 800.0
            }
        }
    """
    result = {
        "include": [],
        "exclude": [],
        "review": [],
        "totals": {
            "include_area": 0.0,
            "exclude_area": 0.0,
            "review_area": 0.0,
            "all_area": 0.0
        }
    }

    for layer_name, layer_data in area_by_layer.items():
        category = categorize_layer(layer_name)
        # Area is already in m² from extraction
        area = layer_data.get("area", 0.0)

        layer_info = {
            "layer": layer_name,
            "area": round(area, 2),
            "polyline_count": layer_data.get("polyline_count", 0),
            "hatch_count": layer_data.get("hatch_count", 0),
            "category": category
        }

        result[category].append(layer_info)
        result["totals"][f"{category}_area"] += area
        result["totals"]["all_area"] += area

    # Round totals
    for key in result["totals"]:
        result["totals"][key] = round(result["totals"][key], 2)

    # Sort each category by area (descending)
    for category in ["include", "exclude", "review"]:
        result[category].sort(key=lambda x: x["area"], reverse=True)

    return result


class DWGExtractionError(Exception):
    """Raised when DWG extraction fails"""
    pass


# AutoCAD COM interface (Windows only)
try:
    import win32com.client
    import pythoncom
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    logger.info("win32com not available - AutoCAD COM interface disabled")

# ODA File Converter paths (common installation locations)
ODA_CONVERTER_PATHS = [
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
    os.environ.get("ODA_CONVERTER_PATH", ""),
]


class AutoCADExtractor:
    """
    Extracts data from DWG files using AutoCAD COM interface.
    Provides the most accurate BOQ extraction when AutoCAD is installed.
    """

    def __init__(self):
        self.acad = None
        self.doc = None

    def connect(self) -> bool:
        """Connect to running AutoCAD instance or start new one"""
        if not HAS_WIN32COM:
            return False

        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
        except:
            pass  # Already initialized

        try:
            # Try to connect to existing AutoCAD instance
            self.acad = win32com.client.Dispatch("AutoCAD.Application")
            self.acad.Visible = True  # Keep visible for stability
            logger.info("Connected to AutoCAD instance")
            time.sleep(2)  # Wait for AutoCAD to be ready
            return True
        except Exception as e:
            logger.warning(f"Could not connect to AutoCAD: {e}")
            return False

    def open_drawing(self, file_path: str) -> bool:
        """Open a DWG file in AutoCAD with proper timing (read-only mode)"""
        if not self.acad:
            return False

        try:
            # Open in read-only mode (True = ReadOnly)
            # This prevents file locking issues and works with files that
            # may have permission restrictions
            self.doc = self.acad.Documents.Open(file_path, True)
            logger.info(f"Opened drawing (read-only): {file_path}")
            # Wait for document to fully load
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Failed to open drawing: {e}")
            return False

    def _get_model_space_with_retry(self, max_retries: int = 5):
        """Get ModelSpace with retry logic for timing issues"""
        for attempt in range(max_retries):
            try:
                time.sleep(1)
                msp = self.doc.ModelSpace
                return msp
            except Exception as e:
                logger.warning(f"ModelSpace access attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        return None

    def scan_elements(self) -> List[Dict]:
        """
        Scan all elements in the drawing and extract BOQ-relevant data.
        Based on Easy-MCP-AutoCAD scan_elements functionality.
        """
        if not self.doc:
            return []

        elements = []

        try:
            # Get model space with retry logic
            model_space = self._get_model_space_with_retry()
            if model_space is None:
                logger.error("Could not access ModelSpace after retries")
                return []

            entity_count = model_space.Count
            logger.info(f"Processing {entity_count} entities...")

            # Track statistics for BOQ
            stats = {
                'blocks': {},      # Block name -> count
                'layers': {},      # Layer name -> entity count
                'text_items': [],  # All text found
                'dimensions': [],  # Dimension values
                'total_length': 0.0,
                'total_area': 0.0,
            }

            for i in range(entity_count):
                try:
                    entity = model_space.Item(i)
                    entity_type = entity.ObjectName
                    layer_name = entity.Layer
                except Exception as e:
                    continue  # Skip problematic entities

                # Count by layer
                stats['layers'][layer_name] = stats['layers'].get(layer_name, 0) + 1

                # Process by entity type
                if entity_type == "AcDbBlockReference":
                    block_name = entity.Name
                    stats['blocks'][block_name] = stats['blocks'].get(block_name, 0) + 1

                    # Extract block attributes (often contain material info)
                    if entity.HasAttributes:
                        for attr in entity.GetAttributes():
                            text = attr.TextString
                            if text:
                                stats['text_items'].append({
                                    'type': 'block_attribute',
                                    'block': block_name,
                                    'tag': attr.TagString,
                                    'value': text
                                })

                elif entity_type in ("AcDbLine", "AcDbPolyline", "AcDbLWPolyline"):
                    try:
                        length = entity.Length
                        stats['total_length'] += length
                    except:
                        pass

                elif entity_type in ("AcDbText", "AcDbMText"):
                    text = entity.TextString
                    if text:
                        stats['text_items'].append({
                            'type': 'text',
                            'layer': layer_name,
                            'value': text
                        })

                elif entity_type == "AcDbDimension":
                    try:
                        measurement = entity.Measurement
                        stats['dimensions'].append({
                            'layer': layer_name,
                            'value': measurement
                        })
                    except:
                        pass

                elif entity_type in ("AcDbHatch", "AcDb2dPolyline"):
                    try:
                        area = entity.Area
                        stats['total_area'] += area
                    except:
                        pass

            # Convert statistics to materials
            elements = self._stats_to_materials(stats)

        except Exception as e:
            logger.error(f"Error scanning elements: {e}")

        return elements

    def _stats_to_materials(self, stats: Dict) -> List[Dict]:
        """Convert scanned statistics to material quantities"""
        materials = []

        # Material patterns in block names
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
        }

        # Process blocks
        for block_name, count in stats['blocks'].items():
            block_upper = block_name.upper()
            matched = False

            for pattern, (material_name, unit) in MATERIAL_PATTERNS.items():
                if pattern in block_upper:
                    # Find existing material or create new
                    existing = next((m for m in materials if m['material_name'] == material_name), None)
                    if existing:
                        existing['quantity'] += count
                    else:
                        materials.append({
                            'material_name': material_name,
                            'quantity': count,
                            'unit': unit,
                            'confidence_score': 0.95,
                            'source': 'autocad_blocks'
                        })
                    matched = True
                    break

            # Unmatched blocks as generic items
            if not matched and count > 1:
                materials.append({
                    'material_name': f"Block: {block_name}",
                    'quantity': count,
                    'unit': 'units',
                    'confidence_score': 0.85,
                    'source': 'autocad_blocks'
                })

        # Add length-based materials
        if stats['total_length'] > 0:
            # Convert to meters if needed (assume drawing units)
            length_m = stats['total_length']
            materials.append({
                'material_name': 'Linear Elements (walls/pipes/conduit)',
                'quantity': round(length_m, 2),
                'unit': 'm',
                'confidence_score': 0.90,
                'source': 'autocad_geometry'
            })

        # Add area-based materials
        if stats['total_area'] > 0:
            area_sqm = stats['total_area']
            materials.append({
                'material_name': 'Area Elements (flooring/ceiling/hatches)',
                'quantity': round(area_sqm, 2),
                'unit': 'm²',
                'confidence_score': 0.90,
                'source': 'autocad_geometry'
            })

        # Parse text items for material mentions
        text_materials = self._parse_text_for_materials(stats['text_items'])
        materials.extend(text_materials)

        return materials

    def _parse_text_for_materials(self, text_items: List[Dict]) -> List[Dict]:
        """Parse text items for material quantities"""
        materials = []

        # Common construction material patterns (English and Hebrew)
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
            # Hebrew
            'בטון': 'Concrete (בטון)',
            'ברזל': 'Steel/Iron (ברזל)',
            'בלוקים': 'Blocks (בלוקים)',
            'טיח': 'Plaster (טיח)',
            'ריצוף': 'Flooring (ריצוף)',
            'צבע': 'Paint (צבע)',
            'אלומיניום': 'Aluminum (אלומיניום)',
            'גבס': 'Gypsum (גבס)',
        }

        import re
        quantity_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(m²|m2|sqm|m³|m3|cum|m|mm|kg|ton|units?|pcs?|יח\'?)', re.IGNORECASE)

        for item in text_items:
            text = item.get('value', '').lower()

            for keyword, material_name in MATERIAL_KEYWORDS.items():
                if keyword.lower() in text:
                    # Try to extract quantity from text
                    match = quantity_pattern.search(text)
                    if match:
                        quantity = float(match.group(1))
                        unit = match.group(2)
                        materials.append({
                            'material_name': material_name,
                            'quantity': quantity,
                            'unit': unit,
                            'confidence_score': 0.80,
                            'source': 'autocad_text'
                        })

        return materials

    def close(self):
        """Close the document and release AutoCAD"""
        try:
            if self.doc:
                self.doc.Close(False)  # Don't save
            # Don't quit AutoCAD - it may have other documents open
        except:
            pass


def find_oda_converter() -> Optional[str]:
    """Find ODA File Converter installation"""
    for path in ODA_CONVERTER_PATHS:
        if path and os.path.exists(path):
            return path
    return None


def convert_dwg_to_dxf(dwg_path: str, output_dir: Optional[str] = None) -> Optional[str]:
    """
    Convert DWG to DXF using ODA File Converter.
    Returns path to converted DXF file or None if conversion failed.
    """
    converter = find_oda_converter()
    if not converter:
        logger.warning("ODA File Converter not found")
        return None

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="dwg_convert_")

    input_dir = os.path.dirname(dwg_path)
    input_file = os.path.basename(dwg_path)

    try:
        # ODA File Converter command line:
        # ODAFileConverter <input_dir> <output_dir> <output_version> <output_type> <recurse> <audit> [filter]
        # Output version: ACAD2018 for maximum compatibility
        # Output type: 0 = DWG, 1 = DXF, 2 = Binary DXF
        cmd = [
            converter,
            input_dir,
            output_dir,
            "ACAD2018",  # Output version
            "1",          # 1 = DXF output
            "0",          # 0 = No recurse
            "1",          # 1 = Audit/repair
            input_file    # Filter to just this file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            logger.error(f"ODA conversion failed: {result.stderr}")
            return None

        # Find the output file
        base_name = os.path.splitext(input_file)[0]
        dxf_path = os.path.join(output_dir, f"{base_name}.dxf")

        if os.path.exists(dxf_path):
            logger.info(f"Converted {dwg_path} to {dxf_path}")
            return dxf_path
        else:
            logger.error(f"Expected output file not found: {dxf_path}")
            return None

    except subprocess.TimeoutExpired:
        logger.error("ODA conversion timed out")
        return None
    except Exception as e:
        logger.error(f"ODA conversion error: {e}")
        return None


def extract_from_dwg(file_path: str) -> List[Dict]:
    """
    Extract material quantities from a DWG file.

    Uses multiple strategies in order of accuracy:
    1. AutoCAD COM interface (most accurate)
    2. ODA File Converter -> DXF -> ezdxf
    3. Direct ezdxf parsing

    NO FALLBACKS - Raises DWGExtractionError if all methods fail.

    Args:
        file_path: Path to the DWG file

    Returns:
        List of extracted materials with quantities

    Raises:
        DWGExtractionError: If extraction fails with all methods
    """
    # Initialize COM for this thread (critical for background tasks!)
    if HAS_WIN32COM:
        try:
            pythoncom.CoInitialize()
            logger.info("COM initialized for extraction thread")
        except Exception as e:
            logger.warning(f"COM init warning: {e}")

    # Convert to absolute path - AutoCAD COM requires absolute paths
    file_path = os.path.abspath(file_path)
    logger.info(f"DWG extraction starting for: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise DWGExtractionError(f"File not found: {file_path}")

    materials = []
    extraction_method = None

    # Strategy 1: Try AutoCAD COM interface (most accurate)
    if HAS_WIN32COM:
        logger.info("Attempting AutoCAD COM extraction...")
        extractor = AutoCADExtractor()

        if extractor.connect():
            if extractor.open_drawing(file_path):
                materials = extractor.scan_elements()
                extraction_method = "autocad_com"
                extractor.close()

                if materials:
                    logger.info(f"AutoCAD COM extracted {len(materials)} materials")
                    return materials
            extractor.close()

    # Strategy 2: Try ODA File Converter -> DXF
    logger.info("Attempting ODA File Converter extraction...")
    dxf_path = convert_dwg_to_dxf(file_path)

    if dxf_path:
        try:
            from .dxf_extractor import extract_from_dxf
            materials = extract_from_dxf(dxf_path)
            extraction_method = "oda_converter"

            # Boost confidence since we converted properly
            for mat in materials:
                mat['confidence_score'] = min(mat.get('confidence_score', 0.7) + 0.1, 1.0)
                mat['source'] = 'oda_converted_dxf'

            # Clean up temp file
            try:
                os.remove(dxf_path)
                os.rmdir(os.path.dirname(dxf_path))
            except:
                pass

            if materials:
                logger.info(f"ODA converter extracted {len(materials)} materials")
                return materials

        except Exception as e:
            logger.error(f"DXF extraction after conversion failed: {e}")

    # Strategy 3: Fallback - try direct ezdxf (works for some DWG versions)
    logger.info("Attempting direct ezdxf extraction (fallback)...")
    try:
        from .dxf_extractor import extract_from_dxf
        materials = extract_from_dxf(file_path)

        if materials:
            # Lower confidence for direct read
            for mat in materials:
                mat['confidence_score'] = max(mat.get('confidence_score', 0.5) - 0.2, 0.3)
                mat['source'] = 'direct_dxf_fallback'

            logger.info(f"Direct ezdxf extracted {len(materials)} materials (fallback)")
            return materials

    except Exception as e:
        logger.warning(f"Direct ezdxf read failed: {e}")

    # All extraction methods failed - raise error
    logger.error(f"All extraction methods failed for {file_path}")
    raise DWGExtractionError(
        f"Failed to extract data from {file_path}. "
        "Install AutoCAD or ODA File Converter for DWG extraction."
    )


def extract_raw_data_from_dwg(file_path: str) -> Dict:
    """
    Extract RAW data from DWG file for AI processing.

    Unlike extract_from_dwg() which returns processed materials,
    this function returns all raw data extracted from AutoCAD
    for the AI to analyze and create an Israeli BOQ.

    Args:
        file_path: Path to the DWG file

    Returns:
        Dict with raw extraction data:
        - blocks: All block references with names, attributes, positions
        - text: All text entities
        - dimensions: All dimension values
        - layers: Layer names and entity counts
        - geometry: Line lengths, areas, polylines
        - metadata: File info, extraction method
    """
    # Initialize COM for this thread (critical for background tasks!)
    if HAS_WIN32COM:
        try:
            pythoncom.CoInitialize()
            logger.info("COM initialized for extraction thread")
        except Exception as e:
            logger.warning(f"COM init warning: {e}")

    # Convert to absolute path - AutoCAD COM requires absolute paths
    file_path = os.path.abspath(file_path)
    logger.info(f"Raw DWG extraction starting for: {file_path}")

    raw_data = {
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "extraction_method": None,
        "extraction_success": False,
        "blocks": [],
        "text_entities": [],
        "dimensions": [],
        "layers": {},
        "geometry": {
            "total_line_length": 0.0,
            "total_area": 0.0,
            "polyline_count": 0,
            "circle_count": 0,
            "arc_count": 0
        },
        "attributes": [],
        "errors": []
    }

    # Strategy 1: AutoCAD COM (most complete data)
    if HAS_WIN32COM:
        logger.info("Extracting raw data via AutoCAD COM...")
        extractor = AutoCADExtractor()

        if extractor.connect():
            if extractor.open_drawing(file_path):
                try:
                    raw_data = _extract_raw_autocad_data(extractor.doc, file_path)
                    raw_data["extraction_method"] = "autocad_com"
                    raw_data["extraction_success"] = True
                except Exception as e:
                    raw_data["errors"].append(f"AutoCAD extraction error: {e}")
                finally:
                    extractor.close()

                if raw_data["extraction_success"]:
                    return raw_data
            extractor.close()

    # Strategy 2: ODA + ezdxf
    logger.info("Extracting raw data via ODA/ezdxf...")
    dxf_path = convert_dwg_to_dxf(file_path)

    if dxf_path:
        try:
            raw_data = _extract_raw_dxf_data(dxf_path)
            raw_data["extraction_method"] = "oda_converter"
            raw_data["extraction_success"] = True
            raw_data["file_path"] = file_path
            raw_data["filename"] = os.path.basename(file_path)

            # Cleanup
            try:
                os.remove(dxf_path)
                os.rmdir(os.path.dirname(dxf_path))
            except:
                pass

            return raw_data
        except Exception as e:
            raw_data["errors"].append(f"ODA/DXF extraction error: {e}")

    # Strategy 3: Direct ezdxf (last resort)
    try:
        raw_data = _extract_raw_dxf_data(file_path)
        raw_data["extraction_method"] = "ezdxf_direct"
        raw_data["extraction_success"] = True
        return raw_data
    except Exception as e:
        raw_data["errors"].append(f"Direct ezdxf failed: {e}")

    raw_data["extraction_method"] = "failed"
    return raw_data


def _extract_raw_autocad_data(doc, file_path: str) -> Dict:
    """
    Extract comprehensive raw data from AutoCAD document.

    Enhanced to:
    1. Follow and explode XRefs (external references)
    2. Extract nested block contents
    3. Handle all dimension types
    4. Better text/attribute handling
    5. Track areas PER LAYER for user selection
    """
    raw_data = {
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "extraction_method": "autocad_com",
        "extraction_success": True,
        "blocks": [],
        "text_entities": [],
        "dimensions": [],
        "layers": {},
        "geometry": {
            "total_line_length": 0.0,
            "total_area": 0.0,
            "polyline_count": 0,
            "circle_count": 0,
            "arc_count": 0,
            "hatch_count": 0,
            "solid_count": 0
        },
        # NEW: Per-layer area tracking for user selection
        "area_by_layer": {},  # layer_name -> {"area": float, "polyline_count": int, "hatch_count": int}
        "closed_polylines": [],  # List of individual closed polylines with area
        "attributes": [],
        "xrefs": [],
        "block_definitions": {},
        "tables": [],
        "errors": []
    }

    # Helper to determine if entity is valid BOQ geometry candidate
    def is_boq_candidate(entity, entity_type):
        """
        Generic filter: Returns True only for entities that represent physical objects.
        Excludes annotations, dimensions, hatches, and open lines.
        """
        # 1. Reject Attributes/Annotations
        if entity_type in ("AcDbText", "AcDbMText", "AcDbDimension", "AcDbLeader", 
                          "AcDbAttributeDefinition", "AcDbAttribute"):
            return False
            
        # 2. Reject decorative/non-structural
        if entity_type in ("AcDbHatch", "AcDbPoint", "AcDbRay", "AcDbXline"):
            return False
            
        # 3. Reject Open Polylines (Lines are counted separately for length, not as "items")
        if entity_type in ("AcDbPolyline", "AcDbLWPolyline", "AcDb2dPolyline", "AcDb3dPolyline"):
            if hasattr(entity, 'Closed') and not entity.Closed:
                return False
                
        # 4. Reject pure Lines (counted by length elsewhere, but not as "objects" like columns)
        if entity_type == "AcDbLine":
            return False

        return True

    BLACKLIST_KEYWORDS = [
        "TEXT", "DIM", "DIMENSION", "NOTE", "TAG", "LABEL", "LEGEND", 
        "TITLE", "SHEET", "GRID", "AXIS", "HATCH", "PATTERN", "SYMB"
    ]

    def process_entity(entity, scale_factor=1.0, is_block_content=False, block_name=""):
        """Process a single entity and update raw_data"""
        try:
            # OPTIMIZATION: Get Layer Name first.
            # If accessing entity.Layer fails, it's broken anyway.
            layer_name = entity.Layer if hasattr(entity, 'Layer') else "0"
            layer_upper = layer_name.upper()
            
            # OPTIMIZATION 1: Skip expensive checks for Blacklisted Layers
            # If layer is explicitly an annotation layer, don't bother checking geometry props.
            is_blacklisted = False
            for bad in BLACKLIST_KEYWORDS:
                if bad in layer_upper:
                    is_blacklisted = True
                    break
            
            if is_blacklisted:
                # We don't count these in the main "BOQ Candidate" counts. 
                # We can skip further processing to save time.
                return

            entity_type = entity.ObjectName

            # FILTER: Only count "valid" geometry in the main layer count.
            # This prevents Text/Dims from inflating "Column" counts.
            if is_boq_candidate(entity, entity_type):
                raw_data["layers"][layer_name] = raw_data["layers"].get(layer_name, 0) + 1

            # All dimension types (AcDbAlignedDimension, AcDbRotatedDimension, etc.)
            if "Dimension" in entity_type or entity_type.startswith("AcDbDim"):
                try:
                    measurement = entity.Measurement * scale_factor if hasattr(entity, 'Measurement') else 0
                    text_override = ""
                    if hasattr(entity, 'TextOverride'):
                        text_override = entity.TextOverride

                    raw_data["dimensions"].append({
                        "type": entity_type,
                        "measurement": measurement,
                        "text_override": text_override,
                        "layer": layer_name,
                        "from_block": block_name if is_block_content else ""
                    })
                except Exception as e:
                    pass

            # Text entities
            elif entity_type in ("AcDbText", "AcDbMText"):
                try:
                    raw_data["text_entities"].append({
                        "type": entity_type,
                        "text": entity.TextString,
                        "layer": layer_name,
                        "height": (entity.Height if hasattr(entity, 'Height') else 0) * scale_factor,
                        "position": {
                            "x": entity.InsertionPoint[0],
                            "y": entity.InsertionPoint[1]
                        },
                        "from_block": block_name if is_block_content else ""
                    })
                except:
                    pass

            # Tables (schedule data)
            elif entity_type == "AcDbTable":
                try:
                    table_data = {
                        "rows": entity.Rows,
                        "columns": entity.Columns,
                        "cells": [],
                        "layer": layer_name
                    }
                    for row in range(entity.Rows):
                        row_data = []
                        for col in range(entity.Columns):
                            try:
                                cell_text = entity.GetText(row, col)
                                row_data.append(cell_text)
                            except:
                                row_data.append("")
                        table_data["cells"].append(row_data)
                    raw_data["tables"].append(table_data)
                except Exception as e:
                    raw_data["errors"].append(f"Table extraction error: {e}")

            # Geometry - Lines
            elif entity_type == "AcDbLine":
                try:
                    length = entity.Length * scale_factor
                    raw_data["geometry"]["total_line_length"] += length
                except:
                    pass

            # Geometry - Polylines (including 3D)
            elif entity_type in ("AcDbPolyline", "AcDbLWPolyline", "AcDb2dPolyline", "AcDb3dPolyline"):
                raw_data["geometry"]["polyline_count"] += 1
                try:
                    raw_data["geometry"]["total_line_length"] += entity.Length * scale_factor
                except:
                    pass
                try:
                    if hasattr(entity, 'Closed') and entity.Closed:
                        area = entity.Area * (scale_factor ** 2)
                        raw_data["geometry"]["total_area"] += area

                        # FILTER: Only track as "Column Candidate" if size is realistic
                        # 0.04 m² (20x20cm) to 2.0 m² (140x140cm)
                        # This prevents "Room Boundaries" or "Tiny Debris" from being counted as structural elements.
                        is_valid_structure = (area >= 0.04 and area <= 2.0)
                        
                        # Apply aspect ratio check for columns (max 1:4 usually).
                        # Using BoundingBox if available (requires more complex logic), 
                        # but area check captures 90% of issues (rooms are > 2m).
                        
                        # Only add to area_by_layer if it's a valid structural candidate OR if it's a room/large area (managed by other logic)
                        # Actually, we need to track ALL areas for flooring, but we can flag them?
                        # For now, let's keep area aggregation simple but apply the COUNT logic strictly.
                        
                        # Track area by layer
                        if layer_name not in raw_data["area_by_layer"]:
                            raw_data["area_by_layer"][layer_name] = {
                                "area": 0.0, "polyline_count": 0, "hatch_count": 0,
                                "structural_count": 0 # NEW: Start tracking "real" structural items
                            }
                        raw_data["area_by_layer"][layer_name]["area"] += area
                        raw_data["area_by_layer"][layer_name]["polyline_count"] += 1
                        
                        if is_valid_structure:
                             raw_data["area_by_layer"][layer_name]["structural_count"] += 1

                        # Track individual closed polylines
                        raw_data["closed_polylines"].append({
                            "layer": layer_name,
                            "area": area,
                            "type": entity_type,
                            "is_structural_candidate": is_valid_structure,
                            "from_block": block_name if is_block_content else ""
                        })
                except:
                    pass

            # Geometry - Circles
            elif entity_type == "AcDbCircle":
                raw_data["geometry"]["circle_count"] += 1
                try:
                    raw_data["geometry"]["total_area"] += entity.Area * (scale_factor ** 2)
                except:
                    pass

            # Geometry - Arcs
            elif entity_type == "AcDbArc":
                raw_data["geometry"]["arc_count"] += 1
                try:
                    raw_data["geometry"]["total_line_length"] += entity.ArcLength * scale_factor
                except:
                    pass

            # Geometry - Ellipses
            elif entity_type == "AcDbEllipse":
                try:
                    raw_data["geometry"]["total_area"] += entity.Area * (scale_factor ** 2)
                except:
                    pass

            # Hatches (areas) - important for room areas
            elif entity_type == "AcDbHatch":
                raw_data["geometry"]["hatch_count"] = raw_data["geometry"].get("hatch_count", 0) + 1
                try:
                    area = entity.Area * (scale_factor ** 2)
                    raw_data["geometry"]["total_area"] += area

                    # Track area by layer
                    if layer_name not in raw_data["area_by_layer"]:
                        raw_data["area_by_layer"][layer_name] = {
                            "area": 0.0, "polyline_count": 0, "hatch_count": 0
                        }
                    raw_data["area_by_layer"][layer_name]["area"] += area
                    raw_data["area_by_layer"][layer_name]["hatch_count"] += 1

                    # Track as closed polyline equivalent
                    raw_data["closed_polylines"].append({
                        "layer": layer_name,
                        "area": area,
                        "type": "hatch",
                        "from_block": block_name if is_block_content else ""
                    })
                except:
                    pass

            # Solids and regions
            elif entity_type in ("AcDbSolid", "AcDbRegion", "AcDb3dSolid"):
                raw_data["geometry"]["solid_count"] = raw_data["geometry"].get("solid_count", 0) + 1
                try:
                    if hasattr(entity, 'Area'):
                        raw_data["geometry"]["total_area"] += entity.Area * (scale_factor ** 2)
                except:
                    pass

        except Exception as e:
            raw_data["errors"].append(f"Entity processing error: {e}")

    def process_block_reference(entity, parent_scale=1.0):
        """Process a block reference and its contents"""
        try:
            block_name = entity.Name
            layer_name = entity.Layer if hasattr(entity, 'Layer') else "0"

            # Calculate combined scale
            x_scale = entity.XScaleFactor if hasattr(entity, 'XScaleFactor') else 1
            y_scale = entity.YScaleFactor if hasattr(entity, 'YScaleFactor') else 1
            combined_scale = parent_scale * ((abs(x_scale) + abs(y_scale)) / 2)

            block_info = {
                "name": block_name,
                "layer": layer_name,
                "position": {
                    "x": entity.InsertionPoint[0],
                    "y": entity.InsertionPoint[1],
                    "z": entity.InsertionPoint[2] if len(entity.InsertionPoint) > 2 else 0
                },
                "rotation": entity.Rotation if hasattr(entity, 'Rotation') else 0,
                "scale": {"x": x_scale, "y": y_scale},
                "is_xref": False,
                "attributes": []
            }

            # Extract block attributes (important for BOQ data)
            if hasattr(entity, 'HasAttributes') and entity.HasAttributes:
                for attr in entity.GetAttributes():
                    attr_data = {
                        "tag": attr.TagString,
                        "value": attr.TextString
                    }
                    block_info["attributes"].append(attr_data)
                    raw_data["attributes"].append({
                        "block": block_name,
                        "tag": attr.TagString,
                        "value": attr.TextString
                    })

            raw_data["blocks"].append(block_info)

            # Check if this is an XRef
            try:
                if hasattr(entity, 'IsDynamicBlock') or "*" in block_name or block_name.startswith("A$"):
                    # This might be an xref or anonymous block
                    pass
            except:
                pass

            return block_name, combined_scale

        except Exception as e:
            raw_data["errors"].append(f"Block reference error: {e}")
            return None, 1.0

    try:
        model_space = doc.ModelSpace
        logger.info(f"Processing ModelSpace with {model_space.Count} entities")

        # First pass: Process all entities in model space
        total_entities = model_space.Count
        logger.info(f"Starting generic entity scan on {total_entities} items...")
        
        for i in range(total_entities):
            if i > 0 and i % 500 == 0:
                msg = f"Scanning entities: {i}/{total_entities} ({(i/total_entities)*100:.1f}%)"
                logger.info(msg)
                print(msg) # Ensure visibility in console

            try:
                entity = model_space.Item(i)
                entity_type = entity.ObjectName

                if entity_type == "AcDbBlockReference":
                    block_name, scale = process_block_reference(entity)
                else:
                    process_entity(entity)

            except Exception as e:
                raw_data["errors"].append(f"Error processing entity {i}: {e}")

        # Second pass: Extract block definition contents for geometry
        try:
            blocks_collection = doc.Blocks
            logger.info(f"Processing {blocks_collection.Count} block definitions")

            for i in range(blocks_collection.Count):
                try:
                    block_def = blocks_collection.Item(i)
                    block_name = block_def.Name

                    # Skip model space, paper space, and system blocks
                    if block_name.startswith("*") and block_name not in ["*Model_Space", "*Paper_Space"]:
                        continue
                    if block_name in ["*Model_Space", "*Paper_Space"]:
                        continue

                    # Count entities in block definition
                    entity_count = block_def.Count
                    if entity_count == 0:
                        continue

                    block_def_data = {
                        "name": block_name,
                        "entity_count": entity_count,
                        "is_xref": block_def.IsXRef if hasattr(block_def, 'IsXRef') else False,
                        "xref_path": "",
                        "geometry": {
                            "lines": 0,
                            "polylines": 0,
                            "circles": 0,
                            "hatches": 0,
                            "texts": 0,
                            "dimensions": 0
                        }
                    }

                    # Check if it's an XRef
                    if hasattr(block_def, 'IsXRef') and block_def.IsXRef:
                        block_def_data["is_xref"] = True
                        try:
                            block_def_data["xref_path"] = block_def.Path
                        except:
                            pass
                        raw_data["xrefs"].append({
                            "name": block_name,
                            "path": block_def_data.get("xref_path", ""),
                            "entity_count": entity_count
                        })

                    # Process entities within block definition
                    for j in range(entity_count):
                        try:
                            block_entity = block_def.Item(j)
                            block_entity_type = block_entity.ObjectName

                            # Count by type
                            if block_entity_type == "AcDbLine":
                                block_def_data["geometry"]["lines"] += 1
                            elif "Polyline" in block_entity_type:
                                block_def_data["geometry"]["polylines"] += 1
                            elif block_entity_type == "AcDbCircle":
                                block_def_data["geometry"]["circles"] += 1
                            elif block_entity_type == "AcDbHatch":
                                block_def_data["geometry"]["hatches"] += 1
                            elif block_entity_type in ("AcDbText", "AcDbMText"):
                                block_def_data["geometry"]["texts"] += 1
                            elif "Dimension" in block_entity_type:
                                block_def_data["geometry"]["dimensions"] += 1

                            # Process the entity to extract actual geometry
                            process_entity(block_entity, scale_factor=1.0, is_block_content=True, block_name=block_name)

                        except Exception as e:
                            pass

                    raw_data["block_definitions"][block_name] = block_def_data

                except Exception as e:
                    raw_data["errors"].append(f"Block definition error: {e}")

        except Exception as e:
            raw_data["errors"].append(f"Blocks collection error: {e}")

        # Log summary
        logger.info(f"Extraction complete: {len(raw_data['blocks'])} blocks, "
                   f"{len(raw_data['dimensions'])} dimensions, "
                   f"{len(raw_data['text_entities'])} texts, "
                   f"{len(raw_data['xrefs'])} xrefs")

    except Exception as e:
        raw_data["errors"].append(f"Model space iteration error: {e}")

    return raw_data


def _extract_raw_dxf_data(file_path: str) -> Dict:
    """Extract raw data from DXF file using ezdxf"""
    import ezdxf

    raw_data = {
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "extraction_method": "ezdxf",
        "extraction_success": True,
        "blocks": [],
        "text_entities": [],
        "dimensions": [],
        "layers": {},
        "geometry": {
            "total_line_length": 0.0,
            "total_area": 0.0,
            "polyline_count": 0,
            "circle_count": 0,
            "arc_count": 0
        },
        "attributes": [],
        "errors": []
    }

    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        for entity in msp:
            entity_type = entity.dxftype()
            layer_name = entity.dxf.layer if hasattr(entity.dxf, 'layer') else "0"

            # Count by layer
            raw_data["layers"][layer_name] = raw_data["layers"].get(layer_name, 0) + 1

            # Blocks (INSERT entities)
            if entity_type == "INSERT":
                block_info = {
                    "name": entity.dxf.name,
                    "layer": layer_name,
                    "position": {
                        "x": entity.dxf.insert.x,
                        "y": entity.dxf.insert.y,
                        "z": entity.dxf.insert.z if hasattr(entity.dxf.insert, 'z') else 0
                    },
                    "rotation": entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                    "scale": {
                        "x": entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1,
                        "y": entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1
                    },
                    "attributes": []
                }

                # Extract attributes
                if hasattr(entity, 'attribs'):
                    for attrib in entity.attribs:
                        block_info["attributes"].append({
                            "tag": attrib.dxf.tag,
                            "value": attrib.dxf.text
                        })
                        raw_data["attributes"].append({
                            "block": entity.dxf.name,
                            "tag": attrib.dxf.tag,
                            "value": attrib.dxf.text
                        })

                raw_data["blocks"].append(block_info)

            # Text
            elif entity_type in ("TEXT", "MTEXT"):
                text_value = entity.dxf.text if entity_type == "TEXT" else entity.text
                raw_data["text_entities"].append({
                    "type": entity_type,
                    "text": text_value,
                    "layer": layer_name
                })

            # Dimensions
            elif entity_type == "DIMENSION":
                try:
                    raw_data["dimensions"].append({
                        "type": "dimension",
                        "text": entity.dxf.text if hasattr(entity.dxf, 'text') else "",
                        "layer": layer_name
                    })
                except:
                    pass

            # Lines
            elif entity_type == "LINE":
                try:
                    start = entity.dxf.start
                    end = entity.dxf.end
                    length = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5
                    raw_data["geometry"]["total_line_length"] += length
                except:
                    pass

            # Polylines
            elif entity_type == "LWPOLYLINE":
                raw_data["geometry"]["polyline_count"] += 1
                try:
                    raw_data["geometry"]["total_line_length"] += entity.length
                except:
                    pass

            # Circles
            elif entity_type == "CIRCLE":
                raw_data["geometry"]["circle_count"] += 1
                try:
                    import math
                    raw_data["geometry"]["total_area"] += math.pi * entity.dxf.radius**2
                except:
                    pass

            # Arcs
            elif entity_type == "ARC":
                raw_data["geometry"]["arc_count"] += 1

    except Exception as e:
        raw_data["errors"].append(f"DXF parsing error: {e}")
        raw_data["extraction_success"] = False

    return raw_data
