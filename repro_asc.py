from stellium_engine import StelliumEngine
from stellium import ChartBuilder
from datetime import datetime

def check_asc(time_str, label, tz=None):
    engine = StelliumEngine()
    loc = {"latitude": 67.9387, "longitude": 32.9241, "name": "Monchegorsk"}
    if tz: loc["timezone"] = tz
    
    chart = engine.create_natal_chart("Test", time_str, loc)
    
    asc = next(p for p in chart.positions if p.name == "ASC")
    
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    sign_idx = int(asc.longitude // 30)
    deg = asc.longitude % 30
    
    print(f"[{label}] Time: {time_str} TZ: {tz} -> ASC: {signs[sign_idx]} {deg:.2f}°")

# 1. As reported (19:50 UTC)
check_asc("1980-10-30T19:50:00+00:00", "19:50 UTC", "UTC")

# 2. Local 19:50 MSK
check_asc("1980-10-30T19:50:00", "19:50 Local", "Europe/Moscow")