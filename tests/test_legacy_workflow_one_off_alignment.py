import os
import sys
import uuid
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
TEST_BOT_TOKEN = "test_token_for_legacy_workflow_alignment"
os.environ["TELEGRAM_BOT_TOKEN"] = TEST_BOT_TOKEN
os.environ["ENVIRONMENT"] = "test"
sys.path.append(os.getcwd())

from backend.app.main import app, get_db
from backend.app.models import Base, Report, ReportEntitlement, User
from backend.app.services.one_off_entitlements import AccessGrantSource, EntitlementSource
from tests.utils import sign_init_data


def _build_auth_headers(telegram_id: int) -> dict[str, str]:
    init_data = sign_init_data(
        {
            "id": telegram_id,
            "first_name": "Legacy",
            "last_name": "Workflow",
            "username": f"legacy_{telegram_id}",
        },
        TEST_BOT_TOKEN,
    )
    return {"X-Telegram-Auth": init_data}


def _build_payload(report_type: str = "month_forecast") -> dict[str, object]:
    return {
        "client_name": "Legacy Workflow",
        "birth_date": "1990-01-01T12:00:00",
        "birth_location": "Moscow",
        "birth_timezone": "Europe/Moscow",
        "report_type": report_type,
    }


def _build_chart_response() -> dict[str, object]:
    return {
        "chart_type": "natal",
        "name": "Legacy Workflow",
        "datetime_utc": "1990-01-01T09:00:00+00:00",
        "datetime_local": "1990-01-01T12:00:00+03:00",
        "location": {
            "name": "Moscow",
            "latitude": 55.75,
            "longitude": 37.61,
            "timezone": "Europe/Moscow",
        },
        "house_system": "placidus",
        "houses": [],
        "positions": [],
        "fixed_stars": [],
        "dispositor_summary": None,
    }


class LegacyWorkflowOneOffAlignmentTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db_session = session_local()

        def override_get_db():
            try:
                yield self.db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        self.patchers = [
            patch("backend.app.main.start_scheduler", new=AsyncMock(return_value=None)),
            patch("backend.app.main.log_analytics_event"),
            patch("backend.app.main.run_report_generation", new=lambda *args, **kwargs: None),
        ]
        for patcher in self.patchers:
            patcher.start()

        self.client_cm = TestClient(app)
        self.client = self.client_cm.__enter__()

    def tearDown(self):
        self.client_cm.__exit__(None, None, None)
        app.dependency_overrides.clear()
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.db_session.close()

    def _seed_user(
        self,
        *,
        telegram_id: int,
        subscription_active_until: datetime | None = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=f"legacy_{telegram_id}",
            full_name="Legacy Workflow",
            birth_time_known=True,
            subscription_active_until=subscription_active_until,
        )
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def test_legacy_async_workflow_consumes_one_off_entitlement(self):
        user = self._seed_user(telegram_id=660001)
        headers = _build_auth_headers(user.telegram_id)

        entitlement = ReportEntitlement(
            user_id=user.id,
            report_type="month_forecast",
            status="active",
            source=EntitlementSource.PAYMENT.value,
        )
        self.db_session.add(entitlement)
        self.db_session.commit()
        self.db_session.refresh(entitlement)

        with patch.dict(
            os.environ,
            {
                "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
                "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
            },
            clear=False,
        ):
            response = self.client.post(
                "/api/workflows/report/async",
                headers=headers,
                json=_build_payload(),
            )

        self.assertEqual(response.status_code, 200)

        self.db_session.expire_all()
        report = self.db_session.get(Report, uuid.UUID(response.json()["report_id"]))
        entitlement = self.db_session.get(ReportEntitlement, entitlement.id)

        self.assertIsNotNone(report)
        self.assertEqual(report.access_source, AccessGrantSource.REPORT_ENTITLEMENT.value)
        self.assertEqual(report.entitlement_id, entitlement.id)
        self.assertTrue(report.paid)
        self.assertEqual(entitlement.status, "consumed")
        self.assertEqual(entitlement.consumed_report_id, report.id)

    def test_legacy_sync_workflow_consumes_one_off_entitlement(self):
        user = self._seed_user(telegram_id=660002)
        headers = _build_auth_headers(user.telegram_id)

        entitlement = ReportEntitlement(
            user_id=user.id,
            report_type="month_forecast",
            status="active",
            source=EntitlementSource.PAYMENT.value,
        )
        self.db_session.add(entitlement)
        self.db_session.commit()
        self.db_session.refresh(entitlement)

        with patch.dict(
            os.environ,
            {
                "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
                "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
            },
            clear=False,
        ), patch(
            "backend.app.main.generate_report_sections",
            new=AsyncMock(
                return_value=(
                    [{"section_id": "summary", "title": "Summary", "content": "ok"}],
                    _build_chart_response(),
                )
            ),
        ):
            response = self.client.post(
                "/api/workflows/report",
                headers=headers,
                json=_build_payload(),
            )

        self.assertEqual(response.status_code, 200)

        self.db_session.expire_all()
        report = self.db_session.get(Report, uuid.UUID(response.json()["report_id"]))
        entitlement = self.db_session.get(ReportEntitlement, entitlement.id)

        self.assertIsNotNone(report)
        self.assertEqual(report.access_source, AccessGrantSource.REPORT_ENTITLEMENT.value)
        self.assertEqual(report.entitlement_id, entitlement.id)
        self.assertTrue(report.paid)
        self.assertEqual(entitlement.status, "consumed")
        self.assertEqual(entitlement.consumed_report_id, report.id)

    def test_legacy_async_workflow_keeps_subscription_behavior_when_runtime_disabled(self):
        user = self._seed_user(
            telegram_id=660003,
            subscription_active_until=datetime.now(timezone.utc) + timedelta(days=7),
        )
        headers = _build_auth_headers(user.telegram_id)

        with patch.dict(
            os.environ,
            {
                "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "false",
                "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
            },
            clear=False,
        ):
            response = self.client.post(
                "/api/workflows/report/async",
                headers=headers,
                json=_build_payload(),
            )

        self.assertEqual(response.status_code, 200)

        self.db_session.expire_all()
        report = self.db_session.get(Report, uuid.UUID(response.json()["report_id"]))

        self.assertIsNotNone(report)
        self.assertIsNone(report.access_source)
        self.assertIsNone(report.entitlement_id)
        self.assertFalse(report.paid)


if __name__ == "__main__":
    unittest.main()
