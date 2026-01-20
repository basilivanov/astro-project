# ############################################################################
# AI_HEADER: MODULE_MODELS
# ROLE: SQLAlchemy ORM models for core entities.
# DEPENDENCIES: sqlalchemy, backend/app/db.py
# GRACE_ANCHORS: [CLIENT_MODEL, REPORT_MODEL, REPORT_CHUNK_MODEL, REPORT_RUN_MODEL, USER_MODEL, SUBSCRIPTION_MODEL, REFERRAL_MODEL, TRANSACTION_MODEL]
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
    
    # Commercial
    is_partner: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    subscription_active_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
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
# #END_BLOCK_USER_MODEL

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
        DateTime(timezone=True), onupdate=func.now()
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
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    birth_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    birth_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birth_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birth_timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    birth_place_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

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
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
