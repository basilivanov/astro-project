# ############################################################################
# AI_HEADER: MODULE_ONE_OFF_ENTITLEMENTS
# ROLE: Owns typed catalog, entitlement grants, and runtime resume helpers for one-off reports.
# DEPENDENCIES: SQLAlchemy Session, backend.app.models, backend.app.core.config_business.
# GRACE_ANCHORS: [ONE_OFF_CATALOG, ENTITLEMENT_GRANT, ENTITLEMENT_RESUME]
# ############################################################################

# START_MODULE_CONTRACT: M-ONE-OFF-ENTITLEMENTS
# purpose: Provide canonical catalog alignment, entitlement storage, and runtime linkage for one-off report unlocks.
# owns:
#   - backend/app/services/one_off_entitlements.py
# inputs:
#   - Product codes and report types from billing/admin/runtime flows
#   - SQLAlchemy sessions when mutating entitlement state
# outputs:
#   - ProductCatalogEntry lookups aligned with access_control.align_catalog_product
#   - ReportEntitlement records, resume decisions, and access snapshots
# dependencies:
#   - backend.app.core.config_business (pricing + catalog seeds)
#   - backend.app.models (ReportEntitlement, BillingCheckoutSession)
#   - structlog for block-aware logging
# side_effects:
#   - Writes and updates ReportEntitlement/BillingCheckoutSession rows
#   - Emits block-aware structured logs compatible with access_control labels
# invariants:
#   - Unsupported report types are rejected early
#   - Entitlement reuse remains idempotent per checkout/grant transaction
# failure_policy:
#   - Raises ValueError for invalid products or report types
#   - Propagates DB exceptions to callers for transactional rollback
# trace_obligations:
#   - Every entrypoint emits module/contract/block markers through structured logs
#   - Mutation flows include correlation_id or entitlement_id on every event
#   - Catalog alignment logs mirror access_control labels for bridgeability
# non_goals:
#   - Managing billing provider sessions or UI orchestration
# END_MODULE_CONTRACT: M-ONE-OFF-ENTITLEMENTS

# START_MODULE_MAP: M-ONE-OFF-ENTITLEMENTS
# entrypoints:
#   - resolve_catalog_product (shared catalog lookup used by align_catalog_product)
#   - grant_one_off_entitlement (canonical entitlement mutation entrypoint)
#   - resume_catalog_checkout (checkout resume resolver for report unlocks)
#   - enqueue_runtime_grant (runtime/admin wrapper over grant_one_off_entitlement)
#   - sync_admin_entitlement (admin sync flow with aligned notes/source)
#   - ensure_catalog_alignment (bridge to access_control.align_catalog_product)
#   - reconcile_failed_grant (recovery helper for broken grant attempts)
#   - build_report_unlock_snapshot
#   - get_active_report_entitlement
#   - count_active_report_entitlements
#   - consume_report_entitlement
# queues:
#   - none (invoked synchronously via billing/admin flows)
# owned_tests:
#   - tests/test_one_off_entitlements_scaffold.py
#   - tests/test_billing_checkout_sessions.py
#   - tests/test_one_off_runtime_smoke.py
#   - tests/test_admin_grant_one_off_alignment.py
# adjacent_modules:
#   - backend/app/services/billing.py (webhook + checkout lifecycle)
#   - backend/app/services/access_control.py (runtime access decisions)
#   - backend/app/main.py (admin grant endpoints)
# END_MODULE_MAP: M-ONE-OFF-ENTITLEMENTS

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING

import structlog
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config_business import HORARY_PACKS, REPORT_PRICES, SUBSCRIPTION_PRICE
from ..logging_utils import get_correlation_ids, log_grace_event

if TYPE_CHECKING:  # pragma: no cover
    from ..models import BillingCheckoutSession


logger = structlog.get_logger()
MODULE_ID = "M-ONE-OFF-ENTITLEMENTS"


def _entitlements_log(
    level: str,
    event: str,
    *,
    fn: str,
    block: str,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields,
) -> None:
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        block=block,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **fields,
    )


def _trace_context(
    *,
    correlation_id: Optional[str] = None,
    entitlement_id: Optional[uuid.UUID | str] = None,
) -> dict[str, Optional[str]]:
    """Return normalized trace identifiers for entitlement/access logs."""
    trace_context = get_correlation_ids()
    resolved_correlation_id = correlation_id or trace_context.get("correlation_id")
    resolved_entitlement_id = str(entitlement_id) if entitlement_id is not None else None
    return {
        "correlation_id": resolved_correlation_id,
        "trace_id": trace_context.get("trace_id"),
        "correlation_source": trace_context.get("correlation_source"),
        "entitlement_id": resolved_entitlement_id,
    }


