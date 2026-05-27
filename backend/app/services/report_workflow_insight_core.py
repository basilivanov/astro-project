# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-CORE
# purpose: Provide natal section rules, constants, and compact chart-pack helpers for insight builders.
# inputs: serialized chart dictionaries and section rule identifiers.
# outputs: compact position, house, aspect, balance, and chart-pack dictionaries.
# invariants: fact selection and naming aliases remain identical to the legacy report workflow implementation.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-INSIGHT-CORE

# START_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-CORE
# entrypoints:
#   - _build_section_chart_pack -> SECTION_CHART_PACK
#   - _build_position_lookup / _build_house_lookup -> FACT_LOOKUPS
#   - NATAL_SECTION_CONTEXT_RULES -> SECTION_RULES
# END_MODULE_MAP: M-REPORT-WORKFLOW-INSIGHT-CORE

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from .report_workflow_content_fallback import (
    _clean_sentence,
    _collect_fact_anchor_evidence,
    _compose_fact_first_fragment,
    _extract_named_anchor,
    _format_insight_value,
    _normalize_executive_fragment,
)
from .report_workflow_forecast import RU_ASPECTS, RU_PLANET_NAMES, RU_SIGNS_PLAIN

# START_BLOCK: INSIGHT_CORE_CONSTANTS
SIGN_ELEMENT_MAP = {
    "Aries": "Fire",
    "Taurus": "Earth",
    "Gemini": "Air",
    "Cancer": "Water",
    "Leo": "Fire",
    "Virgo": "Earth",
    "Libra": "Air",
    "Scorpio": "Water",
    "Sagittarius": "Fire",
    "Capricorn": "Earth",
    "Aquarius": "Air",
    "Pisces": "Water",
}

SIGN_MODE_MAP = {
    "Aries": "Cardinal",
    "Taurus": "Fixed",
    "Gemini": "Mutable",
    "Cancer": "Cardinal",
    "Leo": "Fixed",
    "Virgo": "Mutable",
    "Libra": "Cardinal",
    "Scorpio": "Fixed",
    "Sagittarius": "Mutable",
    "Capricorn": "Cardinal",
    "Aquarius": "Fixed",
    "Pisces": "Mutable",
}

SIGN_RULER_MAP = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Pluto",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Uranus",
    "Pisces": "Neptune",
}

POINT_NAME_ALIASES = {
    "Mean Apogee": "Lilith",
}

FACTS_FIRST_P0_SECTION_IDS = {
    "executive_summary",
    "synthesis",
    "money_realization",
    "love_intimacy",
    "final_synthesis",
}

FACTS_FIRST_P1_SECTION_IDS = {
    "dispositor_office",
    "balance_wheel_1_6",
    "balance_wheel_7_12",
    "time_cycles",
}

FACTS_FIRST_P2_SECTION_IDS = {
    "axes_truths",
    "aspects_beginner",
    "nodes_growth",
    "mercury_mind",
    "shadow_trauma",
}

FACTS_FIRST_P3_SECTION_IDS = {
    "core_triad",
    "configurations_geometry",
    "vertex_fate",
    "stars_transuranus",
}

FACTS_FIRST_P4_SECTION_IDS = {
    "framework_elements_modes",
}

FACTS_FIRST_INSIGHT_PACK_SECTION_IDS = (
    FACTS_FIRST_P0_SECTION_IDS
    | FACTS_FIRST_P1_SECTION_IDS
    | FACTS_FIRST_P2_SECTION_IDS
    | FACTS_FIRST_P3_SECTION_IDS
    | FACTS_FIRST_P4_SECTION_IDS
)

MAJOR_DISPOSITOR_PLANETS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]

