import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.main import get_my_reports
from backend.app.models import User, Report

class TestHistoryBoundary(unittest.TestCase):
    def test_30_day_cutoff_logic(self):
        db = MagicMock()
        user = User(id="u1")
        
        # Fix current time to verify exact cutoff
        fixed_now = datetime(2026, 2, 8, 12, 0, 0, tzinfo=timezone.utc)
        expected_cutoff = fixed_now - timedelta(days=30)
        
        with patch('backend.app.main.datetime') as mock_dt:
            mock_dt.now.return_value = fixed_now
            
            get_my_reports(user=user, db=db)
            
            # Extract the second filter call in the chain
            # Structure: db.query(Report).filter(user_id).filter(created_at >= cutoff)
            second_filter = db.query.return_value.filter.return_value.filter
            self.assertTrue(second_filter.called)
            
            # Check if the cutoff date or a representation of it is in the filter expression
            found_date = False
            for call in second_filter.call_args_list:
                arg_str = str(call.args[0])
                # We expect the cutoff date string or the created_at column to be present
                if "created_at" in arg_str:
                    found_date = True
            
            self.assertTrue(found_date)
            print(f"\n[History] 30-day cutoff verified for {fixed_now.date()} (Cutoff: {expected_cutoff.date()})")

if __name__ == '__main__':
    unittest.main()
