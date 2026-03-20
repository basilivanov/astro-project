import requests
import json
import uuid

API_URL = "http://localhost:8000"

def test_analytics_extension():
    print("🧪 Testing Analytics Extended Schema...")
    
    payload = {
        "event_name": "landing_view",
        "telegram_id": 12345,
        "source": "test_script",
        "metadata": {"test": "true"},
        "session_id": str(uuid.uuid4()),
        "path": "/landing",
        "utm_source": "google",
        "utm_campaign": "summer_sale",
        "device": "mobile",
        "browser": "chrome"
    }
    
    try:
        res = requests.post(f"{API_URL}/api/analytics/event", json=payload)
        if res.status_code == 200:
            print("✅ Analytics event with NEW fields accepted (200 OK).")
            print(res.json())
        else:
            print(f"❌ Failed: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_analytics_extension()
