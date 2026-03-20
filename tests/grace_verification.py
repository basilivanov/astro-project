import requests
import json
import time

API_URL = "http://localhost:8000"
REPORT_ID = "2c2fd927-0306-4538-8a24-7310131efb51"

def verify_chunks():
    print(f"🚀 Verifying Chunks for Report {REPORT_ID}...")
    
    url = f"{API_URL}/api/admin/reports/{REPORT_ID}?include_content=0"
    print(f"📡 Getting report from {url}...")
    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            chunks = data.get('chunks', [])
            chunk_ids = [c['section'] for c in chunks]
            
            print(f"Found {len(chunks)} chunks.")
            print(f"Chunks: {chunk_ids}")
            
            if "executive_summary" in chunk_ids:
                print("✅ executive_summary FOUND.")
            else:
                print("❌ executive_summary NOT FOUND.")
                
            if "technical_appendix" in chunk_ids:
                print("✅ technical_appendix FOUND.")
            else:
                print("❌ technical_appendix NOT FOUND.")
                
        else:
            print(f"❌ API Error: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    verify_chunks()
