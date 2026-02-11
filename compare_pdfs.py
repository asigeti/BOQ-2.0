import pdfplumber
import os

generated_pdf = r"docs\BOQ_as_20251211.pdf"
reference_pdf = r"docs\3300-C כתב כמויות-קאנטרי רמות.pdf"

def extract_boq_items(pdf_path, label):
    print(f"\n=== {label} ITEMS (01 & 02) ===")
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check first 20 pages as early chapters are usually there
            for i, page in enumerate(pdf.pages[:20]):
                text = page.extract_text()
                if not text: continue
                
                lines = text.split('\n')
                for line in lines:
                    # Look for specific chapter starts 01 or 02
                    # In Hebrew PDF, text might be reversed, so 01.01 might appear as 10.10 or scattered
                    # We'll just look for substrings strictly
                    if "01.01" in line or "01.02" in line or "02.01" in line or "02.02" in line:
                         print(f"[P{i+1}] {line}")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

extract_boq_items(generated_pdf, "GENERATED BOQ")
extract_boq_items(reference_pdf, "REFERENCE BOQ")
