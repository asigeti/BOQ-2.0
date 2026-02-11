import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Attempting to import app.main...")
    from app.main import app
    print("Successfully imported app.main")
    
    print("Attempting to import israeli_boq_service...")
    from app.services.boq.israeli_boq_service import IsraeliBOQService
    print("Successfully imported israeli_boq_service")
    
    print("Attempting to import layer_categorizer...")
    from app.services.layer_categorizer import categorize_layer
    print("Successfully imported layer_categorizer")
    
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
