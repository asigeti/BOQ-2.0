import pdfplumber
import re

generated_pdf = r"docs\BOQ_as_20251211.pdf"

print("--- Scanning for all 02.02.xx items ---")
with pdfplumber.open(generated_pdf) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text: continue
        # Regex to find codes like 02.02.xx
        matches = re.finditer(r'(02\.02\.\d{2})', text)
        for m in matches:
            code = m.group(1)
            # Get the line
            line_start = text.rfind('\n', 0, m.start()) + 1
            line_end = text.find('\n', m.end())
            line = text[line_start:line_end] if line_end != -1 else text[line_start:]
            print(f"Found {code}: {line}")

print("\n--- Testing Table Extraction on Page 3 ---")
with pdfplumber.open(generated_pdf) as pdf:
    p3 = pdf.pages[2] # Page 3 (0-indexed 2)
    tables = p3.extract_tables()
    for i, table in enumerate(tables):
        print(f"Table {i}:")
        for row in table:
            print(row)
