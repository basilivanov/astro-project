# ############################################################################
# AI_HEADER: MODULE_FEED_SERVICE
# ROLE: Generate daily astrological content using LLM.
# DEPENDENCIES: backend.app.llm.orchestrator
# GRACE_ANCHORS: [FEED_GENERATION]
# ############################################################################

import json
import os
import re
from datetime import datetime
from typing import Any, Optional
import structlog

from ..llm.orchestrator import OpenRouterClient, build_cli_client_from_env
from .report_workflow import cleanup_content_artifacts

logger = structlog.get_logger()

# Simple In-Memory Cache for MVP: {(date_str, moon_sign): "vibe_text"}
_FEED_CACHE = {}

DAILY_FEED_PROMPT_REGISTRY = {
    "personalized_daily_v2": {
        "version": "2026-03-20",
        "contract": [
            "Ровно 2 коротких предложения на русском языке.",
            "Опирайся только на supplied facts, semantic layer и traffic lights.",
            "Не придумывай аспекты, события, сроки, города или биографию пользователя.",
            "Первое предложение: точная сцена дня. Второе: один практический шаг.",
            "Тон: 35% атмосфера, 65% практическая навигация; без рандома и лозунгов.",
        ],
    }
}

DAILY_GENERIC_MARKERS = (
    "отличный день",
    "любые препятствия",
    "все получится",
    "всё получится",
    "внутренний огонь",
    "энергией и уверенностью",
    "наполняет вас",
    "следуй за сердцем",
)

DAILY_WEAK_OPENERS = (
    "сегодня ты можешь чувствовать",
    "сегодня можно почувствовать",
    "ты можешь чувствовать",
    "день может ощущаться",
    "сегодня день",
)

DAILY_PLANET_ANCHORS = (
    "солнце",
    "луна",
    "меркур",
    "венер",
    "марс",
    "юпитер",
    "сатурн",
    "уран",
    "нептун",
    "плутон",
    "asc",
    "mc",
)

DAILY_SEMANTIC_ANCHOR_STEMS = (
    "договор",
    "переговор",
    "документ",
    "деньг",
    "покуп",
    "цен",
    "разговор",
    "контакт",
    "ритм",
    "темп",
    "пауз",
    "дедлайн",
    "срок",
    "приоритет",
    "запуск",
    "работ",
)

DAILY_ASPECT_RENDER = {
    "соединение": "в точном соединении",
    "квадрат": "в квадрате",
    "оппозиция": "в оппозиции",
    "тригон": "в тригоне",
    "секстиль": "в секстиле",
}

_ASPECT_CLAUSE_RE = re.compile(
    r"^(?P<transit>[A-Za-zА-Яа-яЁё. ]+?)\s+"
    r"(?P<aspect>Соединение|Квадрат|Оппозиция|Тригон|Секстиль)"
    r"(?:\s*\([^)]*\))?\s+"
    r"(?P<natal>[A-Za-zА-Яа-яЁё. ]+?)$"
)

# #START_BLOCK_FEED_GENERATION
def build_daily_vibe_fallback(
    moon_sign: str,
    moon_phase: str,
    aspects_summary: str,
    emphasis: Optional[str] = None,
) -> str:
    sign = (moon_sign or "неизвестном знаке").strip()
    phase = (moon_phase or "текущей фазе").strip()
    aspects = (aspects_summary or "").strip()
    emphasis_text = (emphasis or "").strip()
    if len(emphasis_text) > 180:
        emphasis_text = emphasis_text[:180].rsplit(" ", 1)[0].strip()
    details = "День лучше прожить на коротком фокусе: выбери один приоритет и не перегружай расписание."
    if any(token in emphasis_text.lower() for token in ("red", "шторм", "напряж", "оппозици", "квадрат")):
        details = "День не любит спешку: сузь повестку, не открывай лишние фронты и не решай все за один заход."
    if aspects and aspects.lower() != "нет мажорных аспектов":
        details = f"Главный акцент дня: {aspects}. Действуй точечно и не распыляй силы на лишние споры и резкие повороты."
    if emphasis_text:
        details = f"{details} {emphasis_text}"
    text = (
        f"Сегодня Луна в знаке {sign}, фаза: {phase}. "
        f"{details} Подходит время для аккуратных решений и взрослого темпа. ✨"
    )
    return cleanup_content_artifacts(text)


