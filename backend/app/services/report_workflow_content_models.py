# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_CONTENT_MODELS
# ROLE: LLM model and concurrency configuration resolution helpers.
# DEPENDENCIES: os
# GRACE_ANCHORS: [MODEL_RESOLUTION]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTENT-MODELS
# purpose: Resolve report workflow LLM retry, fallback, primary model, concurrency, and throttle settings.
# inputs:
#   - Environment variables and report type keys
# outputs:
#   - Primitive model/concurrency configuration values
# trace_obligations:
#   - Pure config helper module; workflow caller retains generation logs
# invariants:
#   - Defaults and environment variable names remain unchanged across extraction
# non_goals:
#   - Does not instantiate LLM clients or call providers
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTENT-MODELS

# START_MODULE_MAP: M-REPORT-WORKFLOW-CONTENT-MODELS
# entrypoints:
#   - resolve_primary_model -> MODEL_RESOLUTION
#   - resolve_llm_fallback_chain -> FALLBACK_MODEL_CHAIN
# END_MODULE_MAP: M-REPORT-WORKFLOW-CONTENT-MODELS

from __future__ import annotations

import os
from typing import List, Optional

# START_BLOCK: MODEL_RESOLUTION
def resolve_llm_retry_attempts() -> int:
    """
    # PURPOSE: Resolve retry attempts for structural validation failures.
    # INPUT: None.
    # OUTPUT: Retry count (>=1).
    # CONTEXT: Used before switching to fallback model.
    """

    raw = os.getenv("OPENROUTER_RETRY_ATTEMPTS", "3").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 3
    return max(1, value)


def resolve_llm_fallback_model() -> str:
    """
    # PURPOSE: Resolve fallback OpenRouter model name.
    # INPUT: None.
    # OUTPUT: Model name string (empty means disabled).
    # CONTEXT: Used when primary model fails structural validation.
    """

    model = os.getenv(
        "OPENROUTER_FALLBACK_MODEL", "openai/gpt-4o-mini"
    ).strip()
    return model


def resolve_llm_fallback_chain() -> List[str]:
    """
    # PURPOSE: Resolve a list of fallback models for the chain.
    # INPUT: None.
    # OUTPUT: List of model names.
    """
    raw = os.getenv("OPENROUTER_FALLBACK_CHAIN", "").strip()
    if not raw:
        # Defaults for MVP (all free and verified stable)
        return [
            "openai/gpt-4o-mini"
        ]
    return [m.strip() for m in raw.split(",") if m.strip()]


def resolve_primary_model(report_type: Optional[str]) -> str:
    """
    # PURPOSE: Pick a primary OpenRouter model based on report type.
    # INPUT: report_type (str | None).
    # OUTPUT: Model name string.
    # CONTEXT: Used to route expensive vs. cheap models per product.
    """

    report_key = (report_type or "").strip().lower()
    if report_key.startswith("natal"):
        model = os.getenv("OPENROUTER_MODEL_NATAL", "").strip()
    elif "forecast" in report_key:
        model = os.getenv("OPENROUTER_MODEL_FORECAST", "").strip()
    elif "horary" in report_key:
        model = os.getenv("OPENROUTER_MODEL_HORARY", "").strip()
    elif "synastry" in report_key:
        model = os.getenv("OPENROUTER_MODEL_SYNASTRY", "").strip()
    else:
        model = ""

    if model:
        return model

    return os.getenv(
        "OPENROUTER_MODEL", "openai/gpt-4.1-nano"
    ).strip()


def resolve_llm_concurrency(llm_mode: str) -> int:
    mode = (llm_mode or "").strip().lower()
    if mode in {"cli", "gemini", "codex"}:
        env_name = "LLM_CLI_CONCURRENCY"
        default = 3
    else:
        env_name = "LLM_CONCURRENCY"
        default = 10  # High concurrency for paid/budget models

    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def resolve_openrouter_throttle_seconds() -> float:
    raw = os.getenv("OPENROUTER_THROTTLE_SECONDS", "0.0").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0
# END_BLOCK: MODEL_RESOLUTION
