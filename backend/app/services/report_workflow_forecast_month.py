# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_FORECAST_MONTH
# ROLE: Month forecast prompt and rendering helpers.
# DEPENDENCIES: forecast_semantics.py, report_workflow_content.py
# GRACE_ANCHORS: [MONTH_PROMPT_CONTEXT, MONTH_FORECAST_RENDERING]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-FORECAST-MONTH
# purpose: Build month forecast deterministic cards, semantic prompt context, and rendered content.
# inputs:
#   - Month forecast context dictionaries and optional LLM content
# outputs:
#   - Month forecast prompt dictionaries and JSON block strings
# trace_obligations:
#   - Pure helper module; workflow caller retains report_id/block log attribution
# invariants:
#   - Month forecast copy and JSON structure remain stable across extraction
# non_goals:
#   - Does not mutate workflow persistence or call external LLM services
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-FORECAST-MONTH

# START_MODULE_MAP: M-REPORT-WORKFLOW-FORECAST-MONTH
# entrypoints:
#   - _build_month_forecast_prompt_context -> MONTH_PROMPT_CONTEXT
#   - _render_month_forecast_content -> MONTH_FORECAST_RENDERING
# END_MODULE_MAP: M-REPORT-WORKFLOW-FORECAST-MONTH

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from .forecast_semantics import build_month_forecast_semantic_layer
from .report_workflow_content import cleanup_content_artifacts


def _merge_week_text(base_text: str, factual_tail: str) -> str:
    base = str(base_text or "").strip()
    extra = str(factual_tail or "").strip()
    if not base:
        return extra
    if not extra:
        return base
    if extra.lower() in base.lower():
        return base
    if base[-1] not in ".!?":
        base = f"{base}."
    return f"{base} {extra}"


def _upper_first(text: Any) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    return value[0].upper() + value[1:]


def _join_sentence_parts(*parts: Any) -> str:
    merged = ""
    for part in parts:
        text = _upper_first(part)
        if not text:
            continue
        if text[-1] not in ".!?":
            text = f"{text}."
        merged = _merge_week_text(merged, text)
    return merged


def _normalize_status_variant(status: Any) -> str:
    normalized = str(status or "").strip().upper()
    if normalized == "RED":
        return "error"
    if normalized == "YELLOW":
        return "warning"
    return "success"

RU_MONTH_NAMES = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}

# START_BLOCK: MONTH_PROMPT_CONTEXT
def _parse_forecast_window_start(forecast_window: dict[str, Any]) -> datetime:
    raw = str((forecast_window or {}).get("start") or "").strip()
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _format_month_window_label(forecast_window: dict[str, Any]) -> str:
    start_dt = _parse_forecast_window_start(forecast_window)
    month_name = RU_MONTH_NAMES.get(start_dt.month, "")
    if not month_name:
        return str(start_dt.year)
    return f"{month_name} {start_dt.year}"


def _parse_month_event_line(raw_text: Any, start_dt: datetime) -> dict[str, Any]:
    raw = str(raw_text or "").strip()
    if not raw:
        return {"raw": "", "date_label": "", "event": "", "event_dt": None}

    date_label = ""
    event = raw
    match = re.match(r"^(?P<date>\d{2}\.\d{2})\s+(?P<body>.+)$", raw)
    if match:
        date_label = match.group("date")
        event = match.group("body").strip()

    event_dt = None
    if date_label:
        try:
            day_raw, month_raw = date_label.split(".", 1)
            day = int(day_raw)
            month = int(month_raw)
            year = start_dt.year + (1 if month < start_dt.month else 0)
            event_dt = datetime(
                year,
                month,
                day,
                tzinfo=start_dt.tzinfo,
            )
        except ValueError:
            event_dt = None

    return {
        "raw": raw,
        "date_label": date_label,
        "event": event,
        "event_dt": event_dt,
    }


