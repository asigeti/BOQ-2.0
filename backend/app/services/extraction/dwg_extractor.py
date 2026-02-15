"""
DWG Extractor for ConstructionAI Pro

Extracts material quantities from AutoCAD DWG files using multiple strategies:
1. AutoCAD COM interface (most accurate - requires AutoCAD installed)
2. ODA File Converter (DWG -> DXF conversion)
3. libredwg dwg2dxf (free, works on Linux/Docker)
4. Direct ezdxf fallback
5. Placeholder

Based on Easy-MCP-AutoCAD patterns for accurate BOQ extraction.
"""

import os
import logging
import shutil
import subprocess
import tempfile
import time
import re
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# AutoCAD COM interface (Windows only)
try:
    import win32com.client
    import pythoncom
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    logger.info("win32com not available - AutoCAD COM interface disabled")

# ODA File Converter paths (common installation locations - Windows and Linux)
ODA_CONVERTER_PATHS = [
    # Windows
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
    # Linux
    "/usr/bin/ODAFileConverter",
    "/opt/ODAFileConverter/ODAFileConverter",
    "/usr/local/bin/ODAFileConverter",
    # Environment override
    os.environ.get("ODA_CONVERTER_PATH", ""),
]


def _log_dwg_capabilities():
    """Log available DWG extraction tools at module load time"""
    capabilities = []

    if HAS_WIN32COM:
        capabilities.append("AutoCAD COM")

    for path in ODA_CONVERTER_PATHS:
        if path and os.path.exists(path):
            capabilities.append(f"ODA FileConverter ({path})")
            break

    dwg2dxf_path = shutil.which("dwg2dxf")
    if dwg2dxf_path:
        capabilities.append(f"libredwg dwg2dxf ({dwg2dxf_path})")

    try:
        import ezdxf
        capabilities.append("ezdxf (direct DXF read)")
    except ImportError:
        pass

    if capabilities:
        logger.info(f"DWG extraction capabilities: {', '.join(capabilities)}")
    else:
        logger.warning("DWG extraction: NO tools available - uploads will return placeholder")


# Log capabilities at import time
_log_dwg_capabilities()


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
        """Open a DWG file in AutoCAD with proper timing"""
        if not self.acad:
            return False

        try:
            self.doc = self.acad.Documents.Open(file_path)
            logger.info(f"Opened drawing: {file_path}")
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


def convert_dwg_to_dxf_oda(dwg_path: str, output_dir: Optional[str] = None) -> Optional[str]:
    """
    Convert DWG to DXF using ODA File Converter.
    Returns path to converted DXF file or None if conversion failed.
    """
    converter = find_oda_converter()
    if not converter:
        logger.debug("ODA File Converter not found")
        return None

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="dwg_convert_")

    input_dir = os.path.dirname(dwg_path)
    input_file = os.path.basename(dwg_path)

    try:
        # ODA File Converter command line:
        # ODAFileConverter <input_dir> <output_dir> <output_version> <output_type> <recurse> <audit> [filter]
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
            logger.info(f"ODA converted {dwg_path} to {dxf_path}")
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


