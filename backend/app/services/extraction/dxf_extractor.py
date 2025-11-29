import ezdxf
from typing import List, Dict
import sys

def extract_from_dxf(file_path: str) -> List[Dict]:
    """
    Extracts information from a DXF file.
    Counts entities like Lines, Circles, etc., to estimate complexity/materials.
    """
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        counts = {
            "LINE": 0,
            "CIRCLE": 0,
            "LWPOLYLINE": 0,
            "INSERT": 0 # Blocks
        }
        
        total_length = 0.0
        
        for entity in msp:
            if entity.dxftype() in counts:
                counts[entity.dxftype()] += 1
            
            if entity.dxftype() == "LINE":
                # Calculate length of lines (could represent walls, pipes, etc.)
                start = entity.dxf.start
                end = entity.dxf.end
                length = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5
                total_length += length

        materials = []
        
        # Heuristic mapping from entities to materials
        if counts["LINE"] > 0 or counts["LWPOLYLINE"] > 0:
            materials.append({
                "material_name": "Estimated Wall/Piping Length",
                "quantity": round(total_length, 2),
                "unit": "m", # Assuming drawing units are meters
                "confidence_score": 0.7
            })
            
        if counts["INSERT"] > 0:
             materials.append({
                "material_name": "Fixtures/Blocks",
                "quantity": counts["INSERT"],
                "unit": "units",
                "confidence_score": 0.9
            })

        return materials

    except Exception as e:
        print(f"Error reading DXF: {e}", file=sys.stderr)
        return []