HOUSE_DOMAIN_MAP = {
    1: "личная подача, тело и способ входить в мир",
    2: "деньги, ценность и чувство опоры",
    3: "мышление, речь, обучение и ближний круг",
    4: "дом, корни и внутренняя база",
    5: "радость, романтика, творчество и самовыражение",
    6: "ритм, работа, здоровье и повседневная дисциплина",
    7: "партнерство, зеркало и контракты",
    8: "близость, кризисы, общие ресурсы и контроль",
    9: "смысл, вера, горизонт и большие маршруты",
    10: "статус, карьера и видимая роль",
    11: "сообщества, связи, друзья и долгие цели",
    12: "тишина, завершения, восстановление и бессознательное",
}

SIGN_STYLE_HINTS = {
    "Aries": {
        "tone": "прямой старт, скорость и право действовать первым",
        "plus": "инициатива, смелость и быстрый запуск",
        "minus": "импульсивность, напор и жизнь в режиме атаки",
        "growth": "сочетать скорость с выдержкой и экологичной силой",
    },
    "Taurus": {
        "tone": "устойчивость, материальная база и телесная опора",
        "plus": "надежность, терпение и умение удерживать ресурс",
        "minus": "инерция, застревание и страх менять привычное",
        "growth": "сохранять опору, не превращая ее в застой",
    },
    "Gemini": {
        "tone": "подвижность, обмен, обучение и множество связей",
        "plus": "гибкость, контактность и быстрый сбор информации",
        "minus": "распыление, шум и недоведенные решения",
        "growth": "собирать разнообразие в ясную мысль и маршрут",
    },
    "Cancer": {
        "tone": "чувствительность, защита, память и создание базы",
        "plus": "забота, интуиция и умение удерживать близких",
        "minus": "обидчивость, закрытость и зависание в прошлом",
        "growth": "строить безопасность без изоляции и гиперконтроля",
    },
    "Leo": {
        "tone": "видимость, творческое ядро и потребность светить",
        "plus": "щедрость, харизма и здоровая уверенность",
        "minus": "драма, самолюбие и болезненная реакция на непризнание",
        "growth": "нести свет без театрального перегрева и гордыни",
    },
    "Virgo": {
        "tone": "точность, сервис, настройка процесса и полезность",
        "plus": "системность, внимательность и качество",
        "minus": "перфекционизм, тревога и вечное исправление",
        "growth": "оставлять высокую планку, не превращая ее в самокритику",
    },
    "Libra": {
        "tone": "баланс, диалог, партнерство и поиск формы",
        "plus": "дипломатия, чувство меры и способность договориться",
        "minus": "зависание в выборе и зависимость от внешнего согласия",
        "growth": "сохранять баланс, не теряя собственный вектор",
    },
    "Scorpio": {
        "tone": "глубина, контроль, кризисы и трансформация",
        "plus": "сила, стойкость и умение идти в сложное",
        "minus": "подозрительность, крайности и борьба за власть",
        "growth": "нести глубину без тотального контроля и войн",
    },
    "Sagittarius": {
        "tone": "горизонт, риск, вера и движение вперед",
        "plus": "широта взгляда, оптимизм и смелость маршрута",
        "minus": "избыточная уверенность, разгон и уход от конкретики",
        "growth": "держать горизонт, не теряя точность шага",
    },
    "Capricorn": {
        "tone": "структура, ответственность и длинный подъем",
        "plus": "дисциплина, выносливость и управленческий каркас",
        "minus": "жесткость, холодность и жизнь под внутренним прессом",
        "growth": "сохранять взрослость без самоцементирования",
    },
    "Aquarius": {
        "tone": "свобода, сеть, обновление и собственные правила",
        "plus": "оригинальность, независимость и работа с будущим",
        "minus": "отстраненность, резкие развороты и протест ради протеста",
        "growth": "давать себе свободу без эмоционального выключения",
    },
    "Pisces": {
        "tone": "проницаемость, воображение, сострадание и растворение границ",
        "plus": "эмпатия, образность и тонкое считывание атмосферы",
        "minus": "размытость, бегство и слабые контуры реальности",
        "growth": "оставлять глубину, но укреплять границы и форму",
    },
}

