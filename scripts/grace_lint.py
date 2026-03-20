import os
import re
import sys

# ############################################################################
# AI_HEADER: GRACE_LINT
# ROLE: Automatically verify that LLM templates comply with strict rules.
# ############################################################################

def lint_templates():
    template_path = "backend/app/reporting/section_templates.py"
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found")
        sys.exit(1)
        
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    rules = [
        (r"Не выполняй собственные расчеты", "No self-calculations prohibition"),
        (r"СТРОГО JSON МАССИВ БЛОКОВ", "Strict JSON format instruction"),
        (r"Эмодзи разрешены ТОЛЬКО", "Emoji restrictions"),
        (r"КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать английские слова", "No anglicisms/latin rule")
    ]
    
    errors = []
    for pattern, desc in rules:
        if not re.search(pattern, content):
            errors.append(f"MISSING RULE: {desc}")
            
    if errors:
        print("Template compliance FAILED:")
        print("\n".join(errors))
        sys.exit(1)
    else:
        print("[GRACE-LINT] All content rules are present in templates (PROMPT COMPLIANCE VERIFIED).")

if __name__ == "__main__":
    lint_templates()