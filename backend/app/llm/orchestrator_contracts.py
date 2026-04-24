"""Shared LLM orchestration DTOs and validation errors."""

# ############################################################################
# AI_HEADER: MODULE_LLM_ORCHESTRATOR_CONTRACTS
# ROLE: Stable DTO and error contracts shared by LLM facade and parser modules.
# DEPENDENCIES: pydantic.
# GRACE_ANCHORS: [LLM_SCHEMAS]
# ############################################################################

# START_MODULE_CONTRACT: M-LLM-ORCHESTRATOR-CONTRACTS
# purpose: Provide neutral SectionSpec/SectionResult/error contracts without parser-facade import cycles.
# owns:
#   - backend/app/llm/orchestrator_contracts.py
# inputs:
#   - report section identifiers, titles, prompts, and generated content metadata
# outputs:
#   - shared DTO classes, validation errors, and natal section id sets
# invariants:
#   - public classes remain re-exported from backend.app.llm.orchestrator
# non_goals:
#   - changing provider routing or validation rules
# END_MODULE_CONTRACT: M-LLM-ORCHESTRATOR-CONTRACTS

# START_MODULE_MAP: M-LLM-ORCHESTRATOR-CONTRACTS
# public_entrypoints:
#   - SectionSpec -> report section input DTO
#   - SectionResult -> generated section output DTO
#   - LLMContentValidationError/LLMBlockContractError -> retry/fallback control errors
# semantic_blocks:
#   - LLM_SCHEMAS: DTOs, errors, natal section id sets, and small text helper
# owned_tests:
#   - tests/test_llm_fallback_chain.py
# adjacent_modules:
#   - backend/app/llm/orchestrator.py
#   - backend/app/llm/orchestrator_parse.py
# END_MODULE_MAP: M-LLM-ORCHESTRATOR-CONTRACTS

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# #START_BLOCK_LLM_SCHEMAS
class SectionSpec(BaseModel):
    """
    # PURPOSE: Describe a report section to be generated.
    # INPUT: section_id, title, prompt.
    # OUTPUT: Validated specification object.
    # CONTEXT: Used by the orchestrator during generation.
    """

    section_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    max_tokens: Optional[int] = None


class SectionResult(BaseModel):
    """
    # PURPOSE: Capture a generated section result.
    # INPUT: section_id, title, content.
    # OUTPUT: Validated result object.
    # CONTEXT: Returned by the orchestrator.
    """

    section_id: str
    title: str
    content: str
    usage: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
# #END_BLOCK_LLM_SCHEMAS


class LLMContentValidationError(ValueError):
    """
    # PURPOSE: Signal that LLM output failed structural validation.
    # INPUT: error message.
    # OUTPUT: Exception for retry/fallback control flow.
    # CONTEXT: Raised after parsing when content shape is insufficient.
    """


class LLMBlockContractError(LLMContentValidationError):
    """
    # PURPOSE: Signal that JSON blocks violate the renderer contract.
    # INPUT: error message.
    # OUTPUT: Exception for retry/template-fallback flow.
    # CONTEXT: Raised for invalid block types, required keys or field shapes.
    """


NATAL_SECTION_IDS = {
    "executive_summary",
    "input_frame",
    "synthesis",
    "framework_elements_modes",
    "axes_truths",
    "aspects_beginner",
    "configurations_geometry",
    "dispositor_office",
    "core_triad",
    "mercury_mind",
    "shadow_trauma",
    "nodes_growth",
    "vertex_fate",
    "balance_wheel_1_6",
    "balance_wheel_7_12",
    "love_intimacy",
    "money_realization",
    "stars_transuranus",
    "time_cycles",
    "final_synthesis",
}

PREMIUM_NATAL_SECTION_IDS = {
    "executive_summary",
    "synthesis",
    "love_intimacy",
}


def _contains_any(text: str, tokens: List[str]) -> bool:
    return any(token in text for token in tokens)


