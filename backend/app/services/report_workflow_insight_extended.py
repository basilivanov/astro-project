# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-EXTENDED
# purpose: Build geometry, vertex, outer-planet, and dispatcher natal insight packs.
# inputs: compact chart_pack dictionaries produced by insight core.
# outputs: insight_pack dictionaries and dispatcher results for all natal sections.
# invariants: section-id dispatch remains import-compatible with report_workflow facade.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-EXTENDED

# START_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-EXTENDED
# entrypoints:
#   - _build_configurations_geometry_insight_pack -> CONFIGURATION_PACK
#   - _build_vertex_fate_insight_pack -> VERTEX_FATE_PACK
#   - _build_stars_transuranus_insight_pack -> STARS_TRANSURANUS_PACK
#   - _build_natal_section_insight_pack -> NATAL_SECTION_DISPATCH
# END_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-EXTENDED

from __future__ import annotations

import copy

from .report_workflow_insight_core import *
from .report_workflow_insight_houses_cycles import (
    _build_axes_truths_insight_pack,
    _build_balance_wheel_insight_pack,
    _build_time_cycles_insight_pack,
)
from .report_workflow_insight_mind_growth import (
    _build_aspects_beginner_insight_pack,
    _build_core_triad_insight_pack,
    _build_mercury_mind_insight_pack,
    _build_nodes_growth_insight_pack,
    _build_shadow_trauma_insight_pack,
)
from .report_workflow_insight_relationships import (
    _build_love_intimacy_insight_pack,
    _build_money_realization_insight_pack,
)
from .report_workflow_insight_summary import (
    _build_executive_summary_insight_pack,
    _build_framework_elements_modes_insight_pack,
    _build_synthesis_insight_pack,
)
from .report_workflow_insight_synthesis import (
    _build_dispositor_office_insight_pack,
    _build_final_synthesis_insight_pack,
    _format_planet_name_list,
)

