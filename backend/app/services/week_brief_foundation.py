"""WeekBrief shared constants, types, and telemetry helpers."""

# ############################################################################
# AI_HEADER: MODULE_WEEK_BRIEF_FOUNDATION
# ROLE: Shared WeekBrief identifiers, DTO seeds, and packet-local telemetry.
# DEPENDENCIES: backend.app.logging_utils, week_brief_types.
# GRACE_ANCHORS: [WEEK_BRIEF_CONSTANTS, WEEK_BRIEF_TYPES, WEEK_BRIEF_TELEMETRY]
# ############################################################################

# START_MODULE_CONTRACT: M-WEEK-BRIEF-FOUNDATION
# purpose: Keep WeekBrief constants, factor seed dataclasses, and structured telemetry in a small shared module.
# owns:
#   - backend/app/services/week_brief_foundation.py
# inputs:
#   - report references and packet-local correlation context
# outputs:
#   - shared constants, seed dataclasses, and week_brief.* structured events
# invariants:
#   - module/function/block attribution and packet_local evidence fields remain stable
# non_goals:
#   - changing WeekBrief response schema or factor scoring logic
# END_MODULE_CONTRACT: M-WEEK-BRIEF-FOUNDATION

# START_MODULE_MAP: M-WEEK-BRIEF-FOUNDATION
# public_entrypoints:
#   - _log_week_brief -> structured WeekBrief event emission helper
# internal_entrypoints:
#   - WeekSectionSeed/_FactorSeed -> deterministic assembly seed records
# semantic_blocks:
#   - WEEK_BRIEF_CONSTANTS: identifiers, domain maps, and defaults
#   - WEEK_BRIEF_TYPES: dataclasses used by factor and section assembly
#   - WEEK_BRIEF_TELEMETRY: correlation-aware event emission
# owned_tests:
#   - tests/test_week_brief_service.py
# adjacent_modules:
#   - backend/app/services/week_brief_service.py
#   - backend/app/services/week_brief_normalization.py
#   - backend/app/services/week_brief_assembly.py
# END_MODULE_MAP: M-WEEK-BRIEF-FOUNDATION

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable
import sys

from ..logging_utils import get_correlation_ids, log_grace_event
from .aggregation_weights import apply_weighted_factors
from .forecast_factor_pipeline import NormalizedFactor, clamp_signal, make_factor, normalize_domain
from .personal_susceptibility import attach_susceptibility, build_susceptibility_profile, calibration_entrypoints
try:
    from .week_brief_seed import (
        build_week_brief_seed_bundle as _build_week_brief_seed_bundle,
        normalize_week_day_payload as _normalize_week_day_payload,
        normalize_week_summary as _normalize_week_summary,
        parse_json_block_list as _parse_json_block_list,
    )
except ModuleNotFoundError:  # pragma: no cover - test env without heavy astro deps
    def _build_week_brief_seed_bundle(context: dict[str, Any]) -> dict[str, Any]:
        week_data = context.get("week_forecast_data") or {}
        return {
            "forecast_window": context.get("forecast_window") or {},
            "days": copy.deepcopy((week_data.get("days") or [])[:7]),
            "summary": copy.deepcopy(week_data.get("summary") or {}),
            "semantic_layer": copy.deepcopy(context.get("semantic_layer") or {}),
            "year_forecast_data": copy.deepcopy(context.get("year_forecast_data") or {}),
            "month_forecast_data": copy.deepcopy(context.get("month_forecast_data") or {}),
        }

    def _normalize_week_day_payload(day: dict[str, Any]) -> dict[str, Any]:
        payload = dict(day or {})
        payload.setdefault("traffic_light", "YELLOW")
        payload.setdefault("moon", {})
        payload.setdefault("events", payload.get("ingresses") or [])
        return payload

    def _normalize_week_summary(summary: dict[str, Any], _days: list[dict[str, Any]]) -> dict[str, Any]:
        payload = dict(summary or {})
        payload.setdefault("traffic_light", "YELLOW")
        payload.setdefault("avg_tension", 0.6)
        return payload

    def _parse_json_block_list(raw_content: str) -> list[dict[str, Any]]:
        try:
            parsed = json.loads(raw_content or "[]")
        except Exception:
            return []
        return parsed if isinstance(parsed, list) else []
from .week_brief_types import SignalSource
from .week_brief_validators import (
    validate_week_brief_envelope_payload,
    validate_week_brief_payload,
)

