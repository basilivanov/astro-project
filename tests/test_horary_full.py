import requests
import time
import json

API_URL = "http://localhost:8000"
CLIENT_ID = "69dfc6d5-9d17-4c10-9796-b7b09786fc80"

def test_horary_creation():
    print("🚀 Testing Horary Report Creation...")
    
    url = f"{API_URL}/api/workflows/report/async"
    payload = {
        "client_id": CLIENT_ID,
        "report_type": "horary_answer",
        "question": "Завтра суд, могут права либо отобрать либо штраф, за пересечение двойной сплошной. Права заберут или нет?",
        "client_note": "Суд завтра",
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Telegram-Auth": "12345" # Admin bypass
    }
    
    try:
        # 1. Create Report
        print(f"📡 POST {url}")
        res = requests.post(url, json=payload, headers=headers)
        
        if res.status_code != 200:
            print(f"❌ Failed to create report: {res.status_code} {res.text}")
            return
            
        data = res.json()
        report_id = data["report_id"]
        print(f"✅ Report created: {report_id}")
        
        # 2. Poll for completion (or at least check structure)
        print("⏳ Waiting for processing...")
        time.sleep(2)
        
        # 3. Check Report Chunks structure
        chunks_url = f"{API_URL}/api/admin/reports/{report_id}?include_content=0"
        res_chunks = requests.get(chunks_url)
        chunks_data = res_chunks.json().get("chunks", [])
        chunk_ids = [c["section"] for c in chunks_data]
        
        print(f"Found chunks: {len(chunks_data)}")
        # Check for new sections
        expected = ["horary_00_passport", "horary_00_technical", "horary_01_verdict", "horary_02_radicality"]
        missing = [ex for ex in expected if ex not in chunk_ids]
        
        if missing:
            print(f"❌ Missing sections: {missing}")
            print(f"Actual chunks: {chunk_ids}")
        else:
            print("✅ All horary sections present!")
            
        # 4. Trigger generation of section 0 to verify fix
        print("⚡ Regenerating section 0 (Passport)...")
        regen_url = f"{API_URL}/api/admin/reports/{report_id}/sections/horary_00_passport/regenerate"
        res_regen = requests.post(regen_url, headers=headers)
        
        if res_regen.status_code == 200:
            print("✅ Section 0 regenerated successfully.")
            content = res_regen.json().get("sections", [{}])[0].get("content", "")
            print("📝 Content Preview:")
            print(content[:200] + "...")
        else:
            print(f"❌ Failed to regenerate section 0: {res_regen.status_code} {res_regen.text}")
            
        # 5. Trigger regeneration of section 1 (LLM)
        print("⚡ Regenerating section 1 (Verdict)...")
        regen_llm_url = f"{API_URL}/api/admin/reports/{report_id}/sections/horary_01_verdict/regenerate"
        # Note: This might be slow if LLM is called, but in fallback mode it's fast.
        # We assume fallback mode or mock if no API key.
        res_llm = requests.post(regen_llm_url, headers=headers)
        
        if res_llm.status_code == 200:
            print("✅ Section 1 regenerated successfully.")
        else:
            print(f"❌ Failed to regenerate section 1: {res_llm.status_code} {res_llm.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_horary_creation()
