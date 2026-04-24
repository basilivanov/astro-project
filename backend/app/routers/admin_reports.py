# START_MODULE_CONTRACT: M-API-GATEWAY-ADMIN-REPORTS
# purpose: Expose admin report, ticket, feedback, and broadcast routes.
# owns:
#   - backend/app/routers/admin-reports.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-ADMIN-REPORTS

# START_MODULE_MAP: M-API-GATEWAY-ADMIN-REPORTS
# public_entrypoints:
#   - router
#   - get_admin_report
#   - list_admin_reports
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-ADMIN-REPORTS

from fastapi import APIRouter

from .gateway_context import *

router = APIRouter()

# START_BLOCK: ROUTER_EXTRACTION
@router.post("/api/admin/reports/{report_id}/regenerate_copy")
def regenerate_report_copy(
    report_id: str,
    payload: Optional[AdminRegenerateRequest] = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    # PURPOSE: Create a fresh copy of a report and regenerate it.
    """
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    old_report = db.query(Report).filter(Report.id == rid).first()
    if not old_report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Clone logic
    new_report = Report(
        client_id=old_report.client_id,
        user_id=old_report.user_id,
        report_type=old_report.report_type,
        status="in_progress",
        paid=old_report.paid,
        is_test=old_report.is_test,
        input_payload=old_report.input_payload # Copy payload
    )
    db.add(new_report)
    db.commit()
    
    # Audit
    from ..models import AuditLog
    reason = payload.reason if payload else "Manual regeneration"
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=old_report.user_id,
        action="regenerate_copy",
        reason=reason,
        details=json.dumps({"original_id": str(old_report.id), "new_id": str(new_report.id)})
    )
    db.add(audit)
    db.commit()
    
    # Start generation
    if new_report.input_payload:
        try:
            payload_data = json.loads(new_report.input_payload)
            # Re-init chunks
            section_specs = build_section_specs(ReportWorkflowRequest.model_validate(payload_data))
            initialize_report_chunks(new_report, section_specs, db, reset=True)
            db.commit()
            
            background_tasks.add_task(
                run_report_generation, new_report.id, payload_data, False
            )
        except Exception as e:
            logger.error("regen.copy.failed", error=str(e))
            
    return {"status": "ok", "new_report_id": str(new_report.id)}

@router.get("/api/admin/tickets", response_model=List[AdminTicketOut])
def list_admin_tickets(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: List support tickets for admin.
    """
    from ..models import SupportTicket
    query = db.query(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status:
        query = query.filter(SupportTicket.status == status)

    tickets = query.limit(limit).all()

    results = []
    for t in tickets:
        results.append({
            "id": str(t.id),
            "user_id": str(t.user_id),
            "username": t.user.username if t.user else None,
            "topic": t.topic,
            "status": t.status,
            "message": t.message,
            "created_at": format_datetime(t.created_at)
        })
    return results




@router.post("/api/admin/broadcast")
async def admin_broadcast(
    payload: AdminBroadcastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Start a background task to broadcast a message to all users.
    """
    # We could also restrict this to admin users only if we had an admin check.
    # For now, it's an internal admin-only endpoint by convention.

    background_tasks.add_task(run_mass_broadcast, payload.text, payload.image_url)
    return {"status": "broadcast_started"}


async def run_mass_broadcast(text: str, image_url: Optional[str] = None):
    """
    # PURPOSE: Send messages to all Telegram users with batching.
    """
    from ..services.notification import send_bot_notification
    db = SessionLocal()
    try:
        # Get all users with telegram_id
        users = db.query(User).filter(User.telegram_id.isnot(None)).all()
        logger.info("broadcast.start", total_users=len(users))

        batch_size = 20
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            tasks = []
            for user in batch:
                tasks.append(send_bot_notification(user.telegram_id, text, image_url))

            await asyncio.gather(*tasks)
            logger.info("broadcast.batch_sent", offset=i, size=len(batch))

            # Wait 1 second between batches to stay under TG limits (30/sec)
            await asyncio.sleep(1.0)

        logger.info("broadcast.complete")
    finally:
        db.close()


@router.get("/api/admin/reports", response_model=List[AdminReportOut])
def list_admin_reports(
    status: Optional[str] = None,
    show_test: bool = False,
    limit: int = 25,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Return reports with client names and chunk counts.
    # INPUT: status (optional), limit, offset.
    # OUTPUT: List[AdminReportOut].
    # CONTEXT: Used by the admin UI reports list.
    """

    query = db.query(Report).order_by(Report.created_at.desc())
    
    if not show_test:
        query = query.filter(Report.is_test == False)

    if status:
        query = query.filter(Report.status == status)
    rows = query.offset(offset).limit(limit).all()
    log_admin_report_event("admin.queue", admin=admin, stage="list", queue_size=len(rows), status_filter=status, show_test=show_test)

    results = []
    for report in rows:
        results.append(
            {
                "id": str(report.id),
                "report_type": report.report_type,
                "status": report.status,
                "paid": report.paid,
                "error_message": report.error_message,
                "error_at": format_datetime(report.error_at),
                "created_at": format_datetime(report.created_at),
                "updated_at": format_datetime(report.updated_at),
                "client_id": str(report.client_id),
                "client_name": report.client.full_name if report.client else "",
                "chunk_count": len(report.chunks),
            }
        )

    return results


@router.get("/api/admin/reports/{report_id}", response_model=AdminReportDetailOut)
def get_admin_report(
    report_id: str,
    include_content: bool = True,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Return report detail with chunks and markdown.
    # INPUT: report_id.
    # OUTPUT: AdminReportDetailOut.
    # CONTEXT: Used by the admin report detail page.
    """

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report id.") from exc

    report = (
        db.query(Report)
        .filter(Report.id == report_uuid)
        .first()
    )
    if not report:
        log_admin_report_event("admin.error", admin=admin, stage="detail_missing", target_report_id=report_id)
        raise HTTPException(status_code=404, detail="Report not found.")
    log_admin_report_event("admin.entry", admin=admin, report=report, stage="detail", include_content=include_content, chunk_count=len(report.chunks), run_count=len(report.runs))

    chunks_sorted = sorted(report.chunks, key=lambda item: item.order_index)
    payload_data = safe_load_report_payload_data(report)
    section_specs = load_section_specs_for_report(report, payload_data)
    title_map = {spec.section_id: spec.title for spec in section_specs}
    chunks_payload = []
    for chunk in chunks_sorted:
        content_html = None
        # Legacy markdown_to_html removed
        chunks_payload.append(
            {
                "id": str(chunk.id),
                "section": chunk.section,
                "title": title_map.get(chunk.section),
                "status": chunk.status,
                "error_message": chunk.error_message,
                "error_at": format_datetime(chunk.error_at),
                "order_index": chunk.order_index,
                "content": chunk.content if include_content else None,
                "content_html": content_html,
                "created_at": format_datetime(chunk.created_at),
            }
        )

    runs_sorted = sorted(
        report.runs, key=lambda item: item.created_at, reverse=True
    )
    runs_payload = []
    for run in runs_sorted:
        runs_payload.append(
            {
                "id": str(run.id),
                "status": run.status,
                "error_message": run.error_message,
                "started_at": format_datetime(run.started_at),
                "finished_at": format_datetime(run.finished_at),
                "prompt_tokens": run.prompt_tokens,
                "completion_tokens": run.completion_tokens,
                "total_tokens": run.total_tokens,
                "estimated_cost": float(run.estimated_cost),
                "created_at": format_datetime(run.created_at),
            }
        )

    report_payload = {
        "id": str(report.id),
        "report_type": report.report_type,
        "status": report.status,
        "paid": report.paid,
        "error_message": report.error_message,
        "error_at": format_datetime(report.error_at),
        "created_at": format_datetime(report.created_at),
        "updated_at": format_datetime(report.updated_at),
        "client_id": str(report.client_id),
        "client_name": report.client.full_name if report.client else "",
        "chunk_count": len(report.chunks),
    }

    chart_svg = None
    if include_content:
        try:
            payload_model = load_report_payload(report)
            chart_data = build_chart_data(payload_model)
            chart_svg = build_natal_chart_svg(chart_data)
            logger.info("admin.svg.generated", report_id=str(report.id), svg_len=len(chart_svg or ""))
        except Exception as e:
            logger.warning("admin.svg.gen_failed", report_id=str(report.id), error=str(e))
            log_admin_report_event("admin.error", admin=admin, report=report, stage="chart_svg_failed")

    return {
        "report": report_payload,
        "chunks": chunks_payload,
        "runs": runs_payload,
        "chart_svg": chart_svg if include_content else None
    }


@router.get(
    "/api/admin/reports/{report_id}/sections/{section_id}",
    response_model=AdminReportChunkOut,
)
def get_admin_report_section(
    report_id: str,
    section_id: str,
    include_content: bool = True,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Return a single report chunk with optional content.
    # INPUT: report_id, section_id.
    # OUTPUT: AdminReportChunkOut.
    # CONTEXT: Used for lazy-loading section content in the admin UI.
    """

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report id.") from exc

    report = (
        db.query(Report)
        .filter(Report.id == report_uuid)
        .first()
    )
    if not report:
        log_admin_report_event("admin.error", admin=admin, stage="section_report_missing", target_report_id=report_id, section_id=section_id)
        raise HTTPException(status_code=404, detail="Report not found.")

    chunk = next((item for item in report.chunks if item.section == section_id), None)
    if not chunk:
        log_admin_report_event("admin.error", admin=admin, report=report, stage="section_missing", section_id=section_id)
        raise HTTPException(status_code=404, detail="Section not found.")
    log_admin_report_event("admin.entry", admin=admin, report=report, stage="section_detail", section_id=section_id, include_content=include_content, section_status=chunk.status)

    payload_data = safe_load_report_payload_data(report)
    section_specs = load_section_specs_for_report(report, payload_data)
    title_map = {spec.section_id: spec.title for spec in section_specs}

    content_html = None
    # Legacy markdown_to_html removed

    return {
        "id": str(chunk.id),
        "section": chunk.section,
        "title": title_map.get(chunk.section),
        "status": chunk.status,
        "error_message": chunk.error_message,
        "error_at": format_datetime(chunk.error_at),
        "order_index": chunk.order_index,
        "content": chunk.content if include_content else None,
        "content_html": content_html,
        "created_at": format_datetime(chunk.created_at),
    }

# END_BLOCK: ROUTER_EXTRACTION
