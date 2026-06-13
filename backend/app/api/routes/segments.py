"""
Segment API routes.

Endpoints:
    GET  /api/segments                  — List all segments
    POST /api/segments                  — Create a new segment from filter rules
    GET  /api/segments/{id}/customers   — Preview customers in a segment
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.segment import Segment
from app.schemas.customer import CustomerListResponse, CustomerResponse
from app.schemas.segment import (
    SegmentCreate,
    SegmentListResponse,
    SegmentResponse,
)
from app.services.segment_service import (
    count_segment_customers,
    get_segment_customers,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/segments", tags=["Segments"])


# ─────────────────────────────────────────────────────────────────
# GET /api/segments — list all segments
# ─────────────────────────────────────────────────────────────────


@router.get("", response_model=SegmentListResponse)
async def list_segments(
    db: AsyncSession = Depends(get_db),
) -> SegmentListResponse:
    """List all saved customer segments, newest first."""
    result = await db.execute(
        select(Segment).order_by(Segment.created_at.desc())
    )
    segments = result.scalars().all()

    return SegmentListResponse(
        segments=[SegmentResponse.model_validate(s) for s in segments],
        total=len(segments),
    )


# ─────────────────────────────────────────────────────────────────
# POST /api/segments — create a new segment
# ─────────────────────────────────────────────────────────────────


@router.post("", response_model=SegmentResponse, status_code=201)
async def create_segment(
    payload: SegmentCreate,
    db: AsyncSession = Depends(get_db),
) -> SegmentResponse:
    """
    Create a new customer segment.

    Validates the filter rules by counting matching customers,
    then saves the segment with the cached count.
    """
    # Serialise filter rules to plain dicts for JSONB storage.
    filter_dicts = [rule.model_dump() for rule in payload.filter_rules]

    # Count matching customers to validate the rules are sensible.
    try:
        customer_count = await count_segment_customers(db, filter_dicts)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Create and persist the segment.
    segment = Segment(
        name=payload.name,
        description=payload.description,
        filter_rules=filter_dicts,
        customer_count=customer_count,
    )
    db.add(segment)
    await db.flush()
    await db.refresh(segment)

    logger.info(
        "Segment '%s' created with %d matching customers.",
        segment.name, customer_count,
    )

    return SegmentResponse.model_validate(segment)


# ─────────────────────────────────────────────────────────────────
# GET /api/segments/{id}/customers — preview segment audience
# ─────────────────────────────────────────────────────────────────


@router.get("/{segment_id}/customers", response_model=CustomerListResponse)
async def get_segment_customers_endpoint(
    segment_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CustomerListResponse:
    """
    Preview the customers that match a segment's filter rules.

    Returns a paginated list so the marketer can verify the audience
    before launching a campaign.
    """
    # Load the segment.
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment {segment_id} not found.")

    filter_rules = segment.filter_rules
    if isinstance(filter_rules, dict):
        filter_rules = [filter_rules]

    # Count total matching customers.
    try:
        total = await count_segment_customers(db, filter_rules)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Fetch the page of customers.
    offset = (page - 1) * page_size
    customers = await get_segment_customers(
        db, filter_rules, limit=page_size, offset=offset
    )

    return CustomerListResponse(
        customers=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size,
    )
