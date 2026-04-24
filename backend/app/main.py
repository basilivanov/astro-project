# ############################################################################
# AI_HEADER: MODULE_API
# ROLE: FastAPI entrypoint and compatibility facade for extracted API routers.
# DEPENDENCIES: fastapi, backend.app.routers
# GRACE_ANCHORS: [APP_INIT, ROUTER_REGISTRATION, COMPAT_EXPORTS]
# ############################################################################

# START_MODULE_CONTRACT: M-API-GATEWAY
# purpose: Create the FastAPI app, preserve request correlation/startup behavior, register extracted routers, and expose compatibility imports.
# owns:
#   - backend/app/main.py
# inputs:
#   - authenticated FastAPI requests routed through extracted API router modules
# outputs:
#   - stable FastAPI route table and compatibility symbols for existing tests/importers
# dependencies:
#   - backend.app.routers.* for endpoint ownership
#   - backend.app.logging_utils for correlation and GRACE structured logging
# invariants:
#   - public API paths, methods, response schemas, auth dependencies, and access-control semantics remain unchanged
#   - billing router remains registered without local service rewrites
# non_goals:
#   - redesigning route behavior, billing semantics, report workflow internals, or frontend contracts
# END_MODULE_CONTRACT: M-API-GATEWAY

# START_MODULE_MAP: M-API-GATEWAY
# public_entrypoints:
#   - app -> FastAPI application instance
#   - bind_request_correlation -> request/trace header propagation middleware
#   - init_db -> startup database/scheduler bootstrap
#   - compatibility exports -> extracted route/helper symbols imported below
# semantic_blocks:
#   - API_GATEWAY_LOGGING: gateway-level GRACE event helper and module identity
#   - API_GATEWAY_APP_INIT: app creation, correlation middleware, startup lifecycle
#   - API_GATEWAY_ROUTER_REGISTRATION: extracted router registration preserving route table
#   - API_GATEWAY_COMPAT_EXPORTS: main.py import/monkeypatch compatibility facade
# owned_tests:
#   - tests/test_admin_api.py
#   - tests/test_daily_feed_robustness.py
#   - tests/test_access_control_integration.py
#   - tests/test_catalog_logging.py
#   - tests/test_backend_grace_wave_finish.py
# adjacent_modules:
#   - backend/app/routers/*.py
#   - backend/app/api_schemas.py
#   - backend/app/api_helpers.py
# END_MODULE_MAP: M-API-GATEWAY

from fastapi import FastAPI, Request
import structlog

from .db import Base, apply_runtime_migrations, engine, get_db
from .logging_utils import configure_structlog, correlation_scope, get_correlation_ids, log_grace_event
from .services.scheduler import start_scheduler
from .routers import (
    admin_clients,
    admin_reports,
    admin_users,
    b2c_reports,
    billing,
    public,
    reports,
)

# START_BLOCK: API_GATEWAY_LOGGING
logger = structlog.get_logger()
API_GATEWAY_MODULE_ID = "M-API-GATEWAY"


# START_CONTRACT: FN-LOG-API-GATEWAY-EVENT
def _log_api_gateway_event(level: str, event: str, *, fn: str, block: str, **fields) -> None:
    log_grace_event(level, event, module=API_GATEWAY_MODULE_ID, fn=fn, block=block, **fields)
# END_CONTRACT: FN-LOG-API-GATEWAY-EVENT
# END_BLOCK: API_GATEWAY_LOGGING


# START_BLOCK: API_GATEWAY_APP_INIT
configure_structlog()
app = FastAPI(title="AstroSaaS API", version="0.1.0")


@app.middleware("http")
# START_CONTRACT: FN-BIND-REQUEST-CORRELATION
async def bind_request_correlation(request: Request, call_next):
    incoming_request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
    incoming_trace_id = request.headers.get("X-Trace-ID") or request.headers.get("traceparent")
    with correlation_scope(
        "fastapi.middleware",
        correlation_id=incoming_request_id,
        trace_id=incoming_trace_id,
        request_id=incoming_request_id,
    ) as context:
        request.state.correlation_context = context
        response = await call_next(request)
        current = get_correlation_ids()
        if current.get("request_id"):
            response.headers.setdefault("X-Request-ID", str(current["request_id"]))
        if current.get("trace_id"):
            response.headers.setdefault("X-Trace-ID", str(current["trace_id"]))
        return response
# END_CONTRACT: FN-BIND-REQUEST-CORRELATION


@app.on_event("startup")
# START_CONTRACT: FN-INIT-API-GATEWAY
async def init_db():
    _log_api_gateway_event("info", "api_gateway.startup", fn="init_db", block="API_GATEWAY_APP_INIT", stage="db_setup_start")
    Base.metadata.create_all(bind=engine)
    apply_runtime_migrations()
    await start_scheduler()
    _log_api_gateway_event("info", "api_gateway.startup", fn="init_db", block="API_GATEWAY_APP_INIT", stage="scheduler_started")
# END_CONTRACT: FN-INIT-API-GATEWAY
# END_BLOCK: API_GATEWAY_APP_INIT

# START_BLOCK: API_GATEWAY_ROUTER_REGISTRATION
app.include_router(billing.router)
app.include_router(admin_users.router)
app.include_router(admin_clients.router)
app.include_router(admin_reports.router)
app.include_router(public.router)
app.include_router(reports.router)
app.include_router(b2c_reports.router)
# END_BLOCK: API_GATEWAY_ROUTER_REGISTRATION

# START_BLOCK: API_GATEWAY_COMPAT_EXPORTS
# START_CONTRACT: API-GATEWAY-SCHEMA-COMPAT-IMPORTS
from .api_schemas import *  # noqa: F401,F403
# END_CONTRACT: API-GATEWAY-SCHEMA-COMPAT-IMPORTS

# START_CONTRACT: API-GATEWAY-HELPER-COMPAT-IMPORTS
from .api_helpers import *  # noqa: F401,F403
from .routers.gateway_context import *  # noqa: F401,F403
from .routers.gateway_runtime import run_report_generation, run_report_section_generation
from .routers.admin_clients import create_admin_client, get_admin_client, list_admin_clients, update_admin_client
from .routers.admin_reports import (
    admin_broadcast,
    get_admin_report,
    get_admin_report_section,
    list_admin_reports,
    list_admin_tickets,
    regenerate_report_copy,
    run_mass_broadcast,
)
from .routers.admin_users import (
    admin_add_balance,
    admin_add_subscription_days,
    admin_grant_item,
    get_admin_stats,
    get_admin_tasks,
    get_admin_user_detail,
    list_admin_audit_logs,
    list_admin_feedback,
    list_admin_users,
    update_admin_task,
)
from .routers.b2c_reports import create_b2c_report
from .routers.public import (
    capture_analytics_event,
    create_natal_chart,
    create_support_ticket,
    create_transit_chart,
    geo_autocomplete,
    geo_timezone,
    get_daily_feed,
    get_day_brief,
    get_my_profile,
    get_week_map_endpoint,
    health_check,
    list_payment_packs,
    run_diagnostics_endpoint,
    submit_report_feedback,
    update_my_profile,
)
from .routers.reports import (
    create_report,
    create_report_async,
    get_my_reports,
    get_report_detail,
    regenerate_report,
    regenerate_report_async,
    regenerate_report_section,
    regenerate_report_section_async,
    user_regenerate_report,
)
# END_CONTRACT: API-GATEWAY-HELPER-COMPAT-IMPORTS
# END_BLOCK: API_GATEWAY_COMPAT_EXPORTS
