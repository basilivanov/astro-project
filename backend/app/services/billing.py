# ############################################################################
# AI_HEADER: MODULE_BILLING_SERVICE
# ROLE: YooKassa integration logic.
# DEPENDENCIES: yookassa, sqlalchemy, backend.app.models.
# GRACE_ANCHORS: [BILLING_CONFIG, CREATE_PAYMENT, WEBHOOK_HANDLER]
# ############################################################################

import json
import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from yookassa import Configuration, Payment
from sqlalchemy.orm import Session

from ..core.feature_flags import is_one_off_entitlements_runtime_enabled
from ..models import BillingCheckoutSession, Subscription, Transaction, User
from ..services.analytics import log_analytics_event
from .one_off_entitlements import (
    BillingKind,
    CheckoutSessionStatus,
    EntitlementSource,
    grant_report_entitlement,
    is_one_off_report_type,
    normalize_product_code,
    normalize_report_type,
)

logger = structlog.get_logger()

# #START_BLOCK_BILLING_CONFIG
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

if SHOP_ID and SECRET_KEY:
    Configuration.account_id = SHOP_ID
    Configuration.secret_key = SECRET_KEY
else:
    logger.warning("billing.config_missing", msg="YooKassa credentials not found.")
# #END_BLOCK_BILLING_CONFIG


def build_checkout_return_url(resume_token: str) -> str:
    base_url = os.getenv("WEBAPP_URL", "https://t.me/AstroGraceBot").rstrip("/")
    return f"{base_url}/billing/complete?checkout={resume_token}"


def _serialize_draft_payload(draft_payload: Optional[dict]) -> Optional[str]:
    if draft_payload is None:
        return None
    return json.dumps(draft_payload, ensure_ascii=True, separators=(",", ":"))


def create_checkout_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    billing_kind: str,
    product_code: str,
    amount: float,
    currency: str = "RUB",
    provider: str = "yookassa",
    report_type: Optional[str] = None,
    pack_id: Optional[str] = None,
    return_path: Optional[str] = None,
    draft_payload: Optional[dict] = None,
) -> BillingCheckoutSession:
    normalized_product_code = normalize_product_code(product_code) or product_code
    normalized_report_type = normalize_report_type(report_type)

    checkout_session = BillingCheckoutSession(
        user_id=user_id,
        provider=provider,
        status=CheckoutSessionStatus.CREATED.value,
        billing_kind=billing_kind,
        product_code=normalized_product_code,
        report_type=normalized_report_type,
        pack_id=pack_id,
        amount=Decimal(str(amount)),
        currency=currency,
        idempotence_key=str(uuid.uuid4()),
        resume_token=uuid.uuid4().hex,
        return_path=return_path,
        draft_payload=_serialize_draft_payload(draft_payload),
    )
    db.add(checkout_session)
    db.commit()
    db.refresh(checkout_session)
    logger.info(
        "billing.checkout_session_created",
        session_id=str(checkout_session.id),
        user_id=str(user_id),
        billing_kind=billing_kind,
        product_code=product_code,
    )
    return checkout_session