def _extract_text_from_feed_payload(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("general_vibe", "text", "content", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return ""
    if isinstance(payload, list):
        parts = []
        for item in payload:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str) and item.get("text").strip():
                    parts.append(item["text"].strip())
                elif isinstance(item.get("content"), str) and item.get("content").strip():
                    parts.append(item["content"].strip())
            elif isinstance(item, str) and item.strip():
                parts.append(item.strip())
        return " ".join(parts)
    return ""


def _split_aspect_clauses(aspects_summary: str) -> list[str]:
    return [
        clause.strip(" .")
        for clause in re.split(r"\s*,\s*", aspects_summary or "")
        if clause.strip() and clause.strip().lower() != "нет мажорных аспектов"
    ]


def _is_supportive_clause(clause: str) -> bool:
    lower = clause.lower()
    if "тригон" in lower or "секстиль" in lower:
        return True
    return "соединение" in lower and any(token in lower for token in ("венер", "юпитер", "солнц", "меркур"))


def _is_tense_clause(clause: str) -> bool:
    lower = clause.lower()
    if any(token in lower for token in ("квадрат", "оппозиц", "шторм", "red")):
        return True
    return "соединение" in lower and any(token in lower for token in ("марс", "сатурн", "уран", "плутон"))


def _render_aspect_clause(clause: str) -> str:
    match = _ASPECT_CLAUSE_RE.match((clause or "").strip())
    if not match:
        return clause.strip()
    transit = match.group("transit").strip()
    natal = match.group("natal").strip()
    aspect = DAILY_ASPECT_RENDER.get(match.group("aspect").strip().lower(), match.group("aspect").strip().lower())
    return f"{transit}-{natal} {aspect}"


def _pick_focus_area(personalization_context: Optional[dict[str, Any]], aspects_summary: str) -> str:
    traffic_lights = {}
    if personalization_context and isinstance(personalization_context.get("traffic_lights"), dict):
        traffic_lights = personalization_context["traffic_lights"]

    for key in ("love", "money", "health"):
        if str(traffic_lights.get(key, "")).lower() == "red":
            return key
    for key in ("money", "love", "health"):
        if str(traffic_lights.get(key, "")).lower() == "green":
            return key

    lower = aspects_summary.lower()
    if "венер" in lower or "луна" in lower:
        return "love"
    if "меркур" in lower or "юпитер" in lower or "mc" in lower:
        return "money"
    if "марс" in lower or "сатурн" in lower or "asc" in lower:
        return "health"
    return "money"


def _build_practical_move(focus_area: str, support: str, tension: str) -> str:
    source = " ".join(part for part in (support, tension) if part).lower()
    if "меркур" in source:
        return "Закрой одну переписку, одно согласование или один документ, не обещая лишнего."
    if "венер" in source and "марс" in source:
        return "Выбери один важный разговор или один аккуратный шаг навстречу, без давления и без лишних споров."
    if "венер" in source:
        return "Сделай ставку на один мягкий разговор, один жест или одну аккуратную покупку."
    if "марс" in source:
        return "Сведи день к одному приоритету и не заходи в спор на скорости."
    if "сатурн" in source:
        return "Проверь сроки и рамки, затем двигай только один обязательный вопрос."

    if focus_area == "love":
        return "Сделай ставку на один честный разговор вместо серии намеков и лишних претензий."
    if focus_area == "health":
        return "Снизь темп, оставь запас по времени и не бери на себя лишнюю нагрузку."
    return "Закрой один рабочий или денежный вопрос и не раздувай список задач."


def _build_daily_editorial_brief(
    moon_sign: str,
    aspects_summary: str,
    personalization_context: Optional[dict[str, Any]],
) -> tuple[str, str]:
    semantic_layer = {}
    if personalization_context and isinstance(personalization_context.get("semantic_layer"), dict):
        semantic_layer = personalization_context["semantic_layer"]

    headline = str(semantic_layer.get("headline") or "").strip()
    practical_move = str(semantic_layer.get("practical_move") or "").strip()
    if headline and practical_move:
        return headline.rstrip(". "), practical_move.rstrip(". ")

    clauses = _split_aspect_clauses(aspects_summary)
    support = next((clause for clause in clauses if _is_supportive_clause(clause)), "")
    tension = next((clause for clause in clauses if _is_tense_clause(clause)), "")
    focus_area = _pick_focus_area(personalization_context, aspects_summary)
    rendered_support = _render_aspect_clause(support) if support else ""
    rendered_tension = _render_aspect_clause(tension) if tension else ""

    if rendered_support and rendered_tension:
        image = f"{rendered_support} смягчает тон, но {rendered_tension} не любит нажим"
    elif rendered_tension:
        image = f"{rendered_tension} просит держать день уже и тише"
    elif rendered_support:
        focus_phrase = {
            "love": "контакта и симпатии",
            "money": "рабочих и денежных решений",
            "health": "темпа и самоконтроля",
        }.get(focus_area, "короткого фокуса")
        image = f"{rendered_support} дает мягкое окно для {focus_phrase}"
    else:
        image = f"Луна в {moon_sign} лучше раскрывается в коротком фокусе, а не в широком размахе"

    move = _build_practical_move(focus_area, support, tension)
    return image, move


def _build_personalized_daily_fallback(
    moon_sign: str,
    moon_phase: str,
    aspects_summary: str,
    emphasis: Optional[str],
    personalization_context: Optional[dict[str, Any]],
) -> str:
    image, move = _build_daily_editorial_brief(moon_sign, aspects_summary, personalization_context)
    image = image.rstrip(". ")
    move = move.rstrip(". ")
    fact_hint = ""
    if emphasis:
        cleaned = str(emphasis).strip()
        if cleaned:
            fact_hint = cleaned[:120].rsplit(" ", 1)[0].strip() if len(cleaned) > 120 else cleaned

    first_sentence = f"Сегодня {image}."
    second_sentence = move + "."
    if fact_hint and not any(token in first_sentence.lower() for token in DAILY_PLANET_ANCHORS):
        first_sentence = f"{first_sentence[:-1]} {fact_hint}."
    return cleanup_content_artifacts(f"{first_sentence} {second_sentence}")


def _extract_fact_anchors(personalization_context: Optional[dict[str, Any]], aspects_summary: str) -> set[str]:
    source_chunks = [aspects_summary]
    if personalization_context:
        source_chunks.extend(
            line for line in personalization_context.get("fact_lines", []) if isinstance(line, str) and line.strip()
        )
        semantic_layer = personalization_context.get("semantic_layer")
        if isinstance(semantic_layer, dict):
            source_chunks.extend(
                str(value)
                for key, value in semantic_layer.items()
                if key in {"headline", "practical_move", "money_admin_focus", "relationship_softness", "pacing", "rest"}
                and isinstance(value, str)
                and value.strip()
            )

    lower = " ".join(source_chunks).lower()
    anchors = {token for token in DAILY_PLANET_ANCHORS if token in lower}
    if "green" in lower:
        anchors.add("green")
    if "red" in lower:
        anchors.add("red")
    anchors.update({token for token in DAILY_SEMANTIC_ANCHOR_STEMS if token in lower})
    return anchors


def _is_personalized_output_usable(
    text: str,
    aspects_summary: str,
    personalization_context: Optional[dict[str, Any]],
) -> bool:
    lower = text.lower()
    if any(marker in lower for marker in DAILY_GENERIC_MARKERS):
        return False
    if any(marker in lower for marker in DAILY_WEAK_OPENERS):
        return False
    sentences = [chunk.strip() for chunk in re.split(r"[.!?]+", text) if chunk.strip()]
    if len(sentences) > 2:
        return False
    if len(text.split()) > 60:
        return False

    level = str((personalization_context or {}).get("level") or "")
    if level.startswith("personalized"):
        anchors = _extract_fact_anchors(personalization_context, aspects_summary)
        if anchors and not any(anchor in lower for anchor in anchors):
            return False
    return True


def normalize_daily_vibe_text(
    raw_vibe: Any,
    moon_sign: str,
    moon_phase: str,
    aspects_summary: str,
    emphasis: Optional[str] = None,
    personalization_context: Optional[dict[str, Any]] = None,
) -> str:
    fallback = (
        _build_personalized_daily_fallback(
            moon_sign,
            moon_phase,
            aspects_summary,
            emphasis,
            personalization_context,
        )
        if personalization_context
        else build_daily_vibe_fallback(moon_sign, moon_phase, aspects_summary, emphasis=emphasis)
    )
    if isinstance(raw_vibe, tuple) and raw_vibe:
        raw_vibe = raw_vibe[0]

    text = raw_vibe if isinstance(raw_vibe, str) else _extract_text_from_feed_payload(raw_vibe)
    text = (text or "").strip()
    if not text:
        return fallback

    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            if lines[-1].strip().startswith("```"):
                text = "\n".join(lines[1:-1]).strip()
            else:
                text = "\n".join(lines[1:]).strip()

    candidate = text
    if candidate.startswith("{") or candidate.startswith("["):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None:
            text = _extract_text_from_feed_payload(parsed)

    text = cleanup_content_artifacts((text or "").replace('"', "").strip())
    if len(text) < 20:
        return fallback
    if personalization_context and not _is_personalized_output_usable(text, aspects_summary, personalization_context):
        return fallback
    return text


def resolve_feed_llm_mode() -> str:
    default_mode = os.getenv("DEFAULT_LLM_MODE", "openrouter").strip().lower() or "openrouter"
    mode = os.getenv("FEED_LLM_MODE", "").strip().lower() or default_mode
    if mode == "cheap":
        return "cheap"
    if mode not in {"openrouter", "fallback", "local", "mock", "stub", "cli", "gemini", "codex"}:
        return default_mode if default_mode in {"openrouter", "cheap", "cli", "gemini", "codex"} else "openrouter"
    return mode


def _build_personalized_prompt(personalization_context: Optional[dict[str, Any]]) -> tuple[str, str]:
    if not personalization_context:
        return "", ""

    fact_lines = [
        line.strip()
        for line in personalization_context.get("fact_lines", [])
        if isinstance(line, str) and line.strip()
    ]
    if not fact_lines:
        return "", ""

    prompt_block = "Персональный factual context:\n" + "\n".join(f"- {line}" for line in fact_lines[:6]) + "\n"
    fallback_detail = personalization_context.get("fallback_detail")
    if not isinstance(fallback_detail, str):
        fallback_detail = ""
    traffic_lights = personalization_context.get("traffic_lights")
    if isinstance(traffic_lights, dict) and traffic_lights:
        prompt_block += (
            "Светофоры дня:\n"
            f"- health: {traffic_lights.get('health', 'unknown')}\n"
            f"- money: {traffic_lights.get('money', 'unknown')}\n"
            f"- love: {traffic_lights.get('love', 'unknown')}\n"
        )
    semantic_layer = personalization_context.get("semantic_layer")
    if isinstance(semantic_layer, dict) and semantic_layer:
        prompt_block += (
            "Семантический слой дня (уже собран из фактов, не пересобирай его заново):\n"
            f"- tone: {semantic_layer.get('tone', '')}\n"
            f"- pacing: {semantic_layer.get('pacing', '')}\n"
            f"- negotiation: {semantic_layer.get('negotiation', '')}\n"
            f"- friction: {semantic_layer.get('friction', '')}\n"
            f"- rest: {semantic_layer.get('rest', '')}\n"
            f"- money_admin_focus: {semantic_layer.get('money_admin_focus', '')}\n"
            f"- relationship_softness: {semantic_layer.get('relationship_softness', '')}\n"
            f"- headline: {semantic_layer.get('headline', '')}\n"
            f"- practical_move: {semantic_layer.get('practical_move', '')}\n"
        )
    return prompt_block, fallback_detail.strip()


def get_daily_feed_prompt_contract(name: str = "personalized_daily_v2") -> dict[str, Any]:
    return DAILY_FEED_PROMPT_REGISTRY.get(name, DAILY_FEED_PROMPT_REGISTRY["personalized_daily_v2"])


async def get_daily_vibe_llm(
    moon_sign: str,
    moon_phase: str,
    aspects_summary: str,
    *,
    personalization_context: Optional[dict[str, Any]] = None,
    cache_scope: Optional[str] = None,
) -> str:
    """
    # PURPOSE: Generate a personalized daily vibe using a cheap LLM.
    # INPUT: Moon data, aspects summary string.
    # OUTPUT: 2-3 sentences of advice.
    # CONTEXT: Cached per day/sign.
    """
    
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    cache_key = (today_str, moon_sign, cache_scope or "shared")
    
    if cache_key in _FEED_CACHE:
        return _FEED_CACHE[cache_key]

    personalization_prompt, fallback_detail = _build_personalized_prompt(personalization_context)
    editorial_image, editorial_move = _build_daily_editorial_brief(
        moon_sign,
        aspects_summary,
        personalization_context,
    )

    prompt_contract = get_daily_feed_prompt_contract()
    contract_lines = "\n".join(f"- {line}" for line in prompt_contract["contract"])

    # Prompt construction
    prompt = (
        "Ты — персональный астролог-редактор. Нужны ровно 2 коротких предложения на русском языке.\n"
        f"Prompt registry: personalized_daily_v2 / {prompt_contract['version']}.\n"
        "Контракт daily из STYLE_CONTRACT.md: 35% атмосфера, 65% практическая навигация.\n"
        f"Жёсткие правила:\n{contract_lines}\n"
        "Собери ответ по формуле: один образ -> один поворот -> один практический ход.\n"
        "Первое предложение: одна жизненная сцена с опорой на точный факт. Второе предложение: один конкретный шаг на сегодня.\n"
        "Пиши на 'ты'. Без учебникового тона, без эзотерики и без мотивационных лозунгов.\n"
        "Общий объём: 24-48 слов. Максимум 1 эмодзи, но лучше без него.\n"
        "Если в данных есть шторм, RED-статус, квадрат или оппозиция, тон должен быть собранным и трезвым, а не восторженным.\n"
        "Запрещены фразы: 'отличный день', 'все получится', 'любые препятствия', 'внутренний огонь', 'ты можешь чувствовать'.\n"
        "Не пиши общие советы вроде 'избегай конфликтов' без сцены и без факта.\n"
        "Обязательно опирайся минимум на один конкретный факт или один semantic anchor из персонального блока ниже.\n"
        f"Редакторская сборка дня: образ '{editorial_image}'; практический ход '{editorial_move}'.\n"
        f"Текущие показатели: Луна в знаке {moon_sign}, фаза: {moon_phase}.\n"
        f"Аспекты дня: {aspects_summary}.\n"
        f"{personalization_prompt}"
        "Если есть и поддержка, и напряжение, покажи разворот через одно 'но'.\n"
        "Стиль: живой, личный, короткий.\n"
        f"Опирайся только на данные выше, не придумывай новые аспекты или события.\n"
        f"Ответь только текстом прогноза."
    )

    mode = resolve_feed_llm_mode()

    from ..engine_utils import translate_sign
    moon_sign_ru = translate_sign(moon_sign)

    if mode in {"fallback", "local", "mock", "stub"}:
        vibe = normalize_daily_vibe_text(
            "",
            moon_sign_ru,
            moon_phase,
            aspects_summary,
            emphasis=fallback_detail,
            personalization_context=personalization_context,
        )
        _FEED_CACHE[cache_key] = vibe
        return vibe

    try:
        if mode in {"cli", "gemini", "codex"}:
            provider_override = mode if mode in {"gemini", "codex"} else None
            client = build_cli_client_from_env(provider_override=provider_override)
        else:
            # Feed uses a cheap OpenRouter model by default.
            client = OpenRouterClient.from_env(mode="cheap")

        vibe = client.generate(prompt)
        vibe = normalize_daily_vibe_text(
            vibe,
            moon_sign_ru,
            moon_phase,
            aspects_summary,
            emphasis=fallback_detail,
            personalization_context=personalization_context,
        )

        _FEED_CACHE[cache_key] = vibe
        logger.info("feed.generated", sign=moon_sign_ru, mode=mode)
        return vibe
    except Exception as exc:
        logger.error("feed.generation_error", error=str(exc), mode=mode)
        vibe = normalize_daily_vibe_text(
            "",
            moon_sign_ru,
            moon_phase,
            aspects_summary,
            emphasis=fallback_detail,
            personalization_context=personalization_context,
        )
        _FEED_CACHE[cache_key] = vibe
        return vibe
# #END_BLOCK_FEED_GENERATION
