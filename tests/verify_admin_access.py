from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.getcwd())
from backend.app.main import app
from backend.app.auth import get_current_user
from backend.app.models import User

def test_admin_access():
    with TestClient(app) as client:
        # Mock a regular user
        regular_user = User(telegram_id=555, full_name="Regular User")
        app.dependency_overrides[get_current_user] = lambda: regular_user

        # Try to access admin endpoint
        response = client.get("/api/admin/stats")
        print(f"Regular user access: {response.status_code} {response.text}")
        assert response.status_code == 403

        # Mock an admin user (must be in BOT_ADMIN_IDS)
        # Instead of relying on env, patch BOT_ADMIN_IDS for the test.
        import backend.app.auth
        original_ids = backend.app.auth.BOT_ADMIN_IDS
        backend.app.auth.BOT_ADMIN_IDS = [999]

        admin_user = User(telegram_id=999, full_name="Admin User")
        app.dependency_overrides[get_current_user] = lambda: admin_user

        response = client.get("/api/admin/stats")
        print(f"Admin user access: {response.status_code}")
        assert response.status_code == 200

        # Cleanup
        app.dependency_overrides = {}
        backend.app.auth.BOT_ADMIN_IDS = original_ids

if __name__ == "__main__":
    try:
        test_admin_access()
        print("Admin access test: OK")
    except Exception as e:
        print(f"Admin access test: FAILED: {e}")
        sys.exit(1)
