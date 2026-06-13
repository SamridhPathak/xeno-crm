"""
Customer API routes.

Endpoints:
    GET  /api/customers         — List customers with optional filters & pagination
    GET  /api/customers/{id}    — Get a single customer by ID
    POST /api/customers/bulk    — Bulk-import customers
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerBulkCreate,
    CustomerListResponse,
    CustomerResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/customers", tags=["Customers"])


# ─────────────────────────────────────────────────────────────────
# GET /api/customers — paginated list with optional filters
# ─────────────────────────────────────────────────────────────────


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(20, ge=1, le=100, description="Items per page."),
    city: Optional[str] = Query(None, description="Filter by city name."),
    min_spend: Optional[float] = Query(None, ge=0, description="Minimum total spend."),
    max_spend: Optional[float] = Query(None, ge=0, description="Maximum total spend."),
    min_orders: Optional[int] = Query(None, ge=0, description="Minimum order count."),
    search: Optional[str] = Query(None, description="Search by name or email."),
    db: AsyncSession = Depends(get_db),
) -> CustomerListResponse:
    """
    List all customers with optional filtering and pagination.

    Supports filtering by city, spend range, order count, and
    free-text search across name and email fields.
    """
    query = select(Customer)
    count_query = select(func.count(Customer.id))

    # Apply filters.
    if city:
        query = query.where(Customer.city == city)
        count_query = count_query.where(Customer.city == city)
    if min_spend is not None:
        query = query.where(Customer.total_spend >= min_spend)
        count_query = count_query.where(Customer.total_spend >= min_spend)
    if max_spend is not None:
        query = query.where(Customer.total_spend <= max_spend)
        count_query = count_query.where(Customer.total_spend <= max_spend)
    if min_orders is not None:
        query = query.where(Customer.order_count >= min_orders)
        count_query = count_query.where(Customer.order_count >= min_orders)
    if search:
        search_filter = Customer.name.ilike(f"%{search}%") | Customer.email.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count before pagination.
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination and ordering.
    offset = (page - 1) * page_size
    query = query.order_by(Customer.id).offset(offset).limit(page_size)

    result = await db.execute(query)
    customers = result.scalars().all()

    return CustomerListResponse(
        customers=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size,
    )


# ─────────────────────────────────────────────────────────────────
# GET /api/customers/{id} — single customer detail
# ─────────────────────────────────────────────────────────────────


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    """Fetch a single customer by ID."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")

    return CustomerResponse.model_validate(customer)


# ─────────────────────────────────────────────────────────────────
# POST /api/customers/bulk — bulk import
# ─────────────────────────────────────────────────────────────────


@router.post("/bulk", response_model=dict, status_code=201)
async def bulk_create_customers(
    payload: CustomerBulkCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Bulk-import customers.

    Accepts up to 1000 customers per request. Skips duplicates
    (by phone or email) and reports the count of successfully
    imported records.
    """
    imported = 0
    skipped = 0

    for cust_data in payload.customers:
        # Check for existing customer by phone or email.
        existing = await db.execute(
            select(Customer.id).where(
                (Customer.phone == cust_data.phone) | (Customer.email == cust_data.email)
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        customer = Customer(**cust_data.model_dump())
        db.add(customer)
        imported += 1

    await db.flush()

    logger.info("Bulk import: %d imported, %d skipped.", imported, skipped)

    return {
        "imported": imported,
        "skipped": skipped,
        "total": len(payload.customers),
        "message": f"Successfully imported {imported} customers ({skipped} duplicates skipped).",
    }