def _update_checkout_session_status(
    checkout_session: BillingCheckoutSession,
    *,
    status: str,
    provider_payment_id: Optional[str] = None,
    provider_status: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    now = datetime.now(timezone.utc)
    checkout_session.status = status
    if provider_payment_id:
        checkout_session.provider_payment_id = provider_payment_id
    if provider_status:
        checkout_session.provider_status = provider_status
    if error_code is not None:
        checkout_session.error_code = error_code
    if error_message is not None:
        checkout_session.error_message = error_message
    if status == CheckoutSessionStatus.SUCCEEDED.value and checkout_session.succeeded_at is None:
        checkout_session.succeeded_at = now
    if status == CheckoutSessionStatus.CANCELED.value and checkout_session.canceled_at is None:
        checkout_session.canceled_at = now


def mark_checkout_session_pending(
    db: Session,
    checkout_session: BillingCheckoutSession,
    payment_data: dict,
) -> BillingCheckoutSession:
    _update_checkout_session_status(
        checkout_session,
        status=CheckoutSessionStatus.PENDING.value,
        provider_payment_id=payment_data.get("id"),
        provider_status=payment_data.get("status"),
        error_code=None,
        error_message=None,
    )
    db.add(checkout_session)
    db.commit()
    db.refresh(checkout_session)
    return checkout_session


def mark_checkout_session_failed(
    db: Session,
    checkout_session: BillingCheckoutSession,
    *,
    error_code: str,
    error_message: str,
) -> BillingCheckoutSession:
    _update_checkout_session_status(
        checkout_session,
        status=CheckoutSessionStatus.FAILED.value,
        error_code=error_code,
        error_message=error_message,
    )
    db.add(checkout_session)
    db.commit()
    db.refresh(checkout_session)
    return checkout_session


def get_checkout_session_by_token(
    db: Session,
    resume_token: str,
    *,
    user_id: Optional[uuid.UUID] = None,
) -> Optional[BillingCheckoutSession]:
    query = db.query(BillingCheckoutSession).filter(
        BillingCheckoutSession.resume_token == resume_token
    )
    if user_id is not None:
        query = query.filter(BillingCheckoutSession.user_id == user_id)
    return query.first()


def serialize_checkout_session(checkout_session: BillingCheckoutSession) -> dict[str, object]:
    return {
        "checkout_token": checkout_session.resume_token,
        "status": checkout_session.status,
        "provider": checkout_session.provider,
        "billing_kind": checkout_session.billing_kind,
        "product_code": checkout_session.product_code,
        "report_type": checkout_session.report_type,
        "pack_id": checkout_session.pack_id,
        "amount": float(checkout_session.amount),
        "currency": checkout_session.currency,
        "provider_status": checkout_session.provider_status,
        "return_path": checkout_session.return_path,
        "has_draft_payload": checkout_session.draft_payload is not None,
        "entitlement_id": str(checkout_session.entitlement_id) if checkout_session.entitlement_id else None,
        "resumed_report_id": str(checkout_session.resumed_report_id) if checkout_session.resumed_report_id else None,
        "created_at": checkout_session.created_at.isoformat() if checkout_session.created_at else None,
        "succeeded_at": checkout_session.succeeded_at.isoformat() if checkout_session.succeeded_at else None,
        "canceled_at": checkout_session.canceled_at.isoformat() if checkout_session.canceled_at else None,
        "error_code": checkout_session.error_code,
        "error_message": checkout_session.error_message,
    }


def _resolve_checkout_session_from_metadata(
    metadata: dict,
    db: Session,
) -> Optional[BillingCheckoutSession]:
    checkout_session_id = metadata.get("checkout_session_id")
    if not checkout_session_id:
        return None

    try:
        checkout_session_uuid = uuid.UUID(checkout_session_id)
    except ValueError:
        logger.warning("billing.webhook_bad_checkout_session_uuid", checkout_session_id=checkout_session_id)
        return None

    return db.query(BillingCheckoutSession).filter(
        BillingCheckoutSession.id == checkout_session_uuid
    ).first()


def _resolve_billing_kind(metadata: dict, checkout_session: Optional[BillingCheckoutSession]) -> str:
    if checkout_session and checkout_session.billing_kind:
        return checkout_session.billing_kind

    billing_kind = metadata.get("billing_kind")
    if billing_kind:
        return str(billing_kind)

    product_type = normalize_product_code(metadata.get("product_type"))
    if product_type in {"horary", "credits"}:
        return BillingKind.CREDITS.value
    if is_one_off_entitlements_runtime_enabled() and is_one_off_report_type(product_type):
        return BillingKind.REPORT_UNLOCK.value
    return BillingKind.SUBSCRIPTION.value


def _resolve_report_unlock_type(
    metadata: dict,
    checkout_session: Optional[BillingCheckoutSession],
) -> Optional[str]:
    report_type = normalize_report_type(checkout_session.report_type if checkout_session else None)
    if report_type:
        return report_type

    report_type = normalize_report_type(metadata.get("report_type"))
    if report_type:
        return report_type

    product_code = normalize_product_code(metadata.get("product_code"))
    if is_one_off_report_type(product_code):
        return product_code

    product_type = normalize_product_code(metadata.get("product_type"))
    if is_one_off_report_type(product_type):
        return product_type

    return None


def _ensure_checkout_session_succeeded(
    checkout_session: Optional[BillingCheckoutSession],
    *,
    payment_object: dict,
) -> None:
    if checkout_session is None:
        return

    _update_checkout_session_status(
        checkout_session,
        status=CheckoutSessionStatus.SUCCEEDED.value,
        provider_payment_id=payment_object.get("id"),
        provider_status=payment_object.get("status"),
        error_code=None,
        error_message=None,
    )


def _ensure_report_unlock_entitlement(
    db: Session,
    *,
    user: User,
    checkout_session: Optional[BillingCheckoutSession],
    transaction: Transaction,
    metadata: dict,
):
    report_type = _resolve_report_unlock_type(metadata, checkout_session)
    if not report_type:
        logger.error(
            "billing.report_unlock_missing_report_type",
            user_id=str(user.id),
            checkout_session_id=str(checkout_session.id) if checkout_session else None,
            metadata=metadata,
        )
        return None

    entitlement = grant_report_entitlement(
        db,
        user_id=user.id,
        report_type=report_type,
        source=EntitlementSource.PAYMENT,
        checkout_session_id=checkout_session.id if checkout_session else None,
        granted_transaction_id=transaction.id,
    )

    if checkout_session is not None and checkout_session.entitlement_id != entitlement.id:
        checkout_session.entitlement_id = entitlement.id
        db.add(checkout_session)

    return entitlement


# #START_BLOCK_CREATE_PAYMENT
def create_payment(
    user_id: uuid.UUID,
    amount: float,
    description: str,
    is_recurring: bool = False,
    metadata: dict = None,
    return_url: Optional[str] = None,
    idempotence_key: Optional[str] = None,
) -> str:
    """
    # PURPOSE: Create a payment intent in YooKassa.
    # INPUT: user_id, amount, desc, recurring flag, metadata.
    # OUTPUT: JSON string with confirmation URL.
    """
    if not SHOP_ID:
        raise ValueError("Billing not configured")

    idempotence_key = idempotence_key or str(uuid.uuid4())
    
    meta = {
        "user_id": str(user_id),
        "is_recurring": str(is_recurring)
    }
    if metadata:
        meta.update(metadata)
    
    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": return_url or os.getenv("WEBAPP_URL", "https://t.me/AstroGraceBot")
        },
        "description": description,
        "metadata": meta,
        "save_payment_method": is_recurring
    }

    try:
        payment = Payment.create(payload, idempotence_key)
        return json.dumps(payment, default=str)
    except Exception as e:
        logger.error("billing.create_failed", error=str(e))
        raise e
