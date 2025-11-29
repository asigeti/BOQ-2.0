"""
IFC/BIM File Extractor for ConstructionAI Pro

Extracts material quantities from Industry Foundation Classes (IFC) files,
which are the standard format for Building Information Modeling (BIM).
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import ifcopenshell - it may not be installed
try:
    import ifcopenshell
    import ifcopenshell.util.element as element_util
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False
    logger.warning("ifcopenshell not installed. IFC extraction will not be available.")


# Mapping of IFC element types to material categories
IFC_CATEGORY_MAP = {
    'IfcWall': 'masonry',
    'IfcWallStandardCase': 'masonry',
    'IfcSlab': 'concrete',
    'IfcBeam': 'steel',
    'IfcColumn': 'concrete',
    'IfcDoor': 'doors_windows',
    'IfcWindow': 'doors_windows',
    'IfcRoof': 'roofing',
    'IfcStair': 'concrete',
    'IfcRailing': 'steel',
    'IfcCovering': 'flooring',
    'IfcCurtainWall': 'doors_windows',
    'IfcPlate': 'steel',
    'IfcMember': 'steel',
    'IfcFooting': 'concrete',
    'IfcPile': 'concrete',
    'IfcReinforcingBar': 'steel',
    'IfcReinforcingMesh': 'steel',
    'IfcTendon': 'steel',
    'IfcBuildingElementProxy': 'other',
}

# Default units for different quantity types
QUANTITY_UNITS = {
    'area': 'm2',
    'volume': 'm3',
    'length': 'm',
    'count': 'pcs',
    'weight': 'kg',
}


def extract_from_ifc(file_path: str) -> List[Dict]:
    """
    Extract material quantities from an IFC/BIM file.

    IFC files contain detailed 3D model data with accurate quantities
    calculated from the geometry, making them highly reliable for BOQ.

    Args:
        file_path: Path to the IFC file

    Returns:
        List of material dictionaries with quantities
    """
    if not IFC_AVAILABLE:
        logger.error("ifcopenshell is not installed. Cannot process IFC files.")
        return [{
            'material_name': 'IFC Processing Unavailable',
            'quantity': 0,
            'unit': 'N/A',
            'confidence_score': 0.0,
            'category': 'other',
            'notes': 'ifcopenshell library not installed. Please install it to process IFC files.'
        }]

    try:
        logger.info(f"Opening IFC file: {file_path}")
        ifc_file = ifcopenshell.open(file_path)

        # Get project info
        project = ifc_file.by_type('IfcProject')
        if project:
            logger.info(f"IFC Project: {project[0].Name if project[0].Name else 'Unnamed'}")

        materials = []

        # Extract building elements
        materials.extend(_extract_building_elements(ifc_file))

        # Extract material definitions
        materials.extend(_extract_material_definitions(ifc_file))

        # Merge duplicates
        merged = _merge_ifc_materials(materials)

        logger.info(f"IFC extraction complete. Found {len(merged)} materials.")
        return merged

    except Exception as e:
        logger.error(f"IFC extraction failed: {e}")
        return [{
            'material_name': 'IFC Processing Error',
            'quantity': 0,
            'unit': 'N/A',
            'confidence_score': 0.0,
            'category': 'other',
            'notes': f'Error processing IFC file: {str(e)}'
        }]


def _extract_building_elements(ifc_file) -> List[Dict]:
    """Extract quantities from IFC building elements"""
    materials = []
    element_counts = defaultdict(lambda: {'count': 0, 'area': 0, 'volume': 0, 'length': 0})

    # Process each element type
    for ifc_type, category in IFC_CATEGORY_MAP.items():
        try:
            elements = ifc_file.by_type(ifc_type)

            for element in elements:
                element_name = _get_element_name(element, ifc_type)
                quantities = _get_element_quantities(element)

                # Create unique key for this element type
                key = (element_name, category)

                element_counts[key]['count'] += 1
                element_counts[key]['area'] += quantities.get('area', 0)
                element_counts[key]['volume'] += quantities.get('volume', 0)
                element_counts[key]['length'] += quantities.get('length', 0)
                element_counts[key]['category'] = category
                element_counts[key]['ifc_type'] = ifc_type

        except Exception as e:
            logger.debug(f"Error processing {ifc_type}: {e}")

    # Convert to material list
    for (name, category), data in element_counts.items():
        # Determine primary quantity type based on element
        if data['volume'] > 0:
            quantity = round(data['volume'], 2)
            unit = 'm3'
        elif data['area'] > 0:
            quantity = round(data['area'], 2)
            unit = 'm2'
        elif data['length'] > 0:
            quantity = round(data['length'], 2)
            unit = 'm'
        else:
            quantity = data['count']
            unit = 'pcs'

        if quantity > 0:
            materials.append({
                'material_name': name,
                'quantity': quantity,
                'unit': unit,
                'confidence_score': 0.95,  # BIM data is highly accurate
                'category': category,
                'notes': f"IFC Type: {data.get('ifc_type', 'Unknown')}, Count: {data['count']}"
            })

    return materials


def _extract_material_definitions(ifc_file) -> List[Dict]:
    """Extract material definitions and their usage"""
    materials = []
    material_usage = defaultdict(lambda: {'volume': 0, 'area': 0, 'count': 0})

    try:
        # Get all material definitions
        ifc_materials = ifc_file.by_type('IfcMaterial')

        for mat in ifc_materials:
            mat_name = mat.Name if mat.Name else 'Unnamed Material'

            # Try to get associated elements and their quantities
            # This is a simplified approach - full implementation would
            # traverse IfcRelAssociatesMaterial relationships
            material_usage[mat_name]['count'] += 1

        # Convert to material list
        for mat_name, usage in material_usage.items():
            if usage['count'] > 0:
                materials.append({
                    'material_name': f"Material: {mat_name}",
                    'quantity': usage['count'],
                    'unit': 'pcs',
                    'confidence_score': 0.8,
                    'category': _guess_category(mat_name),
                    'notes': 'Extracted from IFC material definitions'
                })

    except Exception as e:
        logger.debug(f"Error extracting material definitions: {e}")

    return materials


def _get_element_name(element, ifc_type: str) -> str:
    """Get a descriptive name for an IFC element"""
    # Try to get element name
    if hasattr(element, 'Name') and element.Name:
        return element.Name

    # Try to get type name
    if hasattr(element, 'ObjectType') and element.ObjectType:
        return element.ObjectType

    # Use IFC type as fallback
    type_names = {
        'IfcWall': 'Wall',
        'IfcWallStandardCase': 'Wall',
        'IfcSlab': 'Slab',
        'IfcBeam': 'Beam',
        'IfcColumn': 'Column',
        'IfcDoor': 'Door',
        'IfcWindow': 'Window',
        'IfcRoof': 'Roof',
        'IfcStair': 'Stair',
        'IfcRailing': 'Railing',
        'IfcCovering': 'Covering/Flooring',
        'IfcFooting': 'Footing',
        'IfcPile': 'Pile',
    }

    return type_names.get(ifc_type, ifc_type.replace('Ifc', ''))


def _get_element_quantities(element) -> Dict[str, float]:
    """Extract quantity data from an IFC element"""
    quantities = {'area': 0, 'volume': 0, 'length': 0}

    try:
        # Check for quantity sets (IfcElementQuantity)
        if hasattr(element, 'IsDefinedBy'):
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    prop_set = definition.RelatingPropertyDefinition

                    if prop_set.is_a('IfcElementQuantity'):
                        for qty in prop_set.Quantities:
                            if qty.is_a('IfcQuantityArea'):
                                quantities['area'] += qty.AreaValue or 0
                            elif qty.is_a('IfcQuantityVolume'):
                                quantities['volume'] += qty.VolumeValue or 0
                            elif qty.is_a('IfcQuantityLength'):
                                quantities['length'] += qty.LengthValue or 0

    except Exception as e:
        logger.debug(f"Error getting quantities: {e}")

    return quantities


def _guess_category(material_name: str) -> str:
    """Guess category based on material name"""
    name_lower = material_name.lower()

    category_keywords = {
        'concrete': ['concrete', 'beton', 'cement'],
        'steel': ['steel', 'metal', 'iron', 'rebar', 'reinforc'],
        'masonry': ['brick', 'block', 'masonry', 'stone'],
        'lumber': ['wood', 'timber', 'lumber', 'plywood'],
        'drywall': ['drywall', 'gypsum', 'plaster', 'board'],
        'roofing': ['roof', 'shingle', 'membrane'],
        'insulation': ['insulation', 'thermal', 'acoustic'],
        'flooring': ['floor', 'tile', 'carpet', 'vinyl'],
        'paint': ['paint', 'coating', 'finish'],
    }

    for category, keywords in category_keywords.items():
        if any(kw in name_lower for kw in keywords):
            return category

    return 'other'


def _merge_ifc_materials(materials: List[Dict]) -> List[Dict]:
    """Merge duplicate materials from IFC extraction"""
    merged = {}

    for mat in materials:
        key = (mat['material_name'].lower(), mat['unit'].lower())

        if key in merged:
            merged[key]['quantity'] += mat['quantity']
            # Keep higher confidence score
            merged[key]['confidence_score'] = max(
                merged[key]['confidence_score'],
                mat['confidence_score']
            )
        else:
            merged[key] = mat.copy()

    return list(merged.values())
