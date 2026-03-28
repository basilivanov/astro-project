# ############################################################################
# AI_HEADER: MODULE_DB
# ROLE: Database engine and session configuration.
# DEPENDENCIES: sqlalchemy.
# GRACE_ANCHORS: [DB_SETTINGS, DB_ENGINE, DB_SESSION, DB_BASE, DB_MIGRATIONS]
# ############################################################################

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .base import Base
from .migrations_v2 import (
    apply_v2_migrations,
    apply_v3_migrations,
    apply_v4_migrations,
    apply_v5_migrations,
    apply_v6_migrations,
    apply_v7_migrations,
)

# #START_BLOCK_DB_SETTINGS
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://astro:astro@db:5432/astro",
)
# #END_BLOCK_DB_SETTINGS

# #START_BLOCK_DB_ENGINE
engine = create_engine(DATABASE_URL, future=True)
# #END_BLOCK_DB_ENGINE

# #START_BLOCK_DB_SESSION
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# #END_BLOCK_DB_SESSION


# #START_BLOCK_DB_MIGRATIONS
def apply_runtime_migrations():
    """
    # PURPOSE: Apply additive schema changes for new columns and tables.
    # INPUT: None.
    # OUTPUT: None.
    # CONTEXT: MVP helper to avoid manual migrations.
    """

    statements = [
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS notes TEXT",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS birth_lat DOUBLE PRECISION",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS birth_lon DOUBLE PRECISION",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS birth_timezone VARCHAR(64)",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS birth_time_known BOOLEAN DEFAULT TRUE",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS birth_place_id VARCHAR(64)",
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS is_test BOOLEAN DEFAULT FALSE",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS input_payload TEXT",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS error_message TEXT",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS error_at TIMESTAMPTZ",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS is_test BOOLEAN DEFAULT FALSE",
        "ALTER TABLE report_chunks ADD COLUMN IF NOT EXISTS error_message TEXT",
        "ALTER TABLE report_chunks ADD COLUMN IF NOT EXISTS error_at TIMESTAMPTZ",
        "ALTER TABLE report_runs ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER DEFAULT 0",
        "ALTER TABLE report_runs ADD COLUMN IF NOT EXISTS completion_tokens INTEGER DEFAULT 0",
        "ALTER TABLE report_runs ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0",
        "ALTER TABLE report_runs ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC(10, 4) DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_test BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(10)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC(10, 2) DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_partner BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_timezone VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_location VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_lat DOUBLE PRECISION",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_lon DOUBLE PRECISION",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_timezone VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS sun_sign VARCHAR(32)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_horary_reset_at TIMESTAMPTZ",
        """
        CREATE TABLE IF NOT EXISTS report_runs (
            id UUID PRIMARY KEY,
            report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            error_message TEXT,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS report_runs_report_id_idx ON report_runs(report_id)",
        
        # --- B2C Telegram Pivot Tables ---
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            username VARCHAR(255),
            full_name VARCHAR(255),
            birth_date VARCHAR(32),
            birth_time VARCHAR(32),
            birth_time_known BOOLEAN DEFAULT TRUE,
            birth_place VARCHAR(255),
            birth_lat DOUBLE PRECISION,
            birth_lon DOUBLE PRECISION,
            is_partner BOOLEAN DEFAULT FALSE,
            is_test BOOLEAN DEFAULT FALSE,
            balance NUMERIC(10, 2) DEFAULT 0,
            subscription_active_until TIMESTAMPTZ,
            referral_code VARCHAR(10),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS users_telegram_id_idx ON users(telegram_id)",

        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id UUID PRIMARY KEY,
            user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            status VARCHAR(32) DEFAULT 'inactive',
            payment_method_id VARCHAR(255),
            next_billing_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """,
        "ALTER TABLE subscriptions ALTER COLUMN updated_at SET DEFAULT NOW()",

        """
        CREATE TABLE IF NOT EXISTS transactions (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            amount NUMERIC(10, 2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'RUB',
            type VARCHAR(32) NOT NULL,
            status VARCHAR(32) DEFAULT 'success',
            provider_id VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS referrals (
            id UUID PRIMARY KEY,
            referrer_id UUID REFERENCES users(id) ON DELETE SET NULL,
            referee_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            status VARCHAR(32) DEFAULT 'pending',
            reward_type VARCHAR(32) DEFAULT 'days',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            report_id UUID REFERENCES reports(id) ON DELETE SET NULL,
            telegram_id BIGINT NOT NULL,
            source VARCHAR(16) DEFAULT 'voice',
            status VARCHAR(32) DEFAULT 'pending_confirmation',
            transcript TEXT,
            summary TEXT,
            clarification TEXT,
            voice_file_id VARCHAR(255),
            result_summary TEXT,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            approved_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS agent_tasks_telegram_id_idx ON agent_tasks(telegram_id)",
        "CREATE INDEX IF NOT EXISTS agent_tasks_status_idx ON agent_tasks(status)",
        "CREATE INDEX IF NOT EXISTS agent_tasks_created_at_idx ON agent_tasks(created_at)",
        """
        CREATE TABLE IF NOT EXISTS analytics_events (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            telegram_id BIGINT,
            event_name VARCHAR(64) NOT NULL,
            source VARCHAR(32),
            metadata TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS analytics_events_user_id_idx ON analytics_events(user_id)",
        "CREATE INDEX IF NOT EXISTS analytics_events_telegram_id_idx ON analytics_events(telegram_id)",
        "CREATE INDEX IF NOT EXISTS analytics_events_event_name_idx ON analytics_events(event_name)",
        "CREATE INDEX IF NOT EXISTS analytics_events_created_at_idx ON analytics_events(created_at)",
    ]
    with engine.begin() as connection:
        for statement in statements:
            try:
                connection.exec_driver_sql(statement)
            except Exception as e:
                print(f"Migration warning: {e}")
        apply_v2_migrations(connection)
        apply_v3_migrations(connection)
        apply_v4_migrations(connection)
        apply_v5_migrations(connection)
        apply_v6_migrations(connection)
        apply_v7_migrations(connection)
# #END_BLOCK_DB_MIGRATIONS
