# ############################################################################
# AI_HEADER: MODULE_FORECAST_SEMANTICS
# ROLE: Build narrow deterministic semantic layers for daily/week/month forecast copy.
# DEPENDENCIES: none (pure semantic helpers over already calculated forecast facts).
# GRACE_ANCHORS: [FORECAST_SEMANTICS]
# ############################################################################

from __future__ import annotations

from typing import Any

SUPPORTIVE_ASPECT_TOKENS = ("тригон", "секстиль")
TENSE_ASPECT_TOKENS = ("квадрат", "оппозиц")

SUPPORTIVE_CONJUNCTION_TRANSITS = {"Venus", "Mercury", "Sun", "Jupiter"}
TENSE_CONJUNCTION_TRANSITS = {"Mars", "Saturn", "Uranus", "Neptune", "Pluto"}

DAILY_SPECIAL_PATTERNS = {
    ("Venus", "Venus", "supportive"): "мягче идут симпатии, спокойные покупки и договоренности о цене",
    ("Venus", "Sun", "supportive"): "личная подача теплеет, а хорошие слова легче находят отклик",
    ("Venus", "Moon", "supportive"): "эмоциональный контакт, бытовая мягкость и чувство вкуса работают в плюс",
    ("Venus", "MC", "supportive"): "рабочие и статусные договоренности проще собирать через вежливость и форму",
    ("Mercury", "Mercury", "supportive"): "проще собрать мысль, договориться о деталях и сшить разрозненные вводные",
    ("Mercury", "Venus", "supportive"): "мягкий разговор помогает и в деньгах, и в личных договоренностях",
    ("Mercury", "MC", "supportive"): "документы, согласования и административные решения идут чище обычного",
    ("Sun", "Sun", "supportive"): "проще держать личный курс и обозначать приоритет без лишних объяснений",
    ("Sun", "MC", "supportive"): "видимость в работе и личный жест дают реальный ход",
    ("Mars", "Sun", "supportive"): "хватает решимости на прямой шаг и защиту главного приоритета",
    ("Mars", "MC", "supportive"): "есть ход на короткое рабочее решение, запуск и решающий разговор",
    ("Mars", "Sun", "tense"): "скорость и самолюбие легко переводят разговор в нажим или спор за право решать",
    ("Mars", "Moon", "tense"): "раздражение быстро пробивает по эмоциям, быту и внутреннему запасу",
    ("Mars", "Mercury", "tense"): "спор рождается не из сути, а из резкой формулировки и спешки",
    ("Mars", "Venus", "tense"): "нажим в деньгах и симпатиях быстро ломает мягкий контакт",
    ("Mars", "ASC", "tense"): "тело и темп быстрее обычного отвечают на перегруз и суету",
    ("Mercury", "Moon", "tense"): "мысли, переписка и эмоции легко начинают дергать друг друга",
    ("Mercury", "Venus", "tense"): "цена слов и цена компромисса становятся щекотливее обычного",
    ("Sun", "Moon", "tense"): "личное желание и эмоциональная реакция спорят за центр дня",
}

TRANSIT_SUPPORTIVE_OPENERS = {
    "Venus": "мягче идут",
    "Mercury": "яснее идут",
    "Sun": "виднее становятся",
    "Mars": "легче двигаются",
    "Jupiter": "шире открываются",
}

TRANSIT_TENSE_OPENERS = {
    "Venus": "щекотливее становятся",
    "Mercury": "спешка быстро путает",
    "Sun": "слишком остро реагируют",
    "Mars": "быстро перегреваются",
    "Jupiter": "размах легко превышает реальную базу в",
}

NATAL_DOMAIN_PHRASES = {
    "Sun": "личные приоритеты и вопрос, кто задает тон",
    "Moon": "эмоции, бытовой ритм и уязвимые реакции",
    "Mercury": "разговоры, формулировки и мелкая координация",
    "Venus": "симпатии, деньги и условия обмена",
    "Mars": "границы, темп и силовые ходы",
    "ASC": "тело, запас сил и личный темп",
    "MC": "работа, статус и административные решения",
}

