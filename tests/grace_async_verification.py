import json
import urllib.request
import time
import sys

# GRACE Async Verification Script
# PURPOSE: Simulate frontend behavior (Async + Polling).
# CONTEXT: Hits /api/workflows/report/async and polls /api/admin/reports/{id}.

API_URL = "http://localhost:8000"

def run_test():
    print("--- [GRACE] Starting Async Verification ---")

    # 1. Create Payload
    payload = {
        "client_name": "Async Tester",
        "birth_date": "1990-01-01T12:00:00",
        "birth_location": "London",
        "birth_lat": 51.5074,
        "birth_lon": -0.1278,
        "birth_timezone": "Europe/London",
        "report_type": "horary_answer",
        "question": "Will async generation work?",
        "include_fixed_stars": True,
        "llm_mode": "openrouter"
    }

    print(f"--- [PCAM] Action: POST /api/workflows/report/async ---")
    
    req = urllib.request.Request(
        f"{API_URL}/api/workflows/report/async",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            report_id = data.get("report_id")
            print(f"--- [PCAM] Started: Report ID: {report_id} ---")

            # 2. Poll for completion
            for i in range(30): # Wait up to 60 seconds
                time.sleep(2)
                status_url = f"{API_URL}/api/admin/reports/{report_id}?include_content=true"
                with urllib.request.urlopen(status_url) as status_resp:
                    report_data = json.loads(status_resp.read().decode('utf-8'))
                    status = report_data["report"]["status"]
                    chunk_count = report_data["report"]["chunk_count"]
                    
                    print(f"   > Poll {i+1}: Status={status}, Chunks={chunk_count}")
                    
                    if status == "completed":
                        print("--- [PCAM] Status: COMPLETED ---")
                        chunks = report_data["chunks"]
                        empty_chunks = [c for c in chunks if not c.get("content")]
                        
                        if empty_chunks:
                            print(f"!!! FAILURE: {len(empty_chunks)} chunks are empty! !!!")
                            sys.exit(1)
                        
                        print("--- [GRACE] Result: SUCCESS (All chunks have content) ---")
                        return
                    
                    if status == "failed":
                        print("!!! FAILURE: Report status is FAILED !!!")
                        # Try to fetch logs from docker if possible, or just exit
                        sys.exit(1)

            print("!!! FAILURE: Timeout waiting for completion !!!")
            sys.exit(1)

    except urllib.error.HTTPError as e:
        print(f"!!! FAILURE: HTTP Error {e.code} !!!")
        print(e.read().decode('utf-8'))
        sys.exit(1)
    except Exception as e:
        print(f"!!! FAILURE: Connection Error: {e} !!!")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
