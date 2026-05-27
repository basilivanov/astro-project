# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-MIND-GROWTH
# purpose: Build aspects, nodes, Mercury, shadow, and core-triad natal insight packs.
# inputs: compact chart_pack dictionaries produced by insight core.
# outputs: insight_pack dictionaries for cognition, growth, trauma, and identity sections.
# invariants: aspect evidence selection and growth labels remain unchanged.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-MIND-GROWTH

# START_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-MIND-GROWTH
# entrypoints:
#   - _build_aspects_beginner_insight_pack -> ASPECTS_BEGINNER_PACK
#   - _build_nodes_growth_insight_pack -> NODES_GROWTH_PACK
#   - _build_mercury_mind_insight_pack -> MERCURY_MIND_PACK
#   - _build_shadow_trauma_insight_pack -> SHADOW_TRAUMA_PACK
#   - _build_core_triad_insight_pack -> CORE_TRIAD_PACK
# END_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-MIND-GROWTH

from __future__ import annotations

from .report_workflow_insight_core import *

# START_BLOCK: INSIGHT_MIND_GROWTH_PACKS
def _build_aspects_beginner_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    aspect_templates = {
        "conjunction": {
            "anchor": "две функции карты работают как единый контур",
            "resource": "дает цельность, концентрацию и мощный общий вектор",
            "shadow": "сливает темы вместе, из-за чего сложнее отделять одно от другого",
            "key": "учиться различать роли, даже когда они спаяны",
        },
        "opposition": {
            "anchor": "две части психики стоят друг напротив друга и требуют баланса",
            "resource": "дает объемный взгляд и способность видеть обе стороны",
            "shadow": "дает качели, проекции и чувство внутреннего раздвоения",
            "key": "не выбирать один полюс насмерть, а строить мост между ними",
        },
        "square": {
            "anchor": "внутреннее трение заставляет действовать через напряжение",
            "resource": "дает мотор, выносливость и способность пробивать сложное",
            "shadow": "дает внутренний перегрев, конфликтность и давление на себя",
            "key": "переводить трение в задачу и ритм, а не в самоуничтожение",
        },
        "trine": {
            "anchor": "энергия между функциями течет естественно и без лишнего усилия",
            "resource": "дает врожденный талант и естественный ресурс",
            "shadow": "можно привыкнуть и не развивать то, что и так дается легко",
            "key": "осознанно капитализировать легкость, а не только полагаться на нее",
        },
        "sextile": {
            "anchor": "между функциями есть рабочая возможность, которую нужно включать действием",
            "resource": "дает навык, который хорошо собирается практикой",
            "shadow": "без инициативы аспект спит и не работает на полную",
            "key": "регулярно включать этот канал делом, а не ждать автоматизма",
        },
    }
    selected = sorted(chart_data.get("aspects", []), key=lambda item: item.get("orb", 99))[:6]
    aspect_cards = []
    for raw_aspect in selected:
        aspect = _compact_aspect_fact(raw_aspect)
        template = aspect_templates.get(aspect.get("t"), aspect_templates["sextile"])
        p1 = RU_PLANET_NAMES.get(aspect.get("p1"), aspect.get("p1") or "")
        p2 = RU_PLANET_NAMES.get(aspect.get("p2"), aspect.get("p2") or "")
        role1 = PLANET_ROLE_HINTS.get(aspect.get("p1"), aspect.get("p1") or "")
        role2 = PLANET_ROLE_HINTS.get(aspect.get("p2"), aspect.get("p2") or "")
        aspect_cards.append(
            {
                "aspect": f"{p1} {RU_ASPECTS.get(aspect.get('t'), aspect.get('t') or '')} {p2}",
                "orb": aspect.get("o"),
                "anchor": template["anchor"],
                "scenario": f"сюжет строится вокруг темы '{role1}' в связке с темой '{role2}'",
                "resource": template["resource"],
                "shadow": template["shadow"],
                "key": template["key"],
                "evidence": [_format_aspect_evidence(aspect)],
            }
        )

    return {
        "version": "natal_v2_p2",
        "aspect_cards": aspect_cards,
        "selection_rule": "взяты самые точные мажорные аспекты по орбису",
        "cross_links": [
            "synthesis.core_conflict",
            "executive_summary.strengths_score",
            "executive_summary.risk_score",
        ],
    }


