# START_MODULE_CONTRACT: M-API-GATEWAY-RUNTIME
# purpose: Run report background generation helpers.
# owns:
#   - backend/app/routers/runtime.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-RUNTIME

# START_MODULE_MAP: M-API-GATEWAY-RUNTIME
# public_entrypoints:
#   - run_report_generation
#   - run_report_section_generation
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-RUNTIME

from fastapi import APIRouter

from .gateway_context import *

router = APIRouter()

# START_BLOCK: ROUTER_EXTRACTION
# START_CONTRACT: FN-RUN-REPORT-GENERATION
async def run_report_generation(
    report_id: uuid.UUID, payload_data: dict, reset_chunks: bool = False
) -> None:
    """
    # PURPOSE: Generate report sections and markdown in the background.
    # INPUT: report_id (UUID), payload_data (dict).
    # OUTPUT: None.
    # CONTEXT: Background task for /api/workflows/report/async.
    """

    db = SessionLocal()
    report: Optional[Report] = None
    run: Optional[ReportRun] = None
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        logger.info(
            "report.async.start",
            block_id="REPORT_ASYNC",
            report_id=str(report.id),
            client_id=str(report.client_id),
        )

        run = start_report_run(report, db)
        payload = ReportWorkflowRequest.model_validate(payload_data)
        llm_mode = resolve_llm_mode(payload)
        llm_client = None
        if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)

        generated_sections, _ = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=reset_chunks,
            raise_on_error=False,
            run=run,
        )
        if report.status == "completed":
            finish_report_run(run, db, "completed")
            if report.report_type == "week_forecast":
                logger.info("week_generate_succeeded", user_id=str(report.user_id), report_id=str(report.id))
            log_analytics_event(
                db,
                "report_generated",
                user_id=report.user_id,
                telegram_id=None,
                source="backend",
                metadata={
                    "report_id": str(report.id),
                    "report_type": report.report_type,
                    "client_id": str(report.client_id),
                },
            )

            logger.info(
                "report.async.complete",
                block_id="REPORT_ASYNC",
                report_id=str(report.id),
                client_id=str(report.client_id),
                sections=len(generated_sections),
            )
        else:
            if report.report_type == "week_forecast":
                logger.error("week_generate_failed", user_id=str(report.user_id), report_id=str(report.id), error=report.error_message)
            finish_report_run(run, db, "failed", error_message=report.error_message)
    except Exception as exc:
        if report:
            if report.report_type == "week_forecast":
                logger.error("week_generate_failed", user_id=str(report.user_id), report_id=str(report.id), error=str(exc))
            report.status = "failed"
            report.error_message = str(exc)
            report.error_at = datetime.now(timezone.utc)
            db.commit()
            finish_report_run(run, db, "failed", error_message=str(exc))
            logger.error(
                "report.async.error",
                block_id="REPORT_ASYNC",
                report_id=str(report.id),
                client_id=str(report.client_id),
                error=str(exc),
            )
    finally:
        db.close()
