# START_MODULE_CONTRACT: M-API-GATEWAY-REPORTS
# purpose: Expose report workflow and user report routes.
# owns:
#   - backend/app/routers/reports.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-REPORTS

# START_MODULE_MAP: M-API-GATEWAY-REPORTS
# public_entrypoints:
#   - router
#   - create_report_async
#   - get_report_detail
#   - user_regenerate_report
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-REPORTS

from fastapi import APIRouter

from .gateway_context import *
from .gateway_runtime import run_report_generation, run_report_section_generation
from .gateway_context import _consume_legacy_workflow_access_if_needed, _resolve_legacy_workflow_access

router = APIRouter()

_COMPAT_ORIGINALS = {
    "load_report_payload": load_report_payload,
    "build_chart_data": build_chart_data,
    "build_natal_chart_svg": build_natal_chart_svg,
    "build_report_context": build_report_context,
    "build_week_brief_payload": build_week_brief_payload,
    "build_week_brief_envelope": build_week_brief_envelope,
}


def _compat(name: str):
    import sys

    local_value = globals()[name]
    original_value = _COMPAT_ORIGINALS.get(name)
    if local_value is not original_value:
        return local_value
    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, name):
        main_value = getattr(main_module, name)
        if main_value is not original_value:
            return main_value
    return local_value

