# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-SYNTHESIS
# purpose: Build final synthesis and dispositor-office natal insight packs.
# inputs: compact chart_pack dictionaries and summary/domain pack builders.
# outputs: final synthesis, dispositor, and graph dictionaries.
# invariants: final synthesis composition and dispositor graph semantics remain unchanged.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-SYNTHESIS

# START_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-SYNTHESIS
# entrypoints:
#   - _build_final_synthesis_insight_pack -> FINAL_SYNTHESIS_PACK
#   - _build_dispositor_office_insight_pack -> DISPOSITOR_OFFICE_PACK
# END_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-SYNTHESIS

from __future__ import annotations

from .report_workflow_insight_core import *
from .report_workflow_insight_relationships import (
    _build_love_intimacy_insight_pack,
    _build_money_realization_insight_pack,
)
from .report_workflow_insight_summary import (
    _build_executive_summary_insight_pack,
    _build_synthesis_insight_pack,
)

# START_BLOCK: INSIGHT_SYNTHESIS_PACKS
def _build_final_synthesis_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    executive_pack = _build_executive_summary_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    synthesis_pack = _build_synthesis_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    money_pack = _build_money_realization_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    love_pack = _build_love_intimacy_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )

    top_resource = (executive_pack.get("strengths_score") or [{}])[0]
    top_conflict = synthesis_pack.get("core_conflict") or (executive_pack.get("risk_score") or [{}])[0]
    career_vector = money_pack.get("career_vector") or {}
    realization_mode = money_pack.get("realization_mode") or {}
    attachment_style = love_pack.get("attachment_style") or {}
    partnership_needs = love_pack.get("partnership_needs") or {}
    best_mode_of_action = executive_pack.get("best_mode_of_action") or {}

    resource_key = top_resource.get("key")
    conflict_key = top_conflict.get("key")
    career_key = career_vector.get("key")
    realization_key = realization_mode.get("key")
    attachment_key = attachment_style.get("key")
    needs_key = partnership_needs.get("key")

    resource_motto_map = {
        "structured_ambition": "строй опору",
        "intuitive_depth": "слушай глубину",
        "independent_innovation": "обновляй маршрут",
        "resilient_influence": "держи сложность в форме",
    }
    conflict_motto_map = {
        "control_vs_sensitivity": "не цементируй себя контролем",
        "stability_vs_freedom": "не ломай базу ради свободы",
        "depth_vs_distance": "не уходи в дистанцию",
        "vision_vs_grounding": "приземляй образ в факты",
    }
    resource_integration_map = {
        "structured_ambition": "твоя сила максимальна, когда каркас остается живым, а не жестким",
        "intuitive_depth": "твоя сила максимальна, когда чувствительность получает форму, а не туман",
        "independent_innovation": "твоя сила максимальна, когда свобода обновляет систему, а не сжигает опору",
        "resilient_influence": "твоя сила максимальна, когда давление превращается в рычаг, а не в постоянный режим жизни",
    }
    conflict_integration_map = {
        "control_vs_sensitivity": "контроль не должен душить чувствительность",
        "stability_vs_freedom": "поворот должен строиться поверх базы",
        "depth_vs_distance": "глубина не должна уходить в молчаливую дистанцию",
        "vision_vs_grounding": "большой образ должен получать критерии, срок и форму",
    }
    conflict_action_map = {
        "control_vs_sensitivity": "Сначала называй перегруз и потребность, а уже потом ужесточай план",
        "stability_vs_freedom": "Не разворачивай маршрут рывком, пока не собраны база, ритм и запас ресурса",
        "depth_vs_distance": "Начинай важный разговор до того, как уязвимость уйдет в молчание",
        "vision_vs_grounding": "Ставь рядом с интуицией критерии, сроки и проверку реальностью",
    }
    work_anchor_map = {
        "systems_leader": "держи систему, стандарт и длинный горизонт",
        "network_builder": "делай ставку на среду, связи и аудиторию",
        "care_container": "опирайся на полезность, качество и удержание",
        "crisis_specialist": "заходи в сложные кейсы, где другим тяжело",
    }
    work_mode_map = {
        "disciplined_climb": "с ясным ритмом и накоплением статуса",
        "autonomous_project_cycles": "через короткие автономные циклы",
        "community_platform": "через платформу, сеть и совместные инициативы",
        "deep_problem_solving": "через разбор сложных и неоднозначных задач",
    }
    love_anchor_map = {
        "freedom_then_depth": "сначала договаривайся о воздухе и границах, а потом углубляй связь",
        "soft_private_bonding": "сохраняй медленный безопасный темп",
        "steady_tested_commitment": "показывай надежность делом и выдерживай ритм",
        "idealized_merge": "проверяй сильное чувство временем и поступками",
    }
    love_needs_map = {
        "friendship_clarity_loyalty": "с честными договоренностями и лояльностью без игр",
        "safety_time_privacy": "с правом на паузу и эмоциональную безопасность",
        "shared_future_and_work": "с общей целью и уважением к надежности",
        "passion_and_depth": "с доверием к уязвимости и глубине",
    }

    def _merge_focus_line(primary: str, secondary: str) -> str:
        primary = (primary or "").strip()
        secondary = (secondary or "").strip()
        if not primary:
            return secondary
        if not secondary:
            return primary
        if secondary.startswith(("с ", "через ")):
            return f"{primary} {secondary}"
        return f"{primary} и {secondary}"

    work_line = _merge_focus_line(
        work_anchor_map.get(career_key, _format_insight_value(career_vector)),
        work_mode_map.get(realization_key, _format_insight_value(realization_mode)),
    )
    love_line = _merge_focus_line(
        love_anchor_map.get(attachment_key, _format_insight_value(attachment_style)),
        love_needs_map.get(needs_key, _format_insight_value(partnership_needs)),
    )
    work_line = _compose_fact_first_fragment(work_line, career_vector, realization_mode, limit=1)
    love_line = _compose_fact_first_fragment(love_line, attachment_style, partnership_needs, limit=1)
    angle_anchor = _extract_named_anchor(career_vector, realization_mode, names=("asc", "mc", "⬆️", "🏔️"))
    best_mode_fragment = _normalize_executive_fragment(
        _format_insight_value(best_mode_of_action),
        [r"^лучший режим действия\s*[—:-]\s*"],
    )
    resource_fragment = _normalize_executive_fragment(
        _format_insight_value(top_resource),
        [],
    )

    motto_core = "; ".join(
        part
        for part in [
            resource_fragment
            or resource_motto_map.get(resource_key, "собирай свою сильную сторону в действие"),
            f"режим карты — {best_mode_fragment}"
            if best_mode_fragment
            else conflict_motto_map.get(conflict_key, "не отдавай глубину хаосу"),
        ]
        if part
    )
    integration_label = "; ".join(
        part
        for part in [
            _compose_fact_first_fragment(
                resource_integration_map.get(resource_key, top_resource.get("label", "")),
                top_resource,
                limit=1,
            ),
            _compose_fact_first_fragment(
                conflict_integration_map.get(conflict_key, top_conflict.get("label", "")),
                top_conflict,
                limit=1,
            ),
        ]
        if part
    )
    advice_parts = []
    if best_mode_fragment:
        advice_parts.append(f"Зрелый ход этой карты — {best_mode_fragment}")
    advice_parts.append(
        conflict_action_map.get(
            conflict_key,
            "Не отдавай главный внутренний конфликт автопилоту: переводи его в ясное решение",
        )
    )
    bridge_parts = []
    if work_line:
        bridge_parts.append(f"в работе {work_line}")
    if love_line:
        bridge_parts.append(f"в близости {love_line}")
    if bridge_parts:
        advice_parts.append("; ".join(bridge_parts))
    advice_text = " ".join(
        _clean_sentence(part)
        for part in advice_parts
        if str(part or "").strip()
    ).strip()
    integration_key = "_".join(
        part for part in [resource_key or "resource", conflict_key or "conflict"] if part
    )

    integration = {
        "key": integration_key,
        "label": integration_label,
        "evidence": [
            *(top_resource.get("evidence", [])[:2]),
            *(top_conflict.get("evidence", [])[:2]),
            *(best_mode_of_action.get("evidence", [])[:1] if best_mode_of_action else []),
            *(career_vector.get("evidence", [])[:1] if career_vector else []),
            *(attachment_style.get("evidence", [])[:1] if attachment_style else []),
            *(partnership_needs.get("evidence", [])[:1] if partnership_needs else []),
        ][:6],
    }
    sun_anchor = _extract_named_anchor(
        top_resource,
        top_conflict,
        best_mode_of_action,
        integration,
        names=("солнце", "☀️"),
    )
    moon_anchor = _extract_named_anchor(
        top_resource,
        top_conflict,
        best_mode_of_action,
        integration,
        names=("луна", "🌙"),
    )
    if not sun_anchor and "солнце" in integration_label.lower():
        sun_anchor = "☀️ Солнце"
    if not moon_anchor and "луна" in integration_label.lower():
        moon_anchor = "🌙 Луна"
    motto_details = [part for part in [sun_anchor, moon_anchor, angle_anchor] if part]
    motto_label = "; ".join(part for part in [motto_core, *motto_details] if part)
    top_conflict_vs_top_resource = {
        "resource": top_resource,
        "conflict": top_conflict,
        "integration": integration,
    }
    closing_bridge = {
        "key": f"{integration_key}_bridge",
        "label": "; ".join(
            part
            for part in [
                f"В работе - {work_line}" if work_line else "",
                f"В близости - {love_line}" if love_line else "",
            ]
            if part
        ),
        "work_line": work_line,
        "love_line": love_line,
        "evidence": [
            *(career_vector.get("evidence", [])[:2] if career_vector else []),
            *(realization_mode.get("evidence", [])[:1] if realization_mode else []),
            *(attachment_style.get("evidence", [])[:2] if attachment_style else []),
            *(partnership_needs.get("evidence", [])[:1] if partnership_needs else []),
        ][:5],
    }
    applied_cross_links = [
        {"path": "executive_summary.strengths_score", "label": top_resource.get("label", "")},
        {"path": "synthesis.core_conflict", "label": top_conflict.get("label", "")},
        {"path": "money_realization.career_vector", "label": career_vector.get("label", "")},
        {"path": "money_realization.realization_mode", "label": realization_mode.get("label", "")},
        {"path": "love_intimacy.attachment_style", "label": attachment_style.get("label", "")},
        {"path": "love_intimacy.partnership_needs", "label": partnership_needs.get("label", "")},
    ]
    integration_focus = {
        "key": f"{integration_key}_focus",
        "label": integration_label,
        "closing_bridge": closing_bridge.get("label", ""),
        "evidence": integration.get("evidence", [])[:6],
    }
    final_motto_seed = {
        "key": f"{integration_key}_motto",
        "label": motto_label,
        "score": _score_to_int(
            (
                top_resource.get("score", 55)
                + top_conflict.get("score", 55)
                + career_vector.get("score", 55)
                + attachment_style.get("score", 55)
            )
            / 4
        ),
        "evidence": integration.get("evidence", [])[:4],
    }
    one_sentence_advice = {
        "key": f"{integration_key}_advice",
        "label": advice_text,
        "text": advice_text,
        "evidence": [
            *(integration.get("evidence", [])[:4]),
            *(_collect_fact_anchor_evidence(best_mode_of_action, career_vector, attachment_style, limit=2)),
        ][:5],
    }

    return {
        "version": "natal_v2_p0",
        "final_motto_seed": final_motto_seed,
        "one_sentence_advice": one_sentence_advice,
        "sun_vector": {"label": sun_anchor} if sun_anchor else {},
        "moon_vector": {"label": moon_anchor} if moon_anchor else {},
        "asc_mc_axis": {"label": angle_anchor} if angle_anchor else {},
        "top_conflict_vs_top_resource": top_conflict_vs_top_resource,
        "integration_focus": integration_focus,
        "closing_bridge": closing_bridge,
        "applied_cross_links": [item for item in applied_cross_links if item.get("label")],
        "cross_links": [
            "executive_summary.strengths_score",
            "synthesis.core_conflict",
            "money_realization.career_vector",
            "money_realization.realization_mode",
            "love_intimacy.attachment_style",
            "love_intimacy.partnership_needs",
        ],
    }