FOCUS_STEMS = {
    "money_admin": (
        "меркур",
        "документ",
        "соглас",
        "письм",
        "переписк",
        "деньг",
        "покуп",
        "цен",
        "сделк",
        "услов",
        "срок",
        "дедлайн",
        "админ",
        "статус",
        "работ",
        "mc",
    ),
    "relationship": (
        "венер",
        "симпат",
        "отнош",
        "партнер",
        "мягк",
        "контакт",
        "луна",
        "эмоц",
        "близ",
        "разговор",
    ),
    "rest": (
        "тело",
        "пауз",
        "восстанов",
        "перегруз",
        "запас",
        "ритм",
        "void",
        "без курса",
        "луна",
    ),
    "launch": (
        "марс",
        "солнц",
        "запуск",
        "старт",
        "приоритет",
        "ход",
        "дедлайн",
    ),
}

DEFAULT_WEEK_HEADLINES = {
    "RED": "Неделя про сужение фронта и взрослую дисциплину: важнее не разгон, а точный контроль над тем, куда уходит ресурс.",
    "YELLOW": "Неделя про координацию, проверку стыков и спокойную сборку хода вместо нервного ускорения.",
    "GREEN": "Неделя про видимый ход: можно двигать подготовленное и закреплять результат без лишней суеты.",
}

DEFAULT_MONTH_HEADLINES = {
    "RED": "Месяц про пересборку контура: давление есть, но результат приходит через короткий фронт, трезвый расчет и отказ от лишнего геройства.",
    "YELLOW": "Месяц про настройку курса и рабочего ритма: сначала собрать механику, потом уже давать ускорение.",
    "GREEN": "Месяц про сильную ставку и длинный ход: полезно проводить одну главную линию через весь горизонт, а не распыляться.",
}


def _normalize_status(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"RED", "YELLOW", "GREEN"}:
        return normalized
    return "YELLOW"


def _aspect_quality(aspect_type: Any, transit: Any = "") -> str:
    lower = str(aspect_type or "").strip().lower()
    if any(token in lower for token in SUPPORTIVE_ASPECT_TOKENS):
        return "supportive"
    if any(token in lower for token in TENSE_ASPECT_TOKENS):
        return "tense"
    if "соединение" in lower or "conjunction" in lower:
        if str(transit or "") in SUPPORTIVE_CONJUNCTION_TRANSITS:
            return "supportive"
        if str(transit or "") in TENSE_CONJUNCTION_TRANSITS:
            return "tense"
    return "highlight"


def _describe_fast_hit(hit: dict[str, Any]) -> str:
    transit = str(hit.get("transit") or "").strip()
    natal = str(hit.get("natal") or "").strip()
    quality = _aspect_quality(hit.get("type"), transit)

    special = DAILY_SPECIAL_PATTERNS.get((transit, natal, quality))
    if special:
        return special

    if quality == "supportive":
        opener = TRANSIT_SUPPORTIVE_OPENERS.get(transit, "лучше собираются")
    elif quality == "tense":
        opener = TRANSIT_TENSE_OPENERS.get(transit, "легче перегреваются")
    else:
        opener = "подсвечиваются"

    domain = NATAL_DOMAIN_PHRASES.get(natal, "личные решения и повседневный ритм")
    if quality == "tense" and transit == "Jupiter":
        return f"{opener} {domain}"
    return f"{opener} {domain}"


def _collect_focus_scores(*chunks: str) -> dict[str, int]:
    lower = " ".join(str(chunk or "").lower() for chunk in chunks if str(chunk or "").strip())
    scores = {key: 0 for key in FOCUS_STEMS}
    for focus_key, stems in FOCUS_STEMS.items():
        scores[focus_key] = sum(lower.count(stem) for stem in stems)
    return scores


