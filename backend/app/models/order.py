"""
Order ORM model.

Represents a single purchase transaction at BrewBox.
Items are stored as a JSON column for flexible product cataloguing.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Order(Base):
    """
    A BrewBox order tied to a specific customer.

    Attributes:
        id: Auto-incrementing primary key.
        customer_id: FK to the customer who placed this order.
        amount: Total order amount in INR.
        items: JSON list of purchased items, e.g.
               [{"name": "Cappuccino", "qty": 2, "price": 250}]
        created_at: When the order was placed.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="orders"
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, customer_id={self.customer_id}, amount={self.amount})>"
