# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-SUMMARY
# purpose: Build executive, synthesis, and framework natal insight packs.
# inputs: compact chart_pack dictionaries produced by insight core.
# outputs: insight_pack dictionaries for summary-oriented natal sections.
# invariants: fact-first copy and scoring semantics remain unchanged.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-SUMMARY

# START_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-SUMMARY
# entrypoints:
#   - _build_executive_summary_insight_pack -> EXECUTIVE_SUMMARY_PACK
#   - _build_synthesis_insight_pack -> SYNTHESIS_PACK
#   - _build_framework_elements_modes_insight_pack -> FRAMEWORK_PACK
# END_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-SUMMARY

from __future__ import annotations

from .report_workflow_insight_core import *

# START_BLOCK: INSIGHT_SUMMARY_PACKS
def _build_executive_summary_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    balance = _get_balance_snapshot(facts, chart_data)
    earth = _balance_value(balance, "elements", "Earth")
    water = _balance_value(balance, "elements", "Water")
    air = _balance_value(balance, "elements", "Air")
    fire = _balance_value(balance, "elements", "Fire")
    cardinal = _balance_value(balance, "modes", "Cardinal")

    sun = position_lookup.get("Sun")
    moon = position_lookup.get("Moon")
    mercury = position_lookup.get("Mercury")
    venus = position_lookup.get("Venus")
    mars = position_lookup.get("Mars")
    jupiter = position_lookup.get("Jupiter")
    saturn = position_lookup.get("Saturn")
    uranus = position_lookup.get("Uranus")
    neptune = position_lookup.get("Neptune")
    pluto = position_lookup.get("Pluto")
    asc = position_lookup.get("ASC")
    mc = position_lookup.get("MC")

    sun_saturn = _find_aspect(chart_data, "Sun", "Saturn")
    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")
    moon_jupiter = _find_aspect(chart_data, "Moon", "Jupiter")
    uranus_jupiter = _find_aspect(chart_data, "Uranus", "Jupiter")
    venus_mars = _find_aspect(chart_data, "Venus", "Mars")
    saturn_pluto = _find_aspect(chart_data, "Saturn", "Pluto")

    house2 = _build_house_snapshot(house_lookup, position_lookup, 2)
    house7 = _build_house_snapshot(house_lookup, position_lookup, 7)
    house10 = _build_house_snapshot(house_lookup, position_lookup, 10)

    strengths = {
        "structured_ambition": _new_rank_item(
            "structured_ambition",
            "структура, амбиция и умение держать высокий стандарт",
        ),
        "intuitive_depth": _new_rank_item(
            "intuitive_depth",
            "эмпатия, интуиция и чувство подводных процессов",
        ),
        "independent_innovation": _new_rank_item(
            "independent_innovation",
            "самостоятельность, свежий взгляд и способность обновлять правила",
        ),
        "resilient_influence": _new_rank_item(
            "resilient_influence",
            "стойкость в кризисах и влияние в сложных ситуациях",
        ),
    }
    risks = {
        "overcontrol_and_pressure": _new_rank_item(
            "overcontrol_and_pressure",
            "самопрессинг, перегруз и жесткость к себе",
        ),
        "emotional_withdrawal": _new_rank_item(
            "emotional_withdrawal",
            "привычка уходить в дистанцию вместо раннего разговора",
        ),
        "idealization_and_blur": _new_rank_item(
            "idealization_and_blur",
            "идеализация, размытые границы и неверная оценка ресурса",
        ),
        "stability_vs_freedom_swings": _new_rank_item(
            "stability_vs_freedom_swings",
            "качели между безопасной базой и резкими разворотами",
        ),
    }
    relationship_themes = {
        "freedom_plus_depth": _new_rank_item(
            "freedom_plus_depth",
            "в отношениях нужны свобода, дружеская база и при этом настоящая глубина",
        ),
        "safety_before_merging": _new_rank_item(
            "safety_before_merging",
            "близость раскрывается через безопасность, бережный темп и право не спешить",
        ),
        "shared_mission": _new_rank_item(
            "shared_mission",
            "сильнее всего работает союз, где есть общая цель и общий маршрут",
        ),
        "clear_honesty": _new_rank_item(
            "clear_honesty",
            "ключ к отношениям в прямом разговоре и ясных договоренностях",
        ),
    }
    money_themes = {
        "long_game_builder": _new_rank_item(
            "long_game_builder",
            "деньги лучше всего приходят через длинную стратегию, систему и репутацию",
        ),
        "network_value_creator": _new_rank_item(
            "network_value_creator",
            "доход усиливается через связи, сообщества, аудитории и современные форматы",
        ),
        "care_and_usefulness": _new_rank_item(
            "care_and_usefulness",
            "ресурс приходит там, где есть полезность, удержание и забота о людях",
        ),
        "crisis_strategy": _new_rank_item(
            "crisis_strategy",
            "финансовый ресурс включается в сложных задачах, трансформациях и работе с риском",
        ),
    }

    if _house_in(sun, {10}):
        _bump_rank(strengths, "structured_ambition", 18, _format_position_evidence(sun))
        _bump_rank(risks, "overcontrol_and_pressure", 12, _format_position_evidence(sun))
    if _house_in(saturn, {10}):
        _bump_rank(strengths, "structured_ambition", 18, _format_position_evidence(saturn))
        _bump_rank(risks, "overcontrol_and_pressure", 14, _format_position_evidence(saturn))
    if _house_in(mc, {10}) or _sign_in(mc, {"Capricorn"}):
        _bump_rank(strengths, "structured_ambition", 10, _format_position_evidence(mc))
        _bump_rank(money_themes, "long_game_builder", 12, _format_position_evidence(mc))
    if earth >= 35:
        evidence = _format_balance_evidence(balance, "elements", "Earth")
        _bump_rank(strengths, "structured_ambition", 12, evidence)
        _bump_rank(money_themes, "long_game_builder", 10, evidence)
        _bump_rank(risks, "overcontrol_and_pressure", 8, evidence)
    if cardinal >= 45:
        evidence = _format_balance_evidence(balance, "modes", "Cardinal")
        _bump_rank(strengths, "structured_ambition", 8, evidence)
        _bump_rank(risks, "stability_vs_freedom_swings", 8, evidence)
    if sun_saturn:
        evidence = _format_aspect_evidence(sun_saturn)
        _bump_rank(strengths, "structured_ambition", 16, evidence)
        _bump_rank(risks, "overcontrol_and_pressure", 16, evidence)
    if _sign_in(moon, {"Cancer", "Scorpio", "Pisces"}) or _house_in(moon, {8, 12}):
        evidence = _format_position_evidence(moon)
        _bump_rank(strengths, "intuitive_depth", 18, evidence)
        _bump_rank(relationship_themes, "safety_before_merging", 16, evidence)
        _bump_rank(risks, "emotional_withdrawal", 14, evidence)
    if water >= 30:
        evidence = _format_balance_evidence(balance, "elements", "Water")
        _bump_rank(strengths, "intuitive_depth", 10, evidence)
        _bump_rank(risks, "idealization_and_blur", 8, evidence)
    if moon_jupiter and _is_harmonious(moon_jupiter):
        evidence = _format_aspect_evidence(moon_jupiter)
        _bump_rank(strengths, "intuitive_depth", 12, evidence)
        _bump_rank(money_themes, "care_and_usefulness", 10, evidence)
    if _sign_in(venus, {"Aquarius", "Gemini", "Libra"}) or _house_in(venus, {11}):
        evidence = _format_position_evidence(venus)
        _bump_rank(strengths, "independent_innovation", 14, evidence)
        _bump_rank(relationship_themes, "freedom_plus_depth", 15, evidence)
        _bump_rank(money_themes, "network_value_creator", 12, evidence)
        _bump_rank(risks, "emotional_withdrawal", 8, evidence)
    if _sign_in(asc, {"Aries"}) or _sign_in(mars, {"Aries", "Sagittarius", "Aquarius"}):
        evidence = _format_position_evidence(mars) or _format_position_evidence(asc)
        _bump_rank(strengths, "independent_innovation", 10, evidence)
        _bump_rank(relationship_themes, "clear_honesty", 10, evidence)
        _bump_rank(risks, "stability_vs_freedom_swings", 8, evidence)
    if uranus and (_house_in(uranus, {1, 10, 11}) or _sign_in(uranus, {"Aquarius"})):
        evidence = _format_position_evidence(uranus)
        _bump_rank(strengths, "independent_innovation", 10, evidence)
        _bump_rank(money_themes, "network_value_creator", 8, evidence)
    if _house_in(pluto, {7, 8}) or _house_in(mars, {8}):
        evidence = _format_position_evidence(pluto) or _format_position_evidence(mars)
        _bump_rank(strengths, "resilient_influence", 14, evidence)
        _bump_rank(relationship_themes, "freedom_plus_depth", 12, evidence)
        _bump_rank(money_themes, "crisis_strategy", 12, evidence)
    if saturn_pluto and saturn_pluto.get("t") in {"sextile", "trine", "conjunction"}:
        evidence = _format_aspect_evidence(saturn_pluto)
        _bump_rank(strengths, "resilient_influence", 14, evidence)
        _bump_rank(money_themes, "crisis_strategy", 8, evidence)
    if sun_neptune:
        evidence = _format_aspect_evidence(sun_neptune)
        _bump_rank(strengths, "intuitive_depth", 8, evidence)
        _bump_rank(risks, "idealization_and_blur", 18, evidence)
    if _sign_in(moon, {"Pisces"}) or _house_in(neptune, {10, 12}):
        evidence = _format_position_evidence(moon) or _format_position_evidence(neptune)
        _bump_rank(risks, "idealization_and_blur", 10, evidence)
    if uranus_jupiter and _is_tense(uranus_jupiter):
        evidence = _format_aspect_evidence(uranus_jupiter)
        _bump_rank(risks, "stability_vs_freedom_swings", 18, evidence)
        _bump_rank(strengths, "independent_innovation", 8, evidence)
    if venus_mars and _is_harmonious(venus_mars):
        evidence = _format_aspect_evidence(venus_mars)
        _bump_rank(relationship_themes, "freedom_plus_depth", 8, evidence)
        _bump_rank(relationship_themes, "clear_honesty", 6, evidence)
    if venus and venus.get("r"):
        evidence = _format_position_evidence(venus)
        _bump_rank(risks, "emotional_withdrawal", 10, evidence)
    if house7:
        _bump_rank(relationship_themes, "shared_mission", 6, _format_house_snapshot(house7))
    if house10:
        _bump_rank(money_themes, "long_game_builder", 10, _format_house_snapshot(house10))
    if house2:
        snapshot_evidence = _format_house_snapshot(house2)
        _bump_rank(money_themes, "long_game_builder", 6, snapshot_evidence)
        if (house2.get("ruler_position") or {}).get("h") == 11:
            _bump_rank(money_themes, "network_value_creator", 12, snapshot_evidence)
        if (house2.get("ruler_position") or {}).get("h") == 8:
            _bump_rank(money_themes, "crisis_strategy", 12, snapshot_evidence)

    strengths_score = _finalize_ranked(strengths, limit=2)
    risk_score = _finalize_ranked(risks, limit=2)
    relationship_theme = _pick_primary_ranked(
        relationship_themes,
        fallback_key="clear_honesty",
        fallback_label="ключ к отношениям в прямом разговоре и ясных договоренностях",
        fallback_evidence=[
            _format_position_evidence(venus),
            _format_position_evidence(moon),
        ],
    )
    money_theme = _pick_primary_ranked(
        money_themes,
        fallback_key="long_game_builder",
        fallback_label="деньги лучше всего приходят через длинную стратегию, систему и репутацию",
        fallback_evidence=[
            _format_house_snapshot(house10),
            _format_position_evidence(saturn),
        ],
    )

    top_risk = risk_score[0]["key"] if risk_score else ""
    if top_risk == "overcontrol_and_pressure":
        development_label = "снижать внутренний прессинг и раньше замечать свои чувства, усталость и пределы"
        development_key = "soften_pressure_with_self_contact"
    elif top_risk == "idealization_and_blur":
        development_label = "проверять большие цели и сильные чувства фактами, сроками и режимом"
        development_key = "ground_vision_in_facts"
    elif top_risk == "stability_vs_freedom_swings":
        development_label = "сначала собирать базу и ритм, а уже потом делать резкие повороты"
        development_key = "stabilize_before_pivot"
    else:
        development_label = "не уходить в дистанцию: переводить напряжение в разговор и конкретные договоренности"
        development_key = "speak_before_withdrawal"

    development_focus = {
        "key": development_key,
        "label": development_label,
        "score": _score_to_int(
            (
                (risk_score[0]["score"] if risk_score else 55)
                + (strengths_score[0]["score"] if strengths_score else 55)
            )
            / 2
        ),
        "evidence": [
            *(risk_score[0]["evidence"][:2] if risk_score else []),
            *(strengths_score[0]["evidence"][:2] if strengths_score else []),
        ][:4],
    }

    top_strength = strengths_score[0] if strengths_score else {}
    top_risk_item = risk_score[0] if risk_score else {}
    strength_key = top_strength.get("key", "")
    risk_key = top_risk_item.get("key", "")
    relationship_key = relationship_theme.get("key", "")
    money_key = money_theme.get("key", "")

    strength_life_map = {
        "structured_ambition": "в жизни это выглядит как привычка брать на себя каркас, держать стандарт и собирать хаос в систему",
        "intuitive_depth": "в жизни это проявляется как раннее считывание подтекста, настроения и скрытых развилок",
        "independent_innovation": "в жизни это видно в нежелании жить по чужой схеме и в умении находить собственный ход",
        "resilient_influence": "в жизни это заметно в способности не разваливаться в кризисе, а собирать из него рычаг влияния",
    }
    relationship_manifestation_map = {
        "freedom_plus_depth": "в отношениях притягивают люди, с которыми можно и дышать свободно, и нырять глубоко без поверхностной игры",
        "safety_before_merging": "в отношениях всё раскрывается не быстро, а через ощущение безопасности, права на паузу и бережный темп",
        "shared_mission": "в отношениях сильнее всего включается союз, где есть общий маршрут, проект или ощущение совместной сборки будущего",
        "clear_honesty": "в отношениях лучше всего работает прямота: недосказанность быстро съедает энергию и доверие",
    }
    career_manifestation_map = {
        "long_game_builder": "в работе и деньгах лучший результат приходит там, где можно строить долго, накапливать репутацию и не жить только быстрым дофамином",
        "network_value_creator": "в карьере и деньгах ресурс включается через связи, среду, аудиторию и современные гибкие форматы",
        "care_and_usefulness": "в карьере и деньгах выигрыш идёт через полезность, удержание качества и реальную заботу о людях или процессе",
        "crisis_strategy": "в карьере и деньгах сила раскрывается, когда нужно разбирать сложность, риски и то, где другим некомфортно",
    }
    stress_manifestation_map = {
        "overcontrol_and_pressure": "под стрессом всё сжимается в режим внутреннего менеджера: больше контроля, меньше воздуха и почти нулевая терпимость к ошибке",
        "emotional_withdrawal": "под стрессом контакт гаснет раньше слов: становится проще исчезнуть внутрь себя, чем обозначить потребность прямо",
        "idealization_and_blur": "под стрессом растёт туман: хочется верить в красивую картину, игнорируя реальные сроки, границы и цену",
        "stability_vs_freedom_swings": "под стрессом включаются качели: сначала терпеть слишком долго, а потом резко переворачивать стол и маршрут",
    }
    trigger_map = {
        "overcontrol_and_pressure": ["высокая ставка", "слишком много ответственности", "ощущение, что ошибаться нельзя"],
        "emotional_withdrawal": ["неясные договоренности", "чувство небезопасности", "страх быть неправильно понятым"],
        "idealization_and_blur": ["слишком красивое обещание", "эмоционально заряженный образ", "отсутствие четких критериев"],
        "stability_vs_freedom_swings": ["долгое накопление скуки", "ощущение клетки", "внезапная тяга всё изменить одним рывком"],
    }
    sabotage_map = {
        "overcontrol_and_pressure": "самосаботаж идёт через привычку сначала пережать себя, а потом терять живую энергию и контакт с реальным состоянием",
        "emotional_withdrawal": "самосаботаж идёт через молчаливую дистанцию: важное не озвучивается вовремя и постепенно превращается в отчуждение",
        "idealization_and_blur": "самосаботаж идёт через красивую фантазию без достаточной проверки фактами, цифрами и режимом",
        "stability_vs_freedom_swings": "самосаботаж идёт через крайности: сначала удерживать слишком долго, потом ломать слишком резко",
    }
    compensation_map = {
        "overcontrol_and_pressure": "компенсация чаще всего выглядит как ещё большее ужесточение режима, требований и самоконтроля",
        "emotional_withdrawal": "компенсация чаще всего выглядит как уход в самостоятельность и демонстрацию, что помощь и разговор не нужны",
        "idealization_and_blur": "компенсация чаще всего выглядит как вера, что вдохновение и правильное чувство сами всё решат",
        "stability_vs_freedom_swings": "компенсация чаще всего выглядит как резкая смена курса вместо постепенной перенастройки",
    }
    do_map = {
        "structured_ambition": ["держать длинный горизонт", "снижать внутренний прессинг раньше перегруза", "назначать себе ясные критерии завершения"],
        "intuitive_depth": ["проверять ощущения фактами", "давать чувствам язык, а не только тишину", "оставлять место для восстановления"],
        "independent_innovation": ["сначала тестировать поворот на малом масштабе", "сохранять право на свой ход без разрушения базы", "искать среду, где идеи можно быстро проверять"],
        "resilient_influence": ["работать с кризисом дозированно", "переводить давление в стратегию", "не путать силу с постоянной перегрузкой"],
    }
    not_do_map = {
        "overcontrol_and_pressure": ["не принимать ключевые решения в пике самопрессинга", "не путать дисциплину с самонаказанием"],
        "emotional_withdrawal": ["не ждать, пока другой сам догадается", "не превращать паузу в исчезновение"],
        "idealization_and_blur": ["не соглашаться на красивый туман без критериев", "не строить всё на вдохновении без режима"],
        "stability_vs_freedom_swings": ["не делать резкий разворот без базы", "не терпеть слишком долго только ради видимой стабильности"],
    }
    best_mode_map = {
        "structured_ambition": "лучший режим действия — длинная стратегия, ясный каркас и ранняя коррекция перегруза",
        "intuitive_depth": "лучший режим действия — сначала почувствовать тон процесса, затем приземлить это в конкретный шаг",
        "independent_innovation": "лучший режим действия — короткие экспериментальные циклы поверх сохраненной опоры",
        "resilient_influence": "лучший режим действия — брать сложные узлы по одному и сразу превращать давление в структуру",
    }

    life_manifestations = [
        {
            "domain": "daily_life",
            "label": strength_life_map.get(strength_key, top_strength.get("label", "")),
            "evidence": top_strength.get("evidence", [])[:3],
        },
        {
            "domain": "relationships",
            "label": relationship_manifestation_map.get(relationship_key, relationship_theme.get("label", "")),
            "evidence": relationship_theme.get("evidence", [])[:3],
        },
        {
            "domain": "career",
            "label": career_manifestation_map.get(money_key, money_theme.get("label", "")),
            "evidence": money_theme.get("evidence", [])[:3],
        },
    ]
    stress_manifestation = {
        "key": f"{risk_key}_stress",
        "label": stress_manifestation_map.get(risk_key, top_risk_item.get("label", "")),
        "triggers": trigger_map.get(risk_key, []),
        "evidence": top_risk_item.get("evidence", [])[:4],
    }
    self_sabotage_pattern = {
        "key": f"{risk_key}_self_sabotage",
        "label": sabotage_map.get(risk_key, top_risk_item.get("label", "")),
        "evidence": top_risk_item.get("evidence", [])[:4],
    }
    compensation_pattern = {
        "key": f"{risk_key}_compensation",
        "label": compensation_map.get(risk_key, development_focus.get("label", "")),
        "evidence": [
            *(top_risk_item.get("evidence", [])[:2]),
            *(development_focus.get("evidence", [])[:2]),
        ][:4],
    }
    what_to_do = {
        "items": [
            *do_map.get(strength_key, []),
            development_focus.get("label"),
        ][:4],
        "evidence": development_focus.get("evidence", [])[:4],
    }
    what_not_to_do = {
        "items": not_do_map.get(risk_key, [])[:3],
        "evidence": top_risk_item.get("evidence", [])[:3],
    }
    best_mode_of_action = {
        "key": f"{strength_key or 'steady'}_best_mode",
        "label": best_mode_map.get(strength_key, development_focus.get("label", "")),
        "evidence": [
            *(top_strength.get("evidence", [])[:2]),
            *(money_theme.get("evidence", [])[:2]),
        ][:4],
    }
    scene_seeds = [
        {
            "title": "рабочая сцена",
            "seed": (
                "человек, который первым собирает задачу в систему, но рискует взять на себя лишний вес и слишком долго держать всё на личной воле"
                if strength_key == "structured_ambition"
                else "человек, который быстро чувствует, где скрытый узел, но под стрессом может уйти в перегруз, туман или дистанцию"
            ),
        },
        {
            "title": "личная сцена",
            "seed": relationship_manifestation_map.get(
                relationship_key,
                "в близости важнее всего не сама интенсивность, а то, насколько рано удаётся назвать потребность и границу",
            ),
        },
    ]

    return {
        "version": "natal_v2_p0",
        "strengths_score": strengths_score,
        "risk_score": risk_score,
        "relationship_theme": relationship_theme,
        "money_theme": money_theme,
        "development_focus": development_focus,
        "life_manifestations": life_manifestations,
        "stress_manifestation": stress_manifestation,
        "self_sabotage_pattern": self_sabotage_pattern,
        "compensation_pattern": compensation_pattern,
        "what_to_do": what_to_do,
        "what_not_to_do": what_not_to_do,
        "best_mode_of_action": best_mode_of_action,
        "scene_seeds": scene_seeds,
        "cross_links": [
            "synthesis.identity_vector",
            "love_intimacy.attachment_style",
            "money_realization.career_vector",
        ],
    }