# START_BLOCK: WEEK_BRIEF_CONSTANTS
MODULE_ID = "M-WEEK-BRIEF-SERVICE"
WEEK_BRIEF_PAYLOAD_BLOCK = "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
WEEK_BRIEF_FALLBACK_BLOCK = "WEEK_BRIEF_FALLBACK_RECOVERY"
WEEK_BRIEF_VALIDATION_BLOCK = "WEEK_BRIEF_VALIDATION_GUARD"
WEEK_BRIEF_EVIDENCE_LANE = "packet_local"
WEEK_BRIEF_PACKET_SCOPE = "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:W01:packet_local"
WEEK_BRIEF_LOG_PACKET_SCOPE = "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:W01:packet_local"
WEEKDAY_CODE_MAP = {
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
    "sunday": "sun",
    "понедельник": "mon",
    "вторник": "tue",
    "среда": "wed",
    "четверг": "thu",
    "пятница": "fri",
    "суббота": "sat",
    "воскресенье": "sun",
}
FOCUS_THEME_MAP = {
    "money_admin": "Работа, договоренности и ритм",
    "relationship": "Контакт, тон и личные границы",
    "rest": "Ресурс, восстановление и буфер",
    "launch": "Запуск, фокус и системный ход",
}
FOCUS_DOMAIN_MAP = {
    "money_admin": "work_money",
    "relationship": "relationships",
    "rest": "energy",
    "launch": "focus",
}
HOUSE_DOMAIN_MAP = {
    1: "energy",
    2: "work_money",
    3: "focus",
    4: "relationships",
    5: "relationships",
    6: "energy",
    7: "relationships",
    8: "work_money",
    9: "focus",
    10: "work_money",
    11: "relationships",
    12: "energy",
}
POINT_DOMAIN_MAP = {
    "Солнце": "work_money",
    "MC": "work_money",
    "ASC": "energy",
    "Марс": "energy",
    "Луна": "relationships",
    "Венера": "relationships",
    "Меркурий": "focus",
    "Юпитер": "focus",
}
DOMAIN_TITLES = {
    "work_money": "Работа и деньги",
    "relationships": "Отношения",
    "energy": "Энергия",
    "focus": "Фокус",
}
DOMAIN_HEADLINES = {
    "work_money": "Неделя показывает, насколько хорошо собран рабочий контур.",
    "relationships": "Тон и формат разговора сейчас влияют на результат сильнее обычного.",
    "energy": "Ресурс держится на ритме, а не на одном сильном рывке.",
    "focus": "Лучше всего едут задачи, где понятен следующий конкретный шаг.",
}
GENERIC_BEST_USES = (
    "Сузь неделю до одной главной линии и держи решения привязанными к ней.",
    "Фиксируй договоренности письменно, чтобы не тратить ресурс на повторные согласования.",
)
GENERIC_RISKS = (
    "Не принимай промежуточную ясность за окончательный результат.",
    "Не трать сильные дни на шум и параллельные срочности.",
)
# END_BLOCK: WEEK_BRIEF_CONSTANTS


# START_BLOCK: WEEK_BRIEF_TYPES
@dataclass
class WeekSectionSeed:
    id: str
    slug: str
    title: str
    summary: str
    factor_ids: list[str] = field(default_factory=list)
    domain: str = "focus"
    source: str = "deterministic"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class _FactorSeed:
    factor: NormalizedFactor
    profile_category: str
    dto_category: str
    source_models: list[str]
    confidence: float
    section_slug: str = "overview"

    @property
    def id(self) -> str:
        return self.factor.id

    @property
    def label(self) -> str:
        return self.factor.label

    @property
    def explanation_human(self) -> str:
        return self.factor.explanation_human

    @property
    def explanation_astro(self) -> str:
        return self.factor.explanation_astro

    @property
    def domain(self) -> str:
        return self.factor.domain

    @property
    def weight(self) -> float:
        return self.factor.weight

    @property
    def signal(self) -> float:
        return self.factor.signal
# END_BLOCK: WEEK_BRIEF_TYPES


# START_BLOCK: WEEK_BRIEF_TELEMETRY
# START_CONTRACT: FN-LOG-WEEK-BRIEF
# purpose: Emit stable week_brief.* logs without changing payload assembly behavior.
# inputs:
#   - log level, event name, optional report, and structured WeekBrief fields
# outputs:
#   - structured log event with module/function/block attribution
def _log_week_brief(
    level: str,
    event: str,
    *,
    report: Any | None = None,
    fn: str = "build_week_brief_payload",
    block: str = WEEK_BRIEF_PAYLOAD_BLOCK,
    **fields: Any,
) -> None:
    context = get_correlation_ids()
    payload = {key: value for key, value in fields.items() if value is not None}
    payload.setdefault("week_brief_evidence_lane", WEEK_BRIEF_EVIDENCE_LANE)
    payload.setdefault("week_brief_packet_scope", WEEK_BRIEF_LOG_PACKET_SCOPE)
    if report is not None:
        payload["report_id"] = str(report.id)
        payload["report_type"] = getattr(report, "report_type", None)
        payload["report_status"] = getattr(report, "status", None)
    emitter = getattr(sys.modules.get("backend.app.services.week_brief_service"), "log_grace_event", log_grace_event)
    emitter(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        block=block,
        correlation_id=context.get("correlation_id"),
        trace_id=context.get("trace_id"),
        correlation_source=context.get("correlation_source"),
        request_id=context.get("request_id"),
        **payload,
    )
# END_CONTRACT: FN-LOG-WEEK-BRIEF
# END_BLOCK: WEEK_BRIEF_TELEMETRY
