"""
Receipts API route.

Endpoint:
    POST /api/receipts — Handle delivery event callbacks from the channel service

The channel service fires these callbacks asynchronously as messages
are delivered, opened, and clicked. Each receipt updates the
Communication status and creates an immutable CampaignEvent.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.communication import BulkDeliveryReceipt, DeliveryReceipt
from app.services.receipt_service import process_receipt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/receipts", tags=["Receipts"])


# ─────────────────────────────────────────────────────────────────
# POST /api/receipts — channel service callback
# ─────────────────────────────────────────────────────────────────


@router.post("", status_code=200)
async def receive_receipt(
    payload: DeliveryReceipt | BulkDeliveryReceipt,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Receive delivery event(s) from the channel service.

    Accepts both single receipts and bulk batches. Each receipt
    updates the corresponding Communication record and creates
    an audit event.

    The channel service fires these progressively:
        - 1-3s after send:  80% delivered, 20% failed
        - 5-8s after send:  60% of delivered → opened
        - 10-15s after send: 30% of opened → clicked
    """
    # Normalise single receipt into a list for uniform processing.
    if isinstance(payload, DeliveryReceipt):
        receipts = [payload]
    else:
        receipts = payload.receipts

    processed = 0
    skipped = 0

    for receipt in receipts:
        timestamp = receipt.timestamp or datetime.now(timezone.utc)

        success = await process_receipt(
            db=db,
            communication_id=receipt.communication_id,
            event_type=receipt.event_type,
            timestamp=timestamp,
        )

        if success:
            processed += 1
        else:
            skipped += 1

    await db.commit()

    logger.info("Receipts processed: %d success, %d skipped.", processed, skipped)

    return {
        "processed": processed,
        "skipped": skipped,
        "total": len(receipts),
    }
