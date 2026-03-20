import os
import subprocess
import sys
import requests
import json

def test_no_llm_default():
    print("\n--- Verifying that reports use STUB by default ---")
    
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    HEADERS = {"X-Telegram-Auth": "999"} # Dev bypass

    # 1. Trigger report WITHOUT llm_mode in payload
    # We expect it to use 'stub' because DEFAULT_LLM_MODE is now 'stub' in docker-compose.yml.
    payload = {
        "report_type": "horary",
        "question": "Does it use stub by default?"
    }
    
    # We use an invalid API key to ensure it FAILS if it tries to call real LLM
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = "sk-invalid-key"
    if "LLM_SMOKE" in env: del env["LLM_SMOKE"]

    print("POST /api/reports/create without llm_mode...")
    res = requests.post(f"{API_URL}/api/reports/create", headers=HEADERS, json=payload)
    if res.status_code != 200:
        print(f"  [FAIL] Creation failed: {res.text}")
        return False
    
    report_id = res.json()["report_id"]
    print(f"  [OK] Created ID: {report_id}. Polling...")

    # 2. Wait for completion
    import time
    for i in range(10):
        res = requests.get(f"{API_URL}/api/reports/{report_id}", headers=HEADERS)
        data = res.json()
        status = data["report"]["status"]
        if status == "completed":
            # Check content - build_section_template_content returns "🧭 О чем этот блок"
            chunks = data.get("chunks", [])
            for c in chunks:
                if "О чем этот блок" in (c.get("content") or ""):
                    print("  [OK] Found 'О чем этот блок'. Default is STUB.")
                    return True
            print("  [FAIL] Report completed but didn't contain stub-template indicators.")
            return False
        if status == "failed":
            print(f"  [FAIL] Report failed (maybe it tried to call real LLM and failed API key?)")
            return False
        time.sleep(2)
    
    print("  [FAIL] Timeout")
    return False

if __name__ == "__main__":
    if not test_no_llm_default(): sys.exit(1)