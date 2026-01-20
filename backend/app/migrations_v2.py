# ############################################################################
# AI_HEADER: MODULE_DB_MIGRATIONS_V2
# ROLE: Add support models (SupportTicket) and referral codes.
# DEPENDENCIES: sqlalchemy
# GRACE_ANCHORS: [DB_MIGRATIONS_V2]
# ############################################################################

from sqlalchemy import text

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
            
# #END_BLOCK_DB_MIGRATIONS_V2
