# START_MODULE_CONTRACT: M-API-GATEWAY-PUBLIC
# purpose: Expose health, engine, geo, diagnostics, profile, analytics, feed, week and day routes.
# owns:
#   - backend/app/routers/public.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-PUBLIC

# START_MODULE_MAP: M-API-GATEWAY-PUBLIC
# public_entrypoints:
#   - router
#   - get_daily_feed
#   - get_day_brief
#   - get_my_profile
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-PUBLIC

from fastapi import APIRouter

from .gateway_context import *

router = APIRouter()

_COMPAT_ORIGINALS = {
    "datetime": datetime,
    "authenticate_telegram_user": authenticate_telegram_user,
    "build_personalized_daily_facts": build_personalized_daily_facts,
    "get_daily_vibe_llm": get_daily_vibe_llm,
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
@router.post("/api/support/tickets")
async def create_support_ticket(
    payload: SupportTicketRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Create a new support ticket and notify admins.
    """
    from ..models import SupportTicket
    from ..services.notification import send_bot_notification

    if not payload.consent_accepted:
        raise HTTPException(status_code=400, detail="consent_required")

    consent_snapshot = log_consent_event(
        db,
        user=user,
        flow=payload.consent_flow or "support_ticket",
        accepted=True,
        extra={"topic": payload.topic, "surface": "support"},
    )

    ticket = SupportTicket(
        user_id=user.id,
        topic=payload.topic,
        message=payload.message,
        status="open",
        consent_snapshot=consent_snapshot,
    )
    db.add(ticket)
    db.commit()

    # Notify Admins via Bot
    admin_ids = [int(i) for i in os.getenv("BOT_ADMIN_IDS", "").split(",") if i.strip()]
    for admin_id in admin_ids:
        msg = (
            f"🎫 <b>Новый тикет!</b>\n"
            f"От: {user.full_name} (@{user.username or '—'})\n"
            f"Тема: {payload.topic}\n\n"
            f"{payload.message}"
        )
        asyncio.create_task(send_bot_notification(admin_id, msg))

    return {"status": "ok", "ticket_id": str(ticket.id)}

@router.get("/health")
@router.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """
    # PURPOSE: Check service availability and DB connection.
    # INPUT: None.
    # OUTPUT: {"status": "ok", "db": "connected"}.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error("health.db_fail", error=str(e))
        return {"status": "error", "db": str(e)}


@router.post("/api/engine/natal", response_model=ChartResponse)
def create_natal_chart(payload: NatalRequest):
    """
    # PURPOSE: Return raw natal chart data.
    # INPUT: NatalRequest (name, birth_date, birth_location, house_system).
    # OUTPUT: ChartResponse with positions and houses.
    # CONTEXT: Primary data source for the LLM orchestrator.
    """

    engine = StelliumEngine()
    house_system = resolve_house_system(payload.house_system)
    chart = engine.create_natal_chart(
        payload.name, payload.birth_date, payload.birth_location, house_system
    )

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(
            chart, orb=payload.fixed_star_orb
        )

    return serialize_chart(chart, chart_type="natal", fixed_stars=stars)


@router.post("/api/engine/transit", response_model=ChartResponse)
def create_transit_chart(payload: TransitRequest):
    """
    # PURPOSE: Return raw transit chart data.
    # INPUT: TransitRequest (date, location, house_system).
    # OUTPUT: ChartResponse with positions and houses.
    # CONTEXT: Used for forecasts and current cycles.
    """

    engine = StelliumEngine()
    house_system = resolve_house_system(payload.house_system)
    chart = engine.create_transit_chart(payload.date, payload.location, house_system)

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(
            chart, orb=payload.fixed_star_orb
        )

    return serialize_chart(chart, chart_type="transit", fixed_stars=stars)

@router.get("/api/geo/autocomplete", response_model=List[GeoSuggestionOut])
def geo_autocomplete(q: str, limit: int = 8):
    """
    # PURPOSE: Return GeoNames suggestions for location autocomplete.
    # INPUT: q (query), limit.
    # OUTPUT: List[GeoSuggestionOut].
    # CONTEXT: Used by the admin UI location picker.
    """

    try:
        return search_geonames(q, limit=limit)
    except GeoNamesError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/geo/timezone", response_model=GeoTimezoneOut)
def geo_timezone(lat: float, lon: float):
    """
    # PURPOSE: Return GeoNames timezone for coordinates.
    # INPUT: lat, lon.
    # OUTPUT: GeoTimezoneOut.
    # CONTEXT: Used by the admin UI location picker.
    """

    try:
        return get_timezone(lat, lon)
    except GeoNamesError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/diagnostics/run")
def run_diagnostics_endpoint():
    """
    # PURPOSE: Run diagnostics and return the result.
    # INPUT: None.
    # OUTPUT: Dict with status and steps.
    # CONTEXT: Admin trigger for Log-Driven verification.
    """

    return run_diagnostics()


# #START_BLOCK_USER_ENDPOINTS

@router.get("/api/users/me", response_model=UserProfileOut)
def get_my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Get current user profile for Telegram WebApp.
    """
    if not user.referral_code:
        from ..services.code_gen import generate_referral_code
        user.referral_code = generate_referral_code()
        db.add(user)
        db.commit()
        db.refresh(user)

    now = _compat("datetime").now(timezone.utc)
    days_left = 0
    if user.subscription_active_until:
        sub_end = user.subscription_active_until
        if sub_end.tzinfo is None: sub_end = sub_end.replace(tzinfo=timezone.utc)
        delta = sub_end - now
        days_left = max(0, delta.days)

    from ..models import Referral, Transaction, Report
    from ..services.access_control import build_report_access_snapshot, check_user_access
    from ..core.feature_flags import get_feature_flag_snapshot
    from ..services.one_off_entitlements import build_report_unlock_snapshot
    
    referrals_count = db.query(Referral).filter(Referral.referrer_id == user.id).count()
    
    # Horary Stats
    horary_balance = int(
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user.id)
        .filter(Transaction.currency == "CRD")
        .scalar() or 0
    )
    
    from ..services.access_control import get_local_week_start_utc
    monday_utc = get_local_week_start_utc(user)
    
    quota_used = (
        db.query(func.count(Report.id))
        .filter(Report.user_id == user.id)
        .filter(Report.report_type.in_(["horary", "horary_answer", "horary_full"]))
        .filter(Report.created_at >= monday_utc)
        .scalar()
    ) or 0

    log_analytics_event(db, "app_open", user_id=user.id, telegram_id=user.telegram_id, source="webapp")

    return {
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "is_partner": user.is_partner,
        "is_test": user.is_test,
        "balance": float(user.balance),
        "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
        "days_left": days_left,
        "birth_time_known": user.birth_time_known,
        "birth_time": user.birth_time,
        "birth_date": user.birth_date,
        "birth_place": user.birth_place,
        "birth_timezone": user.birth_timezone,
        "current_location": user.current_location,
        "current_lat": user.current_lat,
        "current_lon": user.current_lon,
        "current_timezone": user.current_timezone,
        "sun_sign": user.sun_sign,
        "referral_code": user.referral_code,
        "referrals_count": referrals_count,
        "horary_balance": horary_balance,
        "weekly_quota_used": quota_used,
        "report_unlocks": build_report_unlock_snapshot(db, user_id=user.id),
        "report_access": build_report_access_snapshot(user, db),
        "feature_flags": get_feature_flag_snapshot(),
        "can_access_premium": check_user_access(user, "natal_master", db),
        "can_ask_horary": check_user_access(user, "horary", db),
        "consent_log": user.consent_log or {},
    }

@router.get("/api/billing/packs")
def list_payment_packs():
    """
    # PURPOSE: Provide list of available horary packs for frontend.
    """
    from ..core.config_business import HORARY_PACKS
    return HORARY_PACKS





@router.post("/api/reports/{report_id}/feedback", response_model=AnalyticsEventOut)
async def submit_report_feedback(
    report_id: uuid.UUID,
    payload: FeedbackIn,
    db: Session = Depends(get_db),
    x_telegram_auth: Optional[str] = Header(None, alias="X-Telegram-Auth"),
):
    """
    # PURPOSE: Submit user feedback for a report or section.
    # INPUT: report_id, rating, comment.
    # OUTPUT: ok status.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    user_id = None
    # If auth provided, use it
    if x_telegram_auth:
        try:
            from ..auth import verify_telegram_auth
            user_data = verify_telegram_auth(x_telegram_auth)
            tg_id = int(user_data["id"])
            user = db.query(User).filter(User.telegram_id == tg_id).first()
            if user:
                user_id = user.id
        except:
            pass
    
    # Fallback to telegram_id in payload if no auth
    if not user_id and payload.telegram_id:
        user = db.query(User).filter(User.telegram_id == payload.telegram_id).first()
        if user:
            user_id = user.id

    feedback = ReportFeedback(
        report_id=report_id,
        user_id=user_id,
        section_id=payload.section_id,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(feedback)
    db.commit()
    
    return {"ok": True}

@router.post("/api/analytics/event", response_model=AnalyticsEventOut)
def capture_analytics_event(
    payload: AnalyticsEventIn,
    db: Session = Depends(get_db),
    x_telegram_id: Optional[int] = Header(None, alias="X-Telegram-ID"),
):
    """
    # PURPOSE: Capture a funnel analytics event from webapp or services.
    # INPUT: event payload.
    # OUTPUT: ok flag + optional error.
    """
    event_name = payload.event_name.strip()
    if event_name not in ALLOWED_ANALYTICS_EVENTS:
        return {"ok": False, "error": "invalid_event"}

    telegram_id = payload.telegram_id or x_telegram_id
    user_id = None
    if telegram_id:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user_id = user.id

    ok = log_analytics_event(
        db,
        event_name,
        user_id=user_id,
        telegram_id=telegram_id,
        source=payload.source or "webapp",
        metadata=payload.metadata,
        session_id=payload.session_id,
        path=payload.path,
        product_type=payload.product_type,
        price=payload.price,
        currency=payload.currency,
        duration_ms=payload.duration_ms,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        device=payload.device,
        os_name=payload.os,
        browser=payload.browser
    )
    return {"ok": ok}

def get_sun_sign(birth_date_str: str) -> str:
    """Determine Sun sign from YYYY-MM-DD string."""
    try:
        dt = datetime.fromisoformat(birth_date_str)
        month, day = dt.month, dt.day
        if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "Aries"
        if (month == 4 and day >= 20) or (month == 5 and day <= 20): return "Taurus"
        if (month == 5 and day >= 21) or (month == 6 and day <= 20): return "Gemini"
        if (month == 6 and day >= 21) or (month == 7 and day <= 22): return "Cancer"
        if (month == 7 and day >= 23) or (month == 8 and day <= 22): return "Leo"
        if (month == 8 and day >= 23) or (month == 9 and day <= 22): return "Virgo"
        if (month == 9 and day >= 23) or (month == 10 and day <= 22): return "Libra"
        if (month == 10 and day >= 23) or (month == 11 and day <= 21): return "Scorpio"
        if (month == 11 and day >= 22) or (month == 12 and day <= 21): return "Sagittarius"
        if (month == 12 and day >= 22) or (month == 1 and day <= 19): return "Capricorn"
        if (month == 1 and day >= 20) or (month == 2 and day <= 18): return "Aquarius"
        return "Pisces"
    except:
        return "Unknown"

@router.put("/api/users/me")
def update_my_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import sys
    print(f"DEBUG: Entered update_my_profile with {payload}", file=sys.stderr)
    try:
        if payload.birth_time_known is False:
            raise HTTPException(status_code=400, detail="birth_time_required")
        was_complete = bool(user.full_name and user.birth_date and user.birth_place)
        # Update fields if provided
        if payload.full_name is not None: user.full_name = payload.full_name
        if payload.birth_date is not None: 
            user.birth_date = payload.birth_date
            user.sun_sign = get_sun_sign(payload.birth_date)
        if payload.birth_time is not None: user.birth_time = payload.birth_time
        if payload.birth_time_known is not None: user.birth_time_known = payload.birth_time_known
        if payload.birth_place is not None: user.birth_place = payload.birth_place
        if payload.birth_lat is not None: user.birth_lat = payload.birth_lat
        if payload.birth_lon is not None: user.birth_lon = payload.birth_lon
        if payload.birth_timezone is not None: user.birth_timezone = payload.birth_timezone
        if payload.current_location is not None: user.current_location = payload.current_location
        if payload.current_lat is not None: user.current_lat = payload.current_lat
        if payload.current_lon is not None: user.current_lon = payload.current_lon
        if payload.current_timezone is not None: user.current_timezone = payload.current_timezone
        if payload.is_test is not None: user.is_test = payload.is_test

        if payload.consent_accepted is True:
            log_consent_event(
                db,
                user=user,
                flow=payload.consent_flow or "profile_update",
                accepted=True,
                extra={"surface": "profile", "endpoint": "/api/users/me"},
            )

        db.add(user)
        db.commit()
        db.refresh(user)

        is_complete = bool(user.full_name and user.birth_date and user.birth_place)
        if is_complete and not was_complete:
            try:
                log_analytics_event(
                    db,
                    "profile_fill",
                    user_id=user.id,
                    telegram_id=user.telegram_id,
                    source="webapp",
                    metadata={"endpoint": "/api/users/me"},
                )
            except Exception as e:
                logger.error("analytics.fail", error=str(e))

        days_left = 0
        if user.subscription_active_until:
            if user.subscription_active_until.tzinfo:
                now = _compat("datetime").now(timezone.utc)
            else:
                now = datetime.utcnow()
            
            delta = user.subscription_active_until - now
            days_left = max(0, delta.days)

        return {
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "is_partner": user.is_partner,
            "is_test": user.is_test,
            "balance": float(user.balance),
            "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
            "days_left": days_left,
            "birth_time_known": user.birth_time_known,
            "birth_date": user.birth_date,
            "birth_place": user.birth_place,
            "referral_code": user.referral_code,
            "referrals_count": 0,
            "consent_log": user.consent_log or {},
        }
    except Exception as e:
        import sys
        print(f"ERROR in update_my_profile: {e}", file=sys.stderr)
        with open("/tmp/backend_error.log", "w") as f:
            f.write(str(e))
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

def _build_feed_payload(
    now: datetime,
    moon_sign: str,
    moon_phase: str,
    moon_emoji: str,
    general_vibe: str,
    aspects_count: int,
    traffic_lights: Optional[dict] = None,
    moon: Optional[dict] = None,
    fast_hits: Optional[list] = None,
    personalization_level: Optional[str] = None,
    meta: Optional[dict] = None,
    day_brief: Optional[dict] = None,
    trace_id: Optional[str] = None,
    generation_mode: Optional[str] = None,
    birth_time_used: Optional[bool] = None,
    confidence_bucket: Optional[str] = None,
    factor_count: Optional[int] = None,
) -> dict:
    return {
        "date": now.strftime("%d.%m.%Y"),
        "moon_sign": moon_sign,
        "moon_phase": moon_phase,
        "moon_emoji": moon_emoji,
        "aspects_count": aspects_count,
        "general_vibe": general_vibe,
        "traffic_lights": traffic_lights or {
            "health": "yellow",
            "money": "yellow",
            "love": "yellow",
        },
        "moon": moon or {"sign": moon_sign, "phase": moon_phase, "emoji": moon_emoji},
        "fast_hits": fast_hits or [],
        "personalization_level": personalization_level,
        "meta": meta,
        "day_brief": day_brief,
        "trace_id": trace_id,
        "generation_mode": generation_mode,
        "birth_time_used": birth_time_used,
        "confidence_bucket": confidence_bucket,
        "factor_count": factor_count,
    }

@router.get("/api/feed/today", response_model=FeedOut)
# START_BLOCK: API_TODAY_ROUTE
# START_CONTRACT: FN-GET-DAILY-FEED
async def get_daily_feed(
    request: Request,
    debug: bool = Query(False),
    x_telegram_auth: Optional[str] = Header(None, alias="X-Telegram-Auth"),
    x_feed_debug: Optional[str] = Header(None, alias="X-Feed-Debug"),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Get daily astrological feed (Moon, Vibe) with real LLM advice.
    # INPUT: Optional Telegram auth header for personalized context.
    # OUTPUT: FeedOut object.
    """
    now = _compat("datetime").now(timezone.utc)
    user = None
    auth_mode = "none"
    _log_api_gateway_event(
        "info",
        "feed.entry",
        fn="get_daily_feed",
        block="API_TODAY_ROUTE",
        stage="request_start",
        path=str(request.url.path),
        debug=bool(debug),
        has_auth_header=bool(x_telegram_auth),
    )
    if x_telegram_auth:
        try:
            user = _compat("authenticate_telegram_user")(x_telegram_auth, db)
            auth_mode = "telegram"
        except HTTPException as exc:
            auth_mode = "anonymous"
            _log_api_gateway_event(
                "info",
                "feed.debug",
                fn="get_daily_feed",
                block="API_TODAY_ROUTE",
                stage="auth_fallback",
                path=str(request.url.path),
                auth_mode=auth_mode,
                reason="telegram_auth_invalid",
            )

    debug_enabled = debug or str(x_feed_debug or "").lower() in {"1", "true", "yes", "on"}

    fallback_sign = "Луна"
    fallback_phase = "Текущий день"
    fallback_vibe = build_daily_vibe_fallback(fallback_sign, fallback_phase, "Нет мажорных аспектов")

    bypass_runtime_cache = bool(debug_enabled and x_telegram_auth)

    try:
        facts = _compat("build_personalized_daily_facts")(now, user=user, bypass_cache=bypass_runtime_cache)
        prompt_context = summarize_personalization_for_prompt(facts)
        _log_api_gateway_event(
            "info",
            "feed.debug",
            fn="get_daily_feed",
            block="API_TODAY_ROUTE",
            stage="llm_prompt_path",
            path=str(request.url.path),
            auth_mode=auth_mode,
            personalization_level=prompt_context.get("level"),
            cache_scope=prompt_context.get("cache_scope"),
            prompt_path=prompt_context.get("prompt_contract"),
        )
        vibe, vibe_meta = await _compat("get_daily_vibe_llm")(
            facts["moon_sign"],
            facts["moon_phase"],
            facts["aspect_summary"],
            personalization_context=prompt_context,
            cache_scope=prompt_context.get("cache_scope"),
            bypass_cache=bypass_runtime_cache,
            return_metadata=True,
        )
        day_brief = build_day_brief_payload(
            facts,
            user=user,
            general_vibe=vibe,
            generation_mode=vibe_meta.get("generation_mode"),
        )
        day_brief_telemetry = build_day_brief_telemetry(
            day_brief,
            generation_mode=vibe_meta.get("generation_mode"),
            trace_id=get_correlation_ids().get("trace_id"),
            request_id=get_correlation_ids().get("request_id"),
        )

        _log_api_gateway_event(
            "info",
            "feed.debug",
            fn="get_daily_feed",
            block="API_TODAY_ROUTE",
            stage="request_success",
            auth_mode=auth_mode,
            personalization_level=facts.get("personalization_level"),
            cache_scope=facts.get("cache_scope"),
            debug=debug_enabled,
            path=str(request.url.path),
        )
        _log_api_gateway_event(
            "info",
            "day_brief.response_returned",
            fn="get_daily_feed",
            block="API_TODAY_ROUTE",
            path=str(request.url.path),
            status=day_brief.get("status"),
            fallback_mode=bool(day_brief.get("fallback_mode", False)),
            personalization_level=facts.get("personalization_level"),
            cache_scope=facts.get("cache_scope"),
            generation_mode=day_brief_telemetry.get("generation_mode"),
            trace_id=day_brief_telemetry.get("trace_id"),
            request_id=day_brief_telemetry.get("request_id"),
            birth_time_used=day_brief_telemetry.get("birth_time_used"),
            confidence_bucket=day_brief_telemetry.get("confidence_bucket"),
            factor_count=day_brief_telemetry.get("factor_count"),
        )
        return _build_feed_payload(
            now,
            moon_sign=facts["moon_sign"],
            moon_phase=facts["moon_phase"],
            moon_emoji=facts["moon_emoji"],
            general_vibe=vibe,
            aspects_count=int(facts.get("aspects_count", 0) or 0),
            traffic_lights=facts.get("traffic_lights"),
            moon={
                "sign": facts.get("moon_sign"),
                "phase": facts.get("moon_phase"),
                "emoji": facts.get("moon_emoji"),
                "degree": facts.get("moon_degree"),
            },
            fast_hits=facts.get("fast_hits") or [],
            personalization_level=facts.get("personalization_level"),
            meta=(facts.get("meta") if debug_enabled and bool(x_telegram_auth) else None),
            trace_id=day_brief_telemetry.get("trace_id"),
            generation_mode=day_brief_telemetry.get("generation_mode"),
            birth_time_used=day_brief_telemetry.get("birth_time_used"),
            confidence_bucket=day_brief_telemetry.get("confidence_bucket"),
            factor_count=day_brief_telemetry.get("factor_count"),
            day_brief=(
                {
                    **day_brief,
                    "debug": day_brief.get("debug"),
                }
                if debug_enabled and isinstance(day_brief, dict) and day_brief.get("debug")
                else day_brief
            ),
        )
    except Exception as exc:
        _log_api_gateway_event(
            "error",
            "feed.error",
            fn="get_daily_feed",
            block="API_TODAY_ROUTE",
            stage="endpoint_error",
            error=str(exc),
            auth_mode=auth_mode,
            debug=debug_enabled,
            path=str(request.url.path),
            reason="endpoint_error",
        )
        return _build_feed_payload(
            now,
            moon_sign=fallback_sign,
            moon_phase=fallback_phase,
            moon_emoji="🌙",
            general_vibe=fallback_vibe,
            aspects_count=0,
            traffic_lights={
                "health": "yellow",
                "money": "yellow",
                "love": "yellow",
            },
            moon={"sign": fallback_sign, "phase": fallback_phase, "emoji": "🌙"},
            fast_hits=[],
            personalization_level="anonymous",
            meta=({"reason": "endpoint_error"} if debug_enabled and bool(x_telegram_auth) else None),
            day_brief=None,
            trace_id=get_correlation_ids().get("trace_id"),
            generation_mode="fallback",
            birth_time_used=None,
            confidence_bucket=None,
            factor_count=None,
        )
# END_CONTRACT: FN-GET-DAILY-FEED
# END_BLOCK: API_TODAY_ROUTE
# #END_BLOCK_FEED_ENDPOINT


@router.get("/api/week/map", response_model=WeekMapOut)
async def get_week_map_endpoint(
    x_telegram_auth: Optional[str] = Header(None, alias="X-Telegram-Auth"),
    db: Session = Depends(get_db),
):
    user = None
    if x_telegram_auth:
        user = _compat("authenticate_telegram_user")(x_telegram_auth, db)
    if not user:
        raise HTTPException(status_code=401, detail="WeekMap requires authenticated user")
    now = _compat("datetime").now(timezone.utc)
    return build_week_map(now, user)


@router.get("/api/day/brief", response_model=DayBriefDTO)
# START_BLOCK: API_DAY_BRIEF_ROUTE
# START_CONTRACT: FN-GET-DAY-BRIEF
async def get_day_brief(
    request: Request,
    debug: bool = Query(False),
    x_telegram_auth: Optional[str] = Header(None, alias="X-Telegram-Auth"),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Provide aggregated personalized day brief.
    # INPUT: Optional Telegram auth header for personalization.
    # OUTPUT: strict canonical DayBrief DTO.
    """
    now = _compat("datetime").now(timezone.utc)
    user = None
    auth_mode = "none"
    _log_api_gateway_event(
        "info",
        "day_brief.entry",
        fn="get_day_brief",
        block="API_DAY_BRIEF_ROUTE",
        stage="request_start",
        path=str(request.url.path),
        debug=bool(debug),
        has_auth_header=bool(x_telegram_auth),
    )
    if x_telegram_auth:
        try:
            user = _compat("authenticate_telegram_user")(x_telegram_auth, db)
            auth_mode = "telegram"
        except HTTPException as exc:
            auth_mode = "anonymous"
            _log_api_gateway_event(
                "info",
                "day_brief.debug",
                fn="get_day_brief",
                block="API_DAY_BRIEF_ROUTE",
                stage="auth_fallback",
                path=str(request.url.path),
                auth_mode=auth_mode,
                reason="telegram_auth_invalid",
                detail=exc.detail,
            )

    try:
        facts = build_personalized_daily_facts(now, user=user)
        payload = build_day_brief_payload(facts, user=user, generation_mode="deterministic")
        _log_api_gateway_event(
            "info",
            "day_brief.debug",
            fn="get_day_brief",
            block="API_DAY_BRIEF_ROUTE",
            stage="request_success",
            auth_mode=auth_mode,
            personalization_level=facts.get("personalization_level"),
            cache_scope=facts.get("cache_scope"),
            path=str(request.url.path),
        )
        telemetry = build_day_brief_telemetry(payload, generation_mode="deterministic")
        _log_api_gateway_event(
            "info",
            "day_brief.response_returned",
            fn="get_day_brief",
            block="API_DAY_BRIEF_ROUTE",
            path=str(request.url.path),
            status=payload.get("status"),
            fallback_mode=bool(payload.get("fallback_mode", False)),
            personalization_level=facts.get("personalization_level"),
            generation_mode=telemetry.get("generation_mode"),
            trace_id=telemetry.get("trace_id"),
            request_id=telemetry.get("request_id"),
            birth_time_used=telemetry.get("birth_time_used"),
            confidence_bucket=telemetry.get("confidence_bucket"),
            factor_count=telemetry.get("factor_count"),
        )
        return payload
    except Exception as exc:
        _log_api_gateway_event(
            "error",
            "day_brief.error",
            fn="get_day_brief",
            block="API_DAY_BRIEF_ROUTE",
            stage="fallback",
            error=str(exc),
            auth_mode=auth_mode,
            path=str(request.url.path),
        )
        raise HTTPException(status_code=503, detail="Day brief unavailable")

# END_BLOCK: ROUTER_EXTRACTION
