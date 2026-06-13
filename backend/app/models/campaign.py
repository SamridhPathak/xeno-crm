"""
Campaign ORM model.

A campaign links a segment to a message template and tracks overall
delivery status. When launched, individual Communication records are
created for each customer in the segment.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Campaign(Base):
    """
    A marketing campaign targeting a specific segment.

    Attributes:
        id: Auto-incrementing primary key.
        name: Campaign name (e.g. "Summer Cold Brew Promo").
        segment_id: FK to the audience segment.
        message_template: The message copy, may contain {name} placeholders.
        channel: Delivery channel — "sms", "email", or "whatsapp".
        status: Lifecycle state — draft → sending → completed.
        created_at: When the campaign was created.
    """

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    segment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(
        Enum("sms", "email", "whatsapp", name="channel_type", create_constraint=True),
        nullable=False,
        default="email",
    )
    status: Mapped[str] = mapped_column(
        Enum("draft", "sending", "completed", "failed" , name="campaign_status", create_constraint=True),
        nullable=False,
        default="draft",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    segment: Mapped["Segment"] = relationship(  # noqa: F821
        "Segment", back_populates="campaigns"
    )
    communications: Mapped[list["Communication"]] = relationship(  # noqa: F821
        "Communication", back_populates="campaign", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"
