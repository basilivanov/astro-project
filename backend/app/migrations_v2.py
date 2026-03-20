# ############################################################################
# AI_HEADER: MODULE_DB_MIGRATIONS_V2
# ROLE: Add support models (SupportTicket) and referral codes.
# DEPENDENCIES: sqlalchemy
# GRACE_ANCHORS: [DB_MIGRATIONS_V2]
# ############################################################################

from sqlalchemy import text

# #START_BLOCK_DB_MIGRATIONS_V2
def apply_v2_migrations(connection):
    """
    # PURPOSE: Apply Schema V2 changes.
    # CHANGES:
    # 1. Add `referral_code` to `users`.
    # 2. Create `support_tickets` table.
    """
    
    statements = [
        # 1. Referral Code
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(10) UNIQUE",
        "CREATE INDEX IF NOT EXISTS users_referral_code_idx ON users(referral_code)",
        
        # 2. Support Tickets
        """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            topic VARCHAR(64) NOT NULL,
            status VARCHAR(32) DEFAULT 'open',
            message TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS support_tickets_user_id_idx ON support_tickets(user_id)"
    ]
    
    for stmt in statements:
        try:
            connection.execute(text(stmt))
        except Exception as e:
            print(f"Migration warning: {e}")

def apply_v3_migrations(connection):
    """
    # PURPOSE: Add user_id to reports for notification logic.
    """
    statements = [
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL",
        "CREATE INDEX IF NOT EXISTS reports_user_id_idx ON reports(user_id)"
    ]
    for stmt in statements:
        try:
            connection.execute(text(stmt))
        except Exception as e:
            print(f"Migration V3 warning: {e}")

def apply_v4_migrations(connection):
    """
    # PURPOSE: Extend analytics_events table.
    """
    statements = [
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS metadata TEXT",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS session_id VARCHAR(64)",
        "CREATE INDEX IF NOT EXISTS analytics_events_session_id_idx ON analytics_events(session_id)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS path VARCHAR(255)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS product_type VARCHAR(64)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS price FLOAT",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS currency VARCHAR(3)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS duration_ms INTEGER",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS utm_source VARCHAR(64)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS utm_medium VARCHAR(64)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(64)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS device VARCHAR(32)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS os VARCHAR(32)",
        "ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS browser VARCHAR(32)"
    ]
    for stmt in statements:
        try:
            connection.execute(text(stmt))
        except Exception as e:
            print(f"Migration V4 warning: {e}")

def apply_v5_migrations(connection):
    """
    # PURPOSE: Add user_id to clients for ownership tracking.
    """
    statements = [
        "ALTER TABLE clients ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL",
        "CREATE INDEX IF NOT EXISTS clients_user_id_idx ON clients(user_id)"
    ]
    for stmt in statements:
        try:
            connection.execute(text(stmt))
        except Exception as e:
            print(f"Migration V5 warning: {e}")


def apply_v6_migrations(connection):
    """
    # PURPOSE: Add one-off entitlement scaffolding tables and report linkage fields.
    # CONTEXT: Storage-only slice; current runtime remains on legacy access paths.
    """
    statements = [
        """
        CREATE TABLE IF NOT EXISTS billing_checkout_sessions (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            provider VARCHAR(32) NOT NULL DEFAULT 'yookassa',
            status VARCHAR(32) NOT NULL DEFAULT 'created',
            billing_kind VARCHAR(32) NOT NULL,
            product_code VARCHAR(64) NOT NULL,
            report_type VARCHAR(64),
            pack_id VARCHAR(64),
            amount NUMERIC(10, 2) NOT NULL,
            currency VARCHAR(3) NOT NULL DEFAULT 'RUB',
            provider_payment_id VARCHAR(255),
            provider_status VARCHAR(64),
            idempotence_key VARCHAR(64),
            resume_token VARCHAR(64) NOT NULL UNIQUE,
            return_path VARCHAR(255),
            draft_payload TEXT,
            resumed_report_id UUID REFERENCES reports(id) ON DELETE SET NULL,
            error_code VARCHAR(64),
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            succeeded_at TIMESTAMPTZ,
            resumed_at TIMESTAMPTZ,
            canceled_at TIMESTAMPTZ
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS report_entitlements (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            report_type VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            source VARCHAR(32) NOT NULL DEFAULT 'payment',
            checkout_session_id UUID REFERENCES billing_checkout_sessions(id) ON DELETE SET NULL,
            granted_transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
            consumed_report_id UUID REFERENCES reports(id) ON DELETE SET NULL,
            scope_key VARCHAR(128),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            consumed_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ
        )
        """,
        "ALTER TABLE billing_checkout_sessions ADD COLUMN IF NOT EXISTS entitlement_id UUID",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS access_source VARCHAR(32)",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS entitlement_id UUID REFERENCES report_entitlements(id) ON DELETE SET NULL",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS checkout_session_id UUID REFERENCES billing_checkout_sessions(id) ON DELETE SET NULL",
        "CREATE UNIQUE INDEX IF NOT EXISTS billing_checkout_sessions_provider_payment_id_uq ON billing_checkout_sessions(provider_payment_id) WHERE provider_payment_id IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS billing_checkout_sessions_user_status_created_idx ON billing_checkout_sessions(user_id, status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS billing_checkout_sessions_resume_token_idx ON billing_checkout_sessions(resume_token)",
        "CREATE INDEX IF NOT EXISTS billing_checkout_sessions_entitlement_id_idx ON billing_checkout_sessions(entitlement_id)",
        "CREATE INDEX IF NOT EXISTS billing_checkout_sessions_resumed_report_id_idx ON billing_checkout_sessions(resumed_report_id)",
        "CREATE INDEX IF NOT EXISTS report_entitlements_user_type_status_created_idx ON report_entitlements(user_id, report_type, status, created_at)",
        "CREATE UNIQUE INDEX IF NOT EXISTS report_entitlements_consumed_report_id_uq ON report_entitlements(consumed_report_id) WHERE consumed_report_id IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS report_entitlements_active_idx ON report_entitlements(user_id, report_type, created_at) WHERE status = 'active'",
        "CREATE INDEX IF NOT EXISTS report_entitlements_checkout_session_id_idx ON report_entitlements(checkout_session_id)",
        "CREATE INDEX IF NOT EXISTS report_entitlements_granted_transaction_id_idx ON report_entitlements(granted_transaction_id)",
        "CREATE INDEX IF NOT EXISTS reports_entitlement_id_idx ON reports(entitlement_id)",
        "CREATE INDEX IF NOT EXISTS reports_checkout_session_id_idx ON reports(checkout_session_id)",
    ]
    for stmt in statements:
        try:
            connection.execute(text(stmt))
        except Exception as e:
            print(f"Migration V6 warning: {e}")
            
# #END_BLOCK_DB_MIGRATIONS_V2
