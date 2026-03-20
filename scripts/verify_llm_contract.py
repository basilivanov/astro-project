import sys
import os
import re

sys.path.append(os.getcwd())

from backend.app.reporting.section_templates import RU_LANG_INSTRUCTION, JSON_FORMAT_INSTRUCTION, EMOJI_RESTRICTION

def verify_rules():
    print("Verifying LLM Content Rules...")
    
    rules = [
        (r"Не выполняй собственные расчеты", "Calculation Prohibition", RU_LANG_INSTRUCTION),
        (r"JSON", "JSON Contract", JSON_FORMAT_INSTRUCTION),
        (r"Эмодзи разрешены ТОЛЬКО", "Emoji Usage", EMOJI_RESTRICTION)
    ]
    
    all_ok = True
    for pattern, label, text in rules:
        if re.search(pattern, text, re.IGNORECASE):
            print(f"  [OK] {label} present.")
        else:
            print(f"  [FAIL] {label} MISSING!")
            all_ok = False
    
    if all_ok:
        print("\n[LLM-Contract] Compliance check PASSED.")
    else:
        print("\n[LLM-Contract] Compliance check FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    verify_rules()