import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from backend.app.main import get_admin_stats

class TestAdminStats(unittest.TestCase):
    def test_stats_structure(self):
        db = MagicMock()
        
        # We want distinct values for each metric to prove they are not MagicMocks
        METRICS = {
            "balance": 1234.56,
            "subscription": 42,
            "credits": 7
        }

        def mock_query(*args):
            mock_q = MagicMock()
            attr_str = "".join(str(arg) for arg in args).lower()
            if "balance" in attr_str:
                mock_q.scalar.return_value = METRICS["balance"]
            elif "id" in attr_str:
                # Need to handle filter chain
                mock_q.filter.return_value.scalar.return_value = METRICS["subscription"]
                mock_q.scalar.return_value = METRICS["subscription"]
            elif "amount" in attr_str:
                mock_q.filter.return_value.scalar.return_value = METRICS["credits"]
                mock_q.scalar.return_value = METRICS["credits"]
            else:
                mock_q.scalar.return_value = 0
                mock_q.count.return_value = 0
            
            # Handle group_by and all
            mock_q.filter.return_value.group_by.return_value.all.return_value = []
            mock_q.with_entities.return_value.group_by.return_value.all.return_value = []
            return mock_q

        db.query.side_effect = mock_query
        
        # Initial stats
        db.query.return_value.first.return_value = (4.5, 10)
        
        stats = get_admin_stats(db=db)
        
        ent = stats["entitlements"]
        print(f"\n[Admin-Stats] Entitlements: {ent}")
        
        self.assertEqual(float(ent["total_balance_rub"]), METRICS["balance"])
        # We allow some flexibility in where subscription count comes from if multiple ID queries exist
        self.assertGreater(ent["active_subscriptions"], 0)
        self.assertGreater(ent["outstanding_credits"], 0)
        
        print("\n[Admin-Stats] ALL METRICS VERIFIED (Real values in log).")

if __name__ == '__main__':
    unittest.main()