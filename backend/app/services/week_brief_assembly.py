"""WeekBrief payload assembly, validation, and envelope entrypoints."""

# ############################################################################
# AI_HEADER: MODULE_WEEK_BRIEF_ASSEMBLY
# ROLE: Build canonical WeekBrief payloads and envelopes from normalized seeds.
# DEPENDENCIES: week_brief_foundation, week_brief_normalization, week_brief_seed, week_brief_validators.
# GRACE_ANCHORS: [WEEK_BRIEF_FACTORS, WEEK_BRIEF_ENTRYPOINTS]
# ############################################################################

# START_MODULE_CONTRACT: M-WEEK-BRIEF-ASSEMBLY
# purpose: Assemble, validate, and fallback WeekBrief payloads while preserving existing API semantics.
# owns:
#   - backend/app/services/week_brief_assembly.py
# inputs:
#   - report workflow context, report chunks, payload metadata, and optional user context
# outputs:
#   - validated week_brief_v1 payloads and ready/in-progress/error envelopes
# invariants:
#   - schema, fallback mode, report_ref, premium, CTA, and telemetry semantics remain unchanged
# non_goals:
#   - changing report workflow ownership or frontend mapping
# END_MODULE_CONTRACT: M-WEEK-BRIEF-ASSEMBLY

# START_MODULE_MAP: M-WEEK-BRIEF-ASSEMBLY
# public_entrypoints:
#   - build_week_brief_payload -> canonical WeekBrief DTO assembly
#   - build_week_brief_envelope -> API envelope for report detail
# internal_entrypoints:
#   - _build_week_brief_fallback -> deterministic fallback payload builder
#   - _build_explainability -> confidence and source summary builder
# semantic_blocks:
#   - WEEK_BRIEF_FACTORS: weighted payload, domain, explainability, markdown and report-ref helpers
#   - WEEK_BRIEF_ENTRYPOINTS: seed resolution, fallback, payload, and envelope builders
# owned_tests:
#   - tests/test_week_brief_service.py
#   - tests/test_week_brief_api.py
# adjacent_modules:
#   - backend/app/services/week_brief_service.py
#   - backend/app/services/week_brief_normalization.py
# END_MODULE_MAP: M-WEEK-BRIEF-ASSEMBLY

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Iterable

