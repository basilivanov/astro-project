from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from enum import Enum
import uuid
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
import structlog

from ..core.config_business import HORARY_PACKS, REPORT_PRICES, SUBSCRIPTION_PRICE


logger = structlog.get_logger()


class BillingKind(str, Enum):
    SUBSCRIPTION = "subscription"
    CREDITS = "credits"
    REPORT_UNLOCK = "report_unlock"


class CheckoutSessionStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"
    EXPIRED = "expired"
    RESUMED = "resumed"


class EntitlementStatus(str, Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    REFUNDED = "refunded"
    REVOKED = "revoked"
    EXPIRED = "expired"


class EntitlementSource(str, Enum):
    PAYMENT = "payment"
    ADMIN_GRANT = "admin_grant"
    MIGRATION = "migration"
    SUPPORT = "support"


class AccessGrantSource(str, Enum):
    BYPASS = "bypass"
    FREE = "free"
    SUBSCRIPTION = "subscription"
    TRIAL = "trial"
    CREDITS = "credits"
    REPORT_ENTITLEMENT = "report_entitlement"


ONE_OFF_REPORT_TYPES = (
    "natal_master",
    "month_forecast",
    "year_forecast",
    "solar_return",
    "synastry",
)

ONE_OFF_REPORT_TYPE_ALIASES = {
    "solar_return_master": "solar_return",
    "synastry_master": "synastry",
}

LEGACY_SUBSCRIPTION_REPORT_TYPES = ("week_forecast",)


@dataclass(frozen=True)
class ProductCatalogEntry:
    product_code: str
    billing_kind: BillingKind
    amount: float
    currency: str = "RUB"
    report_type: Optional[str] = None
    pack_id: Optional[str] = None
    credits_qty: Optional[int] = None
    is_recurring: bool = False
    paywall_key: str = "default"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    report_type: str
    granted_via: Optional[AccessGrantSource] = None
    entitlement_id: Optional[str] = None
    remaining_unlocks: int = 0
    reason_code: str = "payment_required"
    legacy_subscription_applied: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_zero_report_unlocks() -> dict[str, int]:
    return {report_type: 0 for report_type in ONE_OFF_REPORT_TYPES}


def normalize_report_type(report_type: Optional[str]) -> Optional[str]:
    if report_type is None:
        return None
    normalized = str(report_type).strip()
    if not normalized:
        return None
    return ONE_OFF_REPORT_TYPE_ALIASES.get(normalized, normalized)


def normalize_product_code(product_code: Optional[str]) -> Optional[str]:
    return normalize_report_type(product_code)


def is_one_off_report_type(report_type: Optional[str]) -> bool:
    normalized = normalize_report_type(report_type)
    return bool(normalized and normalized in ONE_OFF_REPORT_TYPES)


def allow_access(
    report_type: str,
    granted_via: AccessGrantSource,
    entitlement_id: Optional[str] = None,
    remaining_unlocks: int = 0,
    legacy_subscription_applied: bool = False,
) -> AccessDecision:
    return AccessDecision(
        allowed=True,
        report_type=report_type,
        granted_via=granted_via,
        entitlement_id=entitlement_id,
        remaining_unlocks=remaining_unlocks,
        reason_code="ok",
        legacy_subscription_applied=legacy_subscription_applied,
    )


def deny_access(report_type: str, reason_code: str = "payment_required") -> AccessDecision:
    return AccessDecision(
        allowed=False,
        report_type=report_type,
        granted_via=None,
        entitlement_id=None,
        remaining_unlocks=0,
        reason_code=reason_code,
        legacy_subscription_applied=False,
    )


def resolve_catalog_product(product_code: str) -> Optional[ProductCatalogEntry]:
    normalized = normalize_product_code(product_code)
    if not normalized:
        return None
    return PRODUCT_CATALOG.get(normalized)


def _build_product_catalog() -> dict[str, ProductCatalogEntry]:
    catalog = {
        "subscription": ProductCatalogEntry(
            product_code="subscription",
            billing_kind=BillingKind.SUBSCRIPTION,
            amount=SUBSCRIPTION_PRICE,
            report_type="week_forecast",
            is_recurring=True,
            paywall_key="subscription",
        )
    }

    for pack_id, pack in HORARY_PACKS.items():
        catalog[pack_id] = ProductCatalogEntry(
            product_code=pack_id,
            billing_kind=BillingKind.CREDITS,
            amount=pack["price"],
            pack_id=pack_id,
            credits_qty=pack["credits"],
            paywall_key="horary_credits",
        )

    for report_type in ONE_OFF_REPORT_TYPES:
        catalog[report_type] = ProductCatalogEntry(
            product_code=report_type,
            billing_kind=BillingKind.REPORT_UNLOCK,
            amount=REPORT_PRICES[report_type],
            report_type=report_type,
            paywall_key="report_unlock",
        )

    return catalog


PRODUCT_CATALOG = _build_product_catalog()


def get_active_report_entitlement(
    db: Session,
    *,
    user_id: uuid.UUID,
    report_type: str,
):
    from ..models import ReportEntitlement

    normalized_report_type = normalize_report_type(report_type)
    if not normalized_report_type:
        return None

    return (
        db.query(ReportEntitlement)
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.report_type == normalized_report_type)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .order_by(ReportEntitlement.created_at.asc(), ReportEntitlement.id.asc())
        .first()
    )


