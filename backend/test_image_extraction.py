import os
from pypdf import PdfReader

def test_image_extraction():
    pdf_path = os.path.join("uploads", "רחוב קקל בניית מדכה.pdf")
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    reader = PdfReader(pdf_path)
    print(f"Processing {pdf_path} with {len(reader.pages)} pages...")

    for i, page in enumerate(reader.pages):
        count = 0
        for image_file_object in page.images:
            print(f"Page {i+1}: Found image {image_file_object.name} ({len(image_file_object.data)} bytes)")
            count += 1
        
        if count == 0:
            print(f"Page {i+1}: No images found.")

if __name__ == "__main__":
    test_image_extraction()
