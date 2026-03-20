import urllib.request
import json
import uuid

API_URL = "http://localhost:8000"

def create_test_client():
    payload = {
        "client_name": f"Test Client {uuid.uuid4().hex[:4]}",
        "birth_date": "1990-01-01T12:00:00",
        "birth_location": "Moscow",
        "birth_lat": 55.75,
        "birth_lon": 37.61,
        "birth_timezone": "Europe/Moscow",
        "is_test": True
    }
    
    req = urllib.request.Request(
        f"{API_URL}/api/admin/clients",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            if res.status == 200:
                data = json.loads(res.read().decode())
                print(f"SUCCESS: Created client {data['id']} - {data['full_name']}")
                return data['id']
            else:
                print(f"FAILED: Status {res.status}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    create_test_client()
