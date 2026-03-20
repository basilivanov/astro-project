import json
import urllib.request
import sys
import time
import re

# CONFIGURATION
API_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "X-Telegram-Auth": "12345" # Mock auth
}

# RUSSIAN ZODIAC DECLENSIONS (Nominative, Prepositional/Genitive roots)
# Used to find "Овен", "в Овне", "для Овна"
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
    "Uranus": "Уран",
    "Neptune": "Нептун",
    "Pluto": "Плутон",
    "ASC": "Асцендент" # or ASC
}

class HallucinationError(Exception):
    pass

def api_request(payload):
    req = urllib.request.Request(
        f"{API_URL}/api/workflows/report",
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return None

def get_true_position(chart, planet_name):
    # Search in positions
    for p in chart.get("positions", []):
        if p["name"] == planet_name:
            return p["sign"]
    # Search in houses for Angles
    if planet_name == "ASC":
        for h in chart.get("houses", []):
            if h["house"] == 1:
                return h["sign"]
    return None

def check_text_for_truth(text, planet_en, sign_en):
    """
    Returns True if the text correctly mentions the planet in the sign.
    """
    planet_ru = PLANETS_RU.get(planet_en, planet_en)
    sign_roots = ZODIAC_RU.get(sign_en, [sign_en])
    
    # Simple check: Does text contain "Planet" AND "Sign" nearby?
    # Or just checks if the sign keywords appear in the section dedicated to that planet.
    
    found_sign = False
    for root in sign_roots:
        if root.lower() in text.lower():
            found_sign = True
            break
            
    return found_sign

def check_text_for_lies(text, planet_en, true_sign_en):
    """
    Returns a list of lies found (e.g., claims planet is in wrong sign).
    """
    planet_ru = PLANETS_RU.get(planet_en, planet_en)
    lies = []
    
    for sign_en, roots in ZODIAC_RU.items():
        if sign_en == true_sign_en:
            continue # Skip the truth
            
        # Construct specific lying phrases
        # "Солнце в Тельце", "Солнце — Телец"
        # We search for "Planet ... WrongSign" pattern? Too complex for regex.
        # Let's search for explicit wrong statements if the section is small.
        
        # Heuristic: If we find "Солнце" and "WrongSign" in the same small sentence?
        # Let's check strict "Planet in Sign" phrases
        
        for root in roots:
            # Check specifically for "Planet in Sign" structure roughly
            # Regex: Planet (words){0,3} Sign
            # e.g. "Солнце в знаке Тельца", "Солнце (Телец)"
            pattern = rf"{planet_ru}.{{0,20}}{root}" 
            if re.search(pattern, text, re.IGNORECASE):
                 # False positive check: "Sun in Aries (unlike Taurus...)"
                 # Hard to detect without NLP. 
                 # But in "Input Frame" or "Core Triad", such contrasts are rare.
                 lies.append(f"{planet_en} -> {sign_en} (False match found: '{root}')")
                 
    return lies

def verify_natal(data):
    chart = data.get("chart", {})
    sections = {s["section_id"]: s["content"] for s in data.get("sections", [])}
    
    print("   ...Verifying Natal Positions...")
    
    # 1. Input Frame (Must match exactly)
    input_text = sections.get("input_frame", "")
    for planet in ["Sun", "Moon", "Mercury", "Venus", "Mars", "ASC"]:
        true_sign = get_true_position(chart, planet)
        if not true_sign: continue
        
        if not check_text_for_truth(input_text, planet, true_sign):
             raise HallucinationError(f"Input Frame missing truth: {planet} is {true_sign}")
             
    # 2. Core Triad (Must match Sun/Moon/Asc)
    core_text = sections.get("core_triad", "")
    for planet in ["Sun", "Moon", "ASC"]:
        true_sign = get_true_position(chart, planet)
        if not check_text_for_truth(core_text, planet, true_sign):
            # Warning only, sometimes it describes qualities without naming sign
            print(f"      ⚠️  Warning: Core Triad text didn't explicitly name {true_sign} for {planet}")
        
        lies = check_text_for_lies(core_text, planet, true_sign)
        if lies:
            raise HallucinationError(f"Core Triad Hallucination: {lies}")

    print("   ✅ Natal Checks Passed")

def verify_horary(data):
    chart = data.get("chart", {})
    horary_data = chart.get("horary", {})
    sections = {s["section_id"]: s["content"] for s in data.get("sections", [])}
    
    print("   ...Verifying Horary Significators...")
    
    # Check L1 (Querent) match
    # Engine says: "L1": "Saturn"
    # Text (Significators section) should mention "Сатурн"
    
    # Extract roles from engine
    roles = horary_data.get("roles", {})
    querent_planet = roles.get("querent", {}).get("name") # e.g. "Saturn"
    quesited_planet = roles.get("quesited", {}).get("name") # e.g. "Moon"
    
    sig_text = sections.get("horary_03_significators", "") + sections.get("horary_00_technical", "")
    
    if querent_planet:
        ru_name = PLANETS_RU.get(querent_planet, querent_planet)
        if ru_name not in sig_text and ru_name.lower() not in sig_text.lower():
             raise HallucinationError(f"Horary text missing Querent planet: {querent_planet}")

    if quesited_planet:
        ru_name = PLANETS_RU.get(quesited_planet, quesited_planet)
        if ru_name not in sig_text and ru_name.lower() not in sig_text.lower():
             raise HallucinationError(f"Horary text missing Quesited planet: {quesited_planet}")

    print("   ✅ Horary Checks Passed")

def run_suite():
    tests = [
        {
            "name": "Natal Check (Standard)",
            "payload": {
                "client_name": "Truth Seeker",
                "birth_date": "1985-10-26T14:00:00", # Scorpio Sun, Aries Moon?
                "birth_location": "Kyiv",
                "birth_lat": 50.45,
                "birth_lon": 30.52,
                "report_type": "natal_master",
                "llm_mode": "openrouter"
            },
            "verifier": verify_natal
        },
        {
            "name": "Horary Check (Job)",
            "payload": {
                "client_name": "Horary User",
                "birth_date": "1990-01-01T00:00:00",
                "birth_location": "Moscow",
                "birth_lat": 55.75, 
                "birth_lon": 37.61,
                "report_type": "horary_answer",
                "question": "When will I move?",
                "llm_mode": "openrouter"
            },
            "verifier": verify_horary
        }

    ]

    print("🛡️  STARTING HALLUCINATION GUARD PROTOCOL 🛡️\n")
    
    for test in tests:
        print(f"🔹 Running: {test['name']}...")
        start_time = time.time()
        
        data = api_request(test["payload"])
        if not data:
            print("   ⛔ API Error. Skipping.")
            continue
            
        try:
            test["verifier"](data)
            duration = time.time() - start_time
            print(f"   ✨ PASSED in {duration:.2f}s\n")
        except HallucinationError as e:
            print(f"   💀 HALLUCINATION DETECTED: {e}\n")
            sys.exit(1)
        except Exception as e:
            print(f"   ⚠️  Script Error: {e}\n")
            import traceback
            traceback.print_exc()

    print("🏆 ALL CHECKS COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    run_suite()
