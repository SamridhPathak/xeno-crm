"""
Campaign API routes.

Endpoints:
    GET  /api/campaigns             — List all campaigns
    POST /api/campaigns             — Create a new campaign (draft)
    GET  /api/campaigns/{id}        — Get campaign detail with live stats
    POST /api/campaigns/{id}/launch — Launch a campaign to the channel service
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.campaign import Campaign
from app.models.segment import Segment
from app.schemas.campaign import (
    CampaignCreate,
    CampaignDetailResponse,
    CampaignListResponse,
    CampaignResponse,
)
from app.services.campaign_service import get_campaign_stats, launch_campaign

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


# ─────────────────────────────────────────────────────────────────
# GET /api/campaigns — list all campaigns
# ─────────────────────────────────────────────────────────────────


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
) -> CampaignListResponse:
    """List all campaigns, newest first."""
    result = await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()

    return CampaignListResponse(
        campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
        total=len(campaigns),
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/campaigns — create a new draft campaign
# ─────────────────────────────────────────────────────────────────


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """
    Create a new campaign in 'draft' status.

    Validates that the referenced segment exists before creation.
    The campaign must be explicitly launched via the /launch endpoint.
    """
    # Verify segment exists.
    seg_result = await db.execute(
        select(Segment).where(Segment.id == payload.segment_id)
    )
    segment = seg_result.scalar_one_or_none()

    if not segment:
        raise HTTPException(
            status_code=404,
            detail=f"Segment {payload.segment_id} not found.",
        )

    # Validate channel.
    valid_channels = {"sms", "email", "whatsapp"}
    if payload.channel not in valid_channels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel '{payload.channel}'. Must be one of: {', '.join(valid_channels)}.",
        )

    campaign = Campaign(
        name=payload.name,
        segment_id=payload.segment_id,
        message_template=payload.message_template,
        channel=payload.channel,
        status="draft",
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)

    logger.info("Campaign '%s' created (draft) targeting segment %d.", campaign.name, segment.id)

    return CampaignResponse.model_validate(campaign)


# ─────────────────────────────────────────────────────────────────
# GET /api/campaigns/{id} — campaign detail with live stats
# ─────────────────────────────────────────────────────────────────


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
) -> CampaignDetailResponse:
    """
    Get a campaign's details including live delivery stats.

    Stats are computed in real-time from Communication records,
    so they reflect the latest channel service callbacks.
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found.")

    # Load segment name.
    seg_result = await db.execute(select(Segment.name).where(Segment.id == campaign.segment_id))
    segment_name = seg_result.scalar_one_or_none()

    # Compute live stats.
    stats = await get_campaign_stats(db, campaign_id)

    return CampaignDetailResponse(
        **CampaignResponse.model_validate(campaign).model_dump(),
        segment_name=segment_name,
        total_sent=stats["total_sent"],
        delivered=stats["delivered"],
        failed=stats["failed"],
        opened=stats["opened"],
        clicked=stats["clicked"],
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/campaigns/{id}/launch — launch a draft campaign
# ─────────────────────────────────────────────────────────────────


@router.post("/{campaign_id}/launch", response_model=dict)
async def launch_campaign_endpoint(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Launch a draft campaign.

    This triggers the full send flow:
    1. Resolve segment → customers
    2. Create Communication records
    3. POST to channel service
    4. Channel service fires callbacks asynchronously
    """
    try:
        result = await launch_campaign(db, campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result
