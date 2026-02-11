import pdfplumber
import re

# File paths
generated_pdf = r"C:\Users\asige\Downloads\BOQ_asdasd_20251211.pdf"
# Reference PDF is kept for potential future use or verification, but values are hardcoded as per user provided baseline
reference_pdf = r"docs\3300-C כתב כמויות-קאנטרי רמות.pdf"

def extract_text_from_pdf(path, pages=None):
    text_content = ""
    try:
        with pdfplumber.open(path) as pdf:
            if pages:
                for p in pages:
                    if p < len(pdf.pages):
                        text_content += pdf.pages[p].extract_text() + "\n"
            else:
                for page in pdf.pages:
                    text_content += page.extract_text() + "\n"
    except Exception as e:
        return ""
    return text_content

def parse_english_number(s):
    """Parses a string like '5,611.96' to float 5611.96"""
    if not s: return 0.0
    try:
        return float(s.replace(',', ''))
    except:
        return 0.0

def get_asd_quantity(text, code):
    """
    Scans the text for lines containing the item code (e.g. '01.01.01').
    Extracts the quantity.
    In the generated PDF, lines look like:
    ₪ 252,538.34 ... 5,611.96 ... 01.01.01
    
    We need to identify which number is the Quantity.
    Usually: Total Price, Unit Price, Quantity, ...
    
    Heuristic: 
    1. Find all numbers in the line.
    2. Sort them? No.
    3. The structure seems consistent. 
       Page 3 inspect showed:
       "₪ 252,538.34 ₪ 45.00 ק"מ 5,611.96 ... 01.01.01"
       Prices have '₪'. Quantity usually doesn't, or is followed by unit like 'מ"ק'.
       
    Let's Regex for `(\d{1,3}(,\d{3})*(\.\d+)?)` followed optionally by Hebrew text.
    """
    total_qty = 0.0
    lines = text.split('\n')
    for line in lines:
        if code in line:
            # Simple heuristic: find all numbers looking like floats
            # Filter out the code itself if it looks like a number (it has dots, usually treated as string)
            # Filter out integers that are likely line numbers?
            
            # Remove the code from line to avoid parsing it
            clean_line = line.replace(code, "")
            
            # Find patterns like "1,234.56"
            matches = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', clean_line)
            
            # Logic to pick the right extracted number:
            # In "252,538.34 45.00 5,611.96" -> usually Quantity is the one that multiplies to Total.
            # But simpler: typically the Quantity is the 3rd number from the right? Or 1st?
            # Hebrew text is RTL visually but logical memory is LTR.
            # "Total UnitPrice Quantity Description Code" (Visual)
            # "Code Description Quantity UnitPrice Total" (Likely Logical for some generators)
            
            # Let's look at the inspect output again:
            # "₪ 252,538.34 ₪ 45.00 ק"מ 5,611.96 ... 01.01.01"
            # It seems the numbers appear in order: Total, Unit Price, Quantity.
            # So Quantity is likely the VALID number that is NOT the Unit Price (usually smaller, rounder) and NOT the Total (large).
            # OR we can see "5,611.96" is roughly "252538 / 45".
            
            # Let's try to harvest all floats
            nums = [parse_english_number(m) for m in matches if '.' in m]
            
            if len(nums) >= 3:
                # Based on observation, Quantity is usually the 3rd number (Total, Price, Qty)
                qty = nums[2]
                total_qty += qty
            elif len(nums) == 2:
                # If only 2 numbers found, assume Price and Qty? Or Total and Qty?
                # Usually larger is Total.
                # Heuristic: the one that is NOT price?
                # If we assume Price < Qty < Total (often true or Qty > Price).
                # Safe bet: the last number might be Quantity if the text order is Price, Qty.
                # But let's stick to the 3-number pattern which seems standard in this file.
                pass

    return total_qty

def format_number(n):
    return f"{n:,.2f}"

def format_ratio(asd, ref):
    if ref == 0: return "—"
    ratio = asd / ref
    return f"≈ {ratio:.2f}×"

def format_diff(asd, ref, unit):
    diff = asd - ref
    return f"{format_number(diff)} {unit}"

# Configuration for Comparison
# Fields: Name, ASDCode, RefCode, RefQty (Hardcoded for now), Unit
comparison_rows = [
    {
        "name": "חפירה כללית + פינוי",
        "asd_code": "01.01.01",
        "ref_code": "2.01.01.0020",
        "ref_qty": 3550.00,
        "unit": "מ״ק"
    },
    {
        "name": "מילוי חול / מצע מהודק",
        "asd_code": "01.02.01",
        "ref_code": "2.01.02.0010 + 2.01.02.0020",
        "ref_qty": 650.00,
        "unit": "מ״ק"
    },
    {
        "name": "פינוי עודפי חפירה",
        "asd_code": "01.03.01",
        "ref_code": "כלול בתוך סעיפי החפירה",
        "ref_qty": 0, # Special handling
        "unit": "מ״ק",
        "special": True 
    },
    {
        "name": "עמודי בטון מזוין",
        "asd_code": "02.02.01",
        "ref_code": "2.02.05.0070",
        "ref_qty": 1.80,
        "unit": "מ״ק"
    },
    {
        "name": "תקרות / גגות בטון",
        "asd_code": "02.03.01",
        "ref_code": "2.02.07.0010–2.02.07.0090",
        "ref_qty": 1358.50, # This is m2 in Ref, but m3 in ASD?
        "unit": "מ״ק",
        "ref_unit": "מ״ר", # Mismatch
        "mismatch": True
    },
    {
        "name": "פלדת זיון",
        "asd_code": "02.04.01",
        "ref_code": "2.02.09.0010 + ...",
        "ref_qty": 101.50,
        "unit": "טון"
    }
]


