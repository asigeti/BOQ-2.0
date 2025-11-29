from typing import List, Dict

def get_supplier_recommendations(materials: List[Dict]) -> List[Dict]:
    """
    Mock supplier recommendations based on materials.
    """
    suppliers = [
        {"name": "Global Cement Co.", "material": "Concrete", "price_per_unit": 120.0, "delivery_days": 2},
        {"name": "SteelWorks Inc.", "material": "Steel", "price_per_unit": 850.0, "delivery_days": 5},
        {"name": "LumberJack Supply", "material": "Lumber", "price_per_unit": 5.5, "delivery_days": 1},
        {"name": "WallToWall Drywall", "material": "Drywall", "price_per_unit": 12.0, "delivery_days": 1},
    ]
    
    recommendations = []
    for mat in materials:
        # Simple matching logic
        matched = [s for s in suppliers if s["material"] in mat["material_name"]]
        if matched:
            for s in matched:
                recommendations.append({
                    "material": mat["material_name"],
                    "supplier": s["name"],
                    "price": s["price_per_unit"],
                    "total_cost": s["price_per_unit"] * mat["quantity"],
                    "delivery": f"{s['delivery_days']} days"
                })
        else:
             recommendations.append({
                    "material": mat["material_name"],
                    "supplier": "Generic Supplier",
                    "price": 0,
                    "total_cost": 0,
                    "delivery": "Unknown"
                })
    
    return recommendations
