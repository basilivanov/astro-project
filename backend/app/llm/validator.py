# ############################################################################
# AI_HEADER: MODULE_LLM_VALIDATOR
# ROLE: Validate LLM output against calculated facts to prevent hallucinations.
# ############################################################################

import re
import json
from typing import List, Dict, Any

PLANET_MAP = {
    "солнце": "Sun", "луна": "Moon", "меркурий": "Mercury", "венера": "Venus",
    "марс": "Mars", "юпитер": "Jupiter", "сатурн": "Saturn", "уран": "Uranus",
    "нептун": "Neptune", "плутон": "Pluto", "хирон": "Chiron", "лилит": "Lilith"
}

SIGN_MAP = {
    "овен": "Aries", "телец": "Taurus", "близнецы": "Gemini", "рак": "Cancer",
    "лев": "Leo", "дева": "Virgo", "весы": "Libra", "скорпион": "Scorpio",
    "стрелец": "Sagittarius", "козерог": "Capricorn", "водолей": "Aquarius", "рыбы": "Pisces"
}

SIGN_VARIANTS = {
    "Aries": ["овен", "овне"],
    "Taurus": ["телец", "тельце"],
    "Gemini": ["близнецы", "близнецах"],
    "Cancer": ["рак", "раке"],
    "Leo": ["лев", "льве"],
    "Virgo": ["дева", "деве"],
    "Libra": ["весы", "весах"],
    "Scorpio": ["скорпион", "скорпионе"],
    "Sagittarius": ["стрелец", "стрельце"],
    "Capricorn": ["козерог", "козероге"],
    "Aquarius": ["водолей", "водолее"],
    "Pisces": ["рыбы", "рыбах"]
}

def validate_llm_hallucinations(blocks: List[Dict], facts: Dict) -> List[str]:
    """
    # PURPOSE: Check if LLM output contradicts calculated facts.
    # INPUT: blocks (list of block dicts), facts (facts_v1 dict).
    # OUTPUT: List of error messages (empty if valid).
    """
    errors = []
    if not blocks or not facts:
        return []
    
    # 1. Flatten all text from blocks
    all_text = ""
    for b in blocks:
        if not isinstance(b, dict): continue
        b_type = b.get("type")
        if b_type in ["paragraph", "text"]: all_text += str(b.get("text", "")) + " "
        elif b_type == "header": all_text += str(b.get("text", "")) + " "
        elif b_type == "list": all_text += " ".join([str(i) for i in b.get("items", [])]) + " "
        elif b_type == "callout": all_text += str(b.get("title", "")) + " " + str(b.get("content", "")) + " "
    
    all_text = all_text.lower()
    
    # 2. Check Planet-Sign combinations
    pos_data = {p["p"]: p["s"] for p in facts.get("pos", [])}
    
    for ru_p, en_p in PLANET_MAP.items():
        if ru_p in all_text:
            # Found planet mention. Look for signs in a small window forward.
            for match in re.finditer(re.escape(ru_p), all_text):
                # Look mostly forward, usually "Planet in Sign"
                start = match.start()
                end = min(len(all_text), match.end() + 30) # Reduced from 60 to 30
                window = all_text[start:end]
                
                for en_s, variants in SIGN_VARIANTS.items():
                    if any(v in window for v in variants):
                        # Sign mentioned near planet. Validate.
                        actual_s = pos_data.get(en_p)
                        if actual_s and actual_s != en_s:
                            errors.append(f"Hallucination: {en_p} mentioned in {en_s}, but actually in {actual_s}")
                            # Break inner loop once a sign is matched for this occurrence
                            break
                            
    return list(set(errors)) # Unique errors
