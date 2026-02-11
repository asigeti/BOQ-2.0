import requests
import time
import sys

PROJECT_ID = 96
API_URL = f"http://localhost:7000/projects/{PROJECT_ID}"

print(f"Polling completion status for Project {PROJECT_ID}...")
start_time = time.time()

while True:
    try:
        if time.time() - start_time > 120:  # 2 min timeout
            print("Timeout waiting for completion.")
            break

        response = requests.get(API_URL)
        if response.status_code == 200:
            project = response.json()
            status = project.get("processing_status")
            progress = project.get("processing_progress")
            
            sys.stdout.write(f"\rStatus: {status} ({progress}%)   ")
            sys.stdout.flush()

            if status in ["completed", "failed", "extracted"]:
                print(f"\nFinished with status: {status}")
                sys.exit(0)
        
        time.sleep(2)
    except Exception as e:
        print(f"\nError: {e}")
        time.sleep(2)
