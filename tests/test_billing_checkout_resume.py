import json
import os
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
TEST_BOT_TOKEN = "test_token_for_billing_checkout_resume"
os.environ["TELEGRAM_BOT_TOKEN"] = TEST_BOT_TOKEN
os.environ["ENVIRONMENT"] = "test"

from backend.app.main import app, get_db
from backend.app.models import Base, BillingCheckoutSession, Report, ReportEntitlement, User
from backend.app.services.one_off_entitlements import AccessGrantSource, BillingKind, EntitlementSource
from tests.utils import sign_init_data


def _build_auth_headers(telegram_id: int) -> dict[str, str]:
    init_data = sign_init_data(
        {
            "id": telegram_id,
            "first_name": "Resume",
            "last_name": "Tester",
            "username": f"resume_{telegram_id}",
        },
        TEST_BOT_TOKEN,
    )
    return {"X-Telegram-Auth": init_data}


class BillingCheckoutResumeTestCase(unittest.TestCase):
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
            patch("backend.app.services.billing.log_analytics_event"),
            patch("backend.app.services.referral_service.process_partner_reward"),
            patch("backend.app.main.run_report_generation", new=lambda *args, **kwargs: None),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for patcher in reversed(self.patchers):
            patcher.stop()
        app.dependency_overrides.clear()
        self.db_session.close()

    def _seed_profiled_user(self, telegram_id: int) -> User:
        user = User(
            telegram_id=telegram_id,
            username=f"resume_{telegram_id}",
            full_name="Resume Tester",
            birth_date="1990-01-01",
            birth_time="12:00",
            birth_time_known=True,
            birth_place="Moscow",
            birth_lat=55.75,
            birth_lon=37.61,
            birth_timezone="Europe/Moscow",
            current_timezone="Europe/Moscow",
            subscription_active_until=None,
        )
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def _create_checkout_session(
        self,
        *,
        user_id,
        report_type: str,
        billing_kind: str,
    ) -> BillingCheckoutSession:
        checkout_session = BillingCheckoutSession(
            user_id=user_id,
            provider="mock",
            status="succeeded",
            billing_kind=billing_kind,
            product_code=report_type if billing_kind == BillingKind.REPORT_UNLOCK.value else "subscription",
            report_type=report_type if billing_kind == BillingKind.REPORT_UNLOCK.value else "week_forecast",
            amount=199.0,
            currency="RUB",
            idempotence_key=uuid.uuid4().hex,
            resume_token=uuid.uuid4().hex,
            provider_payment_id=f"pay_{uuid.uuid4().hex[:8]}",
            draft_payload=json.dumps({"report_type": report_type}),
        )
        self.db_session.add(checkout_session)
        self.db_session.commit()
        self.db_session.refresh(checkout_session)
        return checkout_session

    def _grant_checkout_entitlement(
        self,
        *,
        user_id,
        report_type: str,
        checkout_session_id,
    ) -> ReportEntitlement:
        entitlement = ReportEntitlement(
            user_id=user_id,
            report_type=report_type,
            status="active",
            source=EntitlementSource.PAYMENT.value,
            checkout_session_id=checkout_session_id,
        )
        self.db_session.add(entitlement)
        self.db_session.commit()
        self.db_session.refresh(entitlement)

        checkout_session = self.db_session.get(BillingCheckoutSession, checkout_session_id)
        checkout_session.entitlement_id = entitlement.id
        self.db_session.add(checkout_session)
        self.db_session.commit()
        self.db_session.refresh(checkout_session)
        return entitlement

    def test_resume_checkout_session_creates_report_and_is_idempotent(self):
        user = self._seed_profiled_user(telegram_id=560001)
        headers = _build_auth_headers(user.telegram_id)
        checkout_session = self._create_checkout_session(
            user_id=user.id,
            report_type="month_forecast",
            billing_kind=BillingKind.REPORT_UNLOCK.value,
        )
        entitlement = self._grant_checkout_entitlement(
            user_id=user.id,
            report_type="month_forecast",
            checkout_session_id=checkout_session.id,
        )

        with patch.dict(
            os.environ,
            {
                "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
                "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
                "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
            },
            clear=False,
        ):
            first_response = self.client.post(
                f"/api/billing/sessions/{checkout_session.resume_token}/resume",
                headers=headers,
            )
            second_response = self.client.post(
                f"/api/billing/sessions/{checkout_session.resume_token}/resume",
                headers=headers,
            )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        first_payload = first_response.json()
        second_payload = second_response.json()
        self.assertEqual(first_payload["report_id"], second_payload["report_id"])
        self.assertEqual(first_payload["checkout_session"]["status"], "resumed")
        self.assertEqual(
            second_payload["checkout_session"]["resumed_report_id"],
            first_payload["report_id"],
        )

        self.db_session.expire_all()
        report = self.db_session.query(Report).filter(
            Report.id == uuid.UUID(first_payload["report_id"])
        ).one()
        refreshed_checkout = self.db_session.get(BillingCheckoutSession, checkout_session.id)
        refreshed_entitlement = self.db_session.get(ReportEntitlement, entitlement.id)

        self.assertEqual(self.db_session.query(Report).count(), 1)
        self.assertEqual(report.access_source, AccessGrantSource.REPORT_ENTITLEMENT.value)
        self.assertEqual(report.entitlement_id, refreshed_entitlement.id)
        self.assertEqual(report.checkout_session_id, refreshed_checkout.id)
        self.assertTrue(report.paid)
        self.assertEqual(refreshed_entitlement.status, "consumed")
        self.assertEqual(refreshed_entitlement.consumed_report_id, report.id)
        self.assertEqual(refreshed_checkout.status, "resumed")
        self.assertEqual(refreshed_checkout.resumed_report_id, report.id)

    def test_get_checkout_session_status_includes_draft_payload(self):
        user = self._seed_profiled_user(telegram_id=560010)
        headers = _build_auth_headers(user.telegram_id)
        checkout_session = self._create_checkout_session(
            user_id=user.id,
            report_type="solar_return",
            billing_kind=BillingKind.REPORT_UNLOCK.value,
        )
        checkout_session.draft_payload = json.dumps(
            {
                "report_type": "solar_return",
                "solar_current_location": "Tbilisi, Georgia",
            }
        )
        self.db_session.add(checkout_session)
        self.db_session.commit()

        response = self.client.get(
            f"/api/billing/sessions/{checkout_session.resume_token}",
            headers=headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["draft_payload"]["report_type"], "solar_return")
        self.assertEqual(
            response.json()["draft_payload"]["solar_current_location"],
            "Tbilisi, Georgia",
        )

    def test_get_checkout_session_status_includes_synastry_partner_draft_payload(self):
        user = self._seed_profiled_user(telegram_id=560011)
        headers = _build_auth_headers(user.telegram_id)
        checkout_session = self._create_checkout_session(
            user_id=user.id,
            report_type="synastry",
            billing_kind=BillingKind.REPORT_UNLOCK.value,
        )
        checkout_session.draft_payload = json.dumps(
            {
                "report_type": "synastry",
                "partner_name": "Partner",
                "partner_birth_date": "1992-02-02T06:30",
                "partner_birth_location": "London",
            }
        )
        self.db_session.add(checkout_session)
        self.db_session.commit()

        response = self.client.get(
            f"/api/billing/sessions/{checkout_session.resume_token}",
            headers=headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["draft_payload"]["report_type"], "synastry")
        self.assertEqual(response.json()["draft_payload"]["partner_name"], "Partner")
        self.assertEqual(
            response.json()["draft_payload"]["partner_birth_date"],
            "1992-02-02T06:30",
        )
        self.assertEqual(
            response.json()["draft_payload"]["partner_birth_location"],
            "London",
        )

    def test_resume_checkout_session_rejects_subscription_checkout(self):
        user = self._seed_profiled_user(telegram_id=560002)
        headers = _build_auth_headers(user.telegram_id)
        checkout_session = self._create_checkout_session(
            user_id=user.id,
            report_type="subscription",
            billing_kind=BillingKind.SUBSCRIPTION.value,
        )

        with patch.dict(
            os.environ,
            {
                "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
                "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
            },
            clear=False,
        ):
            response = self.client.post(
                f"/api/billing/sessions/{checkout_session.resume_token}/resume",
                headers=headers,
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["detail"],
            "Checkout session does not support resume",
        )
        self.assertEqual(self.db_session.query(Report).count(), 0)


if __name__ == "__main__":
    unittest.main()
