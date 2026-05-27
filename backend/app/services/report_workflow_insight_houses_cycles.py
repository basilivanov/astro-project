# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-HOUSES-CYCLES
# purpose: Build house-wheel, balance, time-cycle, and axes natal insight packs.
# inputs: compact chart_pack dictionaries and client/forecast context.
# outputs: insight_pack dictionaries for house, cycle, and axis sections.
# invariants: house domain and cycle age calculations remain unchanged.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-HOUSES-CYCLES

# START_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-HOUSES-CYCLES
# entrypoints:
#   - _build_balance_wheel_insight_pack -> BALANCE_WHEEL_PACK
#   - _build_time_cycles_insight_pack -> TIME_CYCLES_PACK
#   - _build_axes_truths_insight_pack -> AXES_TRUTHS_PACK
# END_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-HOUSES-CYCLES

from __future__ import annotations

from datetime import datetime, timezone

from .report_workflow_insight_core import *
from .report_workflow_insight_synthesis import _build_house_tenants, _format_planet_name_list

# START_BLOCK: INSIGHT_HOUSE_CYCLE_PACKS
def _describe_house_item(
    house_number: int,
    house_lookup: Dict[int, dict],
    position_lookup: Dict[str, dict],
    house_tenants: Dict[int, List[str]],
) -> Optional[Dict[str, Any]]:
    snapshot = _build_house_snapshot(house_lookup, position_lookup, house_number)
    if not snapshot:
        return None

    sign = snapshot.get("sign")
    ruler = snapshot.get("ruler")
    ruler_position = snapshot.get("ruler_position") or {}
    sign_hint = SIGN_STYLE_HINTS.get(sign, {})
    tenants = house_tenants.get(house_number, [])
    occupant_roles = [PLANET_ROLE_HINTS.get(name, name) for name in tenants[:3]]
    occupant_labels = [_format_planet_name_list(tenants)] if tenants else []

    theme = (
        f"{HOUSE_DOMAIN_MAP.get(house_number, 'тема дома')} "
        f"через {sign_hint.get('tone', 'свой природный ритм')}"
    )

    plus_parts = [sign_hint.get("plus", "ресурс дома")]
    if ruler_position.get("h") in {1, 4, 7, 10}:
        plus_parts.append("тема дома видна и влияет на маршрут напрямую")
    if any(name in tenants for name in ["Sun", "Venus", "Jupiter", "ASC", "MC"]):
        plus_parts.append("есть дополнительная видимость или поддержка изнутри дома")

    minus_parts = [sign_hint.get("minus", "теневая сторона дома")]
    if ruler_position.get("h") in {8, 12}:
        minus_parts.append("тема легко уходит в скрытое напряжение или откладывание")
    if any(name in tenants for name in ["Saturn", "Mars", "Pluto", "Neptune"]):
        minus_parts.append("внутри дома есть точка давления, борьбы или размывания")

    trigger = (
        f"активируется через темы {HOUSE_DOMAIN_MAP.get(ruler_position.get('h'), 'дома управителя')}"
        if ruler_position.get("h")
        else "активируется, когда дом затрагивает базовую жизненную тему"
    )
    if tenants:
        trigger += f"; внутри дома это особенно заметно через {_format_planet_name_list(tenants)}"

    growth_vector = sign_hint.get("growth", "учиться удерживать дом в зрелом режиме")
    if ruler_position.get("h"):
        growth_vector += f"; связывать это с темой {HOUSE_DOMAIN_MAP.get(ruler_position.get('h'), 'дома управителя')}"

    evidence = [
        _format_house_snapshot(snapshot),
        _format_position_evidence(ruler_position),
        (
            f"планеты в доме: {_format_planet_name_list(tenants)}"
            if tenants
            else "дом без планет, опора идет через управителя"
        ),
    ]

    return {
        "house": house_number,
        "domain": HOUSE_DOMAIN_MAP.get(house_number),
        "cusp_sign": sign,
        "ruler": ruler,
        "ruler_house": ruler_position.get("h"),
        "ruler_sign": ruler_position.get("s"),
        "occupants": tenants,
        "theme": theme,
        "plus": "; ".join(part for part in plus_parts if part),
        "minus": "; ".join(part for part in minus_parts if part),
        "trigger": trigger,
        "growth_vector": growth_vector,
        "ruler_story": _format_house_snapshot(snapshot),
        "occupant_roles": occupant_roles,
        "evidence": [item for item in evidence if item][:4],
    }