PLANET_ROLE_HINTS = {
    "Sun": "воля и видимость",
    "Moon": "эмоции и базовые потребности",
    "Mercury": "мысль и коммуникация",
    "Venus": "симпатия, ценность и выбор",
    "Mars": "энергия, конфликт и действие",
    "Jupiter": "рост и возможности",
    "Saturn": "долг, рамка и зрелость",
    "Uranus": "свобода и резкие обновления",
    "Neptune": "идеал, тонкость и размывание",
    "Pluto": "контроль, кризис и глубинная сила",
    "Chiron": "уязвимость и настройка",
    "North Node": "вектор роста",
    "True Node": "вектор роста",
    "South Node": "привычный сценарий",
    "ASC": "личный способ входа",
    "MC": "видимая роль и статус",
}



NATAL_SECTION_CONTEXT_RULES: Dict[str, Dict[str, Any]] = {
    "executive_summary": {
        "focus": "Краткая выжимка по сильным сторонам, рискам, отношениям и деньгам.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC", "North Node", "Chiron"],
        "houses": [1, 2, 5, 6, 7, 8, 10],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
        "aspect_limit": 8,
        "include_balance": True,
        "include_patterns": True,
    },
    "synthesis": {
        "focus": "Образ карты, ядро личности и центральный внутренний конфликт.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
        "houses": [1, 4, 7, 10],
        "aspect_points": ["Sun", "Moon", "ASC", "MC", "Mercury", "Venus", "Mars"],
        "aspect_limit": 8,
        "include_balance": True,
        "include_patterns": True,
    },
    "framework_elements_modes": {
        "focus": "Баланс стихий и модальностей без лишних деталей карты.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"],
        "aspect_limit": 4,
        "include_balance": True,
    },
    "axes_truths": {
        "focus": "Главные оси карты: ASC/DSC и IC/MC.",
        "positions": ["ASC", "DSC", "IC", "MC", "Sun", "Moon"],
        "houses": [1, 4, 7, 10],
        "aspect_points": ["ASC", "DSC", "IC", "MC", "Sun", "Moon"],
        "aspect_limit": 6,
    },
    "aspects_beginner": {
        "focus": "Только самые важные и точные аспекты.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"],
        "aspect_limit": 8,
    },
    "configurations_geometry": {
        "focus": "Фигуры и конфигурации карты.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"],
        "aspect_limit": 8,
        "include_patterns": True,
    },
    "dispositor_office": {
        "focus": "Иерархия управления планетами и центры принятия решений.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"],
        "aspect_limit": 6,
        "include_balance": True,
    },
    "core_triad": {
        "focus": "ASC, Солнце и Луна как личное ядро.",
        "positions": ["ASC", "Sun", "Moon", "Mercury"],
        "houses": [1, 4, 10],
        "aspect_points": ["ASC", "Sun", "Moon", "Mercury"],
        "aspect_limit": 6,
    },
    "mercury_mind": {
        "focus": "Как человек думает, говорит и обрабатывает информацию.",
        "positions": ["Mercury", "Moon", "Saturn", "Uranus"],
        "aspect_points": ["Mercury", "Moon", "Saturn", "Uranus"],
        "aspect_limit": 6,
    },
    "shadow_trauma": {
        "focus": "Теневая зона через Хирон, Лилит и напряженные связки.",
        "positions": ["Chiron", "Lilith", "Moon", "Saturn", "Pluto"],
        "aspect_points": ["Chiron", "Lilith", "Moon", "Saturn", "Pluto"],
        "aspect_limit": 6,
    },
    "nodes_growth": {
        "focus": "Ось роста и привычный сценарий через лунные узлы.",
        "positions": ["North Node", "True Node", "South Node", "Sun", "Moon", "Saturn"],
        "aspect_points": ["North Node", "True Node", "South Node", "Sun", "Moon", "Saturn"],
        "aspect_limit": 6,
    },
    "vertex_fate": {
        "focus": "Сюжетные встречи, Вертекс и связанная динамика отношений.",
        "positions": ["Vertex", "Venus", "Mars", "Moon", "DSC"],
        "houses": [5, 7, 8],
        "aspect_points": ["Vertex", "Venus", "Mars", "Moon"],
        "aspect_limit": 6,
    },
    "balance_wheel_1_6": {
        "focus": "Дома 1-6, их темы, управители и триггеры.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
        "houses": [1, 2, 3, 4, 5, 6],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
        "aspect_limit": 8,
    },
    "balance_wheel_7_12": {
        "focus": "Дома 7-12, их темы, управители и триггеры.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
        "houses": [7, 8, 9, 10, 11, 12],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "MC"],
        "aspect_limit": 8,
    },
    "love_intimacy": {
        "focus": "Любовный стиль, близость и сексуальная динамика.",
        "positions": ["Venus", "Mars", "Moon", "Sun", "Saturn"],
        "houses": [5, 7, 8],
        "aspect_points": ["Venus", "Mars", "Moon", "Sun", "Saturn"],
        "aspect_limit": 6,
    },
    "money_realization": {
        "focus": "Деньги, работа и реализация через дома 2/6/10 и Юпитер/Сатурн.",
        "positions": ["Jupiter", "Saturn", "Venus", "Mars", "Sun", "ASC", "MC"],
        "houses": [2, 6, 10],
        "aspect_points": ["Jupiter", "Saturn", "Venus", "Mars", "Sun", "MC"],
        "aspect_limit": 6,
    },
    "stars_transuranus": {
        "focus": "Высшие планеты и долгие смысловые линии карты.",
        "positions": ["Uranus", "Neptune", "Pluto", "Sun", "Moon", "Saturn"],
        "aspect_points": ["Uranus", "Neptune", "Pluto", "Sun", "Moon", "Saturn"],
        "aspect_limit": 6,
    },
    "time_cycles": {
        "focus": "Текущий жизненный период и циклы взросления.",
        "positions": ["Sun", "Moon", "Saturn", "Jupiter", "North Node", "ASC", "MC"],
        "houses": [1, 10],
        "aspect_points": ["Sun", "Moon", "Saturn", "Jupiter", "North Node"],
        "aspect_limit": 6,
    },
    "final_synthesis": {
        "focus": "Финальный девиз и главный совет по всей карте.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC", "North Node"],
        "houses": [1, 2, 5, 6, 7, 8, 10],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
        "aspect_limit": 8,
        "include_balance": True,
        "include_patterns": True,
    },
}

