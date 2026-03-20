import json
import urllib.request
import sys
import time
import re

# CONFIGURATION
API_URL = "http://localhost:8000"
USER_ID = "123456789" # Dev bypass ID
HEADERS = {
    "Content-Type": "application/json",
    "X-Telegram-Auth": USER_ID
}

# USER DATA (Svetlana)
USER_PROFILE = {
    "full_name": "Svetlana Test",
    "birth_date": "1976-02-14",
    "birth_time": "05:30",
    "birth_time_known": True,
    "birth_place": "Khabarovsk, Russia",
    "birth_lat": 48.48,
    "birth_lon": 135.08
}

# RUSSIAN ZODIAC DECLENSIONS
ZODIAC_RU = {
    "Aries": ["Овен", "Овн"],
    "Taurus": ["Телец", "Тельц"],
    "Gemini": ["Близнецы", "Близнец"],
    "Cancer": ["Рак", "Рак"],
    "Leo": ["Лев", "Льв"],
    "Virgo": ["Дева", "Дев"],
    "Libra": ["Весы", "Вес"],
    "Scorpio": ["Скорпион", "Скорпион"],
    "Sagittarius": ["Стрелец", "Стрельц"],
    "Capricorn": ["Козерог", "Козерог"],
    "Aquarius": ["Водолей", "Водоле"],
    "Pisces": ["Рыбы", "Рыб"]
}

PLANETS_RU = {
    "Sun": "Солнце",
    "Moon": "Луна",
    "Mercury": "Меркурий",
    "Venus": "Венера",
    "Mars": "Марс",
    "Jupiter": "Юпитер",
    "Saturn": "Сатурн",
    "ASC": "Асцендент"
}

class HallucinationError(Exception):
    pass

def api_call(method, endpoint, data=None):
    url = f"{API_URL}{endpoint}"
    if data:
        encoded_data = json.dumps(data).encode("utf-8")
    else:
        encoded_data = None
        
    req = urllib.request.Request(
        url,
        data=encoded_data,
        headers=HEADERS,
        method=method
    )
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                return None
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"❌ API Error {e.code}: {e.read().decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

def check_text_for_truth(text, planet_en, sign_en):
    planet_ru = PLANETS_RU.get(planet_en, planet_en)
    sign_roots = ZODIAC_RU.get(sign_en, [sign_en])
    found_sign = False
    for root in sign_roots:
        if root.lower() in text.lower():
            found_sign = True
            break
    return found_sign

def verify_natal_content(data):
    chart = data.get("chart", {})
    sections = {s["section_id"]: s["content"] for s in data.get("sections", [])}
    
    print("   ...Verifying Natal Content...")
    
    # 1. Input Frame
    input_text = sections.get("input_frame", "")
    for planet in ["Sun", "Moon", "Mercury", "Venus", "Mars", "ASC"]:
        true_sign = None
        # Find true sign
        for p in chart.get("positions", []):
            if p["name"] == planet:
                true_sign = p["sign"]
                break
        if planet == "ASC": # Check houses if not in positions
             for h in chart.get("houses", []):
                if h["house"] == 1:
                    true_sign = h["sign"]
                    break
        
        if not true_sign: continue
        
        if not check_text_for_truth(input_text, planet, true_sign):
             raise HallucinationError(f"Input Frame missing truth: {planet} is {true_sign}")

    print("   ✅ Natal Facts Verified")

def run_flow():
    print("🚀 STARTING USER FLOW VERIFICATION 🚀")
    
    # 1. Auth & Profile
    print("\n🔹 Step 1: Onboarding (Update Profile)...")
    user = api_call("PUT", "/api/users/me", USER_PROFILE)
    print(f"   ✅ User updated: {user['full_name']} ({user['birth_date']})")
    
    # 2. Check Profile
    print("\n🔹 Step 2: Verification (Get Profile)...")
    me = api_call("GET", "/api/users/me")
    if me["birth_place"] != USER_PROFILE["birth_place"]:
        raise Exception("Profile mismatch!")
    print("   ✅ Profile confirmed.")
    
    # 3. Generate Natal Report
    print("\n🔹 Step 3: Generating Natal Report (Llama 3.3 70B)...")
    payload = {
        "client_name": me["full_name"],
        "birth_date": f"{me['birth_date']}T{me['birth_time']}",
        "birth_location": me["birth_place"],
        "birth_lat": me["birth_lat"],
        "birth_lon": me["birth_lon"],
        "report_type": "natal_master",
        "llm_mode": "openrouter"
    }
    
    start_t = time.time()
    report = api_call("POST", "/api/workflows/report", payload)
    duration = time.time() - start_t
    print(f"   ✅ Report Generated in {duration:.2f}s")
    
    # 4. Verify Hallucinations
    print("\n🔹 Step 4: Fact Checking...")
    try:
        verify_natal_content(report)
    except HallucinationError as e:
        print(f"   💀 HALLUCINATION: {e}")
        sys.exit(1)
        
    print("\n🏆 USER FLOW VERIFIED SUCCESSFULLY.")

if __name__ == "__main__":
    run_flow()
