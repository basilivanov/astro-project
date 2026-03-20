import requests
import time
import sys
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_AUTH = os.getenv("X_TELEGRAM_AUTH", "999")
HEADERS = {"X-Telegram-Auth": TEST_AUTH}

def generate_natal(i):
    print(f"Natal {i}: Starting...")
    payload = {
        "report_type": "natal_master",
        "llm_mode": "openrouter"
    }
    
    start_time = time.time()
    res = requests.post(f"{API_URL}/api/reports/create", json=payload, headers=HEADERS)
    if res.status_code != 200:
        print(f"Natal {i}: [FAIL] Create status {res.status_code} {res.text}")
        return None, 0
    data = res.json()
    report_id = data["report_id"]
    
    while True:
        res = requests.get(f"{API_URL}/api/reports/{report_id}", headers=HEADERS)
        if res.status_code != 200:
            print(f"Natal {i}: [WARN] Poll status {res.status_code}")
            time.sleep(5)
            continue
        data = res.json()
        status = data["report"]["status"]
        if status == "completed":
            duration = time.time() - start_time
            section_count = len(data.get("chunks", []))
            print(f"Natal {i}: [OK] Finished in {duration:.1f}s (Sections: {section_count})")
            return duration, section_count
        if status == "failed":
            print(f"Natal {i}: [FAIL] Error: {data['report'].get('error_message')}")
            return None, 0
        time.sleep(5)

def main():
    # Sequential 5 runs
    durations = []
    total_sections = 0
    for i in range(1, 6):
        d, s = generate_natal(i)
        if d: 
            durations.append(d)
            total_sections += s
    
    if durations:
        avg = sum(durations) / len(durations)
        print(f"\n--- BENCHMARK SUMMARY ---")
        print(f"Average Duration: {avg:.1f}s")
        print(f"Total Successful Runs: {len(durations)}")
        print(f"Total Sections Generated: {total_sections}")
        print(f"--------------------------")
    else:
        print("\nNo successful runs.")

if __name__ == "__main__":
    main()