DEFAULT_NATAL_SECTION_CONTEXT_RULE: Dict[str, Any] = {
    "focus": "Ключевые факты карты для этого раздела.",
    "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
    "houses": [1, 4, 7, 10],
    "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
    "aspect_limit": 6,
    "include_balance": True,
}


def _unique_preserve_order(values: List[Any]) -> List[Any]:
    result: List[Any] = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize_point_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    return POINT_NAME_ALIASES.get(name, name)


def _compact_position_fact(position: dict) -> dict:
    name = _normalize_point_name(position.get("key") or position.get("p") or position.get("name"))
    degree = position.get("deg")
    if degree is None:
        degree = position.get("sign_degree")
    try:
        degree = int(float(degree))
    except (TypeError, ValueError):
        degree = 0
    return {
        "p": name,
        "s": position.get("s") or position.get("sign"),
        "deg": degree,
        "h": position.get("h", position.get("house")),
        "r": bool(position.get("r", position.get("is_retrograde", False))),
    }


def _compact_house_fact(house: dict) -> dict:
    degree = house.get("deg")
    if degree is None:
        degree = house.get("sign_degree")
    try:
        degree = int(float(degree))
    except (TypeError, ValueError):
        degree = 0
    return {
        "h": house.get("h", house.get("house")),
        "s": house.get("s", house.get("sign")),
        "deg": degree,
    }


