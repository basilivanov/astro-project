# START_MODULE_CONTRACT: M-API-GATEWAY-ADMIN-USERS
# purpose: Expose admin user and task management routes.
# owns:
#   - backend/app/routers/admin-users.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-ADMIN-USERS

# START_MODULE_MAP: M-API-GATEWAY-ADMIN-USERS
# public_entrypoints:
#   - router
#   - list_admin_users
#   - get_admin_stats
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-ADMIN-USERS

from fastapi import APIRouter

from .gateway_context import *
from .gateway_runtime import run_report_generation, run_report_section_generation

router = APIRouter()

# START_BLOCK: ROUTER_EXTRACTION
@router.get("/api/admin/feedback", response_model=List[dict])
def list_admin_feedback(
    limit: int = 20,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: List recent user feedback.
    """
    rows = (
        db.query(ReportFeedback)
        .order_by(ReportFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    res = []
    for r in rows:
        res.append({
            "id": str(r.id),
            "report_id": str(r.report_id),
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
            "report_type": r.report.report_type if r.report else "unknown",
            "client_name": r.report.client.full_name if r.report and r.report.client else "—"
        })
    return res

@router.get("/api/admin/audit", response_model=List[AdminAuditLogOut])
def list_admin_audit_logs(
    limit: int = 50,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: View audit logs for security and history.
    """
    from ..models import AuditLog
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    
    if user_id:
        try:
            uid = uuid.UUID(user_id)
            query = query.filter(or_(AuditLog.target_user_id == uid, AuditLog.admin_id == uid))
        except ValueError:
            pass
            
    if action:
        query = query.filter(AuditLog.action == action)
        
    logs = query.limit(limit).all()
    
    res = []
    for l in logs:
        res.append({
            "id": str(l.id),
            "admin_id": str(l.admin_id) if l.admin_id else None,
            "target_user_id": str(l.target_user_id) if l.target_user_id else None,
            "action": l.action,
            "reason": l.reason,
            "details": l.details,
            "created_at": format_datetime(l.created_at),
            "admin_name": l.admin.full_name if l.admin else "System",
            "target_user_name": l.target_user.full_name if l.target_user else "—"
        })
    return res




@router.get("/api/admin/users/{user_id}", response_model=AdminUserDetailOut)

def get_admin_user_detail(

    user_id: str,

    db: Session = Depends(get_db),

    admin: User = Depends(get_admin_user)

):
    """
    # PURPOSE: Get full user profile for admin.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
        
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Reports
    reports = (
        db.query(Report)
        .filter(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Transactions
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Referrals
    from ..models import Referral
    ref_count = db.query(func.count(Referral.id)).filter(Referral.referrer_id == user.id).scalar() or 0
    report_count = db.query(func.count(Report.id)).filter(Report.user_id == user.id).scalar() or 0

    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "username": user.username,
        "balance": float(user.balance),
        "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
        "created_at": user.created_at.isoformat(),
        "is_partner": user.is_partner,
        "referral_code": user.referral_code,
        "reports_count": report_count,
        "referrals_count": ref_count,
        "recent_reports": [
            {
                "id": str(r.id),
                "type": r.report_type,
                "status": r.status,
                "created_at": r.created_at.isoformat()
            } for r in reports
        ],
        "recent_transactions": [
            {
                "id": str(t.id),
                "amount": float(t.amount),
                "type": t.type,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            } for t in txs
        ]
    }

@router.post("/api/admin/users/{user_id}/subscription/add-days")
def admin_add_subscription_days(
    user_id: str, 
    payload: AdminUserUpdateDays,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Manually extend user subscription (Audit Logged).
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
        
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    now = datetime.now(timezone.utc)
    current_end = user.subscription_active_until
    if current_end and current_end.tzinfo is None:
        current_end = current_end.replace(tzinfo=timezone.utc)
        
    if current_end and current_end > now:
        user.subscription_active_until = current_end + timedelta(days=payload.days)
    else:
        user.subscription_active_until = now + timedelta(days=payload.days)
    
    # Audit Log
    from ..models import AuditLog
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=user.id,
        action="add_subscription_days",
        reason=payload.reason,
        details=json.dumps({"days": payload.days})
    )
    db.add(audit)
        
    db.commit()
    return {"status": "ok", "new_date": format_datetime(user.subscription_active_until)}

@router.post("/api/admin/users/{user_id}/balance/add")
def admin_add_balance(
    user_id: str,
    payload: AdminUserUpdateBalance,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Manually add credits/money (Audit Logged).
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from decimal import Decimal
    user.balance += Decimal(payload.amount)
    
    # Audit Log
    from ..models import AuditLog
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=user.id,
        action="add_balance",
        reason=payload.reason,
        details=json.dumps({"amount": payload.amount})
    )
    db.add(audit)

    db.commit()
    return {"status": "ok", "new_balance": float(user.balance)}


@router.post("/api/admin/users/{user_id}/grant")
def admin_grant_item(
    user_id: str,
    payload: AdminGrantRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    # PURPOSE: Grant credits or specific report to user.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
        
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from ..models import AuditLog
    details = {}

    if payload.type == "credits":
        if not payload.amount:
            raise HTTPException(status_code=400, detail="Amount required for credits")
        
        # Add transaction
        trx = Transaction(
            user_id=user.id,
            amount=payload.amount,
            currency="CRD",
            type="admin_grant",
            status="success",
            provider_id=f"grant_{admin.id}_{datetime.now().timestamp()}"
        )
        db.add(trx)
        details["amount"] = payload.amount
        details["currency"] = "CRD"

    elif payload.type == "report":
        if not payload.report_type:
            raise HTTPException(status_code=400, detail="Report type required")

        report_type = payload.report_type
        entitlement = None
        one_off_admin_grant = is_one_off_report_type(report_type)

        # Check profile
        if not user.birth_date or not user.birth_place:
            raise HTTPException(status_code=400, detail="User profile incomplete, cannot generate report.")

        # Create Report
        birth_dt_iso = user.birth_date
        if user.birth_time:
            birth_dt_iso = f"{user.birth_date}T{user.birth_time}:00"

        wf_payload = ReportWorkflowRequest(
            client_name=user.full_name or "User",
            client_note=f"Gift from admin {admin.telegram_id}",
            birth_date=birth_dt_iso,
            birth_location=user.birth_place,
            birth_lat=user.birth_lat,
            birth_lon=user.birth_lon,
            report_type=report_type,
            house_system="placidus",
            include_fixed_stars=True
        )
        
        # Upsert client (reuse logic?)
        # We can just use user_id directly if we link it. 
        # But Report model needs client_id. 
        # Upsert client from payload helper:
        client = upsert_client_from_payload(wf_payload, db, owner_user_id=user.id)
        db.flush()

        if one_off_admin_grant:
            entitlement = grant_report_entitlement(
                db,
                user_id=user.id,
                report_type=report_type,
                source=EntitlementSource.ADMIN_GRANT,
                notes=payload.reason,
            )

        report = Report(
            client_id=client.id,
            user_id=user.id,
            report_type=report_type,
            status="in_progress",
            paid=not one_off_admin_grant,
            is_test=user.is_test
        )
        report.input_payload = json.dumps(wf_payload.model_dump(), ensure_ascii=True)
        db.add(report)
        db.flush()

        if entitlement is not None:
            try:
                consume_report_access(
                    user,
                    report,
                    db,
                    decision=allow_access(
                        report_type,
                        AccessGrantSource.REPORT_ENTITLEMENT,
                        entitlement_id=str(entitlement.id),
                        remaining_unlocks=1,
                    ),
                )
            except AccessConsumptionError as exc:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=f"Admin grant could not be consumed: {exc}",
                ) from exc

        # Run generation
        section_specs = build_section_specs(wf_payload)
        initialize_report_chunks(report, section_specs, db, reset=True)
        
        background_tasks.add_task(
            run_report_generation, report.id, wf_payload.model_dump(), False
        )

        details["report_type"] = report_type
        details["report_id"] = str(report.id)
        if entitlement is not None:
            details["entitlement_id"] = str(entitlement.id)
            details["access_source"] = report.access_source
            details["grant_model"] = "entitlement_first"

    else:
        raise HTTPException(status_code=400, detail="Invalid grant type")

    # Audit
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=user.id,
        action=f"grant_{payload.type}",
        reason=payload.reason,
        details=json.dumps(details)
    )
    db.add(audit)
    db.commit()
    
    return {"status": "ok", "details": details}


@router.get("/api/admin/users", response_model=List[AdminUserOut])
def list_admin_users(
    limit: int = 50, 
    q: Optional[str] = None, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: List Telegram users for admin management.
    """
    query = db.query(User)
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search),
                User.username.ilike(search),
                User.referral_code.ilike(search)
            )
        )
    
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    
    results = []
    for u in users:
        credits = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == u.id, 
            Transaction.currency == "CRD"
        ).scalar() or 0
        
        results.append({
            "id": str(u.id),
            "telegram_id": u.telegram_id,
            "full_name": u.full_name,
            "username": u.username,
            "balance": float(u.balance),
            "subscription_active_until": format_datetime(u.subscription_active_until),
            "created_at": format_datetime(u.created_at),
            "is_partner": u.is_partner,
            "referral_code": u.referral_code,
            "horary_credits": int(credits)
        })
    
    return results