def _emit_contract_log(
    *,
    event: str,
    fn: str,
    block: str,
    contract: str,
    correlation_id: Optional[str] = None,
    entitlement_id: Optional[uuid.UUID | str] = None,
    level: str = "info",
    **fields,
) -> None:
    """Emit a canonical structured log with GRACE contract metadata."""
    trace_context = _trace_context(
        correlation_id=correlation_id,
        entitlement_id=entitlement_id,
    )
    _entitlements_log(
        level,
        event,
        fn=fn,
        block=block,
        contract=contract,
        correlation_id=trace_context["correlation_id"],
        trace_id=trace_context["trace_id"],
        correlation_source=trace_context["correlation_source"],
        entitlement_id=trace_context["entitlement_id"],
        **fields,
    )


class ResumeAccessError(RuntimeError):
    def __init__(self, message: str, *, reason: str, status_code: int = 409):
        super().__init__(message)
        self.reason = reason
        self.status_code = status_code


@dataclass(frozen=True)
class ResumeAccessDecision:
    status: str
    payload: Optional[dict[str, Any]] = None
    resumed_report_id: Optional[str] = None


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
    # START_CONTRACT: FN-RESOLVE-CATALOG-PRODUCT
    # purpose: Return catalog metadata for a given product/report alias.
    # inputs: raw product code from billing/admin flows.
    # side_effects: none.
    # returns: ProductCatalogEntry or None when unsupported.
    # END_CONTRACT: FN-RESOLVE-CATALOG-PRODUCT
    # START_BLOCK: NORMALIZE_PRODUCT_CODE
    normalized = normalize_product_code(product_code)
    # END_BLOCK: NORMALIZE_PRODUCT_CODE
    if not normalized:
        return None

    # START_BLOCK: LOOKUP_PRODUCT_CATALOG
    return PRODUCT_CATALOG.get(normalized)
    # END_BLOCK: LOOKUP_PRODUCT_CATALOG


def ensure_catalog_alignment(product_code: str) -> ProductCatalogEntry:
    # START_CONTRACT: FN-ENSURE-CATALOG-ALIGNMENT
    # purpose: Enforce canonical catalog alignment for one-off flows and mirror access_control labels.
    # inputs: raw product/report identifier from admin, billing, or runtime flows.
    # returns: ProductCatalogEntry guaranteed to be present in the local one-off catalog.
    # side_effects: emits alignment logs compatible with access_control.align_catalog_product.
    # errors: ValueError when product code is unsupported.
    # END_CONTRACT: FN-ENSURE-CATALOG-ALIGNMENT
    # START_BLOCK: CATALOG_ALIGNMENT_RESOLUTION
    contract = "FN-ENSURE-CATALOG-ALIGNMENT"
    trace_context = _trace_context()
    normalized_product_code = normalize_product_code(product_code)
    catalog_entry = resolve_catalog_product(product_code)
    if catalog_entry is None or normalized_product_code is None:
        _emit_contract_log(
            event="access_control.catalog_alignment_missing",
            fn="ensure_catalog_alignment",
            block="CATALOG_ALIGNMENT_RESOLUTION",
            contract=contract,
            correlation_id=trace_context["correlation_id"],
            level="error",
            result="fail",
            product_code=product_code,
            normalized_product_code=normalized_product_code,
        )
        raise ValueError(f"Unsupported catalog product: {product_code}")

    _emit_contract_log(
        event="access_control.catalog_alignment_ok",
        fn="ensure_catalog_alignment",
        block="CATALOG_ALIGNMENT_RESOLUTION",
        contract=contract,
        correlation_id=trace_context["correlation_id"],
        result="ok",
        product_code=product_code,
        normalized_product_code=normalized_product_code,
        report_type=catalog_entry.report_type,
        billing_kind=catalog_entry.billing_kind.value,
        paywall_key=catalog_entry.paywall_key,
        bridge_target="access_control.align_catalog_product",
        bridge_contract="access_control.ensure_entitlement_bridge",
    )
    return catalog_entry
    # END_BLOCK: CATALOG_ALIGNMENT_RESOLUTION


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
    # START_CONTRACT: FN-GET-ACTIVE-ENTITLEMENT
    # purpose: Load earliest active entitlement for user/report combination.
    # inputs: db session, user_id, report_type.
    # returns: ReportEntitlement or None.
    # END_CONTRACT: FN-GET-ACTIVE-ENTITLEMENT
    from ..models import ReportEntitlement

    # START_BLOCK: NORMALIZE_REPORT_TYPE
    normalized_report_type = normalize_report_type(report_type)
    # END_BLOCK: NORMALIZE_REPORT_TYPE
    if not normalized_report_type:
        return None

    # START_BLOCK: LOAD_ACTIVE_ENTITLEMENT
    return (
        db.query(ReportEntitlement)
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.report_type == normalized_report_type)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .order_by(ReportEntitlement.created_at.asc(), ReportEntitlement.id.asc())
        .first()
    )
    # END_BLOCK: LOAD_ACTIVE_ENTITLEMENT