def _compact_aspect_fact(aspect: dict) -> dict:
    orb = aspect.get("o")
    if orb is None:
        orb = aspect.get("orb")
    try:
        orb = round(float(orb), 1)
    except (TypeError, ValueError):
        orb = 0.0
    return {
        "p1": _normalize_point_name(aspect.get("p1_key") or aspect.get("p1")),
        "t": aspect.get("t", aspect.get("type")),
        "p2": _normalize_point_name(aspect.get("p2_key") or aspect.get("p2")),
        "o": orb,
    }


def _build_position_lookup(facts: dict, chart_data: dict) -> Dict[str, dict]:
    lookup: Dict[str, dict] = {}
    for position in facts.get("pos", []):
        compact = _compact_position_fact(position)
        name = compact.get("p")
        if name:
            lookup[name] = compact
    for position in chart_data.get("positions", []):
        compact = _compact_position_fact(position)
        name = compact.get("p")
        if name and name not in lookup:
            lookup[name] = compact
    return lookup


def _build_house_lookup(facts: dict, chart_data: dict) -> Dict[int, dict]:
    lookup: Dict[int, dict] = {}
    for house in facts.get("houses", []):
        compact = _compact_house_fact(house)
        house_id = compact.get("h")
        if isinstance(house_id, int):
            lookup[house_id] = compact
    for house in chart_data.get("houses", []):
        compact = _compact_house_fact(house)
        house_id = compact.get("h")
        if isinstance(house_id, int) and house_id not in lookup:
            lookup[house_id] = compact
    return lookup


def _collect_section_aspects(chart_data: dict, point_names: List[str], limit: int) -> List[dict]:
    aspect_points = {_normalize_point_name(name) for name in (point_names or [])}
    items: List[dict] = []
    for aspect in chart_data.get("aspects", []):
        p1 = _normalize_point_name(aspect.get("p1_key") or aspect.get("p1"))
        p2 = _normalize_point_name(aspect.get("p2_key") or aspect.get("p2"))
        if aspect_points and p1 not in aspect_points and p2 not in aspect_points:
            continue
        items.append(_compact_aspect_fact(aspect))
    items.sort(key=lambda aspect: aspect.get("o", 99.0))
    return items[:limit] if limit else items


def _collect_section_patterns(chart_data: dict, point_names: List[str]) -> List[dict]:
    point_set = {_normalize_point_name(name) for name in (point_names or [])}
    patterns: List[dict] = []
    for pattern in chart_data.get("patterns", []):
        points = [
            _normalize_point_name(point)
            for point in (pattern.get("point_keys") or pattern.get("points", []))
        ]
        if point_set and not any(point in point_set for point in points):
            continue
        patterns.append({
            "type": pattern.get("type"),
            "points": points,
        })
    return patterns


def _build_section_chart_pack(rule: dict, chart_data: dict) -> dict:
    position_names = _unique_preserve_order(rule.get("positions", []))
    house_numbers = _unique_preserve_order(rule.get("houses", []))
    aspect_points = _unique_preserve_order(rule.get("aspect_points", position_names))
    aspect_limit = int(rule.get("aspect_limit", 0) or 0)

    positions = []
    for position in chart_data.get("positions", []):
        normalized_name = _normalize_point_name(position.get("key") or position.get("name"))
        if position_names and normalized_name not in position_names:
            continue
        normalized_position = copy.deepcopy(position)
        if normalized_name:
            normalized_position["name"] = normalized_name
        positions.append(normalized_position)

    houses = []
    for house in chart_data.get("houses", []):
        if house_numbers and house.get("house") not in house_numbers:
            continue
        houses.append(copy.deepcopy(house))

    chart_pack: Dict[str, Any] = {
        "house_system": chart_data.get("house_system"),
        "datetime_utc": chart_data.get("datetime_utc"),
        "datetime_local": chart_data.get("datetime_local"),
        "location": copy.deepcopy(chart_data.get("location", {})),
    }
    if positions:
        chart_pack["positions"] = positions
    if houses:
        chart_pack["houses"] = houses

    aspects = _collect_section_aspects(chart_data, aspect_points, aspect_limit)
    if aspects:
        chart_pack["aspects"] = aspects

    if rule.get("include_patterns"):
        patterns = _collect_section_patterns(chart_data, position_names)
        if patterns:
            chart_pack["patterns"] = patterns

    if rule.get("include_balance") and chart_data.get("balances"):
        chart_pack["balances"] = copy.deepcopy(chart_data.get("balances"))

    return chart_pack


