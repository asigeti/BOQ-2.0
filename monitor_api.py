import requests
import time
import sys

API_URL = "http://localhost:7000/projects/"
LAST_KNOWN_ID = 95

print(f"Monitoring API for projects with ID > {LAST_KNOWN_ID}...")
print("Press Ctrl+C to stop manually (timeout in 60s).")

start_time = time.time()
while True:
    try:
        if time.time() - start_time > 60:
            print("Timeout: No new project detected in 60 seconds.")
            break

        response = requests.get(API_URL)
        if response.status_code == 200:
            projects = response.json()
            # Sort by ID descending
            projects.sort(key=lambda x: x['id'], reverse=True)
            
            if projects:
                latest = projects[0]
                if latest['id'] > LAST_KNOWN_ID:
                    print(f"\n[DETECTED] New Project Found!")
                    print(f"ID: {latest['id']}")
                    print(f"Name: {latest['name']}")
                    print(f"Status: {latest['processing_status']}")
                    print(f"Progress: {latest['processing_progress']}%")
                    sys.exit(0)
                else:
                    print(f".", end="", flush=True)
            else:
                print(f"?", end="", flush=True)
        else:
            print(f"!", end="", flush=True)

        time.sleep(2)
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
