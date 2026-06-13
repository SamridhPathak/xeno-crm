"""
Pydantic schemas for Campaign request/response validation.

Campaigns link a segment audience to a message template, track
delivery lifecycle, and aggregate performance stats.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class CampaignCreate(BaseModel):
    """Schema for creating a new campaign."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Summer Cold Brew Promo"])
    segment_id: int = Field(..., description="ID of the target audience segment.")
    message_template: str = Field(
        ..., min_length=1,
        description="Message copy. Use {name} as a placeholder for customer name.",
        examples=["Hey {name}! ☕ Get 20% off your next Cold Brew at BrewBox. Use code CHILL20."],
    )
    channel: str = Field(
        default="email",
        description="Delivery channel: sms, email, or whatsapp.",
    )


# ═══════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class CampaignResponse(BaseModel):
    """Full campaign record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    segment_id: int
    message_template: str
    channel: str
    status: str
    created_at: datetime


class CampaignDetailResponse(CampaignResponse):
    """Extended campaign response with segment info and live stats."""

    segment_name: Optional[str] = None
    total_sent: int = 0
    delivered: int = 0
    failed: int = 0
    opened: int = 0
    clicked: int = 0


class CampaignListResponse(BaseModel):
    """List of all campaigns with basic info."""

    campaigns: list[CampaignResponse]
    total: int
