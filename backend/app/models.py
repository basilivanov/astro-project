# ############################################################################
# AI_HEADER: MODULE_MODELS
# ROLE: SQLAlchemy ORM models for core entities.
# DEPENDENCIES: sqlalchemy, backend/app/db.py
# GRACE_ANCHORS: [CLIENT_MODEL, REPORT_MODEL, REPORT_CHUNK_MODEL, REPORT_RUN_MODEL, USER_MODEL, SUBSCRIPTION_MODEL, REFERRAL_MODEL, TRANSACTION_MODEL, ANALYTICS_EVENT_MODEL, FEEDBACK_MODEL]
# ############################################################################

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# #START_BLOCK_USER_MODEL
class User(Base):
    """
    # PURPOSE: Main user entity for Telegram-based B2C flow.
    # INPUT: telegram_id, profile data.
    # OUTPUT: ORM user record.
    # CONTEXT: Links to Subscription, Referrals, Transactions.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Astrology Profile
    birth_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True) # YYYY-MM-DD
    birth_time: Mapped[Optional[str]] = mapped_column(String(32), nullable=True) # HH:MM
    birth_time_known: Mapped[bool] = mapped_column(Boolean, default=True)
    birth_place: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birth_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birth_timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    current_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sun_sign: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    # Commercial
    is_partner: Mapped[bool] = mapped_column(Boolean, default=False)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    subscription_active_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    referral_code: Mapped[Optional[str]] = mapped_column(String(10), unique=True, index=True, nullable=True)
    last_horary_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    referrals_made: Mapped[list["Referral"]] = relationship(
        "Referral", foreign_keys="Referral.referrer_id", back_populates="referrer"
    )
    referral_origin: Mapped[Optional["Referral"]] = relationship(
        "Referral", foreign_keys="Referral.referee_id", back_populates="referee", uselist=False
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="user"
    )
    report_entitlements: Mapped[list["ReportEntitlement"]] = relationship(
        "ReportEntitlement", back_populates="user", cascade="all, delete-orphan"
    )
    billing_checkout_sessions: Mapped[list["BillingCheckoutSession"]] = relationship(
        "BillingCheckoutSession", back_populates="user", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["SupportTicket"]] = relationship(
        "SupportTicket", back_populates="user", cascade="all, delete-orphan"
    )
    feedbacks: Mapped[list["ReportFeedback"]] = relationship(
        "ReportFeedback", back_populates="user"
    )
# #END_BLOCK_USER_MODEL

# #START_BLOCK_FEEDBACK_MODEL
class ReportFeedback(Base):
    """
    # PURPOSE: Track user quality ratings for reports.
    """
    __tablename__ = "report_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False) # 1-5 or 1-10
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="feedbacks")
    report: Mapped["Report"] = relationship("Report")
# #END_BLOCK_FEEDBACK_MODEL

# #START_BLOCK_SUPPORT_MODEL
class SupportTicket(Base):
    """
    # PURPOSE: Track user support requests/partner applications.
    """
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="tickets")
# #END_BLOCK_SUPPORT_MODEL

# #START_BLOCK_SUBSCRIPTION_MODEL
class Subscription(Base):
    """
    # PURPOSE: Track recurring subscription status.
    # INPUT: user_id, status, payment_token.
    """
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[str] = mapped_column(String(32), default="inactive") # active, past_due, canceled
    payment_method_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Yookassa token
    next_billing_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="subscription")
# #END_BLOCK_SUBSCRIPTION_MODEL

# #START_BLOCK_REFERRAL_MODEL
class Referral(Base):
    """
    # PURPOSE: Track invitations (who invited whom).
    # INPUT: referrer_id, referee_id.
    """
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    referee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending") # pending, rewarded
    reward_type: Mapped[str] = mapped_column(String(32), default="days") # days, money
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    referrer: Mapped["User"] = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referee: Mapped["User"] = relationship("User", foreign_keys=[referee_id], back_populates="referral_origin")
# #END_BLOCK_REFERRAL_MODEL

# #START_BLOCK_TRANSACTION_MODEL
class Transaction(Base):
    """
    # PURPOSE: Financial log (payments, payouts, bonuses).
    """
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    type: Mapped[str] = mapped_column(String(32), nullable=False) # payment, referral_payout, refund
    status: Mapped[str] = mapped_column(String(32), default="success")
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Payment gateway ID
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="transactions")
# #END_BLOCK_TRANSACTION_MODEL

# #START_BLOCK_REPORT_ENTITLEMENT_MODEL
class ReportEntitlement(Base):
    """
    # PURPOSE: Persistent one-off unlock state for report creation.
    # CONTEXT: Additive scaffold for the future one-off entitlement runtime.
    """
    __tablename__ = "report_entitlements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="payment", nullable=False)
    checkout_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "billing_checkout_sessions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_report_entitlements_checkout_session_id",
        ),
        nullable=True,
        index=True,
    )
    granted_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    consumed_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "reports.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_report_entitlements_consumed_report_id",
        ),
        nullable=True,
        unique=True,
        index=True,
    )
    scope_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    consumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="report_entitlements")
    granted_transaction: Mapped[Optional["Transaction"]] = relationship("Transaction")
    consumed_report: Mapped[Optional["Report"]] = relationship(
        "Report", foreign_keys=[consumed_report_id]
    )
# #END_BLOCK_REPORT_ENTITLEMENT_MODEL

# #START_BLOCK_BILLING_CHECKOUT_SESSION_MODEL
class BillingCheckoutSession(Base):
    """
    # PURPOSE: Persistent checkout state for redirect/resume flows.
    # CONTEXT: Additive scaffold for future webhook and resume idempotency.
    """
    __tablename__ = "billing_checkout_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="yookassa", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    billing_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    report_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pack_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    provider_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    idempotence_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resume_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    return_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    draft_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entitlement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "report_entitlements.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_billing_checkout_sessions_entitlement_id",
        ),
        nullable=True,
        index=True,
    )
    resumed_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "reports.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_billing_checkout_sessions_resumed_report_id",
        ),
        nullable=True,
        index=True,
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    succeeded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="billing_checkout_sessions")
    resumed_report: Mapped[Optional["Report"]] = relationship(
        "Report", foreign_keys=[resumed_report_id]
    )
# #END_BLOCK_BILLING_CHECKOUT_SESSION_MODEL

# #START_BLOCK_AGENT_TASK_MODEL
class AgentTask(Base):
    """
    # PURPOSE: Store operator tasks created via bot messages.
    """
    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, index=True, nullable=False
    )
    source: Mapped[str] = mapped_column(String(16), default="voice")
    status: Mapped[str] = mapped_column(String(32), default="pending_confirmation")
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clarification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[Optional["User"]] = relationship("User")
    report: Mapped[Optional["Report"]] = relationship("Report")
# #END_BLOCK_AGENT_TASK_MODEL

# #START_BLOCK_ANALYTICS_EVENT_MODEL
class AnalyticsEvent(Base):
    """
    # PURPOSE: Store funnel analytics events for product tracking.
    """
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    event_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    event_metadata: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)
    
    # Context
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Product / Transaction
    product_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    
    # Performance
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Marketing
    utm_source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Tech
    device: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    browser: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[Optional["User"]] = relationship("User")
# #END_BLOCK_ANALYTICS_EVENT_MODEL

# #START_BLOCK_AUDIT_LOG_MODEL
class AuditLog(Base):
    """
    # PURPOSE: Track administrative actions for security and history.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    target_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[admin_id])
    target_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[target_user_id])