def _build_balance_wheel_insight_pack(
    section_id: str,
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    house_numbers = [1, 2, 3, 4, 5, 6] if section_id == "balance_wheel_1_6" else [7, 8, 9, 10, 11, 12]
    house_tenants = _build_house_tenants(chart_data)
    house_pack = []
    activation = []
    sensitive = []

    for house_number in house_numbers:
        item = _describe_house_item(
            house_number,
            house_lookup,
            position_lookup,
            house_tenants,
        )
        if not item:
            continue
        house_pack.append(item)
        score = len(item.get("occupants", []))
        if item.get("ruler_house") in {1, 4, 7, 10}:
            score += 1
        activation.append((house_number, score))
        if item.get("ruler_house") in {8, 12} or any(
            occupant in item.get("occupants", [])
            for occupant in ["Saturn", "Mars", "Pluto", "Neptune", "Lilith"]
        ):
            sensitive.append(house_number)

    activation.sort(key=lambda item: (item[1], -item[0]), reverse=True)
    zone_summary = {
        "dominant_houses": [item[0] for item in activation[:2] if item[1] > 0],
        "sensitive_houses": sensitive[:2],
        "label": (
            f"самая активная зона: дома {', '.join(str(item[0]) for item in activation[:2] if item[1] > 0)}"
            if any(item[1] > 0 for item in activation[:2])
            else "зона читается в основном через управителей, а не через скопления планет"
        ),
    }

    return {
        "version": "natal_v2_p1",
        "house_pack": house_pack,
        "zone_summary": zone_summary,
        "cross_links": [
            "executive_summary.strengths_score",
            "money_realization.career_vector" if section_id == "balance_wheel_1_6" else "love_intimacy.attachment_style",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value)
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result


def _format_year_delta(delta_years: float) -> str:
    if delta_years >= 0:
        return f"через {delta_years:.1f} лет"
    return f"{abs(delta_years):.1f} лет назад"


def _describe_age_cycle(age_years: float, cycle_years: float, cycle_name: str) -> Dict[str, Any]:
    cycle_index = int(age_years // cycle_years)
    phase_fraction = (age_years / cycle_years) - cycle_index
    if phase_fraction < 0.25:
        phase_label = "старт нового витка"
    elif phase_fraction < 0.5:
        phase_label = "набор инерции и расширение"
    elif phase_fraction < 0.75:
        phase_label = "проверка маршрута и перенастройка"
    else:
        phase_label = "сборка результатов и подготовка к новому перезапуску"
    next_return_age = (cycle_index + 1) * cycle_years
    return {
        "cycle": cycle_name,
        "cycle_index": cycle_index + 1,
        "phase_label": phase_label,
        "age_years": round(age_years, 1),
        "years_to_next_return": round(max(0.0, next_return_age - age_years), 1),
    }


def _build_cycle_markers(age_years: float) -> List[Dict[str, Any]]:
    markers: List[Dict[str, Any]] = []
    cycle_specs = [
        ("return", "возврат Сатурна", 29.46, 0.0),
        ("opposition", "оппозиция Сатурна", 29.46, 14.73),
        ("return", "возврат Юпитера", 11.86, 0.0),
        ("return", "возврат Узлов", 18.6, 0.0),
        ("opposition", "оппозиция Узлов", 18.6, 9.3),
    ]
    for marker_type, label, cycle_years, offset in cycle_specs:
        index = 0
        while True:
            age_at = offset + cycle_years * index
            if age_at <= 0:
                index += 1
                continue
            if age_at > age_years + 15:
                break
            markers.append(
                {
                    "type": marker_type,
                    "label": label,
                    "age_at": round(age_at, 1),
                    "delta_years": round(age_at - age_years, 1),
                }
            )
            index += 1
    markers.sort(key=lambda item: abs(item.get("delta_years", 0.0)))
    return markers[:5]


def _build_time_cycles_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
    client: Optional[dict],
    forecast_window: Optional[dict],
) -> Dict[str, Any]:
    birth_dt = _parse_iso_datetime((client or {}).get("birth_date"))
    current_dt = _parse_iso_datetime((forecast_window or {}).get("start"))
    age_years = 0.0
    if birth_dt and current_dt:
        age_years = max(0.0, (current_dt - birth_dt).total_seconds() / (365.2425 * 24 * 3600))

    saturn = position_lookup.get("Saturn")
    jupiter = position_lookup.get("Jupiter")
    node = position_lookup.get("North Node") or position_lookup.get("True Node")

    saturn_phase = _describe_age_cycle(age_years, 29.46, "Saturn")
    jupiter_phase = _describe_age_cycle(age_years, 11.86, "Jupiter")
    node_phase = _describe_age_cycle(age_years, 18.6, "Nodes")
    cycle_markers = _build_cycle_markers(age_years)
    top_marker = cycle_markers[0] if cycle_markers else {}

    saturn_focus = HOUSE_DOMAIN_MAP.get((saturn or {}).get("h"), "темы зрелости и рамок")
    jupiter_focus = HOUSE_DOMAIN_MAP.get((jupiter or {}).get("h"), "темы роста и расширения")
    node_focus = HOUSE_DOMAIN_MAP.get((node or {}).get("h"), "темы вектора роста")

    if top_marker and abs(top_marker.get("delta_years", 99.0)) <= 1.5:
        summary_label = (
            f"сейчас активно окно {top_marker.get('label')}: период требует "
            f"переоценить {saturn_focus.lower()} и связать это с {jupiter_focus.lower()}"
        )
        summary_key = "active_marker_window"
    else:
        summary_label = (
            f"текущий период читается как {saturn_phase.get('phase_label')} по Сатурну "
            f"на фоне фазы '{jupiter_phase.get('phase_label')}' по Юпитеру"
        )
        summary_key = "age_phase_summary"

    maturity_cycle_summary = {
        "key": summary_key,
        "label": summary_label,
        "score": _score_to_int(100 - abs(top_marker.get("delta_years", 3.0)) * 18 if top_marker else 58),
        "evidence": [
            f"возраст {age_years:.1f} лет",
            (
                f"ближайший маркер: {top_marker.get('label')} ({_format_year_delta(top_marker.get('delta_years', 0.0))})"
                if top_marker
                else None
            ),
            _format_position_evidence(saturn),
            _format_position_evidence(jupiter),
        ][:4],
    }

    saturn_jupiter_phase = {
        "saturn": {
            **saturn_phase,
            "focus": saturn_focus,
            "evidence": [_format_position_evidence(saturn)],
        },
        "jupiter": {
            **jupiter_phase,
            "focus": jupiter_focus,
            "evidence": [_format_position_evidence(jupiter)],
        },
        "node": {
            **node_phase,
            "focus": node_focus,
            "evidence": [_format_position_evidence(node)],
        },
    }

    growth_tension = {
        "key": "saturn_jupiter_node_tension",
        "label": (
            f"главное напряжение роста сейчас между {saturn_focus.lower()}, "
            f"{jupiter_focus.lower()} и требованием не терять {node_focus.lower()}"
        ),
        "score": _score_to_int(60 + (12 if top_marker and abs(top_marker.get("delta_years", 99.0)) <= 2.0 else 0)),
        "evidence": [
            _format_position_evidence(saturn),
            _format_position_evidence(jupiter),
            _format_position_evidence(node),
        ][:4],
    }

    current_age = {
        "years": round(age_years, 1),
        "as_of": current_dt.isoformat() if current_dt else None,
    }

    return {
        "version": "natal_v2_p1",
        "current_age": current_age,
        "cycle_markers": cycle_markers,
        "maturity_cycle_summary": maturity_cycle_summary,
        "saturn_jupiter_phase": saturn_jupiter_phase,
        "growth_tension": growth_tension,
        "cross_links": [
            "executive_summary.development_focus",
            "synthesis.core_conflict",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _build_axes_truths_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    house_tenants = _build_house_tenants(chart_data)
    axis_specs = [
        (1, 7, "identity_vs_partner", "ASC-DSC"),
        (4, 10, "private_base_vs_public_role", "IC-MC"),
        (2, 8, "ownership_vs_merging", "2-8"),
        (5, 11, "self_expression_vs_collective", "5-11"),
    ]
    axis_polarities = []
    axis_tasks = []
    tension_scores = []

    for left_house, right_house, axis_key, axis_label in axis_specs:
        left = _build_house_snapshot(house_lookup, position_lookup, left_house)
        right = _build_house_snapshot(house_lookup, position_lookup, right_house)
        if not left or not right:
            continue
        left_hint = SIGN_STYLE_HINTS.get(left.get("sign"), {})
        right_hint = SIGN_STYLE_HINTS.get(right.get("sign"), {})
        left_ruler = left.get("ruler_position") or {}
        right_ruler = right.get("ruler_position") or {}

        your_truth = (
            f"твой полюс тянет к режиму '{left_hint.get('tone', 'естественный ритм')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get(left_house, 'этой оси').lower()}"
        )
        partner_truth = (
            f"противоположный полюс требует '{right_hint.get('tone', 'свою правду')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get(right_house, 'ответной оси').lower()}"
        )
        task = (
            f"{left_hint.get('growth', 'собирать свой полюс в зрелую форму')} "
            f"и дать место теме {HOUSE_DOMAIN_MAP.get(right_house, 'противоположного дома').lower()}"
        )
        evidence = [
            _format_house_snapshot(left),
            _format_house_snapshot(right),
            _format_position_evidence(left_ruler),
            _format_position_evidence(right_ruler),
        ]
        sensitivity = (
            len(house_tenants.get(left_house, []))
            + len(house_tenants.get(right_house, []))
            + (1 if left_ruler.get("h") in {8, 12} else 0)
            + (1 if right_ruler.get("h") in {8, 12} else 0)
        )
        axis_polarities.append(
            {
                "axis": axis_key,
                "axis_label": axis_label,
                "your_truth": your_truth,
                "partner_truth": partner_truth,
                "task": task,
                "evidence": [item for item in evidence if item][:4],
            }
        )
        axis_tasks.append(
            {
                "axis": axis_key,
                "axis_label": axis_label,
                "task": task,
            }
        )
        tension_scores.append((axis_key, axis_label, sensitivity, evidence))

    tension_scores.sort(key=lambda item: item[2], reverse=True)
    dominant_axis_tension = {
        "axis": tension_scores[0][0] if tension_scores else "identity_vs_partner",
        "axis_label": tension_scores[0][1] if tension_scores else "ASC-DSC",
        "label": (
            f"самая чувствительная ось сейчас — {tension_scores[0][1]}"
            if tension_scores
            else "самая чувствительная ось определяется через базовые полярности карты"
        ),
        "score": _score_to_int(45 + (tension_scores[0][2] * 10 if tension_scores else 0)),
        "evidence": [item for item in (tension_scores[0][3] if tension_scores else []) if item][:4],
    }

    return {
        "version": "natal_v2_p2",
        "axis_polarities": axis_polarities,
        "axis_tasks": axis_tasks,
        "dominant_axis_tension": dominant_axis_tension,
        "cross_links": [
            "synthesis.core_conflict",
            "balance_wheel_1_6.house_pack",
            "balance_wheel_7_12.house_pack",
        ],
    }
# END_BLOCK: INSIGHT_HOUSE_CYCLE_PACKS
