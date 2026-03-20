import unittest
from unittest.mock import MagicMock
import sys
import os
import uuid
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.append(os.getcwd())

from backend.app.main import admin_add_subscription_days, admin_add_balance, admin_grant_item, list_admin_audit_logs, regenerate_report_copy, get_admin_report, AdminUserUpdateDays, AdminUserUpdateBalance, AdminGrantRequest
from backend.app.models import User, AuditLog, Report, Client, ReportRun

class TestAdminOps(unittest.TestCase):
    # ... logic ...
    def test_get_report_usage(self):
        # Mock report with a run
        report_id = uuid.uuid4()
        run = ReportRun(
            id=uuid.uuid4(),
            report_id=report_id,
            status="completed",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost=Decimal("0.0015"),
            created_at=datetime.now()
        )
        report = Report(
            id=report_id,
            report_type="natal_master",
            status="completed",
            runs=[run],
            chunks=[]
        )
        self.db.query.return_value.filter.return_value.first.return_value = report
        
        res = get_admin_report(str(report_id), include_content=False, db=self.db, admin=self.admin)
        
        self.assertEqual(len(res["runs"]), 1)
        run_data = res["runs"][0]
        self.assertEqual(run_data["prompt_tokens"], 100)
        self.assertEqual(run_data["completion_tokens"], 50)
        self.assertEqual(run_data["total_tokens"], 150)
        self.assertEqual(run_data["estimated_cost"], 0.0015)
        print(f"\n[P0-LLM-USAGE-LOG-01] Admin Report Usage verified.")

    # ... setup ...
    def setUp(self):
        self.db = MagicMock()
        self.admin = User(id=uuid.uuid4(), telegram_id=999, full_name="Admin")
        self.target_user = User(
            id=uuid.uuid4(), 
            telegram_id=100, 
            full_name="User", 
            balance=Decimal(0), 
            subscription_active_until=None,
            birth_date="2000-01-01",
            birth_place="Moscow"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = self.target_user

    def test_regenerate_copy(self):
        # Mock existing report
        old_report = Report(
            id=uuid.uuid4(), 
            user_id=self.target_user.id, 
            report_type="natal_master",
            input_payload='{"client_name": "Test"}'
        )
        self.db.query.return_value.filter.return_value.first.return_value = old_report
        
        # Patch build_section_specs and initialize_report_chunks inside main or mock them
        # Since they are imported, we can patch where they are used.
        # But for MVP test, we can just run it and expect Audit Log.
        # run_report_generation is a background task, we can mock it.
        
        with unittest.mock.patch("backend.app.main.run_report_generation") as mock_run:
             with unittest.mock.patch("backend.app.main.build_section_specs") as mock_specs:
                 with unittest.mock.patch("backend.app.main.initialize_report_chunks") as mock_init:
                     res = regenerate_report_copy(
                         str(old_report.id),
                         admin=self.admin,
                         db=self.db
                     )
                     
                     self.assertIn("new_report_id", res)
                     # Check Audit
                     audit_logs = [call[0][0] for call in self.db.add.call_args_list if isinstance(call[0][0], AuditLog)]
                     self.assertTrue(any(l.action == "regenerate_copy" for l in audit_logs))
                     print(f"\n[P0-ADM-04] Regenerate Copy verified.")

    def test_audit_logs(self):
        # Mock logs
        log1 = AuditLog(
            id=uuid.uuid4(), 
            action="test_action", 
            reason="test", 
            created_at=datetime.now(), 
            admin=self.admin, 
            target_user=self.target_user
        )
        
        # Chain for list_admin_audit_logs: query(AuditLog).order_by().filter().limit().all()
        # If no filters: query(AuditLog).order_by().limit().all()
        self.db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [log1]
        
        res = list_admin_audit_logs(limit=10, db=self.db)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["action"], "test_action")
        self.assertEqual(res[0]["admin_name"], "Admin")
        
        print(f"\n[P0-ADM-05] Audit Log List verified.")

    def test_grant_credits(self):
        payload = AdminGrantRequest(type="credits", amount=5, reason="Gift")
        res = admin_grant_item(
            str(self.target_user.id),
            payload,
            admin=self.admin,
            db=self.db
        )
        self.assertEqual(res["details"]["amount"], 5)
        # Check Audit Log
        audit_logs = [call[0][0] for call in self.db.add.call_args_list if isinstance(call[0][0], AuditLog)]
        self.assertTrue(any(l.action == "grant_credits" for l in audit_logs))
        print(f"\n[P0-ADM-03] Grant Credits. Audit Log found.")

    def test_grant_report(self):
        payload = AdminGrantRequest(type="report", report_type="natal_master", reason="Gift")
        # Ensure upsert client returns a client
        self.db.query.return_value.filter.return_value.first.side_effect = [self.target_user, None] # User found, Client not found (create new)

        fake_entitlement_id = uuid.uuid4()

        def _consume_report_access(_user, report, _db, *, decision=None):
            report.paid = True
            report.access_source = "report_entitlement"
            report.entitlement_id = fake_entitlement_id

        with unittest.mock.patch("backend.app.main.upsert_client_from_payload") as mock_upsert:
            mock_upsert.return_value = Client(id=uuid.uuid4())
            with unittest.mock.patch("backend.app.main.grant_report_entitlement") as mock_grant:
                mock_grant.return_value = MagicMock(id=fake_entitlement_id)
                with unittest.mock.patch("backend.app.main.consume_report_access", side_effect=_consume_report_access) as mock_consume:
                    with unittest.mock.patch("backend.app.main.build_section_specs", return_value=[]):
                        with unittest.mock.patch("backend.app.main.initialize_report_chunks"):
                            res = admin_grant_item(
                                str(self.target_user.id),
                                payload,
                                admin=self.admin,
                                db=self.db
                            )
            self.assertEqual(res["details"]["report_type"], "natal_master")
            self.assertEqual(res["details"]["entitlement_id"], str(fake_entitlement_id))
            self.assertEqual(res["details"]["grant_model"], "entitlement_first")
            reports = [call[0][0] for call in self.db.add.call_args_list if isinstance(call[0][0], Report)]
            self.assertTrue(len(reports) > 0)
            self.assertTrue(reports[0].paid)
            self.assertEqual(reports[0].access_source, "report_entitlement")
            self.assertEqual(reports[0].entitlement_id, fake_entitlement_id)
            mock_grant.assert_called_once()
            mock_consume.assert_called_once()
            print(f"\n[P0-ADM-03] Grant Report. Entitlement-first report created.")

    def test_grant_report_normalizes_alias(self):
        payload = AdminGrantRequest(type="report", report_type="synastry_master", reason="Gift")
        self.db.query.return_value.filter.return_value.first.side_effect = [self.target_user, None]

        fake_entitlement_id = uuid.uuid4()

        def _consume_report_access(_user, report, _db, *, decision=None):
            report.paid = True
            report.access_source = "report_entitlement"
            report.entitlement_id = fake_entitlement_id

        with unittest.mock.patch("backend.app.main.upsert_client_from_payload") as mock_upsert:
            mock_upsert.return_value = Client(id=uuid.uuid4())
            with unittest.mock.patch("backend.app.main.grant_report_entitlement") as mock_grant:
                mock_grant.return_value = MagicMock(id=fake_entitlement_id)
                with unittest.mock.patch("backend.app.main.consume_report_access", side_effect=_consume_report_access):
                    with unittest.mock.patch("backend.app.main.build_section_specs", return_value=[]):
                        with unittest.mock.patch("backend.app.main.initialize_report_chunks"):
                            res = admin_grant_item(
                                str(self.target_user.id),
                                payload,
                                admin=self.admin,
                                db=self.db
                            )

            self.assertEqual(res["details"]["report_type"], "synastry")
            self.assertEqual(res["details"]["entitlement_id"], str(fake_entitlement_id))
            mock_grant.assert_called_once()
            self.assertEqual(mock_grant.call_args.kwargs["report_type"], "synastry")
            reports = [call[0][0] for call in self.db.add.call_args_list if isinstance(call[0][0], Report)]
            self.assertTrue(len(reports) > 0)
            self.assertEqual(reports[0].report_type, "synastry")

    def test_add_subscription_days(self):
        payload = AdminUserUpdateDays(days=7, reason="Bonus")
        
        admin_add_subscription_days(
            str(self.target_user.id),
            payload,
            admin=self.admin,
            db=self.db
        )
        
        # Verify Date Update
        self.assertIsNotNone(self.target_user.subscription_active_until)
        # Check Audit Log
        self.db.add.assert_called()
        # Find AuditLog arg
        # We assume db.add called once for AuditLog (commit called separately)
        # Actually commit is called. 
        # Inspect call_args_list for db.add
        audit_logs = [call[0][0] for call in self.db.add.call_args_list if isinstance(call[0][0], AuditLog)]
        self.assertEqual(len(audit_logs), 1)
        log = audit_logs[0]
        self.assertEqual(log.action, "add_subscription_days")
        self.assertEqual(log.reason, "Bonus")
        self.assertEqual(log.admin_id, self.admin.id)
        
        print(f"\n[P0-ADM-02] Added days. Audit Log: {log.action} reason={log.reason}")

    def test_add_balance(self):
        payload = AdminUserUpdateBalance(amount=500.0, reason="Refund")
        
        admin_add_balance(
            str(self.target_user.id),
            payload,
            admin=self.admin,
            db=self.db
        )
        
        self.assertEqual(self.target_user.balance, Decimal(500.0))
        
        audit_logs = [call[0][0] for call in self.db.add.call_args_list if isinstance(call[0][0], AuditLog)]
        # This list might contain logs from previous test if setUp/mock isn't reset?
        # setUp recreates db mock, so it's fresh.
        self.assertEqual(len(audit_logs), 1)
        log = audit_logs[0]
        self.assertEqual(log.action, "add_balance")
        self.assertEqual(log.reason, "Refund")
        self.assertIn("500", log.details)
        
        print(f"\n[P0-ADM-02] Added balance. Audit Log: {log.action} reason={log.reason}")

if __name__ == '__main__':
    unittest.main()