# #END_BLOCK_AUDIT_LOG_MODEL

# #START_BLOCK_CLIENT_MODEL
class Client(Base):
    """
    # PURPOSE: Store client identity and birth profile details.
    # INPUT: full_name, email, birth_datetime, birth_location.
    # OUTPUT: ORM client record with a unique identifier.
    # CONTEXT: Linked to reports and their sections.
    """

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    birth_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    birth_time_known: Mapped[bool] = mapped_column(Boolean, default=True)
    birth_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birth_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birth_timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    birth_place_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[Optional["User"]] = relationship("User")
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="client", cascade="all, delete-orphan"
    )
# #END_BLOCK_CLIENT_MODEL

# #START_BLOCK_REPORT_MODEL
class Report(Base):
    """
    # PURPOSE: Store report metadata and generation status.
    # INPUT: client_id, report_type, status, paid.
    # OUTPUT: ORM report record linked to a client.
    # CONTEXT: Contains a set of ReportChunk sections.
    """

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    access_source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    entitlement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "report_entitlements.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_reports_entitlement_id",
        ),
        nullable=True,
        index=True,
    )
    checkout_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "billing_checkout_sessions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_reports_checkout_session_id",
        ),
        nullable=True,
        index=True,
    )
    input_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    client: Mapped["Client"] = relationship("Client", back_populates="reports")
    user: Mapped[Optional["User"]] = relationship("User")
    entitlement: Mapped[Optional["ReportEntitlement"]] = relationship(
        "ReportEntitlement", foreign_keys=[entitlement_id]
    )
    checkout_session: Mapped[Optional["BillingCheckoutSession"]] = relationship(
        "BillingCheckoutSession", foreign_keys=[checkout_session_id]
    )
    chunks: Mapped[list["ReportChunk"]] = relationship(
        "ReportChunk", back_populates="report", cascade="all, delete-orphan"
    )
    runs: Mapped[list["ReportRun"]] = relationship(
        "ReportRun", back_populates="report", cascade="all, delete-orphan"
    )
# #END_BLOCK_REPORT_MODEL

# #START_BLOCK_REPORT_CHUNK_MODEL
class ReportChunk(Base):
    """
    # PURPOSE: Store a single report section (content and status).
    # INPUT: report_id, section, content, status, order_index.
    # OUTPUT: ORM report section record.
    # CONTEXT: Used by the LLM orchestrator and Markdown reporter.
    """

    __tablename__ = "report_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        index=True,
    )
    section: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    report: Mapped["Report"] = relationship("Report", back_populates="chunks")
# #END_BLOCK_REPORT_CHUNK_MODEL

# #START_BLOCK_REPORT_RUN_MODEL
class ReportRun(Base):
    """
    # PURPOSE: Track a single generation run for a report.
    # INPUT: report_id, status, error metadata.
    # OUTPUT: ORM run record for audit/debug.
    # CONTEXT: Used for pipeline observability.
    """

    __tablename__ = "report_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Usage Stats
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    report: Mapped["Report"] = relationship("Report", back_populates="runs")
# #END_BLOCK_REPORT_RUN_MODEL