# END_CONTRACT: FN-RUN-REPORT-GENERATION
# START_CONTRACT: FN-RUN-REPORT-SECTION-GENERATION
async def run_report_section_generation(
    report_id: uuid.UUID, section_id: str, payload_data: dict
) -> None:
    """
    # PURPOSE: Regenerate a single report section in the background.
    # INPUT: report_id (UUID), section_id (str), payload_data (dict).
    # OUTPUT: None.
    # CONTEXT: Background task for async section regeneration.
    """

    db = SessionLocal()
    report: Optional[Report] = None
    run: Optional[ReportRun] = None
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        logger.info(
            "report.section.async.start",
            block_id="REPORT_ASYNC_SECTION",
            report_id=str(report.id),
            section_id=section_id,
        )

        run = start_report_run(report, db)
        payload = ReportWorkflowRequest.model_validate(payload_data)
        llm_mode = resolve_llm_mode(payload)

        llm_client = None
        if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
            try:
                model_override = (
                    resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
                )
                llm_client = build_llm_client(llm_mode, model_override=model_override)
            except ValueError as exc:
                logger.warning("llm.init.error", error=str(exc))

        section_specs = build_section_specs(payload)
        target_spec = next(
            (spec for spec in section_specs if spec.section_id == section_id),
            None,
        )
        target_index = next(
            (idx for idx, spec in enumerate(section_specs) if spec.section_id == section_id),
            0,
        )
        if not target_spec:
            report.status = "failed"
            report.error_message = "Section not found."
            report.error_at = datetime.now(timezone.utc)
            db.commit()
            finish_report_run(run, db, "failed", error_message=report.error_message)
        chart_data = build_chart_data(payload)
        context = build_report_context(payload, chart_data)

        # Context Anonymization
        section_context = build_section_context(section_id, context, chart_data)
        if section_id != "input_frame":
            section_context["client"]["name"] = "Ты"
            section_context["client"]["note"] = ""

        chunk_map = initialize_report_chunks(report, section_specs, db, reset=False)
        report.status = "in_progress"
        report.error_message = None
        report.error_at = None

        target_chunk = chunk_map.get(section_id)
        if target_chunk:
            target_chunk.status = "in_progress"
            target_chunk.error_message = None
            target_chunk.error_at = None
        db.commit()

        error_message = None
        retry_attempts = resolve_llm_retry_attempts()
        fallback_models = []
        if llm_mode in {"openrouter", "cheap"}:
            model = resolve_llm_fallback_model()
            if model:
                fallback_models = [model]
        use_template = llm_mode in {"fallback", "local", "mock", "stub"}

        try:
            result = await generate_section_content(
                target_spec,
                section_context,
                chart_data,
                llm_client,
                fallback_models,
                retry_attempts,
                use_template
            )
            content = result.content
            usage = result.usage
            if usage and run:
                run.prompt_tokens = usage.get("prompt_tokens", 0)
                run.completion_tokens = usage.get("completion_tokens", 0)
                run.total_tokens = usage.get("total_tokens", 0)
                run.estimated_cost = Decimal(str(round(run.total_tokens * 0.0000001, 4)))
                db.commit()
        except Exception as exc:
            if should_fallback_on_llm_error(exc) or isinstance(exc, LLMContentValidationError):
                error_message = str(exc)
                if isinstance(exc, LLMContentValidationError):
                    content = inject_planet_emojis(
                        build_section_validation_fallback_content(target_spec, section_context)
                    )
                else:
                    content = inject_planet_emojis(
                        build_section_fallback_content(target_spec, section_context)
                    )
                logger.warning(
                    "report.section.fallback",
                    block_id="REPORT_SECTION",
                    report_id=str(report.id),
                    section_id=section_id,
                    error=str(exc),
                )
            else:
                if target_chunk:
                    target_chunk.status = "failed"
                    target_chunk.error_message = str(exc)
                    target_chunk.error_at = datetime.now(timezone.utc)
                report.status = "failed"
                report.error_message = str(exc)
                report.error_at = datetime.now(timezone.utc)
                db.commit()
                finish_report_run(run, db, "failed", error_message=str(exc))
                logger.error(
                    "report.section.error",
                    block_id="REPORT_SECTION",
                    report_id=str(report.id),
                    section_id=section_id,
                    error=str(exc),
                )
                return
        if target_chunk:
            target_chunk.content = content
            target_chunk.status = "completed"
            target_chunk.error_message = error_message
            target_chunk.error_at = (
                datetime.now(timezone.utc) if error_message else None
            )
        else:
            db.add(
                ReportChunk(
                    report_id=report.id,
                    section=section_id,
                    content=content,
                    status="completed",
                    order_index=target_index,
                    error_message=error_message,
                    error_at=datetime.now(timezone.utc) if error_message else None,
                )
            )
        db.commit()

        # Markdown assembly removed (JSON-only pipeline)

        report.status = "completed"
        db.commit()
        finish_report_run(run, db, "completed", error_message=error_message)
        logger.info(
            "report.section.async.complete",
            block_id="REPORT_ASYNC_SECTION",
            report_id=str(report.id),
            section_id=section_id,
        )
    except Exception as exc:
        if report:
            report.status = "failed"
            report.error_message = str(exc)
            report.error_at = datetime.now(timezone.utc)
            db.commit()
            finish_report_run(run, db, "failed", error_message=str(exc))
            logger.error(
                "report.section.async.error",
                block_id="REPORT_ASYNC_SECTION",
                report_id=str(report.id),
                section_id=section_id,
                error=str(exc),
            )
    finally:
        db.close()
# END_CONTRACT: FN-RUN-REPORT-SECTION-GENERATION

# END_BLOCK: ROUTER_EXTRACTION
