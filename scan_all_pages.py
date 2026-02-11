import pdfplumber
import re

generated_pdf = r"docs\BOQ_as_20251211.pdf"

target_codes = ["02.02.01", "02.04.01"]

print(f"Scanning {generated_pdf} for {target_codes}...")

with pdfplumber.open(generated_pdf) as pdf:
    print(f"Total Pages: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text: continue
        for code in target_codes:
            if code in text:
                print(f"\n--- Found {code} on Page {i+1} ---")
                lines = text.split('\n')
                for line in lines:
                    if code in line:
                         print(f"Line: {line}")
