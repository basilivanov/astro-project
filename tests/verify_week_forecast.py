import requests
import time
import sys
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_AUTH = os.getenv("X_TELEGRAM_AUTH", "999")
HEADERS = {"X-Telegram-Auth": TEST_AUTH}

def verify_week():
    print("\n--- Verifying Week Forecast (real OpenRouter) ---")
    payload = {
        "report_type": "week_forecast",
        "llm_mode": "openrouter"
    }
    res = requests.post(f"{API_URL}/api/reports/create", headers=HEADERS, json=payload)
    if res.status_code != 200:
        print(f"  [FAIL] {res.status_code} {res.text}")
        return False
    rid = res.json()["report_id"]
    for i in range(60):
        data = requests.get(f"{API_URL}/api/reports/{rid}", headers=HEADERS).json()
        status = data["report"]["status"]
        print(f"    Attempt {i+1}: {status}")
        if status == "completed":
            errors = [c["section"] for c in data.get("chunks", []) if "Ошибка генерации" in (c.get("content") or "")]
            if errors:
                print(f"  [FAIL] Fallbacks: {errors}")
                return False
            print("  [OK] Success!")
            return True
        if status == "failed":
            print(f"  [FAIL] {data['report'].get('error_message')}")
            return False
        time.sleep(5)
    return False

if __name__ == "__main__":
    if not verify_week(): sys.exit(1)