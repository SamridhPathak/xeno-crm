"""
Pydantic schemas for Segment request/response validation.

Segments are created from AI-parsed natural-language intent.
The filter_rules field stores a JSON structure that the segment
service translates into SQLAlchemy queries.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════
# FILTER RULE SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class FilterRule(BaseModel):
    """
    A single filter condition for segmenting customers.

    Examples:
        {"field": "total_spend", "op": ">", "value": 5000}
        {"field": "city", "op": "==", "value": "Mumbai"}
        {"field": "order_count", "op": ">=", "value": 3}
        {"field": "last_purchase_date", "op": "<", "value": "2025-01-01"}
    """

    field: str = Field(
        ...,
        description="Customer field to filter on (e.g. total_spend, city, order_count).",
    )
    op: str = Field(
        ...,
        description="Comparison operator: ==, !=, >, <, >=, <=, in, not_in, contains.",
    )
    value: Any = Field(
        ...,
        description="Value to compare against. Type depends on field and operator.",
    )


# ═══════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class SegmentCreate(BaseModel):
    """Schema for creating a new segment with filter rules."""

    name: str = Field(..., min_length=1, max_length=255, examples=["High spenders in Mumbai"])
    description: Optional[str] = Field(None, examples=["Customers who spent over ₹5000 in Mumbai"])
    filter_rules: list[FilterRule] = Field(
        ..., min_length=1,
        description="One or more filter rules. All rules are combined with AND logic.",
    )


# ═══════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class SegmentResponse(BaseModel):
    """Full segment record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    filter_rules: Any  # JSONB comes back as list[dict]
    customer_count: int
    created_at: datetime


class SegmentListResponse(BaseModel):
    """List of all segments."""

    segments: list[SegmentResponse]
    total: int
