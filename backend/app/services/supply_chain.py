from typing import List, Dict


class SupplyChainNotImplementedError(Exception):
    """Raised when supply chain feature is called but not yet implemented"""
    pass


def get_supplier_recommendations(materials: List[Dict]) -> List[Dict]:
    """
    Get supplier recommendations based on materials.

    NO MOCK DATA - This feature requires real supplier integration.
    """
    raise SupplyChainNotImplementedError(
        "Supply chain recommendations not yet implemented. "
        "This feature requires integration with real Israeli supplier APIs."
    )
