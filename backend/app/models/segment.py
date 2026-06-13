"""
Segment ORM model.

A segment is a saved audience filter created from natural-language intent.
The AI service translates marketer language into JSON filter rules that
can be replayed against the customer table at any time.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Segment(Base):
    """
    A reusable customer audience segment.

    Attributes:
        id: Auto-incrementing primary key.
        name: Human-readable segment name (e.g. "High spenders in Mumbai").
        description: Optional longer description of the segment's intent.
        filter_rules: JSON structure encoding the DB query filters, e.g.
                      {"field": "total_spend", "op": ">", "value": 5000}
        customer_count: Cached count of matching customers at creation time.
        created_at: When the segment was created.
    """

    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    filter_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    customer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    campaigns: Mapped[list["Campaign"]] = relationship(  # noqa: F821
        "Campaign", back_populates="segment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Segment(id={self.id}, name='{self.name}', count={self.customer_count})>"