def _score_to_int(value: Any, fallback: int = 50) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = fallback
    return max(0, min(100, score))


def _append_unique(items: List[str], *values: Optional[str]) -> None:
    for value in values:
        if value and value not in items:
            items.append(value)


def _new_rank_item(key: str, label: str) -> Dict[str, Any]:
    return {"key": key, "label": label, "score": 0, "evidence": []}


def _bump_rank(
    bucket: Dict[str, Dict[str, Any]],
    key: str,
    delta: int,
    *evidence: Optional[str],
) -> None:
    item = bucket[key]
    item["score"] += delta
    _append_unique(item["evidence"], *evidence)


def _finalize_ranked(
    bucket: Dict[str, Dict[str, Any]],
    *,
    limit: int,
) -> List[Dict[str, Any]]:
    ranked = sorted(
        bucket.values(),
        key=lambda item: (item.get("score", 0), len(item.get("evidence", []))),
        reverse=True,
    )
    selected = ranked[:limit]
    for item in selected:
        item["score"] = _score_to_int(item.get("score", 0), fallback=0)
        item["evidence"] = item.get("evidence", [])[:4]
    return selected


def _pick_primary_ranked(
    bucket: Dict[str, Dict[str, Any]],
    *,
    fallback_key: str,
    fallback_label: str,
    fallback_evidence: Optional[List[str]] = None,
) -> Dict[str, Any]:
    ranked = _finalize_ranked(bucket, limit=1)
    if ranked and ranked[0].get("score", 0) > 0:
        return ranked[0]
    evidence: List[str] = []
    _append_unique(evidence, *(fallback_evidence or []))
    return {
        "key": fallback_key,
        "label": fallback_label,
        "score": 50,
        "evidence": evidence[:4],
    }


def _get_balance_snapshot(facts: dict, chart_data: dict) -> dict:
    return copy.deepcopy(facts.get("balance") or chart_data.get("balances") or {})


def _balance_value(balance: dict, family: str, key: str) -> int:
    return _score_to_int((balance.get(family) or {}).get(key, 0), fallback=0)


def _format_balance_evidence(balance: dict, family: str, key: str) -> Optional[str]:
    value = (balance.get(family) or {}).get(key)
    if value is None:
        return None
    ru_family = "стихия" if family == "elements" else "модальность"
    ru_key_map = {
        "Fire": "Огонь",
        "Earth": "Земля",
        "Air": "Воздух",
        "Water": "Вода",
        "Cardinal": "Кардинальность",
        "Fixed": "Фиксированность",
        "Mutable": "Мутабельность",
    }
    ru_key = ru_key_map.get(key, key)
    return f"{ru_family}: {ru_key} {value}%"


def _rank_balance_family(balance: dict, family: str, keys: List[str]) -> List[Dict[str, Any]]:
    ranked = []
    for key in keys:
        ranked.append(
            {
                "key": key,
                "score": _balance_value(balance, family, key),
                "evidence": [_format_balance_evidence(balance, family, key)],
            }
        )
    ranked.sort(key=lambda item: item.get("score", 0), reverse=True)
    return ranked


def _format_position_evidence(position: Optional[dict]) -> Optional[str]:
    if not position:
        return None
    name = position.get("key") or position.get("p") or position.get("name")
    sign = position.get("s") or position.get("sign")
    house = position.get("h", position.get("house"))
    retro = bool(position.get("r", position.get("is_retrograde", False)))
    parts = [RU_PLANET_NAMES.get(name, name or "Точка")]
    if sign:
        parts.append(f"в {RU_SIGNS_PLAIN.get(sign, sign)}")
    if house:
        parts.append(f"дом {house}")
    if retro:
        parts.append("ретро")
    return ", ".join(parts)