def _build_house_tenants(chart_data: dict) -> Dict[int, List[str]]:
    tenants: Dict[int, List[str]] = {house: [] for house in range(1, 13)}
    allowed = set(PLANET_ROLE_HINTS.keys()) | {"Lilith"}
    for position in chart_data.get("positions", []):
        house = position.get("house")
        name = _normalize_point_name(position.get("key") or position.get("name"))
        if isinstance(house, int) and 1 <= house <= 12 and name in allowed:
            tenants[house].append(name)
    return tenants


def _normalize_dispositor_summary(summary: Any) -> str:
    if isinstance(summary, list):
        parts = [str(item).strip() for item in summary if str(item).strip()]
        return "; ".join(parts)
    if summary is None:
        return ""
    cleaned = re.sub(r"\s+", " ", str(summary)).strip()
    return cleaned


def _normalize_fixed_star_record(star: Any) -> Dict[str, Any]:
    if not isinstance(star, dict):
        return {"name": str(star).strip(), "point": None, "orb": None}
    orb = star.get("orb")
    try:
        orb = round(float(orb), 1)
    except (TypeError, ValueError):
        orb = None
    point = _normalize_point_name(
        star.get("point") or star.get("planet") or star.get("raw_point") or star.get("body") or star.get("target")
    )
    return {
        "name": (star.get("name") or star.get("star") or "Fixed star").strip(),
        "point": point,
        "orb": orb,
        "sign": star.get("sign"),
    }