# #END_BLOCK_CREATE_PAYMENT


# #START_BLOCK_WEBHOOK_HANDLER
def handle_payment_succeeded(payment_object: dict, db: Session):
    """
    # PURPOSE: Process successful payment webhook.
    # LOGIC:
    # 1. Log transaction.
    # 2. Update/Create Subscription.
    # 3. Add 30 days access.
    # 4. Save payment method if recurring.
    """
    metadata = payment_object.get("metadata", {})
    checkout_session = _resolve_checkout_session_from_metadata(metadata, db)
    payment_id = payment_object.get("id")
    billing_kind = _resolve_billing_kind(metadata, checkout_session)
    if (
        checkout_session
        and checkout_session.provider_payment_id == payment_id
        and checkout_session.status in {CheckoutSessionStatus.SUCCEEDED.value, CheckoutSessionStatus.RESUMED.value}
    ):
        logger.info(
            "billing.webhook_duplicate_checkout_session",
            payment_id=payment_id,
            session_id=str(checkout_session.id),
        )
        return

    user_id_str = metadata.get("user_id")
    if checkout_session:
        user_id_str = str(checkout_session.user_id)
    is_recurring = metadata.get("is_recurring") == "True"
    
    amount_val = payment_object.get("amount", {}).get("value")
    currency = payment_object.get("amount", {}).get("currency")
    payment_method = payment_object.get("payment_method", {})
    payment_method_id = payment_method.get("id")
    saved = payment_method.get("saved", False)

    if not user_id_str:
        logger.error("billing.webhook_no_user", payment_id=payment_object.get("id"))
        return

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        logger.error("billing.webhook_bad_uuid", user_id=user_id_str)
        return

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        logger.error("billing.webhook_user_not_found", user_id=user_id_str)
        return

    existing_payment = db.query(Transaction).filter(
        Transaction.type == "payment",
        Transaction.provider_id == payment_id,
    ).first()
    if existing_payment:
        needs_commit = False
        if (
            billing_kind == BillingKind.REPORT_UNLOCK.value
            and is_one_off_entitlements_runtime_enabled()
        ):
            _ensure_report_unlock_entitlement(
                db,
                user=user,
                checkout_session=checkout_session,
                transaction=existing_payment,
                metadata=metadata,
            )
            needs_commit = True
        if checkout_session:
            _ensure_checkout_session_succeeded(checkout_session, payment_object=payment_object)
            db.add(checkout_session)
            needs_commit = True
        if needs_commit:
            db.commit()
        logger.info("billing.webhook_duplicate_payment", payment_id=payment_id, user_id=str(user.id))
        return

    amount_numeric = Decimal(str(amount_val))
    trx = Transaction(
        user_id=user.id,
        amount=amount_numeric,
        currency=currency,
        type="payment",
        status="success",
        provider_id=payment_id,
    )
    db.add(trx)
    db.flush()

    # 2. Update Subscription OR Add Credits OR Grant Report Unlock
    product_type = normalize_product_code(metadata.get("product_type")) or "subscription"

    if billing_kind == BillingKind.CREDITS.value:
        # Add Credit Transaction
        # Amount logic: if 199rub -> 1 credit? 
        # For MVP, assume 1 payment = 1 credit (simplification)
        # Or parse description? 
        # Ideally metadata has 'credits_amount'.
        credits_qty = int(metadata.get("credits_qty", 1))
        
        existing_credit = db.query(Transaction).filter(
            Transaction.type == "credit_topup",
            Transaction.provider_id == payment_id,
        ).first()
        if not existing_credit:
            credit_trx = Transaction(
                user_id=user.id,
                amount=credits_qty,
                currency="CRD",
                type="credit_topup",
                status="success",
                provider_id=payment_id,
            )
            db.add(credit_trx)
        logger.info("billing.credits_added", user_id=str(user.id), qty=credits_qty)

    elif (
        billing_kind == BillingKind.REPORT_UNLOCK.value
        and is_one_off_entitlements_runtime_enabled()
    ):
        entitlement = _ensure_report_unlock_entitlement(
            db,
            user=user,
            checkout_session=checkout_session,
            transaction=trx,
            metadata=metadata,
        )
        logger.info(
            "billing.report_unlock_granted",
            user_id=str(user.id),
            report_type=entitlement.report_type if entitlement else None,
            checkout_session_id=str(checkout_session.id) if checkout_session else None,
        )

    else:
        # Default: Subscription Extension
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if not sub:
            sub = Subscription(user_id=user.id)
            db.add(sub)
        
        sub.status = "active"
        if is_recurring and saved and payment_method_id:
            sub.payment_method_id = payment_method_id

        # 3. Grant Access (+30 days)
        now = datetime.now(timezone.utc)
        current_end = user.subscription_active_until
        
        if current_end and current_end.tzinfo is None:
             current_end = current_end.replace(tzinfo=timezone.utc)

        if current_end and current_end > now:
            user.subscription_active_until = current_end + timedelta(days=30)
        else:
            user.subscription_active_until = now + timedelta(days=30)
        
        # Set next billing date for cron
        sub.next_billing_at = user.subscription_active_until

    # Check Referrer Bonus (CPA/RevShare logic hook)
    from .referral_service import process_partner_reward
    process_partner_reward(user.id, float(amount_numeric), db)

    if checkout_session:
        _ensure_checkout_session_succeeded(checkout_session, payment_object=payment_object)
        db.add(checkout_session)

    db.commit()
    logger.info("billing.success", user_id=str(user.id), amount=amount_val)
    log_analytics_event(
        db,
        "payment_success",
        user_id=user.id,
        telegram_id=user.telegram_id,
        source="billing",
        metadata={
            "amount": amount_val,
            "currency": currency,
            "payment_id": payment_id,
        },
    )
# #END_BLOCK_WEBHOOK_HANDLER


def handle_payment_canceled(payment_object: dict, db: Session):
    metadata = payment_object.get("metadata", {})
    checkout_session = _resolve_checkout_session_from_metadata(metadata, db)
    if not checkout_session:
        return

    if checkout_session.status == CheckoutSessionStatus.CANCELED.value:
        return

    cancellation_details = payment_object.get("cancellation_details") or {}
    _update_checkout_session_status(
        checkout_session,
        status=CheckoutSessionStatus.CANCELED.value,
        provider_payment_id=payment_object.get("id"),
        provider_status=payment_object.get("status"),
        error_code="payment_canceled",
        error_message=cancellation_details.get("reason"),
    )
    db.add(checkout_session)
    db.commit()
