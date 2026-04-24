import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import sys

from fastapi import BackgroundTasks
from structlog.testing import capture_logs

mock_stellium = SimpleNamespace(
    ChartBuilder=object,
    ReturnBuilder=object,
    ChartLocation=object,
    FIXED_STARS_REGISTRY={},
    get_fixed_star_info=lambda *args, **kwargs: None,
)
mock_stellium_modules = {
    "stellium": mock_stellium,
    "stellium.core": SimpleNamespace(config=SimpleNamespace(CalculationConfig=object)),
    "stellium.core.config": SimpleNamespace(CalculationConfig=object),
    "stellium.engines": SimpleNamespace(
        houses=SimpleNamespace(WholeSignHouses=object, PlacidusHouses=object, EqualHouses=object),
        aspects=SimpleNamespace(calculate_ascendant=lambda *args, **kwargs: 0),
        aspect_rules=SimpleNamespace(),
    ),
    "stellium.engines.houses": SimpleNamespace(WholeSignHouses=object, PlacidusHouses=object, EqualHouses=object),
    "stellium.engines.aspects": SimpleNamespace(calculate_ascendant=lambda *args, **kwargs: 0),
    "stellium.engines.aspect_rules": SimpleNamespace(),
}
sys.modules.update({name: module for name, module in mock_stellium_modules.items() if name not in sys.modules})


class _Mapped:
    def __class_getitem__(cls, item):
        return cls


def _sa_type(*args, **kwargs):
    return {"args": args, "kwargs": kwargs}


class _FuncNamespace:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def _declarative_base():
    return _ModelFactory("Base", (), {})


class _ColumnStub:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return ("eq", self.name, other)

    def __ge__(self, other):
        return ("ge", self.name, other)

    def __lt__(self, other):
        return ("lt", self.name, other)

    def desc(self):
        return ("desc", self.name)


class _ModelFactory(type):
    def __getattr__(cls, name):
        return _ColumnStub(name)

    def __call__(cls, *args, **kwargs):
        instance = super().__call__()
        for key, value in kwargs.items():
            setattr(instance, key, value)
        return instance

with patch.dict(os.environ, {"DATABASE_URL": "sqlite://", "SQLALCHEMY_WARN_20": "1"}, clear=False):
    orm_module = sys.modules.setdefault(
        "sqlalchemy.orm",
        SimpleNamespace(
            Mapped=_Mapped,
            mapped_column=lambda *args, **kwargs: _ColumnStub("mapped_column"),
            relationship=lambda *args, **kwargs: None,
            Session=SimpleNamespace,
            declarative_base=_declarative_base,
            sessionmaker=lambda *args, **kwargs: (lambda *factory_args, **factory_kwargs: None),
        ),
    )
    sqlalchemy_module = sys.modules.setdefault(
        "sqlalchemy",
        SimpleNamespace(
            orm=orm_module,
            create_engine=lambda *args, **kwargs: SimpleNamespace(),
            func=_FuncNamespace(),
            or_=lambda *args, **kwargs: None,
            select=lambda *args, **kwargs: None,
            extract=lambda *args, **kwargs: None,
            text=lambda *args, **kwargs: None,
            BigInteger=_sa_type,
            Boolean=_sa_type,
            DateTime=_sa_type,
            Float=_sa_type,
            ForeignKey=lambda *args, **kwargs: None,
            Integer=_sa_type,
            String=_sa_type,
            Text=_sa_type,
            Numeric=_sa_type,
            JSON=dict,
        ),
    )
    sys.modules.setdefault(
        "sqlalchemy.dialects",
        SimpleNamespace(postgresql=SimpleNamespace(UUID=uuid.UUID)),
    )
    sys.modules.setdefault(
        "sqlalchemy.dialects.postgresql",
        SimpleNamespace(UUID=lambda *args, **kwargs: uuid.uuid4),
    )
    from backend.app.main import (
        B2CReportCreateRequest,
        create_b2c_report,
        get_my_reports,
        get_report_detail,
    )
from backend.app.services.one_off_entitlements import AccessGrantSource, allow_access


