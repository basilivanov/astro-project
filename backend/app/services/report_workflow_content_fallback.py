# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_CONTENT_FALLBACK
# ROLE: Validation fallback content builders for report sections.
# DEPENDENCIES: backend/app/llm/orchestrator.py, report_workflow_forecast.py
# GRACE_ANCHORS: [VALIDATION_FALLBACK]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTENT-FALLBACK
# purpose: Build deterministic fallback content when section validation or generation cannot use LLM output.
# inputs:
#   - SectionSpec values and section/global report contexts
# outputs:
#   - JSON block strings preserving report copy/schema compatibility
# trace_obligations:
#   - Pure helper module; workflow caller logs fallback application with report_id/block fields
# invariants:
#   - Validation fallback wording and facts-first anchors remain stable across extraction
# non_goals:
#   - Does not decide fallback policy or mutate report lifecycle state
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTENT-FALLBACK

# START_MODULE_MAP: M-REPORT-WORKFLOW-CONTENT-FALLBACK
# entrypoints:
#   - build_section_validation_fallback_content -> VALIDATION_FALLBACK
# END_MODULE_MAP: M-REPORT-WORKFLOW-CONTENT-FALLBACK

from __future__ import annotations

import json
import re
from typing import Any, List, Optional

from ..llm.orchestrator import NATAL_SECTION_IDS, SectionSpec
from .report_workflow_content import build_section_template_content
from .report_workflow_forecast import build_section_fallback_content

