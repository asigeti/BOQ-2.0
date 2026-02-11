import json
import re

# =============================================================================
# MOCKED LOGIC (Mirroring the changes made in backend)
# =============================================================================

# 1. Extraction Filter Logic
def is_boq_candidate(entity_type, is_closed=False):
    """Mirror of dwg_extractor.py logic"""
    # 1. Reject Attributes/Annotations
    if entity_type in ("AcDbText", "AcDbMText", "AcDbDimension", "AcDbLeader", 
                      "AcDbAttributeDefinition", "AcDbAttribute"):
        return False
        
    # 2. Reject decorative/non-structural
    if entity_type in ("AcDbHatch", "AcDbPoint", "AcDbRay", "AcDbXline"):
        return False
        
    # 3. Reject Open Polylines
    if entity_type in ("AcDbPolyline", "AcDbLWPolyline", "AcDb2dPolyline", "AcDb3dPolyline"):
        if not is_closed:
            return False
            
    # 4. Reject pure Lines
    if entity_type == "AcDbLine":
        return False

    return True

# 2. Layer Categorization Logic
LAYER_PATTERNS = {
    "STRUCTURAL": [r"עמוד", r"קורה", r"יסוד", r"בטון", r"זיון", "column", "beam", "foundation", "concrete", "rebar", "S-"],
    "INFRASTRUCTURE": [r"חפירה", "excavation", "dig"]
}

BLACKLIST_KEYWORDS = [
    "TEXT", "DIM", "DIMENSION", "NOTE", "TAG", "LABEL", "LEGEND", 
    "TITLE", "SHEET", "GRID", "AXIS", "HATCH", "PATTERN", "SYMB"
]

def categorize_layer(layer_name):
    """Mirror of layer_categorizer.py logic"""
    upper = layer_name.upper()
    
    # Blacklist check
    for bad in BLACKLIST_KEYWORDS:
        if bad in upper:
            return "ANNOTATIONS"
            
    # Regex check
    for cat, patterns in LAYER_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, layer_name, re.IGNORECASE):
                return cat
    return "UNKNOWN"

# 3. Formula Logic (Calibrated)
def calc_quantities(counts, areas, building_area, site_area):
    """Mirror of NEW israeli_boq_service.py logic"""
    
    # Earthworks
    # Old: site_area * 0.3
    # New: building_area * 1.2 * 0.5
    earthworks = building_area * 1.2 * 0.5
    
    # Columns
    # Old: count * 0.3 * 0.3 * 3.0 (bad count)
    # New: filtered_count * 0.3 * 0.3 * 3.5
    col_count = counts.get("STRUCTURAL", 0)
    columns_vol = col_count * 0.3 * 0.3 * 3.5
    
    # Steel
    # Old: total_concrete * 100
    # New: decoupled (approx here)
    steel = columns_vol * 120 / 1000.0 # tons
    
    return earthworks, columns_vol, steel

# =============================================================================
# SIMULATION
# =============================================================================

def run_simulation():
    try:
        with open(r"docs\raw_extraction_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: docs/raw_extraction_data.json not found.")
        return

    print("loaded raw data...")
    
    # Metrics
    total_entities_raw = 0
    total_entities_filtered = 0
    
    layer_counts_raw = {}
    layer_counts_filtered = {}
    
    # --- 1. Blocks ---
    for b in data.get("blocks", []):
        lname = b.get("layer", "0")
        cat = categorize_layer(lname)
        
        # Raw count (everything in a category layer)
        if cat != "UNKNOWN" and cat != "ANNOTATIONS": 
             layer_counts_raw[cat] = layer_counts_raw.get(cat, 0) + 1
        
        # Filtered count
        if cat != "ANNOTATIONS" and cat != "UNKNOWN":
             # Blocks are valid unless they are clearly annotations (handled by blacklist)
             layer_counts_filtered[cat] = layer_counts_filtered.get(cat, 0) + 1

    # --- 2. Text ---
    for t in data.get("text_entities", []):
        lname = t.get("layer", "0")
        cat = categorize_layer(lname)
        
        # Raw count: Text WAS counted if it was on a structural layer
        if cat != "UNKNOWN" and cat != "ANNOTATIONS":
            layer_counts_raw[cat] = layer_counts_raw.get(cat, 0) + 1
        
        # Filtered: Text is completely rejected
        pass 

    # --- 3. Closed Polylines ---
    for p in data.get("closed_polylines", []):
        lname = p.get("layer", "0")
        cat = categorize_layer(lname)
        area = p.get("area", 0)
        
        if cat != "UNKNOWN" and cat != "ANNOTATIONS":
            # Raw
            layer_counts_raw[cat] = layer_counts_raw.get(cat, 0) + 1
            
            # Filtered
            if cat == "STRUCTURAL":
                # Column logic: 0.04 - 2.0
                if 0.04 <= area <= 2.0:
                    layer_counts_filtered[cat] = layer_counts_filtered.get(cat, 0) + 1
            else:
                 layer_counts_filtered[cat] = layer_counts_filtered.get(cat, 0) + 1

    print("\n--- SIMULATION RESULTS ---\n")
    
    # User Reference Data
    A_site_raw = 28183 
    A_build_est = 5900 # Estimate
    
    # Calculation
    
    # Earthworks
    earth_old = A_site_raw * 0.3
    earth_new, _, _ = calc_quantities(layer_counts_filtered, {}, A_build_est, A_site_raw)
    
    print(f"EARTHWORKS ESTIMATE:")
    print(f"  OLD Logic: {earth_old:,.1f} m3")
    print(f"  NEW Logic: {earth_new:,.1f} m3")
    print(f"  TARGET:    3,550 m3")
    
    # Columns
    count_raw = layer_counts_raw.get("STRUCTURAL", 0)
    count_new = layer_counts_filtered.get("STRUCTURAL", 0)
    
    vol_old = count_raw * 0.3 * 0.3 * 3.0
    _, vol_new, _ = calc_quantities(layer_counts_filtered, {}, A_build_est, A_site_raw)
    
    print(f"\nCOLUMNS ESTIMATE (STRUCTURAL Filter):")
    print(f"  Raw Count (incl Text/Hatch): {count_raw}")
    print(f"  Filtered Count (Valid Geom): {count_new}")
    print(f"  OLD Volume: {vol_old:,.1f} m3")
    print(f"  NEW Volume: {vol_new:,.1f} m3")
    print(f"  TARGET:     ~2-10 m3")
    
if __name__ == "__main__":
    run_simulation()