def _build_month_event_life_signal(kind: str, event_text: str) -> str:
    lower = str(event_text or "").lower()

    if kind == "lunations":
        if "новолуние" in lower:
            return "запуск нового цикла: выбери одну ставку и сразу переведи ее в календарь."
        return "развязка и обратная связь: пора завершить висящий сюжет, а не держать его в подвешенном виде."

    if kind == "retrogrades":
        if "меркурий" in lower:
            return "перепроверка документов, переписок и условий сделки: цена спешки здесь выше обычного."
        if "венера" in lower:
            return "ревизия цены, симпатий и договоренностей: важно понять, что для тебя действительно ценно."
        return "возврат к старым обязательствам и настройке процесса: лучше править, чем форсировать."

    if kind == "ingresses":
        if "солнце" in lower:
            return "смена центра тяжести месяца: внимание уходит туда, где нужен личный жест и ясная позиция."
        if "меркурий" in lower:
            return "переговоры, письма, документы и короткие согласования выходят на первый план."
        if "венера" in lower:
            return "деньги, личные договоренности и вкус к выбору требуют более точной настройки."
        if "марс" in lower:
            return "темп заметно растет: запуск, дедлайны и силовые разговоры становятся острее."
        if "юпитер" in lower:
            return "окно для расширения, обучения или выхода к более широкой аудитории."
        return "меняется способ действовать и распределять внимание: старый режим уже не тянет месяц."

    if kind == "major_transits":
        hard = any(token in lower for token in ["квадрат", "оппозиц"])
        if "сатурн" in lower:
            return "проверка прочности планов и дедлайнов: месяц быстро наказывает за слабую сборку."
        if "марс" in lower and hard:
            return "темп легко превращается в конфликт: силу нужно дозировать, а не демонстрировать."
        if "уран" in lower:
            return "сюжет меняется рывком: оставляй запас на неожиданный разворот, а не цементируй план."
        if "плутон" in lower:
            return "вопрос контроля и цены решения выходит наружу: по инерции этот сюжет не пройти."
        if "юпитер" in lower:
            return "есть окно для роста, если уже собрана база и понятен вектор расширения."
        if hard:
            return "месяц требует точности и трезвого темпа: лишнее давление быстро даст отдачу."
        return "внешний триггер меняет ход событий: смотри, где пора закреплять результат, а не спорить."

    return "это один из внешних триггеров месяца: важно заметить, где он меняет твой реальный режим решений."


def _build_month_event_pressure(kind: str, event_text: str) -> str:
    lower = str(event_text or "").lower()
    if kind == "retrogrades":
        return "high"
    if kind == "major_transits" and any(token in lower for token in ["квадрат", "оппозиц"]):
        return "high"
    if kind in {"lunations", "major_transits"}:
        return "medium"
    return "low"


