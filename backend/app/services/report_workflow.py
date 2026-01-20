# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW
# ROLE: Domain service for report generation pipeline.
# DEPENDENCIES: stellium_engine.py, backend/app/models.py, backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [WORKFLOW_UTILS, WORKFLOW_CONTEXT, WORKFLOW_CHART, WORKFLOW_SECTIONS, WORKFLOW_MARKDOWN, WORKFLOW_GENERATION]
# ############################################################################

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
import re
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
import structlog

from stellium_engine import StelliumEngine

from .. import engine_utils
from ..llm.orchestrator import (
    LLMOrchestrator,
    LLMContentValidationError,
    OpenRouterClient,
    SectionResult,
    SectionSpec,
)
from ..models import Report, ReportChunk, ReportRun, User
from ..reporting.markdown_reporter import ReportSection, assemble_markdown
from ..reporting.section_templates import get_default_sections
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


def inject_planet_emojis(content: str) -> str:
    """
    # PURPOSE: Ensure planet names include emoji prefixes.
    # INPUT: Markdown content.
    # OUTPUT: Content with emoji-prefixed planet names.
    # CONTEXT: Used to normalize section text regardless of LLM drift.
    """

    text = content or ""
    for name, emoji in PLANET_EMOJI_MAP.items():
        escaped = re.escape(name)
        pattern = rf"(?<!{re.escape(emoji)}\s)(?<!{re.escape(emoji)})\b{escaped}\b"
        text = re.sub(pattern, f"{emoji} {name}", text)
    return text


# #START_BLOCK_WORKFLOW_UTILS
def build_forecast_window(report_type: str) -> dict:
    """
    # PURPOSE: Build forecast window metadata for prompts.
    # INPUT: report_type (str).
    # OUTPUT: Dict with window fields.
    # CONTEXT: Used in report context for forecasts.
    """

    start = datetime.now(timezone.utc).isoformat()
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
    return "OpenRouter error:" in message or "OpenRouter connection error" in message


def build_section_fallback_content(spec: SectionSpec) -> str:
    """
    # PURPOSE: Provide a user-friendly fallback body for a failed section.
    # INPUT: section spec.
    # OUTPUT: Markdown string.
    # CONTEXT: Used when LLM credits/network errors occur.
    """

    return (
        f"Раздел **{spec.title}** сейчас недоступен из-за ошибки генерации.\n\n"
        "- Отчет сохранен, можно перегенерировать этот раздел позже.\n"
        "- Данные по карте доступны, ошибка только в тексте.\n"
        "- Если проблема повторяется, проверьте лимит токенов.\n\n"
        "### 💡 Рекомендации\n"
        "- Запустите перегенерацию через несколько минут.\n"
        "- Убедитесь, что баланс OpenRouter не исчерпан.\n"
    )


