# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_RUNTIME
# ROLE: Report workflow lifecycle, chunk persistence, generation finalization, and delivery notification.
# DEPENDENCIES: backend/app/models.py, report_workflow_runtime_sections.py
# GRACE_ANCHORS: [RUN_LIFECYCLE, CHUNK_RUNTIME, REPORT_GENERATION, DELIVERY_NOTIFY]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-RUNTIME
# purpose: Coordinate ReportRun records, ReportChunk state, whole-report section generation, status finalization, and delivery notifications.
# inputs:
#   - Report entity, payload object, SQLAlchemy session, section specs, LLM runtime options
# outputs:
#   - Persisted run/chunk/report state plus generated sections and chart data
# trace_obligations:
#   - Lifecycle logs preserve module, contract, block, report_id, run_id, and status attribution
# invariants:
#   - ReportRun/ReportChunk status transitions and minimum usable-section threshold remain unchanged
# failure_policy:
#   - Marks chunks/reports failed or partial using existing error messages and fallback rules
# non_goals:
#   - Does not redefine chart/context/content semantics owned by extracted sibling modules
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-RUNTIME

# START_MODULE_MAP: M-REPORT-WORKFLOW-RUNTIME
# entrypoints:
#   - start_report_run -> RUN_START_RECORD
#   - finish_report_run -> RUN_FINISH_RECORD
#   - initialize_report_chunks -> CHUNK_RESET / CHUNK_UPSERT / CHUNK_STATUS_SUMMARY
#   - generate_report_sections -> GENERATION_PREPARE / GENERATION_PARALLEL_SECTIONS / GENERATION_FINALIZE / REPORT_READY_NOTIFY
# END_MODULE_MAP: M-REPORT-WORKFLOW-RUNTIME

from __future__ import annotations

import asyncio
import copy
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy.orm import Session

from ..llm.orchestrator import LLMClient, LLMContentValidationError, SectionResult, SectionSpec
from ..models import Report, ReportChunk, ReportRun, User
from ..reporting.telegram_renderer import render_report_chunks_to_messages as _default_render_report_chunks_to_messages
from .notification import send_bot_notification as _default_send_bot_notification
from .report_workflow_chart import build_chart_data as _default_build_chart_data
from .report_workflow_context import (
    build_report_context as _default_build_report_context,
    build_section_context as _default_build_section_context,
)
from .report_workflow_content import inject_planet_emojis
from .report_workflow_content_fallback import build_section_validation_fallback_content
from .report_workflow_content_models import (
    resolve_llm_concurrency,
    resolve_llm_fallback_chain,
    resolve_llm_retry_attempts,
    resolve_openrouter_throttle_seconds,
)
from .report_workflow_forecast import build_section_fallback_content
from .report_workflow_logging import _workflow_log as _default_workflow_log
from .report_workflow_runtime_sections import (
    generate_section_content as _default_generate_section_content,
    should_fallback_on_llm_error,
)

logger = structlog.get_logger()

def _facade_symbol(name: str, default):
    module = sys.modules.get("backend.app.services.report_workflow")
    return getattr(module, name, default) if module is not None else default

def _workflow_log(*args, **kwargs):
    return _facade_symbol("_workflow_log", _default_workflow_log)(*args, **kwargs)

def build_chart_data(*args, **kwargs):
    return _facade_symbol("build_chart_data", _default_build_chart_data)(*args, **kwargs)

def build_report_context(*args, **kwargs):
    return _facade_symbol("build_report_context", _default_build_report_context)(*args, **kwargs)

def build_section_context(*args, **kwargs):
    return _facade_symbol("build_section_context", _default_build_section_context)(*args, **kwargs)

def build_section_specs(*args, **kwargs):
    target = _facade_symbol("build_section_specs", None)
    if target is None:
        raise RuntimeError("report_workflow facade is required for section spec resolution")
    return target(*args, **kwargs)

def generate_section_content(*args, **kwargs):
    return _facade_symbol("generate_section_content", _default_generate_section_content)(*args, **kwargs)

def render_report_chunks_to_messages(*args, **kwargs):
    return _facade_symbol("render_report_chunks_to_messages", _default_render_report_chunks_to_messages)(*args, **kwargs)