def extract_quantities_from_tables(pdf_path):
    """
    Extracts quantities from PDF tables using pdfplumber.
    Returns a dict: {code: total_quantity}
    """
    quantities = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Row structure usually: [Total, Price, Unit, Qty, Desc, Code]
                        # But might vary. We match Code first.
                        # Filter None values
                        row = [str(x) if x else "" for x in row]
                        
                        # Find code in the row (usually last or second to last)
                        code = None
                        qty = 0.0
                        
                        # Iterate to find the code in format XX.XX.XX
                        for col in row:
                            if re.match(r'^\d{2}\.\d{2}\.\d{2}$', col.strip()):
                                code = col.strip()
                                break
                        
                        if code:
                            # If code found, find the quantity.
                            # Heuristic: the column with a float value that is NOT the Unit Price or Total.
                            # Based on inspection:
                            # 0: Total (Currency)
                            # 1: Unit Price (Currency)
                            # 2: Unit (Text)
                            # 3: Quantity (Float)
                            # 4: Description
                            # 5: Code
                            
                            # Let's collect all numbers
                            nums = []
                            for col in row:
                                # cleanup currency symbols and commas
                                clean = col.replace('₪', '').replace(',', '').strip()
                                try:
                                    val = float(clean)
                                    nums.append(val)
                                except:
                                    pass
                                    
                            # Determine Qty
                            # Usually Qty is index 3 in the original row?
                            # Let's try to grab by specific index if structure is consistent.
                            if len(row) >= 6:
                                # Try index 3 specifically
                                try:
                                    val = float(row[3].replace(',', '').strip())
                                    qty = val
                                except:
                                    # Fallback to logic
                                    if len(nums) >= 3:
                                        # Total, Price, Qty -> Qty is likely the one that isn't Price/Total
                                        # Or just the 3rd number found?
                                        # In ['592,624.80', '880.00', 'qm', '673.44'] -> nums are [592624.8, 880.0, 673.44]
                                        # Qty is usually the last number before description?
                                        # Actually in the sample: Total, Price, Unit, Qty
                                        # So nums would be [Total, Price, Qty]
                                        qty = nums[2]
                            
                            if qty > 0:
                                quantities[code] = quantities.get(code, 0.0) + qty

    except Exception as e:
        print(f"Error extracting tables: {e}")
        return {}
    return quantities


# Extract ASD Quantities Map
asd_quantities = extract_quantities_from_tables(generated_pdf)

print(f"{'תחום עבודה':<25} | {'סעיף asd':<10} | {'כמות asd':<15} | {'סעיף/ים קאנטרי':<20} | {'כמות קאנטרי':<15} | {'הפרש כמות':<15} | {'יחס':<10}")
print("-" * 120)

for row in comparison_rows:
    # Get ASD Qty from Map
    asd_qty = asd_quantities.get(row['asd_code'], 0.0)
    
    # Format columns
    col_name = row['name']
    col_asd_code = row['asd_code']
    col_asd_qty = f"{format_number(asd_qty)} {row['unit']}"
    col_ref_code = row['ref_code'] if len(row['ref_code']) < 20 else row['ref_code'][:17] + "..."
    
    if row.get('special'):
        col_ref_qty = "—"
        col_diff = "—"
        col_ratio = "—"
    elif row.get('mismatch'):
        col_ref_qty = f"{format_number(row['ref_qty'])} {row.get('ref_unit')}"
        col_diff = "לא ישים"
        col_ratio = "—"
    else:
        col_ref_qty = f"{format_number(row['ref_qty'])} {row['unit']}"
        col_diff = format_diff(asd_qty, row['ref_qty'], row['unit'])
        col_ratio = format_ratio(asd_qty, row['ref_qty'])

    # Hebrew alignment in terminal is tricky, using simple tab separation for clarity or English layout
    # Reversing Hebrew for display might be needed if terminal is RTL/LTR confused, but let's stick to logical string
    print(f"{col_name:<25} | {col_asd_code:<10} | {col_asd_qty:<15} | {col_ref_code:<20} | {col_ref_qty:<15} | {col_diff:<15} | {col_ratio:<10}")