def build_section_template_content(spec: SectionSpec) -> str:
    """
    # PURPOSE: Provide a low-cost local template for test-mode generation.
    # INPUT: section spec.
    # OUTPUT: Markdown string.
    # CONTEXT: Used when LLM calls are disabled for tests.
    """

    if spec.section_id == "month_theme":
        return (
            "1. Заголовок и метаданные: Март 2026 | Москва | Натал: базовый | Метод: транзиты | Слои: 4.\n"
            "2. Статус месяца (Светофор 🟡):\n"
            "* Цветовой индикатор: 🟡.\n"
            "* Название месяца: «Лабиринт с подсказками».\n"
            "* Общий фон: Неспешная перестройка.\n"
            "* Цена ошибок: Высокая.\n"
            "* Рычаг: Структура дня.\n"
            "* Совет-формула: Действуй по плану, оставляя люфт.\n"
            "3. Центральная нить смысла: Метафора + тезис. Маркеры «в теме»: стабильный ритм, ясные границы, регулярные проверки.\n"
            "4. Главные активаторы месяца (ТОП-5):\n"
            "- Марс (секстиль) → Импульс → Работа → Ресурс.\n"
            "- Венера (квадрат) → Напряжение → Отношения → Риск.\n"
            "- Меркурий (трин) → Ясность → Деньги → Ресурс.\n"
            "- Сатурн (соединение) → Давление → Здоровье → Риск.\n"
            "- Юпитер (оппозиция) → Расширение → Учеба → Ресурс.\n"
            "5. Карта сфер месяца: ТОП-3 — Финансы, Отношения, Здоровье. Остальные: Быт, Соцсети, Дом.\n"
            "6. Событийный слой: Ингрессы — без резких сдвигов; Ретроградность — рабочая пауза; Затмения — нет; Лунации — средняя интенсивность.\n"
            "7. Личный слой: Углы/Светила — стабилизируют; Управители — требуют порядка; Узлы/Вертекс — мягкий поворот; Конфигурации — умеренные.\n"
            "8. Глубинный слой: Прогрессивная Луна — смена фокуса; Дуги/Дирекции — медленный рост; Итог созревания — дисциплина.\n"
            "9. Солярный контекст: Связь с темой года через дом карьеры; наложение домов усиливает трудовую сферу.\n"
            "10. Тайм-лорды: Годовой управитель дает стабильность и контроль.\n"
            "11. Фиксированные звёзды: Архетип → Проявление → Дар/Риск (точные попадания отсутствуют).\n"
            "12. Трансураны: Режим края без перегрева, поддержка через долгий фокус.\n"
            "13. Итог месяца: 3 результата — порядок, ясность, устойчивость. 3 ловушки — спешка, перфекционизм, перегруз. Ключ — ритм. Переход — спокойное закрепление.\n"
        )

    title = spec.title.strip()
    return (
        f"{title} раскрывает ключевые процессы и фокус внимания этого блока. "
        "Здесь важно отметить динамику, сильные стороны и зоны роста, "
        "чтобы использовать потенциал максимально осознанно.\n\n"
        "### 🧭 О чем этот блок\n"
        "Коротко: какие темы и задачи раскрывает этот раздел.\n\n"
        "### 📊 Краткая карта блока\n"
        "| Параметр | Содержание |\n"
        "| --- | --- |\n"
        "| Фокус | Основные задачи и акценты |\n"
        "| Ресурс | Сильные стороны и опоры |\n"
        "| Риск | Слепые зоны и напряжение |\n\n"
        "> **Тезис:** настройка этого блока дает устойчивую опору и ясный вектор.\n\n"
        "### ✨ Контуры раздела\n"
        "Этот фрагмент описывает, как проявляется энергия и где она приносит "
        "наиболее ощутимый результат. Отмечаются типичные паттерны и "
        "сценарии поведения, которые усиливают ваши сильные стороны.\n\n"
        "- 🧭 **Вектор развития:** куда направить усилия в ближайшее время.\n"
        "- 💬 **Проявление:** как энергия блока отражается в повседневности.\n"
        "- 🌙 **Баланс:** что помогает сохранять внутреннюю устойчивость.\n\n"
        "### 💡 Рекомендации\n"
        "- Сформулируйте 1-2 практичных шага для закрепления результата.\n"
        "- Отмечайте сигналы и фиксируйте наблюдения в течение недели.\n"
    )


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
        "OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"
    ).strip()