# START_BLOCK: VALIDATION_FALLBACK
def _build_insight_pack_fallback_content(spec: SectionSpec, insight_pack: dict) -> str:
    """
    # PURPOSE: Build meaningful fallback using deterministic insight_pack when LLM validation fails.
    # INPUT: section spec, insight_pack (dict with section-specific structured data).
    # OUTPUT: JSON string (list of blocks) verbalizing the insight pack.
    # CONTEXT: Ensures natal sections don't fall to generic template markers.
    """
    import json

    blocks = []
    title = spec.title.strip()

    # Executive summary fallback
    if spec.section_id == "executive_summary":
        scene_seed = ""
        for scene in insight_pack.get("scene_seeds", []):
            if isinstance(scene, dict) and str(scene.get("seed", "")).strip():
                scene_seed = str(scene.get("seed")).strip()
                break
        if not scene_seed:
            for manifestation in insight_pack.get("life_manifestations", []):
                if isinstance(manifestation, dict) and str(manifestation.get("label", "")).strip():
                    scene_seed = str(manifestation.get("label")).strip()
                    break
        if scene_seed:
            scene_seed = scene_seed[0].upper() + scene_seed[1:]
            if scene_seed[-1] not in ".!?":
                scene_seed += "."

        strength_desc = _format_insight_value(insight_pack.get("strengths_score"))
        risk_desc = _format_insight_value(insight_pack.get("risk_score"))
        relationship_desc = _format_insight_value(insight_pack.get("relationship_theme"))
        money_desc = _format_insight_value(insight_pack.get("money_theme"))
        development_desc = _format_insight_value(insight_pack.get("development_focus"))
        best_mode_desc = _format_insight_value(insight_pack.get("best_mode_of_action"))
        practical_hint = _pick_first_action_item(insight_pack.get("what_to_do"))
        sun_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("sun_vector")))
        moon_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("moon_vector")))
        axis_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("asc_mc_axis")))
        items = []
        if strength_desc:
            items.append(f"Сильная опора здесь в том, что {strength_desc}")
        if risk_desc:
            items.append(f"Перегиб включается через {risk_desc}")
        if relationship_desc:
            items.append(f"В отношениях сильнее всего работает {relationship_desc}")
        if money_desc:
            items.append(f"В работе и деньгах сильнее всего работает {money_desc}")
        if sun_anchor:
            items.append(f"☀️ Опорный солнечный вектор: {sun_anchor}")
        if moon_anchor:
            items.append(f"🌙 Эмоциональный якорь: {moon_anchor}")
        if axis_anchor:
            items.append(f"⬆️/🏔️ Социальная ось: {axis_anchor}")
        if development_desc:
            items.append(f"Следующий вектор роста здесь в том, чтобы {development_desc}")
        if practical_hint:
            items.append(f"Практический ход на сейчас — {practical_hint}")

        intro_parts = []
        if scene_seed:
            intro_parts.append(scene_seed)
        if sun_anchor:
            intro_parts.append(_clean_sentence(f"☀️ Солнце: {sun_anchor}"))
        if moon_anchor:
            intro_parts.append(_clean_sentence(f"🌙 Луна: {moon_anchor}"))
        intro_text = " ".join(part for part in intro_parts if part).strip() or "Карта собирается вокруг сильного внутреннего паттерна, который важно переводить в живое действие без перегиба."

        closing_bits = []
        if axis_anchor:
            closing_bits.append(_clean_sentence(f"⬆️ ASC / 🏔️ MC: {axis_anchor}"))
        closing_bits.append(
            _clean_sentence(
                f"Зрелый режим здесь — {best_mode_desc}"
                if best_mode_desc
                else "Зрелый режим здесь — двигаться не рывком, а в ясном взрослом ритме"
            )
        )

        blocks.extend([
            {
                "type": "paragraph",
                "text": intro_text,
            },
            {"type": "list", "items": items[:6], "ordered": False},
            {
                "type": "paragraph",
                "text": " ".join(bit for bit in closing_bits if bit),
            },
        ])

    # Synthesis fallback
    elif spec.section_id == "synthesis":
        blocks.extend([
            {"type": "callout", "variant": "quote", "title": "Образ карты", "content": _format_insight_value(insight_pack.get("map_metaphor_seed"))},
            {"type": "paragraph", "text": _format_insight_value(insight_pack.get("core_life_story"))},
            {"type": "paragraph", "text": f"**Главный тезис:** {_format_insight_value(insight_pack.get('core_conflict'))}"},
        ])

    # Framework elements fallback
    elif spec.section_id == "framework_elements_modes":
        balance_list = [f"{k} - {v}%" for k, v in insight_pack.get("element_rank", {}).items()]
        blocks.append({"type": "list", "items": balance_list, "ordered": False})
        blocks.append({"type": "paragraph", "text": f"**Доминанта:** {_format_insight_value(insight_pack.get('dominant_signature'))}"})
        blocks.append({"type": "paragraph", "text": f"**Дефицит:** {_format_insight_value(insight_pack.get('deficit_signature'))}"})
        blocks.append({"type": "paragraph", "text": f"**Стиль жизни:** {_format_insight_value(insight_pack.get('lifestyle_vector'))}"})
        blocks.append({"type": "paragraph", "text": f"**Формула баланса:** {_format_insight_value(insight_pack.get('balance_formula'))}"})

    # Axes truths fallback
    elif spec.section_id == "axes_truths":
        for axis in insight_pack.get("axis_polarities", [])[:4]:
            axis_name = axis.get("axis", "")
            your_truth = axis.get("your_truth", "")
            partner_truth = axis.get("partner_truth", "")
            task = axis.get("task", "")
            blocks.append({"type": "header", "level": 3, "text": f"Ось {axis_name}"})
            blocks.append({"type": "list", "items": [f"Твоя правда: {your_truth}", f"Правда партнера: {partner_truth}", f"Задача: {task}"], "ordered": False})

    # Aspects beginner fallback
    elif spec.section_id == "aspects_beginner":
        for card in insight_pack.get("aspect_cards", [])[:5]:
            anchor = card.get("anchor", "")
            scenario = card.get("scenario", "")
            resource = card.get("resource", "")
            blocks.append({"type": "header", "level": 3, "text": anchor})
            blocks.append({"type": "list", "items": [f"Сценарий: {scenario}", f"Ресурс: {resource}"], "ordered": False})

    # Configurations fallback
    elif spec.section_id == "configurations_geometry":
        cards = insight_pack.get("configuration_cards", [])
        if cards:
            for card in cards[:3]:
                geometry = card.get("geometry", "")
                gift = card.get("gift", "")
                risk = card.get("risk", "")
                blocks.append({"type": "header", "level": 3, "text": geometry})
                blocks.append({"type": "list", "items": [f"Дар: {gift}", f"Риск: {risk}"], "ordered": False})
        else:
            blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("absence_summary", "В карте нет устойчивых конфигураций."))})

    # Dispositor office fallback
    elif spec.section_id == "dispositor_office":
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("engine_summary"))})
        for office in insight_pack.get("office_map", [])[:3]:
            ruler = office.get("ruler", "")
            role = office.get("role", "")
            blocks.append({"type": "paragraph", "text": f"**{ruler}** управляет: {role}"})
        bosses = insight_pack.get("final_bosses", [])
        if bosses:
            blocks.append({"type": "callout", "variant": "info", "title": "Главный Босс", "content": ", ".join(bosses)})

    # Core triad fallback
    elif spec.section_id == "core_triad":
        asc_mask = insight_pack.get("asc_mask", {})
        solar_drive = insight_pack.get("solar_drive", {})
        lunar_need = insight_pack.get("lunar_need", {})
        blocks.append({"type": "header", "level": 3, "text": f"⬆️ ASC: {_format_insight_value(asc_mask.get('label'))}"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(asc_mask.get('mode'))})
        blocks.append({"type": "header", "level": 3, "text": f"☀️ Солнце: {_format_insight_value(solar_drive.get('label'))}"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(solar_drive.get('drive'))})
        blocks.append({"type": "header", "level": 3, "text": f"🌙 Луна: {_format_insight_value(lunar_need.get('label'))}"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(lunar_need.get('need'))})
        triad_info = insight_pack.get("triad_integration", {})
        blocks.append({"type": "callout", "variant": "info", "title": "Сборка ядра", "content": _format_insight_value(triad_info.get("summary") or triad_info.get("steps"))})

    # Mercury mind fallback
    elif spec.section_id == "mercury_mind":
        blocks.append({"type": "header", "level": 3, "text": "☿ Меркурий"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("thinking_style"))})
        blocks.append({"type": "list", "items": [
            f"**Стиль:** {_format_insight_value(insight_pack.get('thinking_style'))}",
            f"**Режим:** {_format_insight_value(insight_pack.get('processing_mode'))}",
            f"**Ловушка:** {_format_insight_value(', '.join(insight_pack.get('cognitive_risks', [])))}",
            f"**Ключ:** {_format_insight_value(', '.join(insight_pack.get('mind_keys', [])))}"
        ], "ordered": False})

    # Shadow trauma fallback
    elif spec.section_id == "shadow_trauma":
        chiron_pattern = insight_pack.get("chiron_pattern", {})
        lilith_pattern = insight_pack.get("lilith_pattern", {})
        blocks.append({"type": "header", "level": 3, "text": f"⚷ Хирон: {_format_insight_value(chiron_pattern.get('anchor'))}"})
        blocks.append({"type": "list", "items": [
            f"**Сценарий:** {_format_insight_value(chiron_pattern.get('scenario'))}",
            f"**Ресурс:** {_format_insight_value(chiron_pattern.get('resource'))}"
        ], "ordered": False})
        blocks.append({"type": "header", "level": 3, "text": f"⚸ Лилит: {_format_insight_value(lilith_pattern.get('anchor'))}"})
        blocks.append({"type": "list", "items": [
            f"**Сценарий:** {_format_insight_value(lilith_pattern.get('scenario'))}",
            f"**Ресурс:** {_format_insight_value(lilith_pattern.get('resource'))}"
        ], "ordered": False})
        blocks.append({"type": "callout", "variant": "info", "title": "Задача интеграции", "content": _format_insight_value(insight_pack.get("integration_task"))})

    # Nodes growth fallback
    elif spec.section_id == "nodes_growth":
        blocks.append({"type": "header", "level": 3, "text": f"☊ Северный узел"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("north_node_direction"))})
        blocks.append({"type": "list", "items": [
            f"**Миссия:** {_format_insight_value(insight_pack.get('north_node_direction'))}"
        ], "ordered": False})
        blocks.append({"type": "header", "level": 3, "text": f"☋ Южный узел"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("south_node_habit"))})
        blocks.append({"type": "list", "items": [
            f"**Ловушка:** {_format_insight_value(insight_pack.get('south_node_habit'))}"
        ], "ordered": False})
        blocks.append({"type": "callout", "variant": "info", "title": "Мост", "content": _format_insight_value(insight_pack.get("bridge_task"))})

    # Vertex fate fallback
    elif spec.section_id == "vertex_fate":
        blocks.append({"type": "header", "level": 3, "text": "✴️ Вертекс"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("vertex_signature"))})
        blocks.append({"type": "list", "items": [
            f"**Триггеры встреч:** {_format_insight_value(', '.join(insight_pack.get('encounter_triggers', [])))}",
            f"**Вектор:** {_format_insight_value(insight_pack.get('relationship_vector'))}"
        ], "ordered": False})
        blocks.append({"type": "callout", "variant": "quote", "title": "Урок судьбы", "content": _format_insight_value(insight_pack.get("fated_lesson"))})

    # Balance wheel fallback
    elif spec.section_id in {"balance_wheel_1_6", "balance_wheel_7_12"}:
        for house in insight_pack.get("house_pack", []):
            h_num = house.get("house", "")
            h_theme = house.get("theme", "")
            blocks.append({"type": "header", "level": 3, "text": f"{h_num} Дом"})
            blocks.append({"type": "list", "items": [
                f"**Тема:** {h_theme}",
                f"**В плюсе:** {house.get('plus', '')}",
                f"**В минусе:** {house.get('minus', '')}",
                f"**Триггер:** {house.get('trigger', '')}",
                f"**Вектор зрелости:** {house.get('growth_vector', '')}"
            ], "ordered": False})

    # Love intimacy fallback
    elif spec.section_id == "love_intimacy":
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("relationship_theme"))})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("relationship_manifestations"))})
        items = []
        if insight_pack.get("self_sabotage_pattern"):
            items.append(f"**Ловушка:** {insight_pack['self_sabotage_pattern']}")
        if insight_pack.get("what_to_do"):
            items.extend(_format_list_items(insight_pack['what_to_do']))
        if items:
            blocks.append({"type": "list", "items": items, "ordered": False})
        blocks.append({"type": "paragraph", "text": f"**Зрелый режим:** {_format_insight_value(insight_pack.get('best_mode_of_action'))}"})

    # Money realization fallback
    elif spec.section_id == "money_realization":
        blocks.append({"type": "paragraph", "text": f"**Вектор карьеры:** {_format_insight_value(insight_pack.get('career_vector'))}"})
        blocks.append({"type": "paragraph", "text": f"**Паттерн денег:** {_format_insight_value(insight_pack.get('money_pattern'))}"})
        items = []
        if insight_pack.get("work_risk_flags"):
            items.append(f"**Риски:** {', '.join(insight_pack['work_risk_flags'])}")
        if items:
            blocks.append({"type": "list", "items": items, "ordered": False})
        blocks.append({"type": "paragraph", "text": f"**Режим реализации:** {_format_insight_value(insight_pack.get('realization_mode'))}"})

    # Stars transuranus fallback
    elif spec.section_id == "stars_transuranus":
        for planet, vec_key in [("⚅ Уран", "uranus_vector"), ("⛆ Нептун", "neptune_vector"), ("⯓ Плутон", "pluto_vector")]:
            vec = insight_pack.get(vec_key, {})
            mode = vec.get("mode", "")
            gift = vec.get("gift", "")
            risk = vec.get("risk", "")
            key = vec.get("key", "")
            blocks.append({"type": "header", "level": 3, "text": planet})
            blocks.append({"type": "paragraph", "text": f"**Режим:** {mode}"})
            blocks.append({"type": "list", "items": [f"**Дар:** {gift}", f"**Риск:** {risk}", f"**Ключ:** {key}"], "ordered": False})

    # Time cycles fallback
    elif spec.section_id == "time_cycles":
        age_info = insight_pack.get("current_age", {})
        cycles = insight_pack.get("cycle_markers", [])
        blocks.append({"type": "paragraph", "text": f"**Текущий период:** {_format_insight_value(age_info.get('summary', age_info.get('years')))}"})
        if cycles:
            blocks.append({"type": "list", "items": [f"**Цикл:** {c}" for c in cycles[:3]], "ordered": False})
        sj_phase = insight_pack.get("saturn_jupiter_phase", "")
        if sj_phase:
            blocks.append({"type": "callout", "variant": "info", "title": "Сатурн-Юпитер фаза", "content": sj_phase})
        growth = insight_pack.get("growth_tension", "")
        if growth:
            blocks.append({"type": "callout", "variant": "warning", "title": "Напряжение роста", "content": growth})

    # Final synthesis fallback
    elif spec.section_id == "final_synthesis":
        motto = _format_insight_value(insight_pack.get("final_motto_seed"))
        advice = _format_insight_value(insight_pack.get("one_sentence_advice"))
        blocks.append({
            "type": "callout",
            "variant": "success",
            "title": "Финальная сборка",
            "content": f"**Девиз:** {motto}\n**Главный совет:** {advice}"
        })

    # Default: minimal but section-aware
    else:
        blocks.append({
            "type": "callout",
            "variant": "warning",
            "title": "Временное содержание",
            "content": f"Секция '{title}' требует донастройки. Данные insight_pack загружены, но вербализация требует перезапуска."
        })

    return json.dumps(blocks, ensure_ascii=False)