def _format_planet_name_list(names: List[str], limit: int = 4) -> str:
    return ", ".join(RU_PLANET_NAMES.get(name, name) for name in names[:limit])


def _build_dispositor_graph(position_lookup: Dict[str, dict]) -> Dict[str, Any]:
    planets = [planet for planet in MAJOR_DISPOSITOR_PLANETS if planet in position_lookup]
    links: Dict[str, str] = {}
    for planet in planets:
        sign = (position_lookup.get(planet) or {}).get("s")
        ruler = SIGN_RULER_MAP.get(sign)
        if ruler in planets:
            links[planet] = ruler

    inbound = {planet: 0 for planet in planets}
    for target in links.values():
        if target in inbound:
            inbound[target] += 1

    chains: Dict[str, Dict[str, Any]] = {}
    loops_seen: set[tuple[str, ...]] = set()
    loops: List[List[str]] = []
    for planet in planets:
        chain: List[str] = []
        current = planet
        while current in links and current not in chain:
            chain.append(current)
            current = links[current]
        loop: List[str] = []
        if current in chain:
            loop = chain[chain.index(current):]
            loop_key = tuple(loop)
            if loop_key not in loops_seen:
                loops_seen.add(loop_key)
                loops.append(loop)
        chains[planet] = {
            "chain": chain,
            "loop": loop,
        }
    return {
        "links": links,
        "inbound": inbound,
        "chains": chains,
        "loops": loops,
    }


