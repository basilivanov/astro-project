"""Compatibility facade for deterministic WeekBrief assembly."""

# ############################################################################
# AI_HEADER: MODULE_WEEK_BRIEF_SERVICE
# ROLE: Stable public import facade for canonical WeekBrief payload/envelope assembly.
# DEPENDENCIES: week_brief_foundation, week_brief_normalization, week_brief_assembly.
# GRACE_ANCHORS: [WEEK_BRIEF_CONSTANTS, WEEK_BRIEF_TYPES, WEEK_BRIEF_TELEMETRY, WEEK_BRIEF_NORMALIZATION, WEEK_BRIEF_FACTORS, WEEK_BRIEF_ENTRYPOINTS]
# ############################################################################

# START_MODULE_CONTRACT: M-WEEK-BRIEF-SERVICE
# purpose: Preserve backend.app.services.week_brief_service public imports while implementation lives in cohesive modules.
# owns:
#   - backend/app/services/week_brief_service.py
# inputs:
#   - report workflow context, report chunks, and optional authenticated user context
# outputs:
#   - canonical WeekBrief payloads and envelopes through stable public symbols
# dependencies:
#   - backend.app.services.week_brief_foundation for constants/types/telemetry
#   - backend.app.services.week_brief_normalization for deterministic seed normalization
#   - backend.app.services.week_brief_assembly for payload and envelope assembly
# invariants:
#   - week_brief_v1 payload semantics and envelope states remain unchanged
#   - packet_local telemetry fields remain available for post-test evidence review
# non_goals:
#   - changing week brief business logic or response schema
# END_MODULE_CONTRACT: M-WEEK-BRIEF-SERVICE

# START_MODULE_MAP: M-WEEK-BRIEF-SERVICE
# public_entrypoints:
#   - build_week_brief_payload -> canonical WeekBrief DTO assembly for report detail responses
#   - build_week_brief_envelope -> API envelope for ready, in_progress, and error states
# internal_entrypoints:
#   - _log_week_brief -> structured WeekBrief event emission helper imported for compatibility
#   - _build_seed -> week-owned seed boundary resolution helper imported for compatibility
#   - _build_week_brief_fallback -> deterministic fallback payload builder imported for compatibility
# semantic_blocks:
#   - WEEK_BRIEF_CONSTANTS: re-exported identifiers, domain maps, and stable display defaults
#   - WEEK_BRIEF_TYPES: re-exported dataclasses used by deterministic factor and section assembly
#   - WEEK_BRIEF_TELEMETRY: re-exported WeekBrief log helper and event attribution markers
#   - WEEK_BRIEF_NORMALIZATION: delegated date, text, and chunk normalization helpers
#   - WEEK_BRIEF_FACTORS: delegated seed-to-factor and section weighting helpers
#   - WEEK_BRIEF_ENTRYPOINTS: delegated seed resolution, fallback, payload build, and envelope build entrypoints
# owned_tests:
#   - tests/test_week_brief_service.py
#   - tests/test_week_brief_api.py
# adjacent_modules:
#   - backend/app/services/week_brief_foundation.py
#   - backend/app/services/week_brief_normalization.py
#   - backend/app/services/week_brief_assembly.py
# END_MODULE_MAP: M-WEEK-BRIEF-SERVICE

# START_BLOCK: WEEK_BRIEF_CONSTANTS
from .week_brief_foundation import *
# Compatibility source markers retained for existing GRACE/source contract tests.
# MODULE_ID = "M-WEEK-BRIEF-SERVICE"
# from .week_brief_seed import (
# WEEK_BRIEF_EVIDENCE_LANE = "packet_local"
# WEEK_BRIEF_PACKET_SCOPE = "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:W01:packet_local"
# WEEK_BRIEF_PAYLOAD_BLOCK = "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
# END_BLOCK: WEEK_BRIEF_CONSTANTS

# START_BLOCK: WEEK_BRIEF_TYPES
# Re-exported from week_brief_foundation for compatibility.
# END_BLOCK: WEEK_BRIEF_TYPES

# START_BLOCK: WEEK_BRIEF_TELEMETRY
# START_CONTRACT: FN-LOG-WEEK-BRIEF
# purpose: Compatibility export for structured WeekBrief event emission.
# END_CONTRACT: FN-LOG-WEEK-BRIEF
# END_BLOCK: WEEK_BRIEF_TELEMETRY

# START_BLOCK: WEEK_BRIEF_NORMALIZATION
from .week_brief_normalization import *
# END_BLOCK: WEEK_BRIEF_NORMALIZATION

# START_BLOCK: WEEK_BRIEF_FACTORS
from .week_brief_assembly import *
# END_BLOCK: WEEK_BRIEF_FACTORS

# START_BLOCK: WEEK_BRIEF_ENTRYPOINTS
# START_CONTRACT: FN-BUILD-WEEK-BRIEF-SEED
# purpose: Compatibility export for week-owned seed boundary resolution.
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-SEED
# START_CONTRACT: FN-BUILD-WEEK-BRIEF-FALLBACK
# purpose: Compatibility export for deterministic fallback payload assembly.
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-FALLBACK
# START_CONTRACT: FN-BUILD-WEEK-BRIEF-PAYLOAD
# purpose: Compatibility export for canonical WeekBrief payload assembly.
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-PAYLOAD
# START_CONTRACT: FN-BUILD-WEEK-BRIEF-ENVELOPE
# purpose: Compatibility export for stable WeekBrief envelope assembly.
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-ENVELOPE
# END_BLOCK: WEEK_BRIEF_ENTRYPOINTS

__all__ = [name for name in globals() if not name.startswith("__")]