def count_active_report_entitlements(
    db: Session,
    *,
    user_id: uuid.UUID,
    report_type: str,
) -> int:
    # START_CONTRACT: FN-COUNT-ACTIVE-ENTITLEMENTS
    # purpose: Count active entitlements per report type.
    # inputs: db session, user_id, report_type.
    # returns: integer count (0 when unsupported type).
    # END_CONTRACT: FN-COUNT-ACTIVE-ENTITLEMENTS
    from ..models import ReportEntitlement

    # START_BLOCK: NORMALIZE_REPORT_TYPE
    normalized_report_type = normalize_report_type(report_type)
    # END_BLOCK: NORMALIZE_REPORT_TYPE
    if not normalized_report_type:
        return 0

    # START_BLOCK: COUNT_ACTIVE_ENTITLEMENTS
    count = (
        db.query(func.count(ReportEntitlement.id))
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.report_type == normalized_report_type)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .scalar()
    )
    return int(count or 0)
    # END_BLOCK: COUNT_ACTIVE_ENTITLEMENTS


def build_report_unlock_snapshot(db: Session, *, user_id: uuid.UUID) -> dict[str, int]:
    # START_CONTRACT: FN-BUILD-UNLOCK-SNAPSHOT
    # purpose: Produce current unlock counts per report type.
    # inputs: db session, user id.
    # returns: dict {report_type: count} covering ONE_OFF_REPORT_TYPES.
    # END_CONTRACT: FN-BUILD-UNLOCK-SNAPSHOT
    from ..models import ReportEntitlement

    # START_BLOCK: INITIALIZE_ZERO_SNAPSHOT
    snapshot = build_zero_report_unlocks()
    # END_BLOCK: INITIALIZE_ZERO_SNAPSHOT

    # START_BLOCK: LOAD_ACTIVE_UNLOCK_COUNTS
    rows = (
        db.query(ReportEntitlement.report_type, func.count(ReportEntitlement.id))
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .filter(ReportEntitlement.report_type.in_(ONE_OFF_REPORT_TYPES))
        .group_by(ReportEntitlement.report_type)
        .all()
    )
    # END_BLOCK: LOAD_ACTIVE_UNLOCK_COUNTS

    # START_BLOCK: MERGE_UNLOCK_COUNTS
    for report_type, count in rows:
        snapshot[str(report_type)] = int(count or 0)
    return snapshot
    # END_BLOCK: MERGE_UNLOCK_COUNTS


