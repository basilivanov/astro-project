# ############################################################################
# AI_HEADER: MODULE_LLM_MODE
# ROLE: Resolve LLM mode selection and client construction.
# DEPENDENCIES: backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [LLM_MODE]
# ############################################################################

from __future__ import annotations

import os
from typing import Optional

from .orchestrator import OpenRouterClient, build_cli_client_from_env


# #START_BLOCK_LLM_MODE
def resolve_llm_mode(payload) -> str:
    """
    # PURPOSE: Normalize the requested LLM mode.
    # INPUT: payload with optional llm_mode attribute.
    # OUTPUT: Normalized mode string.
    # CONTEXT: Used by report generation entrypoints.
    """

    # If LLM_SMOKE=1 is not set, we default to 'stub' to avoid accidental costs.
    fallback_default = "stub"
    if os.getenv("LLM_SMOKE") == "1":
        fallback_default = "openrouter"

    default_mode = os.getenv("DEFAULT_LLM_MODE", fallback_default).strip().lower() or fallback_default
    mode = (getattr(payload, "llm_mode", None) or default_mode).strip().lower()
    if mode == "cheap":
        return "cheap"
    if mode not in {"openrouter", "fallback", "local", "mock", "stub", "cli", "gemini", "codex"}:
        if default_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
            return default_mode
        return "openrouter"
    return mode


def build_llm_client(llm_mode: str, model_override: Optional[str] = None):
    """
    # PURPOSE: Construct an LLM client for the selected mode.
    # INPUT: llm_mode (str), report_type (optional).
    # OUTPUT: LLM client instance or None.
    # CONTEXT: Used by report generation endpoints.
    """

    if llm_mode == "openrouter":
        return OpenRouterClient.from_env(model_override=model_override)
    if llm_mode == "cheap":
        return OpenRouterClient.from_env(mode="cheap")
    if llm_mode in {"cli", "gemini", "codex"}:
        provider_override = llm_mode if llm_mode in {"gemini", "codex"} else None
        return build_cli_client_from_env(provider_override=provider_override)
    return None
# #END_BLOCK_LLM_MODE
