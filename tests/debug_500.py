import urllib.request
import json
import sys

API_URL = "http://localhost:8000"
HEADERS = {"X-Telegram-Auth": "123456789"}

def test():
    print("--- DEBUG 500 ---")
    
    # 1. GET (Auth check)
    print("\n1. GET /api/users/me")
    req = urllib.request.Request(f"{API_URL}/api/users/me", headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as res:
            print(f"✅ GET Success: {res.status}")
            print(res.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ GET Failed: {e.code} {e.read().decode()}")
        sys.exit(1)

    # 2. PUT (Update check)
    print("\n2. PUT /api/users/me")
    data = {
        "full_name": "Debug User",
        "birth_date": "1990-01-01"
    }
    req = urllib.request.Request(
        f"{API_URL}/api/users/me", 
        headers=HEADERS, 
        method="PUT",
        data=json.dumps(data).encode("utf-8")
    )
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as res:
            print(f"✅ PUT Success: {res.status}")
            print(res.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ PUT Failed: {e.code} {e.read().decode()}")

if __name__ == "__main__":
    test()