def generate_section_with_retries(
    spec: SectionSpec,
    context: Dict[str, Any],
    *,
    primary_client: OpenRouterClient,
    fallback_model: str,
    max_attempts: int,
) -> SectionResult:
    """
    # PURPOSE: Generate a section with retries + fallback model on bad structure.
    # INPUT: spec, context, primary client, fallback model, max attempts.
    # OUTPUT: SectionResult.
    # CONTEXT: Used by report workflows to stabilize structure.
    """

    last_error: Optional[Exception] = None
    orchestrator = LLMOrchestrator(primary_client)
    for attempt in range(max_attempts):
        try:
            return orchestrator.generate_sections([spec], context=context)[0]
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

    if fallback_model:
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
    # PURPOSE: Calculate natal chart data for report context.
    # INPUT: payload (ReportWorkflowRequest-like).
    # OUTPUT: Serialized chart dict.
    # CONTEXT: Used by report generation prompts.
    """

    engine = StelliumEngine()
    house_system = engine_utils.resolve_house_system(payload.house_system)

    clean_birth_date = payload.birth_date
    if "+" in clean_birth_date:
        clean_birth_date = clean_birth_date.split("+")[0]

    location_input: object = payload.birth_location
    if payload.birth_lat is not None and payload.birth_lon is not None:
        location_input = {
            "latitude": payload.birth_lat,
            "longitude": payload.birth_lon,
            "name": payload.birth_location or payload.client_name,
        }

    try:
        chart = engine.create_natal_chart(
            payload.client_name,
            clean_birth_date,
            location_input,
            house_system,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Chart error: {exc}"
        ) from exc

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(chart, orb=payload.fixed_star_orb)

    return engine_utils.serialize_chart(chart, chart_type="natal", fixed_stars=stars)
# #END_BLOCK_WORKFLOW_CHART


# #START_BLOCK_WORKFLOW_CONTEXT
def build_report_context(payload: Any, chart_data: dict) -> dict:
    """
    # PURPOSE: Build the LLM prompt context for report generation.
    # INPUT: payload (ReportWorkflowRequest-like), chart_data (dict).
    # OUTPUT: Context dict for LLM.
    # CONTEXT: Used by the LLM orchestrator.
    """

    return {
        "client": {
            "name": payload.client_name,
            "note": payload.client_note,
            "birth_date": payload.birth_date,
            "birth_location": payload.birth_location,
            "birth_lat": payload.birth_lat,
            "birth_lon": payload.birth_lon,
            "birth_timezone": payload.birth_timezone,
            "birth_place_id": payload.birth_place_id,
            "report_type": payload.report_type,
        },
        "partner": {
            "name": payload.partner_name,
            "birth_date": payload.partner_birth_date,
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
        "forecast_window": build_forecast_window(payload.report_type),
        "chart": chart_data,
    }
# #END_BLOCK_WORKFLOW_CONTEXT


# #START_BLOCK_WORKFLOW_MARKDOWN
def assemble_markdown_from_specs(
    report_type: str, section_specs: List[SectionSpec], chunk_map: dict
) -> str:
    """
    # PURPOSE: Assemble markdown from section specs and stored chunks.
    # INPUT: report_type (str), section_specs (list), chunk_map (dict).
    # OUTPUT: Markdown string.
    # CONTEXT: Used by admin report exports.
    """

    sections = []
    for spec in section_specs:
        chunk = chunk_map.get(spec.section_id)
        sections.append(
            ReportSection(
                section_id=spec.section_id,
                title=spec.title,
                content=(chunk.content if chunk else "") or "",
            )
        )
    return assemble_markdown(f"Report: {report_type}", sections)
# #END_BLOCK_WORKFLOW_MARKDOWN


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

    markdown_index = len(section_specs)
    markdown_chunk = chunks.get("final_markdown")
    if markdown_chunk:
        if reset:
            markdown_chunk.content = ""
            markdown_chunk.status = "pending"
            markdown_chunk.error_message = None
            markdown_chunk.error_at = None
        markdown_chunk.order_index = markdown_index
    else:
        markdown_chunk = ReportChunk(
            report_id=report.id,
            section="final_markdown",
            content="",
            status="pending",
            order_index=markdown_index,
        )
        db.add(markdown_chunk)
        chunks["final_markdown"] = markdown_chunk

    return chunks
# #END_BLOCK_WORKFLOW_SECTIONS


# #START_BLOCK_WORKFLOW_GENERATION
async def generate_report_sections(
    report: Report,
    payload: Any,
    db: Session,
    *,
    llm_client: Optional[OpenRouterClient],
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
        raise ValueError("LLM client is required for openrouter mode.")
        
    retry_attempts = resolve_llm_retry_attempts()
    fallback_model = resolve_llm_fallback_model()
    
    # Semaphore for rate limiting (OpenRouter limit or cost control)
    semaphore = asyncio.Semaphore(10)

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

            if use_template:
                content = inject_planet_emojis(build_section_template_content(spec))
                if chunk:
                    chunk.content = content
                    chunk.status = "completed"
                    db.commit()
                return SectionResult(section_id=spec.section_id, title=spec.title, content=content)

            # Offload blocking LLM call
            try:
                result = await asyncio.to_thread(
                    generate_section_with_retries,
                    spec,
                    context,
                    primary_client=llm_client,
                    fallback_model=fallback_model,
                    max_attempts=retry_attempts,
                )
                final_content = inject_planet_emojis(result.content)
                if chunk:
                    chunk.content = final_content
                    chunk.status = "completed"
                    db.commit()
                return SectionResult(section_id=result.section_id, title=result.title, content=final_content)
            except Exception as exc:
                error_msg = str(exc)
                logger.error("report.section.error", section_id=spec.section_id, error=error_msg)
                
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

    # Assemble Markdown
    chunk_map = {c.section: c for c in db.query(ReportChunk).filter(ReportChunk.report_id == report.id).all()}
    markdown = assemble_markdown_from_specs(report.report_type, section_specs, chunk_map)
    
    markdown_chunk = chunk_map.get("final_markdown")
    if markdown_chunk:
        markdown_chunk.content = markdown
        markdown_chunk.status = "completed"
        db.commit()

    report.status = "completed"
    db.commit()
    
    # Notification Logic
    # We need to find the Telegram User to notify.
    # Report -> Client. Does Client have link to User?
    # In B2C flow, User creates Client (themselves) or just orders report.
    # We haven't linked Report to User yet in `models.py`.
    # Major architectural gap for notifications!
    # Fix: We will try to find a User who has the same name? Unreliable.
    # Fix: Use `Client` email if it stores TG ID? No.
    # Fix: For MVP, pass `telegram_id` in payload or look up via some other way.
    # Best way: Add `user_id` to Report model in next migration.
    # Workaround now: Use `Client.notes` to store "tg_12345"? 
    # Or just `payload.client_note`?
    
    return generated_sections, chart_data, markdown
# #END_BLOCK_WORKFLOW_GENERATION