def _format_aspect_evidence(aspect: Optional[dict]) -> Optional[str]:
    if not aspect:
        return None
    p1_key = _normalize_point_name(aspect.get("p1_key") or aspect.get("p1"))
    p2_key = _normalize_point_name(aspect.get("p2_key") or aspect.get("p2"))
    p1 = RU_PLANET_NAMES.get(p1_key, p1_key or "")
    p2 = RU_PLANET_NAMES.get(p2_key, p2_key or "")
    aspect_type = RU_ASPECTS.get(aspect.get("t"), aspect.get("t") or "аспект")
    orb = aspect.get("o")
    orb_text = f" ({orb}°)" if orb is not None else ""
    return f"{p1} {aspect_type} {p2}{orb_text}"


def _get_point(position_lookup: Dict[str, dict], *names: str) -> Optional[dict]:
    for name in names:
        if name in position_lookup:
            return position_lookup[name]
    return None


def _find_aspect(chart_data: dict, first: str, second: str) -> Optional[dict]:
    first = _normalize_point_name(first)
    second = _normalize_point_name(second)
    for aspect in chart_data.get("aspects", []):
        points = {
            _normalize_point_name(aspect.get("p1_key") or aspect.get("p1")),
            _normalize_point_name(aspect.get("p2_key") or aspect.get("p2")),
        }
        if {first, second} == points:
            return _compact_aspect_fact(aspect)
    return None


def _is_harmonious(aspect: Optional[dict]) -> bool:
    return bool(aspect and aspect.get("t") in {"trine", "sextile"})


def _is_tense(aspect: Optional[dict]) -> bool:
    return bool(aspect and aspect.get("t") in {"square", "opposition"})


def _sign_in(position: Optional[dict], signs: set[str]) -> bool:
    return bool(position and position.get("s") in signs)


def _house_in(position: Optional[dict], houses: set[int]) -> bool:
    house = position.get("h") if position else None
    return isinstance(house, int) and house in houses


def _count_points_in_houses(
    position_lookup: Dict[str, dict],
    houses: set[int],
    point_names: Optional[List[str]] = None,
) -> int:
    names = point_names or list(position_lookup.keys())
    total = 0
    for name in names:
        position = position_lookup.get(name)
        if _house_in(position, houses):
            total += 1
    return total


def _build_house_snapshot(
    house_lookup: Dict[int, dict],
    position_lookup: Dict[str, dict],
    house_number: int,
) -> Optional[Dict[str, Any]]:
    house = house_lookup.get(house_number)
    if not house:
        return None
    sign = house.get("s")
    ruler = SIGN_RULER_MAP.get(sign)
    ruler_position = position_lookup.get(ruler) if ruler else None
    return {
        "house": house_number,
        "sign": sign,
        "ruler": ruler,
        "ruler_position": ruler_position,
    }


def _format_house_snapshot(snapshot: Optional[dict]) -> Optional[str]:
    if not snapshot:
        return None
    sign = RU_SIGNS_PLAIN.get(snapshot.get("sign"), snapshot.get("sign") or "?")
    ruler = RU_PLANET_NAMES.get(snapshot.get("ruler"), snapshot.get("ruler") or "?")
    ruler_position = snapshot.get("ruler_position") or {}
    if ruler_position:
        ruler_sign = RU_SIGNS_PLAIN.get(ruler_position.get("s"), ruler_position.get("s") or "?")
        ruler_house = ruler_position.get("h")
        return (
            f"{snapshot.get('house')} дом в {sign}, "
            f"управитель {ruler} в {ruler_sign}, дом {ruler_house}"
        )
    return f"{snapshot.get('house')} дом в {sign}, управитель {ruler}"
# END_BLOCK: INSIGHT_CORE_CONSTANTS

__all__ = [name for name in globals() if not name.startswith("__")]
