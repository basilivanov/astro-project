# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-RELATIONSHIPS
# purpose: Build money, realization, love, and intimacy natal insight packs.
# inputs: compact chart_pack dictionaries produced by insight core.
# outputs: insight_pack dictionaries for relationship and resource sections.
# invariants: scoring, evidence, and copy templates remain unchanged.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-RELATIONSHIPS

# START_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-RELATIONSHIPS
# entrypoints:
#   - _build_money_realization_insight_pack -> MONEY_REALIZATION_PACK
#   - _build_love_intimacy_insight_pack -> LOVE_INTIMACY_PACK
# END_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-RELATIONSHIPS

from __future__ import annotations

from .report_workflow_insight_core import *

# START_BLOCK: INSIGHT_RELATIONSHIP_PACKS
def _build_money_realization_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    balance = _get_balance_snapshot(facts, chart_data)
    earth = _balance_value(balance, "elements", "Earth")
    cardinal = _balance_value(balance, "modes", "Cardinal")

    sun = position_lookup.get("Sun")
    venus = position_lookup.get("Venus")
    mars = position_lookup.get("Mars")
    jupiter = position_lookup.get("Jupiter")
    saturn = position_lookup.get("Saturn")
    uranus = position_lookup.get("Uranus")
    neptune = position_lookup.get("Neptune")
    mc = position_lookup.get("MC")

    house2 = _build_house_snapshot(house_lookup, position_lookup, 2)
    house6 = _build_house_snapshot(house_lookup, position_lookup, 6)
    house10 = _build_house_snapshot(house_lookup, position_lookup, 10)

    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")
    saturn_neptune = _find_aspect(chart_data, "Saturn", "Neptune")
    uranus_jupiter = _find_aspect(chart_data, "Uranus", "Jupiter")
    saturn_pluto = _find_aspect(chart_data, "Saturn", "Pluto")

    career_vectors = {
        "systems_leader": _new_rank_item(
            "systems_leader",
            "реализация через систему, управленческий каркас, стандарты и репутацию",
        ),
        "network_builder": _new_rank_item(
            "network_builder",
            "реализация через сообщества, связи, аудитории и современные форматы",
        ),
        "care_container": _new_rank_item(
            "care_container",
            "реализация через полезность, поддержку, удержание и заботу о людях",
        ),
        "crisis_specialist": _new_rank_item(
            "crisis_specialist",
            "реализация через сложные задачи, трансформации и работу с риском",
        ),
    }
    money_patterns = {
        "long_cycle_accumulation": _new_rank_item(
            "long_cycle_accumulation",
            "деньги растут через длинный горизонт, дисциплину и накопление репутации",
        ),
        "networked_income": _new_rank_item(
            "networked_income",
            "доход приходит через связи, проекты с людьми и распределенные каналы",
        ),
        "service_expertise": _new_rank_item(
            "service_expertise",
            "деньги включаются через экспертизу, регулярную полезность и качество процесса",
        ),
        "shared_resources": _new_rank_item(
            "shared_resources",
            "деньги приходят через совместные ресурсы, кризисные задачи и стратегию риска",
        ),
    }
    realization_modes = {
        "disciplined_climb": _new_rank_item(
            "disciplined_climb",
            "лучший режим реализации: длинный подъем, ясный KPI и последовательный рост статуса",
        ),
        "autonomous_project_cycles": _new_rank_item(
            "autonomous_project_cycles",
            "лучший режим реализации: автономные проектные циклы и право быстро принимать решения",
        ),
        "community_platform": _new_rank_item(
            "community_platform",
            "лучший режим реализации: платформа, сеть, аудитория и совместные инициативы",
        ),
        "deep_problem_solving": _new_rank_item(
            "deep_problem_solving",
            "лучший режим реализации: разбирать сложность, кризисы и неоднозначные кейсы",
        ),
    }
    work_risks = {
        "overwork_and_rigidity": _new_rank_item(
            "overwork_and_rigidity",
            "риск: перегруз, внутренний прессинг и жесткость к себе",
        ),
        "blurred_goalposts": _new_rank_item(
            "blurred_goalposts",
            "риск: размытые критерии, идеализация проекта или плохая оценка ресурса",
        ),
        "zigzag_decisions": _new_rank_item(
            "zigzag_decisions",
            "риск: резкие развороты и доходные качели из-за импульсивных смен курса",
        ),
        "value_revisions": _new_rank_item(
            "value_revisions",
            "риск: затяжные пересмотры цены, условий и собственной ценности",
        ),
        "power_drains": _new_rank_item(
            "power_drains",
            "риск: втягиваться в тяжелые силовые игры, кризисы и чужое напряжение",
        ),
    }

    if house10:
        evidence = _format_house_snapshot(house10)
        _bump_rank(career_vectors, "systems_leader", 16, evidence)
        _bump_rank(money_patterns, "long_cycle_accumulation", 10, evidence)
        if house10.get("sign") in {"Aquarius", "Gemini", "Libra"}:
            _bump_rank(career_vectors, "network_builder", 10, evidence)
        if house10.get("sign") in {"Cancer", "Pisces"}:
            _bump_rank(career_vectors, "care_container", 10, evidence)
        if house10.get("sign") in {"Scorpio"}:
            _bump_rank(career_vectors, "crisis_specialist", 10, evidence)
    if house2:
        evidence = _format_house_snapshot(house2)
        _bump_rank(money_patterns, "long_cycle_accumulation", 8, evidence)
        ruler_house = (house2.get("ruler_position") or {}).get("h")
        if ruler_house == 11:
            _bump_rank(money_patterns, "networked_income", 14, evidence)
        if ruler_house == 8:
            _bump_rank(money_patterns, "shared_resources", 14, evidence)
        if ruler_house in {6, 10}:
            _bump_rank(money_patterns, "service_expertise", 12, evidence)
    if house6:
        evidence = _format_house_snapshot(house6)
        _bump_rank(realization_modes, "disciplined_climb", 8, evidence)
        ruler_house = (house6.get("ruler_position") or {}).get("h")
        if ruler_house in {10, 11}:
            _bump_rank(realization_modes, "community_platform", 10, evidence)
        if ruler_house in {8, 12}:
            _bump_rank(realization_modes, "deep_problem_solving", 10, evidence)
        if ruler_house in {1, 9}:
            _bump_rank(realization_modes, "autonomous_project_cycles", 10, evidence)

    if _house_in(sun, {10}) or _house_in(saturn, {10}) or _house_in(mc, {10}):
        evidence = _format_position_evidence(sun) or _format_position_evidence(saturn) or _format_position_evidence(mc)
        _bump_rank(career_vectors, "systems_leader", 16, evidence)
        _bump_rank(realization_modes, "disciplined_climb", 12, evidence)
        _bump_rank(work_risks, "overwork_and_rigidity", 12, evidence)
    if earth >= 35:
        evidence = _format_balance_evidence(balance, "elements", "Earth")
        _bump_rank(career_vectors, "systems_leader", 10, evidence)
        _bump_rank(money_patterns, "long_cycle_accumulation", 10, evidence)
        _bump_rank(realization_modes, "disciplined_climb", 8, evidence)
    if cardinal >= 45:
        evidence = _format_balance_evidence(balance, "modes", "Cardinal")
        _bump_rank(realization_modes, "disciplined_climb", 6, evidence)
        _bump_rank(work_risks, "zigzag_decisions", 6, evidence)
    if _house_in(venus, {11}) or _sign_in(venus, {"Aquarius", "Gemini", "Libra"}):
        evidence = _format_position_evidence(venus)
        _bump_rank(career_vectors, "network_builder", 12, evidence)
        _bump_rank(money_patterns, "networked_income", 14, evidence)
        _bump_rank(realization_modes, "community_platform", 12, evidence)
    if _sign_in(jupiter, {"Cancer", "Pisces"}) or _house_in(jupiter, {4, 12}):
        evidence = _format_position_evidence(jupiter)
        _bump_rank(career_vectors, "care_container", 12, evidence)
        _bump_rank(money_patterns, "service_expertise", 8, evidence)
    if _house_in(mars, {8}) or _house_in(position_lookup.get("Pluto"), {7, 8}):
        evidence = _format_position_evidence(mars) or _format_position_evidence(position_lookup.get("Pluto"))
        _bump_rank(career_vectors, "crisis_specialist", 14, evidence)
        _bump_rank(money_patterns, "shared_resources", 12, evidence)
        _bump_rank(realization_modes, "deep_problem_solving", 10, evidence)
        _bump_rank(work_risks, "power_drains", 10, evidence)
    if saturn_pluto and saturn_pluto.get("t") in {"sextile", "trine", "conjunction"}:
        evidence = _format_aspect_evidence(saturn_pluto)
        _bump_rank(career_vectors, "crisis_specialist", 8, evidence)
        _bump_rank(realization_modes, "deep_problem_solving", 8, evidence)
    if sun_neptune or saturn_neptune:
        evidence = _format_aspect_evidence(sun_neptune) or _format_aspect_evidence(saturn_neptune)
        _bump_rank(work_risks, "blurred_goalposts", 16, evidence)
    if uranus_jupiter and _is_tense(uranus_jupiter):
        evidence = _format_aspect_evidence(uranus_jupiter)
        _bump_rank(work_risks, "zigzag_decisions", 16, evidence)
        _bump_rank(realization_modes, "autonomous_project_cycles", 8, evidence)
    if venus and venus.get("r"):
        evidence = _format_position_evidence(venus)
        _bump_rank(work_risks, "value_revisions", 14, evidence)

    career_vector = _pick_primary_ranked(
        career_vectors,
        fallback_key="systems_leader",
        fallback_label="реализация через систему, управленческий каркас, стандарты и репутацию",
        fallback_evidence=[
            _format_house_snapshot(house10),
            _format_position_evidence(saturn),
        ],
    )
    money_pattern = _pick_primary_ranked(
        money_patterns,
        fallback_key="long_cycle_accumulation",
        fallback_label="деньги растут через длинный горизонт, дисциплину и накопление репутации",
        fallback_evidence=[
            _format_house_snapshot(house2),
            _format_position_evidence(venus),
        ],
    )
    realization_mode = _pick_primary_ranked(
        realization_modes,
        fallback_key="disciplined_climb",
        fallback_label="лучший режим реализации: длинный подъем, ясный KPI и последовательный рост статуса",
        fallback_evidence=[
            _format_house_snapshot(house6),
            _format_position_evidence(sun),
        ],
    )
    work_risk_flags = _finalize_ranked(work_risks, limit=3)

    return {
        "version": "natal_v2_p0",
        "career_vector": career_vector,
        "money_pattern": money_pattern,
        "work_risk_flags": work_risk_flags,
        "realization_mode": realization_mode,
        "cross_links": [
            "executive_summary.money_theme",
            "synthesis.identity_vector",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _build_love_intimacy_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    venus = position_lookup.get("Venus")
    mars = position_lookup.get("Mars")
    moon = position_lookup.get("Moon")
    saturn = position_lookup.get("Saturn")
    pluto = position_lookup.get("Pluto")
    uranus = position_lookup.get("Uranus")

    house5 = _build_house_snapshot(house_lookup, position_lookup, 5)
    house7 = _build_house_snapshot(house_lookup, position_lookup, 7)
    house8 = _build_house_snapshot(house_lookup, position_lookup, 8)

    venus_mars = _find_aspect(chart_data, "Venus", "Mars")
    moon_uranus = _find_aspect(chart_data, "Moon", "Uranus")
    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")

    attachment_styles = {
        "freedom_then_depth": _new_rank_item(
            "freedom_then_depth",
            "привязанность строится через свободу и дружескую базу, но внутри нужна очень глубокая близость",
        ),
        "soft_private_bonding": _new_rank_item(
            "soft_private_bonding",
            "чувства раскрываются мягко: через безопасность, приватность и неспешность",
        ),
        "steady_tested_commitment": _new_rank_item(
            "steady_tested_commitment",
            "близость проходит через проверку временем, надежностью и зрелыми рамками",
        ),
        "idealized_merge": _new_rank_item(
            "idealized_merge",
            "есть тяга к слиянию и идеалу, поэтому важно отличать реального человека от фантазии",
        ),
    }
    partnership_needs_candidates = {
        "friendship_clarity_loyalty": _new_rank_item(
            "friendship_clarity_loyalty",
            "нужны дружеская база, честный разговор и лояльность без игр",
        ),
        "safety_time_privacy": _new_rank_item(
            "safety_time_privacy",
            "нужны бережный темп, эмоциональная безопасность и право на тишину",
        ),
        "shared_future_and_work": _new_rank_item(
            "shared_future_and_work",
            "нужны общая цель, уважение к амбиции и партнерская надежность",
        ),
        "passion_and_depth": _new_rank_item(
            "passion_and_depth",
            "нужны сексуальная честность, глубина и доверие в уязвимости",
        ),
    }
    conflict_styles = {
        "silent_accumulation_then_surge": _new_rank_item(
            "silent_accumulation_then_surge",
            "конфликтный стиль: копить напряжение внутри, а потом выдавать его резко и мощно",
        ),
        "direct_and_principled": _new_rank_item(
            "direct_and_principled",
            "конфликтный стиль: говорить прямо, но на принципах и высоком стандарте",
        ),
        "detach_then_recalibrate": _new_rank_item(
            "detach_then_recalibrate",
            "конфликтный стиль: сначала отстраниться, охладить эмоцию и только потом обсуждать",
        ),
        "control_and_loyalty_tests": _new_rank_item(
            "control_and_loyalty_tests",
            "конфликтный стиль: проверять границы, верность и устойчивость партнера",
        ),
    }
    risk_flags = {
        "distance_instead_of_request": _new_rank_item(
            "distance_instead_of_request",
            "риск: уходить в дистанцию и молчание вместо прямой просьбы",
        ),
        "hot_cold_pattern": _new_rank_item(
            "hot_cold_pattern",
            "риск: режим то близко, то далеко, если свобода и глубина не согласованы",
        ),
        "idealization_then_disappointment": _new_rank_item(
            "idealization_then_disappointment",
            "риск: видеть идеал и позже сталкиваться с разочарованием",
        ),
        "fear_of_vulnerability": _new_rank_item(
            "fear_of_vulnerability",
            "риск: путать близость с потерей контроля и потому долго не раскрывать уязвимость",
        ),
    }

    if _sign_in(venus, {"Aquarius", "Gemini", "Libra"}) or _house_in(venus, {11}):
        evidence = _format_position_evidence(venus)
        _bump_rank(attachment_styles, "freedom_then_depth", 16, evidence)
        _bump_rank(partnership_needs_candidates, "friendship_clarity_loyalty", 14, evidence)
        _bump_rank(conflict_styles, "detach_then_recalibrate", 12, evidence)
        _bump_rank(risk_flags, "hot_cold_pattern", 10, evidence)
        _bump_rank(risk_flags, "distance_instead_of_request", 8, evidence)
    if _house_in(mars, {8}) or _house_in(pluto, {7, 8}):
        evidence = _format_position_evidence(mars) or _format_position_evidence(pluto)
        _bump_rank(attachment_styles, "freedom_then_depth", 14, evidence)
        _bump_rank(partnership_needs_candidates, "passion_and_depth", 14, evidence)
        _bump_rank(conflict_styles, "control_and_loyalty_tests", 10, evidence)
        _bump_rank(risk_flags, "fear_of_vulnerability", 12, evidence)
    if _sign_in(moon, {"Cancer", "Scorpio", "Pisces"}) or _house_in(moon, {12}):
        evidence = _format_position_evidence(moon)
        _bump_rank(attachment_styles, "soft_private_bonding", 18, evidence)
        _bump_rank(partnership_needs_candidates, "safety_time_privacy", 16, evidence)
        _bump_rank(conflict_styles, "silent_accumulation_then_surge", 14, evidence)
        _bump_rank(risk_flags, "distance_instead_of_request", 12, evidence)
    if _house_in(saturn, {7, 8, 10}) or _sign_in(saturn, {"Capricorn", "Aquarius"}):
        evidence = _format_position_evidence(saturn)
        _bump_rank(attachment_styles, "steady_tested_commitment", 12, evidence)
        _bump_rank(partnership_needs_candidates, "shared_future_and_work", 10, evidence)
        _bump_rank(conflict_styles, "direct_and_principled", 10, evidence)
        _bump_rank(risk_flags, "fear_of_vulnerability", 8, evidence)
    if house5:
        _bump_rank(attachment_styles, "soft_private_bonding", 6, _format_house_snapshot(house5))
    if house7:
        evidence = _format_house_snapshot(house7)
        _bump_rank(partnership_needs_candidates, "shared_future_and_work", 6, evidence)
        _bump_rank(partnership_needs_candidates, "friendship_clarity_loyalty", 6, evidence)
    if house8:
        evidence = _format_house_snapshot(house8)
        _bump_rank(partnership_needs_candidates, "passion_and_depth", 10, evidence)
        _bump_rank(risk_flags, "fear_of_vulnerability", 6, evidence)
    if venus_mars and _is_harmonious(venus_mars):
        evidence = _format_aspect_evidence(venus_mars)
        _bump_rank(attachment_styles, "freedom_then_depth", 8, evidence)
        _bump_rank(partnership_needs_candidates, "friendship_clarity_loyalty", 6, evidence)
        _bump_rank(partnership_needs_candidates, "passion_and_depth", 6, evidence)
    if moon_uranus:
        evidence = _format_aspect_evidence(moon_uranus)
        _bump_rank(conflict_styles, "detach_then_recalibrate", 8, evidence)
        _bump_rank(risk_flags, "hot_cold_pattern", 12, evidence)
    if sun_neptune:
        evidence = _format_aspect_evidence(sun_neptune)
        _bump_rank(attachment_styles, "idealized_merge", 12, evidence)
        _bump_rank(risk_flags, "idealization_then_disappointment", 16, evidence)
    if venus and venus.get("r"):
        evidence = _format_position_evidence(venus)
        _bump_rank(risk_flags, "distance_instead_of_request", 10, evidence)
        _bump_rank(risk_flags, "hot_cold_pattern", 8, evidence)

    attachment_style = _pick_primary_ranked(
        attachment_styles,
        fallback_key="soft_private_bonding",
        fallback_label="чувства раскрываются мягко: через безопасность, приватность и неспешность",
        fallback_evidence=[
            _format_position_evidence(venus),
            _format_position_evidence(moon),
        ],
    )
    partnership_needs = _pick_primary_ranked(
        partnership_needs_candidates,
        fallback_key="friendship_clarity_loyalty",
        fallback_label="нужны дружеская база, честный разговор и лояльность без игр",
        fallback_evidence=[
            _format_house_snapshot(house7),
            _format_position_evidence(venus),
        ],
    )
    needs_map = {
        "friendship_clarity_loyalty": ["дружеская база", "честный разговор", "лояльность без игр"],
        "safety_time_privacy": ["бережный темп", "эмоциональная безопасность", "право на тишину"],
        "shared_future_and_work": ["общая цель", "уважение к амбиции", "надежность"],
        "passion_and_depth": ["сексуальная честность", "глубина", "доверие в уязвимости"],
    }
    partnership_needs["needs"] = needs_map.get(partnership_needs.get("key"), [])[:3]

    conflict_style = _pick_primary_ranked(
        conflict_styles,
        fallback_key="direct_and_principled",
        fallback_label="конфликтный стиль: говорить прямо, но на принципах и высоком стандарте",
        fallback_evidence=[
            _format_position_evidence(mars),
            _format_position_evidence(saturn),
        ],
    )
    intimacy_risk_flags = _finalize_ranked(risk_flags, limit=3)

    attachment_key = attachment_style.get("key", "")
    needs_key = partnership_needs.get("key", "")
    conflict_key = conflict_style.get("key", "")
    top_intimacy_risk = intimacy_risk_flags[0] if intimacy_risk_flags else {}
    risk_key = top_intimacy_risk.get("key", "")

    relationship_manifestation_map = {
        "freedom_then_depth": [
            "притяжение чаще начинается с ощущения воздуха, дружбы, интеллектуального контакта или ощущения, что рядом можно быть собой",
            "по-настоящему важно не поверхностное общение, а момент, когда за свободой появляется настоящая глубина и доверие",
            "если свобода и глубина не согласованы, включается сценарий то вместе, то на расстоянии",
        ],
        "soft_private_bonding": [
            "любовь раскрывается не под давлением, а в тихой приватной атмосфере, где можно не спешить",
            "близость становится настоящей там, где есть эмоциональная безопасность и право не объяснять всё мгновенно",
            "при перегрузе отношениям вредят не конфликты сами по себе, а накопленное молчание",
        ],
        "steady_tested_commitment": [
            "любовь читается через надёжность, выдержку и уважение к времени, а не только через вспышку",
            "привязанность крепнет, когда другой выдерживает дистанцию, сроки и реальные обязательства",
            "если зрелые рамки путаются с холодом, близость начинает идти через проверки на прочность",
        ],
        "idealized_merge": [
            "отношения легко поднимаются до уровня большого образа, фантазии и сильного притяжения",
            "любовь особенно цепляет, когда кажется, что найдено идеальное совпадение по смыслу или спасению",
            "главный риск — заметить реального человека слишком поздно, уже после эмоционального вложения",
        ],
    }
    triggers_map = {
        "distance_instead_of_request": ["неясные договорённости", "ощущение, что надо просить слишком много", "эмоциональная небезопасность"],
        "hot_cold_pattern": ["слишком быстрый темп", "страх потерять свободу", "ощущение, что связь стала слишком обязательной"],
        "idealization_then_disappointment": ["сильная химия без проверки реальности", "слияние на раннем этапе", "обещания без опоры на поступки"],
        "fear_of_vulnerability": ["слишком глубокая близость", "тема доверия, секса или зависимости", "необходимость показать слабое место"],
    }
    sabotage_map = {
        "distance_instead_of_request": "самосаботаж в любви идёт через молчание и дистанцию вместо прямой просьбы о нужном",
        "hot_cold_pattern": "самосаботаж идёт через качели приближения и отдаления, когда связь уже важна, но ещё страшно закрепить её формой",
        "idealization_then_disappointment": "самосаботаж идёт через быстрое наделение связи слишком большим смыслом до реальной проверки её качества",
        "fear_of_vulnerability": "самосаботаж идёт через контроль, проверку партнёра или удержание глубины на пороге, не давая ей стать взаимной",
    }
    compensation_map = {
        "distance_instead_of_request": "компенсация выглядит как образ самостоятельного человека, которому якобы ничего не нужно",
        "hot_cold_pattern": "компенсация выглядит как рационализация: сначала приблизиться, потом резко охладить всё ради чувства контроля",
        "idealization_then_disappointment": "компенсация выглядит как вера, что сама химия и сильное чувство решат то, что ещё не подтверждено поступками",
        "fear_of_vulnerability": "компенсация выглядит как проверки на верность, силу и устойчивость вместо прямого доверия",
    }
    action_map = {
        "freedom_then_depth": "лучший режим любви — сначала договариваться о воздухе и границах, а потом уже углублять связь",
        "soft_private_bonding": "лучший режим любви — медленный темп, приватность и ясное право на бережную паузу без наказания",
        "steady_tested_commitment": "лучший режим любви — выдерживать ритм, слово и поступок, не заменяя это сухой дистанцией",
        "idealized_merge": "лучший режим любви — держать чувство и реальность рядом: проверять образ поступками и временем",
    }

    relationship_manifestations = [
        {
            "phase": "attraction",
            "label": relationship_manifestation_map.get(attachment_key, [attachment_style.get("label", "")])[0],
            "evidence": attachment_style.get("evidence", [])[:3],
        },
        {
            "phase": "bonding",
            "label": relationship_manifestation_map.get(attachment_key, ["", partnership_needs.get("label", "")])[1],
            "evidence": partnership_needs.get("evidence", [])[:3],
        },
        {
            "phase": "stress",
            "label": relationship_manifestation_map.get(attachment_key, ["", "", conflict_style.get("label", "")])[2],
            "evidence": [
                *(conflict_style.get("evidence", [])[:2]),
                *(top_intimacy_risk.get("evidence", [])[:2]),
            ][:4],
        },
    ]
    relationship_triggers = {
        "key": f"{risk_key}_triggers",
        "items": triggers_map.get(risk_key, []),
        "evidence": top_intimacy_risk.get("evidence", [])[:4],
    }
    self_sabotage_pattern = {
        "key": f"{risk_key}_self_sabotage",
        "label": sabotage_map.get(risk_key, top_intimacy_risk.get("label", "")),
        "evidence": top_intimacy_risk.get("evidence", [])[:4],
    }
    compensation_pattern = {
        "key": f"{risk_key}_compensation",
        "label": compensation_map.get(risk_key, conflict_style.get("label", "")),
        "evidence": [
            *(conflict_style.get("evidence", [])[:2]),
            *(top_intimacy_risk.get("evidence", [])[:2]),
        ][:4],
    }
    what_to_do = {
        "items": [
            action_map.get(attachment_key, attachment_style.get("label", "")),
            f"прямо обозначать потребность в {', '.join(partnership_needs.get('needs', [])[:2])}" if partnership_needs.get("needs") else partnership_needs.get("label", ""),
            "замечать триггер раньше, чем он превратится в дистанцию, проверку или резкое охлаждение",
        ][:4],
        "evidence": [
            *(attachment_style.get("evidence", [])[:2]),
            *(partnership_needs.get("evidence", [])[:2]),
        ][:4],
    }
    what_not_to_do = {
        "items": [
            "не требовать глубины без оговорённых границ и темпа",
            "не путать самозащиту с зрелой дистанцией",
            "не принимать химию за гарантию совместимости без проверки реальностью",
        ],
        "evidence": top_intimacy_risk.get("evidence", [])[:3],
    }
    best_mode_of_action = {
        "key": f"{attachment_key or 'attachment'}_best_mode",
        "label": action_map.get(attachment_key, attachment_style.get("label", "")),
        "evidence": [
            *(attachment_style.get("evidence", [])[:2]),
            *(partnership_needs.get("evidence", [])[:2]),
        ][:4],
    }
    scene_seeds = [
        {
            "title": "сцена сближения",
            "seed": relationship_manifestation_map.get(attachment_key, [attachment_style.get("label", "")])[0],
        },
        {
            "title": "сцена конфликта",
            "seed": (
                f"{conflict_style.get('label')}; риск сверху обычно включается через {', '.join(triggers_map.get(risk_key, [])[:2])}"
            ),
        },
    ]

    return {
        "version": "natal_v2_p0",
        "attachment_style": attachment_style,
        "partnership_needs": partnership_needs,
        "conflict_style": conflict_style,
        "intimacy_risk_flags": intimacy_risk_flags,
        "relationship_manifestations": relationship_manifestations,
        "relationship_triggers": relationship_triggers,
        "self_sabotage_pattern": self_sabotage_pattern,
        "compensation_pattern": compensation_pattern,
        "what_to_do": what_to_do,
        "what_not_to_do": what_not_to_do,
        "best_mode_of_action": best_mode_of_action,
        "scene_seeds": scene_seeds,
        "cross_links": [
            "executive_summary.relationship_theme",
            "synthesis.core_conflict",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }
# END_BLOCK: INSIGHT_RELATIONSHIP_PACKS