def send_bot_notification(*args, **kwargs):
    return _facade_symbol("send_bot_notification", _default_send_bot_notification)(*args, **kwargs)

async def _send_report_delivery_messages_default(telegram_id: int, messages: list[str]) -> None:
    for index, message in enumerate(messages):
        if not message or not message.strip():
            continue
        ok = await send_bot_notification(telegram_id, message)
        if not ok:
            logger.warning(
                "report.notify.delivery_failed",
                telegram_id=telegram_id,
                message_index=index,
            )
            break

def _send_report_delivery_messages(*args, **kwargs):
    return _facade_symbol("_send_report_delivery_messages", _send_report_delivery_messages_default)(*args, **kwargs)

# START_BLOCK: REPORT_RUNTIME_GENERATION
def start_report_run(report: Report, db: Session) -> ReportRun:
    """
    # START_CONTRACT: FN-START-REPORT-RUN
    # purpose: Persist a workflow run record before section generation begins.
    # inputs: report entity, db session.
    # returns: ReportRun instance bound to report lifecycle.
    # side_effects: inserts ReportRun row and emits workflow lifecycle logs.
    # errors: propagates database write failures to caller-managed transaction scope.
    # END_CONTRACT: FN-START-REPORT-RUN
    """

    # START_BLOCK: RUN_START_RECORD
    _workflow_log(
        "info",
        "report.workflow.run_start",
        fn="start_report_run",
        contract="FN-START-REPORT-RUN",
        block="RUN_START_RECORD",
        report=report,
        status="in_progress",
    )

    run = ReportRun(
        report_id=report.id,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    _workflow_log(
        "info",
        "report.workflow.run_started",
        fn="start_report_run",
        contract="FN-START-REPORT-RUN",
        block="RUN_START_RECORD",
        report=report,
        run_id=str(run.id),
    )
    # END_BLOCK: RUN_START_RECORD
    return run


async def _send_report_delivery_messages(telegram_id: int, messages: list[str]) -> None:
    for index, message in enumerate(messages):
        if not message or not message.strip():
            continue
        ok = await send_bot_notification(telegram_id, message)
        if not ok:
            logger.warning(
                "report.notify.delivery_failed",
                telegram_id=telegram_id,
                message_index=index,
            )
            break

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

def initialize_report_chunks(
    report: Report,
    section_specs: List[SectionSpec],
    db: Session,
    reset: bool = False,
) -> dict:
    """
    # START_CONTRACT: FN-SAVE-SECTION-PAYLOAD
    # purpose: Ensure persisted section payload/chunk placeholders exist before generation or resume.
    # inputs: report row, section specs, db session, reset flag.
    # returns: mapping of section_id to ReportChunk rows.
    # side_effects: mutates chunk rows and emits admin/workflow queue logs.
    # errors: propagates database persistence failures.
    # END_CONTRACT: FN-SAVE-SECTION-PAYLOAD
    """

    if reset:
        # START_BLOCK: CHUNK_RESET
        db.query(ReportChunk).filter(ReportChunk.report_id == report.id).delete()
        db.flush()
        _workflow_log(
            "info",
            "report.workflow.queue_reset",
            fn="initialize_report_chunks",
            contract="FN-SAVE-SECTION-PAYLOAD",
            block="CHUNK_RESET",
            report=report,
            stage="reset",
            reset=True,
            section_total=len(section_specs),
            bridge="admin_resume_checkout",
        )
        # END_BLOCK: CHUNK_RESET

    chunks = {
        chunk.section: chunk
        for chunk in db.query(ReportChunk)
        .filter(ReportChunk.report_id == report.id)
        .all()
    }

    # START_BLOCK: CHUNK_UPSERT
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

    # END_BLOCK: CHUNK_UPSERT
    # START_BLOCK: CHUNK_STATUS_SUMMARY
    _workflow_log(
        "info",
        "report.workflow.queue_initialized",
        fn="initialize_report_chunks",
        contract="FN-SAVE-SECTION-PAYLOAD",
        block="CHUNK_STATUS_SUMMARY",
        report=report,
        stage="initialized",
        reset=reset,
        section_total=len(section_specs),
        pending=sum(1 for chunk in chunks.values() if chunk.status == "pending"),
        running=sum(1 for chunk in chunks.values() if chunk.status == "in_progress"),
        error=sum(1 for chunk in chunks.values() if chunk.status in {"failed", "error"}),
    )
    # END_BLOCK: CHUNK_STATUS_SUMMARY

    return chunks

async def generate_report_sections(
    report: Report,
    payload: Any,
    db: Session,
    *,
    llm_client: Optional[LLMClient],
    llm_mode: Optional[str] = None,
    reset_chunks: bool,
    raise_on_error: bool,
    run: Optional[ReportRun] = None,
    use_template: Optional[bool] = None,
) -> tuple[list, dict]:
    """
    # START_CONTRACT: FN-HANDLE-GENERATION-RESULT
    # purpose: Orchestrate full report generation, persistence, fallback handling, and ready notification.
    # inputs: report row, payload, db session, llm config, reset flag, error policy, optional run row.
    # returns: generated section results and chart_data for downstream rendering/export.
    # side_effects: mutates report/chunks/run state, emits admin/workflow logs, schedules telegram delivery.
    # errors: propagates unrecoverable generation failures when raise_on_error is enabled.
    # END_CONTRACT: FN-HANDLE-GENERATION-RESULT
    """

    # START_BLOCK: GENERATION_PREPARE
    section_specs = build_section_specs(payload)
    total_expected = len(section_specs)
    
    chunk_map = _facade_symbol("initialize_report_chunks", initialize_report_chunks)(
        report, section_specs, db, reset=reset_chunks
    )
    report.status = "in_progress"
    report.error_message = None
    report.error_at = None
    db.commit()

    chart_data = build_chart_data(payload)
    context = build_report_context(payload, chart_data)
    effective_mode = (llm_mode or "openrouter").strip().lower()
    if use_template is None:
        use_template = effective_mode in {"fallback", "local", "mock", "stub"}
    
    if not use_template and llm_client is None:
        raise ValueError("LLM client is required for this llm_mode.")
        
    retry_attempts = resolve_llm_retry_attempts()
    fallback_models = []
    if effective_mode in {"openrouter", "cheap"}:
        fallback_models = resolve_llm_fallback_chain()
    
    _workflow_log(
        "info",
        "report.workflow.generation_start",
        fn="generate_report_sections",
        contract="FN-HANDLE-GENERATION-RESULT",
        block="GENERATION_PREPARE",
        report=report,
        mode=effective_mode,
        sections_total=total_expected,
        fallback_chain=fallback_models,
    )
    # END_BLOCK: GENERATION_PREPARE

    # Semaphore for rate limiting (OpenRouter limit or CLI concurrency control)
    semaphore = asyncio.Semaphore(resolve_llm_concurrency(effective_mode))

    # Track successes and usage
    success_count = 0
    fallback_count = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_total_tokens = 0

    # Helper for single section processing
    # START_BLOCK: GENERATION_PARALLEL_SECTIONS
    async def process_section(spec: SectionSpec, index: int) -> SectionResult:
        nonlocal success_count, fallback_count, total_prompt_tokens, total_completion_tokens, total_total_tokens
        async with semaphore:
            # Throttle for OpenRouter (free tier is rate-limited)
            if effective_mode == "openrouter":
                await asyncio.sleep(resolve_openrouter_throttle_seconds())
            
            chunk = chunk_map.get(spec.section_id)
            if chunk:
                chunk.status = "in_progress"
                chunk.error_message = None
                chunk.error_at = None
                chunk.order_index = index
                db.commit()

            # CONTEXT ANONYMIZATION + SECTION PACK
            section_context = copy.deepcopy(build_section_context(spec.section_id, context, chart_data))
            if spec.section_id != "input_frame":
                section_context["client"]["name"] = "Ты"
                section_context["client"]["note"] = ""

            result = None
            try:
                result = await generate_section_content(
                    spec,
                    section_context,
                    chart_data,
                    llm_client,
                    fallback_models,
                    retry_attempts,
                    use_template
                )
                
                if isinstance(result, SectionResult):
                    content = result.content
                    usage = result.usage
                    section_result = result
                elif hasattr(result, "content"):
                    content = str(getattr(result, "content") or "")
                    usage = getattr(result, "usage", {}) or {}
                    section_result = SectionResult(
                        section_id=spec.section_id,
                        title=spec.title,
                        content=content,
                    )
                else:
                    content = str(result)
                    usage = {}
                    section_result = SectionResult(
                        section_id=spec.section_id,
                        title=spec.title,
                        content=content,
                    )

                if usage:
                    total_prompt_tokens += usage.get("prompt_tokens", 0)
                    total_completion_tokens += usage.get("completion_tokens", 0)
                    total_total_tokens += usage.get("total_tokens", 0)

                if chunk:
                    chunk.content = content
                    chunk.status = "completed"
                    db.commit()
                
                # If content contains error callout, it's a soft fallback
                if "Ошибка генерации" in content:
                    fallback_count += 1
                    _workflow_log(
                        "info",
                        "report.workflow.section_fallback_content",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="GENERATION_PARALLEL_SECTIONS",
                        report=report,
                        stage="fallback_content",
                        section_id=spec.section_id,
                        run_id=str(run.id) if run else None,
                        fallback=True,
                    )
                else:
                    success_count += 1
                
                _workflow_log(
                    "info",
                    "report.workflow.section_done",
                    fn="generate_report_sections",
                    contract="FN-HANDLE-GENERATION-RESULT",
                    block="GENERATION_PARALLEL_SECTIONS",
                    report=report,
                    section_id=spec.section_id,
                    duration_ms=getattr(section_result, "duration_ms", 0),
                    status="completed",
                )
                    
                return section_result
            except Exception as exc:
                error_msg = str(exc)
                # Check if we should fail hard or fallback
                allow_fallback = not raise_on_error or should_fallback_on_llm_error(exc)
                if isinstance(exc, LLMContentValidationError):
                    # Validation errors are also allowed to fallback
                    allow_fallback = True
                
                _workflow_log(
                    "error",
                    "report.workflow.section_error",
                    fn="generate_report_sections",
                    contract="FN-HANDLE-GENERATION-RESULT",
                    block="GENERATION_PARALLEL_SECTIONS",
                    report=report,
                    section_id=spec.section_id,
                    error=error_msg,
                    exc_type=type(exc).__name__,
                    allow_fallback=allow_fallback,
                    stage="section_error",
                    run_id=str(run.id) if run else None,
                )

                if allow_fallback:
                    if isinstance(exc, LLMContentValidationError):
                        fb_content = inject_planet_emojis(
                            build_section_validation_fallback_content(spec, section_context)
                        )
                    else:
                        fb_content = inject_planet_emojis(build_section_fallback_content(spec, section_context))
                    fallback_count += 1
                    _workflow_log(
                        "info",
                        "report.workflow.section_fallback_applied",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="GENERATION_PARALLEL_SECTIONS",
                        report=report,
                        stage="fallback_applied",
                        section_id=spec.section_id,
                        run_id=str(run.id) if run else None,
                        fallback=True,
                    )
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
        if raise_on_error: raise e
        return [], {}

    # END_BLOCK: GENERATION_PARALLEL_SECTIONS

    # START_BLOCK: GENERATION_FINAL_SYNTHESIS
    # Run Final Synthesis if others succeeded
    if final_spec and not failed:
        try:
            res = await process_section(final_spec, len(independent_specs))
            generated_sections.append(res)
        except Exception as e:
            if raise_on_error: raise e

    # END_BLOCK: GENERATION_FINAL_SYNTHESIS

    # START_BLOCK: GENERATION_FINALIZE
    # HARD CHECK: Minimum successful sections
    # For natal_master (approx 18 sections), we expect at least 5 to consider it "usable"
    # For others (1-3 sections), we expect at least 1.
    min_required = 1
    if report.report_type == "natal_master":
        min_required = 5
    
    total_ok = success_count + fallback_count
    # Single-section forecast/report lanes remain usable when deterministic fallback content
    # was applied; natal keeps a stricter threshold because broad fallback-only output is not
    # sufficient for that surface.
    usable_count = total_ok if report.report_type != "natal_master" else success_count
    
    # Update Run stats if provided
    if run:
        run.prompt_tokens = total_prompt_tokens
        run.completion_tokens = total_completion_tokens
        run.total_tokens = total_total_tokens
        # Estimated cost: very rough heuristic for GPT-4.1-Nano
        # $0.05 / 1M tokens? Let's use a conservative placeholder or 0 for now
        # until we have real pricing logic.
        run.estimated_cost = Decimal(str(round(total_total_tokens * 0.0000001, 4)))
        db.commit()

    _workflow_log(
        "info",
        "report.workflow.generation_stats",
        fn="generate_report_sections",
        contract="FN-HANDLE-GENERATION-RESULT",
        block="GENERATION_FINALIZE",
        report=report,
        success=success_count,
        fallback=fallback_count,
        total=total_expected,
        min_required=min_required,
        total_ok=total_ok,
        usable=usable_count,
    )
    _workflow_log(
        "info",
        "report.workflow.generation_complete",
        fn="generate_report_sections",
        contract="FN-HANDLE-GENERATION-RESULT",
        block="GENERATION_FINALIZE",
        report=report,
        stage="generation_complete",
        run_id=str(run.id) if run else None,
        success=success_count,
        fallback=fallback_count,
        usable=usable_count,
        pending=sum(1 for chunk in chunk_map.values() if chunk.status == "pending"),
        running=sum(1 for chunk in chunk_map.values() if chunk.status == "in_progress"),
        error=sum(1 for chunk in chunk_map.values() if chunk.status in {"failed", "error"}),
    )

    if usable_count < min_required and not use_template:
        report.status = "failed"
        report.error_message = (
            f"Generation failed: only {usable_count}/{total_expected} sections usable "
            f"(min {min_required})."
        )
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        _workflow_log(
            "error",
            "report.workflow.failed_threshold",
            fn="generate_report_sections",
            contract="FN-HANDLE-GENERATION-RESULT",
            block="GENERATION_FINALIZE",
            report=report,
            success=success_count,
            fallback=fallback_count,
            usable=usable_count,
        )
    else:
        report.status = "completed"
        if fallback_count:
            report.error_message = (
                f"Partial generation: {fallback_count} of {total_expected} sections used fallback content."
            )
            report.error_at = datetime.now(timezone.utc)
        else:
            report.error_message = None
            report.error_at = None
        db.commit()
        
        # END_BLOCK: GENERATION_FINALIZE

        # START_BLOCK: REPORT_READY_NOTIFY
        # Notification Logic
        if report.user_id:
            user = db.query(User).filter(User.id == report.user_id).first()
            if user and user.telegram_id:
                report_names = {
                    "natal_master": "Твой Натальный разбор",
                    "year_forecast": "Твой Альманах 2026",
                    "week_forecast": "Прогноз на неделю",
                    "month_forecast": "Прогноз на месяц",
                    "ten_year_forecast": "Прогноз на 10 лет",
                    "solar_return": "Твой Соляр",
                    "horary_answer": "Ответ на твой вопрос",
                }
                report_name = report_names.get(report.report_type, "Твой отчет")
                fallback_msg = f"✨ {report_name} готов! Заходи в приложение, чтобы прочитать его. 📂"
                messages: list[str] = []
                try:
                    chunks = (
                        db.query(ReportChunk)
                        .filter(ReportChunk.report_id == report.id)
                        .order_by(ReportChunk.order_index.asc(), ReportChunk.created_at.asc())
                        .all()
                    )
                    messages = render_report_chunks_to_messages(chunks, title=report_name)
                except Exception as exc:
                    _workflow_log(
                        "error",
                        "report.workflow.notify_render_failed",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="REPORT_READY_NOTIFY",
                        report=report,
                        error=str(exc),
                    )

                if messages:
                    _workflow_log(
                        "info",
                        "report.workflow.notify_report_ready",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="REPORT_READY_NOTIFY",
                        report=report,
                        delivery="chunked_messages",
                        message_total=len(messages),
                        bridge="resume_checkout_ready",
                    )
                    asyncio.create_task(
                        _send_report_delivery_messages(user.telegram_id, messages)
                    )
                else:
                    _workflow_log(
                        "info",
                        "report.workflow.notify_report_ready",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="REPORT_READY_NOTIFY",
                        report=report,
                        delivery="single_fallback_message",
                        bridge="resume_checkout_ready",
                    )
                    asyncio.create_task(send_bot_notification(user.telegram_id, fallback_msg))
        # END_BLOCK: REPORT_READY_NOTIFY

    return generated_sections, chart_data
# END_BLOCK: REPORT_RUNTIME_GENERATION