def grant_one_off_entitlement(
    db: Session,
    *,
    user_id: uuid.UUID,
    report_type: str,
    source: EntitlementSource = EntitlementSource.PAYMENT,
    checkout_session_id: Optional[uuid.UUID] = None,
    granted_transaction_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
):
    # START_CONTRACT: FN-GRANT-ONE-OFF-ENTITLEMENT
    # purpose: Create or reuse a report entitlement for a user, linking it to billing transactions.
    # inputs:
    #   - user_id: UUID of the report owner
    #   - report_type: canonical or alias string
    #   - source/granted_transaction_id/checkout_session_id: audit context
    # side_effects:
    #   - Inserts or updates ReportEntitlement rows
    #   - May re-link BillingCheckoutSession.entitlement_id
    # errors: ValueError when report_type is unsupported
    # END_CONTRACT: FN-GRANT-ONE-OFF-ENTITLEMENT
    from ..models import BillingCheckoutSession, ReportEntitlement

    contract = "FN-GRANT-ONE-OFF-ENTITLEMENT"
    # START_BLOCK: VALIDATE_CATALOG_ALIGNMENT
    normalized_report_type = normalize_report_type(report_type)
    if not is_one_off_report_type(normalized_report_type):
        _emit_contract_log(
            event="access_control.catalog_alignment_missing",
            fn="grant_one_off_entitlement",
            block="VALIDATE_CATALOG_ALIGNMENT",
            contract=contract,
            level="error",
            result="fail",
            user_id=str(user_id),
            product_code=report_type,
            normalized_product_code=normalized_report_type,
        )
        raise ValueError(f"Unsupported report entitlement type: {report_type}")
    catalog_entry = ensure_catalog_alignment(normalized_report_type)
    # END_BLOCK: VALIDATE_CATALOG_ALIGNMENT

    trace_context = _trace_context()

    entitlement = None
    # START_BLOCK: LOOKUP_BY_CHECKOUT
    if checkout_session_id is not None:
        entitlement = (
            db.query(ReportEntitlement)
            .filter(ReportEntitlement.checkout_session_id == checkout_session_id)
            .order_by(ReportEntitlement.created_at.asc(), ReportEntitlement.id.asc())
            .first()
        )
        if entitlement is not None:
            _emit_contract_log(
                event="admin.entitlement_grant.checkout_reused",
                fn="grant_one_off_entitlement",
                block="LOOKUP_BY_CHECKOUT",
                contract=contract,
                correlation_id=trace_context["correlation_id"],
                entitlement_id=entitlement.id,
                result="ok",
                user_id=str(user_id),
                checkout_session_id=str(checkout_session_id),
                report_type=normalized_report_type,
            )
    # END_BLOCK: LOOKUP_BY_CHECKOUT

    # START_BLOCK: LOOKUP_BY_TRANSACTION
    if entitlement is None and granted_transaction_id is not None:
        entitlement = (
            db.query(ReportEntitlement)
            .filter(ReportEntitlement.granted_transaction_id == granted_transaction_id)
            .filter(ReportEntitlement.report_type == normalized_report_type)
            .order_by(ReportEntitlement.created_at.asc(), ReportEntitlement.id.asc())
            .first()
        )
        if entitlement is not None:
            _emit_contract_log(
                event="admin.entitlement_grant.transaction_reused",
                fn="grant_one_off_entitlement",
                block="LOOKUP_BY_TRANSACTION",
                contract=contract,
                correlation_id=trace_context["correlation_id"],
                entitlement_id=entitlement.id,
                result="ok",
                user_id=str(user_id),
                granted_transaction_id=str(granted_transaction_id),
                report_type=normalized_report_type,
            )
    # END_BLOCK: LOOKUP_BY_TRANSACTION

    # START_BLOCK: UPSERT_ENTITLEMENT
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
    _emit_contract_log(
        event="admin.entitlement_grant.upserted",
        fn="grant_one_off_entitlement",
        block="UPSERT_ENTITLEMENT",
        contract=contract,
        correlation_id=trace_context["correlation_id"],
        entitlement_id=entitlement.id,
        result="ok",
        action=action,
        source=source.value,
        report_type=normalized_report_type,
        billing_kind=catalog_entry.billing_kind.value,
        user_id=str(user_id),
        checkout_session_id=str(checkout_session_id) if checkout_session_id else None,
        granted_transaction_id=str(granted_transaction_id) if granted_transaction_id else None,
        notes_present=bool(notes or entitlement.notes),
    )
    # END_BLOCK: UPSERT_ENTITLEMENT

    # START_BLOCK: LINK_CHECKOUT_SESSION
    if checkout_session_id is not None:
        checkout_session = (
            db.query(BillingCheckoutSession)
            .filter(BillingCheckoutSession.id == checkout_session_id)
            .first()
        )
        if checkout_session is not None and checkout_session.entitlement_id != entitlement.id:
            checkout_session.entitlement_id = entitlement.id
            db.add(checkout_session)
            _emit_contract_log(
                event="admin.entitlement_grant.checkout_linked",
                fn="grant_one_off_entitlement",
                block="LINK_CHECKOUT_SESSION",
                contract=contract,
                correlation_id=trace_context["correlation_id"],
                entitlement_id=entitlement.id,
                result="ok",
                checkout_session_id=str(checkout_session_id),
                user_id=str(user_id),
                report_type=normalized_report_type,
            )
    # END_BLOCK: LINK_CHECKOUT_SESSION

    return entitlement


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
    """Backward-compatible alias for the canonical one-off entitlement grant entrypoint."""
    return grant_one_off_entitlement(
        db,
        user_id=user_id,
        report_type=report_type,
        source=source,
        checkout_session_id=checkout_session_id,
        granted_transaction_id=granted_transaction_id,
        notes=notes,
    )