def _pick_focus_key(scores: dict[str, int], *, fallback: str = "money_admin") -> str:
    if not scores:
        return fallback
    key, value = max(scores.items(), key=lambda item: item[1])
    return key if value > 0 else fallback


def _build_daily_tone(traffic_lights: dict[str, Any], support_pattern: str, tension_pattern: str) -> str:
    health = str((traffic_lights or {}).get("health") or "").lower()
    money = str((traffic_lights or {}).get("money") or "").lower()
    love = str((traffic_lights or {}).get("love") or "").lower()
    if tension_pattern and health == "red":
        return "тон собранный и экономный по ресурсу"
    if tension_pattern:
        return "тон мягкий снаружи, но без права на лишний нажим"
    if support_pattern and money == "green" and love == "green":
        return "тон теплый, договорный и вполне прикладной"
    return "тон ровный, взрослый и без суеты"


def _build_daily_pacing(traffic_lights: dict[str, Any], day_context: dict[str, Any], month_data: dict[str, Any]) -> str:
    health = str((traffic_lights or {}).get("health") or "").lower()
    money = str((traffic_lights or {}).get("money") or "").lower()
    love = str((traffic_lights or {}).get("love") or "").lower()
    month_status = _normalize_status((month_data or {}).get("status"))
    if (day_context.get("moon") or {}).get("void_of_course"):
        return "ритм дня лучше держать короткими циклами: сначала проверить обратную связь, потом дожимать"
    if health == "red":
        return "день любит узкий фокус, короткий список дел и запас по времени"
    if month_status == "RED":
        return "лучше вести день короткими руками, а не инерцией длинного фронта"
    if money == "green" or love == "green":
        return "рабочий темп держится на одном-двух приоритетах, без расползания в суету"
    return "темп лучше собирать спокойно: один шаг, одна проверка, одно подтверждение"


def _build_daily_negotiation(focus_key: str, tension_pattern: str) -> str:
    if focus_key == "money_admin":
        if tension_pattern:
            return "в переговорах и документах полезнее короткая формулировка и письменная фиксация деталей"
        return "переговоры, письма и согласования лучше вести коротко, ясно и сразу по условиям"
    if focus_key == "relationship":
        return "в разговоре с близкими лучше работает теплый тон и один прямой вопрос вместо серии намеков"
    if tension_pattern:
        return "если разговор нагревается, снизь скорость ответа и вернись к фактам, а не к правоте"
    return "говори по существу и не растягивай согласование дольше, чем нужно делу"


def _build_daily_friction(tension_pattern: str, day_context: dict[str, Any]) -> str:
    if (day_context.get("moon") or {}).get("void_of_course"):
        return "жесткие решения в пустоту, торопливая переписка и попытка закрыть вопрос без обратной связи"
    if tension_pattern:
        return tension_pattern
    return "распыление внимания, лишние обещания и попытка решить все одним рывком"


def _build_daily_rest(traffic_lights: dict[str, Any], day_context: dict[str, Any]) -> str:
    health = str((traffic_lights or {}).get("health") or "").lower()
    if (day_context.get("moon") or {}).get("void_of_course"):
        return "оставь запас между задачами и не требуй от дня мгновенной финальности"
    if health == "red":
        return "телу нужен режим и пауза перед следующим заходом: перегрев здесь дорогой"
    if health == "yellow":
        return "держи запас по времени и не съедай весь ресурс первым импульсом"
    return "силы лучше держатся на ровном темпе, чем на вспышках"


