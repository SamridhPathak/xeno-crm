"""
Customer ORM model.

Represents a retail shopper in the BrewBox CRM.
Tracks contact info, location, and aggregate purchase behaviour.
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Customer(Base):
    """
    A BrewBox customer record.

    Attributes:
        id: Auto-incrementing primary key.
        name: Full name (e.g. "Aarav Sharma").
        phone: 10-digit Indian mobile number.
        email: Contact email address.
        city: City of residence (e.g. "Mumbai", "Bengaluru").
        total_spend: Lifetime spend in INR, updated on each order.
        order_count: Total number of completed orders.
        last_purchase_date: Date of the most recent order.
        created_at: Timestamp when the customer was first ingested.
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    total_spend: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    order_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    orders: Mapped[list["Order"]] = relationship(  # noqa: F821
        "Order", back_populates="customer", cascade="all, delete-orphan"
    )
    communications: Mapped[list["Communication"]] = relationship(  # noqa: F821
        "Communication", back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}', city='{self.city}')>"