def enqueue_runtime_grant(
    db: Session,
    *,
    user_id: uuid.UUID,
    report_type: str,
    source: EntitlementSource = EntitlementSource.PAYMENT,
    checkout_session_id: Optional[uuid.UUID] = None,
    granted_transaction_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
):
    # START_CONTRACT: FN-ENQUEUE-RUNTIME-GRANT
    # purpose: Runtime/admin wrapper that normalizes grant requests before creating one-off entitlements.
    # inputs: db session, user_id, report_type, optional audit linkage ids, notes.
    # returns: ReportEntitlement persisted or reused by grant_one_off_entitlement.
    # side_effects: emits queue-style logs while executing synchronously.
    # errors: propagates ValueError/DB exceptions from catalog validation or grant mutation.
    # END_CONTRACT: FN-ENQUEUE-RUNTIME-GRANT
    contract = "FN-ENQUEUE-RUNTIME-GRANT"
    # START_BLOCK: NORMALIZE_RUNTIME_GRANT
    catalog_entry = ensure_catalog_alignment(report_type)
    _emit_contract_log(
        event="admin.entitlement_grant.enqueued",
        fn="enqueue_runtime_grant",
        block="NORMALIZE_RUNTIME_GRANT",
        contract=contract,
        result="ok",
        user_id=str(user_id),
        product_code=report_type,
        report_type=catalog_entry.report_type,
        checkout_session_id=str(checkout_session_id) if checkout_session_id else None,
        granted_transaction_id=str(granted_transaction_id) if granted_transaction_id else None,
    )
    # END_BLOCK: NORMALIZE_RUNTIME_GRANT

    # START_BLOCK: EXECUTE_RUNTIME_GRANT
    entitlement = grant_one_off_entitlement(
        db,
        user_id=user_id,
        report_type=catalog_entry.report_type or report_type,
        source=source,
        checkout_session_id=checkout_session_id,
        granted_transaction_id=granted_transaction_id,
        notes=notes,
    )
    _emit_contract_log(
        event="admin.entitlement_grant.completed",
        fn="enqueue_runtime_grant",
        block="EXECUTE_RUNTIME_GRANT",
        contract=contract,
        entitlement_id=entitlement.id,
        result="ok",
        user_id=str(user_id),
        report_type=entitlement.report_type,
        source=entitlement.source,
    )
    return entitlement
    # END_BLOCK: EXECUTE_RUNTIME_GRANT


def sync_admin_entitlement(
    db: Session,
    *,
    user_id: uuid.UUID,
    product_code: str,
    checkout_session_id: Optional[uuid.UUID] = None,
    granted_transaction_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
):
    # START_CONTRACT: FN-SYNC-ADMIN-ENTITLEMENT
    # purpose: Sync an admin-triggered unlock request into the canonical entitlement ledger.
    # inputs: db session, user id, raw product code, optional linkage ids, notes.
    # returns: ReportEntitlement for the aligned one-off report product.
    # side_effects: emits admin sync logs and delegates grant creation to enqueue_runtime_grant.
    # errors: ValueError when product_code does not resolve to a report unlock.
    # END_CONTRACT: FN-SYNC-ADMIN-ENTITLEMENT
    contract = "FN-SYNC-ADMIN-ENTITLEMENT"
    # START_BLOCK: ALIGN_ADMIN_PRODUCT
    catalog_entry = ensure_catalog_alignment(product_code)
    if catalog_entry.billing_kind != BillingKind.REPORT_UNLOCK or not catalog_entry.report_type:
        _emit_contract_log(
            event="admin.entitlement_grant.unsupported_kind",
            fn="sync_admin_entitlement",
            block="ALIGN_ADMIN_PRODUCT",
            contract=contract,
            level="error",
            result="fail",
            user_id=str(user_id),
            product_code=product_code,
            billing_kind=catalog_entry.billing_kind.value,
        )
        raise ValueError(f"Unsupported admin entitlement product: {product_code}")
    # END_BLOCK: ALIGN_ADMIN_PRODUCT

    # START_BLOCK: ISSUE_ADMIN_GRANT
    entitlement = enqueue_runtime_grant(
        db,
        user_id=user_id,
        report_type=catalog_entry.report_type,
        source=EntitlementSource.ADMIN_GRANT,
        checkout_session_id=checkout_session_id,
        granted_transaction_id=granted_transaction_id,
        notes=notes,
    )
    _emit_contract_log(
        event="admin.entitlement_grant.synced",
        fn="sync_admin_entitlement",
        block="ISSUE_ADMIN_GRANT",
        contract=contract,
        entitlement_id=entitlement.id,
        result="ok",
        user_id=str(user_id),
        product_code=product_code,
        report_type=entitlement.report_type,
    )
    return entitlement
    # END_BLOCK: ISSUE_ADMIN_GRANT


