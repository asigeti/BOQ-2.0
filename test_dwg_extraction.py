"""
Test script to simulate frontend triggering DWG extraction
Generates a report as if it was created for the frontend display
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_extraction_test():
    """Run DWG extraction test and generate frontend-ready report"""

    # Path to test file
    test_file = os.path.join(os.path.dirname(__file__), 'docs', 'DCRC-WP-PLG.dwg')

    print("=" * 70)
    print("ConstructionAI Pro - DWG Extraction Test")
    print("=" * 70)
    print(f"\nTest File: {os.path.basename(test_file)}")
    print(f"File Size: {os.path.getsize(test_file) / 1024 / 1024:.2f} MB")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 70)

    try:
        # Import the extractor
        from app.services.extraction.dwg_extractor import extract_from_dwg, HAS_WIN32COM, find_oda_converter

        # Check available extraction methods
        print("\n[System Check]")
        print(f"  AutoCAD COM Available: {'Yes' if HAS_WIN32COM else 'No'}")

        oda_path = find_oda_converter()
        print(f"  ODA File Converter: {'Found at ' + oda_path if oda_path else 'Not installed'}")
        print(f"  ezdxf Fallback: Available")

        print("\n[Starting Extraction...]")
        start_time = datetime.now()

        # Run extraction
        materials = extract_from_dwg(test_file)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        print(f"[Extraction Complete] Processing time: {processing_time:.2f}s")
        print("-" * 70)

        # Generate Frontend Report
        report = generate_frontend_report(
            filename=os.path.basename(test_file),
            materials=materials,
            processing_time=processing_time
        )

        return report

    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_frontend_report(filename: str, materials: list, processing_time: float) -> dict:
    """Generate a report in the format expected by the frontend"""

    # Calculate summary statistics
    total_items = len(materials)
    avg_confidence = sum(m.get('confidence_score', 0) for m in materials) / total_items if total_items > 0 else 0

    # Group by source/method
    by_source = {}
    for m in materials:
        source = m.get('source', 'unknown')
        by_source[source] = by_source.get(source, 0) + 1

    # Determine extraction method used
    if any('autocad' in str(m.get('source', '')) for m in materials):
        method = 'AutoCAD COM Interface'
    elif any('oda' in str(m.get('source', '')) for m in materials):
        method = 'ODA File Converter'
    elif any('dxf' in str(m.get('source', '')) for m in materials):
        method = 'ezdxf Direct Read'
    else:
        method = 'Fallback/Manual Review'

    # Build the report
    report = {
        "status": "completed",
        "filename": filename,
        "processed_at": datetime.now().isoformat(),
        "processing_time_seconds": round(processing_time, 2),
        "extraction_method": method,
        "summary": {
            "total_materials": total_items,
            "average_confidence": round(avg_confidence * 100, 1),
            "extraction_sources": by_source
        },
        "materials": materials
    }

    # Print formatted report for console
    print("\n" + "=" * 70)
    print("[EXTRACTION REPORT] - Frontend Format")
    print("=" * 70)

    print(f"\n[File]: {filename}")
    print(f"[Processing Time]: {processing_time:.2f} seconds")
    print(f"[Extraction Method]: {method}")

    print(f"\n[Summary]:")
    print(f"   - Total Materials Found: {total_items}")
    print(f"   - Average Confidence: {avg_confidence * 100:.1f}%")

    print(f"\n[Materials Extracted]:")
    print("-" * 70)
    print(f"{'Material Name':<40} {'Quantity':>10} {'Unit':<10} {'Confidence':>10}")
    print("-" * 70)

    for mat in materials:
        name = mat.get('material_name', 'Unknown')[:38]
        qty = mat.get('quantity', 0)
        unit = mat.get('unit', 'N/A')[:8]
        conf = mat.get('confidence_score', 0) * 100

        print(f"{name:<40} {qty:>10.2f} {unit:<10} {conf:>9.1f}%")

    print("-" * 70)

    # Print any notes
    for mat in materials:
        if mat.get('note'):
            print(f"\n[NOTE]: {mat.get('note')}")

    # Print JSON for API response
    print("\n[JSON Response] (for Frontend API):")
    print("-" * 70)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    return report


if __name__ == "__main__":
    report = run_extraction_test()

    if report:
        # Save report to file
        output_file = os.path.join(os.path.dirname(__file__), 'docs', 'extraction_report.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Report saved to: {output_file}")
    else:
        print("\n[FAILED] Extraction failed - no report generated")
        sys.exit(1)
