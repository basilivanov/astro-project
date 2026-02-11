import unittest
from unittest.mock import MagicMock, patch
import uuid
import json
import sys
import os

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.routers.billing import initiate_payment, CreatePaymentRequest
from backend.app.core.config_business import REPORT_PRICES, SUBSCRIPTION_PRICE

class TestBillingPrices(unittest.TestCase):
    def setUp(self):
        self.user = MagicMock()
        self.user.id = uuid.uuid4()
        self._old_mode = os.environ.get("PAYMENTS_MODE")
        os.environ["PAYMENTS_MODE"] = "real"

    def tearDown(self):
        if self._old_mode is None:
            if "PAYMENTS_MODE" in os.environ:
                del os.environ["PAYMENTS_MODE"]
        else:
            os.environ["PAYMENTS_MODE"] = self._old_mode

    @patch("backend.app.routers.billing.create_payment")
    def test_resolve_report_price(self, mock_create_payment):
        mock_create_payment.return_value = json.dumps({"confirmation": {"confirmation_url": "http://ok"}})
        db = MagicMock()
        # Mock user returned by db query
        mock_user_db = MagicMock()
        mock_user_db.subscription_active_until = None
        db.query.return_value.filter.return_value.first.return_value = mock_user_db
        
        # Test year_forecast (499)
        payload = CreatePaymentRequest(product_type="year_forecast")
        initiate_payment(payload, self.user, db=db)
        
        args, kwargs = mock_create_payment.call_args
        self.assertEqual(kwargs["amount"], 499.0)
        self.assertEqual(kwargs["metadata"]["product_type"], "year_forecast")

    @patch("backend.app.routers.billing.create_payment")
    def test_resolve_subscription_price(self, mock_create_payment):
        mock_create_payment.return_value = json.dumps({"confirmation": {"confirmation_url": "http://ok"}})
        db = MagicMock()
        mock_user_db = MagicMock()
        mock_user_db.subscription_active_until = None
        db.query.return_value.filter.return_value.first.return_value = mock_user_db
        
        payload = CreatePaymentRequest(product_type="subscription")
        initiate_payment(payload, self.user, db=db)
        
        args, kwargs = mock_create_payment.call_args
        self.assertEqual(kwargs["amount"], SUBSCRIPTION_PRICE)
        self.assertTrue(kwargs["is_recurring"])

    @patch("backend.app.routers.billing.create_payment")
    def test_resolve_natal_price(self, mock_create_payment):
        mock_create_payment.return_value = json.dumps({"confirmation": {"confirmation_url": "http://ok"}})
        db = MagicMock()
        mock_user_db = MagicMock()
        mock_user_db.subscription_active_until = None
        db.query.return_value.filter.return_value.first.return_value = mock_user_db
        
        payload = CreatePaymentRequest(product_type="natal_master")
        initiate_payment(payload, self.user, db=db)
        
        args, kwargs = mock_create_payment.call_args
        self.assertEqual(kwargs["amount"], 199.0)

if __name__ == "__main__":
    unittest.main()
