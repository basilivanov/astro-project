# ############################################################################
# AI_HEADER: MODULE_TEST_VALIDATOR
# ROLE: Unit test for Hallucination Validator.
# ############################################################################

import pytest
from backend.app.llm.validator import validate_llm_hallucinations

def test_validator_detects_mismatch():
    facts = {
        "pos": [
            {"p": "Sun", "s": "Aries", "deg": 10},
            {"p": "Moon", "s": "Taurus", "deg": 5}
        ]
    }
    
    # 1. Valid text
    blocks_valid = [{"type": "paragraph", "text": "Ваше Солнце в Овне дает энергию."}]
    errors = validate_llm_hallucinations(blocks_valid, facts)
    assert len(errors) == 0
    
    # 2. Hallucination (Sign mismatch)
    blocks_invalid = [{"type": "paragraph", "text": "Луна в Скорпионе приносит тайны."}]
    errors = validate_llm_hallucinations(blocks_invalid, facts)
    assert len(errors) == 1
    assert "Moon mentioned in Scorpio, but actually in Taurus" in errors[0]

def test_validator_handles_variants():
    facts = {"pos": [{"p": "Mars", "s": "Leo"}]}
    
    # Check grammatical variant "Льве"
    blocks = [{"type": "paragraph", "text": "Марс находится во Льве."}]
    errors = validate_llm_hallucinations(blocks, facts)
    assert len(errors) == 0
    
    # Check mismatch
    blocks_err = [{"type": "paragraph", "text": "Марс стоит в Раке."}]
    errors = validate_llm_hallucinations(blocks_err, facts)
    assert len(errors) == 1
