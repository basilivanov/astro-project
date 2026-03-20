# ############################################################################
# AI_HEADER: TEST_ONE_OFF_ENTITLEMENTS_SCAFFOLD
# ROLE: Verify additive scaffold for one-off entitlement rollout.
# ############################################################################

import os
import sys
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, inspect

sys.path.append(os.getcwd())

from backend.app.core.feature_flags import (
    allow_legacy_premium_subscription_access,
    is_one_off_entitlements_runtime_enabled,
    use_persistent_checkout_sessions,
)
from backend.app.models import Base
from backend.app.services.one_off_entitlements import (
    AccessGrantSource,
    BillingKind,
    PRODUCT_CATALOG,
    ONE_OFF_REPORT_TYPES,
    allow_access,
    build_zero_report_unlocks,
    deny_access,
    is_one_off_report_type,
    normalize_product_code,
    normalize_report_type,
    resolve_catalog_product,
)


class TestOneOffEntitlementsScaffold(unittest.TestCase):
    def test_metadata_create_all_includes_one_off_tables(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        self.assertIn("report_entitlements", tables)
        self.assertIn("billing_checkout_sessions", tables)

        report_columns = {column["name"] for column in inspector.get_columns("reports")}
        self.assertIn("access_source", report_columns)
        self.assertIn("entitlement_id", report_columns)
        self.assertIn("checkout_session_id", report_columns)

    def test_product_catalog_matches_slice_matrix(self):
        subscription = PRODUCT_CATALOG["subscription"]
        self.assertEqual(subscription.billing_kind, BillingKind.SUBSCRIPTION)
        self.assertTrue(subscription.is_recurring)
        self.assertEqual(subscription.report_type, "week_forecast")

        for report_type in ONE_OFF_REPORT_TYPES:
            product = PRODUCT_CATALOG[report_type]
            self.assertEqual(product.billing_kind, BillingKind.REPORT_UNLOCK)
            self.assertEqual(product.report_type, report_type)

        zero_unlocks = build_zero_report_unlocks()
        self.assertEqual(set(zero_unlocks.keys()), set(ONE_OFF_REPORT_TYPES))
        self.assertTrue(all(value == 0 for value in zero_unlocks.values()))

    def test_aliases_normalize_to_canonical_one_off_types(self):
        self.assertEqual(normalize_report_type("synastry_master"), "synastry")
        self.assertEqual(normalize_report_type("solar_return_master"), "solar_return")
        self.assertEqual(normalize_product_code("synastry_master"), "synastry")
        self.assertTrue(is_one_off_report_type("solar_return_master"))
        self.assertEqual(resolve_catalog_product("synastry_master").report_type, "synastry")

    def test_access_decision_helpers_keep_structured_contract(self):
        allowed = allow_access(
            report_type="month_forecast",
            granted_via=AccessGrantSource.REPORT_ENTITLEMENT,
            entitlement_id="ent-1",
            remaining_unlocks=1,
        )
        denied = deny_access(report_type="month_forecast")

        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.to_dict()["granted_via"], AccessGrantSource.REPORT_ENTITLEMENT)
        self.assertEqual(allowed.reason_code, "ok")
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.reason_code, "payment_required")

    def test_feature_flags_default_to_safe_rollout_values(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_one_off_entitlements_runtime_enabled())
            self.assertFalse(use_persistent_checkout_sessions())
            self.assertTrue(allow_legacy_premium_subscription_access())


if __name__ == "__main__":
    unittest.main()