def _clean_sentence(text: Any) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def _strip_known_prefixes(text: Any, patterns: list[str]) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    for pattern in patterns:
        candidate = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE).strip(" ,:;-")
        if candidate and candidate != cleaned:
            return candidate
    return cleaned


def _normalize_executive_fragment(text: Any, patterns: list[str]) -> str:
    cleaned = _strip_known_prefixes(text, patterns)
    if not cleaned:
        return ""
    return re.sub(r"^[—–-]+\s*", "", cleaned).strip()


def _strip_fact_anchor_parentheticals(text: Any) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    while True:
        updated = re.sub(r"\s*\([^()]*\)", "", cleaned)
        if updated == cleaned:
            break
        cleaned = updated
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*;\s*", "; ", cleaned)
    return cleaned.strip(" ;,")


def _build_final_synthesis_fact_anchor(insight_pack: dict, *, include_axis: bool = True) -> str:
    sun_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("sun_vector")))
    moon_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("moon_vector")))
    if not sun_line:
        sun_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("solar_drive")))
    if not moon_line:
        moon_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("lunar_need")))

    axis_line = ""
    if include_axis:
        axis_line = _strip_fact_anchor_parentheticals(
            _format_insight_value(insight_pack.get("asc_mc_axis"))
        )
        if not axis_line:
            axis_line = _strip_fact_anchor_parentheticals(
                _format_insight_value(insight_pack.get("closing_bridge"))
            )

    fragments = []
    if sun_line:
        fragments.append(_clean_sentence(f"☀️ Солнце: {sun_line}"))
    if moon_line:
        fragments.append(_clean_sentence(f"🌙 Луна: {moon_line}"))
    if axis_line:
        fragments.append(_clean_sentence(f"⬆️ ASC / 🏔️ MC: {axis_line}"))
    return " ".join(part for part in fragments if part).strip()