@router.get("/api/admin/stats", response_model=AdminStatsOut)
def get_admin_stats(
    days: int = 7,
    show_test: bool = False,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Return admin dashboard counters.
    # INPUT: days (window size).
    # OUTPUT: AdminStatsOut.
    # CONTEXT: Used by the admin UI dashboard.
    """

    window_days = max(1, min(days, 30))
    
    clients_query = db.query(func.count(Client.id))
    reports_query = db.query(Report)
    
    if not show_test:
        clients_query = clients_query.filter(Client.is_test == False)
        reports_query = reports_query.filter(Report.is_test == False)

    clients = clients_query.scalar() or 0
    reports_total = reports_query.count()
    
    reports_in_progress = (
        reports_query
        .filter(Report.status == "in_progress")
        .count()
    )
    reports_completed = (
        reports_query
        .filter(Report.status == "completed")
        .count()
    )
    reports_failed = (
        reports_query
        .filter(Report.status == "failed")
        .count()
    )

    report_type_rows = (
        reports_query
        .with_entities(Report.report_type, func.count(Report.id))
        .group_by(Report.report_type)
        .all()
    )
    reports_by_type = {row[0]: int(row[1]) for row in report_type_rows}

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=window_days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    
    daily_rows = (
        reports_query
        .with_entities(func.date(Report.created_at).label("day"), func.count(Report.id))
        .filter(Report.created_at >= start_dt)
        .group_by("day")
        .order_by("day")
        .all()
    )
    daily_map = {str(row[0]): int(row[1]) for row in daily_rows}
    reports_daily = []
    for offset in range(window_days):
        day = start_date + timedelta(days=offset)
        day_key = day.isoformat()
        reports_daily.append(
            {
                "date": day_key,
                "count": daily_map.get(day_key, 0),
            }
        )

    tasks_total = db.query(func.count(AgentTask.id)).scalar() or 0
    tasks_open = (
        db.query(func.count(AgentTask.id))
        .filter(AgentTask.status.in_(["queued", "approved", "running"]))
        .scalar()
        or 0
    )

    analytics_rows = (
        db.query(AnalyticsEvent.event_name, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.created_at >= start_dt)
        .group_by(AnalyticsEvent.event_name)
        .all()
    )
    analytics_funnel = {name: 0 for name in ALLOWED_ANALYTICS_EVENTS}
    for name, count in analytics_rows:
        analytics_funnel[name] = int(count)

    feedback_stats = db.query(
        func.avg(ReportFeedback.rating),
        func.count(ReportFeedback.id)
    ).first()
    
    feedback_avg = float(feedback_stats[0]) if feedback_stats[0] else 0
    feedback_count = int(feedback_stats[1]) if feedback_stats[1] else 0

    # Entitlement Stats
    total_balance = db.query(func.sum(User.balance)).scalar() or 0
    active_subs = db.query(func.count(User.id)).filter(User.subscription_active_until > datetime.now(timezone.utc)).scalar() or 0
    horary_credits = db.query(func.sum(Transaction.amount)).filter(Transaction.currency == "CRD").scalar() or 0

    return {
        "clients": clients,
        "reports_total": reports_total,
        "reports_in_progress": reports_in_progress,
        "reports_completed": reports_completed,
        "reports_failed": reports_failed,
        "reports_by_type": reports_by_type,
        "reports_daily": reports_daily,
        "tasks_open": tasks_open,
        "tasks_total": tasks_total,
        "analytics_funnel": analytics_funnel,
        "feedback_avg": feedback_avg,
        "feedback_count": feedback_count,
        "entitlements": {
            "total_balance_rub": float(total_balance),
            "active_subscriptions": active_subs,
            "outstanding_credits": int(horary_credits)
        }
    }


@router.get("/api/admin/tasks", response_model=List[AdminTaskOut])
def get_admin_tasks(
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Return recent operator tasks from the bot.
    # INPUT: limit, status.
    # OUTPUT: List of AdminTaskOut.
    # CONTEXT: Used by the admin dashboard.
    """

    query = db.query(AgentTask).order_by(AgentTask.created_at.desc())
    if status:
        query = query.filter(AgentTask.status == status)
    tasks = query.limit(limit).all()

    payload = []
    for task in tasks:
        payload.append(
            {
                "id": str(task.id),
                "user_id": str(task.user_id) if task.user_id else None,
                "telegram_id": task.telegram_id,
                "status": task.status,
                "source": task.source,
                "transcript": task.transcript,
                "summary": task.summary,
                "clarification": task.clarification,
                "voice_file_id": task.voice_file_id,
                "report_id": str(task.report_id) if task.report_id else None,
                "result_summary": task.result_summary,
                "error_message": task.error_message,
                "created_at": format_datetime(task.created_at),
                "updated_at": format_datetime(task.updated_at),
                "approved_at": format_datetime(task.approved_at),
                "completed_at": format_datetime(task.completed_at),
            }
        )
    return payload


@router.patch("/api/admin/tasks/{task_id}", response_model=AdminTaskOut)
def update_admin_task(
    task_id: str,
    payload: AdminTaskUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: Update a task created via the bot.
    # INPUT: task_id, update payload.
    # OUTPUT: Updated task.
    # CONTEXT: Used by admin UI and automation.
    """

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid task id.") from exc

    task = db.query(AgentTask).filter(AgentTask.id == task_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if payload.status is not None:
        task.status = payload.status
        if payload.status == "approved" and not task.approved_at:
            task.approved_at = datetime.now(timezone.utc)
        if payload.status in {"completed", "failed"} and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
    if payload.summary is not None:
        task.summary = payload.summary
    if payload.clarification is not None:
        task.clarification = payload.clarification
    if payload.result_summary is not None:
        task.result_summary = payload.result_summary
    if payload.error_message is not None:
        task.error_message = payload.error_message
    if payload.report_id is not None:
        if payload.report_id:
            try:
                task.report_id = uuid.UUID(payload.report_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail="Invalid report id."
                ) from exc
        else:
            task.report_id = None

    db.commit()
    db.refresh(task)

    return {
        "id": str(task.id),
        "user_id": str(task.user_id) if task.user_id else None,
        "telegram_id": task.telegram_id,
        "status": task.status,
        "source": task.source,
        "transcript": task.transcript,
        "summary": task.summary,
        "clarification": task.clarification,
        "voice_file_id": task.voice_file_id,
        "report_id": str(task.report_id) if task.report_id else None,
        "result_summary": task.result_summary,
        "error_message": task.error_message,
        "created_at": format_datetime(task.created_at),
        "updated_at": format_datetime(task.updated_at),
        "approved_at": format_datetime(task.approved_at),
        "completed_at": format_datetime(task.completed_at),
    }

# END_BLOCK: ROUTER_EXTRACTION