def convert_dwg_to_dxf_libredwg(dwg_path: str, output_dir: Optional[str] = None) -> Optional[str]:
    """
    Convert DWG to DXF using libredwg's dwg2dxf command.
    Available on Linux/Docker via apt-get install libredwg-tools.
    Returns path to converted DXF file or None if conversion failed.
    """
    dwg2dxf = shutil.which("dwg2dxf")
    if not dwg2dxf:
        logger.debug("dwg2dxf (libredwg-tools) not found on PATH")
        return None

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="dwg_libredwg_")

    base_name = os.path.splitext(os.path.basename(dwg_path))[0]
    dxf_output = os.path.join(output_dir, f"{base_name}.dxf")

    try:
        cmd = [dwg2dxf, "-o", dxf_output, dwg_path]
        logger.info(f"Running libredwg: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # libredwg sometimes returns non-zero but still produces usable output
        if result.returncode != 0:
            logger.warning(
                f"dwg2dxf exited with code {result.returncode}: "
                f"{result.stderr[:500] if result.stderr else 'no stderr'}"
            )

        # Check if output file was created regardless of exit code
        if os.path.exists(dxf_output) and os.path.getsize(dxf_output) > 0:
            logger.info(
                f"libredwg converted {dwg_path} -> {dxf_output} "
                f"({os.path.getsize(dxf_output)} bytes)"
            )
            return dxf_output

        logger.warning(f"dwg2dxf produced no output file at {dxf_output}")
        return None

    except subprocess.TimeoutExpired:
        logger.error("dwg2dxf conversion timed out (120s)")
        return None
    except Exception as e:
        logger.error(f"dwg2dxf conversion error: {e}")
        return None


def _extract_dxf_and_cleanup(dxf_path: str, source_label: str) -> List[Dict]:
    """
    Extract materials from a converted DXF file and clean up temp files.
    Shared by ODA and libredwg conversion strategies.
    """
    try:
        from .dxf_extractor import extract_from_dxf
        materials = extract_from_dxf(dxf_path)

        # Tag source
        for mat in materials:
            mat['source'] = f'{source_label}_converted_dxf'
            # Boost confidence slightly since conversion succeeded
            mat['confidence_score'] = min(mat.get('confidence_score', 0.7) + 0.05, 1.0)

        return materials

    except Exception as e:
        logger.error(f"DXF extraction after {source_label} conversion failed: {e}")
        return []

    finally:
        # Clean up temp files
        try:
            os.remove(dxf_path)
            parent = os.path.dirname(dxf_path)
            if parent and os.path.isdir(parent) and parent.startswith(tempfile.gettempdir()):
                os.rmdir(parent)
        except Exception:
            pass


def extract_from_dwg(file_path: str) -> List[Dict]:
    """
    Extract material quantities from a DWG file.

    Uses multiple strategies in order of accuracy:
    1. AutoCAD COM interface (most accurate, Windows only)
    2. ODA File Converter -> DXF -> ezdxf
    3. libredwg dwg2dxf -> DXF -> ezdxf (primary Docker/Linux strategy)
    4. Direct ezdxf (works for some DWG versions)
    5. Placeholder fallback

    Args:
        file_path: Path to the DWG file

    Returns:
        List of extracted materials with quantities
    """
    # Strategy 1: Try AutoCAD COM interface (most accurate)
    if HAS_WIN32COM:
        logger.info("Attempting AutoCAD COM extraction...")
        extractor = AutoCADExtractor()

        if extractor.connect():
            if extractor.open_drawing(file_path):
                materials = extractor.scan_elements()
                extractor.close()

                if materials:
                    logger.info(f"AutoCAD COM extracted {len(materials)} materials")
                    return materials
            extractor.close()

    # Strategy 2: Try ODA File Converter -> DXF
    logger.info("Attempting ODA File Converter extraction...")
    dxf_path = convert_dwg_to_dxf_oda(file_path)

    if dxf_path:
        materials = _extract_dxf_and_cleanup(dxf_path, "oda")
        if materials:
            logger.info(f"ODA converter extracted {len(materials)} materials")
            return materials

    # Strategy 3: Try libredwg dwg2dxf -> DXF (primary Docker/Linux strategy)
    logger.info("Attempting libredwg dwg2dxf extraction...")
    dxf_path = convert_dwg_to_dxf_libredwg(file_path)

    if dxf_path:
        materials = _extract_dxf_and_cleanup(dxf_path, "libredwg")
        if materials:
            logger.info(f"libredwg extracted {len(materials)} materials")
            return materials

    # Strategy 4: Fallback - try direct ezdxf (works for some DWG versions)
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

    # Strategy 5: Last resort - return placeholder
    logger.warning(f"All extraction methods failed for {file_path}")
    return [{
        'material_name': 'DWG File - Manual Review Required',
        'quantity': 1,
        'unit': 'file',
        'confidence_score': 0.1,
        'source': 'no_extraction',
        'note': 'Install libredwg-tools, AutoCAD, or ODA File Converter for accurate extraction'
    }]


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
    dxf_path = convert_dwg_to_dxf_oda(file_path)

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

    # Strategy 3: libredwg dwg2dxf + ezdxf
    logger.info("Extracting raw data via libredwg/ezdxf...")
    dxf_path = convert_dwg_to_dxf_libredwg(file_path)

    if dxf_path:
        try:
            raw_data = _extract_raw_dxf_data(dxf_path)
            raw_data["extraction_method"] = "libredwg"
            raw_data["extraction_success"] = True
            raw_data["file_path"] = file_path
            raw_data["filename"] = os.path.basename(file_path)

            # Cleanup
            try:
                os.remove(dxf_path)
                parent = os.path.dirname(dxf_path)
                if parent and os.path.isdir(parent) and parent.startswith(tempfile.gettempdir()):
                    os.rmdir(parent)
            except:
                pass

            return raw_data
        except Exception as e:
            raw_data["errors"].append(f"libredwg/DXF extraction error: {e}")

    # Strategy 4: Direct ezdxf (last resort)
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
    """Extract comprehensive raw data from AutoCAD document"""
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
            "arc_count": 0
        },
        "attributes": [],
        "errors": []
    }

    try:
        model_space = doc.ModelSpace

        for i in range(model_space.Count):
            try:
                entity = model_space.Item(i)
                entity_type = entity.ObjectName
                layer_name = entity.Layer

                # Count by layer
                raw_data["layers"][layer_name] = raw_data["layers"].get(layer_name, 0) + 1

                # Blocks
                if entity_type == "AcDbBlockReference":
                    block_info = {
                        "name": entity.Name,
                        "layer": layer_name,
                        "position": {
                            "x": entity.InsertionPoint[0],
                            "y": entity.InsertionPoint[1],
                            "z": entity.InsertionPoint[2] if len(entity.InsertionPoint) > 2 else 0
                        },
                        "rotation": entity.Rotation if hasattr(entity, 'Rotation') else 0,
                        "scale": {
                            "x": entity.XScaleFactor if hasattr(entity, 'XScaleFactor') else 1,
                            "y": entity.YScaleFactor if hasattr(entity, 'YScaleFactor') else 1
                        },
                        "attributes": []
                    }

                    # Extract block attributes
                    if entity.HasAttributes:
                        for attr in entity.GetAttributes():
                            block_info["attributes"].append({
                                "tag": attr.TagString,
                                "value": attr.TextString
                            })
                            raw_data["attributes"].append({
                                "block": entity.Name,
                                "tag": attr.TagString,
                                "value": attr.TextString
                            })

                    raw_data["blocks"].append(block_info)

                # Text
                elif entity_type in ("AcDbText", "AcDbMText"):
                    raw_data["text_entities"].append({
                        "type": entity_type,
                        "text": entity.TextString,
                        "layer": layer_name,
                        "height": entity.Height if hasattr(entity, 'Height') else 0,
                        "position": {
                            "x": entity.InsertionPoint[0],
                            "y": entity.InsertionPoint[1]
                        }
                    })

                # Dimensions
                elif entity_type == "AcDbDimension":
                    try:
                        raw_data["dimensions"].append({
                            "type": "dimension",
                            "measurement": entity.Measurement,
                            "text_override": entity.TextOverride if hasattr(entity, 'TextOverride') else "",
                            "layer": layer_name
                        })
                    except:
                        pass

                # Geometry - Lines
                elif entity_type == "AcDbLine":
                    try:
                        length = entity.Length
                        raw_data["geometry"]["total_line_length"] += length
                    except:
                        pass

                # Geometry - Polylines
                elif entity_type in ("AcDbPolyline", "AcDbLWPolyline", "AcDb2dPolyline"):
                    raw_data["geometry"]["polyline_count"] += 1
                    try:
                        raw_data["geometry"]["total_line_length"] += entity.Length
                    except:
                        pass
                    try:
                        if entity.Closed:
                            raw_data["geometry"]["total_area"] += entity.Area
                    except:
                        pass

                # Geometry - Circles
                elif entity_type == "AcDbCircle":
                    raw_data["geometry"]["circle_count"] += 1
                    try:
                        raw_data["geometry"]["total_area"] += entity.Area
                    except:
                        pass

                # Geometry - Arcs
                elif entity_type == "AcDbArc":
                    raw_data["geometry"]["arc_count"] += 1
                    try:
                        raw_data["geometry"]["total_line_length"] += entity.ArcLength
                    except:
                        pass

                # Hatches (areas)
                elif entity_type == "AcDbHatch":
                    try:
                        raw_data["geometry"]["total_area"] += entity.Area
                    except:
                        pass

            except Exception as e:
                raw_data["errors"].append(f"Error processing entity {i}: {e}")

    except Exception as e:
        raw_data["errors"].append(f"Model space iteration error: {e}")

    return raw_data


def _extract_raw_dxf_data(file_path: str) -> Dict:
    """Extract raw data from DXF file using ezdxf"""
    import ezdxf
    import math

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