from .aggregation_weights import apply_weighted_factors
try:
    from .week_brief_seed import (
        build_week_brief_seed_bundle as _build_week_brief_seed_bundle,
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
from .week_brief_foundation import *
from .week_brief_normalization import *
from . import week_brief_foundation as _foundation
from . import week_brief_normalization as _normalization
globals().update({name: getattr(_foundation, name) for name in dir(_foundation) if name.startswith("_") and not name.startswith("__")})
globals().update({name: getattr(_normalization, name) for name in dir(_normalization) if name.startswith("_") and not name.startswith("__")})
from .week_brief_types import SignalSource
from .week_brief_validators import validate_week_brief_envelope_payload, validate_week_brief_payload

# START_BLOCK: WEEK_BRIEF_FACTORS
def _weighted_factor_payloads(records: list[_FactorSeed]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return _assemble_week_top_layer(records, limit=5)


def _build_domain_scores(
    seed: dict[str, Any],
    factor_records: list[_FactorSeed],
    day_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    semantic_layer = seed.get("semantic_layer") or {}
    summary = seed.get("summary") or {}
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    scores = {
        "work_money": 55,
        "relationships": 55,
        "energy": 55,
        "focus": 55,
    }
    traffic = str(summary.get("traffic_light") or "YELLOW").upper()
    if traffic == "GREEN":
        scores["work_money"] += 8
        scores["focus"] += 10
        scores["energy"] += 4
        scores["relationships"] += 4
    elif traffic == "RED":
        scores["energy"] -= 10
        scores["work_money"] -= 6
        scores["focus"] -= 6
        scores["relationships"] -= 4

    dominant_domain = FOCUS_DOMAIN_MAP.get(focus_key, "focus")
    scores[dominant_domain] += 9

    for card in day_cards:
        mode = str(card.get("mode") or "").lower()
        if mode == "green":
            scores[dominant_domain] += 2
            scores["focus"] += 1
        elif mode == "red":
            scores["energy"] -= 2
            scores["focus"] -= 1

    for record in factor_records:
        impact = int(round(record.weight * 12))
        if record.signal < 0:
            scores[record.domain] -= impact
        else:
            scores[record.domain] += impact

    domains: list[dict[str, Any]] = []
    for key in ("work_money", "relationships", "energy", "focus"):
        value = max(0, min(100, int(scores[key])))
        domains.append(
            {
                "key": key,
                "title": DOMAIN_TITLES[key],
                "status": _domain_status(value),
                "value": value,
                "headline": _domain_headline(key, value, focus_key)[:100],
                "advice": _domain_advice(key, value, semantic_layer)[:220],
            }
        )
    return domains


def _confidence_bucket(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.6:
        return "medium"
    return "low"


def _build_explainability(
    seed: dict[str, Any],
    weighted: dict[str, Any],
    factor_count: int,
    *,
    birth_time_used: bool,
    fallback_mode: bool,
    chunk_parse_degraded: bool,
) -> dict[str, Any]:
    confidence = 0.52
    if seed.get("days"):
        confidence += 0.12
    if seed.get("year_forecast_data") or seed.get("month_forecast_data"):
        confidence += 0.1
    if factor_count >= 5:
        confidence += 0.08
    if birth_time_used:
        confidence += 0.06
    if fallback_mode:
        confidence -= 0.16
    if chunk_parse_degraded:
        confidence -= 0.08
    confidence = round(max(0.35, min(0.94, confidence)), 2)

    top_factors = weighted.get("top_factors") or []
    top_signal_source = SignalSource.mixed.value
    if top_factors:
        top_signal_source = _signal_source_for_models(top_factors[0].get("source_models") or [])

    return {
        "confidence": confidence,
        "birth_time_used": bool(birth_time_used),
        "factor_count": factor_count,
        "timing_precision": "exact" if seed.get("days") else "approximate",
        "top_signal_source": top_signal_source,
        "explanation_depth": "full" if factor_count >= 5 else "standard",
        "reliability_support": [
            str(item.get("label") or item.get("factor_id") or "").strip()
            for item in (weighted.get("reliability_support", []) or [])
            if isinstance(item, dict) and str(item.get("label") or item.get("factor_id") or "").strip()
        ],
        "calibration": {
            "weight_profile_version": weighted.get("weight_profile_version", "v2"),
            "susceptibility_source": "deterministic_default",
            "susceptibility_version": "v1",
            "entrypoints": calibration_entrypoints(),
        },
    }


def _render_chunk_markdown(blocks: list[dict[str, Any]], raw_content: str) -> tuple[str, str | None, bool]:
    if not blocks:
        return raw_content.strip() or "Секция доступна в исходном виде.", None, True

    lines: list[str] = []
    summary: str | None = None
    degraded = False
    for block in blocks:
        block_type = str(block.get("type") or "").strip().lower()
        if block_type == "header":
            level = int(block.get("level") or 2)
            text = str(block.get("text") or "").strip()
            if text:
                lines.append(f"{'#' * max(1, min(6, level))} {text}")
        elif block_type == "paragraph":
            text = str(block.get("text") or "").strip()
            if text:
                lines.append(text)
                if summary is None:
                    summary = text[:240]
        elif block_type == "callout":
            title = str(block.get("title") or "").strip()
            content = str(block.get("content") or "").strip()
            if title or content:
                label = f"**{title}**" if title else ""
                lines.append(": ".join(part for part in [label, content] if part))
                if summary is None and content:
                    summary = content[:240]
        elif block_type == "list":
            items = [str(item).strip() for item in (block.get("items") or []) if str(item).strip()]
            lines.extend(f"- {item}" for item in items)
            if summary is None and items:
                summary = items[0][:240]
        elif block_type == "key_value":
            items = [item for item in (block.get("items") or []) if isinstance(item, dict)]
            for item in items:
                key = str(item.get("key") or "").strip()
                value = str(item.get("value") or "").strip()
                if key or value:
                    lines.append(f"- **{key}**: {value}".strip())
            if summary is None and items:
                first = items[0]
                summary = f"{first.get('key')}: {first.get('value')}"[:240]
        elif block_type == "traffic_lights":
            items = block.get("items") or {}
            if isinstance(items, dict):
                normalized_items = []
                for key in ("money", "health", "love"):
                    value = str(items.get(key) or "").strip()
                    if value:
                        normalized_items.append(f"{key}: {value}")
                if normalized_items:
                    lines.append("Срезы недели:")
                    lines.extend(f"- {item}" for item in normalized_items)
                    if summary is None:
                        summary = f"Срезы недели: {', '.join(normalized_items)}"[:240]
                else:
                    degraded = True
            else:
                degraded = True
        else:
            degraded = True
    markdown = "\n\n".join(line for line in lines if line).strip() or raw_content.strip()
    return markdown, summary, degraded


def _chunk_title(section: str, blocks: list[dict[str, Any]]) -> str:
    for block in blocks:
        if str(block.get("type") or "").strip().lower() == "header":
            text = str(block.get("text") or "").strip()
            if text:
                return text[:80]
    return section.replace("_", " ").strip().title()[:80] or "Секция"


def _section_seed_title(seed: WeekSectionSeed) -> str:
    title = str(seed.title or "").strip()
    return title[:80] or seed.slug.replace("_", " ").strip().title()[:80] or "Секция"


def _section_seed_markdown(seed: WeekSectionSeed, factor_records: list[_FactorSeed]) -> str:
    lines: list[str] = [f"# {_section_seed_title(seed)}", str(seed.summary or "").strip()]
    indexed_records = {record.id: record for record in factor_records}
    ordered_records = [indexed_records[factor_id] for factor_id in seed.factor_ids if factor_id in indexed_records]
    for record in ordered_records[:4]:
        detail = str(record.explanation_human or record.explanation_astro or "").strip()
        if not detail:
            continue
        lines.append(f"- {record.label}: {detail}")
    return "\n\n".join(part for part in lines if part).strip()


def _build_seed_deep_sections(
    section_seeds: list[WeekSectionSeed],
    factor_records: list[_FactorSeed],
) -> list[dict[str, Any]]:
    deep_sections: list[dict[str, Any]] = []
    for order, section_seed in enumerate(section_seeds):
        deep_sections.append(
            {
                "id": section_seed.id,
                "slug": section_seed.slug[:64],
                "title": _section_seed_title(section_seed),
                "summary": str(section_seed.summary or "").strip()[:240],
                "body_markdown": _section_seed_markdown(section_seed, factor_records),
                "is_primary": order == 0,
                "order": order,
            }
        )
    return deep_sections[:16]


def _build_deep_sections(chunks: Iterable[Any]) -> tuple[list[dict[str, Any]], bool]:
    deep_sections: list[dict[str, Any]] = []
    degraded = False
    for order, chunk in enumerate(sorted(chunks, key=lambda item: int(getattr(item, "order_index", 0)))):
        section = str(getattr(chunk, "section", "") or "").strip()
        if not section or section == "input_frame":
            continue
        raw_content = str(getattr(chunk, "content", "") or "").strip()
        blocks = _parse_json_block_list(raw_content)
        markdown, summary, section_degraded = _render_chunk_markdown(blocks, raw_content)
        degraded = degraded or section_degraded or str(getattr(chunk, "status", "") or "").lower() != "completed"
        deep_sections.append(
            {
                "id": f"deep_{section}",
                "slug": section[:64],
                "title": _chunk_title(section, blocks),
                "summary": summary,
                "body_markdown": markdown,
                "is_primary": section == "week_strategy" or order == 0,
                "order": order,
            }
        )
    return deep_sections[:16], degraded


def _merge_seed_with_chunk_sections(
    seed_sections: list[dict[str, Any]],
    chunk_sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not seed_sections:
        return chunk_sections[:16]

    chunk_by_slug = {
        str(section.get("slug") or "").strip(): section
        for section in chunk_sections
        if str(section.get("slug") or "").strip()
    }
    merged: list[dict[str, Any]] = []
    for seed_section in seed_sections:
        merged_section = copy.deepcopy(seed_section)
        chunk_section = chunk_by_slug.get(str(seed_section.get("slug") or "").strip())
        if chunk_section:
            chunk_body = str(chunk_section.get("body_markdown") or "").strip()
            if chunk_body and not _looks_like_placeholder_markdown(chunk_body):
                merged_section["body_markdown"] = chunk_body
            chunk_title = str(chunk_section.get("title") or "").strip()
            if chunk_title and not _looks_like_placeholder_text(chunk_title):
                merged_section["title"] = chunk_title[:80]
            chunk_summary = str(chunk_section.get("summary") or "").strip()
            if chunk_summary and not _looks_like_placeholder_text(chunk_summary):
                merged_section["summary"] = chunk_summary[:240]
        merged.append(merged_section)
    return merged[:16]


def _build_day_cards(seed: dict[str, Any]) -> list[dict[str, Any]]:
    semantic_layer = seed.get("semantic_layer") or {}
    factor_records = [record for record in (seed.get("factor_records") or []) if getattr(record, "id", None)]
    indexed_records = {str(record.id): record for record in factor_records if getattr(record, "id", None)}
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    start, _end = _week_window(seed)
    cards: list[dict[str, Any]] = []
    for index in range(7):
        source = (seed.get("days") or [None] * 7)[index] if index < len(seed.get("days") or []) else None
        current_date = start + timedelta(days=index)
        normalized = _normalize_week_day_payload(source or {"date": current_date.isoformat(), "weekday": current_date.strftime("%A"), "traffic_light": "YELLOW"})
        best_for, avoid = _build_day_actions(normalized, focus_key)
        headline = _build_day_headline(normalized, focus_key)[:100]
        lead = ". ".join(part for part in [headline, f"Опора дня — {best_for[0]}" if best_for else None] if part)[:180] or None
        practical = best_for[:2] if best_for else avoid[:1]
        factor_ids = [record.id for record in factor_records[index:index + 2] if getattr(record, "id", None)][:4]
        ordered_records = [indexed_records[factor_id] for factor_id in factor_ids if factor_id in indexed_records]
        detail_supporting_factors = _build_supporting_factor_entries(ordered_records, factor_ids, limit=3)
        why_title = "Почему день так звучит" if detail_supporting_factors else None
        why_parts = [lead]
        if best_for:
            why_parts.append(f"Лучше ставить на {best_for[0].lower()}.")
        if avoid:
            why_parts.append(f"Снижайте риск через режим без {avoid[0].lower()}.")
        why_text = " ".join(part.strip() for part in why_parts if part and str(part).strip())[:280] or None
        supporting_factors = [
            {
                "label": "Лучше направить в",
                "explanation_human": best_for[0] if best_for else "Спокойный ритм и проверяемые шаги дадут лучший результат.",
                "value": f"{_score_day_card(normalized)}/100",
            },
            {
                "label": "Стоит снизить",
                "explanation_human": avoid[0] if avoid else "Избегайте резких решений без подтверждения.",
                "value": str(normalized.get("traffic_light") or "YELLOW").lower(),
            },
        ]
        cards.append(
            {
                "id": f"week-day-{current_date.isoformat()}",
                "date": _safe_date(normalized.get("date"), default=current_date).isoformat(),
                "weekday": _weekday_code(normalized, current_date),
                "mode": str(normalized.get("traffic_light") or "YELLOW").lower(),
                "score": _score_day_card(normalized),
                "headline": headline,
                "lead": lead,
                "practical": practical[:3],
                "supporting_factors": supporting_factors[:3],
                "details": {
                    "why_text": why_text,
                    "why_title": why_title,
                    "supporting_factors": detail_supporting_factors,
                },
                "factor_ids": factor_ids,
                "best_for": best_for[:4],
                "avoid": avoid[:4],
                "peak_window_label": None if (normalized.get("moon") or {}).get("void_of_course") else "до 14:00",
            }
        )
    return cards


def _resolve_week_type(summary: dict[str, Any], day_cards: list[dict[str, Any]], semantic_layer: dict[str, Any]) -> str:
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    green_days = sum(1 for day in day_cards if day.get("mode") == "green")
    red_days = sum(1 for day in day_cards if day.get("mode") == "red")
    traffic = str(summary.get("traffic_light") or "YELLOW").upper()
    if focus_key == "rest":
        return "recovery"
    if red_days >= 2 or traffic == "RED":
        return "caution" if green_days < 2 else "transition"
    if green_days >= 4 and focus_key in {"launch", "money_admin"}:
        return "push"
    if focus_key == "launch":
        return "deep_work"
    if green_days and red_days:
        return "transition"
    return "balance"


def _build_summary(seed: dict[str, Any], day_cards: list[dict[str, Any]]) -> dict[str, Any]:
    summary = seed.get("summary") or {}
    semantic_layer = seed.get("semantic_layer") or {}
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    traffic = str(summary.get("traffic_light") or "YELLOW").upper()
    green_days = sum(1 for item in day_cards if item.get("mode") == "green")
    red_days = sum(1 for item in day_cards if item.get("mode") == "red")

    headline = {
        "GREEN": "Неделя дает ход тем шагам, которые уже готовы к реальному движению.",
        "YELLOW": "Неделя просит точного ритма, коротких проверок и ясных договоренностей.",
        "RED": "Неделя требует взрослой сборки, буфера и отказа от лишнего фронта.",
    }.get(traffic, "Неделя просит точного ритма, коротких проверок и ясных договоренностей.")
    if semantic_layer.get("headline"):
        headline = str(semantic_layer.get("headline")).strip()

    subhead = " ".join(
        part.strip()
        for part in [
            str(semantic_layer.get("pacing") or "").strip(),
            str(semantic_layer.get("negotiation") or "").strip(),
        ]
        if part and str(part).strip()
    )
    if not subhead:
        subhead = "Лучший результат даст одна опорная линия недели и отказ от лишней суеты."

    if red_days >= 2:
        subhead += " Красные дни лучше вести без силового нажима."
    elif green_days >= 3:
        subhead += " Сильные дни стоит использовать для видимых шагов и фиксаций."

    return {
        "headline": headline[:160],
        "subhead": subhead[:300],
        "week_type": _resolve_week_type(summary, day_cards, semantic_layer),
        "theme": FOCUS_THEME_MAP.get(focus_key, "Темп, приоритеты и ясные шаги")[:80],
    }


def _build_premium(user: Any | None, *, report_status: str) -> dict[str, Any] | None:
    if user is None:
        return None
    now = datetime.now(timezone.utc)
    active_until = getattr(user, "subscription_active_until", None)
    if isinstance(active_until, datetime) and active_until.tzinfo is None:
        active_until = active_until.replace(tzinfo=timezone.utc)
    active = bool(active_until and active_until > now)
    days_left = max((active_until - now).days, 0) if active and active_until else None
    return {
        "subscription_active": active,
        "subscription_active_until": active_until.date().isoformat() if active_until else None,
        "days_left": days_left if active else 0 if active_until else None,
        "show_upgrade_cta": not active,
        "show_resume_banner": report_status == "in_progress",
    }


def _build_cta(report: Any) -> dict[str, Any]:
    report_id = str(getattr(report, "id", "") or "").strip()
    return {
        "primary": {
            "type": "open_report",
            "label": "Открыть разбор",
            "href": f"/read/{report_id}",
        },
        "secondary": {
            "type": "open_history",
            "label": "К истории",
            "href": "/reports",
        },
    }


def _report_ref(report: Any) -> dict[str, Any]:
    generated_at = getattr(report, "updated_at", None) or getattr(report, "created_at", None)
    generated = generated_at.isoformat() if isinstance(generated_at, datetime) else None
    return {
        "report_id": str(getattr(report, "id", "")),
        "report_type": "week_forecast",
        "source_status": str(getattr(report, "status", "") or "unknown"),
        "generated_at": generated,
    }
# END_BLOCK: WEEK_BRIEF_FACTORS


# START_BLOCK: WEEK_BRIEF_ENTRYPOINTS
# START_CONTRACT: FN-BUILD-WEEK-BRIEF-SEED
# purpose: Resolve the week-owned seed boundary for WeekBrief assembly.
# inputs:
#   - context: report workflow context or prebuilt week_brief_seed
# returns: copied seed payload for deterministic assembly
def _build_seed(context: dict[str, Any]) -> dict[str, Any]:
    if context.get("week_brief_seed"):
        return copy.deepcopy(context["week_brief_seed"])
    return _build_week_brief_seed_bundle(context)
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-SEED


# START_CONTRACT: FN-BUILD-WEEK-BRIEF-FALLBACK
# purpose: Build deterministic fallback WeekBrief payload when normal validation or assembly fails.
# inputs:
#   - report, payload, context, chunks, and optional user
# returns: fallback WeekBrief dict preserving week_brief_v1 schema semantics
def _build_week_brief_fallback(
    *,
    report: Any,
    payload: Any | None,
    context: dict[str, Any],
    chunks: Iterable[Any],
    user: Any | None,
) -> dict[str, Any]:
    seed = _build_seed(context) if context else {}
    start, end = _week_window(seed, report=report)
    deep_sections, degraded = _build_deep_sections(chunks)
    fallback_day_cards = _build_day_cards(
        {
            **seed,
            "days": [],
            "summary": seed.get("summary") or {"traffic_light": "YELLOW", "avg_tension": 0.6},
            "semantic_layer": seed.get("semantic_layer")
            or {
                "focus_key": "money_admin",
                "headline": "Неделя лучше идет через спокойный ритм и одну опорную линию.",
                "pacing": "Лучше не распыляться и заранее оставлять буфер на перепроверку.",
                "negotiation": "Фиксируй ключевые договоренности сразу после разговора.",
                "rest": "Не геройствуй там, где можно замедлиться и проверить вводные.",
            },
        }
    )
    factors = [
        {
            "id": "fallback_background",
            "label": "Безопасный fallback недели",
            "impact": "medium",
            "category": "background",
            "explanation_human": "Даже без полного набора сигналов неделя лучше всего собирается через один главный трек и короткие проверки.",
            "explanation_astro": "Часть расчетов недоступна, поэтому brief собран из минимального устойчивого слоя.",
            "source_models": [SignalSource.mixed.value],
            "weight": 0.45,
        }
    ]
    explainability = {
        "confidence": 0.4,
        "birth_time_used": bool(payload and getattr(payload, "birth_time_known", True)),
        "factor_count": 1,
        "timing_precision": "approximate",
        "top_signal_source": SignalSource.mixed.value,
        "explanation_depth": "minimal",
    }
    return {
        "version": "week_brief_v1",
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "personalization_level": "personalized_v2" if payload else "anonymous",
        "fallback_mode": True,
        "status": _map_report_status(getattr(report, "status", None)),
        "summary": {
            "headline": "Неделя требует спокойного ритма, ясных приоритетов и коротких подтверждений.",
            "subhead": "Полный слой прогноза сейчас частично недоступен, поэтому держись одной рабочей линии и не разгоняй лишний фронт.",
            "week_type": "transition",
            "theme": "Приоритеты, ритм и проверка деталей",
        },
        "day_cards": fallback_day_cards,
        "domains": [
            {
                "key": key,
                "title": DOMAIN_TITLES[key],
                "status": "yellow",
                "value": 55,
                "headline": DOMAIN_HEADLINES[key][:100],
                "advice": "Иди по шагам и не принимай промежуточный результат за финальный.",
            }
            for key in ("work_money", "relationships", "energy", "focus")
        ],
        "best_uses": _format_action_items(list(GENERIC_BEST_USES), prefix="best"),
        "risks": _format_action_items(list(GENERIC_RISKS), prefix="risk"),
        "major_factors": factors,
        "deep_sections": deep_sections,
        "explainability": explainability,
        "premium": _build_premium(user, report_status=_map_report_status(getattr(report, "status", None))),
        "cta": _build_cta(report),
        "report_ref": _report_ref(report),
    }
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-FALLBACK


# START_CONTRACT: FN-BUILD-WEEK-BRIEF-PAYLOAD
# purpose: Build and validate the canonical WeekBrief payload for report detail responses.
# inputs:
#   - report, payload, context, report chunks, optional user, and optional llm_model label
# returns: validated week_brief_v1 dict, or validated deterministic fallback on failure
# side_effects:
#   - emits week_brief.* structured events with stable module/function/block attribution
def build_week_brief_payload(
    *,
    report: Any,
    payload: Any | None,
    context: dict[str, Any] | None,
    chunks: Iterable[Any],
    user: Any | None = None,
    llm_model: str | None = None,
) -> dict[str, Any]:
    safe_context = copy.deepcopy(context or {})
    try:
        seed = _build_seed(safe_context)
        summary = seed.get("summary") or _normalize_week_summary(
            safe_context.get("week_forecast_data") or {},
            [_normalize_week_day_payload(day) for day in (safe_context.get("week_forecast_data") or {}).get("days", [])[:7]],
        )
        seed["summary"] = summary
        day_cards = _build_day_cards(seed)
        factor_records = _build_factor_seeds(seed)
        section_seeds = _build_week_section_seeds(seed, factor_records)
        major_factors, weighted = _weighted_factor_payloads(factor_records)
        seed_deep_sections = _build_seed_deep_sections(section_seeds, factor_records)
        chunk_deep_sections, chunk_parse_degraded = _build_deep_sections(chunks)
        deep_sections = _merge_seed_with_chunk_sections(seed_deep_sections, chunk_deep_sections)
        best_day = max(day_cards, key=lambda item: int(item.get("score", 0)), default=None)
        worst_day = min(day_cards, key=lambda item: int(item.get("score", 0)), default=None)
        fallback_mode = bool(not seed.get("days") or not deep_sections)
        explainability = _build_explainability(
            seed,
            weighted,
            len(factor_records),
            birth_time_used=bool(payload and getattr(payload, "birth_time_known", True)),
            fallback_mode=fallback_mode,
            chunk_parse_degraded=chunk_parse_degraded,
        )
        week_start, week_end = _week_window(seed, report=report)
        domains = _enrich_domains(_build_domain_scores(seed, factor_records, day_cards), factor_records)
        best_uses = _enrich_action_items(_build_best_uses(seed.get("semantic_layer") or {}, best_day), factor_records, kind="best")
        risks = _enrich_action_items(_build_risks(seed.get("semantic_layer") or {}, worst_day), factor_records, kind="risk")
        result = {
            "version": "week_brief_v1",
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "personalization_level": "personalized_v2" if payload else "anonymous",
            "fallback_mode": fallback_mode,
            "status": _map_report_status(getattr(report, "status", None)),
            "summary": _build_summary(seed, day_cards),
            "day_cards": day_cards,
            "domains": domains,
            "best_uses": best_uses,
            "risks": risks,
            "major_factors": major_factors,
            "deep_sections": deep_sections,
            "explainability": explainability,
            "premium": _build_premium(user, report_status=_map_report_status(getattr(report, "status", None))),
            "cta": _build_cta(report),
            "report_ref": _report_ref(report),
        }
        validated = validate_week_brief_payload(result)
        if validated["fallback_mode"]:
            _log_week_brief(
                "info",
                "week_brief_fallback_triggered",
                report=report,
                block=WEEK_BRIEF_FALLBACK_BLOCK,
                factor_count=validated["explainability"]["factor_count"],
                week_brief_llm_model=llm_model or "deterministic",
                week_brief_fallback_mode=True,
                chunk_parse_degraded=chunk_parse_degraded,
                week_brief_confidence_bucket=_confidence_bucket(validated["explainability"]["confidence"]),
            )
        _log_week_brief(
            "info",
            "week_brief_built",
            report=report,
            block=WEEK_BRIEF_PAYLOAD_BLOCK,
            factor_count=validated["explainability"]["factor_count"],
            week_brief_llm_model=llm_model or "deterministic",
            week_brief_fallback_mode=validated["fallback_mode"],
            chunk_parse_degraded=chunk_parse_degraded,
            week_brief_confidence_bucket=_confidence_bucket(validated["explainability"]["confidence"]),
        )
        return validated
    except Exception as exc:
        _log_week_brief(
            "warning",
            "week_brief_validation_failed",
            report=report,
            block=WEEK_BRIEF_VALIDATION_BLOCK,
            error=str(exc),
            week_brief_llm_model=llm_model or "deterministic",
        )
        fallback = validate_week_brief_payload(
            _build_week_brief_fallback(
                report=report,
                payload=payload,
                context=safe_context,
                chunks=chunks,
                user=user,
            )
        )
        _log_week_brief(
            "info",
            "week_brief_fallback_triggered",
            report=report,
            block=WEEK_BRIEF_FALLBACK_BLOCK,
            factor_count=fallback["explainability"]["factor_count"],
            week_brief_llm_model=llm_model or "deterministic",
            week_brief_fallback_mode=True,
            chunk_parse_degraded=True,
            week_brief_confidence_bucket=_confidence_bucket(fallback["explainability"]["confidence"]),
        )
        _log_week_brief(
            "info",
            "week_brief_built",
            report=report,
            block=WEEK_BRIEF_PAYLOAD_BLOCK,
            factor_count=fallback["explainability"]["factor_count"],
            week_brief_llm_model=llm_model or "deterministic",
            week_brief_fallback_mode=True,
            chunk_parse_degraded=True,
            week_brief_confidence_bucket=_confidence_bucket(fallback["explainability"]["confidence"]),
        )
        return fallback
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-PAYLOAD


# START_CONTRACT: FN-BUILD-WEEK-BRIEF-ENVELOPE
# purpose: Wrap WeekBrief data into the stable API envelope for ready, in-progress, and error reports.
# inputs:
#   - report status, optional WeekBrief payload, retry-after value
# returns: validated WeekBrief envelope dict
def build_week_brief_envelope(
    *,
    report: Any,
    week_brief: dict[str, Any] | None = None,
    retry_after_seconds: int = 3,
) -> dict[str, Any]:
    status = _map_report_status(getattr(report, "status", None))
    payload = {
        "status": status,
        "data": week_brief if status == "ready" else None,
        "message": None,
        "retry_after_seconds": retry_after_seconds if status == "in_progress" else None,
    }
    if status == "in_progress":
        payload["message"] = "Week brief is still building."
    if status == "error":
        payload["message"] = str(getattr(report, "error_message", "") or "Week brief could not be fully assembled.")
    return validate_week_brief_envelope_payload(payload)
# END_CONTRACT: FN-BUILD-WEEK-BRIEF-ENVELOPE
# END_BLOCK: WEEK_BRIEF_ENTRYPOINTS
