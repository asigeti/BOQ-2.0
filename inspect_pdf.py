import pdfplumber

generated_pdf = r"docs\BOQ_as_20251211.pdf"

print("=== RAW GENERATED BOQ (Pages 1-5) ===")
with pdfplumber.open(generated_pdf) as pdf:
    for i, page in enumerate(pdf.pages[:5]):
        print(f"\n--- Page {i+1} ---")
        print(page.extract_text())
