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
from ..models import BillingCheckoutSession, User
from ..catalog_logging import (
    log_bridge_resume_start,
    log_bridge_resume_success,
    log_catalog_surface_error,
    log_checkout_decision,
    log_checkout_denied,
    log_checkout_error,
    log_checkout_payment_created,
    log_checkout_resume_ready,
    log_checkout_start,
    log_checkout_status,
    log_checkout_success,
    log_resume_token_denied,
)
from ..logging_utils import hash_identifier
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


def log_catalog_event(event: str, **fields: Any) -> None:
    logger.info(event, **fields)

class CreatePaymentRequest(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    is_recurring: bool = False
    product_type: Optional[str] = None
    pack_id: Optional[str] = None
    return_path: Optional[str] = None
    draft_payload: Optional[dict[str, Any]] = None
    consent_flow: Optional[str] = None
    consent_accepted: Optional[bool] = None
    legal_versions: Optional[dict[str, str]] = None

    @validator("product_type", pre=True)
    @classmethod
    def normalize_product_type(cls, value: Optional[str]) -> Optional[str]:
        return normalize_product_code(value)

@router.post("/pay")
def initiate_payment(
    payload: CreatePaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    surface = "billing"
    checkout_session = None
    logged_error = False
    try:
        final_amount = payload.amount
        final_desc = payload.description
        metadata: dict[str, Any] = {
            "consent_flow": payload.consent_flow or "create_checkout",
            "consent_accepted": bool(payload.consent_accepted),
        }
        billing_kind = BillingKind.SUBSCRIPTION.value
        product_code = payload.product_type or payload.pack_id or "custom"
        report_type: Optional[str] = None
        pack_id = payload.pack_id

        if payload.pack_id:
            if payload.pack_id not in HORARY_PACKS:
                log_checkout_denied(
                    surface=surface,
                    user=user,
                    report_type="credits",
                    reason="invalid_pack",
                )
                raise HTTPException(status_code=400, detail="Invalid pack_id")

            pack = HORARY_PACKS[payload.pack_id]
            final_amount = pack["price"]
            final_desc = f"Пакет хораров: {pack['label']}"
            metadata.update(
                {
                    "product_type": "credits",
                    "credits_qty": str(pack["credits"]),
                    "pack_id": payload.pack_id,
                }
            )
            billing_kind = BillingKind.CREDITS.value
            product_code = payload.pack_id

        elif payload.product_type:
            metadata["product_type"] = payload.product_type
            resolved_product = resolve_catalog_product(payload.product_type)

            if payload.product_type == "subscription":
                final_amount = SUBSCRIPTION_PRICE
                final_desc = "Подписка AstroSaaS (1 месяц)"
                payload.is_recurring = True
                billing_kind = BillingKind.SUBSCRIPTION.value
                product_code = "subscription"
                report_type = "week_forecast"
            elif payload.product_type in REPORT_PRICES:
                final_amount = REPORT_PRICES[payload.product_type]
                final_desc = f"Астрологический отчет: {payload.product_type}"
                product_code = payload.product_type
                if resolved_product:
                    billing_kind = resolved_product.billing_kind.value
                    report_type = resolved_product.report_type
            else:
                log_checkout_denied(
                    surface=surface,
                    user=user,
                    report_type=payload.product_type,
                    reason="unknown_product_type",
                )
                raise HTTPException(status_code=400, detail="Unknown product_type")

        if not final_amount:
            log_checkout_denied(
                surface=surface,
                user=user,
                report_type=payload.product_type,
                reason="amount_missing",
            )
            raise HTTPException(status_code=400, detail="Amount or product_type required")

        metadata["billing_kind"] = billing_kind
        metadata["product_code"] = product_code
        if report_type:
            metadata["report_type"] = report_type

        pm = os.getenv("PAYMENTS_MODE", "real")
        persistent_sessions_enabled = use_persistent_checkout_sessions()
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
            if payload.legal_versions:
                metadata["legal_versions"] = payload.legal_versions
            metadata["checkout_session_id"] = str(checkout_session.id)

        checkout_token_hash = (
            hash_identifier(checkout_session.resume_token)
            if checkout_session
            else None
        )
        log_checkout_start(
            surface=surface,
            user=user,
            report_type=report_type,
            product_code=product_code,
            amount=final_amount,
            pack_id=pack_id,
            billing_kind=billing_kind,
            checkout_token_hash=checkout_token_hash,
            checkout_session=checkout_session,
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
                    **metadata,
                },
                "payment_method": {
                    "id": "mock_method",
                    "type": "bank_card",
                    "saved": False,
                },
            }
            logger.info(
                "billing.mock_payment",
                user_id=str(user.id),
                amount=final_amount,
                product=payload.product_type or payload.pack_id,
            )
            handle_payment_succeeded(payment_object, db)
            response = {"status": "success", "url": None, "mock": True}
            if checkout_session:
                db.refresh(checkout_session)
                response["checkout_token"] = checkout_session.resume_token
                response["session_status"] = checkout_session.status
                log_checkout_success(
                    surface=surface,
                    user=user,
                    checkout_session=checkout_session,
                    provider="mock",
                    payment_id=mock_id,
                )
            else:
                log_checkout_success(
                    surface=surface,
                    user=user,
                    provider="mock",
                    payment_id=mock_id,
                )
            return response

        try:
            payment_data = create_payment(
                user_id=user.id,
                amount=final_amount,
                description=final_desc or "Оплата услуг AstroSaaS",
                is_recurring=payload.is_recurring,
                metadata=metadata,
                return_url=build_checkout_return_url(checkout_session.resume_token)
                if checkout_session
                else None,
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
                log_checkout_error(
                    surface=surface,
                    user=user,
                    checkout_session=checkout_session,
                    error="create_payment_failed",
                    error_detail=str(exc),
                    status_code=500,
                )
                log_checkout_status(
                    checkout_session,
                    surface=surface,
                    user=user,
                    status=checkout_session.status,
                    failed=True,
                )
            else:
                log_checkout_error(
                    surface=surface,
                    user=user,
                    error="create_payment_failed",
                    error_detail=str(exc),
                    status_code=500,
                )
            logged_error = True
            raise

        payment_data_obj = json.loads(payment_data)
        if checkout_session:
            mark_checkout_session_pending(db, checkout_session, payment_data_obj)
        log_checkout_payment_created(
            checkout_session,
            surface=surface,
            user=user,
            amount=final_amount,
            provider_payment_id=payment_data_obj.get("id"),
            provider_status=payment_data_obj.get("status"),
            confirmation_type=payment_data_obj.get("confirmation", {}).get("type"),
            billing_kind=billing_kind,
            product_code=product_code,
            report_type=report_type,
        )

        confirmation_url = payment_data_obj["confirmation"]["confirmation_url"]
        response = {"url": confirmation_url}
        if checkout_session:
            response["checkout_token"] = checkout_session.resume_token
            response["session_status"] = checkout_session.status
            log_checkout_status(
                checkout_session,
                surface=surface,
                user=user,
                status=checkout_session.status,
                pending=True,
            )
        return response
    except HTTPException:
        raise
    except Exception as exc:
        if not logged_error:
            log_checkout_error(
                surface=surface,
                user=user,
                checkout_session=checkout_session,
                error="initiate_payment_failed",
                error_detail=str(exc),
                status_code=500,
            )
        raise HTTPException(status_code=500, detail=str(exc))


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
    log_checkout_status(
        checkout_session,
        surface="billing",
        user=user,
        status=checkout_session.status,
        source="get_checkout_session_status",
    )
    if checkout_session.status in {CheckoutSessionStatus.SUCCEEDED.value, CheckoutSessionStatus.RESUMED.value}:
        log_checkout_resume_ready(
            checkout_session,
            user=user,
            ready_status=checkout_session.status,
        )
        log_catalog_event("catalog.checkout_resume_ready")
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
        log_resume_token_denied(user=user, resume_token=resume_token, reason="resume_disabled")
        raise HTTPException(status_code=404, detail="Checkout resume is unavailable")

    if not is_one_off_entitlements_runtime_enabled():
        log_resume_token_denied(user=user, resume_token=resume_token, reason="one_off_runtime_disabled")
        raise HTTPException(status_code=404, detail="Checkout resume is unavailable")

    checkout_session = get_checkout_session_by_token(db, resume_token, user_id=user.id)
    if not checkout_session:
        log_resume_token_denied(user=user, resume_token=resume_token, reason="resume_session_not_found")
        raise HTTPException(status_code=404, detail="Checkout session not found")

    if checkout_session.resumed_report_id:
        log_bridge_resume_success(
            checkout_session,
            user=user,
            resumed_report_id=str(checkout_session.resumed_report_id),
            repeat=True,
        )
        return {
            "report_id": str(checkout_session.resumed_report_id),
            "status": CheckoutSessionStatus.RESUMED.value,
            "checkout_session": serialize_checkout_session(checkout_session),
        }

    if checkout_session.billing_kind != BillingKind.REPORT_UNLOCK.value:
        log_checkout_denied(
            surface="billing",
            user=user,
            checkout_session=checkout_session,
            reason="resume_not_supported",
        )
        raise HTTPException(status_code=409, detail="Checkout session does not support resume")

    if checkout_session.status not in {
        CheckoutSessionStatus.SUCCEEDED.value,
        CheckoutSessionStatus.RESUMED.value,
    }:
        log_checkout_status(
            checkout_session,
            user=user,
            status=checkout_session.status,
            resume_blocked=True,
        )
        raise HTTPException(
            status_code=409,
            detail=f"Checkout session is not ready for resume: {checkout_session.status}",
        )

    if checkout_session.entitlement_id is None:
        log_checkout_status(
            checkout_session,
            user=user,
            status=checkout_session.status,
            resume_blocked=True,
            reason="entitlement_pending",
        )
        raise HTTPException(
            status_code=409,
            detail="Checkout entitlement is not ready yet",
        )

    payload_data = _load_checkout_resume_payload(checkout_session)
    log_bridge_resume_start(checkout_session, user=user)

    # Local import avoids a startup circular dependency with `backend.app.main`.
    from ..main import B2CReportCreateRequest, create_b2c_report

    response = create_b2c_report(
        B2CReportCreateRequest.model_validate(payload_data),
        background_tasks=background_tasks,
        user=user,
        db=db,
    )
    db.refresh(checkout_session)
    log_bridge_resume_success(
        checkout_session,
        user=user,
        resumed_report_id=response.get("report_id"),
    )
    return {
        **response,
        "checkout_session": serialize_checkout_session(checkout_session),
    }


@router.post("/webhook")
async def yookassa_webhook(request: Request, db: Session = Depends(get_db)):
    surface = "billing_webhook"
    try:
        event_json = await request.json()
    except json.JSONDecodeError:
        log_catalog_surface_error(surface=surface, error="invalid_json", status_code=400)
        return {"status": "error", "reason": "invalid_json"}

    event_type = event_json.get("event")
    object_data = event_json.get("object") or {}
    metadata = object_data.get("metadata") or {}
    base_fields = _webhook_log_fields(object_data, metadata)

    log_checkout_status(
        None,
        surface=surface,
        webhook_event=event_type,
        **base_fields,
    )

    try:
        if event_type == "payment.succeeded":
            handle_payment_succeeded(object_data, db)
            checkout_session = _get_checkout_session_from_metadata(db, metadata)
            user_ctx = _get_webhook_user(db, metadata, checkout_session)
            log_checkout_success(
                surface=surface,
                user=user_ctx,
                checkout_session=checkout_session,
                webhook_event=event_type,
                **base_fields,
            )
        elif event_type == "payment.canceled":
            handle_payment_canceled(object_data, db)
            checkout_session = _get_checkout_session_from_metadata(db, metadata)
            user_ctx = _get_webhook_user(db, metadata, checkout_session)
            cancellation_reason = (object_data.get("cancellation_details") or {}).get("reason")
            log_checkout_denied(
                surface=surface,
                user=user_ctx,
                checkout_session=checkout_session,
                reason=cancellation_reason or "payment_canceled",
                webhook_event=event_type,
                **base_fields,
            )
        else:
            logger.info("billing.webhook_unhandled_event", webhook_event=event_type)
    except Exception as exc:
        checkout_session = _get_checkout_session_from_metadata(db, metadata)
        user_ctx = _get_webhook_user(db, metadata, checkout_session)
        log_catalog_surface_error(
            surface=surface,
            user=user_ctx,
            checkout_session=checkout_session,
            error="webhook_handler_failed",
            error_detail=str(exc),
            webhook_event=event_type,
            **base_fields,
        )
        raise

    return {"status": "ok"}


def _get_checkout_session_from_metadata(db: Session, metadata: dict[str, Any]) -> BillingCheckoutSession | None:
    checkout_session_id = metadata.get("checkout_session_id")
    if not checkout_session_id:
        return None
    try:
        checkout_session_uuid = uuid.UUID(checkout_session_id)
    except ValueError:
        logger.warning("billing.webhook_bad_checkout_session_uuid", checkout_session_id=checkout_session_id)
        return None
    return (
        db.query(BillingCheckoutSession)
        .filter(BillingCheckoutSession.id == checkout_session_uuid)
        .first()
    )


def _get_webhook_user(
    db: Session,
    metadata: dict[str, Any],
    checkout_session: BillingCheckoutSession | None,
) -> User | None:
    user_id = metadata.get("user_id")
    if not user_id and checkout_session:
        user_id = str(checkout_session.user_id)
    if not user_id:
        return None
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        logger.warning("billing.webhook_bad_user_uuid", user_id=user_id)
        return None
    return db.query(User).filter(User.id == user_uuid).first()


def _webhook_log_fields(object_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    amount_payload = object_data.get("amount") or {}
    fields = {
        "provider_payment_id": object_data.get("id"),
        "provider_status": object_data.get("status"),
        "billing_kind": metadata.get("billing_kind"),
        "product_code": metadata.get("product_code") or metadata.get("product_type"),
        "report_type": metadata.get("report_type"),
        "checkout_session_id": metadata.get("checkout_session_id"),
        "user_id": metadata.get("user_id"),
        "amount_value": amount_payload.get("value"),
        "amount_currency": amount_payload.get("currency"),
    }
    return {key: value for key, value in fields.items() if value is not None}
