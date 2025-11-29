import os
import sys
import time
from dotenv import load_dotenv

# Load env vars from backend/.env
load_dotenv(os.path.join("backend", ".env"))

from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_upload_and_extract_flow():
    print("Starting E2E Test: Upload -> Extract -> View")
    
    # 1. Upload File
    pdf_path = os.path.join("backend", "uploads", "רחוב קקל בניית מדכה.pdf")
    if not os.path.exists(pdf_path):
        print(f"Error: Test file not found at {pdf_path}")
        return

    with open(pdf_path, "rb") as f:
        response = client.post(
            "/plans/upload",
            files={"file": ("test_plan.pdf", f, "application/pdf")}
        )
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return
    
    plan_data = response.json()
    plan_id = plan_data["id"]
    print(f"Upload successful. Plan ID: {plan_id}")

    # 2. Trigger Processing (if not auto-triggered, but usually it is or we poll)
    # Assuming the backend starts processing automatically or we need to poll status
    
    # 3. Poll Status
    max_retries = 30
    for i in range(max_retries):
        response = client.get(f"/plans/{plan_id}/status")
        if response.status_code != 200:
            print(f"Poll failed: {response.text}")
            time.sleep(2)
            continue
            
        data = response.json()
        status = data["status"]
        progress = data["progress"]
        
        print(f"Poll {i+1}: Status={status}, Progress={progress}%")
        
        if status == "completed":
            print("Processing completed successfully!")
            break
        elif status == "failed":
            print("Processing failed!")
            return
        
        time.sleep(2)
    else:
        print("Timeout waiting for processing to complete.")
        return

    # 4. Verify Results
    response = client.get(f"/plans/{plan_id}/quantities")
    if response.status_code != 200:
        print(f"Failed to get materials: {response.text}")
        return
        
    materials = response.json()
    print(f"Extracted Materials Count: {len(materials)}")
    print("Materials Sample:", materials[:3])

    # 5. Test Auth & Optimization Features
    print("\nTesting Auth & Optimization Features...")
    
    # Login
    login_data = {
        "username": "admin@example.com",
        "password": "password"
    }
    response = client.post("/login/access-token", data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # Supply Chain
    # Note: supply-chain endpoint expects plan_id in body: {"plan_id": 1}
    response = client.post("/optimization/supply-chain", json={"plan_id": plan_id}, headers=headers)
    if response.status_code != 200:
        print(f"Supply Chain failed: {response.text}")
    else:
        recommendations = response.json()
        print(f"Supply Chain Recommendations: {len(recommendations)}")

    # Weather
    response = client.get("/optimization/weather?location=Tel%20Aviv", headers=headers)
    if response.status_code != 200:
        print(f"Weather failed: {response.text}")
    else:
        weather = response.json()
        print(f"Weather Forecast for {weather['location']}: {len(weather['forecast'])} days")


if __name__ == "__main__":
    test_upload_and_extract_flow()
