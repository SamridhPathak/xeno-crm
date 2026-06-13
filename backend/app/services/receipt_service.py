"""
Receipt service — processes delivery event callbacks from the channel service.

Updates Communication status and creates CampaignEvent audit records.
Handles both single and bulk receipt processing.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.communication import Communication
from app.models.event import CampaignEvent

logger = logging.getLogger(__name__)

# Status progression order — we only move forward, never backward.
STATUS_ORDER = {
    "sent": 0,
    "delivered": 1,
    "failed": 1,  # Same level as delivered (terminal for failures).
    "opened": 2,
    "read": 3,
    "clicked": 4,
}


async def process_receipt(
    db: AsyncSession,
    communication_id: int,
    event_type: str,
    timestamp: datetime | None = None,
) -> bool:
    """
    Process a single delivery receipt.

    Updates the Communication status if the event represents forward
    progress, and creates an immutable CampaignEvent audit record.

    Args:
        db: Async database session.
        communication_id: ID of the communication to update.
        event_type: The delivery event (delivered, failed, opened, etc.).
        timestamp: When the event occurred (defaults to now).

    Returns:
        True if the receipt was processed, False if skipped (e.g. duplicate).
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    # Fetch the communication record.
    result = await db.execute(
        select(Communication).where(Communication.id == communication_id)
    )
    comm = result.scalar_one_or_none()

    if not comm:
        logger.warning("Receipt for unknown communication ID %d — skipping.", communication_id)
        return False

    # Always create the audit event (immutable log).
    event = CampaignEvent(
        communication_id=communication_id,
        event_type=event_type,
        timestamp=timestamp,
    )
    db.add(event)

    # Only update status if the new event is "ahead" of the current status.
    current_order = STATUS_ORDER.get(comm.status, 0)
    new_order = STATUS_ORDER.get(event_type, 0)

    if new_order > current_order:
        old_status = comm.status
        comm.status = event_type
        logger.info(
            "Communication %d status updated: %s → %s",
            communication_id,
            old_status,
            event_type,
        )
    elif event_type == "failed" and comm.status == "sent":
        # Failed is a special case — it replaces 'sent' but not delivered/opened.
        comm.status = "failed"
        logger.info("Communication %d marked as failed.", communication_id)
    else:
        logger.debug(
            "Communication %d: event '%s' ignored (current status '%s').",
            communication_id, event_type, comm.status,
        )

    # Check if campaign can be marked completed.
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == comm.campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()

    if campaign and campaign.status == "sending":

        total_result = await db.execute(
            select(func.count(Communication.id))
            .where(Communication.campaign_id == campaign.id)
        )
        total_comms = total_result.scalar_one()

        pending_result = await db.execute(
            select(func.count(Communication.id))
            .where(
                Communication.campaign_id == campaign.id,
                Communication.status == "sent",
            )
        )
        pending_comms = pending_result.scalar_one()

        if pending_comms == 0:
            campaign.status = "completed"

            logger.info(
                "Campaign %d marked as completed.",
                campaign.id,
            )

    return True