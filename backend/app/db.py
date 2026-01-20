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
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS birth_place_id VARCHAR(64)",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS input_payload TEXT",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS error_message TEXT",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS error_at TIMESTAMPTZ",
        "ALTER TABLE report_chunks ADD COLUMN IF NOT EXISTS error_message TEXT",
        "ALTER TABLE report_chunks ADD COLUMN IF NOT EXISTS error_at TIMESTAMPTZ",
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
            balance NUMERIC(10, 2) DEFAULT 0,
            subscription_active_until TIMESTAMPTZ,
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
            updated_at TIMESTAMPTZ
        )
        """,

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
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)
# #END_BLOCK_DB_MIGRATIONS
