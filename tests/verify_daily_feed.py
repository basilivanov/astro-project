import requests
import sys
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_AUTH = os.getenv("X_TELEGRAM_AUTH", "999")
HEADERS = {"X-Telegram-Auth": TEST_AUTH}

def verify_daily():
    print("\n--- Verifying Daily Feed ---")
    # 1. Update Profile first to ensure birth data exists for feed
    profile_payload = {
        "full_name": "Daily Tester",
        "birth_date": "1990-01-01",
        "birth_place": "Moscow",
        "birth_lat": 55.75,
        "birth_lon": 37.61,
        "current_timezone": "Europe/Moscow"
    }
    requests.put(f"{API_URL}/api/users/me", headers=HEADERS, json=profile_payload)

    res = requests.get(f"{API_URL}/api/feed/today", headers=HEADERS)
    if res.status_code != 200:
        print(f"  [FAIL] {res.status_code} {res.text}")
        return False
    
    data = res.json()
    print("  [OK] Feed response received.")
    
    # Check for keywords that might indicate failure or English
    text = str(data).lower()
    if "error" in text or "failed" in text or "ошибка" in text:
        # Check if it's just 'error_message: null' which is fine
        if '"error_message":null' not in text.replace(" ", ""):
            print(f"  [FAIL] Error keywords found in response: {data}")
            return False
    
    # Simple check for English words (heuristic)
    # Be careful not to match technical keys like 'type', 'id'
    # I'll check only values if possible, but for simplicity I'll just check for ' the ' and ' and '
    if " the " in text or " and " in text:
        print(f"  [FAIL] English words detected in feed: {data}")
        return False
        
    print("  [OK] Daily feed verified!")
    return True

if __name__ == "__main__":
    if not verify_daily(): sys.exit(1)