def _build_daily_money_focus(focus_key: str, traffic_lights: dict[str, Any], support_pattern: str) -> str:
    money = str((traffic_lights or {}).get("money") or "").lower()
    if focus_key == "money_admin" and money == "green":
        return "хорошо закрывать один документ, одно согласование, одну покупку или одно условие сделки"
    if money == "red":
        return "деньги и условия любят холодную проверку цены, срока и объема обязательств"
    if "покуп" in support_pattern or "цен" in support_pattern:
        return "если тратишь или договариваешься о цене, держи выбор простым и без лишних украшений"
    return "рабочие и денежные вопросы лучше собирать по одному, а не параллельной пачкой"


def _build_daily_relationship_focus(focus_key: str, traffic_lights: dict[str, Any], support_pattern: str) -> str:
    love = str((traffic_lights or {}).get("love") or "").lower()
    if focus_key == "relationship" and love == "green":
        return "контакт лучше строить через теплый тон, малый жест и спокойную формулировку"
    if love == "red":
        return "не достраивай мотивы за другого: сначала уточни, потом реагируй"
    if "симпат" in support_pattern or "контакт" in support_pattern:
        return "мягкость сегодня работает сильнее, чем демонстрация правоты"
    return "отношения сегодня любят ясность без нажима и без скрытых проверок"


def _build_daily_practical_move(
    focus_key: str,
    traffic_lights: dict[str, Any],
    support_pattern: str,
    tension_pattern: str,
) -> str:
    money = str((traffic_lights or {}).get("money") or "").lower()
    love = str((traffic_lights or {}).get("love") or "").lower()
    health = str((traffic_lights or {}).get("health") or "").lower()

    if focus_key == "money_admin":
        if tension_pattern:
            return "Закрой один документ, один дедлайн или одно согласование и не обещай лишнего до перепроверки."
        return "Продвинь один рабочий или денежный вопрос и сразу зафиксируй условие письменно."
    if focus_key == "relationship":
        if love == "green":
            return "Сделай ставку на один теплый разговор, один спокойный жест или одну аккуратную договоренность."
        return "Выбери один важный разговор и снизь в нем градус раньше, чем доказывать свою правоту."
    if focus_key == "rest" or health == "red":
        return "Сузь день до одного приоритета, оставь паузу между задачами и не превращай усталость в спор."
    if "покуп" in support_pattern or money == "green":
        return "Двигай одну покупку, одно условие или одну рабочую задачу, а остальное оставь в фоне."
    return "Держи день на одном главном ходе и не открывай второй фронт без необходимости."


def _build_daily_headline(
    support_pattern: str,
    tension_pattern: str,
    focus_key: str,
    traffic_lights: dict[str, Any],
) -> str:
    if support_pattern and tension_pattern:
        return (
            f"День про {support_pattern}, но важно помнить: {tension_pattern}."
        )
    if tension_pattern:
        return f"День про {tension_pattern}, поэтому лишний нажим быстро даст отдачу."
    if support_pattern:
        return f"День про {support_pattern}: хороший результат дает короткий и взрослый ход."
    if focus_key == "relationship":
        return "День про мягкий контакт и аккуратную ясность, а не про давление."
    if str((traffic_lights or {}).get("money") or "").lower() == "green":
        return "День про собранные решения, деньги и условия, которые лучше доводить без суеты."
    return "День про короткий фокус, спокойный темп и взрослое отношение к приоритетам."


