import requests
import time
import json
import sys

API_URL = "http://localhost:8000"

def verify_high_lat():
    print("🚀 Starting High Latitude & Timezone Verification...")
    
    # Create Client
    client_payload = {
        "client_name": "Vasily Ivanov HighLat",
        "birth_date": "1980-10-30T19:50:00", # Local time input
        "birth_location": "Monchegorsk",
        "birth_lat": 67.9387,
        "birth_lon": 32.9241,
        "birth_timezone": "Europe/Moscow", # Should be UTC+3 or UTC+4 in 1980
        "is_test": True
    }
    
    res = requests.post(f"{API_URL}/api/admin/clients", json=client_payload)
    if res.status_code != 200:
        print(f"❌ Client creation failed: {res.text}")
        return
    
    client_id = res.json()["id"]
    print(f"✅ Created client: {client_id}")
    
    # Create Report
    url = f"{API_URL}/api/workflows/report/async"
    payload = {
        "client_id": client_id,
        "report_type": "natal_master",
        "house_system": "Placidus", # Requesting Placidus
        "is_test": True
    }
    headers = {"X-Telegram-Auth": "12345"}
    
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code != 200:
        print(f"❌ Creation failed: {res.text}")
        return
        
    report_id = res.json()["report_id"]
    print(f"✅ Created report: {report_id}")
    
    # Poll for input_frame
    print("⏳ Waiting for input_frame generation...")
    for _ in range(15):
        time.sleep(2)
        res_check = requests.get(f"{API_URL}/api/admin/reports/{report_id}/sections/input_frame")
        if res_check.status_code == 200:
            data = res_check.json()
            if data["status"] == "completed":
                content = data.get("content")
                print(f"✅ Input Frame Generated!")
                print("-" * 20)
                print(content)
                print("-" * 20)
                
                # Check for warning
                if "Whole Sign" in content and "высоких широтах" in content:
                    print("✅ Warning about High Latitude found.")
                else:
                    print("❌ Warning MISSING!")
                    
                # Check for Timezone
                if "Часовой пояс" in content:
                    print("✅ Timezone displayed.")
                else:
                    print("❌ Timezone MISSING!")
                    
                return
        else:
            print(f"   Status: {res_check.status_code}")
            
    print("⚠️ Timed out waiting for input_frame.")

if __name__ == "__main__":
    verify_high_lat()
