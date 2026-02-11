import pdfplumber

generated_pdf = r"C:\Users\asige\Downloads\BOQ_as_20251211 (1).pdf"

with pdfplumber.open(generated_pdf) as pdf:
    print(f"Total Pages: {len(pdf.pages)}")
    for i in range(min(3, len(pdf.pages))):
        print(f"--- Page {i+1} ---")
        text = pdf.pages[i].extract_text()
        print(text)
        print("-" * 20)
        tables = pdf.pages[i].extract_tables()
        print(f"Tables found: {len(tables)}")
        for table in tables:
            for row in table:
                print(row)