def _build_user(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "telegram_id": 123,
        "full_name": "Test User",
        "birth_date": "1990-01-01",
        "birth_time": "08:00",
        "birth_place": "Moscow",
        "birth_lat": 55.7558,
        "birth_lon": 37.6173,
        "birth_timezone": "Europe/Moscow",
        "birth_time_known": True,
        "current_location": "Moscow",
        "current_lat": 55.7558,
        "current_lon": 37.6173,
        "current_timezone": "Europe/Moscow",
        "is_test": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _adapt_query_chain(db, reports):
    query = MagicMock()
    db.query.return_value = query
    first_filter = MagicMock()
    second_filter = MagicMock()
    order_query = MagicMock()
    offset_query = MagicMock()
    limit_query = MagicMock()

    query.filter.return_value = first_filter
    first_filter.filter.return_value = second_filter
    second_filter.order_by.return_value = order_query
    order_query.offset.return_value = offset_query
    offset_query.limit.return_value = limit_query
    limit_query.all.return_value = reports


def _build_report(user_id):
    client = SimpleNamespace(full_name="Client")
    report = SimpleNamespace(
        id=uuid.uuid4(),
        report_type="week_forecast",
        status="completed",
        created_at=datetime.now(timezone.utc),
        client=client,
        access_source="subscription",
        user_id=user_id,
        chunks=[
            SimpleNamespace(section="intro", content="Hello", status="done", order_index=1),
            SimpleNamespace(section="body", content="World", status="done", order_index=2),
        ],
    )
    return report


def test_get_my_reports_emits_catalog_events():
    user = _build_user()
    db = MagicMock()
    report = _build_report(user.id)
    _adapt_query_chain(db, [report])

    with capture_logs() as cap:
        result = get_my_reports(limit=10, offset=0, user=user, db=db)

    assert len(result) == 1
    start = next(entry for entry in cap if entry["event"] == "catalog.history_start")
    success = next(entry for entry in cap if entry["event"] == "catalog.history_success")

    assert start["surface"] == "history"
    assert start["user_id"] == str(user.id)
    assert success["count"] == 1
    assert success["has_more"] is False


@patch("backend.app.routers.reports.build_natal_chart_svg", return_value="<svg />")
@patch("backend.app.routers.reports.build_chart_data")
@patch("backend.app.routers.reports.load_report_payload")
def test_get_report_detail_logs_events(mock_payload, mock_chart, mock_svg):
    user = _build_user()
    db = MagicMock()
    report = _build_report(user.id)
    db.query.return_value.filter.return_value.first.return_value = report
    mock_payload.return_value = {}
    mock_chart.return_value = {}

    with capture_logs() as cap:
        response = get_report_detail(str(report.id), user=user, db=db)

    assert response["report"]["id"] == str(report.id)
    start = next(entry for entry in cap if entry["event"] == "catalog.history_start")
    success = next(entry for entry in cap if entry["event"] == "catalog.history_success")

    assert start["surface"] == "report_detail"
    assert start["report_id"] == str(report.id)
    assert success["chunk_count"] == 2
    assert success["report_id"] == str(report.id)


@patch("backend.app.routers.b2c_reports.log_analytics_event")
@patch("backend.app.routers.b2c_reports.initialize_report_chunks")
@patch("backend.app.routers.b2c_reports.build_section_specs")
@patch("backend.app.routers.b2c_reports.consume_report_access")
@patch("backend.app.routers.b2c_reports.upsert_client_from_payload")
@patch("backend.app.services.access_control.resolve_report_access")
def test_create_b2c_report_logs_checkout_events(
    mock_resolve_access,
    mock_upsert_client,
    mock_consume_access,
    mock_build_specs,
    mock_init_chunks,
    mock_log_analytics,
):
    user = _build_user()
    db = MagicMock()
    db.commit = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.rollback = MagicMock()

    access_decision = allow_access("natal_master", AccessGrantSource.SUBSCRIPTION)
    mock_resolve_access.return_value = access_decision
    mock_upsert_client.return_value = SimpleNamespace(id=uuid.uuid4())

    payload = B2CReportCreateRequest(report_type="natal_master")
    background_tasks = BackgroundTasks()

    with capture_logs() as cap:
        create_b2c_report(payload, background_tasks, user=user, db=db)

    events = {entry["event"] for entry in cap}
    assert "catalog.checkout_start" in events
    assert "catalog.checkout_decision" in events
    assert "catalog.checkout_success" in events

    success_event = next(entry for entry in cap if entry["event"] == "catalog.checkout_success")
    assert success_event["decision_allowed"] is True
    assert success_event["user_id"] == str(user.id)


def test_trace_logging_scope_does_not_modify_catalog_payload_fields():
    from backend.app.logging_utils import catalog_event_fields

    payload = catalog_event_fields(
        surface="history",
        correlation_id="corr-explicit",
        trace_id="trace-explicit",
        correlation_source="header",
    )

    assert payload == {
        "surface": "history",
        "correlation_id": "corr-explicit",
        "trace_id": "trace-explicit",
        "correlation_source": "header",
    }


def test_log_analytics_event_emits_success_hub_landmark():
    from backend.app.services.analytics import log_analytics_event

    db = MagicMock()
    user_id = uuid.uuid4()

    with capture_logs() as cap:
        ok = log_analytics_event(
            db,
            "app_open",
            user_id=user_id,
            telegram_id=123,
            source="webapp",
            path="/",
            metadata={"surface": "home"},
        )

    assert ok is True
    event = next(entry for entry in cap if entry["event"] == "analytics.event_persisted")
    assert event["module"] == "M-ANALYTICS-EVENTS"
    assert event["fn"] == "log_analytics_event"
    assert event["block"] == "ANALYTICS_EVENT_PERSISTENCE"
    assert event["event_name"] == "app_open"
    assert event["user_id"] == str(user_id)
    assert event["has_metadata"] is True