def count_active_report_entitlements(
    db: Session,
    *,
    user_id: uuid.UUID,
    report_type: str,
) -> int:
    from ..models import ReportEntitlement

    normalized_report_type = normalize_report_type(report_type)
    if not normalized_report_type:
        return 0

    count = (
        db.query(func.count(ReportEntitlement.id))
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.report_type == normalized_report_type)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .scalar()
    )
    return int(count or 0)


def build_report_unlock_snapshot(db: Session, *, user_id: uuid.UUID) -> dict[str, int]:
    from ..models import ReportEntitlement

    snapshot = build_zero_report_unlocks()
    rows = (
        db.query(ReportEntitlement.report_type, func.count(ReportEntitlement.id))
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .filter(ReportEntitlement.report_type.in_(ONE_OFF_REPORT_TYPES))
        .group_by(ReportEntitlement.report_type)
        .all()
    )
    for report_type, count in rows:
        snapshot[str(report_type)] = int(count or 0)
    return snapshot


def grant_report_entitlement(
    db: Session,
    *,
    user_id: uuid.UUID,
    report_type: str,
    source: EntitlementSource = EntitlementSource.PAYMENT,
    checkout_session_id: Optional[uuid.UUID] = None,
    granted_transaction_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
):
    from ..models import BillingCheckoutSession, ReportEntitlement

    normalized_report_type = normalize_report_type(report_type)
    if not is_one_off_report_type(normalized_report_type):
        raise ValueError(f"Unsupported report entitlement type: {report_type}")

    entitlement = None
    if checkout_session_id is not None:
        entitlement = (
            db.query(ReportEntitlement)
            .filter(ReportEntitlement.checkout_session_id == checkout_session_id)
            .order_by(ReportEntitlement.created_at.asc(), ReportEntitlement.id.asc())
            .first()
        )
    if entitlement is None and granted_transaction_id is not None:
        entitlement = (
            db.query(ReportEntitlement)
            .filter(ReportEntitlement.granted_transaction_id == granted_transaction_id)
            .filter(ReportEntitlement.report_type == normalized_report_type)
            .order_by(ReportEntitlement.created_at.asc(), ReportEntitlement.id.asc())
            .first()
        )

    if entitlement is None:
        entitlement = ReportEntitlement(
            user_id=user_id,
            report_type=normalized_report_type,
            status=EntitlementStatus.ACTIVE.value,
            source=source.value,
            checkout_session_id=checkout_session_id,
            granted_transaction_id=granted_transaction_id,
            notes=notes,
        )
        db.add(entitlement)
        db.flush()
        action = "created"
    else:
        action = "reused"

    logger.info(
        "admin.entitlement_grant",
        action=action,
        source=source.value,
        report_type=normalized_report_type,
        user_id=str(user_id),
        entitlement_id=str(entitlement.id),
        checkout_session_id=str(checkout_session_id) if checkout_session_id else None,
        granted_transaction_id=str(granted_transaction_id) if granted_transaction_id else None,
        notes_present=bool(notes or entitlement.notes),
    )

    if checkout_session_id is not None:
        checkout_session = (
            db.query(BillingCheckoutSession)
            .filter(BillingCheckoutSession.id == checkout_session_id)
            .first()
        )
        if checkout_session is not None and checkout_session.entitlement_id != entitlement.id:
            checkout_session.entitlement_id = entitlement.id
            db.add(checkout_session)

    return entitlement


def consume_report_entitlement(
    db: Session,
    *,
    entitlement_id: uuid.UUID,
    user_id: uuid.UUID,
    report_id: uuid.UUID,
):
    from ..models import ReportEntitlement

    entitlement = (
        db.query(ReportEntitlement)
        .filter(ReportEntitlement.id == entitlement_id)
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .with_for_update()
        .first()
    )
    if entitlement is None:
        return None

    now = datetime.now(timezone.utc)
    entitlement.status = EntitlementStatus.CONSUMED.value
    entitlement.consumed_report_id = report_id
    entitlement.consumed_at = now
    db.add(entitlement)
    logger.info(
        "admin.entitlement_grant",
        action="consumed",
        user_id=str(user_id),
        report_id=str(report_id),
        entitlement_id=str(entitlement.id),
        report_type=entitlement.report_type,
        status=entitlement.status,
    )
    return entitlement
