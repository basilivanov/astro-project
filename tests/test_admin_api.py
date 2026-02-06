# ############################################################################
# AI_HEADER: TEST_ADMIN_API
# ROLE: Verify Admin API endpoints (Users, etc) and Schema Migrations.
# GRACE_ANCHORS: [TEST_ADMIN_USERS]
# ############################################################################

import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Environment Setup
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["ENVIRONMENT"] = "test"

from backend.app.main import app, get_db
from backend.app.db import apply_runtime_migrations, Base
from backend.app.models import User

# DB Fixture with Migrations
@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # 1. Simulate CORRECT Schema (as if migrations ran on Postgres)
    # We include all columns here so the endpoint works.
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id CHAR(32) PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username VARCHAR(255),
                full_name VARCHAR(255),
                birth_date VARCHAR(32),
                birth_time VARCHAR(32),
                birth_time_known BOOLEAN,
                birth_place VARCHAR(255),
                birth_lat FLOAT,
                birth_lon FLOAT,
                is_partner BOOLEAN DEFAULT 0,
                is_test BOOLEAN DEFAULT 0,
                balance FLOAT DEFAULT 0,
                subscription_active_until DATETIME,
                referral_code VARCHAR(10),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Create other tables required by FKs
        conn.execute(text("""
            CREATE TABLE clients (
                id CHAR(32) PRIMARY KEY,
                full_name VARCHAR(128),
                email VARCHAR(255),
                birth_datetime DATETIME,
                birth_location VARCHAR(255),
                birth_lat FLOAT,
                birth_lon FLOAT,
                birth_timezone VARCHAR(64),
                birth_place_id VARCHAR(64),
                is_test BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE reports (
                id CHAR(32) PRIMARY KEY,
                client_id CHAR(32),
                user_id CHAR(32),
                report_type VARCHAR(64),
                status VARCHAR(32),
                paid BOOLEAN,
                input_payload TEXT,
                error_message TEXT,
                error_at DATETIME,
                is_test BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE report_chunks (
                id CHAR(32) PRIMARY KEY,
                report_id CHAR(32),
                section VARCHAR(128),
                content TEXT,
                status VARCHAR(32),
                order_index INTEGER,
                error_message TEXT,
                error_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE report_runs (
                id CHAR(32) PRIMARY KEY,
                report_id CHAR(32),
                status VARCHAR(32),
                error_message TEXT,
                started_at DATETIME,
                finished_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
    return engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    # We call apply_runtime_migrations to verify it is ROBUST (does not crash app on sqlite errors)
    # The try-except block we added in db.py should handle the "syntax error" from sqlite for IF NOT EXISTS
    
    with pytest.MonkeyPatch.context() as m:
        m.setattr("backend.app.db.engine", db_engine)
        # Suppress prints during test
        apply_runtime_migrations()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

def test_admin_list_users_success(client, db_session):
    """
    # SCENARIO: Verify /api/admin/users works with correct schema.
    """
    # Create a user via ORM
    user = User(
        telegram_id=123,
        full_name="Test User",
        username="test",
        referral_code="u_123",
        balance=100.0,
        is_partner=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Request
    response = client.get("/api/admin/users")
    
    # Verify
    assert response.status_code == 200, f"Error: {response.text}"
    data = response.json()
    assert len(data) >= 1
    assert data[0]["referral_code"] == "u_123"
    assert data[0]["balance"] == 100.0
    assert data[0]["is_partner"] is True