def _build_nodes_growth_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    north = _get_point(position_lookup, "North Node", "True Node")
    south = _get_point(position_lookup, "South Node")
    south_hint = SIGN_STYLE_HINTS.get((south or {}).get("s"), {})
    north_hint = SIGN_STYLE_HINTS.get((north or {}).get("s"), {})
    south_domain = HOUSE_DOMAIN_MAP.get((south or {}).get("h"), "знакомой жизненной темы")
    north_domain = HOUSE_DOMAIN_MAP.get((north or {}).get("h"), "новой жизненной темы")

    node_drivers = []
    for pair in [("Sun", north), ("Moon", north), ("Saturn", north)]:
        planet_name, node_point = pair
        if not node_point:
            continue
        aspect = _find_aspect(chart_data, planet_name, node_point.get("p", node_point.get("name", "True Node")))
        if aspect:
            node_drivers.append(
                {
                    "planet": planet_name,
                    "aspect": _format_aspect_evidence(aspect),
                    "meaning": f"рост цепляется за тему '{PLANET_ROLE_HINTS.get(planet_name, planet_name)}'",
                }
            )

    south_node_habit = {
        "key": "south_node_habit",
        "label": (
            f"автоматически тянуться к режиму '{south_hint.get('tone', 'привычного способа')}' "
            f"в теме {south_domain.lower()}"
        ),
        "risk": south_hint.get("minus", "застревать в знакомом сценарии"),
        "evidence": [_format_position_evidence(south)],
    }
    north_node_direction = {
        "key": "north_node_direction",
        "label": (
            f"вектор роста — осваивать '{north_hint.get('growth', 'новый взрослый способ')}' "
            f"в теме {north_domain.lower()}"
        ),
        "mission": north_hint.get("growth", "двигаться в сторону нового сценария"),
        "evidence": [_format_position_evidence(north)],
    }
    bridge_task = {
        "key": "node_bridge_task",
        "label": (
            f"не выбрасывать опыт {south_domain.lower()}, а перевести его в более зрелую форму "
            f"ради задач {north_domain.lower()}"
        ),
        "evidence": [
            _format_position_evidence(south),
            _format_position_evidence(north),
            *(driver.get("aspect") for driver in node_drivers[:2]),
        ][:4],
    }

    return {
        "version": "natal_v2_p2",
        "south_node_habit": south_node_habit,
        "north_node_direction": north_node_direction,
        "bridge_task": bridge_task,
        "node_drivers": node_drivers,
        "cross_links": [
            "executive_summary.development_focus",
            "time_cycles.growth_tension",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_mercury_mind_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    mercury = _get_point(position_lookup, "Mercury")
    moon = _get_point(position_lookup, "Moon")
    saturn = _get_point(position_lookup, "Saturn")
    uranus = _get_point(position_lookup, "Uranus")

    mercury_moon = _find_aspect(chart_data, "Mercury", "Moon")
    mercury_saturn = _find_aspect(chart_data, "Mercury", "Saturn")
    mercury_uranus = _find_aspect(chart_data, "Mercury", "Uranus")

    thinking_candidates = {
        "structured_analyst": _new_rank_item(
            "structured_analyst",
            "мышление структурное: собираешь данные в каркас, категории и выводы",
        ),
        "intuitive_reader": _new_rank_item(
            "intuitive_reader",
            "мышление считывает подтекст, атмосферу и неочевидные сигналы",
        ),
        "unconventional_scanner": _new_rank_item(
            "unconventional_scanner",
            "мышление быстро сканирует систему и любит нестандартные ходы",
        ),
    }
    processing_modes = {
        "step_by_step_verification": _new_rank_item(
            "step_by_step_verification",
            "режим обработки: сначала собрать опору и логику, потом говорить",
        ),
        "jump_then_refine": _new_rank_item(
            "jump_then_refine",
            "режим обработки: сначала увидеть ход, потом доточить и проверить",
        ),
        "emotional_filtering": _new_rank_item(
            "emotional_filtering",
            "режим обработки: мысль сильно фильтруется текущим эмоциональным состоянием",
        ),
    }
    cognitive_risks = {
        "overcontrol_and_rumination": _new_rank_item(
            "overcontrol_and_rumination",
            "ловушка: перегружать мысль контролем, проверками и внутренней критикой",
        ),
        "abrupt_jumps": _new_rank_item(
            "abrupt_jumps",
            "ловушка: резкие скачки, отстраненность и разрыв между идеей и объяснением",
        ),
        "mood_bias": _new_rank_item(
            "mood_bias",
            "ловушка: мысль сильнее обычного окрашивается настроением и внутренней погодой",
        ),
    }

    if _sign_in(mercury, {"Capricorn", "Virgo", "Taurus"}):
        evidence = _format_position_evidence(mercury)
        _bump_rank(thinking_candidates, "structured_analyst", 16, evidence)
        _bump_rank(processing_modes, "step_by_step_verification", 12, evidence)
    if mercury_saturn:
        evidence = _format_aspect_evidence(mercury_saturn)
        _bump_rank(thinking_candidates, "structured_analyst", 12, evidence)
        _bump_rank(processing_modes, "step_by_step_verification", 10, evidence)
        _bump_rank(cognitive_risks, "overcontrol_and_rumination", 14, evidence)
    if _sign_in(mercury, {"Aquarius", "Gemini", "Sagittarius"}) or mercury_uranus:
        evidence = _format_position_evidence(mercury) or _format_aspect_evidence(mercury_uranus)
        _bump_rank(thinking_candidates, "unconventional_scanner", 14, evidence)
        _bump_rank(processing_modes, "jump_then_refine", 12, evidence)
        _bump_rank(cognitive_risks, "abrupt_jumps", 12, evidence)
    if _sign_in(mercury, {"Cancer", "Scorpio", "Pisces"}) or mercury_moon:
        evidence = _format_position_evidence(mercury) or _format_aspect_evidence(mercury_moon)
        _bump_rank(thinking_candidates, "intuitive_reader", 12, evidence)
        _bump_rank(processing_modes, "emotional_filtering", 12, evidence)
        _bump_rank(cognitive_risks, "mood_bias", 12, evidence)
    if _house_in(moon, {8, 12}):
        evidence = _format_position_evidence(moon)
        _bump_rank(processing_modes, "emotional_filtering", 8, evidence)
        _bump_rank(cognitive_risks, "mood_bias", 8, evidence)

    thinking_style = _pick_primary_ranked(
        thinking_candidates,
        fallback_key="structured_analyst",
        fallback_label="мышление структурное: собираешь данные в каркас, категории и выводы",
        fallback_evidence=[_format_position_evidence(mercury)],
    )
    processing_mode = _pick_primary_ranked(
        processing_modes,
        fallback_key="step_by_step_verification",
        fallback_label="режим обработки: сначала собрать опору и логику, потом говорить",
        fallback_evidence=[_format_position_evidence(mercury)],
    )
    mind_keys = {
        "key": "mind_key",
        "label": (
            "лучший ключ — сначала назвать структуру мысли, затем добавить интуитивный слой"
            if thinking_style.get("key") == "structured_analyst"
            else "лучший ключ — переводить быстрые инсайты в понятный алгоритм и язык"
        ),
        "evidence": [
            *(thinking_style.get("evidence", [])[:2]),
            *(processing_mode.get("evidence", [])[:2]),
        ][:4],
    }

    return {
        "version": "natal_v2_p2",
        "thinking_style": thinking_style,
        "processing_mode": processing_mode,
        "cognitive_risks": _finalize_ranked(cognitive_risks, limit=3),
        "mind_keys": mind_keys,
        "cross_links": [
            "synthesis.identity_vector",
            "executive_summary.risk_score",
            "shadow_trauma.compensation_modes",
        ],
    }


def _build_shadow_trauma_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    chiron = _get_point(position_lookup, "Chiron")
    lilith = _get_point(position_lookup, "Lilith", "Mean Apogee")
    moon = _get_point(position_lookup, "Moon")
    saturn = _get_point(position_lookup, "Saturn")
    pluto = _get_point(position_lookup, "Pluto")

    chiron_hint = SIGN_STYLE_HINTS.get((chiron or {}).get("s"), {})
    lilith_hint = SIGN_STYLE_HINTS.get((lilith or {}).get("s"), {})

    chiron_pattern = {
        "anchor": (
            f"уязвимость в теме {HOUSE_DOMAIN_MAP.get((chiron or {}).get('h'), 'личной боли').lower()} "
            f"через сюжет '{chiron_hint.get('tone', 'тонкой настройки')}'"
        ),
        "scenario": "болевая точка включается там, где хочется сразу быть сильным и безошибочным",
        "resource": chiron_hint.get("growth", "в боли спрятан навык настройки и исцеления"),
        "shadow": chiron_hint.get("minus", "есть риск застревать в уязвимости и защите"),
        "key": "работать с уязвимостью как с настройкой, а не как с дефектом",
        "evidence": [_format_position_evidence(chiron)],
    }
    lilith_pattern = {
        "anchor": (
            f"теневая сила в теме {HOUSE_DOMAIN_MAP.get((lilith or {}).get('h'), 'теневой зоны').lower()} "
            f"через сюжет '{lilith_hint.get('tone', 'сырой силы')}'"
        ),
        "scenario": "искушение — брать власть, уходить в крайность или проверять мир на прочность",
        "resource": lilith_hint.get("plus", "внутри есть raw-энергия и смелость видеть неудобное"),
        "shadow": lilith_hint.get("minus", "крайности, борьба за контроль или разрушительная резкость"),
        "key": "переводить сырую силу в осознанные границы и выбор",
        "evidence": [_format_position_evidence(lilith)],
    }

    pain_points = [
        {
            "label": f"боль чаще всего цепляет тему {HOUSE_DOMAIN_MAP.get((chiron or {}).get('h'), 'уязвимости').lower()}",
            "evidence": [_format_position_evidence(chiron)],
        },
        {
            "label": f"теневое напряжение особенно видно в теме {HOUSE_DOMAIN_MAP.get((lilith or {}).get('h'), 'контроля').lower()}",
            "evidence": [_format_position_evidence(lilith)],
        },
    ]
    compensation_modes = []
    if saturn:
        compensation_modes.append(
            {
                "key": "saturn_control",
                "label": "компенсация через самоконтроль, сжатие и внутренний прессинг",
                "evidence": [_format_position_evidence(saturn)],
            }
        )
    if pluto:
        compensation_modes.append(
            {
                "key": "pluto_control",
                "label": "компенсация через контроль, силовую проверку и нежелание быть слабым",
                "evidence": [_format_position_evidence(pluto)],
            }
        )
    if moon:
        compensation_modes.append(
            {
                "key": "moon_retreat",
                "label": "компенсация через уход в молчание, закрытие или проживание боли в одиночку",
                "evidence": [_format_position_evidence(moon)],
            }
        )

    integration_task = {
        "key": "shadow_integration",
        "label": "зрелая задача — признать и боль, и темную силу, не отдавая управление ни стыду, ни контролю",
        "evidence": [
            _format_position_evidence(chiron),
            _format_position_evidence(lilith),
            _format_position_evidence(saturn),
            _format_position_evidence(pluto),
        ][:4],
    }

    return {
        "version": "natal_v2_p2",
        "chiron_pattern": chiron_pattern,
        "lilith_pattern": lilith_pattern,
        "pain_points": pain_points,
        "compensation_modes": compensation_modes[:3],
        "integration_task": integration_task,
        "cross_links": [
            "executive_summary.risk_score",
            "mercury_mind.cognitive_risks",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_core_triad_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    asc = _get_point(position_lookup, "ASC")
    sun = _get_point(position_lookup, "Sun")
    moon = _get_point(position_lookup, "Moon")

    asc_hint = SIGN_STYLE_HINTS.get((asc or {}).get("s"), {})
    sun_hint = SIGN_STYLE_HINTS.get((sun or {}).get("s"), {})
    moon_hint = SIGN_STYLE_HINTS.get((moon or {}).get("s"), {})

    sun_moon = _find_aspect(chart_data, "Sun", "Moon")
    sun_asc = _find_aspect(chart_data, "Sun", "ASC")
    moon_asc = _find_aspect(chart_data, "Moon", "ASC")
    sun_saturn = _find_aspect(chart_data, "Sun", "Saturn")
    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")

    asc_mask = {
        "key": "asc_mask",
        "label": (
            f"во внешний мир ты входишь через режим '{asc_hint.get('tone', 'естественной самоподачи')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get((asc or {}).get('h'), 'личной подачи').lower()}"
        ),
        "growth": asc_hint.get("growth", "делать подачу зрелой и управляемой"),
        "evidence": [
            _format_position_evidence(asc),
            _format_aspect_evidence(sun_asc),
            _format_aspect_evidence(moon_asc),
        ][:4],
    }
    solar_drive = {
        "key": "solar_drive",
        "label": (
            f"воля и чувство направления включаются через '{sun_hint.get('plus', 'ядро воли')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get((sun or {}).get('h'), 'самореализации').lower()}"
        ),
        "risk": sun_hint.get("minus", "есть риск перегнуть волю или контроль"),
        "evidence": [
            _format_position_evidence(sun),
            _format_aspect_evidence(sun_saturn),
            _format_aspect_evidence(sun_neptune),
        ][:4],
    }
    lunar_need = {
        "key": "lunar_need",
        "label": (
            f"эмоциональная база просит '{moon_hint.get('plus', 'эмоциональной опоры')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get((moon or {}).get('h'), 'внутренней безопасности').lower()}"
        ),
        "risk": moon_hint.get("minus", "есть риск уходить в крайности настроения"),
        "evidence": [
            _format_position_evidence(moon),
            _format_aspect_evidence(sun_moon),
            _format_aspect_evidence(moon_asc),
        ][:4],
    }

    sun_element = SIGN_ELEMENT_MAP.get((sun or {}).get("s"))
    moon_element = SIGN_ELEMENT_MAP.get((moon or {}).get("s"))
    asc_element = SIGN_ELEMENT_MAP.get((asc or {}).get("s"))

    if _is_tense(sun_moon):
        conflict_key = "will_vs_feelings"
        conflict_label = "ядро личности и эмоции спорят напрямую: воля тянет в один режим, чувства требуют другого темпа"
        conflict_evidence = [_format_aspect_evidence(sun_moon)]
    elif sun_saturn:
        conflict_key = "high_standard_pressure"
        conflict_label = "ядро карты собрано через высокий стандарт и ответственность, поэтому мягкость к себе дается не сразу"
        conflict_evidence = [
            _format_aspect_evidence(sun_saturn),
            _format_position_evidence(sun),
        ]
    elif sun_neptune:
        conflict_key = "clarity_vs_blur"
        conflict_label = "между потребностью держать курс и тягой уходить в идеал, атмосферу или расплывчатый образ"
        conflict_evidence = [
            _format_aspect_evidence(sun_neptune),
            _format_position_evidence(moon),
        ]
    elif sun_element and moon_element and sun_element != moon_element:
        conflict_key = "outer_plan_vs_inner_flow"
        conflict_label = "внешний курс и внутренний ритм собраны из разных стихий, поэтому важно не требовать от себя одной скорости всегда"
        conflict_evidence = [
            _format_position_evidence(sun),
            _format_position_evidence(moon),
        ]
    else:
        conflict_key = "mask_vs_need"
        conflict_label = "главная настройка в том, чтобы маска, воля и чувства не жили тремя разными траекториями"
        conflict_evidence = [
            _format_position_evidence(asc),
            _format_position_evidence(sun),
            _format_position_evidence(moon),
        ]

    triad_conflict = {
        "key": conflict_key,
        "label": conflict_label,
        "score": _score_to_int(
            58
            + (12 if _is_tense(sun_moon) else 0)
            + (8 if sun_saturn else 0)
            + (6 if sun_neptune else 0)
        ),
        "evidence": [item for item in conflict_evidence if item][:4],
    }

    integration_parts = [
        asc_hint.get("growth"),
        sun_hint.get("growth"),
        moon_hint.get("growth"),
    ]
    if asc_element and sun_element and asc_element == sun_element:
        integration_label = "внешняя подача и воля уже говорят на одном языке; задача — добавить туда эмоциональную честность и регулярную самонастройку"
    elif moon_element and sun_element and moon_element == sun_element:
        integration_label = "ядро и чувства близки по природе; задача — чтобы внешняя маска не мешала этой внутренней согласованности"
    else:
        integration_label = "сборка ядра идет через согласование трех скоростей: как входишь, чего хочешь и что тебе реально нужно для опоры"

    triad_integration = {
        "key": "triad_integration",
        "label": integration_label,
        "steps": [part for part in integration_parts if part][:3],
        "evidence": [
            _format_position_evidence(asc),
            _format_position_evidence(sun),
            _format_position_evidence(moon),
        ][:4],
    }

    return {
        "version": "natal_v2_p3",
        "asc_mask": asc_mask,
        "solar_drive": solar_drive,
        "lunar_need": lunar_need,
        "triad_conflict": triad_conflict,
        "triad_integration": triad_integration,
        "cross_links": [
            "synthesis.identity_vector",
            "executive_summary.development_focus",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }
# END_BLOCK: INSIGHT_MIND_GROWTH_PACKS
