import os
import sys
import unittest
from unittest.mock import patch

from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token_for_admin_grant_alignment"
os.environ["ENVIRONMENT"] = "test"
sys.path.append(os.getcwd())

from backend.app.main import AdminGrantRequest, admin_grant_item
from backend.app.models import AuditLog, Base, Client, Report, ReportEntitlement, User
from backend.app.services.one_off_entitlements import AccessGrantSource, EntitlementSource


class AdminGrantOneOffAlignmentTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db_session = session_local()

        self.admin = User(
            telegram_id=999001,
            username="admin_grant_alignment",
            full_name="Admin Alignment",
            is_partner=True,
        )
        self.target_user = User(
            telegram_id=999002,
            username="gifted_user",
            full_name="Gifted User",
            birth_date="1990-01-01",
            birth_time="12:00",
            birth_place="Moscow",
            birth_timezone="Europe/Moscow",
            birth_time_known=True,
        )
        self.db_session.add_all([self.admin, self.target_user])
        self.db_session.commit()
        self.db_session.refresh(self.admin)
        self.db_session.refresh(self.target_user)

        self.patchers = [
            patch("backend.app.main.build_section_specs", return_value=[]),
            patch("backend.app.main.initialize_report_chunks", return_value=None),
            patch("backend.app.main.run_report_generation", new=lambda *args, **kwargs: None),
            patch("backend.app.main.upsert_client_from_payload", side_effect=self._upsert_client),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.db_session.close()

    def _upsert_client(self, wf_payload, db, owner_user_id=None):
        client = Client(
            user_id=owner_user_id,
            full_name=wf_payload.client_name or "User",
            birth_location=wf_payload.birth_location,
            birth_lat=wf_payload.birth_lat,
            birth_lon=wf_payload.birth_lon,
            birth_timezone=wf_payload.birth_timezone,
        )
        db.add(client)
        db.flush()
        return client

    def test_admin_one_off_grant_creates_and_consumes_entitlement(self):
        response = admin_grant_item(
            str(self.target_user.id),
            AdminGrantRequest(type="report", report_type="natal_master", reason="QA gift"),
            admin=self.admin,
            db=self.db_session,
            background_tasks=BackgroundTasks(),
        )

        report = self.db_session.query(Report).one()
        entitlement = self.db_session.query(ReportEntitlement).one()
        audit = self.db_session.query(AuditLog).one()

        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["details"]["report_type"], "natal_master")
        self.assertEqual(response["details"]["report_id"], str(report.id))
        self.assertEqual(response["details"]["entitlement_id"], str(entitlement.id))
        self.assertEqual(response["details"]["grant_model"], "entitlement_first")
        self.assertEqual(response["details"]["access_source"], AccessGrantSource.REPORT_ENTITLEMENT.value)

        self.assertEqual(report.report_type, "natal_master")
        self.assertTrue(report.paid)
        self.assertEqual(report.access_source, AccessGrantSource.REPORT_ENTITLEMENT.value)
        self.assertEqual(report.entitlement_id, entitlement.id)

        self.assertEqual(entitlement.report_type, "natal_master")
        self.assertEqual(entitlement.source, EntitlementSource.ADMIN_GRANT.value)
        self.assertEqual(entitlement.status, "consumed")
        self.assertEqual(entitlement.consumed_report_id, report.id)
        self.assertIsNone(entitlement.checkout_session_id)

        self.assertEqual(audit.action, "grant_report")
        self.assertIn("entitlement_first", audit.details)

    def test_admin_one_off_grant_normalizes_alias_before_entitlement(self):
        response = admin_grant_item(
            str(self.target_user.id),
            AdminGrantRequest(type="report", report_type="synastry_master", reason="QA alias gift"),
            admin=self.admin,
            db=self.db_session,
            background_tasks=BackgroundTasks(),
        )

        report = self.db_session.query(Report).one()
        entitlement = self.db_session.query(ReportEntitlement).one()

        self.assertEqual(response["details"]["report_type"], "synastry")
        self.assertEqual(report.report_type, "synastry")
        self.assertEqual(report.access_source, AccessGrantSource.REPORT_ENTITLEMENT.value)
        self.assertEqual(entitlement.report_type, "synastry")
        self.assertEqual(entitlement.source, EntitlementSource.ADMIN_GRANT.value)
        self.assertEqual(entitlement.status, "consumed")
        self.assertEqual(entitlement.consumed_report_id, report.id)


if __name__ == "__main__":
    unittest.main()
