"""
Pydantic schemas for Customer request/response validation.

Covers single creation, bulk ingestion, filtered list responses,
and detail views.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class CustomerBase(BaseModel):
    """Shared fields for customer creation."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Aarav Sharma"])
    phone: str = Field(..., min_length=10, max_length=15, examples=["9876543210"])
    email: EmailStr = Field(..., examples=["aarav.sharma@gmail.com"])
    city: str = Field(..., min_length=1, max_length=100, examples=["Mumbai"])


class CustomerCreate(CustomerBase):
    """Schema for creating a single customer (with optional spend data)."""

    total_spend: float = Field(default=0.0, ge=0)
    order_count: int = Field(default=0, ge=0)
    last_purchase_date: Optional[date] = None


class CustomerBulkCreate(BaseModel):
    """Schema for bulk-importing multiple customers at once."""

    customers: list[CustomerCreate] = Field(
        ..., min_length=1, max_length=1000,
        description="List of customers to import (max 1000 per batch).",
    )


# ═══════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class CustomerResponse(BaseModel):
    """Full customer record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    email: str
    city: str
    total_spend: float
    order_count: int
    last_purchase_date: Optional[date] = None
    created_at: datetime


class CustomerListResponse(BaseModel):
    """Paginated list of customers with total count for UI pagination."""

    customers: list[CustomerResponse]
    total: int
    page: int
    page_size: int
