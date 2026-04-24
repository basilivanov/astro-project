# START_MODULE_CONTRACT: M-API-GATEWAY-B2C-REPORTS
# purpose: Expose B2C report creation route.
# owns:
#   - backend/app/routers/b2c-reports.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-B2C-REPORTS

# START_MODULE_MAP: M-API-GATEWAY-B2C-REPORTS
# public_entrypoints:
#   - router
#   - create_b2c_report
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-B2C-REPORTS

from fastapi import APIRouter

from .gateway_context import *
from .gateway_runtime import run_report_generation, run_report_section_generation
from .gateway_context import _validate_b2c_report_inputs

router = APIRouter()

# START_BLOCK: ROUTER_EXTRACTION
@router.post("/api/reports/create", response_model=ReportWorkflowStartResponse)
# START_BLOCK: API_B2C_REPORT_ROUTE
# START_CONTRACT: FN-CREATE-B2C-REPORT
def create_b2c_report(
    payload: B2CReportCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: B2C Endpoint to create a report (consumes quota/credits).
    # INPUT: report_type, question.
    # OUTPUT: Report metadata.
    """
    from ..services.access_control import (
        AccessConsumptionError,
        consume_report_access,
        resolve_report_access,
    )

    _validate_b2c_report_inputs(payload)

    log_checkout_start(user=user, report_type=payload.report_type)

    error_log_context: dict[str, Any] = {}
    semantic_checkout_block_logged = False

    try:
        access_decision = resolve_report_access(user, payload.report_type, db)
        error_log_context["decision"] = access_decision
        log_checkout_decision(user=user, report_type=payload.report_type, decision=access_decision)
        if not access_decision.allowed:
            log_checkout_denied(user=user, report_type=payload.report_type, decision=access_decision)
            semantic_checkout_block_logged = True
            raise HTTPException(
                status_code=402,
                detail="Access unavailable. Please check your subscription or payment status."
            )

        if not user.birth_date or not user.birth_place:
            error_log_context["error_phase"] = "profile_validation"
            log_checkout_denied(
                user=user,
                report_type=payload.report_type,
                decision=access_decision,
                reason="profile_incomplete",
            )
            semantic_checkout_block_logged = True
            raise HTTPException(
                status_code=400,
                detail="Profile incomplete. Please set birth data in Profile."
            )

        birth_dt_iso = user.birth_date
        if user.birth_time:
            birth_dt_iso = f"{user.birth_date}T{user.birth_time}:00"

        solar_current_location = payload.solar_current_location or user.current_location or user.birth_place
        solar_current_lat = payload.solar_current_lat or user.current_lat or user.birth_lat
        solar_current_lon = payload.solar_current_lon or user.current_lon or user.birth_lon
        solar_current_timezone = payload.solar_current_timezone or user.current_timezone or user.birth_timezone
        solar_current_place_id = payload.solar_current_place_id

        wf_payload = ReportWorkflowRequest(
            client_name=user.full_name or "User",
            client_note=f"Telegram ID: {user.telegram_id}",
            question=payload.question,
            birth_date=birth_dt_iso,
            birth_location=user.birth_place,
            birth_lat=user.birth_lat,
            birth_lon=user.birth_lon,
            birth_timezone=user.birth_timezone,
            partner_name=payload.partner_name,
            partner_birth_date=payload.partner_birth_date,
            partner_birth_location=payload.partner_birth_location,
            partner_birth_lat=payload.partner_birth_lat,
            partner_birth_lon=payload.partner_birth_lon,
            partner_birth_timezone=payload.partner_birth_timezone,
            partner_birth_place_id=payload.partner_birth_place_id,
            solar_current_location=solar_current_location,
            solar_current_lat=solar_current_lat,
            solar_current_lon=solar_current_lon,
            solar_current_timezone=solar_current_timezone,
            solar_current_place_id=solar_current_place_id,
            report_type=payload.report_type,
            birth_time_known=user.birth_time_known if user.birth_time_known is not None else True,
            llm_mode=payload.llm_mode,
            house_system="placidus",  # Default
            include_fixed_stars=True,
        )

        client = upsert_client_from_payload(wf_payload, db, owner_user_id=user.id)
        db.flush()

        report = Report(
            client_id=client.id,
            user_id=user.id,
            report_type=payload.report_type,
            status="in_progress",
            paid=False,
            is_test=user.is_test,
        )
        report.input_payload = json.dumps(wf_payload.model_dump(), ensure_ascii=True)
        db.add(report)
        db.flush()

        try:
            consume_report_access(user, report, db, decision=access_decision)
        except AccessConsumptionError as exc:
            error_log_context.update(
                {
                    "report": report,
                    "error_phase": "consume_report_access",
                    "error_detail": str(exc),
                }
            )
            log_checkout_denied(
                user=user,
                report_type=payload.report_type,
                decision=access_decision,
                reason="access_consume_conflict",
                report_id=str(report.id),
                error_detail=str(exc),
            )
            semantic_checkout_block_logged = True
            raise HTTPException(
                status_code=409,
                detail=f"Access could not be consumed: {exc}",
            ) from exc

        section_specs = build_section_specs(wf_payload)
        initialize_report_chunks(report, section_specs, db, reset=True)
        db.commit()

        log_checkout_success(
            user=user,
            report=report,
            decision=access_decision,
            access_source=report.access_source,
        )

        background_tasks.add_task(
            run_report_generation,
            report.id,
            wf_payload.model_dump(),
            False,
        )

        if payload.report_type == "week_forecast":
            logger.info("week_generate_started", user_id=str(user.id), report_id=str(report.id))

        if payload.report_type.startswith("horary"):
            log_analytics_event(
                db,
                "horary_asked",
                user_id=user.id,
                telegram_id=user.telegram_id,
                source="webapp",
                metadata={"question_len": len(payload.question or "")},
            )

        return {
            "report_id": str(report.id),
            "client_id": str(client.id),
            "status": report.status,
        }
    except HTTPException as exc:
        db.rollback()
        if exc.status_code >= 500:
            log_checkout_error(
                user=user,
                report=error_log_context.get("report"),
                report_type=payload.report_type,
                decision=error_log_context.get("decision"),
                status_code=exc.status_code,
                error=str(exc.detail or exc),
                error_phase=error_log_context.get("error_phase"),
                error_detail=error_log_context.get("error_detail"),
            )
        elif not semantic_checkout_block_logged:
            log_checkout_denied(
                user=user,
                report_type=payload.report_type,
                decision=error_log_context.get("decision"),
                reason=f"http_{exc.status_code}",
                status_code=exc.status_code,
                error=str(exc.detail or exc),
                error_phase=error_log_context.get("error_phase"),
                error_detail=error_log_context.get("error_detail"),
            )
        raise
    except Exception as exc:
        db.rollback()
        log_checkout_error(user=user, report_type=payload.report_type, error=str(exc))
        raise
# END_CONTRACT: FN-CREATE-B2C-REPORT
# END_BLOCK: API_B2C_REPORT_ROUTE

# #END_BLOCK_USER_ENDPOINTS
# #END_BLOCK_ENDPOINTS

# END_BLOCK: ROUTER_EXTRACTION
