"""
Diagnostic script to test AutoCAD COM interface with proper timing
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def wait_for_autocad(acad, timeout=30):
    """Wait for AutoCAD to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            # Try to access a simple property
            _ = acad.ActiveDocument
            return True
        except:
            time.sleep(0.5)
    return False

def test_autocad_com():
    print("=" * 60)
    print("AutoCAD COM Interface Diagnostic")
    print("=" * 60)

    try:
        import win32com.client
        import pythoncom
        print("[OK] win32com.client imported")
    except ImportError as e:
        print(f"[ERROR] Cannot import win32com.client: {e}")
        return

    # Initialize COM
    pythoncom.CoInitialize()

    # Try to connect to AutoCAD
    acad = None
    try:
        acad = win32com.client.Dispatch("AutoCAD.Application")
        acad.Visible = True  # Make sure it's visible
        print("[OK] Connected to AutoCAD")
    except Exception as e:
        print(f"[ERROR] Cannot connect to AutoCAD: {e}")
        return

    print(f"[INFO] AutoCAD Version: {acad.Version}")

    # Wait for AutoCAD to be ready
    print("[INFO] Waiting for AutoCAD to be ready...")
    time.sleep(3)

    # Open the test file
    test_file = r"C:\Users\asige\OneDrive\Documents\GitHub\BOQ-2.0\docs\DCRC-WP-PLG.dwg"

    if not os.path.exists(test_file):
        print(f"[ERROR] Test file not found: {test_file}")
        return

    print(f"\n[INFO] Opening: {os.path.basename(test_file)}")

    try:
        doc = acad.Documents.Open(test_file)
        print(f"[OK] Document opened")

        # Wait for document to fully load
        print("[INFO] Waiting for document to load...")
        time.sleep(5)

    except Exception as e:
        print(f"[ERROR] Cannot open document: {e}")
        return

    # Get model space with retries
    msp = None
    for attempt in range(5):
        try:
            time.sleep(1)
            msp = doc.ModelSpace
            print(f"[OK] ModelSpace accessed (attempt {attempt + 1})")
            break
        except Exception as e:
            print(f"[RETRY {attempt + 1}] ModelSpace access failed: {e}")
            time.sleep(2)

    if msp is None:
        print("[ERROR] Could not access ModelSpace after retries")
        try:
            doc.Close(False)
        except:
            pass
        return

    # Get entity count
    try:
        count = msp.Count
        print(f"[INFO] Total entities: {count}")
    except Exception as e:
        print(f"[ERROR] Cannot get entity count: {e}")
        try:
            doc.Close(False)
        except:
            pass
        return

    # Sample entities
    print("\n" + "-" * 60)
    print("Analyzing entities...")
    print("-" * 60)

    entity_types = {}
    layers = {}
    blocks = []
    texts = []
    dimensions = []

    total_to_process = min(count, 500)  # Process up to 500 entities

    for i in range(total_to_process):
        try:
            entity = msp.Item(i)

            # Get entity type
            entity_type = "Unknown"
            try:
                entity_type = entity.ObjectName
            except:
                try:
                    entity_type = str(type(entity).__name__)
                except:
                    pass

            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            # Get layer
            try:
                layer = entity.Layer
                layers[layer] = layers.get(layer, 0) + 1
            except:
                pass

            # Block references
            if "BlockReference" in entity_type or entity_type == "AcDbBlockReference":
                try:
                    name = entity.Name
                    blocks.append(name)
                except:
                    pass

            # Text entities
            if "Text" in entity_type:
                try:
                    text = entity.TextString
                    if text and len(text.strip()) > 0:
                        texts.append(text[:100])
                except:
                    pass

            # Dimensions
            if "Dimension" in entity_type:
                try:
                    measurement = entity.Measurement
                    dimensions.append(measurement)
                except:
                    pass

            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{total_to_process} entities...")

        except Exception as e:
            pass  # Skip problematic entities

    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION RESULTS")
    print("=" * 60)

    print(f"\nEntity Types ({len(entity_types)} types found):")
    for etype, cnt in sorted(entity_types.items(), key=lambda x: -x[1])[:15]:
        print(f"  {cnt:>5} x {etype}")

    print(f"\nLayers ({len(layers)} layers found):")
    for layer, cnt in sorted(layers.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cnt:>5} x {layer}")

    print(f"\nBlocks ({len(blocks)} block references):")
    block_counts = {}
    for b in blocks:
        block_counts[b] = block_counts.get(b, 0) + 1
    for block, cnt in sorted(block_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {cnt:>5} x {block}")

    print(f"\nText Items ({len(texts)} text entities):")
    for text in texts[:15]:
        # Clean text for display
        clean_text = text.replace('\n', ' ').strip()[:60]
        print(f"  - {clean_text}")

    print(f"\nDimensions ({len(dimensions)} dimension entities):")
    if dimensions:
        print(f"  Min: {min(dimensions):.2f}")
        print(f"  Max: {max(dimensions):.2f}")
        print(f"  Sample: {dimensions[:5]}")

    # Close document
    print("\n" + "-" * 60)
    try:
        doc.Close(False)
        print("[OK] Document closed")
    except:
        print("[WARN] Could not close document properly")

    print("\n[DONE] Diagnostic complete!")


if __name__ == "__main__":
    test_autocad_com()