def _build_timed_final_synthesis_content(insight_pack: dict) -> str:
    motto_raw = _format_insight_value(insight_pack.get("final_motto_seed"))
    integration_raw = _strip_fact_anchor_parentheticals(
        _format_insight_value(insight_pack.get("integration_focus"))
    )
    bridge = insight_pack.get("closing_bridge") or {}
    work_line = str(bridge.get("work_line") or "").strip()
    love_line = str(bridge.get("love_line") or "").strip()
    fallback_advice = _format_insight_value(insight_pack.get("one_sentence_advice"))

    motto_parts = []
    for index, part in enumerate(re.split(r"\s*;\s*", motto_raw)):
        chunk = part.strip(" ,;")
        if not chunk:
            continue
        if index == 0:
            motto_parts.append(_clean_sentence(chunk))
            continue
        chunk = re.sub(
            r"^режим\s+карты\s*[—:-]\s*",
            "Зрелый ход этой карты: ",
            chunk,
            count=1,
            flags=re.IGNORECASE,
        )
        motto_parts.append(_clean_sentence(chunk))
    motto_text = " ".join(motto_parts).strip()
    if not motto_text:
        motto_text = _clean_sentence("Держи сильную сторону карты в ясном взрослом ритме")
    fact_anchor = _build_final_synthesis_fact_anchor(insight_pack, include_axis=True)
    if fact_anchor:
        motto_text = f"{motto_text} {fact_anchor}".strip()

    advice_parts = []
    for part in re.split(r"\s*;\s*", integration_raw):
        chunk = part.strip(" ,;")
        if not chunk:
            continue
        chunk = re.sub(
            r"^твоя\s+сила\s+максимальна,\s+когда\b",
            "Сильная версия этой карты раскрывается, когда",
            chunk,
            count=1,
            flags=re.IGNORECASE,
        )
        chunk = re.sub(
            r"^большой\s+образ\s+должен\s+получать\b",
            "Большому образу важно сразу давать",
            chunk,
            count=1,
            flags=re.IGNORECASE,
        )
        advice_parts.append(_clean_sentence(chunk))
    if work_line:
        advice_parts.append(_clean_sentence(f"В работе {work_line}"))
    if love_line:
        advice_parts.append(_clean_sentence(f"В близости {love_line}"))
    if not advice_parts and fallback_advice:
        advice_parts.append(_clean_sentence(fallback_advice))
    advice_text = " ".join(advice_parts).strip()
    if fact_anchor and fact_anchor not in advice_text:
        advice_text = f"{fact_anchor} {advice_text}".strip()

    blocks = [
        {
            "type": "callout",
            "variant": "success",
            "title": "Финальная сборка",
            "content": f"**Девиз:** {motto_text}\n**Главный совет:** {advice_text}",
        }
    ]
    return json.dumps(blocks, ensure_ascii=False)


