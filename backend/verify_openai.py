import os
import sys
from dotenv import load_dotenv

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

# Load env vars
load_dotenv()

from app.services.extraction.pdf_extractor import extract_from_pdf
from app.core.config import settings

def test_extraction():
    print(f"Checking OpenAI API Key: {'Found' if settings.OPENAI_API_KEY else 'Missing'}")
    
    pdf_path = os.path.join("uploads", "רחוב קקל בניית מדכה.pdf")
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    print(f"Testing extraction on: {pdf_path}")
    try:
        results = extract_from_pdf(pdf_path)
        print("Extraction Results:")
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    test_extraction()
