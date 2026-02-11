import sys
import os
import logging
import time

# Add backend to path so we can import app modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Setup logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from app.services.extraction.dwg_extractor import extract_raw_data_from_dwg
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

DWG_PATH = r"docs\DCRC-WP-PLG.dwg"
ABS_DWG_PATH = os.path.abspath(DWG_PATH)

def test_extraction():
    if not os.path.exists(ABS_DWG_PATH):
        print(f"Error: DWG file not found at {ABS_DWG_PATH}")
        # Try to find any dwg in docs
        docs_dir = os.path.join(os.getcwd(), 'docs')
        if os.path.exists(docs_dir):
            files = [f for f in os.listdir(docs_dir) if f.endswith('.dwg')]
            if files:
                print(f"Found other DWGs: {files}")
            else:
                print("No DWG files found in docs/.")
        return

    print(f"--- Starting Extraction Test on {ABS_DWG_PATH} ---")
    print("This should show progress logs if optimization is working...")
    
    start_time = time.time()
    try:
        data = extract_raw_data_from_dwg(ABS_DWG_PATH)
        duration = time.time() - start_time
        
        success = data.get("extraction_success", False)
        error_count = len(data.get("errors", []))
        layer_count = len(data.get("layers", {}))
        
        print(f"\n--- Extraction Complete in {duration:.2f} seconds ---")
        print(f"Success: {success}")
        print(f"Errors: {error_count}")
        print(f"Layers Found: {layer_count}")
        if data.get("errors"):
            print("First 3 errors:")
            for e in data["errors"][:3]:
                print(f" - {e}")

    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction()
