"""
Analytics API routes.

Endpoints:
    GET /api/analytics/campaign/{id}  — Detailed stats for a single campaign
    GET /api/analytics/overview       — Dashboard-level overview across all campaigns
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.campaign import Campaign
from app.models.communication import Communication
from app.models.customer import Customer
from app.models.segment import Segment
from app.schemas.communication import CampaignAnalytics, OverviewAnalytics
from app.services.campaign_service import get_campaign_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


# ─────────────────────────────────────────────────────────────────
# GET /api/analytics/campaign/{id} — per-campaign analytics
# ─────────────────────────────────────────────────────────────────


@router.get("/campaign/{campaign_id}", response_model=CampaignAnalytics)
async def campaign_analytics(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
) -> CampaignAnalytics:
    """
    Get detailed analytics for a single campaign.

    Computes delivery, open, and click rates in real-time from
    Communication records. Rates are percentages (0-100).
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found.")

    stats = await get_campaign_stats(db, campaign_id)

    # Compute rates (avoid division by zero).
    total = stats["total_sent"]
    delivery_rate = (stats["delivered"] / total * 100) if total > 0 else 0.0
    open_rate = (stats["opened"] / stats["delivered"] * 100) if stats["delivered"] > 0 else 0.0
    click_rate = (stats["clicked"] / stats["opened"] * 100) if stats["opened"] > 0 else 0.0

    return CampaignAnalytics(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        channel=campaign.channel,
        total_sent=total,
        delivered=stats["delivered"],
        failed=stats["failed"],
        opened=stats["opened"],
        clicked=stats["clicked"],
        delivery_rate=round(delivery_rate, 1),
        open_rate=round(open_rate, 1),
        click_rate=round(click_rate, 1),
    )


# ─────────────────────────────────────────────────────────────────
# GET /api/analytics/overview — dashboard overview
# ─────────────────────────────────────────────────────────────────


@router.get("/overview", response_model=OverviewAnalytics)
async def overview_analytics(
    db: AsyncSession = Depends(get_db),
) -> OverviewAnalytics:
    """
    Get dashboard-level analytics aggregated across all campaigns.

    Returns total counts, overall rates, and stats for the 5
    most recent campaigns.
    """
    # Total customers.
    cust_result = await db.execute(select(func.count(Customer.id)))
    total_customers = cust_result.scalar_one()

    # Total segments.
    seg_result = await db.execute(select(func.count(Segment.id)))
    total_segments = seg_result.scalar_one()

    # Total campaigns.
    camp_result = await db.execute(select(func.count(Campaign.id)))
    total_campaigns = camp_result.scalar_one()

    # Total messages sent (all communications).
    msg_result = await db.execute(select(func.count(Communication.id)))
    total_messages_sent = msg_result.scalar_one()

    # Overall aggregated stats across all communications.
    status_result = await db.execute(
        select(Communication.status, func.count(Communication.id))
        .group_by(Communication.status)
    )
    status_counts = dict(status_result.all())

    # Calculate totals by counting statuses that imply delivery/open/click.
    total_delivered = sum(
        status_counts.get(s, 0) for s in ["delivered", "opened", "read", "clicked"]
    )
    total_opened = sum(status_counts.get(s, 0) for s in ["opened", "read", "clicked"])
    total_clicked = status_counts.get("clicked", 0) + status_counts.get("read", 0)

    overall_delivery_rate = (
        (total_delivered / total_messages_sent * 100) if total_messages_sent > 0 else 0.0
    )
    overall_open_rate = (
        (total_opened / total_delivered * 100) if total_delivered > 0 else 0.0
    )
    overall_click_rate = (
        (total_clicked / total_opened * 100) if total_opened > 0 else 0.0
    )

    # Recent campaigns (last 5) with their individual stats.
    recent_result = await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc()).limit(5)
    )
    recent_campaigns_objs = recent_result.scalars().all()

    recent_campaigns = []
    for camp in recent_campaigns_objs:
        stats = await get_campaign_stats(db, camp.id)
        total = stats["total_sent"]
        dr = (stats["delivered"] / total * 100) if total > 0 else 0.0
        opr = (stats["opened"] / stats["delivered"] * 100) if stats["delivered"] > 0 else 0.0
        cr = (stats["clicked"] / stats["opened"] * 100) if stats["opened"] > 0 else 0.0

        recent_campaigns.append(
            CampaignAnalytics(
                campaign_id=camp.id,
                campaign_name=camp.name,
                channel=camp.channel,
                created_at=camp.created_at,
                status=camp.status,
                total_sent=total,
                delivered=stats["delivered"],
                failed=stats["failed"],
                opened=stats["opened"],
                clicked=stats["clicked"],
                delivery_rate=round(dr, 1),
                open_rate=round(opr, 1),
                click_rate=round(cr, 1),
            )
        )

    return OverviewAnalytics(
        total_customers=total_customers,
        total_segments=total_segments,
        total_campaigns=total_campaigns,
        total_messages_sent=total_messages_sent,
        overall_delivery_rate=round(overall_delivery_rate, 1),
        overall_open_rate=round(overall_open_rate, 1),
        overall_click_rate=round(overall_click_rate, 1),
        recent_campaigns=recent_campaigns,
    )
