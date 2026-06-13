"""
Campaign service — handles campaign launch and channel service integration.

Orchestrates the full launch flow:
1. Resolve segment → get matching customers
2. Create Communication records for each customer
3. POST recipients + message to the channel service
4. Update campaign status to 'sending' → 'completed'
"""

import logging
from datetime import datetime

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import Campaign
from app.models.communication import Communication
from app.models.segment import Segment
from app.services.segment_service import get_segment_customers

logger = logging.getLogger(__name__)


async def launch_campaign(db: AsyncSession, campaign_id: int) -> dict:
    """
    Launch a campaign by sending messages to all segment customers.

    Steps:
        1. Load campaign + segment
        2. Fetch matching customers
        3. Create Communication records (status='sent')
        4. POST to channel service
        5. Update campaign status

    Returns:
        Summary dict with audience_size and campaign status.

    Raises:
        ValueError: If campaign is not in 'draft' status.
    """
    # Load campaign with its segment.
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found.")

    if campaign.status != "draft":
        raise ValueError(
            f"Campaign {campaign_id} is already '{campaign.status}'. "
            "Only draft campaigns can be launched."
        )

    # Load segment.
    seg_result = await db.execute(select(Segment).where(Segment.id == campaign.segment_id))
    segment = seg_result.scalar_one_or_none()

    if not segment:
        raise ValueError(f"Segment {campaign.segment_id} not found.")

    # Fetch all matching customers.
    filter_rules = segment.filter_rules
    if isinstance(filter_rules, dict):
        filter_rules = [filter_rules]
    customers = await get_segment_customers(db, filter_rules)

    if not customers:
        raise ValueError("No customers match this segment. Cannot launch.")

    # Update campaign status to 'sending'.
    campaign.status = "sending"
    await db.flush()

    # Create Communication records for each customer.
    communications = []
    recipients = []
    for customer in customers:
        # Personalise the message by replacing {name} placeholder.
        personalised_message = campaign.message_template.replace(
            "{name}", customer.name
        )
        comm = Communication(
            campaign_id=campaign.id,
            customer_id=customer.id,
            channel=campaign.channel,
            message=personalised_message,
            status="sent",
        )
        db.add(comm)
        communications.append(comm)

    # Flush to assign communication IDs.
    await db.flush()

    # Build the payload for the channel service.
    for comm, customer in zip(communications, customers):
        recipients.append({
            "communication_id": comm.id,
            "customer_name": customer.name,
            "customer_email": customer.email,
            "customer_phone": customer.phone,
            "message": comm.message,
        })

    # POST to channel service (fire-and-forget style — don't block on delivery).
    channel_payload = {
        "campaign_id": campaign.id,
        "channel": campaign.channel,
        "callback_url": f"{settings.CRM_CALLBACK_URL}/api/receipts",
        "recipients": recipients,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.CHANNEL_SERVICE_URL}/send",
                json=channel_payload,
            )
            response.raise_for_status()
    
            logger.info(
                "Channel service accepted campaign %d with %d recipients.",
                campaign.id, len(recipients),
            )
    except httpx.HTTPError as exc:
        logger.error(
            "Failed to reach channel service for campaign %d: %s",
            campaign.id, str(exc),
        )
        campaign.status = "failed"
        await db.commit()

        return {
            "campaign_id": campaign.id,
            "status": "failed",
            "audience_size": len(customers),
            "message": f"Campaign launch failed: {str(exc)}",
        }
        

    await db.commit()

    return {
        "campaign_id": campaign.id,
        "status": campaign.status,
        "audience_size": len(customers),
        "message": f"Campaign launched to {len(customers)} customers.",
    }


async def get_campaign_stats(db: AsyncSession, campaign_id: int) -> dict:
    """
    Compute live delivery stats for a campaign by aggregating
    Communication statuses.
    """
    result = await db.execute(
        select(
            Communication.status,
            func.count(Communication.id),
        )
        .where(Communication.campaign_id == campaign_id)
        .group_by(Communication.status)
    )

    stats = {
        "total_sent": 0,
        "delivered": 0,
        "failed": 0,
        "opened": 0,
        "clicked": 0,
    }

    for status, count in result.all():
        if status == "sent":
            stats["total_sent"] += count
        elif status == "delivered":
            stats["delivered"] += count
            stats["total_sent"] += count
        elif status == "failed":
            stats["failed"] += count
            stats["total_sent"] += count
        elif status == "opened":
            stats["opened"] += count
            stats["delivered"] += count
            stats["total_sent"] += count
        elif status in ("read", "clicked"):
            stats["clicked"] += count
            stats["opened"] += count
            stats["delivered"] += count
            stats["total_sent"] += count

    return stats
