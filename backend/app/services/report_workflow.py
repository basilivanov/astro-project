# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW
# ROLE: Domain service for report generation pipeline.
# DEPENDENCIES: stellium_engine.py, backend/app/models.py, backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [WORKFLOW_UTILS, WORKFLOW_CONTEXT, WORKFLOW_CHART, WORKFLOW_SECTIONS, WORKFLOW_MARKDOWN, WORKFLOW_GENERATION]
# ############################################################################

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
import os
import copy
import re
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session
import structlog

from stellium_engine import StelliumEngine

from .. import engine_utils

from ..engine_utils import normalize_datetime_input

from ..llm.orchestrator import (
    LLMClient,
    LLMContentValidationError,
    LLMOrchestrator,
    OpenRouterClient,
    SectionResult,
    SectionSpec,
)
from ..llm.validator import validate_llm_hallucinations
from ..horary.core import HoraryCore
from ..horary.adapters import detect_adapter
from ..models import Report, ReportChunk, ReportRun, User
from ..reporting.markdown_reporter import ReportSection, assemble_markdown
from ..reporting.section_templates import get_default_sections
from ..reporting.static_content import SECTION_INTROS
from ..reporting.markdown_helpers import (
    format_planet_table, 
    format_technical_appendix, 
    format_house_context, 
    format_horary_technical_data,
    format_chart_facts,
    get_chart_facts_json
)
from .notification import send_bot_notification

logger = structlog.get_logger()

PLANET_EMOJI_MAP = {
    "Солнце": "☀️",
    "Луна": "🌙",
    "Меркурий": "☿",
    "Венера": "♀️",
    "Марс": "♂️",
    "Юпитер": "♃",
    "Сатурн": "♄",
    "Уран": "♅",
    "Нептун": "♆",
    "Плутон": "♇",
    "Хирон": "⚷",
    "Лилит": "⚸",
    "Селена": "🌟",
    "Северный узел": "☊",
    "Южный узел": "☋",
    "Sun": "☀️",
    "Moon": "🌙",
    "Mercury": "☿",
    "Venus": "♀️",
    "Mars": "♂️",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
    "Chiron": "⚷",
    "Lilith": "⚸",
    "Selena": "🌟",
    "North Node": "☊",
    "South Node": "☋",
}

RU_SIGNS = {
    "Aries": "Овен ♈", "Taurus": "Телец ♉", "Gemini": "Близнецы ♊", "Cancer": "Рак ♋",
    "Leo": "Лев ♌", "Virgo": "Дева ♍", "Libra": "Весы ♎", "Scorpio": "Скорпион ♏",
    "Sagittarius": "Стрелец ♐", "Capricorn": "Козерог ♑", "Aquarius": "Водолей ♒", "Pisces": "Рыбы ♓"
}

RU_PLANETS_FULL = {
    "Sun": "☀️ Солнце", "Moon": "🌙 Луна", "Mercury": "☿ Меркурий", "Venus": "♀️ Венера",
    "Mars": "♂️ Марс", "Jupiter": "♃ Юпитер", "Saturn": "♄ Сатурн", "Uranus": "♅ Уран",
    "Neptune": "♆ Нептун", "Pluto": "♇ Плутон", "Chiron": "⚷ Хирон", "Lilith": "⚸ Лилит",
    "Selena": "🌟 Селена", "North Node": "☊ Сев. Узел", "South Node": "☋ Южн. Узел",
    "Mean Apogee": "⚸ Лилит", "True Node": "☊ Сев. Узел", "Part of Fortune": "⊗ Парс Фортуны",
    "ASC": "⬆️ ASC", "MC": "🏔️ MC", "DSC": "⬇️ DSC", "IC": "🏠 IC", "Vertex": "✴️ Вертекс",
    "Ceres": "Церера", "Pallas": "Паллада", "Juno": "Юнона", "Vesta": "Веста"
}


def _clean_text_artifacts(text: str) -> str:
    """Internal text cleaner."""
    if not text:
        return ""

    # 1. Fix L-tokens (L 1, L 10)
    text = re.sub(r'\b([Ll])\s+(\d+)\b', r'\1\2', text)
    
    # 2. Fix Fractions "8 / 10" -> "8/10"
    text = re.sub(r'(\d)\s+/\s+(\d)', r'\1/\2', text)
    
    # 3. Fix Date Dots "27 . 01" -> "27.01"
    text = re.sub(r'(\d)\s+\.\s+(\d)', r'\1.\2', text)
    
    # 4. Fix Double Spaces (except newlines)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # 4.1 Normalize line-leading bullets
    text = re.sub(r'(?m)^\s*[•●▪▫◦]\s+', '- ', text)
    text = re.sub(r'(?m)^\s*[–—]\s+', '- ', text)

    # 4.2 Normalize recommendations heading
    text = re.sub(
        r'(?m)^\s*#{2,4}\s+.*рекомендации.*$',
        '### 💡 Рекомендации',
        text,
        flags=re.IGNORECASE,
    )

    # 5. Fix inline bullets
    def replace_bullet(match):
        return f"\n- {match.group(1)}"
    text = re.sub(r'(?<!^)(?<!\n)\s*[•●]\s*(.+?)(?=[•●\n]|$)', replace_bullet, text)

    return text.strip()


def _inject_emojis_text(text: str) -> str:
    """Internal emoji injector."""
    for name, emoji in PLANET_EMOJI_MAP.items():
        escaped = re.escape(name)
        pattern = rf"(?<!{re.escape(emoji)}\s)(?<!{re.escape(emoji)})\b{escaped}\b"
        text = re.sub(pattern, f"{emoji} {name}", text)
    return text


def _process_json_recursively(data: Any, processors: List[callable]) -> Any:
    if isinstance(data, str):
        res = data
        for p in processors:
            res = p(res)
        return res
    if isinstance(data, list):
        return [_process_json_recursively(item, processors) for item in data]
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Process text fields
            if k in {"text", "content", "title", "key", "value", "header", "description"}:
                new_dict[k] = _process_json_recursively(v, processors)
            # Recurse into containers
            elif k in {"items", "rows", "columns"}:
                new_dict[k] = _process_json_recursively(v, processors)
            else:
                new_dict[k] = v
        return new_dict
    return data


