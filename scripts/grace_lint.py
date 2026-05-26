import os
import re
import sys
from pathlib import Path

# ############################################################################
# AI_HEADER: GRACE_LINT
# ROLE: Automatically verify that LLM templates and platform modules comply with strict rules.
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


def lint_platform_modules(target_dir: str):
    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"Error: Target path {target_path} not found")
        sys.exit(1)

    python_files = []
    if target_path.is_file():
        python_files.append(target_path)
    else:
        python_files.extend(target_path.glob("**/*.py"))

    # Filter out empty files or __pycache__
    python_files = [
        f for f in python_files
        if f.name != "__init__.py" or f.stat().st_size > 0
    ]

    errors = []

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            content = "".join(lines)
        except Exception as e:
            errors.append(f"{file_path}: Failed to read file: {e}")
            continue

        rel_path = file_path.relative_to(target_path.parent.parent if len(target_path.parts) > 1 else target_path.parent)

        # 1. AI_HEADER check (within first 30 lines)
        header_found = False
        for line in lines[:30]:
            if "AI_HEADER" in line:
                header_found = True
                break
        if not header_found:
            errors.append(f"{rel_path}: Missing AI_HEADER banner within the first 30 lines.")

        # 2. START_MODULE_CONTRACT / END_MODULE_CONTRACT
        if "START_MODULE_CONTRACT" not in content:
            errors.append(f"{rel_path}: Missing START_MODULE_CONTRACT.")
        if "END_MODULE_CONTRACT" not in content:
            errors.append(f"{rel_path}: Missing END_MODULE_CONTRACT.")

        # 3. START_MODULE_MAP / END_MODULE_MAP
        if "START_MODULE_MAP" not in content:
            errors.append(f"{rel_path}: Missing START_MODULE_MAP.")
        if "END_MODULE_MAP" not in content:
            errors.append(f"{rel_path}: Missing END_MODULE_MAP.")

        # 4. Paired START_BLOCK / END_BLOCK
        start_blocks = content.count("START_BLOCK")
        end_blocks = content.count("END_BLOCK")
        if start_blocks != end_blocks:
            errors.append(f"{rel_path}: Unbalanced blocks. START_BLOCK count ({start_blocks}) != END_BLOCK count ({end_blocks}).")

        # 5. Prefect imports check
        prefect_imports = []
        for i, line in enumerate(lines, 1):
            if re.match(r"^\s*(import\s+prefect|from\s+prefect\b)", line):
                prefect_imports.append(i)
        if prefect_imports:
            errors.append(f"{rel_path}: Forbidden prefect imports found on lines: {prefect_imports}")

        # 6. Extract all function contracts
        # We can find blocks between START_FUNCTION_CONTRACT and END_FUNCTION_CONTRACT
        contract_matches = re.finditer(
            r"START_FUNCTION_CONTRACT\s*\n(.*?)\n\s*(?:#\s*)?END_FUNCTION_CONTRACT",
            content,
            re.DOTALL
        )

        contracted_funcs = set()
        for match in contract_matches:
            block_text = match.group(1)
            # Find function name in the block, e.g., "name: foo" or "function: foo" or "def foo"
            func_name_match = re.search(r"^\s*(?:#\s*)?(?:name|function)\s*:\s*([a-zA-Z0-9_]+)", block_text, re.MULTILINE)
            func_name = func_name_match.group(1) if func_name_match else None

            # If not explicitly named, look at the line after the match
            if not func_name:
                end_pos = match.end()
                # search for def [name] in the lines following
                following_text = content[end_pos:end_pos + 200]
                def_match = re.search(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(", following_text, re.MULTILINE)
                if def_match:
                    func_name = def_match.group(1)

            if func_name:
                contracted_funcs.add(func_name)
                # Verify required contract fields
                required_fields = ["purpose", "inputs", "returns", "side_effects", "emitted_logs", "error_behavior"]
                missing_fields = []
                for field in required_fields:
                    # Look for "field:" or "field :" (case-insensitive) in block_text
                    if not re.search(fr"^\s*(?:#\s*)?{field}\s*:", block_text, re.IGNORECASE | re.MULTILINE):
                        missing_fields.append(field)
                if missing_fields:
                    errors.append(f"{rel_path}: Function contract for '{func_name}' is missing fields: {', '.join(missing_fields)}")
            else:
                errors.append(f"{rel_path}: Found function contract block but could not associate it with a function name.")

        # 7. Find all public functions/methods defined in file
        # Check that they have a corresponding contract in contracted_funcs
        for i, line in enumerate(lines, 1):
            # Matches top-level or method defs that don't start with underscore, excluding __init__
            def_match = re.match(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(", line)
            if def_match:
                func_name = def_match.group(1)
                if not func_name.startswith("_") and func_name != "main":
                    if func_name not in contracted_funcs:
                        errors.append(f"{rel_path}: Public function/method '{func_name}' on line {i} is missing a GRACE function contract.")

    if errors:
        print("[GRACE-LINT] Strict contract verification FAILED:")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print(f"[GRACE-LINT] All modules in {target_dir} comply with GRACE Canon Script Discipline.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        lint_platform_modules(sys.argv[1])
    else:
        lint_templates()
