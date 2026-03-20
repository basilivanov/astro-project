# ############################################################################
# AI_HEADER: MODULE_ROUTER_BILLING
# ROLE: API endpoints for payments.
# DEPENDENCIES: fastapi, backend.app.services.billing
# GRACE_ANCHORS: [BILLING_ENDPOINTS]
# ############################################################################

import json
import os
import uuid
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Request, HTTPException, Header
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
import structlog

from ..auth import get_current_user
from ..core.feature_flags import (
    is_one_off_entitlements_runtime_enabled,
    use_persistent_checkout_sessions,
)
from ..db import get_db
from ..models import User
from ..services.billing import (
    build_checkout_return_url,
    create_checkout_session,
    create_payment,
    get_checkout_session_by_token,
    handle_payment_canceled,
    handle_payment_succeeded,
    mark_checkout_session_failed,
    mark_checkout_session_pending,
    serialize_checkout_session,
)
from ..core.config_business import HORARY_PACKS, SUBSCRIPTION_PRICE, REPORT_PRICES
from ..services.one_off_entitlements import (
    BillingKind,
    CheckoutSessionStatus,
    normalize_product_code,
    resolve_catalog_product,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/billing", tags=["billing"])

class CreatePaymentRequest(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    is_recurring: bool = False
    product_type: Optional[str] = None
    pack_id: Optional[str] = None
    return_path: Optional[str] = None
    draft_payload: Optional[dict[str, Any]] = None

    @validator("product_type", pre=True)
    @classmethod
    def normalize_product_type(cls, value: Optional[str]) -> Optional[str]:
        return normalize_product_code(value)

@router.post("/pay")
def initiate_payment(
    payload: CreatePaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        final_amount = payload.amount
        final_desc = payload.description
        metadata = {}
        billing_kind = BillingKind.SUBSCRIPTION.value
        product_code = payload.product_type or payload.pack_id or "custom"
        report_type = None
        pack_id = payload.pack_id
        
        # 1. Resolve Package (Horary Credits)
        if payload.pack_id:
            if payload.pack_id not in HORARY_PACKS:
                raise HTTPException(status_code=400, detail="Invalid pack_id")
            
            pack = HORARY_PACKS[payload.pack_id]
            final_amount = pack["price"]
            final_desc = f"Пакет хораров: {pack['label']}"
            metadata["product_type"] = "credits"
            metadata["credits_qty"] = str(pack["credits"])
            metadata["pack_id"] = payload.pack_id
            billing_kind = BillingKind.CREDITS.value
            product_code = payload.pack_id
            
        # 2. Resolve Single Report or Subscription
        elif payload.product_type:
            metadata["product_type"] = payload.product_type
            resolved_product = resolve_catalog_product(payload.product_type)
            
            if payload.product_type == "subscription":
                 final_amount = SUBSCRIPTION_PRICE
                 final_desc = "Подписка AstroSaaS (1 месяц)"
                 payload.is_recurring = True # Force recurring for subscription
                 billing_kind = BillingKind.SUBSCRIPTION.value
                 product_code = "subscription"
                 report_type = "week_forecast"
            
            elif payload.product_type in REPORT_PRICES:
                 final_amount = REPORT_PRICES[payload.product_type]
                 # Get human-readable name if possible, or just the type
                 final_desc = f"Астрологический отчет: {payload.product_type}"
                 product_code = payload.product_type
                 if resolved_product:
                     billing_kind = resolved_product.billing_kind.value
                     report_type = resolved_product.report_type
            
            else:
                 raise HTTPException(status_code=400, detail="Unknown product_type")

        if not final_amount:
             raise HTTPException(status_code=400, detail="Amount or product_type required")

        metadata["billing_kind"] = billing_kind
        metadata["product_code"] = product_code
        if report_type:
            metadata["report_type"] = report_type

        # MOCK MODE
        pm = os.getenv("PAYMENTS_MODE", "real")
        persistent_sessions_enabled = use_persistent_checkout_sessions()
        checkout_session = None
        if persistent_sessions_enabled:
            checkout_session = create_checkout_session(
                db,
                user_id=user.id,
                provider="mock" if pm == "mock" else "yookassa",
                billing_kind=billing_kind,
                product_code=product_code,
                report_type=report_type,
                pack_id=pack_id,
                amount=final_amount,
                return_path=payload.return_path,
                draft_payload=payload.draft_payload,
            )
            metadata.update(
                {
                    "checkout_session_id": str(checkout_session.id),
                }
            )

        logger.info("billing.pay_request", mode=pm, user_id=str(user.id))
        if pm == "mock":
            mock_id = f"mock_{uuid.uuid4().hex[:8]}"
            payment_object = {
                "id": mock_id,
                "status": "succeeded",
                "amount": {"value": str(final_amount), "currency": "RUB"},
                "metadata": {
                    "user_id": str(user.id),
                    "is_recurring": str(payload.is_recurring),
                    "mock": "true",
                    **metadata
                },
                "payment_method": {"id": "mock_method", "type": "bank_card", "saved": False}
            }
            logger.info("billing.mock_payment", user_id=str(user.id), amount=final_amount, product=payload.product_type or payload.pack_id)
            handle_payment_succeeded(payment_object, db)
            response = {"status": "success", "url": None, "mock": True}
            if checkout_session:
                db.refresh(checkout_session)
                response["checkout_token"] = checkout_session.resume_token
                response["session_status"] = checkout_session.status
            return response

        try:
            payment_data = create_payment(
                user_id=user.id,
                amount=final_amount,
                description=final_desc or "Оплата услуг AstroSaaS",
                is_recurring=payload.is_recurring,
                metadata=metadata,
                return_url=build_checkout_return_url(checkout_session.resume_token) if checkout_session else None,
                idempotence_key=checkout_session.idempotence_key if checkout_session else None,
            )
        except Exception as exc:
            if checkout_session:
                mark_checkout_session_failed(
                    db,
                    checkout_session,
                    error_code="provider_create_failed",
                    error_message=str(exc),
                )
            raise

        payment_data_obj = json.loads(payment_data)
        if checkout_session:
            mark_checkout_session_pending(db, checkout_session, payment_data_obj)
        # return confirmation_url directly for frontend redirect
        confirmation_url = payment_data_obj["confirmation"]["confirmation_url"]
        response = {"url": confirmation_url}
        if checkout_session:
            response["checkout_token"] = checkout_session.resume_token
            response["session_status"] = checkout_session.status
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{resume_token}")
def get_checkout_session_status(
    resume_token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    checkout_session = get_checkout_session_by_token(db, resume_token, user_id=user.id)
    if not checkout_session:
        raise HTTPException(status_code=404, detail="Checkout session not found")
    payload = serialize_checkout_session(checkout_session)
    if checkout_session.draft_payload:
        try:
            draft_payload = json.loads(checkout_session.draft_payload)
        except json.JSONDecodeError:
            draft_payload = None
        if isinstance(draft_payload, dict):
            payload["draft_payload"] = draft_payload
    return payload


def _load_checkout_resume_payload(checkout_session) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if checkout_session.draft_payload:
        try:
            draft_payload = json.loads(checkout_session.draft_payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=409, detail="Checkout draft payload is invalid") from exc

        if not isinstance(draft_payload, dict):
            raise HTTPException(status_code=409, detail="Checkout draft payload must be an object")
        payload.update(draft_payload)

    if checkout_session.report_type:
        payload["report_type"] = checkout_session.report_type

    if not payload.get("report_type"):
        raise HTTPException(status_code=409, detail="Checkout session has no resumable report payload")

    return payload


@router.post("/sessions/{resume_token}/resume")
def resume_checkout_session(
    resume_token: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not use_persistent_checkout_sessions():
        raise HTTPException(status_code=404, detail="Checkout resume is unavailable")

    if not is_one_off_entitlements_runtime_enabled():
        raise HTTPException(status_code=404, detail="Checkout resume is unavailable")

    checkout_session = get_checkout_session_by_token(db, resume_token, user_id=user.id)
    if not checkout_session:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    if checkout_session.resumed_report_id:
        return {
            "report_id": str(checkout_session.resumed_report_id),
            "status": CheckoutSessionStatus.RESUMED.value,
            "checkout_session": serialize_checkout_session(checkout_session),
        }

    if checkout_session.billing_kind != BillingKind.REPORT_UNLOCK.value:
        raise HTTPException(status_code=409, detail="Checkout session does not support resume")

    if checkout_session.status not in {
        CheckoutSessionStatus.SUCCEEDED.value,
        CheckoutSessionStatus.RESUMED.value,
    }:
        raise HTTPException(
            status_code=409,
            detail=f"Checkout session is not ready for resume: {checkout_session.status}",
        )

    if checkout_session.entitlement_id is None:
        raise HTTPException(
            status_code=409,
            detail="Checkout entitlement is not ready yet",
        )

    payload_data = _load_checkout_resume_payload(checkout_session)

    # Local import avoids a startup circular dependency with `backend.app.main`.
    from ..main import B2CReportCreateRequest, create_b2c_report

    response = create_b2c_report(
        B2CReportCreateRequest.model_validate(payload_data),
        background_tasks=background_tasks,
        user=user,
        db=db,
    )
    db.refresh(checkout_session)
    return {
        **response,
        "checkout_session": serialize_checkout_session(checkout_session),
    }


@router.post("/webhook")
async def yookassa_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        event_json = await request.json()
    except json.JSONDecodeError:
        return {"status": "error", "reason": "invalid_json"}

    event_type = event_json.get("event")
    object_data = event_json.get("object", {})

    logger.info("billing.webhook_received", webhook_event=event_type)

    if event_type == "payment.succeeded":
        handle_payment_succeeded(object_data, db)
    elif event_type == "payment.canceled":
        handle_payment_canceled(object_data, db)
    
    # We can handle canceled too if needed

    return {"status": "ok"}
