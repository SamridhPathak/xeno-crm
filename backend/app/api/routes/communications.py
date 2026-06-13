"""
Communications API routes.

Endpoints:
    GET /api/communications/campaign/{id} — List communications for a campaign
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.campaign import Campaign
from app.models.communication import Communication
from app.models.customer import Customer
from app.schemas.communication import CommunicationListResponse, CommunicationResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/communications", tags=["Communications"])


# ─────────────────────────────────────────────────────────────────
# GET /api/communications/campaign/{id} — per-campaign message log
# ─────────────────────────────────────────────────────────────────


@router.get("/campaign/{campaign_id}", response_model=CommunicationListResponse)
async def list_campaign_communications(
    campaign_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Filter by status (sent, delivered, failed, opened, clicked)."),
    db: AsyncSession = Depends(get_db),
) -> CommunicationListResponse:
    """
    List all communications (individual messages) for a campaign.

    Returns paginated results with customer name and email for
    the message log view. Optionally filter by delivery status.
    """
    # Verify campaign exists.
    camp_result = await db.execute(select(Campaign.id).where(Campaign.id == campaign_id))
    if not camp_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found.")

    # Base query — join Customer for name/email.
    base_filter = Communication.campaign_id == campaign_id
    if status:
        base_filter = base_filter & (Communication.status == status)

    # Count total.
    count_query = select(func.count(Communication.id)).where(base_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch page with customer join.
    offset = (page - 1) * page_size
    query = (
        select(Communication, Customer.name, Customer.email)
        .join(Customer, Communication.customer_id == Customer.id)
        .where(base_filter)
        .order_by(Communication.id)
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.all()

    communications = []
    for comm, customer_name, customer_email in rows:
        comm_dict = CommunicationResponse.model_validate(comm).model_dump()
        comm_dict["customer_name"] = customer_name
        comm_dict["customer_email"] = customer_email
        communications.append(CommunicationResponse(**comm_dict))

    return CommunicationListResponse(
        communications=communications,
        total=total,
        page=page,
        page_size=page_size,
    )
