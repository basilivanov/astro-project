import json
import os
import re
import requests
import time

API_URL = "http://localhost:8000"
CLIENT_ID = "c163b256-5a75-4ea5-97a1-077b3c4b4149"

def verify_full_content():
    print("🚀 Starting Full Content Verification...")
    
    # 1. Create Report
    url = f"{API_URL}/api/workflows/report/async"
    payload = {
        "client_id": CLIENT_ID,
        "report_type": "horary_answer",
        "question": "Завтра суд, могут права либо отобрать либо штраф, за пересечение двойной сплошной. Права заберут или нет?",
        "client_note": "Суд завтра"
    }
    llm_mode = (os.getenv("LLM_MODE") or "").strip().lower()
    if llm_mode:
        payload["llm_mode"] = llm_mode
    headers = {"X-Telegram-Auth": "12345"}
    
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code != 200:
        print(f"❌ Creation failed: {res.text}")
        return
        
    report_id = res.json()["report_id"]
    print(f"✅ Created report: {report_id}")
    
    # 2. Poll until complete
    print("⏳ Waiting for generation...")
    for _ in range(30): # Wait up to 60s
        time.sleep(2)
        res_check = requests.get(f"{API_URL}/api/admin/reports/{report_id}?include_content=1")
        data = res_check.json()
        chunks = data.get("chunks", [])
        
        # Check if all completed
        pending = [c for c in chunks if c["status"] in ["pending", "in_progress"]]
        if not pending and len(chunks) > 0:
            print("✅ Generation complete!")
            break
        print(f"   Pending: {len(pending)}/{len(chunks)}")
    else:
        print("⚠️ Generation timed out, checking what we have...")

    # 3. Print Content of EACH section
    print("\n" + "="*50)
    print("🔎 SECTION CONTENT REVIEW")
    print("="*50)
    
    def parse_blocks(raw: str) -> list:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(data, list):
            return data
        return []

    def flatten_blocks(blocks: list) -> str:
        parts = []
        for block in blocks:
            b_type = block.get("type")
            if b_type == "header":
                parts.append(str(block.get("text", "")))
            elif b_type == "paragraph":
                parts.append(str(block.get("text", "")))
            elif b_type == "list":
                parts.extend([str(i) for i in block.get("items", [])])
            elif b_type == "callout":
                parts.append(str(block.get("title", "")))
                parts.append(str(block.get("content", "")))
            elif b_type == "table":
                parts.extend([str(c.get("header", "")) for c in block.get("columns", [])])
                for row in block.get("rows", []):
                    parts.extend([str(cell) for cell in row])
            elif b_type == "key_value":
                for item in block.get("items", []):
                    parts.append(str(item.get("key", "")))
                    parts.append(str(item.get("value", "")))
        return " ".join(parts)

    for chunk in chunks:
        section_id = chunk["section"]
        content = chunk.get("content", "")
        
        print(f"\n🔹 SECTION: {section_id}")
        if not content:
            print("❌ EMPTY CONTENT!")
            continue
            
        blocks = parse_blocks(content)
        text = flatten_blocks(blocks) if blocks else content

        # Check for forbidden words
        forbidden = [
            "Mars", "Moon", "Saturn", "Jupiter", "Venus", "Mercury", "Sun",
            "Aquarius", "Pisces", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aries",
            "overthinking", "dumping", "background", "vibe", "administrative",
        ]
        found_forbidden = [w for w in forbidden if w in text]
        
        if found_forbidden:
            print(f"⚠️ FOUND ENGLISH/BAD TERMS: {found_forbidden}")

        if re.search(r"(ключевой фокус|потенциал и ресурс|риск и зона внимания)", text.lower()):
            print("⚠️ FOUND TEMPLATE TAIL PHRASES")
            
        print("-" * 20)
        # Print first 300 chars to check structure
        preview = text[:300].strip()
        print(preview + "...")
        print("-" * 20)

if __name__ == "__main__":
    verify_full_content()
