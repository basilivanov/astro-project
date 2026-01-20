# ############################################################################
# AI_HEADER: MODULE_BILLING_SERVICE
# ROLE: YooKassa integration logic.
# DEPENDENCIES: yookassa, sqlalchemy, backend.app.models.
# GRACE_ANCHORS: [BILLING_CONFIG, CREATE_PAYMENT, WEBHOOK_HANDLER]
# ############################################################################

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from yookassa import Configuration, Payment
from sqlalchemy.orm import Session

from ..models import User, Subscription, Transaction

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


# #START_BLOCK_CREATE_PAYMENT
def create_payment(user_id: uuid.UUID, amount: float, description: str, is_recurring: bool = False) -> str:
    """
    # PURPOSE: Create a payment intent in YooKassa.
    # INPUT: user_id, amount, desc, recurring flag.
    # OUTPUT: JSON string with confirmation URL.
    """
    if not SHOP_ID:
        raise ValueError("Billing not configured")

    idempotence_key = str(uuid.uuid4())
    
    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": os.getenv("WEBAPP_URL", "https://t.me/AstroGraceBot")
        },
        "description": description,
        "metadata": {
            "user_id": str(user_id),
            "is_recurring": str(is_recurring)
        },
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
    user_id_str = metadata.get("user_id")
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

    # 1. Log Transaction
    trx = Transaction(
        user_id=user.id,
        amount=amount_val,
        currency=currency,
        type="payment",
        status="success",
        provider_id=payment_object.get("id")
    )
    db.add(trx)

    # 2. Update Subscription
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
        if sub.next_billing_at:
             # If strictly recurring, usually syncs with access end, 
             # but let's keep it simple: next bill is also extended.
             # Actually, logic dictates next billing date.
             pass
    else:
        user.subscription_active_until = now + timedelta(days=30)
    
    # Set next billing date for cron
    sub.next_billing_at = user.subscription_active_until

    # Check Referrer Bonus (CPA/RevShare logic hook)
    # If user has a referrer, maybe mark referral as "converted"?
    # TODO: Implement CPA Logic later.

    db.commit()
    logger.info("billing.success", user_id=str(user.id), amount=amount_val)
# #END_BLOCK_WEBHOOK_HANDLER