def _build_dispositor_office_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    graph = _build_dispositor_graph(position_lookup)
    links = graph.get("links", {})
    inbound = graph.get("inbound", {})
    chains = graph.get("chains", {})
    loops = graph.get("loops", [])

    office_map = []
    for planet in MAJOR_DISPOSITOR_PLANETS:
        if planet not in position_lookup or planet not in links:
            continue
        reports_to = links.get(planet)
        report_position = position_lookup.get(reports_to)
        office_map.append(
            {
                "planet": planet,
                "planet_label": RU_PLANET_NAMES.get(planet, planet),
                "sign": position_lookup[planet].get("s"),
                "reports_to": reports_to,
                "reports_to_label": RU_PLANET_NAMES.get(reports_to, reports_to),
                "reports_to_sign": (report_position or {}).get("s"),
                "reports_to_house": (report_position or {}).get("h"),
            }
        )

    power_centers = []
    for planet in sorted(
        inbound.keys(),
        key=lambda key: (
            inbound.get(key, 0),
            any(key in loop for loop in loops),
        ),
        reverse=True,
    ):
        evidence = [
            _format_position_evidence(position_lookup.get(planet)),
        ]
        directs = [src for src, dst in links.items() if dst == planet]
        if directs:
            evidence.append(
                f"напрямую собирает: {_format_planet_name_list(directs)}"
            )
        if any(planet in loop for loop in loops):
            evidence.append("входит в конечный диспозиторный контур")
        power_centers.append(
            {
                "planet": planet,
                "label": RU_PLANET_NAMES.get(planet, planet),
                "score": _score_to_int(45 + inbound.get(planet, 0) * 12 + (18 if any(planet in loop for loop in loops) else 0)),
                "evidence": [item for item in evidence if item][:4],
            }
        )
    power_centers = power_centers[:3]

    final_bosses = []
    for loop in loops:
        if not loop:
            continue
        if len(loop) == 1:
            boss = loop[0]
            final_bosses.append(
                {
                    "type": "domicile",
                    "label": f"{RU_PLANET_NAMES.get(boss, boss)} держит кабинет у себя",
                    "planets": loop,
                    "evidence": [_format_position_evidence(position_lookup.get(boss))],
                }
            )
        elif len(loop) == 2:
            p1, p2 = loop
            final_bosses.append(
                {
                    "type": "mutual_reception",
                    "label": f"взаимная рецепция {RU_PLANET_NAMES.get(p1, p1)} и {RU_PLANET_NAMES.get(p2, p2)}",
                    "planets": loop,
                    "evidence": [
                        _format_position_evidence(position_lookup.get(p1)),
                        _format_position_evidence(position_lookup.get(p2)),
                    ][:4],
                }
            )
        else:
            final_bosses.append(
                {
                    "type": "loop",
                    "label": "замкнутый управленческий контур",
                    "planets": loop,
                    "evidence": [_format_planet_name_list(loop)],
                }
            )

    focus_map = {
        "Sun": "ядро и воля",
        "Moon": "эмоции и безопасность",
        "Mercury": "мышление и решения",
        "Venus": "ценность и связи",
        "Mars": "действие и конфликт",
    }
    decision_chains = []
    for planet, focus in focus_map.items():
        chain_info = chains.get(planet) or {}
        chain = chain_info.get("chain") or []
        if not chain:
            continue
        decision_chains.append(
            {
                "focus": focus,
                "planet": planet,
                "chain": chain,
                "chain_labels": [RU_PLANET_NAMES.get(item, item) for item in chain],
                "final_loop": chain_info.get("loop") or [],
                "evidence": [
                    _format_position_evidence(position_lookup.get(item))
                    for item in chain[:2]
                    if position_lookup.get(item)
                ][:4],
            }
        )

    top_center = power_centers[0] if power_centers else {}
    secondary_center = power_centers[1] if len(power_centers) > 1 else {}
    office_metaphor_seed = {
        "key": "office_hierarchy_seed",
        "label": (
            f"главный кабинет у {top_center.get('label', 'ключевой планеты')}, "
            f"а соседний центр влияния у {secondary_center.get('label', 'второго узла управления')}"
            if secondary_center
            else f"главный кабинет у {top_center.get('label', 'ключевой планеты')}"
        ),
        "evidence": [
            *(top_center.get("evidence", [])[:2] if top_center else []),
            *(secondary_center.get("evidence", [])[:1] if secondary_center else []),
        ][:4],
    }

    return {
        "version": "natal_v2_p1",
        "engine_summary": (
            (chart_data.get("dispositor_summary") or {}).get("summary")
            or _normalize_dispositor_summary(chart_data.get("dispositors"))
        ),
        "office_map": office_map,
        "power_centers": power_centers,
        "final_bosses": final_bosses,
        "decision_chains": decision_chains,
        "office_metaphor_seed": office_metaphor_seed,
        "cross_links": [
            "synthesis.identity_vector",
            "money_realization.career_vector",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }
# END_BLOCK: INSIGHT_SYNTHESIS_PACKS