def build_daily_forecast_semantic_layer(
    *,
    fast_hits: list[dict[str, Any]] | None = None,
    traffic_lights: dict[str, Any] | None = None,
    day_context: dict[str, Any] | None = None,
    month_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hits = [item for item in (fast_hits or []) if isinstance(item, dict)]
    support_pattern = ""
    tension_pattern = ""

    for hit in hits:
        pattern = _describe_fast_hit(hit)
        quality = _aspect_quality(hit.get("type"), hit.get("transit"))
        if quality == "supportive" and not support_pattern:
            support_pattern = pattern
        if quality == "tense" and not tension_pattern:
            tension_pattern = pattern
        if support_pattern and tension_pattern:
            break

    support_and_tension_text = " ".join(
        part for part in (support_pattern, tension_pattern) if part
    )
    scores = _collect_focus_scores(
        support_and_tension_text,
        str(day_context or ""),
        str(month_data or ""),
    )
    lights = traffic_lights or {}
    if str(lights.get("money") or "").lower() == "green":
        scores["money_admin"] += 1
    if str(lights.get("love") or "").lower() == "green":
        scores["relationship"] += 1
    if str(lights.get("health") or "").lower() in {"red", "yellow"}:
        scores["rest"] += 1
    focus_key = _pick_focus_key(scores, fallback="money_admin")

    headline = _build_daily_headline(support_pattern, tension_pattern, focus_key, lights)
    return {
        "tone": _build_daily_tone(lights, support_pattern, tension_pattern),
        "tension": tension_pattern or "напряжение рождается не из масштаба, а из лишней скорости и распыления",
        "pacing": _build_daily_pacing(lights, day_context or {}, month_data or {}),
        "negotiation": _build_daily_negotiation(focus_key, tension_pattern),
        "friction": _build_daily_friction(tension_pattern, day_context or {}),
        "rest": _build_daily_rest(lights, day_context or {}),
        "money_admin_focus": _build_daily_money_focus(focus_key, lights, support_pattern),
        "relationship_softness": _build_daily_relationship_focus(focus_key, lights, support_pattern),
        "headline": headline,
        "practical_move": _build_daily_practical_move(focus_key, lights, support_pattern, tension_pattern),
        "support_pattern": support_pattern,
        "focus_key": focus_key,
    }


def _build_primary_focus_from_strings(strings: list[str], *, fallback: str) -> str:
    scores = _collect_focus_scores(*strings)
    return _pick_focus_key(scores, fallback=fallback)


def _build_week_pacing(status: str, void_days: int, red_days: int) -> str:
    if void_days:
        return "держи неделю короткими циклами: согласование, проверка, только потом дожим"
    if status == "RED":
        return "вести неделю лучше узким фронтом и без лобового разгона"
    if red_days:
        return "неделя едет рывками, поэтому полезнее короткие сборки и повторная сверка деталей"
    if status == "GREEN":
        return "можно двигать подготовленное, если не дробить внимание на параллельные срочности"
    return "ритм недели любит спокойную координацию и одну главную линию"


def _build_status_negotiation(status: str, focus_key: str) -> str:
    if focus_key == "money_admin":
        if status == "RED":
            return "условия, сроки и документы требуют холодной формулировки и фиксации без двусмысленности"
        return "лучший результат дают короткие договоренности и быстрое подтверждение деталей"
    if focus_key == "relationship":
        return "в отношениях полезнее прямой спокойный разговор, чем длинная серия намеков и ожиданий"
    if status == "RED":
        return "когда разговор нагревается, сначала сузь задачу, потом возвращайся к сути"
    return "договариваться лучше по существу и не раздувать переписку шире задачи"


def _build_status_rest(status: str, *, has_pressure: bool = False, has_void: bool = False) -> str:
    if has_void:
        return "оставляй буфер между задачами и не считай промежуточное согласие финалом"
    if status == "RED":
        return "восстановление здесь часть стратегии, а не бонус к ней"
    if has_pressure:
        return "держи запас по времени и по нервной системе: неделя/месяц не любят жизнь на одном всплеске"
    return "ритм держится лучше там, где есть пауза, а не только усилие"


def _build_focus_headline(scope: str, status: str, focus_key: str, fallback_headline: str) -> str:
    focus_map = {
        "money_admin": {
            "week": "Неделя про условия, документы, рабочие стыки и цену поспешных решений.",
            "month": "Месяц про условия, цену выбора, документы и взрослую сборку рабочего контура.",
        },
        "relationship": {
            "week": "Неделя про тон контакта и цену лишнего нажима в разговорах.",
            "month": "Месяц про качество договоренностей и то, насколько мягко или жестко ты ведешь важные разговоры.",
        },
        "rest": {
            "week": "Неделя про темп, нервную систему и умение не жить на одном всплеске.",
            "month": "Месяц про режим, выносливость и то, как ты распределяешь ресурс по длинной дистанции.",
        },
        "launch": {
            "week": "Неделя про запуск, видимый ход и контроль над тем, чтобы скорость не превратилась в трение.",
            "month": "Месяц про длинный запуск, видимую ставку и цену слишком раннего разгона.",
        },
    }
    candidate = focus_map.get(focus_key, {}).get(scope)
    if status == "GREEN" and candidate and "цену" in candidate.lower():
        candidate = candidate.replace("цену", "ритм")
    return candidate or fallback_headline


def _build_month_scene_seed(status: str, focus_key: str) -> str:
    scene_map = {
        "money_admin": {
            "RED": "Месяц сильнее всего чувствуется там, где у каждой договоренности появляется цена: сроки, документы, деньги и вопрос, что ты действительно готова или готов тянуть.",
            "YELLOW": "Месяц раскрывается через переговоры, условия работы, деньги и мелкую координацию: одна недосказанность потом тянет весь график.",
            "GREEN": "Месяц дает заметный ход через договоренности, деньги и рабочую механику: то, что названо ясно, начинает приносить результат.",
        },
        "relationship": {
            "RED": "Месяц проверяет не чувства сами по себе, а тон разговора, границы и цену недосказанности в близких и рабочих союзах.",
            "YELLOW": "Месяц чаще проживается через разговоры, симпатии, обратную связь и все места, где хочется додумать за другого.",
            "GREEN": "Месяц хорошо идет через теплые союзы, ясные договоренности и один важный разговор по существу.",
        },
        "rest": {
            "RED": "Месяц быстро показывает цену перегруза: тело, график и нервная система становятся частью стратегии, а не фоном.",
            "YELLOW": "Месяц просит взрослого ритма: запас сил, паузы и режим важны не меньше, чем список задач.",
            "GREEN": "Месяц дает ресурс на длинный ход, если не обращаться с телом и вниманием как с бесконечным запасом.",
        },
        "launch": {
            "RED": "Месяц проверяет цену ускорения: запуск, дедлайны и силовые ходы работают только там, где уже собрана опора.",
            "YELLOW": "Месяц выглядит как длинный запуск: сначала настройка, потом точный нажим, потом закрепление результата.",
            "GREEN": "Месяц любит видимый ход: запуск, переговоры и личный жест могут вывести подготовленную ставку наружу.",
        },
    }
    return scene_map.get(focus_key, scene_map["money_admin"]).get(status, scene_map["money_admin"]["YELLOW"])


def _build_month_campaign_shape(status: str) -> str:
    return {
        "RED": "Сначала сузить фронт, затем пересобрать слабые места, к середине подтвердить рабочий контур, в финале спокойно зафиксировать результат.",
        "YELLOW": "Сначала настроить курс, затем проверить стыки, к середине дать ход главной теме, в финале упаковать и подтвердить результат.",
        "GREEN": "Сначала запустить сильную ставку, затем усилить видимость, к середине закрепить темп, в финале превратить ход в устойчивый результат.",
    }[status]


def _build_month_finale(status: str, focus_key: str) -> str:
    focus_map = {
        "money_admin": "Финал месяца решается на подтверждении условий, сроков и реальной цены обязательств.",
        "relationship": "Финал лучше всего проживать через ясный разговор и фиксацию взаимных ожиданий.",
        "rest": "Финал требует защитить режим и не превращать хороший темп в перерасход.",
        "launch": "Финал нужен, чтобы закрепить ход и не сжечь результат второй волной суеты.",
    }
    if status == "RED":
        return "Финальная неделя выигрывает не рывком, а чистой фиксацией: что закрыто, что перенесено, что снято без сожаления."
    return focus_map.get(focus_key, focus_map["money_admin"])


def build_week_forecast_semantic_layer(
    summary: dict[str, Any],
    days: list[dict[str, Any]],
) -> dict[str, Any]:
    status = _normalize_status((summary or {}).get("traffic_light"))
    red_days = sum(1 for day in days if str(day.get("traffic_light") or "").upper() == "RED")
    void_days = sum(1 for day in days if (day.get("moon") or {}).get("void_of_course"))
    event_strings = [
        str(item)
        for day in days
        for item in (day.get("events") or [])
        if str(item).strip()
    ]
    focus_key = _build_primary_focus_from_strings(event_strings, fallback="money_admin")
    has_pressure = red_days > 0 or float((summary or {}).get("avg_tension") or 0.0) >= 0.8
    headline = _build_focus_headline("week", status, focus_key, DEFAULT_WEEK_HEADLINES[status])

    return {
        "tone": {
            "RED": "неделя требует взрослой собранности и сокращения лишнего",
            "YELLOW": "тон недели рабочий, но требует внимательности к стыкам и мелким срывам",
            "GREEN": "тон недели уверенный и продуктивный, если не расплескать его на шум",
        }[status],
        "tension": {
            "RED": "трение рождается из перегруза, жёсткого нажима и попытки тащить слишком много сразу",
            "YELLOW": "слабое место недели не драматично, но легко рассыпается на деталях и несогласованности",
            "GREEN": "главный риск недели не в препятствии, а в том, что хороший темп можно потратить на второстепенное",
        }[status],
        "pacing": _build_week_pacing(status, void_days, red_days),
        "negotiation": _build_status_negotiation(status, focus_key),
        "friction": {
            "RED": "спор на скорости, лишний фронт и попытка закрыть вопрос силой",
            "YELLOW": "обещания раньше факта, недопроверенные детали и нервная суета",
            "GREEN": "мелкая суета и параллельные срочности, которые съедают сильный ход",
        }[status],
        "rest": _build_status_rest(status, has_pressure=has_pressure, has_void=void_days > 0),
        "money_admin_focus": {
            "money_admin": "рабочие и денежные вопросы лучше вести короткими циклами: согласование, подтверждение, фиксация",
            "relationship": "даже в рабочих вопросах тон и форма разговора будут влиять на результат сильнее обычного",
            "rest": "не вешай на неделю больше обязательств, чем реально выдерживает твой режим",
            "launch": "хорошо двигаются задачи, где уже понятны сроки, владельцы и следующий шаг",
        }.get(focus_key, "лучше всего едет то, что можно быстро проверить и зафиксировать"),
        "relationship_softness": {
            "RED": "контакт держится на ясных границах и коротких договоренностях без скрытого раздражения",
            "YELLOW": "в отношениях лучше работает спокойная обратная связь без домысливания за другого",
            "GREEN": "теплый тон и один прямой разговор дают больше, чем серия косвенных сигналов",
        }[status],
        "headline": headline,
        "practical_move": {
            "RED": "Держи один главный трек недели, все остальное сверяй с ним и не открывай новый спор без необходимости.",
            "YELLOW": "Собери одну рабочую линию недели и проверяй на ней сроки, договоренности и слабые стыки.",
            "GREEN": "Продвигай то, что готово к ходу, и сразу закрепляй результат, пока неделя его держит.",
        }[status],
        "focus_key": focus_key,
    }


def build_month_forecast_semantic_layer(
    *,
    status: Any,
    event_cards: list[dict[str, Any]] | None = None,
    phases: list[dict[str, Any]] | None = None,
    status_summary: str = "",
    central_task: str = "",
) -> dict[str, Any]:
    normalized_status = _normalize_status(status)
    cards = [item for item in (event_cards or []) if isinstance(item, dict)]
    phase_cards = [item for item in (phases or []) if isinstance(item, dict)]
    source_strings = [
        str(card.get("event") or "")
        + " "
        + str(card.get("life_signal") or "")
        for card in cards
    ]
    focus_key = _build_primary_focus_from_strings(source_strings, fallback="money_admin")
    high_pressure = any(str(card.get("pressure") or "").lower() == "high" for card in cards)
    phase_pressure = any(str(phase.get("pressure") or "").lower() == "high" for phase in phase_cards)
    headline = _build_focus_headline("month", normalized_status, focus_key, DEFAULT_MONTH_HEADLINES[normalized_status])
    if status_summary:
        headline = status_summary if len(status_summary) >= len(headline) - 20 else headline

    pacing_map = {
        "RED": "месяц лучше вести короткими этапами и заранее отсекать все, что размывает опорную ставку",
        "YELLOW": "первую половину полезно отдать настройке и проверке, вторую - точечному движению по главной линии",
        "GREEN": "месяц любит длинный ровный ход: запуск, затем закрепление, затем упаковку результата",
    }
    money_map = {
        "RED": "в деньгах, сроках и обязательствах важнее холодный расчет, чем красивая амбиция",
        "YELLOW": "лучше всего месяц едет там, где цена, объем работ и условия названы без тумана",
        "GREEN": "есть окно провести сильную идею в деньги и рабочий результат, если держать форму и счет",
    }
    relationship_map = {
        "RED": "отношения и рабочие союзы не выдерживают скрытого раздражения: полезнее короткая честная рамка",
        "YELLOW": "мягкость здесь не слабость, а способ не тратить месяц на недоговоренность и лишнюю реакцию",
        "GREEN": "контакт можно укреплять через ясный тон, совместный ритм и один важный разговор по существу",
    }

    practical_move = central_task.strip() or {
        "RED": "Выбери один контур месяца, пересчитай цену обязательств и не открывай новый фронт, пока старый не собран.",
        "YELLOW": "Держи месяц как длинную партию: сначала сборка и проверка, потом движение только по главной теме.",
        "GREEN": "Проведи одну сильную ставку через весь месяц и закрепляй каждый промежуточный результат делом.",
    }[normalized_status]

    return {
        "tone": {
            "RED": "месяц требует трезвости, дисциплины и отказа от лишнего геройства",
            "YELLOW": "тон месяца рабочий и фазовый: он любит настройку больше, чем суету",
            "GREEN": "тон месяца уверенный и собранный, если держать курс на одной сильной линии",
        }[normalized_status],
        "tension": {
            "RED": "главное напряжение месяца - цена лишнего фронта, дедлайнов под давлением и плохо собранной системы",
            "YELLOW": "месяц ломается не на большой драме, а на распылении, сырой координации и недопроверенных стыках",
            "GREEN": "риск месяца не в запрете, а в том, что сильный ход можно потратить на шум и лишний азарт",
        }[normalized_status],
        "pacing": pacing_map[normalized_status],
        "negotiation": _build_status_negotiation(normalized_status, focus_key),
        "friction": {
            "RED": "гиперконтроль, жёсткое давление и попытка тащить больше, чем выдерживает контур",
            "YELLOW": "обещания раньше факта, рассыпающиеся детали и жизнь в полуготовом режиме",
            "GREEN": "распыление внимания, лишние встречи и переоценка собственного запаса хода",
        }[normalized_status],
        "rest": _build_status_rest(
            normalized_status,
            has_pressure=high_pressure or phase_pressure,
            has_void=False,
        ),
        "money_admin_focus": money_map[normalized_status],
        "relationship_softness": relationship_map[normalized_status],
        "headline": headline,
        "practical_move": practical_move,
        "scene_seed": _build_month_scene_seed(normalized_status, focus_key),
        "campaign_shape": _build_month_campaign_shape(normalized_status),
        "finale": _build_month_finale(normalized_status, focus_key),
        "focus_key": focus_key,
    }
