import unittest
from unittest.mock import MagicMock
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())

from backend.app.main import list_admin_users

class TestAdminUsers(unittest.TestCase):
    def test_list_users_credits(self):
        db = MagicMock()
        
        # Mock User
        user = MagicMock()
        user.id = "u1"
        user.telegram_id = 123
        user.full_name = "Test User"
        user.balance = 100.0
        user.subscription_active_until = datetime.now()
        user.created_at = datetime.now()
        user.is_partner = False
        user.referral_code = "REF"
        
        # Mock query(User)
        # Without q, chain is: query().order_by().limit().all()
        db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [user]
        
        # Mock credits query: db.query(sum).filter().scalar()
        # list_admin_users calls: db.query(func.sum).filter(...).scalar()
        db.query.return_value.filter.return_value.scalar.return_value = 5 # 5 credits
        
        users = list_admin_users(limit=10, db=db)
        
        self.assertEqual(len(users), 1)
        u = users[0]
        self.assertEqual(u["horary_credits"], 5)
        print(f"\n[P0-ADM-01] User: {u['full_name']}, Credits: {u['horary_credits']}")

if __name__ == '__main__':
    unittest.main()