def reconcile_failed_grant(
    db: Session,
    *,
    user_id: uuid.UUID,
    report_type: str,
    checkout_session_id: Optional[uuid.UUID] = None,
    granted_transaction_id: Optional[uuid.UUID] = None,
):
    # START_CONTRACT: FN-RECONCILE-FAILED-GRANT
    # purpose: Recover entitlement linkage after a partial grant failure without duplicating unlocks.
    # inputs: db session, user_id, report_type, optional checkout/transaction linkage ids.
    # returns: existing or newly restored ReportEntitlement.
    # side_effects: may emit recovery logs and create/reuse entitlement rows.
    # errors: propagates ValueError/DB exceptions from downstream grant logic.
    # END_CONTRACT: FN-RECONCILE-FAILED-GRANT
    contract = "FN-RECONCILE-FAILED-GRANT"
    # START_BLOCK: LOAD_EXISTING_ENTITLEMENT
    entitlement = get_active_report_entitlement(
        db,
        user_id=user_id,
        report_type=report_type,
    )
    if entitlement is not None:
        _emit_contract_log(
            event="admin.entitlement_grant.reconciled_existing",
            fn="reconcile_failed_grant",
            block="LOAD_EXISTING_ENTITLEMENT",
            contract=contract,
            entitlement_id=entitlement.id,
            result="ok",
            user_id=str(user_id),
            report_type=entitlement.report_type,
        )
        return entitlement
    # END_BLOCK: LOAD_EXISTING_ENTITLEMENT

    # START_BLOCK: REISSUE_GRANT
    entitlement = enqueue_runtime_grant(
        db,
        user_id=user_id,
        report_type=report_type,
        source=EntitlementSource.SUPPORT,
        checkout_session_id=checkout_session_id,
        granted_transaction_id=granted_transaction_id,
        notes="reconciled_failed_grant",
    )
    _emit_contract_log(
        event="admin.entitlement_grant.reissued",
        fn="reconcile_failed_grant",
        block="REISSUE_GRANT",
        contract=contract,
        entitlement_id=entitlement.id,
        result="ok",
        user_id=str(user_id),
        report_type=entitlement.report_type,
    )
    return entitlement
    # END_BLOCK: REISSUE_GRANT