def _build_month_event_cards(
    month_data: dict[str, Any],
    forecast_window: dict[str, Any],
) -> list[dict[str, Any]]:
    start_dt = _parse_forecast_window_start(forecast_window)
    event_cards: list[dict[str, Any]] = []
    order = 0
    limits = {
        "lunations": 3,
        "ingresses": 4,
        "major_transits": 6,
        "retrogrades": 3,
    }

    for kind in ("lunations", "ingresses", "major_transits", "retrogrades"):
        for raw_item in (month_data.get(kind) or [])[: limits[kind]]:
            parsed = _parse_month_event_line(raw_item, start_dt)
            if not parsed["event"]:
                continue
            event_cards.append(
                {
                    "order": order,
                    "kind": kind,
                    "date_label": parsed["date_label"],
                    "event": parsed["event"],
                    "event_dt": parsed["event_dt"],
                    "life_signal": _build_month_event_life_signal(kind, parsed["event"]),
                    "pressure": _build_month_event_pressure(kind, parsed["event"]),
                }
            )
            order += 1

    def _sort_key(card: dict[str, Any]) -> tuple[int, int]:
        event_dt = card.get("event_dt")
        ordinal = event_dt.date().toordinal() if isinstance(event_dt, datetime) else 9999999
        return (ordinal, int(card.get("order", 0)))

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for card in sorted(event_cards, key=_sort_key):
        key = (str(card.get("date_label") or ""), str(card.get("event") or ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(card)

    return deduped[:10]


def _build_month_phase_focus(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if "новолуние" in lower:
        return "Собери новую ставку месяца и сразу привяжи ее к реальному графику."
    if "полнолуние" in lower:
        return "Закрой висящий сюжет и добудь честную обратную связь, вместо того чтобы тянуть неопределенность."
    if any(event.get("kind") == "retrogrades" for event in phase_events):
        return "Проверь хвосты и слабые места процесса: здесь полезнее корректировка, чем разгон."
    if any(event.get("pressure") == "high" for event in phase_events):
        return "Сузь повестку до одного-двух фронтов и держи управление руками, а не инерцией."
    if any(event.get("kind") == "ingresses" for event in phase_events):
        return "Перенастрой режим и формат общения под новые вводные, не держась за старую механику."

    default_map = {
        "RED": [
            "Начинай месяц с ревизии ресурсов, а не с красивого рывка.",
            "Держи середину месяца собранной и не дроби внимание.",
            "Проверяй, что выдерживает реальность, а что пора снимать с повестки.",
            "Подводи месяц к спокойной фиксации результата, а не к штурму в последний момент.",
        ],
        "YELLOW": [
            "Собери опорный ритм и не принимай промежуточный результат за финальный.",
            "Проверяй детали и стыки между задачами: на этом месяц либо едет, либо рассыпается.",
            "Используй середину месяца для выравнивания курса и точечных действий.",
            "Дожимай только то, что уже прошло проверку делом.",
        ],
        "GREEN": [
            "Запусти то, что давно готово, и дай сильной идее реальный ход.",
            "Усили видимость и качество коммуникации вокруг главной ставки.",
            "Середину месяца используй для закрепления темпа и переговоров.",
            "Финальную неделю посвяти упаковке результата и фиксации следующего шага.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_push(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if "меркурий" in lower:
        return "Продвигай переговоры, документы, письма, брифы и все, что зависит от ясной формулировки."
    if "венера" in lower:
        return "Продвигай деньги, условия сотрудничества, личные договоренности и вопросы ценности."
    if "марс" in lower:
        return "Продвигай запуск, дедлайны, силовые задачи и короткие решающие разговоры."
    if "юпитер" in lower:
        return "Продвигай обучение, публичность и выход в более широкий контур возможностей."
    if any(event.get("kind") == "lunations" for event in phase_events):
        return "Продвигай одно решение, которое либо открывает новый цикл, либо чисто закрывает старый."

    default_map = {
        "RED": [
            "Продвигай только обязательное и уже подтвержденное: месяц не любит лишний фронт.",
            "Продвигай структуру, договоренности и режим, а не амбициозную надстройку.",
            "Продвигай проверенные задачи с коротким циклом обратной связи.",
            "Продвигай фиксацию результата и разгрузку хвостов.",
        ],
        "YELLOW": [
            "Продвигай задачи, где важны аккуратность, последовательность и ясная договоренность.",
            "Продвигай то, что можно собрать по шагам и быстро перепроверить.",
            "Продвигай один главный трек, а не россыпь параллельных инициатив.",
            "Продвигай завершение, упаковку и внятную передачу результата.",
        ],
        "GREEN": [
            "Продвигай запуск и все, что готово выйти из подготовки в реальное движение.",
            "Продвигай коммуникацию, встречи и заметные ходы вокруг главной темы месяца.",
            "Продвигай масштабирование сильной идеи через системный темп, а не через азарт.",
            "Продвигай закрепление результата и подготовку следующего шага.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_restraint(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if any(event.get("kind") == "retrogrades" for event in phase_events):
        return "Не обещай больше, чем успеешь перепроверить, и не игнорируй правки ради скорости."
    if "марс" in lower and any(token in lower for token in ["квадрат", "оппозиц"]):
        return "Не переводи темп в спор и не жги ресурс на доказательство правоты."
    if "сатурн" in lower:
        return "Не дави на срок там, где система явно просит пересборки и уточнений."
    if "уран" in lower:
        return "Не цементируй жесткий план без запаса на разворот и непредвиденную правку."
    if "плутон" in lower:
        return "Не заходи в силовой контроль и не делай ставку на перетягивание каната."

    default_map = {
        "RED": [
            "Не начинай месяц с второго главного фронта и не живи в аварийном режиме.",
            "Не путай контроль с гиперконтролем: лишнее давление здесь только сжигает ресурс.",
            "Не обещай разворот быстрее, чем позволяет реальная система.",
            "Не штурмуй финал месяца рывком из чувства вины или спешки.",
        ],
        "YELLOW": [
            "Не принимай первую рабочую версию за готовый результат.",
            "Не разбрасывайся на параллельные задачи без общего ритма.",
            "Не ускоряйся раньше, чем закрыты слабые места и зависшие детали.",
            "Не оставляй итог без упаковки и подтверждения договоренностей.",
        ],
        "GREEN": [
            "Не трать сильную неделю на суету и второстепенные переписки.",
            "Не дроби внимание на чужие срочности, если они не двигают твою главную ставку.",
            "Не принимай хороший темп за бессмертный ресурс: телу нужен режим.",
            "Не бросай закрепление результата сразу после удачного хода.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_role(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if "новолуние" in lower:
        return "Запуск новой ставки"
    if "полнолуние" in lower:
        return "Развязка и обратная связь"
    if any(event.get("kind") == "retrogrades" for event in phase_events):
        return "Перепроверка и правки"
    if any(event.get("pressure") == "high" for event in phase_events):
        return "Точка напряжения" if status != "RED" else "Жесткий выбор"
    if any(event.get("kind") == "ingresses" for event in phase_events):
        return "Смена режима"

    default_map = {
        "RED": [
            "Сужение фронта",
            "Техническая пересборка",
            "Жесткий выбор",
            "Спокойная фиксация",
        ],
        "YELLOW": [
            "Сборка курса",
            "Проверка стыков",
            "Точка хода",
            "Упаковка результата",
        ],
        "GREEN": [
            "Запуск ставки",
            "Усиление видимости",
            "Закрепление темпа",
            "Фиксация результата",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_scene(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    if phase_events:
        lead_signal = str(phase_events[0].get("life_signal") or "").strip()
        lead_anchor = " — ".join(
            part
            for part in [
                str(phase_events[0].get("date_label") or "").strip(),
                str(phase_events[0].get("event") or "").strip(),
            ]
            if part
        ).strip()
        text = ""
        if lead_signal:
            text = f"На поверхности недели — {lead_signal.rstrip('.')}."
        if lead_anchor:
            anchor_line = f"Опорная дата: {lead_anchor}."
            text = f"{text} {anchor_line}".strip() if text else anchor_line
        return text

    default_map = {
        "RED": [
            "Неделя чувствуется через необходимость быстро понять, что действительно обязательно, а что пора снять с повестки.",
            "На первый план выходят правки, возвраты и техническая пересборка того, что не выдержало первую проверку.",
            "В центре окажется момент выбора: подтверждать обязательство, переносить срок или честно отказываться от лишнего.",
            "Эта фаза про разгрузку хвостов и спокойную фиксацию результата без финального штурма.",
        ],
        "YELLOW": [
            "Неделя чувствуется через сборку графика, договоренностей и ясного приоритета.",
            "На первый план выходят стыки: кто что обещал, где нужен второй проход и что требует уточнения.",
            "Появляется окно для реального движения по главной теме, если база уже проверена.",
            "Неделя просит упаковать сделанное, подтвердить договоренности и закрыть висящие хвосты.",
        ],
        "GREEN": [
            "На старте недели важно вынести вперед одну главную ставку и сразу дать ей видимый ход.",
            "Неделя чаще проявляется через встречи, переговоры и внешний отклик на то, что уже запущено.",
            "Фаза нужна для удержания темпа: меньше суеты, больше системного продвижения.",
            "Финальная неделя про закрепление результата и подготовку следующего хода без лишнего шума.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_transition(status: str, phase_index: int) -> str:
    transition_map = {
        "RED": [
            "Сначала месяц просит остановить расползание и сузить фронт.",
            "После этого становится видно, где нужна пересборка, а не давление.",
            "К середине вопрос уже не в подготовке, а в цене выбора и выдержке.",
            "В финале выигрывает спокойная фиксация, а не попытка все добежать рывком.",
        ],
        "YELLOW": [
            "Сначала важнее собрать курс, чем создавать видимость быстрого движения.",
            "Дальше месяц переводит внимание на стыки, сроки и качество координации.",
            "К середине появляется право на точечный ход там, где база уже проверена.",
            "Финал нужен для упаковки результата и подтверждения того, что действительно поехало.",
        ],
        "GREEN": [
            "Старт месяца дает окно на запуск, но только для того, что уже готово к реальному ходу.",
            "Затем фокус смещается на видимость, разговоры и поддержку основной ставки.",
            "К середине важно не ускоряться еще сильнее, а удержать темп и качество.",
            "Финальная неделя нужна, чтобы превратить импульс в устойчивый результат.",
        ],
    }
    return transition_map.get(status, transition_map["YELLOW"])[phase_index]


def _build_month_phase_cards(
    event_cards: list[dict[str, Any]],
    forecast_window: dict[str, Any],
    status: str,
) -> list[dict[str, Any]]:
    start_dt = _parse_forecast_window_start(forecast_window)
    phase_cards: list[dict[str, Any]] = []

    for phase_index in range(4):
        phase_start = start_dt + timedelta(days=phase_index * 7)
        phase_end = phase_start + timedelta(days=6)
        phase_events: list[dict[str, Any]] = []
        for event in event_cards:
            event_dt = event.get("event_dt")
            if not isinstance(event_dt, datetime):
                continue
            day_offset = (event_dt.date() - start_dt.date()).days
            if phase_index * 7 <= day_offset <= phase_index * 7 + 6:
                phase_events.append(event)

        pressure = "low"
        if any(event.get("pressure") == "high" for event in phase_events):
            pressure = "high"
        elif any(event.get("pressure") == "medium" for event in phase_events):
            pressure = "medium"

        phase_role = _build_month_phase_role(status, phase_index, phase_events)
        phase_cards.append(
            {
                "label": f"Неделя {phase_index + 1}",
                "date_range_label": f"{phase_start.strftime('%d.%m')}-{phase_end.strftime('%d.%m')}",
                "pressure": pressure,
                "events": [
                    " ".join(
                        part
                        for part in [event.get("date_label"), event.get("event")]
                        if part
                    ).strip()
                    for event in phase_events[:3]
                ],
                "phase_role": phase_role,
                "lead_event": (phase_events[0].get("event") if phase_events else ""),
                "lead_signal": (phase_events[0].get("life_signal") if phase_events else ""),
                "scene_hint": _build_month_phase_scene(status, phase_index, phase_events),
                "transition_hint": _build_month_phase_transition(status, phase_index),
                "focus_hint": _build_month_phase_focus(status, phase_index, phase_events),
                "push_hint": _build_month_phase_push(status, phase_index, phase_events),
                "restraint_hint": _build_month_phase_restraint(status, phase_index, phase_events),
            }
        )

    return phase_cards


def _build_month_status_summary(status: str) -> str:
    summary_map = {
        "RED": "Месяц выглядит как пересборка кампании: давление есть, но выигрыш придет через дисциплину и сужение фронта.",
        "YELLOW": "Месяц неровный, но рабочий: результат держится на ритме, проверке деталей и умении не дергаться раньше времени.",
        "GREEN": "Месяц дает ход для заметного продвижения: важно не распылиться и провести сильную ставку через весь горизонт.",
    }
    return summary_map.get(status, summary_map["YELLOW"])


def _build_month_central_task(status: str) -> str:
    task_map = {
        "RED": "Собери один рабочий контур и убери все, что множит давление без отдачи.",
        "YELLOW": "Держи месяц как длинную партию: сначала настройка и проверка, потом ускорение.",
        "GREEN": "Переведи готовую идею в реальные действия и закрепи темп по ходу месяца.",
    }
    return task_map.get(status, task_map["YELLOW"])


def _build_month_campaign_arc(
    semantic_layer: dict[str, Any],
    phases: list[dict[str, Any]],
) -> dict[str, str]:
    phase_roles = [str(phase.get("phase_role") or "").strip().lower() for phase in phases[:4] if str(phase.get("phase_role") or "").strip()]
    if len(phase_roles) >= 4:
        phase_sequence = (
            f"Сначала {phase_roles[0]}, затем {phase_roles[1]}, "
            f"к середине {phase_roles[2]}, в финале {phase_roles[3]}."
        )
    else:
        phase_sequence = str(semantic_layer.get("campaign_shape") or "").strip()

    return {
        "opening_scene": str(semantic_layer.get("scene_seed") or "").strip(),
        "phase_sequence": phase_sequence,
        "close_focus": str(semantic_layer.get("finale") or semantic_layer.get("practical_move") or "").strip(),
    }


def _build_month_forecast_prompt_context(context: dict[str, Any]) -> dict[str, Any]:
    client = context.get("client", {}) or {}
    month_data = copy.deepcopy(context.get("month_forecast_data") or {})
    forecast_window = copy.deepcopy(context.get("forecast_window") or {})
    event_cards = _build_month_event_cards(month_data, forecast_window)
    status = str(month_data.get("status") or "YELLOW").upper()
    key_events = [
        " ".join(
            part
            for part in [card.get("date_label"), card.get("event")]
            if part
        ).strip()
        for card in event_cards
    ]
    phases = _build_month_phase_cards(event_cards, forecast_window, status)
    status_summary = _build_month_status_summary(status)
    central_task = _build_month_central_task(status)
    semantic_layer = build_month_forecast_semantic_layer(
        status=status,
        event_cards=event_cards,
        phases=phases,
        status_summary=status_summary,
        central_task=central_task,
    )
    campaign_arc = _build_month_campaign_arc(semantic_layer, phases)

    return {
        "client": {
            "gender": client.get("gender"),
            "report_type": client.get("report_type"),
            "birth_time_known": client.get("birth_time_known", True),
        },
        "forecast_window": forecast_window,
        "month_forecast_data": {
            "month_label": _format_month_window_label(forecast_window),
            "status": status,
            "status_label": status,
            "tension_index": month_data.get("tension_index"),
            "key_events": key_events[:10],
            "status_summary": status_summary,
            "central_task": central_task,
            "event_cards": [
                {
                    "date_label": card.get("date_label"),
                    "event": card.get("event"),
                    "kind": card.get("kind"),
                    "life_signal": card.get("life_signal"),
                    "pressure": card.get("pressure"),
                }
                for card in event_cards
            ],
            "phases": phases,
            "semantic_layer": semantic_layer,
            "campaign_arc": campaign_arc,
            "lunations": month_data.get("lunations", [])[:3],
            "ingresses": month_data.get("ingresses", [])[:4],
            "major_transits": month_data.get("major_transits", [])[:6],
            "retrogrades": month_data.get("retrogrades", [])[:3],
        },
    }
# END_BLOCK: MONTH_PROMPT_CONTEXT

# START_BLOCK: MONTH_FORECAST_RENDERING
def _normalize_month_llm_text(value: Any) -> str:
    raw = cleanup_content_artifacts(str(value or "")).strip()
    if not raw:
        return ""
    raw = re.sub(r"\s+", " ", raw).strip()
    lowered = raw.lower()
    if "ошибка генерации" in lowered or "авто-режим" in lowered:
        return ""
    if any(
        token in lowered
        for token in (
            "новые возможности",
            "важные дела",
            "важные планы",
            "избегай конфликтов",
            "не переутомляйся",
            "используй энергию",
            "энергия планет",
            "успех и гармония",
            "общий фон месяца",
        )
    ):
        return ""
    if len(raw) < 45:
        return ""
    if len(raw) > 360:
        sentences = re.split(r"(?<=[.!?])\s+", raw)
        raw = " ".join(sentences[:3]).strip() or raw[:360].rstrip()
    return raw


def _extract_month_forecast_llm_fragments(content: Any) -> dict[str, str]:
    blocks = _parse_json_block_list(content)
    if not blocks:
        return {"status_content": "", "strategy_text": "", "practical_text": ""}

    status_content = ""
    strategy_text = ""
    practical_text = ""
    active_header = ""

    for block in blocks:
        block_type = str(block.get("type") or "").strip()
        if block_type == "header":
            active_header = str(block.get("text") or "").strip().lower()
            continue
        if block_type == "callout":
            candidate = _normalize_month_llm_text(block.get("content"))
            title = str(block.get("title") or "").strip().lower()
            if candidate and (not status_content or "статус" in title):
                status_content = candidate
            if candidate and "практич" in title and not practical_text:
                practical_text = candidate
            continue
        if block_type != "paragraph":
            continue
        candidate = _normalize_month_llm_text(block.get("text"))
        if not candidate:
            continue
        if not strategy_text and "стратег" in active_header:
            strategy_text = candidate
            continue
        if not strategy_text:
            strategy_text = candidate

    return {
        "status_content": status_content,
        "strategy_text": strategy_text,
        "practical_text": practical_text,
    }


def _render_month_forecast_content(context: dict[str, Any], llm_content: Optional[str] = None) -> str:
    month_data = (context or {}).get("month_forecast_data") or {}
    status = str(month_data.get("status") or "YELLOW").upper()
    month_label = str(month_data.get("month_label") or "").strip()
    event_cards = [item for item in (month_data.get("event_cards") or []) if isinstance(item, dict)]
    phases = [item for item in (month_data.get("phases") or []) if isinstance(item, dict)]
    semantic_layer = month_data.get("semantic_layer")
    if not isinstance(semantic_layer, dict) or not semantic_layer:
        semantic_layer = build_month_forecast_semantic_layer(
            status=status,
            event_cards=event_cards,
            phases=phases,
            status_summary=str(month_data.get("status_summary") or "").strip(),
            central_task=str(month_data.get("central_task") or "").strip(),
        )
    campaign_arc = month_data.get("campaign_arc")
    if not isinstance(campaign_arc, dict) or not campaign_arc:
        campaign_arc = _build_month_campaign_arc(semantic_layer, phases)
    key_events = [
        " - ".join(
            part
            for part in [
                str(item.get("date_label") or "").strip(),
                str(item.get("event") or "").strip(),
                str(item.get("life_signal") or "").strip(),
            ]
            if part
        )
        for item in event_cards
        if str(item.get("event") or "").strip()
    ]

    status_content = _join_sentence_parts(
        str(semantic_layer.get("headline") or "").strip(),
        str(campaign_arc.get("opening_scene") or "").strip(),
        str(month_data.get("central_task") or semantic_layer.get("practical_move") or "").strip(),
    )

    strategy_text = _join_sentence_parts(
        str(campaign_arc.get("phase_sequence") or semantic_layer.get("campaign_shape") or "").strip(),
        str(semantic_layer.get("money_admin_focus") or "").strip(),
        str(semantic_layer.get("relationship_softness") or "").strip(),
    )

    finance_value = _merge_week_text(
        _upper_first(str(semantic_layer.get("money_admin_focus") or "").strip()),
        {
            "RED": "Любая срочность требует повторной проверки цены и обязательств.",
            "YELLOW": "Сначала назови условия и объем, потом соглашайся на ход.",
            "GREEN": "Рост приходит через уже собранную идею, а не через азарт.",
        }.get(status, ""),
    )
    relationship_value = _merge_week_text(
        _upper_first(str(semantic_layer.get("relationship_softness") or "").strip()),
        {
            "RED": "Резкая реакция в этом месяце обходится слишком дорого.",
            "YELLOW": "Лучше один честный разговор, чем длинная серия домыслов.",
            "GREEN": "Контакт укрепляется там, где совпадают тон, ритм и намерение.",
        }.get(status, ""),
    )
    energy_value = _merge_week_text(
        _upper_first(str(semantic_layer.get("rest") or "").strip()),
        {
            "RED": "Не строй весь месяц на одном всплеске.",
            "YELLOW": "Ритм с паузами работает лучше аварийного героизма.",
            "GREEN": "Хороший темп нужно удерживать режимом, а не эйфорией.",
        }.get(status, ""),
    )
    practical_text = _join_sentence_parts(
        str(semantic_layer.get("practical_move") or "").strip(),
        str(campaign_arc.get("close_focus") or "").strip(),
    )

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "level": 2,
            "text": f"📅 ПРОГНОЗ НА МЕСЯЦ{f' ({month_label})' if month_label else ''}",
        },
        {
            "type": "callout",
            "variant": _normalize_status_variant(status),
            "title": "СТАТУС МЕСЯЦА",
            "content": status_content,
        },
        {"type": "header", "level": 2, "text": "Ключевые события"},
        {
            "type": "list",
            "items": key_events[:8]
            or [
                "Без крупных внешних разворотов: месяц будет проявляться через темп, повседневные решения и то, как ты держишь главный приоритет."
            ],
            "ordered": False,
        },
        {"type": "header", "level": 2, "text": "Стратегия по неделям"},
        {"type": "paragraph", "text": strategy_text},
    ]

    for phase in phases[:4]:
        role = str(phase.get("phase_role") or "").strip()
        header_text = f"{phase.get('label')} ({phase.get('date_range_label')})"
        if role:
            header_text = f"{phase.get('label')}. {role} ({phase.get('date_range_label')})"
        blocks.append({"type": "header", "level": 3, "text": header_text})
        phase_paragraph = " ".join(
            part
            for part in [
                str(phase.get("transition_hint") or "").strip(),
                str(phase.get("scene_hint") or "").strip(),
            ]
            if part
        )
        if phase_paragraph:
            blocks.append({"type": "paragraph", "text": phase_paragraph})
        blocks.append(
            {
                "type": "list",
                "items": [
                    f"**Фокус:** {phase.get('focus_hint') or 'Держи одну центральную линию и не распыляйся.'}",
                    f"**Что продвигать:** {phase.get('push_hint') or 'Продвигай только то, что дает реальный ход.'}",
                    f"**Где не форсировать:** {phase.get('restraint_hint') or 'Не ускоряй то, что еще не прошло проверку.'}",
                ],
                "ordered": False,
            }
        )

    blocks.extend(
        [
            {"type": "header", "level": 2, "text": "Итог месяца"},
            {
                "type": "key_value",
                "items": [
                    {"key": "Финансы", "value": finance_value},
                    {"key": "Отношения", "value": relationship_value},
                    {"key": "Энергия", "value": energy_value},
                ],
            },
            {
                "type": "callout",
                "variant": "success",
                "title": "Практический ход",
                "content": practical_text,
            },
        ]
    )
    return json.dumps(blocks, ensure_ascii=False)
# END_BLOCK: MONTH_FORECAST_RENDERING
