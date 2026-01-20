import json
import urllib.request
import time
import sys

# GRACE Verification Script
# PURPOSE: End-to-end verification of the report workflow.
# CONTEXT: Hits the running backend via Docker.

API_URL = "http://localhost:8000"

def run_test():
    print("--- [GRACE] Starting Verification ---")

    # 1. Create Payload
    payload = {
        "client_name": "Grace Tester",
        "birth_date": "1990-01-01T12:00:00",
        "birth_location": "Moscow",
        "birth_lat": 55.7558,
        "birth_lon": 37.6173,
        "birth_timezone": "Europe/Moscow",
        "report_type": "horary_answer",
        "question": "Will this test pass?",
        "include_fixed_stars": False,
        "llm_mode": "openrouter"
    }

    print(f"--- [PCAM] Action: Sending Request to {API_URL}/api/workflows/report ---")
    
    req = urllib.request.Request(
        f"{API_URL}/api/workflows/report",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            report_id = data.get("report_id")
            sections = data.get("sections", [])
            markdown = data.get("markdown", "")

            print(f"--- [PCAM] Measure: Report ID: {report_id} ---")
            print(f"--- [PCAM] Measure: Sections Count: {len(sections)} ---")
            
            if len(sections) == 0:
                print("!!! FAILURE: No sections generated. !!!")
                sys.exit(1)
            
            for section in sections:
                print(f"  > Section [{section['section_id']}]: {len(section.get('content', ''))} chars")
                if not section.get('content'):
                    print("    !!! WARNING: Empty content !!!")

            print("\n--- [GRACE] Result: SUCCESS (Content Generated) ---")

    except urllib.error.HTTPError as e:
        print(f"!!! FAILURE: HTTP Error {e.code} !!!")
        print(e.read().decode('utf-8'))
        sys.exit(1)
    except Exception as e:
        print(f"!!! FAILURE: Connection Error: {e} !!!")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
