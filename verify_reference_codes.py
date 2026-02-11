import pdfplumber
import re

reference_pdf = r"docs\3300-C כתב כמויות-קאנטרי רמות.pdf"

target_codes = [
    "2.01.01.0020",
    "2.01.02.0010",
    "2.01.02.0020",
    "2.02.05.0070",
    "2.02.07.0010", 
    "2.02.09.0010"
]

print(f"Searching for codes in {reference_pdf}...")

with pdfplumber.open(reference_pdf) as pdf:
    for page in pdf.pages[:30]: # Search first 30 pages
        text = page.extract_text()
        if not text: continue
        for code in target_codes:
            if code in text:
                print(f"Valid match found code {code} on page {page.page_number}")
                # Try to print the line containing the code
                for line in text.split('\n'):
                     if code in line:
                         print(f"  Line: {line}")