def cleanup_content_artifacts(text: str) -> str:
    """
    # PURPOSE: Fix common LLM formatting artifacts (JSON-aware).
    """
    if not text:
        return ""
    
    # Try JSON
    try:
        if text.strip().startswith("["):
            blocks = json.loads(text)
            processed = _process_json_recursively(blocks, [_clean_text_artifacts])
            return json.dumps(processed, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        pass
        
    return _clean_text_artifacts(text)


def inject_planet_emojis(content: str) -> str:
    """
    # PURPOSE: Ensure planet names include emoji prefixes (JSON-aware).
    """
    if not content:
        return ""
        
    # Try JSON
    try:
        if content.strip().startswith("["):
            blocks = json.loads(content)
            # Apply clean then inject
            processed = _process_json_recursively(
                blocks, 
                [_clean_text_artifacts, _inject_emojis_text]
            )
            return json.dumps(processed, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        pass
        
    # Fallback text
    txt = _clean_text_artifacts(content)
    return _inject_emojis_text(txt)


# #START_BLOCK_WORKFLOW_UTILS
def build_forecast_window(report_type: str, tz_str: str = "UTC") -> dict:
    """
    # PURPOSE: Build forecast window metadata for prompts.
    # INPUT: report_type (str), tz_str (str).
    # OUTPUT: Dict with window fields (start in local time).
    # CONTEXT: Used in report context for forecasts.
    """
    try:
        tz = ZoneInfo(tz_str)
    except:
        tz = timezone.utc

    # Start from local "now"
    start_dt = datetime.now(tz)
    start = start_dt.isoformat()
    
    if report_type == "week_forecast":
        return {"start": start, "days": 7}
    if report_type == "month_forecast":
        return {"start": start, "months": 1}
    if report_type == "year_forecast":
        return {"start": start, "months": 12}
    if report_type == "ten_year_forecast":
        return {"start": start, "months": 120}
    return {"start": start, "months": 12}


def start_report_run(report: Report, db: Session) -> ReportRun:
    """
    # PURPOSE: Create a report run record for observability.
    # INPUT: report, db session.
    # OUTPUT: ReportRun instance.
    # CONTEXT: Used by workflow entrypoints before generation.
    """

    run = ReportRun(
        report_id=report.id,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def should_fallback_on_llm_error(exc: Exception) -> bool:
    """
    # PURPOSE: Decide whether to use fallback content for an LLM error.
    # INPUT: exception from LLM call.
    # OUTPUT: True if fallback should be used.
    # CONTEXT: Keeps report generation resilient to credit/network issues.
    """

    message = str(exc)
    return any(
        token in message
        for token in (
            "OpenRouter error:",
            "OpenRouter connection error",
            "CLI error:",
            "CLI timeout",
        )
    )


def build_section_fallback_content(spec: SectionSpec) -> str:
    """
    # PURPOSE: Provide a user-friendly fallback body for a failed section.
    # INPUT: section spec.
    # OUTPUT: JSON string (error block).
    # CONTEXT: Used when LLM credits/network errors occur.
    """
    
    error_block = {
        "type": "callout",
        "variant": "error",
        "title": "Ошибка генерации",
        "content": (
            f"Не удалось сформировать раздел **{spec.title}**.\n"
            "Пожалуйста, повторите попытку позже или обратитесь в поддержку."
        )
    }
    
    # Try to provide more specific structure if possible
    # But for a hard fallback, a simple error block is safest and complies with JSON.
    return json.dumps([error_block], ensure_ascii=False)


def build_section_template_content(spec: SectionSpec) -> str:
    """
    # PURPOSE: Provide a low-cost local template for test-mode generation (JSON Blocks).
    # INPUT: section spec.
    # OUTPUT: JSON string (list of blocks).
    # CONTEXT: Used when LLM calls are disabled for tests.
    """

    blocks = []

    if spec.section_id == "month_theme":
        blocks.extend([
            {
                "type": "header",
                "level": 3,
                "text": "Март 2026: Лабиринт с подсказками"
            },
            {
                "type": "key_value",
                "items": [
                    {"key": "Период", "value": "01.03.2026 - 31.03.2026"},
                    {"key": "Локация", "value": "Москва"},
                    {"key": "Метод", "value": "Транзиты"}
                ]
            },
            {
                "type": "callout",
                "variant": "warning",
                "title": "Статус месяца",
                "content": "Светофор: 🟡 Желтый. Цена ошибок: Высокая. Действуй по плану, оставляя люфт."
            },
            {
                "type": "paragraph",
                "text": "Месяц похож на лабиринт: движения много, но вектор неочевиден. Главная задача — не терять ритм и проверять карту."
            },
            {
                "type": "header", 
                "level": 3,
                "text": "Главные активаторы"
            },
            {
                "type": "list",
                "style": "bullet",
                "items": [
                    "Марс (секстиль) → Импульс в работе",
                    "Сатурн (соединение) → Проверка дисциплины",
                    "Венера (квадрат) → Напряжение в чувствах"
                ]
            }
        ])
    else:
        title = spec.title.strip()
        blocks.extend([
            {
                "type": "header",
                "level": 3,
                "text": f"🧭 О чем этот блок: {title}"
            },
            {
                "type": "paragraph",
                "text": f"{title} раскрывает ключевые процессы и фокус внимания. Здесь важно отметить динамику и зоны роста."
            },
            {
                "type": "table",
                "columns": [
                    {"header": "Параметр", "width": "30%"},
                    {"header": "Содержание", "width": "70%"}
                ],
                "rows": [
                    ["Фокус", "Основные задачи и акценты"],
                    ["Ресурс", "Сильные стороны и опоры"],
                    ["Риск", "Слепые зоны и напряжение"]
                ]
            },
            {
                "type": "callout",
                "variant": "info",
                "title": "Тезис",
                "content": "Настройка этого блока дает устойчивую опору и ясный вектор."
            },
            {
                "type": "header",
                "level": 3,
                "text": "💡 Рекомендации"
            },
            {
                "type": "list",
                "style": "bullet",
                "items": [
                    "Сформулируйте 1-2 практичных шага.",
                    "Отмечайте сигналы и фиксируйте наблюдения."
                ]
            }
        ])

    return json.dumps(blocks, ensure_ascii=False)


def resolve_llm_retry_attempts() -> int:
    """
    # PURPOSE: Resolve retry attempts for structural validation failures.
    # INPUT: None.
    # OUTPUT: Retry count (>=1).
    # CONTEXT: Used before switching to fallback model.
    """

    raw = os.getenv("OPENROUTER_RETRY_ATTEMPTS", "3").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 3
    return max(1, value)


def resolve_llm_fallback_model() -> str:
    """
    # PURPOSE: Resolve fallback OpenRouter model name.
    # INPUT: None.
    # OUTPUT: Model name string (empty means disabled).
    # CONTEXT: Used when primary model fails structural validation.
    """

    model = os.getenv(
        "OPENROUTER_FALLBACK_MODEL", "anthropic/claude-4.5-sonnet"
    ).strip()
    return model


def resolve_primary_model(report_type: Optional[str]) -> str:
    """
    # PURPOSE: Pick a primary OpenRouter model based on report type.
    # INPUT: report_type (str | None).
    # OUTPUT: Model name string.
    # CONTEXT: Used to route expensive vs. cheap models per product.
    """

    report_key = (report_type or "").strip().lower()
    if report_key.startswith("natal"):
        model = os.getenv("OPENROUTER_MODEL_NATAL", "").strip()
    elif "forecast" in report_key:
        model = os.getenv("OPENROUTER_MODEL_FORECAST", "").strip()
    elif "horary" in report_key:
        model = os.getenv("OPENROUTER_MODEL_HORARY", "").strip()
    elif "synastry" in report_key:
        model = os.getenv("OPENROUTER_MODEL_SYNASTRY", "").strip()
    else:
        model = ""

    if model:
        return model

    return os.getenv(
        "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
    ).strip()


def resolve_llm_concurrency(llm_mode: str) -> int:
    mode = (llm_mode or "").strip().lower()
    if mode in {"cli", "gemini", "codex"}:
        env_name = "LLM_CLI_CONCURRENCY"
        default = 3
    else:
        env_name = "LLM_CONCURRENCY"
        default = 10

    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def generate_section_with_retries(
    spec: SectionSpec,
    context: Dict[str, Any],
    *,
    primary_client: LLMClient,
    fallback_model: str,
    max_attempts: int,
) -> SectionResult:
    """
    # PURPOSE: Generate a section with retries + fallback model on bad structure or hallucinations.
    # INPUT: spec, context, primary client, fallback model, max attempts.
    # OUTPUT: SectionResult.
    """

    last_error: Optional[Exception] = None
    orchestrator = LLMOrchestrator(primary_client)
    facts = context.get("facts")

    for attempt in range(max_attempts):
        try:
            result = orchestrator.generate_sections([spec], context=context)[0]
            
            # HALLUCINATION VALIDATION
            content = result.content or ""
            if facts and ("[" in content and "]" in content):
                try:
                    clean = content.strip()
                    if clean.startswith("```json"): clean = clean[7:]
                    elif clean.startswith("```"): clean = clean[3:]
                    if clean.endswith("```"): clean = clean[:-3]
                    
                    blocks = json.loads(clean.strip())
                    if isinstance(blocks, list):
                        errors = validate_llm_hallucinations(blocks, facts)
                        if errors:
                            msg = "; ".join(errors)
                            logger.warning("report.section.hallucination", section_id=spec.section_id, errors=msg)
                            raise LLMContentValidationError(f"Hallucination control failed: {msg}")
                except json.JSONDecodeError:
                    pass 
            
            return result

        except LLMContentValidationError as exc:
            last_error = exc
            logger.warning(
                "report.section.retry",
                block_id="REPORT_SECTION",
                section_id=spec.section_id,
                attempt=attempt + 1,
                max_attempts=max_attempts,
                error=str(exc),
            )
            continue
        except Exception as exc:
            last_error = exc
            logger.warning(
                "report.section.retry",
                block_id="REPORT_SECTION",
                section_id=spec.section_id,
                attempt=attempt + 1,
                max_attempts=max_attempts,
                error=str(exc),
            )
            continue

    if fallback_model and isinstance(primary_client, OpenRouterClient):
        fallback_client = OpenRouterClient.from_env(model_override=fallback_model)
        fallback_orchestrator = LLMOrchestrator(fallback_client)
        return fallback_orchestrator.generate_sections([spec], context=context)[0]

    if last_error:
        raise last_error
    raise LLMContentValidationError("content validation failed")


def finish_report_run(
    run: Optional[ReportRun],
    db: Session,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """
    # PURPOSE: Finalize a report run record with status and timestamps.
    # INPUT: run, db session, status, optional error_message.
    # OUTPUT: None.
    # CONTEXT: Used after report generation completes or fails.
    """

    if not run:
        return
    run.status = status
    run.error_message = error_message
    run.finished_at = datetime.now(timezone.utc)
    db.commit()


def build_section_specs(payload: Any) -> List[SectionSpec]:
    """
    # PURPOSE: Resolve section specs from payload or defaults.
    # INPUT: payload (ReportWorkflowRequest-like).
    # OUTPUT: List[SectionSpec].
    # CONTEXT: Used by report workflow services.
    """

    if getattr(payload, "sections", None):
        return [
            SectionSpec(
                section_id=section.section_id,
                title=section.title,
                prompt=section.prompt,
            )
            for section in payload.sections
        ]
    return get_default_sections(payload.report_type)


def load_section_specs_for_report(report: Report, payload_data: Optional[dict]) -> List[SectionSpec]:
    """
    # PURPOSE: Resolve section specs for a report without raising errors.
    # INPUT: report, payload_data (dict|None).
    # OUTPUT: List[SectionSpec].
    # CONTEXT: Used when markdown/PDF are requested without payload.
    """

    if payload_data:
        try:
            payload = payload_data
            if isinstance(payload_data, dict):
                class PayloadShim:
                    def __init__(self, data: dict) -> None:
                        self.sections = data.get("sections")
                        self.report_type = data.get("report_type", report.report_type)

                payload = PayloadShim(payload_data)
            return build_section_specs(payload)
        except Exception as exc:
            logger.error(
                "report.payload.invalid",
                block_id="REPORT_PAYLOAD",
                report_id=str(report.id),
                error=str(exc),
            )
    return get_default_sections(report.report_type)
# #END_BLOCK_WORKFLOW_UTILS


# #START_BLOCK_WORKFLOW_CHART
def build_chart_data(payload: Any) -> dict:
    """
    # PURPOSE: Calculate chart data for report context.
    # INPUT: payload (ReportWorkflowRequest-like).
    # OUTPUT: Serialized chart dict.
    # CONTEXT: Used by report generation prompts.
    """

    engine = StelliumEngine()
    house_system = engine_utils.resolve_house_system(payload.house_system)

    # 1. Resolve Location (Prefer coordinates)
    loc_input = payload.birth_location
    tz_str = payload.birth_timezone
    
    current_lat = payload.birth_lat
    
    if payload.birth_lat is not None and payload.birth_lon is not None:
        loc_input = {
            "latitude": payload.birth_lat,
            "longitude": payload.birth_lon,
            "name": payload.birth_location or payload.client_name or "Unknown",
            "timezone": tz_str
        }
        current_lat = payload.birth_lat

    # Force Whole Sign for high latitudes to avoid SwissEph crash
    if current_lat is not None and abs(current_lat) >= 60.0:
        from stellium.engines.houses import WholeSignHouses
        house_system = WholeSignHouses()

    # 2. Resolve Time
    clean_date = ""
    if payload.report_type in ["horary", "horary_answer"]:
        # Horary: Use NOW. Try to find local timezone if coords available.
        now_utc = datetime.now(timezone.utc)
        if payload.birth_lat and payload.birth_lon:
            try:
                from timezonefinder import TimezoneFinder
                tf = TimezoneFinder()
                found_tz = tf.timezone_at(lng=payload.birth_lon, lat=payload.birth_lat)
                if found_tz:
                    tz_str = found_tz
            except ImportError:
                pass
            except Exception:
                pass
        
        # Format current time according to target TZ (or UTC if none)
        # normalize_datetime_input handles conversion if tz_str is passed
        clean_date = normalize_datetime_input(now_utc.isoformat(), tz_str)
    else:
        # Natal/Forecast: Use Birth Date
        clean_date = normalize_datetime_input(payload.birth_date, tz_str, assume_local=False)

    try:
        chart = engine.create_natal_chart(
            payload.client_name,
            clean_date,
            loc_input,
            house_system,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Chart error: {exc}"
        ) from exc

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(chart, orb=payload.fixed_star_orb)
        
    aspects = engine.find_natal_aspects(chart)
    patterns = engine.find_all_patterns(chart)
    
    extra_points = []
    try:
        selena_lon = engine.calculate_selena(chart.datetime.julian_day)
        extra_points.append({"name": "Selena", "longitude": selena_lon})
    except: pass
    
    try:
        pars_lon = engine.calculate_pars_fortuna(chart)
        extra_points.append({"name": "Part of Fortune", "longitude": pars_lon})
    except: pass

    chart_dict = engine_utils.serialize_chart(
        chart, 
        chart_type="natal", 
        fixed_stars=stars,
        aspects=aspects,
        patterns=patterns,
        extra_points=extra_points
    )
    
    if payload.report_type in ["horary", "horary_answer"]:
        q_text = getattr(payload, "question", "") or getattr(payload, "client_note", "") or ""
        adapter_id = detect_adapter(q_text)
        logger.info("horary.adapter.detect", adapter=adapter_id, question=q_text[:50])
        
        horary_core = HoraryCore(engine)
        chart_dict["horary"] = horary_core.analyze(chart, adapter_id)

    if payload.report_type == "solar_return":
        try:
            # Default to current year or next depending on birth date vs now
            now = datetime.now(timezone.utc)
            # If birthday hasn't happened yet this year, SR is last year's. 
            # Or usually we want the "active" SR.
            # Simplified: Use current calendar year.
            target_year = now.year
            sr_chart = engine.calculate_solar_return_chart(chart, target_year, payload.birth_location or "Greenwich")
            chart_dict["solar_return"] = engine_utils.serialize_chart(sr_chart, "solar_return")
        except Exception as e:
            logger.error("solar_return.calc.error", error=str(e))

    if payload.report_type == "synastry":
        try:
            p_dt = normalize_datetime_input(
                payload.partner_birth_date,
                payload.partner_birth_timezone,
                assume_local=False,
            )
            p_loc = payload.partner_birth_location
            if payload.partner_birth_lat and payload.partner_birth_lon:
                p_loc = {
                    "latitude": payload.partner_birth_lat,
                    "longitude": payload.partner_birth_lon,
                    "name": payload.partner_birth_location or "Partner Loc"
                }
            
            p_chart = engine.create_natal_chart(payload.partner_name or "Partner", p_dt, p_loc or "Unknown")
            chart_dict["partner_chart"] = engine_utils.serialize_chart(p_chart, "natal")
            chart_dict["synastry"] = engine.calculate_synastry_data(chart, p_chart)
        except Exception as e:
            logger.error("synastry.calc.error", error=str(e))
        
    return chart_dict
# #END_BLOCK_WORKFLOW_CHART


def infer_gender(full_name: str) -> str:
    """Simple heuristic for Russian names."""
    name = full_name.strip().split()[0].lower() # Take first name
    if name.endswith(('а', 'я')): return "female"
    return "male"

# #START_BLOCK_WORKFLOW_CONTEXT
def build_report_context(payload: Any, chart_data: dict) -> dict:
    """
    # PURPOSE: Build the LLM prompt context for report generation.
    # INPUT: payload (ReportWorkflowRequest-like), chart_data (dict).
    # OUTPUT: Context dict for LLM.
    # CONTEXT: Used by the LLM orchestrator.
    """
    
    # Determine forecast timezone (current location > birth location > UTC)
    forecast_tz = (
        payload.solar_current_timezone 
        or payload.birth_timezone 
        or "UTC"
    )
    
    forecast_window = build_forecast_window(payload.report_type, forecast_tz)
    
    # Clean client name (remove text in parentheses)
    clean_name = payload.client_name
    clean_name = re.sub(r'\s*\(.*?\)', '', clean_name)
    clean_name = re.sub(r'\s*\[.*?\]', '', clean_name)
    clean_name = clean_name.strip()
    logger.info("context.client_name.cleaned", original=payload.client_name, cleaned=clean_name)
    
    # Inferred gender
    gender = infer_gender(clean_name)
    
    # Base context
    display_birth_date = payload.birth_date
    if (
        payload.birth_date
        and payload.birth_timezone
        and payload.report_type not in ["horary", "horary_answer"]
    ):
        display_birth_date = normalize_datetime_input(
            payload.birth_date,
            payload.birth_timezone,
            assume_local=False,
        )

    display_partner_birth_date = payload.partner_birth_date
    if payload.partner_birth_date and payload.partner_birth_timezone:
        display_partner_birth_date = normalize_datetime_input(
            payload.partner_birth_date,
            payload.partner_birth_timezone,
            assume_local=False,
        )

    context = {
        "client": {
            "name": clean_name,
            "gender": "женский" if gender == "female" else "мужской",
            "note": payload.client_note,
            "question": getattr(payload, "question", None) or payload.client_note,
            "birth_date": display_birth_date,
            "birth_location": payload.birth_location,
            "birth_lat": payload.birth_lat,
            "birth_lon": payload.birth_lon,
            "birth_timezone": payload.birth_timezone,
            "birth_place_id": payload.birth_place_id,
            "report_type": payload.report_type,
        },
        "partner": {
            "name": payload.partner_name,
            "birth_date": display_partner_birth_date,
            "birth_location": payload.partner_birth_location,
            "birth_lat": payload.partner_birth_lat,
            "birth_lon": payload.partner_birth_lon,
            "birth_timezone": payload.partner_birth_timezone,
            "birth_place_id": payload.partner_birth_place_id,
        },
        "solar": {
            "current_location": payload.solar_current_location,
            "current_lat": payload.solar_current_lat,
            "current_lon": payload.solar_current_lon,
            "current_timezone": payload.solar_current_timezone,
            "current_place_id": payload.solar_current_place_id,
            "next_location": payload.solar_next_location,
            "next_lat": payload.solar_next_lat,
            "next_lon": payload.solar_next_lon,
            "next_timezone": payload.solar_next_timezone,
            "next_place_id": payload.solar_next_place_id,
        },
        "forecast_window": forecast_window,
        "chart": chart_data,
        "facts": get_chart_facts_json(chart_data)
    }

    # Inject detailed forecast data
    if payload.report_type in ["year_forecast", "week_forecast", "month_forecast", "ten_year_forecast"]:
        try:
            engine = StelliumEngine()
            house_system = engine_utils.resolve_house_system(payload.house_system)
            
            clean_birth_date = payload.birth_date
            if "+" in clean_birth_date:
                clean_birth_date = clean_birth_date.split("+")[0]
            
            location_input = payload.birth_location
            if payload.birth_lat is not None and payload.birth_lon is not None:
                location_input = {
                    "latitude": payload.birth_lat,
                    "longitude": payload.birth_lon,
                    "name": payload.birth_location or payload.client_name,
                }
                
            natal_chart = engine.create_natal_chart(
                payload.client_name,
                clean_birth_date,
                location_input,
                house_system,
            )
            
            forecast_loc = payload.solar_current_location or payload.birth_location
            
            if payload.report_type == "year_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                    target_year = start_dt.year
                except:
                    target_year = datetime.now(timezone.utc).year
                    
                context["year_forecast_data"] = engine.calculate_forecast_year_data(
                    natal_chart,
                    target_year,
                    forecast_loc
                )
                
            elif payload.report_type == "week_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                except:
                    start_dt = datetime.now(timezone.utc)
                    
                context["week_forecast_data"] = engine.calculate_forecast_week_data(
                    natal_chart,
                    start_dt,
                    forecast_loc
                )
                
            elif payload.report_type == "month_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                except:
                    start_dt = datetime.now(timezone.utc)
                    
                context["month_forecast_data"] = engine.calculate_forecast_month_data(
                    natal_chart,
                    start_dt,
                    forecast_loc
                )

            elif payload.report_type == "ten_year_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                    start_year = start_dt.year
                except:
                    start_year = datetime.now(timezone.utc).year
                    
                context["decade_forecast_data"] = engine.calculate_forecast_decade_data(
                    natal_chart,
                    start_year,
                    forecast_loc
                )

        except Exception as exc:
            logger.error("context.forecast.error", error=str(exc))
            
    return context
# #END_BLOCK_WORKFLOW_CONTEXT


# #START_BLOCK_WORKFLOW_SECTIONS
def initialize_report_chunks(
    report: Report,
    section_specs: List[SectionSpec],
    db: Session,
    reset: bool = False,
) -> dict:
    """
    # PURPOSE: Ensure chunk placeholders exist for each section.
    # INPUT: report, section_specs, db, reset flag.
    # OUTPUT: Dict[section_id, ReportChunk].
    # CONTEXT: Used before generation to show progress.
    """

    if reset:
        db.query(ReportChunk).filter(ReportChunk.report_id == report.id).delete()
        db.flush()

    chunks = {
        chunk.section: chunk
        for chunk in db.query(ReportChunk)
        .filter(ReportChunk.report_id == report.id)
        .all()
    }

    for index, spec in enumerate(section_specs):
        chunk = chunks.get(spec.section_id)
        if chunk:
            if reset:
                chunk.content = ""
                chunk.status = "pending"
                chunk.error_message = None
                chunk.error_at = None
            chunk.order_index = index
        else:
            chunk = ReportChunk(
                report_id=report.id,
                section=spec.section_id,
                content="",
                status="pending",
                order_index=index,
            )
            db.add(chunk)
        chunks[spec.section_id] = chunk

    return chunks
# #END_BLOCK_WORKFLOW_SECTIONS


async def generate_section_content(
    spec: SectionSpec,
    context: dict,
    chart_data: dict,
    llm_client: Optional[LLMClient],
    fallback_model: str,
    retry_attempts: int,
    use_template: bool
) -> str:
    logger.info("gen.content.check", block_id="REPORT_GEN", section_id=spec.section_id, title=spec.title)
    
    # 1. Static Overrides
    if spec.section_id == "input_frame":
        logger.info("gen.content.static", block_id="REPORT_GEN", section="input_frame")
        
        blocks = []
        
        # 1. Intro Callout
        intro_text = SECTION_INTROS.get("input_frame", "")
        if intro_text:
            blocks.append({
                "type": "callout",
                "variant": "info",
                "title": "Паспорт карты",
                "content": intro_text
            })
            
        # 2. Client Data
        c = context.get("client", {})
        
        # House System Localization
        hs_raw = str(chart_data.get("house_system") or "Placidus")
        if "Whole" in hs_raw: hs_display = "Цельнознаковая"
        elif "Placidus" in hs_raw: hs_display = "Плацидус"
        elif "Equal" in hs_raw: hs_display = "Равнодомная"
        elif "Koch" in hs_raw: hs_display = "Кох"
        elif "Regio" in hs_raw: hs_display = "Региомонтан"
        elif "Porph" in hs_raw: hs_display = "Порфирий"
        else: hs_display = hs_raw

        # Date Formatting
        tz = c.get("birth_timezone") or "UTC"
        display_date = c.get('birth_date') or "-"
        
        if display_date != "-":
            try:
                clean_iso = display_date.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_iso)
                if dt.tzinfo and tz != "UTC":
                    dt = dt.astimezone(ZoneInfo(tz))
                display_date = dt.strftime("%d.%m.%Y %H:%M")
                if tz == "UTC":
                    display_date = f"{display_date} (UTC)"
            except Exception:
                pass

        blocks.append({
            "type": "header",
            "level": 3,
            "text": "Данные рождения"
        })
        
        blocks.append({
            "type": "key_value",
            "items": [
                {"key": "Кверент", "value": c.get('name') or "Unknown"},
                {"key": "Дата", "value": display_date},
                {"key": "Место", "value": c.get('birth_location') or "-"},
                {"key": "Часовой пояс", "value": tz},
                {"key": "Дома", "value": hs_display}
            ]
        })
        
        # Check for High Latitude switch
        lat = c.get("birth_lat")
        if lat and abs(lat) >= 60.0 and "Whole" in str(hs_raw):
             blocks.append({
                "type": "callout",
                "variant": "warning",
                "title": "⚠️ Особенности расчета",
                "content": f"Место рождения находится в высоких широтах ({lat:.2f}°). Система домов автоматически переключена на «Полнознаковую» (Whole Sign), так как стандартная система Плацидус не работает корректно за полярным кругом."
            })

        # 3. Planets Table Preparation
        positions = chart_data.get("positions", [])
        
        angles_data = []
        planets_data = []
        
        for p in positions:
            name_raw = p["name"]
            if name_raw in ["RAMC", "Zero"]: continue
            
            name_ru = RU_PLANETS_FULL.get(name_raw, name_raw)
            sign_ru = RU_SIGNS.get(p["sign"], p["sign"])
            house = str(p.get("house", "-"))
            
            deg = int(p["sign_degree"])
            minute = int((p["sign_degree"] - deg) * 60)
            deg_str = f"{deg}°{minute:02d}'"
            
            retro = "R" if p.get("is_retrograde") else ""
            
            # Row: [Name, Sign, House, Degree, Retro]
            row = [name_ru, sign_ru, house, deg_str, retro]
            
            if name_raw in ["ASC", "MC", "DSC", "IC", "Vertex", "Part of Fortune"]:
                angles_data.append(row)
            else:
                planets_data.append(row)

        # 4. Render Tables
        if angles_data:
             blocks.append({
                "type": "header",
                "level": 3,
                "text": "Угловые точки"
            })
             # Angles usually don't have Retro, so we use 4 columns
             blocks.append({
                "type": "table",
                "columns": [
                    {"header": "Точка", "width": "35%"},
                    {"header": "Знак", "width": "25%"},
                    {"header": "Дом", "width": "15%", "align": "center"},
                    {"header": "Град.", "width": "25%", "align": "right", "nowrap": True}
                ],
                "rows": [row[:4] for row in angles_data]
            })

        if planets_data:
            blocks.append({
                "type": "header",
                "level": 3,
                "text": "Планеты"
            })
            
            has_retro = any(row[4] for row in planets_data)
            p_cols = [
                {"header": "Планета", "width": "35%"},
                {"header": "Знак", "width": "25%"},
                {"header": "Дом", "width": "15%", "align": "center"},
                {"header": "Град.", "width": "25%", "align": "right", "nowrap": True}
            ]
            
            final_rows = []
            if has_retro:
                p_cols.append({"header": "R", "width": "30px", "align": "center"})
                final_rows = planets_data # Keep all 5
            else:
                final_rows = [row[:4] for row in planets_data]

            blocks.append({
                "type": "table",
                "columns": p_cols,
                "rows": final_rows
            })
            
        return json.dumps(blocks, ensure_ascii=False)

    if spec.section_id == "horary_00_passport":
        logger.info("gen.content.static", section="horary_00_passport")
        c = context.get("client", {})
        question = c.get("question") or c.get("note") or "Вопрос не указан"
        dt_str = chart_data.get("datetime_local") or chart_data.get("datetime_utc")
        
        dt_display = dt_str
        try:
            if dt_str:
                if dt_str.endswith("Z"): dt_str = dt_str[:-1]
                dt_val = datetime.fromisoformat(dt_str)
                
                # Timezone conversion
                tz_name = chart_data.get("location", {}).get("timezone")
                if tz_name:
                    if dt_val.tzinfo is None:
                        dt_val = dt_val.replace(tzinfo=timezone.utc)
                    dt_val = dt_val.astimezone(ZoneInfo(tz_name))
                
                dt_display = dt_val.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass
            
        loc = chart_data.get("location", {}).get("name", "Неизвестно")
        
        blocks = [
            {"type": "header", "level": 2, "text": "Паспорт вопроса"},
            {
                "type": "key_value",
                "items": [
                    {"key": "Вопрос", "value": question},
                    {"key": "Дата и время", "value": dt_display},
                    {"key": "Место", "value": loc},
                ],
            },
        ]
        content = json.dumps(blocks, ensure_ascii=False)
        logger.info("gen.content.passport.result", content_len=len(content), content_preview=content[:50])
        return content

    if spec.section_id == "horary_00_technical":
        h = chart_data.get("horary", {})
        if not h:
             return json.dumps([{"type": "paragraph", "text": "_Нет данных хорара._"}], ensure_ascii=False)

        blocks = []
        
        # 1. Scenario
        adapter_name = h.get('adapter_name', 'Не определен')
        blocks.append({"type": "header", "level": 2, "text": f"🧩 Сценарий: {adapter_name}"})
        
        # 2. Roles
        roles = h.get("roles", {})
        if roles:
            blocks.append({"type": "header", "level": 3, "text": "🎭 Сигнификаторы (Роли)"})
            
            priority = ["querent", "quesited", "opponent", "judge", "law", "verdict", "money", "wallet", "fine", "profit", "job", "partner", "moon"]
            sorted_keys = sorted(roles.keys(), key=lambda k: priority.index(k) if k in priority else 99)
            
            role_names_ru = {
                "querent": "Кверент (Ты)", "quesited": "Квестит (Вопрос)", "opponent": "Оппонент",
                "judge": "Судья/Власть", "law": "Закон", "verdict": "Итог дела", "money": "Деньги",
                "wallet": "Твой кошелек", "fine": "Штраф/Потери", "profit": "Выгода",
                "job": "Работа", "partner": "Партнер", "moon": "Луна"
            }
            
            rows = []
            for key in sorted_keys:
                r = roles[key]
                role_name = role_names_ru.get(key, key.capitalize())
                planet = r.get('planet_ru', '-')
                house = str(r.get('house', '-'))
                desc = r.get('description', '')
                rows.append([role_name, planet, house, desc])
            
            blocks.append({
                "type": "table",
                "columns": [
                    {"header": "Роль", "width": "25%"},
                    {"header": "Планета", "width": "20%"},
                    {"header": "Дом", "width": "15%", "align": "center"},
                    {"header": "Описание", "width": "40%"}
                ],
                "rows": rows
            })

        # 3. Radicality
        rad = h.get("radicality", {})
        if rad:
            score = rad.get('score', '?')
            try:
                score_val = float(score)
            except: 
                score_val = 0
                
            blocks.append({"type": "rating", "value": score_val, "max": 10, "label": "🛡️ Радикальность"})
            
            issues = rad.get('issues', [])
            warnings = rad.get('warnings', [])
            
            if issues:
                blocks.append({
                    "type": "callout", 
                    "variant": "error", 
                    "title": "Проблемы радикальности",
                    "content": "\n".join([f"• {i}" for i in issues])
                })
            
            if warnings:
                blocks.append({
                    "type": "callout", 
                    "variant": "warning", 
                    "title": "Предупреждения",
                    "content": "\n".join([f"• {w}" for w in warnings])
                })
                
            if not issues and not warnings:
                blocks.append({
                    "type": "callout", 
                    "variant": "success", 
                    "title": "Карта радикальна",
                    "content": "Суждение надежно, можно приступать к анализу."
                })

        return json.dumps(blocks, ensure_ascii=False)

    if spec.section_id == "technical_appendix":
        return format_technical_appendix(chart_data)

    # 2. Template Mode
    if use_template:
        return inject_planet_emojis(build_section_template_content(spec))

    # 3. LLM Generation
    effective_spec = spec
    if spec.section_id == "balance_wheel":
        house_ctx = format_house_context(chart_data)
        new_prompt = spec.prompt + f"\n\n### ДАННЫЕ ПО ДОМАМ ДЛЯ АНАЛИЗА (ИСПОЛЬЗУЙ ИХ!):\n{house_ctx}\n\nОписывай каждый дом, учитывая знак куспида, положение управителя и планеты внутри."
        effective_spec = SectionSpec(
            section_id=spec.section_id,
            title=spec.title,
            prompt=new_prompt
        )

    result = await asyncio.to_thread(
        generate_section_with_retries,
        effective_spec,
        context,
        primary_client=llm_client,
        fallback_model=fallback_model,
        max_attempts=retry_attempts,
    )
    
    raw = result.content
    
    # JSON Cleanup: Strip code blocks if present
    if raw and (raw.strip().startswith("```") or raw.strip().startswith("[")):
        clean_json = raw.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:]
        
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
            
        clean_json = clean_json.strip()
        # If it looks like JSON array, use the cleaned version
        if clean_json.startswith("[") and clean_json.endswith("]"):
            raw = clean_json

    # 4. Intro Injection (JSON-safe)
    intro = SECTION_INTROS.get(spec.section_id)
    if intro and raw and raw.strip().startswith("["):
        try:
            blocks = json.loads(raw)
            if isinstance(blocks, list):
                # Prepend intro block
                blocks.insert(0, {
                    "type": "paragraph",
                    "text": intro.strip()
                })
                raw = json.dumps(blocks, ensure_ascii=False)
        except:
            # If parsing fails, we can't safely inject. 
            # But generate_section_with_retries should guarantee valid JSON if valid.
            pass
        
    return inject_planet_emojis(raw)

# #START_BLOCK_WORKFLOW_GENERATION
async def generate_report_sections(
    report: Report,
    payload: Any,
    db: Session,
    *,
    llm_client: Optional[LLMClient],
    llm_mode: Optional[str] = None,
    reset_chunks: bool,
    raise_on_error: bool,
) -> tuple[list, dict, Optional[str]]:
    """
    # PURPOSE: Generate sections in parallel and persist chunks.
    # INPUT: report, payload, db, llm_client, reset_chunks, raise_on_error.
    # OUTPUT: (generated_sections, chart_data, markdown).
    # CONTEXT: Async workflow with notifications.
    """

    section_specs = build_section_specs(payload)
    chunk_map = initialize_report_chunks(
        report, section_specs, db, reset=reset_chunks
    )
    report.status = "in_progress"
    report.error_message = None
    report.error_at = None
    db.commit()

    chart_data = build_chart_data(payload)
    context = build_report_context(payload, chart_data)
    effective_mode = (llm_mode or "openrouter").strip().lower()
    use_template = effective_mode in {"fallback", "local", "mock", "stub"}
    
    if not use_template and llm_client is None:
        raise ValueError("LLM client is required for this llm_mode.")
        
    retry_attempts = resolve_llm_retry_attempts()
    fallback_model = ""
    if effective_mode in {"openrouter", "cheap"}:
        fallback_model = resolve_llm_fallback_model()
    
    # Semaphore for rate limiting (OpenRouter limit or CLI concurrency control)
    semaphore = asyncio.Semaphore(resolve_llm_concurrency(effective_mode))

    # Helper for single section processing
    async def process_section(spec: SectionSpec, index: int) -> SectionResult:
        async with semaphore:
            chunk = chunk_map.get(spec.section_id)
            if chunk:
                # Refresh session state if needed, though mostly safe in single worker per request context
                # But here we are concurrent. SQLAlchemy session is not thread safe?
                # We are running in one event loop, but `to_thread` runs elsewhere.
                # DB ops are here in the loop. Should be fine if we don't share session in threads.
                chunk.status = "in_progress"
                chunk.error_message = None
                chunk.error_at = None
                chunk.order_index = index
                db.commit()

            # CONTEXT ANONYMIZATION
            section_context = copy.deepcopy(context)
            if spec.section_id != "input_frame":
                section_context["client"]["name"] = "Ты"
                section_context["client"]["note"] = ""

            try:
                content = await generate_section_content(
                    spec,
                    section_context,
                    chart_data,
                    llm_client,
                    fallback_model,
                    retry_attempts,
                    use_template
                )

                if chunk:
                    chunk.content = content
                    chunk.status = "completed"
                    db.commit()
                return SectionResult(section_id=spec.section_id, title=spec.title, content=content)
            except Exception as exc:
                error_msg = str(exc)
                logger.error("report.section.error", block_id="REPORT_GEN", section_id=spec.section_id, error=error_msg)
                
                # Check if we should fail hard or fallback
                is_validation = isinstance(exc, LLMContentValidationError)
                allow_fallback = not raise_on_error or should_fallback_on_llm_error(exc)
                if is_validation: 
                    allow_fallback = False
                
                if allow_fallback:
                    fb_content = inject_planet_emojis(build_section_fallback_content(spec))
                    if chunk:
                        chunk.content = fb_content
                        chunk.status = "completed" # Mark completed with error content
                        chunk.error_message = error_msg
                        chunk.error_at = datetime.now(timezone.utc)
                        db.commit()
                    return SectionResult(section_id=spec.section_id, title=spec.title, content=fb_content)
                else:
                    if chunk:
                        chunk.status = "failed"
                        chunk.error_message = error_msg
                        chunk.error_at = datetime.now(timezone.utc)
                        db.commit()
                    raise exc

    # Split sections: Independent vs Final
    independent_specs = [s for s in section_specs if s.section_id != "final_synthesis"]
    final_spec = next((s for s in section_specs if s.section_id == "final_synthesis"), None)
    
    # Run independent in parallel
    tasks = [process_section(spec, i) for i, spec in enumerate(independent_specs)]
    
    generated_sections = []
    failed = False
    
    try:
        results = await asyncio.gather(*tasks)
        generated_sections.extend(results)
    except Exception as e:
        failed = True
        report.status = "failed"
        report.error_message = str(e)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        # Notify failure
        client = db.query(User).filter(User.id == report.client_id).first() # User ID is stored in client_id field? No. 
        # Report.client_id links to Client model. We need User ID.
        # Wait, MVP uses Client model for data, but who ordered it?
        # User is in `Report.user_id`? No, report links to Client.
        # But Client doesn't have telegram_id. 
        # Ah, we have `User` model now. We need to link `Report` to `User` or pass telegram_id.
        # For now, let's assume we can't notify if we don't have TG ID.
        # But wait, `ReportWorkflowRequest` doesn't have user_id.
        # We need to pass user context or link report to user.
        # Let's check `User` logic. `get_my_profile` uses `User`.
        # Report generation calls usually happen in context of a User.
        # We should probably pass telegram_id to this function if available.
        # Or store `user_id` in Report model (we should add it).
        if raise_on_error: raise e
        return [], {}, None

    # Run Final Synthesis if others succeeded
    if final_spec and not failed:
        try:
            # Add context of previous sections for synthesis? 
            # Or just run it (it usually summarizes chart, not previous text, unless we change context).
            # Current `final_synthesis` prompt relies on chart data usually.
            # If it needs text, we should update context. 
            # For now, standard flow.
            res = await process_section(final_spec, len(independent_specs))
            generated_sections.append(res)
        except Exception as e:
            # If final fails, report is still mostly useful?
            # Let's fail hard if raise_on_error
            if raise_on_error: raise e

    report.status = "completed"
    db.commit()
    
    # Notification Logic
    if report.user_id:
        user = db.query(User).filter(User.id == report.user_id).first()
        if user and user.telegram_id:
            report_names = {
                "natal_master": "Твой Натальный разбор",
                "year_forecast": "Твой Альманах 2026",
                "week_forecast": "Прогноз на неделю",
                "month_forecast": "Прогноз на месяц",
                "solar_return": "Твой Соляр",
                "horary_answer": "Ответ на твой вопрос",
            }
            report_name = report_names.get(report.report_type, "Твой отчет")
            msg = f"✨ {report_name} готов! Заходи в приложение, чтобы прочитать его. 📂"
            # Fire and forget notification
            asyncio.create_task(send_bot_notification(user.telegram_id, msg))
    
    return generated_sections, chart_data, None
# #END_BLOCK_WORKFLOW_GENERATION
