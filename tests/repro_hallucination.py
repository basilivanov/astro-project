import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.llm.validator import validate_llm_hallucinations

def test_hallucination_detection():
    facts = {
        "v": "facts_v1",
        "pos": [
            {"p": "Sun", "s": "Leo", "deg": 15, "h": 10},
            {"p": "Moon", "s": "Taurus", "deg": 5, "h": 7}
        ]
    }
    
    # Valid content
    valid_blocks = [
        {"type": "paragraph", "text": "Ваше Солнце во Льве дает много энергии."},
        {"type": "paragraph", "text": "Луна в Тельце ищет комфорта."}
    ]
    
    errors = validate_llm_hallucinations(valid_blocks, facts)
    if errors:
        print(f"[FAIL] Unexpected errors in valid content: {errors}")
        sys.exit(1)
    else:
        print("[OK] Valid content passed.")
        
    # Hallucinated content
    hallucinated_blocks = [
        {"type": "paragraph", "text": "Ваше Солнце в Деве приносит педантизм."}, # ERROR: Sun is in Leo
        {"type": "paragraph", "text": "Луна в Скорпионе дает страсть."} # ERROR: Moon is in Taurus
    ]
    
    errors = validate_llm_hallucinations(hallucinated_blocks, facts)
    if not errors:
        print("[FAIL] Hallucination NOT detected!")
        sys.exit(1)
    else:
        print(f"[OK] Hallucinations detected: {errors}")
        
    print("\nHallucination detection verified successfully.")

if __name__ == "__main__":
    test_hallucination_detection()