# START_BLOCK: INSIGHT_EXTENDED_DISPATCH
def _build_configurations_geometry_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    pattern_templates = {
        "T-square": {
            "geometry": "две точки стоят в оппозиции и стягиваются в третью как в точку давления и сборки",
            "gift": "дает мотор, выносливость и способность расти через напряжение",
            "risk": "можно жить в режиме вечной внутренней тревоги, конфликта и перегрева",
            "question": "куда уходит лишнее напряжение и какую задачу ты пытаешься продавить любой ценой",
            "key": "искать устойчивый канал разрядки и превращать давление в ритм, а не в хаос",
        },
        "Т-квадрат": {
            "geometry": "две точки стоят в оппозиции и стягиваются в третью как в точку давления и сборки",
            "gift": "дает мотор, выносливость и способность расти через напряжение",
            "risk": "можно жить в режиме вечной внутренней тревоги, конфликта и перегрева",
            "question": "куда уходит лишнее напряжение и какую задачу ты пытаешься продавить любой ценой",
            "key": "искать устойчивый канал разрядки и превращать давление в ритм, а не в хаос",
        },
        "Grand Trine": {
            "geometry": "три точки связаны легким потоком и образуют устойчивый контур таланта",
            "gift": "дает врожденный ресурс, интуитивную согласованность и ощущение естественного дара",
            "risk": "легкость может усыплять и откладывать развитие того, что и так получается",
            "question": "как превратить врожденную легкость в осознанный навык и капитал",
            "key": "не полагаться только на дар, а строить на нем дисциплину и форму",
        },
        "Большой тригон": {
            "geometry": "три точки связаны легким потоком и образуют устойчивый контур таланта",
            "gift": "дает врожденный ресурс, интуитивную согласованность и ощущение естественного дара",
            "risk": "легкость может усыплять и откладывать развитие того, что и так получается",
            "question": "как превратить врожденную легкость в осознанный навык и капитал",
            "key": "не полагаться только на дар, а строить на нем дисциплину и форму",
        },
        "Grand Cross": {
            "geometry": "четыре точки держат напряжение по двум осям и не дают расслабиться без осознанной структуры",
            "gift": "дает огромную живучесть, объем и способность держать несколько фронтов сразу",
            "risk": "можно привыкнуть жить только через давление и кризисную мобилизацию",
            "question": "где ты подменяешь ясную стратегию постоянной обороной или атакой",
            "key": "собирать оси в систему приоритетов, а не пытаться тащить все одновременно",
        },
        "Большой крест": {
            "geometry": "четыре точки держат напряжение по двум осям и не дают расслабиться без осознанной структуры",
            "gift": "дает огромную живучесть, объем и способность держать несколько фронтов сразу",
            "risk": "можно привыкнуть жить только через давление и кризисную мобилизацию",
            "question": "где ты подменяешь ясную стратегию постоянной обороной или атакой",
            "key": "собирать оси в систему приоритетов, а не пытаться тащить все одновременно",
        },
        "Yod": {
            "geometry": "две точки сходятся в острую вершину и создают чувство тонкой настройки или судьбоносного прицела",
            "gift": "дает специфический талант и способность видеть тонкие корректировки маршрута",
            "risk": "можно жить в режиме хронической неудовлетворенности и ожидания идеального попадания",
            "question": "какая вершина карты требует не паники, а точной настройки и терпения",
            "key": "относиться к конфигурации как к маршруту настройки, а не как к приговору",
        },
        "Йод": {
            "geometry": "две точки сходятся в острую вершину и создают чувство тонкой настройки или судьбоносного прицела",
            "gift": "дает специфический талант и способность видеть тонкие корректировки маршрута",
            "risk": "можно жить в режиме хронической неудовлетворенности и ожидания идеального попадания",
            "question": "какая вершина карты требует не паники, а точной настройки и терпения",
            "key": "относиться к конфигурации как к маршруту настройки, а не как к приговору",
        },
        "Kite": {
            "geometry": "легкий ресурсный контур получает направляющую ось и возможность превратить талант в траекторию",
            "gift": "дает шанс направить врожденный дар в видимую задачу и результат",
            "risk": "часть ресурса может уходить в расфокус, если ось не проживается осознанно",
            "question": "куда именно просится твой природный талант, если дать ему направление",
            "key": "связывать легкость, цель и дисциплину, чтобы талант не распылялся",
        },
        "Кайт": {
            "geometry": "легкий ресурсный контур получает направляющую ось и возможность превратить талант в траекторию",
            "gift": "дает шанс направить врожденный дар в видимую задачу и результат",
            "risk": "часть ресурса может уходить в расфокус, если ось не проживается осознанно",
            "question": "куда именно просится твой природный талант, если дать ему направление",
            "key": "связывать легкость, цель и дисциплину, чтобы талант не распылялся",
        },
    }

    configuration_cards = []
    for pattern in chart_data.get("patterns", []):
        points = [
            _normalize_point_name(point)
            for point in (pattern.get("point_keys") or pattern.get("points", []))
        ]
        template = pattern_templates.get(pattern.get("type"), {
            "geometry": "в карте есть связанная фигура, которая собирает несколько тем в общий сценарий",
            "gift": "она дает дополнительную структурность и видимый повторяющийся сюжет",
            "risk": "если ее не осознавать, одна и та же сцепка будет повторяться слишком автоматически",
            "question": "какой общий паттерн ты проживаешь снова и снова",
            "key": "сначала назвать повторяющийся узор, а затем выбрать взрослый способ его проживать",
        })
        point_evidence = [
            _format_position_evidence(position_lookup.get(point))
            for point in points[:3]
            if position_lookup.get(point)
        ]
        configuration_cards.append(
            {
                "type": pattern.get("type") or "Конфигурация",
                "points": points,
                "points_label": _format_planet_name_list(points, limit=6),
                "geometry": template["geometry"],
                "gift": template["gift"],
                "risk": template["risk"],
                "question": template["question"],
                "key": template["key"],
                "evidence": [
                    f"точки конфигурации: {_format_planet_name_list(points, limit=6)}",
                    *point_evidence,
                ][:4],
            }
        )

    dominant_pattern = configuration_cards[0] if configuration_cards else None
    absence_summary = {
        "key": "no_major_configurations",
        "label": "жестких конфигураций в карте не видно: основные сюжеты читаются через отдельные аспекты и оси, а не через большую геометрию",
    }

    return {
        "version": "natal_v2_p3",
        "configuration_cards": configuration_cards,
        "dominant_pattern": dominant_pattern,
        "absence_summary": absence_summary,
        "cross_links": [
            "aspects_beginner.aspect_cards",
            "synthesis.core_conflict",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_vertex_fate_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    vertex = _get_point(position_lookup, "Vertex")
    venus = _get_point(position_lookup, "Venus")
    mars = _get_point(position_lookup, "Mars")
    moon = _get_point(position_lookup, "Moon")
    dsc = _get_point(position_lookup, "DSC")

    vertex_sign = (vertex or {}).get("s")
    vertex_hint = SIGN_STYLE_HINTS.get(vertex_sign, {})
    vertex_house = (vertex or {}).get("h")
    vertex_domain = HOUSE_DOMAIN_MAP.get(vertex_house, "сюжетных встреч")
    vertex_ruler = SIGN_RULER_MAP.get(vertex_sign)
    vertex_ruler_position = position_lookup.get(vertex_ruler) if vertex_ruler else None

    encounter_triggers = [
        {
            "key": "vertex_house_trigger",
            "label": f"сюжетные встречи включаются через тему {vertex_domain.lower()}",
            "evidence": [_format_position_evidence(vertex)],
        }
    ]
    if vertex_ruler_position:
        encounter_triggers.append(
            {
                "key": "vertex_ruler_trigger",
                "label": (
                    f"сценарий чаще приходит через тему "
                    f"{HOUSE_DOMAIN_MAP.get(vertex_ruler_position.get('h'), 'дома управителя').lower()}"
                ),
                "evidence": [
                    _format_position_evidence(vertex_ruler_position),
                    _format_position_evidence(vertex),
                ][:4],
            }
        )
    if _house_in(venus, {5, 7, 8}) or _house_in(mars, {5, 7, 8}) or _house_in(moon, {5, 7, 8, 12}):
        encounter_triggers.append(
            {
                "key": "relationship_house_trigger",
                "label": "важные встречи цепляют романтический, партнерский или глубинно-эмоциональный контур карты",
                "evidence": [
                    _format_position_evidence(venus),
                    _format_position_evidence(mars),
                    _format_position_evidence(moon),
                ][:4],
            }
        )

    vertex_signature = {
        "key": "vertex_signature",
        "label": (
            f"Вертекс показывает встречи в режиме '{vertex_hint.get('tone', 'особого притяжения')}' "
            f"через тему {vertex_domain.lower()}"
        ),
        "lesson": vertex_hint.get("growth", "учиться проживать встречи осознанно, а не как чистый рок"),
        "evidence": [
            _format_position_evidence(vertex),
            _format_position_evidence(vertex_ruler_position),
        ][:4],
    }

    if vertex_sign in {"Libra", "Taurus"} or _house_in(venus, {7, 11}):
        vector_key = "relational_mirror"
        vector_label = "сюжетные встречи часто приходят через зеркало отношений, договоренностей и вопроса равновесия"
        vector_evidence = [
            _format_position_evidence(vertex),
            _format_position_evidence(venus),
            _format_position_evidence(dsc),
        ]
    elif vertex_sign in {"Scorpio", "Sagittarius"} or _house_in(mars, {8}):
        vector_key = "transformative_encounter"
        vector_label = "важные встречи несут заряд поворота, риска и глубокой внутренней перестройки"
        vector_evidence = [
            _format_position_evidence(vertex),
            _format_position_evidence(mars),
            _format_position_evidence(moon),
        ]
    else:
        vector_key = "meaningful_alliance"
        vector_label = "сюжетные люди включают не только чувства, но и смену курса, роли или способа видеть себя"
        vector_evidence = [
            _format_position_evidence(vertex),
            _format_position_evidence(vertex_ruler_position),
            _format_position_evidence(dsc),
        ]

    relationship_vector = {
        "key": vector_key,
        "label": vector_label,
        "evidence": [item for item in vector_evidence if item][:4],
    }
    fated_lesson = {
        "key": "vertex_fated_lesson",
        "label": (
            f"главный урок Вертекса — {vertex_hint.get('growth', 'не путать притяжение с зрелым выбором')} "
            f"и связывать это с темой {HOUSE_DOMAIN_MAP.get((vertex_ruler_position or {}).get('h'), vertex_domain).lower()}"
        ),
        "evidence": [
            _format_position_evidence(vertex),
            _format_position_evidence(vertex_ruler_position),
            _format_position_evidence(dsc),
        ][:4],
    }

    return {
        "version": "natal_v2_p3",
        "vertex_signature": vertex_signature,
        "encounter_triggers": encounter_triggers[:3],
        "relationship_vector": relationship_vector,
        "fated_lesson": fated_lesson,
        "cross_links": [
            "love_intimacy.partnership_needs",
            "axes_truths.dominant_axis_tension",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _build_outer_planet_vector(
    planet_name: str,
    chart_data: dict,
    position_lookup: Dict[str, dict],
) -> Dict[str, Any]:
    position = _get_point(position_lookup, planet_name)
    hint = SIGN_STYLE_HINTS.get((position or {}).get("s"), {})
    domain = HOUSE_DOMAIN_MAP.get((position or {}).get("h"), "долгого жизненного сюжета")
    contacts = []
    for target in ["Sun", "Moon", "Saturn"]:
        aspect = _find_aspect(chart_data, planet_name, target)
        if aspect:
            contacts.append(aspect)

    base_label = (
        f"{RU_PLANET_NAMES.get(planet_name, planet_name)} включает тему {domain.lower()} "
        f"через режим '{hint.get('tone', 'долгого влияния')}'"
    )
    if planet_name == "Uranus":
        gift = "дар: запускать обновление, освобождать маршрут и видеть нестандартный ход"
        risk = "риск: резкие повороты, нетерпение к ограничениям и скачкообразные решения"
    elif planet_name == "Neptune":
        gift = "дар: усиливать интуицию, воображение и чувствительность к смыслу и атмосфере"
        risk = "риск: идеализация, туман критериев и потеря границ"
    else:
        gift = "дар: проходить через кризис, глубину и собирать силу из сложных сюжетов"
        risk = "риск: контроль, силовые игры и жизнь через крайние режимы"

    if any(_is_tense(contact) for contact in contacts):
        risk += "; напряженные связи с личными точками усиливают ощущение внутреннего давления"
    if any(_is_harmonious(contact) for contact in contacts):
        gift += "; есть рабочий канал, через который высшая планета легче встраивается в личную жизнь"

    return {
        "planet": planet_name,
        "label": base_label,
        "gift": gift,
        "risk": risk,
        "key": hint.get("growth", "делать влияние этой планеты осознанным и управляемым"),
        "evidence": [
            _format_position_evidence(position),
            *(_format_aspect_evidence(contact) for contact in contacts[:2]),
        ][:4],
    }


def _build_stars_transuranus_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    uranus_vector = _build_outer_planet_vector("Uranus", chart_data, position_lookup)
    neptune_vector = _build_outer_planet_vector("Neptune", chart_data, position_lookup)
    pluto_vector = _build_outer_planet_vector("Pluto", chart_data, position_lookup)

    outer_contacts = []
    for pair in [("Sun", "Uranus"), ("Sun", "Neptune"), ("Saturn", "Neptune"), ("Saturn", "Pluto")]:
        aspect = _find_aspect(chart_data, pair[0], pair[1])
        if aspect:
            outer_contacts.append(aspect)

    collective_story = {
        "key": "collective_story",
        "label": (
            "высшие планеты собирают карту в сюжет, где обновление, идеал и глубинная сила постоянно влияют на жизненный курс"
            if outer_contacts
            else "высшие планеты работают фоном: их темы важны не как событие, а как долгий стиль взросления"
        ),
        "evidence": [
            *(_format_aspect_evidence(aspect) for aspect in outer_contacts[:3]),
            uranus_vector.get("label"),
        ][:4],
    }

    fixed_star_hooks = []
    for star in chart_data.get("fixed_stars", [])[:3]:
        normalized_star = _normalize_fixed_star_record(star)
        name = normalized_star.get("name") or "Fixed star"
        point = normalized_star.get("point")
        orb = normalized_star.get("orb")
        fixed_star_hooks.append(
            {
                "name": name,
                "point": point,
                "label": (
                    f"если использовать fixed stars, {name} цепляется за "
                    f"{RU_PLANET_NAMES.get(point, point or 'точку карты')}"
                ),
                "evidence": [
                    (
                        f"{name} ~ {RU_PLANET_NAMES.get(point, point or 'точка карты')} "
                        f"(orb {orb}°)"
                        if orb is not None
                        else f"{name} ~ {RU_PLANET_NAMES.get(point, point or 'точка карты')}"
                    )
                ],
            }
        )

    return {
        "version": "natal_v2_p3",
        "uranus_vector": uranus_vector,
        "neptune_vector": neptune_vector,
        "pluto_vector": pluto_vector,
        "collective_story": collective_story,
        "fixed_star_hooks": fixed_star_hooks,
        "cross_links": [
            "executive_summary.risk_score",
            "aspects_beginner.aspect_cards",
            "time_cycles.growth_tension",
        ],
    }


def _build_natal_section_insight_pack(
    section_id: str,
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
    client: Optional[dict] = None,
    forecast_window: Optional[dict] = None,
) -> Optional[Dict[str, Any]]:
    if section_id == "executive_summary":
        return _build_executive_summary_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "framework_elements_modes":
        return _build_framework_elements_modes_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "synthesis":
        return _build_synthesis_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "money_realization":
        return _build_money_realization_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "love_intimacy":
        return _build_love_intimacy_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "final_synthesis":
        return _build_final_synthesis_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "dispositor_office":
        return _build_dispositor_office_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id in {"balance_wheel_1_6", "balance_wheel_7_12"}:
        return _build_balance_wheel_insight_pack(
            section_id, facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "time_cycles":
        return _build_time_cycles_insight_pack(
            facts,
            chart_data,
            position_lookup,
            house_lookup,
            client,
            forecast_window,
        )
    if section_id == "axes_truths":
        return _build_axes_truths_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "aspects_beginner":
        return _build_aspects_beginner_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "nodes_growth":
        return _build_nodes_growth_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "mercury_mind":
        return _build_mercury_mind_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "shadow_trauma":
        return _build_shadow_trauma_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "core_triad":
        return _build_core_triad_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "configurations_geometry":
        return _build_configurations_geometry_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "vertex_fate":
        return _build_vertex_fate_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "stars_transuranus":
        return _build_stars_transuranus_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    return None
# END_BLOCK: INSIGHT_EXTENDED_DISPATCH
