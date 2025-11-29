"""
Test Israeli BOQ Generation with AutoCAD + GPT-4 + Dekel Pricing
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set OpenAI API key from backend/.env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

def test_israeli_boq():
    print("=" * 70)
    print("Israeli BOQ Generation Test")
    print("כתב כמויות ישראלי - בדיקת מערכת")
    print("=" * 70)

    test_file = r"C:\Users\asige\OneDrive\Documents\GitHub\BOQ-2.0\docs\DCRC-WP-PLG.dwg"

    if not os.path.exists(test_file):
        print(f"[ERROR] Test file not found: {test_file}")
        return

    print(f"\n[1/4] File: {os.path.basename(test_file)}")
    print(f"      Size: {os.path.getsize(test_file) / 1024 / 1024:.2f} MB")

    # Step 1: Extract raw data from AutoCAD
    print("\n[2/4] Extracting raw data from AutoCAD...")
    print("-" * 70)

    from app.services.extraction.dwg_extractor import extract_raw_data_from_dwg

    start_time = time.time()
    raw_data = extract_raw_data_from_dwg(test_file)
    extraction_time = time.time() - start_time

    print(f"\n[OK] Extraction completed in {extraction_time:.2f}s")
    print(f"     Method: {raw_data.get('extraction_method', 'unknown')}")
    print(f"     Success: {raw_data.get('extraction_success', False)}")

    if raw_data.get('extraction_success'):
        print(f"     Blocks: {len(raw_data.get('blocks', []))}")
        print(f"     Text items: {len(raw_data.get('text_entities', []))}")
        print(f"     Dimensions: {len(raw_data.get('dimensions', []))}")
        print(f"     Layers: {len(raw_data.get('layers', {}))}")
        print(f"     Total line length: {raw_data.get('geometry', {}).get('total_line_length', 0):.2f}")
        print(f"     Total area: {raw_data.get('geometry', {}).get('total_area', 0):.2f}")

        # Show some sample text
        texts = raw_data.get('text_entities', [])[:5]
        if texts:
            print("\n     Sample text items:")
            for t in texts:
                text_val = t.get('text', '')[:50]
                print(f"       - {text_val}")
    else:
        print(f"     Errors: {raw_data.get('errors', [])}")

    # Save raw data for inspection
    raw_data_file = os.path.join(os.path.dirname(test_file), 'raw_extraction_data.json')
    with open(raw_data_file, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] Raw data saved to: {raw_data_file}")

    # Check if we can proceed to BOQ generation
    if not raw_data.get('extraction_success'):
        print("\n[SKIP] Cannot generate BOQ without successful extraction")
        return

    # Step 2: Check for OpenAI API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("\n[SKIP] OPENAI_API_KEY not set - skipping BOQ generation")
        print("       Set OPENAI_API_KEY environment variable to enable GPT-4 BOQ generation")
        return

    # Step 3: Generate Israeli BOQ with GPT-4
    print("\n[3/4] Generating Israeli BOQ with GPT-4...")
    print("-" * 70)

    from app.services.boq.israeli_boq_service import IsraeliBOQService

    service = IsraeliBOQService()

    try:
        start_time = time.time()
        boq = service.generate_boq_from_raw_data(
            raw_data=raw_data,
            filename=os.path.basename(test_file),
            project_name="DCRC Water Park Project"
        )
        boq_time = time.time() - start_time

        print(f"\n[OK] BOQ generated in {boq_time:.2f}s")

        # Convert to dict for display
        boq_dict = service.boq_to_dict(boq)

        # Step 4: Display results
        print("\n[4/4] BOQ Results:")
        print("=" * 70)
        print(f"Project: {boq.project_name}")
        print(f"File: {boq.filename}")
        print(f"Date: {boq.date}")
        print("=" * 70)

        for chapter in boq.chapters:
            if chapter.items:
                print(f"\n{chapter.chapter_code} - {chapter.chapter_name_he} ({chapter.chapter_name_en})")
                print("-" * 70)
                print(f"{'Code':<12} {'Description':<30} {'Qty':>10} {'Unit':<8} {'Price':>10}")
                print("-" * 70)

                for item in chapter.items:
                    desc = item.description_he[:28] if item.description_he else item.description_en[:28]
                    print(f"{item.item_code:<12} {desc:<30} {item.quantity:>10.2f} {item.unit:<8} {item.total_price:>10.2f}")

                print(f"{'':>52} Chapter Total: {chapter.chapter_total:>10.2f}")

        print("\n" + "=" * 70)
        print(f"Subtotal:          {boq.subtotal:>15,.2f} ILS")
        print(f"VAT ({boq.vat_rate*100:.0f}%):          {boq.vat_amount:>15,.2f} ILS")
        print(f"Grand Total:       {boq.grand_total:>15,.2f} ILS")
        print("=" * 70)

        # Save BOQ
        boq_file = os.path.join(os.path.dirname(test_file), 'israeli_boq.json')
        with open(boq_file, 'w', encoding='utf-8') as f:
            json.dump(boq_dict, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVED] BOQ saved to: {boq_file}")

        # Export to Excel
        excel_file = os.path.join(os.path.dirname(test_file), 'israeli_boq.xlsx')
        service.export_to_excel(boq, excel_file)
        print(f"[SAVED] Excel export: {excel_file}")

    except Exception as e:
        print(f"\n[ERROR] BOQ generation failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n[DONE] Test complete!")


if __name__ == "__main__":
    test_israeli_boq()