# START_BLOCK: ROUTER_EXTRACTION
@router.post(
    "/api/workflows/report/async",
    response_model=ReportWorkflowStartResponse,
)
# START_CONTRACT: FN-CREATE-REPORT-ASYNC
async def create_report_async(
    payload: ReportWorkflowRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Run an end-to-end report generation workflow asynchronously.
    # INPUT: ReportWorkflowRequest payload.
    # OUTPUT: ReportWorkflowStartResponse.
    # CONTEXT: Primary entry point for report generation with progress UI.
    """
    client = upsert_client_from_payload(payload, db)
    db.flush()

    access_decision = _resolve_legacy_workflow_access(user, payload.report_type, db)

    report = Report(
        client_id=client.id,
        user_id=user.id,
        report_type=payload.report_type,
        status="in_progress",
        paid=False,
        is_test=client.is_test,
    )
    report.input_payload = json.dumps(payload.model_dump(), ensure_ascii=True)
    db.add(report)
    db.flush()
    _consume_legacy_workflow_access_if_needed(
        user,
        report,
        db,
        access_decision=access_decision,
    )

    if payload.report_type == "week_forecast":
        logger.info("week_generate_started", user_id=str(user.id), report_id=str(report.id))

    section_specs = build_section_specs(payload)
    initialize_report_chunks(report, section_specs, db, reset=True)
    db.commit()

    background_tasks.add_task(
        run_report_generation, report.id, payload.model_dump(), False
    )

    return {
        "report_id": str(report.id),
        "client_id": str(client.id),
        "status": report.status,
    }
# END_CONTRACT: FN-CREATE-REPORT-ASYNC


@router.post(
    "/api/workflows/report",
    response_model=ReportWorkflowResponse,
)
# START_CONTRACT: FN-CREATE-REPORT
async def create_report(
    payload: ReportWorkflowRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Run an end-to-end report generation workflow synchronously.
    # INPUT: ReportWorkflowRequest payload.
    # OUTPUT: ReportWorkflowResponse with sections and chart.
    # CONTEXT: Legacy/Dev entry point for direct report generation.
    """
    client = upsert_client_from_payload(payload, db)
    db.flush()

    access_decision = _resolve_legacy_workflow_access(user, payload.report_type, db)

    report = Report(
        client_id=client.id,
        user_id=user.id,
        report_type=payload.report_type,
        status="in_progress",
        paid=False,
        is_test=client.is_test,
    )
    report.input_payload = json.dumps(payload.model_dump(), ensure_ascii=True)
    db.add(report)
    db.flush()
    _consume_legacy_workflow_access_if_needed(
        user,
        report,
        db,
        access_decision=access_decision,
    )

    if payload.report_type == "week_forecast":
        logger.info("week_generate_started", user_id=str(user.id), report_id=str(report.id))

    # LLM Setup
    llm_mode = resolve_llm_mode(payload)
    llm_client = None
    if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
        try:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)
        except ValueError as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = start_report_run(report, db)
    try:
        generated_sections, chart_data = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=True,
            raise_on_error=True,
            run=run,
        )
    except Exception as exc:
        report.status = "failed"
        report.error_message = str(exc)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        finish_report_run(run, db, "failed", error_message=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    finish_report_run(run, db, "completed")
    log_analytics_event(
        db,
        "report_generated",
        user_id=user.id,
        telegram_id=user.telegram_id,
        source="backend",
        metadata={
            "report_id": str(report.id),
            "report_type": report.report_type,
            "client_id": str(report.client_id),
        },
    )

    return {
        "report_id": str(report.id),
        "client_id": str(client.id),
        "sections": generated_sections,
        "chart": chart_data,
    }
# END_CONTRACT: FN-CREATE-REPORT


@router.post(
    "/api/admin/reports/{report_id}/regenerate",
    response_model=ReportRegenerateResponse,
)
async def regenerate_report(
    report_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Regenerate all report sections and markdown.
    # INPUT: report_id path param.
    # OUTPUT: ReportRegenerateResponse with fresh sections.
    # CONTEXT: Admin-only full regeneration.
    """

    report = get_report_or_404(report_id, db)
    payload = _compat("load_report_payload")(report)

    llm_mode = resolve_llm_mode(payload)
    llm_client = None
    if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
        try:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = start_report_run(report, db)
    try:
        generated_sections, chart_data = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=True,
            raise_on_error=True,
            run=run,
        )
    except Exception as exc:
        report.status = "failed"
        report.error_message = str(exc)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        finish_report_run(run, db, "failed", error_message=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    finish_report_run(run, db, "completed")

    return {
        "report_id": str(report.id),
        "status": report.status,
        "sections": generated_sections,
    }


@router.post(
    "/api/admin/reports/{report_id}/regenerate/async",
    response_model=ReportWorkflowStartResponse,
)
def regenerate_report_async(
    report_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Regenerate all report sections asynchronously.
    # INPUT: report_id path param.
    # OUTPUT: ReportWorkflowStartResponse.
    # CONTEXT: Admin-only full regeneration with progress UI.
    """

    report = get_report_or_404(report_id, db)
    payload = _compat("load_report_payload")(report)
    section_specs = build_section_specs(payload)

    report.status = "in_progress"
    report.error_message = None
    report.error_at = None

    initialize_report_chunks(report, section_specs, db, reset=True)
    db.commit()

    background_tasks.add_task(
        run_report_generation,
        report.id,
        payload.model_dump(),
        True,
    )

    return {
        "report_id": str(report.id),
        "client_id": str(report.client_id),
        "status": report.status,
    }


@router.post(
    "/api/admin/reports/{report_id}/sections/{section_id}/regenerate",
    response_model=ReportRegenerateResponse,
)
async def regenerate_report_section(
    report_id: str,
    section_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Regenerate a single report section and refresh markdown.
    # INPUT: report_id, section_id path params.
    # OUTPUT: ReportRegenerateResponse with updated section.
    # CONTEXT: Admin-only section regeneration.
    """

    report = get_report_or_404(report_id, db)
    payload = _compat("load_report_payload")(report)
    section_specs = build_section_specs(payload)
    target_spec = next(
        (spec for spec in section_specs if spec.section_id == section_id),
        None,
    )
    if not target_spec:
        log_admin_report_event("admin.error", admin=admin, report=report, stage="section_missing", section_id=section_id)
        raise HTTPException(status_code=404, detail="Section not found.")

    llm_mode = resolve_llm_mode(payload)
    llm_client = None
    if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
        try:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = start_report_run(report, db)
    try:
        chart_data = _compat("build_chart_data")(payload)
        context = _compat("build_report_context")(payload, chart_data)

        # Context Anonymization
        section_context = build_section_context(section_id, context, chart_data)
        if section_id != "input_frame":
            section_context["client"]["name"] = "Ты"
            section_context["client"]["note"] = ""

        chunk_map = initialize_report_chunks(report, section_specs, db, reset=False)
        report.status = "in_progress"
        report.error_message = None
        report.error_at = None

        try:
            target_chunk = chunk_map.get(section_id)
            if target_chunk:
                target_chunk.status = "in_progress"
                target_chunk.error_message = None
                target_chunk.error_at = None
            db.commit()

            retry_attempts = resolve_llm_retry_attempts()
            fallback_models = []
            if llm_mode in {"openrouter", "cheap"}:
                model = resolve_llm_fallback_model()
                if model:
                    fallback_models = [model]
            use_template = llm_mode in {"fallback", "local", "mock", "stub"}

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
            
            logger.info("regen.result", section_id=target_spec.section_id, content_len=len(content))

            if not content:
                content = "Content generation failed (empty result)."
                logger.error("regen.empty_content", section=target_spec.section_id)

            generated_sections = [
                SectionResultOut(
                    section_id=target_spec.section_id,
                    title=target_spec.title,
                    content=content,
                )
            ]
        except Exception as exc:
            if should_fallback_on_llm_error(exc) or isinstance(exc, LLMContentValidationError):
                if isinstance(exc, LLMContentValidationError):
                    content = inject_planet_emojis(
                        build_section_validation_fallback_content(target_spec, section_context)
                    )
                else:
                    content = inject_planet_emojis(build_section_fallback_content(target_spec, section_context))
                generated_sections = [
                    SectionResultOut(
                        section_id=target_spec.section_id,
                        title=target_spec.title,
                        content=content,
                    )
                ]
                logger.warning(
                    "report.section.regen.fallback",
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
                raise HTTPException(status_code=502, detail=str(exc)) from exc

        result = generated_sections[0]
        target_chunk = chunk_map.get(section_id)
        if target_chunk:
            target_chunk.content = result.content
            target_chunk.status = "completed"
            target_chunk.error_message = None
            target_chunk.error_at = None
        else:
            target_chunk = ReportChunk(
                report_id=report.id,
                section=section_id,
                content=result.content,
                status="completed",
            )
            db.add(target_chunk)
            chunk_map[section_id] = target_chunk
        db.commit()

        report.status = "completed"
        db.commit()
        finish_report_run(run, db, "completed")
    except HTTPException:
        raise
    except Exception as exc:
        report.status = "failed"
        report.error_message = str(exc)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        finish_report_run(run, db, "failed", error_message=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "report_id": str(report.id),
        "status": report.status,
        "sections": generated_sections,
    }


@router.post(
    "/api/admin/reports/{report_id}/sections/{section_id}/regenerate/async",
    response_model=ReportWorkflowStartResponse,
)
def regenerate_report_section_async(
    report_id: str,
    section_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Regenerate a single report section asynchronously.
    # INPUT: report_id, section_id path params.
    # OUTPUT: ReportWorkflowStartResponse.
    # CONTEXT: Admin-only section regeneration with progress UI.
    """

    report = get_report_or_404(report_id, db)
    payload = _compat("load_report_payload")(report)
    section_specs = build_section_specs(payload)
    target_spec = next(
        (spec for spec in section_specs if spec.section_id == section_id),
        None,
    )
    if not target_spec:
        raise HTTPException(status_code=404, detail="Section not found.")

    report.status = "in_progress"
    report.error_message = None
    report.error_at = None

    chunk_map = initialize_report_chunks(report, section_specs, db, reset=False)
    target_chunk = chunk_map.get(section_id)
    if target_chunk:
        target_chunk.status = "in_progress"
        target_chunk.error_message = None
        target_chunk.error_at = None

    db.commit()
    log_admin_report_event("admin.section_regenerate", admin=admin, report=report, section_id=section_id, stage="queued", pending=sum(1 for chunk in report.chunks if chunk.status == "pending"), running=sum(1 for chunk in report.chunks if chunk.status == "in_progress"), error=sum(1 for chunk in report.chunks if chunk.status in {"failed", "error"}))
    background_tasks.add_task(
        run_report_section_generation,
        report.id,
        section_id,
        payload.model_dump(),
    )

    return {
        "report_id": str(report.id),
        "client_id": str(report.client_id),
        "status": report.status,
    }

@router.get("/api/reports/my", response_model=List[UserReportOut])
def get_my_reports(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: List reports belonging to the current user (last 30 days).
    # INPUT: Auth Dependency.
    # OUTPUT: List of user reports.
    """
    log_history_start(user, limit=limit, offset=offset)
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        reports = (
            db.query(Report)
            .filter(Report.user_id == user.id)
            .filter(Report.created_at >= cutoff)
            .order_by(Report.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        items = [
            {
                "id": str(r.id),
                "report_type": r.report_type,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "client_name": r.client.full_name if r.client else "Unknown",
                "access_source": r.access_source,
            }
            for r in reports
        ]
        log_history_success(user, count=len(items), has_more=len(reports) == limit)
        return items
    except HTTPException as exc:
        log_history_error(user, error=str(exc.detail or exc), status_code=exc.status_code)
        raise
    except Exception as exc:
        log_history_error(user, error=str(exc))
        raise

@router.get("/api/reports/{report_id}", response_model=ReportDetailOut)
# START_BLOCK: API_REPORT_DETAIL_ROUTE
# START_CONTRACT: FN-GET-REPORT-DETAIL
def get_report_detail(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Get full report content for the owner.
    """
    log_report_detail_start(user, report_id=report_id)
    try:
        try:
            r_uuid = uuid.UUID(report_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID")

        report = db.query(Report).filter(Report.id == r_uuid, Report.user_id == user.id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        chunks_out = []
        sorted_chunks = sorted(report.chunks, key=lambda c: c.order_index)

        for chunk in sorted_chunks:
            if chunk.section != "input_frame":  # Optionally exclude technical chunks
                chunks_out.append({
                    "section": chunk.section,
                    "content": chunk.content,
                    "status": chunk.status,
                    "order_index": chunk.order_index,
                })

        chart_svg = None
        week_brief = None
        week_brief_envelope = None
        payload = None
        chart_data = None
        try:
            payload = _compat("load_report_payload")(report)
        except Exception as e:
            logger.warning("report.payload_load_failed", report_id=str(report.id), error=str(e))

        if payload is not None:
            try:
                chart_data = _compat("build_chart_data")(payload)
            except Exception as e:
                logger.warning("report.chart_data_failed", report_id=str(report.id), error=str(e))

        if chart_data is not None:
            try:
                chart_svg = _compat("build_natal_chart_svg")(chart_data)
            except Exception as e:
                logger.warning("svg.gen_failed", report_id=str(report.id), error=str(e))

        if report.report_type == "week_forecast":
            context = {}
            if payload is not None and chart_data is not None:
                try:
                    context = _compat("build_report_context")(payload, chart_data)
                except Exception as e:
                    logger.warning("week_brief.context_failed", report_id=str(report.id), error=str(e))
            try:
                week_brief = _compat("build_week_brief_payload")(
                    report=report,
                    payload=payload,
                    context=context,
                    chunks=sorted_chunks,
                    user=user,
                    llm_model=getattr(payload, "llm_mode", None) if payload is not None else None,
                )
            except Exception as e:
                logger.warning("week_brief.build_failed", report_id=str(report.id), error=str(e))
                week_brief = None
            try:
                week_brief_envelope = _compat("build_week_brief_envelope")(report=report, week_brief=week_brief)
            except Exception as e:
                logger.warning("week_brief.envelope_failed", report_id=str(report.id), error=str(e))
                week_brief_envelope = None

        response = {
            "report": {
                "id": str(report.id),
                "report_type": report.report_type,
                "status": report.status,
                "created_at": report.created_at.isoformat(),
                "client_name": report.client.full_name if report.client else "Unknown",
                "access_source": report.access_source,
            },
            "chart_svg": chart_svg,
            "chunks": chunks_out,
            "week_brief": week_brief,
            "week_brief_envelope": week_brief_envelope,
        }
        if report.report_type == "week_forecast" and week_brief_envelope is not None:
            explainability = week_brief.get("explainability") if isinstance(week_brief, dict) else {}
            _log_api_gateway_event(
                "info",
                "week_brief.response_returned",
                fn="get_report_detail",
                block="API_REPORT_DETAIL_ROUTE",
                path="/api/reports/{report_id}",
                report_id=str(report.id),
                report_type=report.report_type,
                status=week_brief_envelope.get("status"),
                factor_count=explainability.get("factor_count") if isinstance(explainability, dict) else None,
            )
        log_report_detail_success(user, report=report, chunk_count=len(chunks_out))
        return response
    except HTTPException as exc:
        log_report_detail_error(user, report_id=report_id, error=str(exc.detail or exc), status_code=exc.status_code)
        raise
    except Exception as exc:
        log_report_detail_error(user, report_id=report_id, error=str(exc))
        raise
# END_CONTRACT: FN-GET-REPORT-DETAIL
# END_BLOCK: API_REPORT_DETAIL_ROUTE



@router.post("/api/reports/{report_id}/regenerate", response_model=ReportWorkflowStartResponse)
def user_regenerate_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Allow user to retry generation of a failed report.
    # INPUT: report_id.
    # OUTPUT: ReportWorkflowStartResponse.
    """
    log_bridge_resume_start(None, user=user, surface="bridge_regenerate", report_id=report_id)

    try:
        rid = uuid.UUID(report_id)
    except ValueError as exc:
        log_catalog_surface_error(
            surface="bridge_regenerate",
            user=user,
            error="invalid_report_id",
            report_id=report_id,
            status_code=400,
        )
        raise HTTPException(status_code=400, detail="Invalid report ID") from exc

    report = db.query(Report).filter(Report.id == rid, Report.user_id == user.id).first()
    if not report:
        log_catalog_surface_error(
            surface="bridge_regenerate",
            user=user,
            error="report_not_found",
            report_id=report_id,
            status_code=404,
        )
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "failed":
        log_catalog_surface_error(
            surface="bridge_regenerate",
            user=user,
            report=report,
            error="report_not_failed",
            report_status=report.status,
            status_code=400,
        )
        raise HTTPException(status_code=400, detail="Only failed reports can be regenerated by user")
        
    payload = _compat("load_report_payload")(report)
    section_specs = build_section_specs(payload)

    report.status = "in_progress"
    report.error_message = None
    report.error_at = None

    initialize_report_chunks(report, section_specs, db, reset=True)
    db.commit()

    background_tasks.add_task(
        run_report_generation,
        report.id,
        payload.model_dump(),
        True,
    )

    log_bridge_resume_success(None, user=user, surface="bridge_regenerate", report=report)

    return {
        "report_id": str(report.id),
        "client_id": str(report.client_id),
        "status": report.status,
    }

# END_BLOCK: ROUTER_EXTRACTION
