import requests
import json
import os

API_URL = "http://127.0.0.1:8000"
ADMIN_ID = "123456789"

def check_api():
    print(f"Checking API at {API_URL} with ADMIN_ID {ADMIN_ID}")
    try:
        headers = {"X-Telegram-Auth": ADMIN_ID, "Accept": "application/json"}
        
        # Check Clients List
        print(f"GET {API_URL}/api/admin/clients")
        res = requests.get(f"{API_URL}/api/admin/clients", headers=headers)
        if res.status_code == 200:
            data = res.json()
            print(f"API CHECK: Clients List OK ({len(data)} items)")
        else:
            print(f"API CHECK FAILED: {res.status_code} {res.reason}")
            print(f"Response Body: {res.text}")
            exit(1)
            
        # Check Stats
        print(f"GET {API_URL}/api/admin/stats")
        res_stats = requests.get(f"{API_URL}/api/admin/stats", headers=headers)
        if res_stats.status_code == 200:
            stats = res_stats.json()
            print(f"API CHECK: Stats OK (Clients: {stats.get('clients')})")
        else:
            print(f"API CHECK FAILED: {res_stats.status_code} {res_stats.reason}")
            print(f"Response Body: {res_stats.text}")
            exit(1)
            
    except Exception as e:
        print(f"API CHECK FAILED: {e}")
        exit(1)

if __name__ == "__main__":
    check_api()