def _build_untimed_final_synthesis_content(insight_pack: dict) -> str:
    motto = _clean_sentence(_format_insight_value(insight_pack.get("final_motto_seed")))
    advice = _clean_sentence(_format_insight_value(insight_pack.get("one_sentence_advice")))
    bridge = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("closing_bridge")))
    fact_anchor = _build_final_synthesis_fact_anchor(insight_pack, include_axis=False)

    content_parts = []
    if motto:
        content_parts.append(f"**Девиз:** {motto}")
    elif fact_anchor:
        content_parts.append(f"**Девиз:** {fact_anchor}")

    advice_parts = []
    if fact_anchor:
        advice_parts.append(fact_anchor)
    if bridge:
        advice_parts.append(_clean_sentence(bridge))
    if advice:
        advice_parts.append(advice)
    if not advice_parts:
        advice_parts.append("**Главный совет:** Держи сильную сторону карты в живом и проверяемом ритме.")
    else:
        advice_parts[0] = f"**Главный совет:** {advice_parts[0]}"

    blocks = [{
        "type": "callout",
        "variant": "success",
        "title": "Финальная сборка",
        "content": "\n".join(content_parts + advice_parts),
    }]
    return json.dumps(blocks, ensure_ascii=False)


def _build_timed_natal_executive_summary_content(insight_pack: dict) -> str:
    scene_seed = ""
    for scene in insight_pack.get("scene_seeds", []):
        if isinstance(scene, dict) and str(scene.get("seed", "")).strip():
            scene_seed = str(scene.get("seed")).strip()
            break
    if not scene_seed:
        for manifestation in insight_pack.get("life_manifestations", []):
            if isinstance(manifestation, dict) and str(manifestation.get("label", "")).strip():
                scene_seed = str(manifestation.get("label")).strip()
                break

    strength_desc = _format_insight_value(insight_pack.get("strengths_score"))
    risk_desc = _format_insight_value(insight_pack.get("risk_score"))
    relationship_desc = _format_insight_value(insight_pack.get("relationship_theme"))
    money_desc = _format_insight_value(insight_pack.get("money_theme"))
    development_desc = _format_insight_value(insight_pack.get("development_focus"))
    best_mode_desc = _format_insight_value(insight_pack.get("best_mode_of_action"))
    stress_desc = _format_insight_value(insight_pack.get("stress_manifestation"))
    practical_hint = _pick_first_action_item(insight_pack.get("what_to_do"))
    sun_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("sun_vector")))
    moon_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("moon_vector")))
    axis_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("asc_mc_axis")))
    stress_desc = _normalize_executive_fragment(
        stress_desc,
        [r"^под\s+стрессом\b", r"^под\s+давлением\b"],
    )
    relationship_desc = _normalize_executive_fragment(
        relationship_desc,
        [
            r"^в\s+отношениях\b",
            r"^отношения\s+(?:раскрываются|строятся|держатся)\s+через\b",
            r"^близость\s+раскрывается\s+через\b",
        ],
    )
    money_desc = _normalize_executive_fragment(
        money_desc,
        [
            r"^деньги\s+лучше\s+всего\s+приходят\s+через\b",
            r"^лучше\s+всего\s+приходят\s+через\b",
            r"^работа\s+и\s+деньги\s+(?:идут|приходят|строятся)\s+через\b",
            r"^в\s+деньгах\s+и\s+работе\b",
            r"^в\s+работе\s+и\s+деньгах\b",
            r"^деньги\b",
        ],
    )
    best_mode_desc = _normalize_executive_fragment(
        best_mode_desc,
        [r"^лучший\s+режим\s+действия\b", r"^лучший\s+режим\b", r"^зрелый\s+режим\b"],
    )

    intro_parts = []
    scene_line = _clean_sentence(scene_seed)
    if scene_line:
        intro_parts.append(scene_line)
    if strength_desc:
        intro_parts.append(_clean_sentence(f"Сильнее всего карта раскрывается там, где {strength_desc}"))
    if sun_anchor:
        intro_parts.append(_clean_sentence(f"☀️ Солнце: {sun_anchor}"))
    if moon_anchor:
        intro_parts.append(_clean_sentence(f"🌙 Луна: {moon_anchor}"))
    if stress_desc:
        intro_parts.append(_clean_sentence(f"Под давлением особенно видно, как {stress_desc}"))
    intro_text = " ".join(part for part in intro_parts if part).strip()
    if not intro_text:
        intro_text = (
            "Карта собирается вокруг сильного внутреннего паттерна, который важно переводить "
            "в живое действие без перегиба."
        )

    items = []
    if strength_desc:
        items.append(_clean_sentence(f"Сильная опора здесь в том, что {strength_desc}"))
    if risk_desc:
        items.append(_clean_sentence(f"Перегиб включается через {risk_desc}"))
    if relationship_desc:
        items.append(_clean_sentence(f"Отношения держатся на том, что {relationship_desc}"))
    if money_desc:
        items.append(_clean_sentence(f"Деньги и реализация растут через {money_desc}"))
    if axis_anchor:
        items.append(_clean_sentence(f"⬆️ ASC / 🏔️ MC задают социальную ось: {axis_anchor}"))
    if development_desc:
        items.append(_clean_sentence(f"Фокус роста сейчас — {development_desc}"))
    if practical_hint:
        items.append(_clean_sentence(f"Практический ход на сейчас — {practical_hint}"))

    closing_text = _clean_sentence(
        f"Зрелый режим здесь — {best_mode_desc}"
        if best_mode_desc
        else "Зрелый режим здесь — двигаться не рывком, а в ясном зрелом ритме"
    )

    blocks = [
        {"type": "paragraph", "text": intro_text},
        {"type": "list", "items": items, "ordered": False},
        {"type": "paragraph", "text": closing_text},
    ]
    return json.dumps(blocks, ensure_ascii=False)


