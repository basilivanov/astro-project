# ############################################################################
# AI_HEADER: MODULE_ROUTER_BILLING
# ROLE: API endpoints for payments.
# DEPENDENCIES: fastapi, backend.app.services.billing
# GRACE_ANCHORS: [BILLING_ENDPOINTS]
# ############################################################################

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
import structlog

from ..auth import get_current_user
from ..db import get_db
from ..models import User
from ..services.billing import create_payment, handle_payment_succeeded

logger = structlog.get_logger()
router = APIRouter(prefix="/api/billing", tags=["billing"])

class CreatePaymentRequest(BaseModel):
    amount: float
    description: str
    is_recurring: bool = False

@router.post("/pay")
def initiate_payment(
    payload: CreatePaymentRequest,
    user: User = Depends(get_current_user)
):
    try:
        payment_data = create_payment(
            user_id=user.id,
            amount=payload.amount,
            description=payload.description,
            is_recurring=payload.is_recurring
        )
        # return confirmation_url directly for frontend redirect
        confirmation_url = json.loads(payment_data)["confirmation"]["confirmation_url"]
        return {"url": confirmation_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def yookassa_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        event_json = await request.json()
    except json.JSONDecodeError:
        return {"status": "error", "reason": "invalid_json"}

    event_type = event_json.get("event")
    object_data = event_json.get("object", {})

    logger.info("billing.webhook_received", event=event_type)

    if event_type == "payment.succeeded":
        handle_payment_succeeded(object_data, db)
    
    # We can handle canceled too if needed

    return {"status": "ok"}