def _build_synthesis_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    executive_pack = _build_executive_summary_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    strengths = executive_pack.get("strengths_score", [])
    risks = executive_pack.get("risk_score", [])

    primary_strength = strengths[0] if strengths else {}
    secondary_strength = strengths[1] if len(strengths) > 1 else primary_strength
    primary_risk = risks[0] if risks else {}

    primary_key = primary_strength.get("key")
    secondary_key = secondary_strength.get("key")
    risk_key = primary_risk.get("key")

    if primary_key == "structured_ambition" and secondary_key == "intuitive_depth":
        identity_key = "structured_sensitive_strategist"
        identity_label = "структурный стратег: снаружи строишь каркас, внутри считываешь тонкие процессы"
    elif primary_key == "structured_ambition" and secondary_key == "independent_innovation":
        identity_key = "system_reformer"
        identity_label = "системный реформатор: умеешь держать порядок и одновременно обновлять правила"
    elif primary_key == "intuitive_depth":
        identity_key = "deep_sensor"
        identity_label = "глубокий чувствующий наблюдатель, который видит скрытые мотивы и связи"
    else:
        identity_key = "steady_transformer"
        identity_label = "устойчивый трансформатор: собираешь сложность в рабочую систему"

    if risk_key == "overcontrol_and_pressure" and secondary_key == "intuitive_depth":
        conflict_key = "control_vs_sensitivity"
        conflict_label = "между контролем, высоким стандартом и необходимостью не подавлять чувствительность"
    elif risk_key == "stability_vs_freedom_swings":
        conflict_key = "stability_vs_freedom"
        conflict_label = "между безопасной базой и желанием резко менять траекторию"
    elif risk_key == "emotional_withdrawal":
        conflict_key = "depth_vs_distance"
        conflict_label = "между потребностью в глубине и привычкой уходить в дистанцию или молчание"
    else:
        conflict_key = "vision_vs_grounding"
        conflict_label = "между большим образом, интуицией и требованием к конкретике"

    identity_vector = {
        "key": identity_key,
        "label": identity_label,
        "score": _score_to_int(
            (
                primary_strength.get("score", 55)
                + secondary_strength.get("score", primary_strength.get("score", 55))
            )
            / 2
        ),
        "evidence": [
            *(primary_strength.get("evidence", [])[:2]),
            *(secondary_strength.get("evidence", [])[:2]),
        ][:4],
    }
    core_conflict = {
        "key": conflict_key,
        "label": conflict_label,
        "score": _score_to_int(primary_risk.get("score", 55)),
        "evidence": primary_risk.get("evidence", [])[:4],
    }

    drive_labels = {
        "structured_ambition": "мастерство, результат и высокий стандарт",
        "intuitive_depth": "смысл, эмоциональная правда и чувствительность к невидимому",
        "independent_innovation": "свобода, эксперимент и право идти своим маршрутом",
        "resilient_influence": "влияние, глубина и работа со сложностью",
    }
    dominant_drives = []
    for strength in strengths[:3]:
        dominant_drives.append(
            {
                "key": strength.get("key"),
                "label": drive_labels.get(strength.get("key"), strength.get("label")),
                "score": strength.get("score", 50),
                "evidence": strength.get("evidence", [])[:3],
            }
        )
    if not dominant_drives:
        dominant_drives.append(
            {
                "key": "steady_growth",
                "label": "рост через устойчивость и последовательность",
                "score": 50,
                "evidence": [],
            }
        )

    if identity_key == "structured_sensitive_strategist":
        metaphor_label = "высокая опорная башня с внутренним радаром глубины"
        metaphor_keywords = ["каркас", "высота", "скрытая чувствительность"]
    elif identity_key == "system_reformer":
        metaphor_label = "диспетчер сложной системы, который обновляет правила без потери каркаса"
        metaphor_keywords = ["система", "обновление", "маршрут"]
    elif identity_key == "deep_sensor":
        metaphor_label = "тихий глубинный локатор, который считывает то, что другим не видно"
        metaphor_keywords = ["глубина", "наблюдение", "смысл"]
    else:
        metaphor_label = "человек-каркас, который собирает кризис в рабочую форму"
        metaphor_keywords = ["сборка", "давление", "форма"]

    map_metaphor_seed = {
        "key": f"{identity_key}_seed",
        "label": metaphor_label,
        "keywords": metaphor_keywords,
        "evidence": [
            *(identity_vector.get("evidence", [])[:2]),
            *(core_conflict.get("evidence", [])[:2]),
        ][:4],
    }

    life_story_map = {
        "structured_sensitive_strategist": "сюжет жизни часто строится так: внешне держать каркас, внутри всё время сверяться с тонкими сигналами и скрытыми подводными течениями",
        "system_reformer": "сюжет жизни часто строится так: входить в уже существующую систему, видеть её слабое место и постепенно обновлять правила изнутри",
        "deep_sensor": "сюжет жизни часто строится так: сначала долго считывать глубину и мотив, а потом говорить только то, что реально меняет смысл происходящего",
        "steady_transformer": "сюжет жизни часто строится так: брать сложный, перегретый или запутанный материал и превращать его в рабочую форму",
    }
    conflict_manifestation_map = {
        "control_vs_sensitivity": "внутренний конфликт проявляется в жизни как спор между высоким стандартом и живой чувствительностью: хочется быть сильным и собранным, но нельзя гасить тонкость ради эффективности",
        "stability_vs_freedom": "внутренний конфликт проявляется как качели между опорой и резким разворотом: сначала строить базу, а потом хотеть сбросить её одним движением",
        "depth_vs_distance": "внутренний конфликт проявляется как чередование потребности в глубине и привычки отходить на дистанцию, когда связь становится слишком реальной",
        "vision_vs_grounding": "внутренний конфликт проявляется как напряжение между большим образом, интуицией и необходимостью приземлять всё в срок, ритм и факт",
    }
    triggers_map = {
        "control_vs_sensitivity": ["жёсткий дедлайн", "оценка со стороны", "ощущение, что надо держать лицо"],
        "stability_vs_freedom": ["долгое однообразие", "ощущение клетки", "внезапно открывшаяся новая возможность"],
        "depth_vs_distance": ["слишком близкий разговор", "ожидание эмоциональной прозрачности", "страх показать уязвимость"],
        "vision_vs_grounding": ["красивый большой план без критериев", "неопределенность сроков", "слишком много смыслов и мало формы"],
    }
    sabotage_map = {
        "control_vs_sensitivity": "самосаботаж здесь в том, что контроль начинает подменять контакт с собой и лишает силу живого ресурса",
        "stability_vs_freedom": "самосаботаж здесь в крайностях: либо слишком держать, либо слишком резко ломать",
        "depth_vs_distance": "самосаботаж здесь в том, что потребность в глубине выражается не словами, а исчезновением или молчаливым отступлением",
        "vision_vs_grounding": "самосаботаж здесь в том, что большой образ не получает режима и начинает размывать решение",
    }
    compensation_map = {
        "control_vs_sensitivity": "компенсация идёт через ещё большую собранность, жёсткость и отказ от слабости",
        "stability_vs_freedom": "компенсация идёт через резкий поворот, чтобы не чувствовать накопленное внутреннее сжатие",
        "depth_vs_distance": "компенсация идёт через самоизоляцию, независимость и образ человека, которому никто не нужен",
        "vision_vs_grounding": "компенсация идёт через вдохновляющий образ вместо конкретного следующего шага",
    }
    action_map = {
        "structured_sensitive_strategist": "лучший режим действия — строить каркас, но оставлять внутри него живую обратную связь от тела, чувств и среды",
        "system_reformer": "лучший режим действия — менять не всё сразу, а поэтапно, сохраняя рабочую опору и право на корректировку",
        "deep_sensor": "лучший режим действия — сначала назвать главное скрытое напряжение, потом переводить его в простой и точный шаг",
        "steady_transformer": "лучший режим действия — не бороться со сложностью лоб в лоб, а собирать её в форму, которую можно удерживать долго",
    }

    core_life_story = {
        "key": f"{identity_key}_life_story",
        "label": life_story_map.get(identity_key, identity_label),
        "evidence": identity_vector.get("evidence", [])[:4],
    }
    life_manifestations = [
        {
            "domain": "work",
            "label": (
                "в работе это даёт роль человека, который держит структуру и собирает смысл, даже если другие уже теряют нить"
                if identity_key in {"structured_sensitive_strategist", "steady_transformer"}
                else "в работе это даёт роль человека, который меняет систему или считывает то, что не лежит на поверхности"
            ),
            "evidence": identity_vector.get("evidence", [])[:3],
        },
        {
            "domain": "relationships",
            "label": (
                "в близости это создаёт потребность одновременно в глубине и в возможности не терять автономию"
                if conflict_key in {"depth_vs_distance", "stability_vs_freedom"}
                else "в близости это создаёт запрос на связь, где можно быть и сильным, и живым, не теряя одну часть ради другой"
            ),
            "evidence": core_conflict.get("evidence", [])[:3],
        },
        {
            "domain": "stress",
            "label": conflict_manifestation_map.get(conflict_key, core_conflict.get("label", "")),
            "evidence": core_conflict.get("evidence", [])[:3],
        },
    ]
    inner_conflict_dynamics = {
        "key": f"{conflict_key}_dynamics",
        "label": conflict_manifestation_map.get(conflict_key, core_conflict.get("label", "")),
        "triggers": triggers_map.get(conflict_key, []),
        "evidence": core_conflict.get("evidence", [])[:4],
    }
    self_sabotage_pattern = {
        "key": f"{conflict_key}_self_sabotage",
        "label": sabotage_map.get(conflict_key, core_conflict.get("label", "")),
        "evidence": core_conflict.get("evidence", [])[:4],
    }
    compensation_pattern = {
        "key": f"{conflict_key}_compensation",
        "label": compensation_map.get(conflict_key, identity_vector.get("label", "")),
        "evidence": [
            *(identity_vector.get("evidence", [])[:2]),
            *(core_conflict.get("evidence", [])[:2]),
        ][:4],
    }
    what_to_do = {
        "items": [
            action_map.get(identity_key, "держать смысл и форму одновременно"),
            "переводить внутреннее напряжение в задачу, разговор или конкретный ритм",
            "замечать, где конфликт уже начался, до того как он превратится в судьбу дня или отношений",
        ],
        "evidence": [
            *(identity_vector.get("evidence", [])[:2]),
            *(core_conflict.get("evidence", [])[:2]),
        ][:4],
    }
    what_not_to_do = {
        "items": [
            "не строить жизнь только вокруг своей сильной стороны, выдавливая противоположный полюс",
            "не ждать, что конфликт исчезнет сам, если его долго не называть",
            "не принимать пик внутреннего напряжения за окончательную правду о себе",
        ],
        "evidence": core_conflict.get("evidence", [])[:3],
    }
    best_mode_of_action = {
        "key": f"{identity_key}_best_mode",
        "label": action_map.get(identity_key, identity_vector.get("label", "")),
        "evidence": identity_vector.get("evidence", [])[:4],
    }
    scene_seeds = [
        {
            "title": "внутренняя сцена",
            "seed": conflict_manifestation_map.get(conflict_key, core_conflict.get("label", "")),
        },
        {
            "title": "жизненная сцена",
            "seed": life_story_map.get(identity_key, identity_vector.get("label", "")),
        },
    ]

    return {
        "version": "natal_v2_p0",
        "identity_vector": identity_vector,
        "core_conflict": core_conflict,
        "dominant_drives": dominant_drives,
        "map_metaphor_seed": map_metaphor_seed,
        "core_life_story": core_life_story,
        "life_manifestations": life_manifestations,
        "inner_conflict_dynamics": inner_conflict_dynamics,
        "self_sabotage_pattern": self_sabotage_pattern,
        "compensation_pattern": compensation_pattern,
        "what_to_do": what_to_do,
        "what_not_to_do": what_not_to_do,
        "best_mode_of_action": best_mode_of_action,
        "scene_seeds": scene_seeds,
        "cross_links": [
            "executive_summary.strengths_score",
            "executive_summary.risk_score",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_framework_elements_modes_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    balance = _get_balance_snapshot(facts, chart_data)

    element_rank = _rank_balance_family(balance, "elements", ["Fire", "Earth", "Air", "Water"])
    mode_rank = _rank_balance_family(balance, "modes", ["Cardinal", "Fixed", "Mutable"])

    element_labels = {
        "Fire": "Огонь: энергия старта, воля и импульс к действию",
        "Earth": "Земля: устойчивость, форма и способность опираться на реальность",
        "Air": "Воздух: контакт, идеи и интеллектуальная подвижность",
        "Water": "Вода: чувствительность, интуиция и эмоциональная глубина",
    }
    mode_labels = {
        "Cardinal": "Кардинальность: запуск, инициатива и способность открывать цикл",
        "Fixed": "Фиксированность: удержание, концентрация и инерция",
        "Mutable": "Мутабельность: адаптация, настройка и гибкость",
    }
    combo_labels = {
        ("Fire", "Cardinal"): "темперамент инициатора: быстро загораться, брать старт и вести импульсом",
        ("Earth", "Cardinal"): "темперамент системного организатора: запускать через план, задачу и конструкцию",
        ("Air", "Cardinal"): "темперамент социального стратега: начинать через идеи, контакты и переговоры",
        ("Water", "Cardinal"): "темперамент эмоционального лидера: включаться через чувство значимости и внутренний отклик",
        ("Fire", "Fixed"): "темперамент носителя воли: держать курс мощно, ярко и упрямо",
        ("Earth", "Fixed"): "темперамент стабилизатора: строить надолго, удерживать ресурс и не спешить с разворотом",
        ("Air", "Fixed"): "темперамент концептуального держателя: стоять на идее, принципе и собственной логике",
        ("Water", "Fixed"): "темперамент глубинного хранителя: долго проживать, помнить и эмоционально фиксировать важное",
        ("Fire", "Mutable"): "темперамент подвижного мотора: быстро адаптироваться, но жить с избытком искр и переключений",
        ("Earth", "Mutable"): "темперамент практичного настройщика: улучшать процессы и наводить порядок через детали",
        ("Air", "Mutable"): "темперамент коммуникационного сканера: быстро учиться, связывать и собирать сигналы",
        ("Water", "Mutable"): "темперамент тонкого эмпата: улавливать атмосферу и менять режим по внутренней погоде",
    }
    deficit_advice = {
        "Fire": "добавлять прямой старт, право хотеть и привычку действовать без долгой раскачки",
        "Earth": "добавлять режим, телесную опору, конкретные шаги и финансовую/бытовую структуру",
        "Air": "добавлять разговор, интеллектуальный обмен и возможность смотреть на себя со стороны",
        "Water": "добавлять паузу, чувствительность к состоянию и экологичный контакт с эмоцией",
        "Cardinal": "осознанно тренировать старт и способность самому открывать новый цикл",
        "Fixed": "тренировать выдержку, ритм и навык доводить начатое без лишней суеты",
        "Mutable": "тренировать гибкость, допуск к корректировке и умение менять план без краха самооценки",
    }

    for item in element_rank:
        item["label"] = element_labels.get(item["key"], item["key"])
    for item in mode_rank:
        item["label"] = mode_labels.get(item["key"], item["key"])

    dominant_element = element_rank[0] if element_rank else {"key": "Earth", "score": 0, "evidence": []}
    weakest_element = element_rank[-1] if element_rank else {"key": "Water", "score": 0, "evidence": []}
    dominant_mode = mode_rank[0] if mode_rank else {"key": "Cardinal", "score": 0, "evidence": []}
    weakest_mode = mode_rank[-1] if mode_rank else {"key": "Mutable", "score": 0, "evidence": []}

    dominant_signature = {
        "key": f"{dominant_element['key'].lower()}_{dominant_mode['key'].lower()}",
        "label": combo_labels.get(
            (dominant_element.get("key"), dominant_mode.get("key")),
            "темперамент читается через ведущую стихию и модальность карты",
        ),
        "score": _score_to_int(
            (dominant_element.get("score", 0) + dominant_mode.get("score", 0)) / 2
        ),
        "evidence": [
            *(dominant_element.get("evidence", [])[:2]),
            *(dominant_mode.get("evidence", [])[:2]),
        ][:4],
    }
    deficit_signature = {
        "key": f"{weakest_element['key'].lower()}_{weakest_mode['key'].lower()}_deficit",
        "label": (
            f"зона подпитки — {element_labels.get(weakest_element.get('key'), weakest_element.get('key')).split(':', 1)[0].lower()} "
            f"и {mode_labels.get(weakest_mode.get('key'), weakest_mode.get('key')).split(':', 1)[0].lower()}"
        ),
        "growth": (
            f"{deficit_advice.get(weakest_element.get('key'), 'добавлять недостающую стихию')}; "
            f"{deficit_advice.get(weakest_mode.get('key'), 'добавлять недостающую модальность')}"
        ),
        "evidence": [
            *(weakest_element.get("evidence", [])[:2]),
            *(weakest_mode.get("evidence", [])[:2]),
        ][:4],
    }

    if dominant_mode.get("key") == "Cardinal":
        lifestyle_label = "лучший стиль жизни — запускать циклами, но заранее собирать критерии завершения, иначе энергии будет много, а устойчивости меньше"
    elif dominant_mode.get("key") == "Fixed":
        lifestyle_label = "лучший стиль жизни — строить ритм и долгую опору, а перемены вводить дозированно, чтобы не застревать в инерции"
    else:
        lifestyle_label = "лучший стиль жизни — держать гибкий маршрут, но фиксировать опорные точки, чтобы адаптация не превращалась в распыление"

    balance_formula = {
        "key": "balance_formula",
        "label": (
            f"формула баланса: опираться на {dominant_element.get('key')} + {dominant_mode.get('key')}, "
            f"но регулярно подпитывать {weakest_element.get('key')} и {weakest_mode.get('key')}"
        ),
        "evidence": [
            dominant_signature.get("label"),
            deficit_signature.get("growth"),
        ][:4],
    }
    lifestyle_vector = {
        "key": "lifestyle_vector",
        "label": lifestyle_label,
        "evidence": [
            dominant_signature.get("label"),
            deficit_signature.get("label"),
        ][:4],
    }

    return {
        "version": "natal_v2_p4",
        "element_rank": element_rank,
        "mode_rank": mode_rank,
        "dominant_signature": dominant_signature,
        "deficit_signature": deficit_signature,
        "lifestyle_vector": lifestyle_vector,
        "balance_formula": balance_formula,
        "cross_links": [
            "executive_summary.development_focus",
            "synthesis.identity_vector",
            "final_synthesis.one_sentence_advice",
        ],
    }
# END_BLOCK: INSIGHT_SUMMARY_PACKS