def _format_insight_value(value: Any) -> str:
    """Format insight value for display, handling dicts, lists, and strings."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("label", "text", "seed", "summary", "content"):
            text = str(value.get(key, "")).strip()
            if text:
                return text
        items = value.get("items")
        if isinstance(items, list):
            preview = [str(item).strip() for item in items if str(item).strip()]
            if preview:
                return ", ".join(preview[:2])
        return str(value)
    if isinstance(value, list):
        if len(value) == 0:
            return ""
        first = value[0]
        if isinstance(first, dict):
            return str(
                first.get("label")
                or first.get("text")
                or first.get("seed")
                or first.get("value")
                or first
            )
        return str(first)
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def _format_list_items(items: Any) -> list:
    """Format insight pack list items for display."""
    if isinstance(items, list):
        return [
            f"• {item}" if isinstance(item, str) else f"• {_format_insight_value(item)}"
            for item in items[:5]
            if _format_insight_value(item if not isinstance(item, str) else {"label": item}) or isinstance(item, str)
        ]
    if isinstance(items, dict):
        nested_items = items.get("items")
        if isinstance(nested_items, list):
            return _format_list_items(nested_items)
        formatted = _format_insight_value(items)
        return [f"• {formatted}"] if formatted else []
    return []


def _pick_first_action_item(items: Any) -> str:
    """Extract the first human-readable action from insight-pack list fields."""
    if isinstance(items, dict):
        nested_items = items.get("items")
        if isinstance(nested_items, list):
            return _pick_first_action_item(nested_items)
        return _format_insight_value(items)
    if isinstance(items, list):
        for item in items:
            if isinstance(item, str) and item.strip():
                return item.strip()
            text = _format_insight_value(item)
            if text:
                return text
        return ""
    return _format_insight_value(items)


def _collect_fact_anchor_evidence(*sources: Any, limit: int = 2) -> List[str]:
    anchors: List[str] = []
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        evidence = source.get("evidence")
        if not isinstance(evidence, list):
            continue
        for raw in evidence:
            text = str(raw or "").strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            anchors.append(text)
            if len(anchors) >= limit:
                return anchors
    return anchors


def _extract_named_anchor(*sources: Any, names: tuple[str, ...]) -> str:
    normalized_names = tuple(name.lower() for name in names if name)
    for source in sources:
        if not isinstance(source, dict):
            continue
        evidence = source.get("evidence")
        if not isinstance(evidence, list):
            continue
        for raw in evidence:
            text = str(raw or "").strip()
            lowered = text.lower()
            if text and any(name in lowered for name in normalized_names):
                return text
    return ""


def _compose_fact_first_fragment(
    text: Any,
    *sources: Any,
    limit: int = 1,
    prefix_patterns: Optional[list[str]] = None,
) -> str:
    cleaned = _normalize_executive_fragment(text, prefix_patterns or [])
    anchors = _collect_fact_anchor_evidence(*sources, limit=limit)
    if anchors:
        anchor_text = "; ".join(anchors)
        if cleaned:
            return f"{cleaned} ({anchor_text})"
        return anchor_text
    return cleaned


def build_section_validation_fallback_content(spec: SectionSpec, context: dict) -> str:
    if spec.section_id in {"week_strategy", "month_full_forecast", "month_theme"}:
        return build_section_fallback_content(spec, context)
    # For natal sections, use insight_pack-aware fallback instead of generic template
    # This ensures meaningful content even when LLM validation fails
    if spec.section_id in NATAL_SECTION_IDS or spec.section_id == "executive_summary":
        insight_pack = (context.get("section_context") or {}).get("insight_pack")
        if insight_pack:
            if spec.section_id == "executive_summary":
                if context.get("client", {}).get("birth_time_known", True):
                    return _build_timed_natal_executive_summary_content(insight_pack)
                return _build_insight_pack_fallback_content(spec, insight_pack)
            if spec.section_id == "final_synthesis" and context.get("client", {}).get("birth_time_known", True):
                return _build_timed_final_synthesis_content(insight_pack)
            if spec.section_id == "final_synthesis":
                return _build_untimed_final_synthesis_content(insight_pack)
            return _build_insight_pack_fallback_content(spec, insight_pack)
    return build_section_template_content(spec)
# END_BLOCK: VALIDATION_FALLBACK