def resume_catalog_checkout(checkout_session: "BillingCheckoutSession") -> ResumeAccessDecision:
    # START_CONTRACT: FN-RESUME-CATALOG-CHECKOUT
    # purpose: Resolve how a finished checkout should resume report-unlock UX/runtime flow.
    # inputs: BillingCheckoutSession ORM object with optional entitlement/report linkage.
    # returns: ResumeAccessDecision for client redirect/resume handling.
    # side_effects: emits structured logs for resumed, pending, and invalid states.
    # errors: ResumeAccessError for non-resumable or invalid checkout states.
    # END_CONTRACT: FN-RESUME-CATALOG-CHECKOUT
    contract = "FN-RESUME-CATALOG-CHECKOUT"
    trace_context = _trace_context(entitlement_id=checkout_session.entitlement_id)

    # START_BLOCK: VALIDATE_CHECKOUT_KIND
    if getattr(checkout_session, "billing_kind", None) != BillingKind.REPORT_UNLOCK.value:
        _emit_contract_log(
            event="admin.entitlement_grant.resume_invalid_kind",
            fn="resume_catalog_checkout",
            block="VALIDATE_CHECKOUT_KIND",
            contract=contract,
            correlation_id=trace_context["correlation_id"],
            entitlement_id=trace_context["entitlement_id"],
            level="error",
            result="fail",
            checkout_session_id=str(checkout_session.id),
            billing_kind=getattr(checkout_session, "billing_kind", None),
        )
        raise ResumeAccessError(
            "Checkout is not a one-off report unlock",
            reason="invalid_billing_kind",
        )
    # END_BLOCK: VALIDATE_CHECKOUT_KIND

    # START_BLOCK: RESUME_EXISTING_REPORT
    if getattr(checkout_session, "resumed_report_id", None):
        resumed_report_id = str(checkout_session.resumed_report_id)
        _emit_contract_log(
            event="admin.entitlement_grant.resume_existing_report",
            fn="resume_catalog_checkout",
            block="RESUME_EXISTING_REPORT",
            contract=contract,
            correlation_id=trace_context["correlation_id"],
            entitlement_id=trace_context["entitlement_id"],
            result="ok",
            checkout_session_id=str(checkout_session.id),
            resumed_report_id=resumed_report_id,
        )
        return ResumeAccessDecision(status="already_resumed", resumed_report_id=resumed_report_id)
    # END_BLOCK: RESUME_EXISTING_REPORT

    # START_BLOCK: RESUME_PENDING_ENTITLEMENT
    if getattr(checkout_session, "entitlement_id", None):
        payload = {
            "checkout_session_id": str(checkout_session.id),
            "entitlement_id": str(checkout_session.entitlement_id),
            "report_type": normalize_report_type(getattr(checkout_session, "product_code", None)),
        }
        _emit_contract_log(
            event="admin.entitlement_grant.resume_pending",
            fn="resume_catalog_checkout",
            block="RESUME_PENDING_ENTITLEMENT",
            contract=contract,
            correlation_id=trace_context["correlation_id"],
            entitlement_id=trace_context["entitlement_id"],
            result="ok",
            **payload,
        )
        return ResumeAccessDecision(status="resume_available", payload=payload)
    # END_BLOCK: RESUME_PENDING_ENTITLEMENT

    _emit_contract_log(
        event="admin.entitlement_grant.resume_unavailable",
        fn="resume_catalog_checkout",
        block="RESUME_PENDING_ENTITLEMENT",
        contract=contract,
        correlation_id=trace_context["correlation_id"],
        entitlement_id=trace_context["entitlement_id"],
        level="error",
        result="fail",
        checkout_session_id=str(checkout_session.id),
    )
    raise ResumeAccessError(
        "Checkout has no entitlement to resume",
        reason="entitlement_missing",
    )


def consume_report_entitlement(
    db: Session,
    *,
    entitlement_id: uuid.UUID,
    user_id: uuid.UUID,
    report_id: uuid.UUID,
):
    # START_CONTRACT: FN-CONSUME-ENTITLEMENT
    # purpose: Mark active entitlement as consumed for a generated report.
    # inputs: entitlement_id, user_id, report_id, db session.
    # side_effects: Updates entitlement row, emits structlog.
    # returns: ReportEntitlement or None when not found.
    # END_CONTRACT: FN-CONSUME-ENTITLEMENT
    from ..models import ReportEntitlement

    contract = "FN-CONSUME-ENTITLEMENT"
    # START_BLOCK: LOAD_ACTIVE_ENTITLEMENT
    entitlement = (
        db.query(ReportEntitlement)
        .filter(ReportEntitlement.id == entitlement_id)
        .filter(ReportEntitlement.user_id == user_id)
        .filter(ReportEntitlement.status == EntitlementStatus.ACTIVE.value)
        .with_for_update()
        .first()
    )
    # END_BLOCK: LOAD_ACTIVE_ENTITLEMENT
    if entitlement is None:
        return None

    # START_BLOCK: MARK_ENTITLEMENT_CONSUMED
    now = datetime.now(timezone.utc)
    entitlement.status = EntitlementStatus.CONSUMED.value
    entitlement.consumed_report_id = report_id
    entitlement.consumed_at = now
    db.add(entitlement)
    _emit_contract_log(
        event="access_control.consume_entitlement_complete",
        fn="consume_report_entitlement",
        block="MARK_ENTITLEMENT_CONSUMED",
        contract=contract,
        entitlement_id=entitlement.id,
        result="ok",
        user_id=str(user_id),
        report_id=str(report_id),
        report_type=entitlement.report_type,
        status=entitlement.status,
    )
    return entitlement
    # END_BLOCK: MARK_ENTITLEMENT_CONSUMED
