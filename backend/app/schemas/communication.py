"""
Pydantic schemas for Communication and delivery receipt validation.

Communications are individual messages sent to customers as part of
a campaign. Receipts are async callbacks from the channel service
updating delivery status.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════
# RECEIPT (CALLBACK) SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class DeliveryReceipt(BaseModel):
    """
    Payload sent by the channel service for each delivery event.

    The channel service fires these to POST /receipts as messages
    progress through the delivery lifecycle.
    """

    communication_id: int = Field(..., description="ID of the communication record.")
    event_type: str = Field(
        ...,
        description="Event type: delivered, failed, opened, read, clicked.",
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="When the event occurred. Defaults to server time if omitted.",
    )


class BulkDeliveryReceipt(BaseModel):
    """Batch of delivery receipts for efficient processing."""

    receipts: list[DeliveryReceipt] = Field(
        ..., min_length=1,
        description="One or more delivery event receipts.",
    )


# ═══════════════════════════════════════════════════════════════════
# COMMUNICATION RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class CommunicationResponse(BaseModel):
    """Individual communication record with customer info."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    customer_id: int
    channel: str
    message: str
    status: str
    created_at: datetime
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class CommunicationListResponse(BaseModel):
    """Paginated list of communications for a campaign."""

    communications: list[CommunicationResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════════
# ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class CampaignAnalytics(BaseModel):
    """Aggregated delivery stats for a single campaign."""

    campaign_id: int
    campaign_name: str
    channel: str

    created_at: datetime | None = None
    status: str = "completed"

    total_sent: int = 0
    delivered: int = 0
    failed: int = 0
    opened: int = 0
    clicked: int = 0

    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0


class OverviewAnalytics(BaseModel):
    """Dashboard-level overview stats across all campaigns."""

    total_customers: int = 0
    total_segments: int = 0
    total_campaigns: int = 0
    total_messages_sent: int = 0
    overall_delivery_rate: float = 0.0
    overall_open_rate: float = 0.0
    overall_click_rate: float = 0.0
    recent_campaigns: list[CampaignAnalytics] = []
