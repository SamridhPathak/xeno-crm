"""
CampaignEvent ORM model.

Stores granular delivery lifecycle events received via async callbacks
from the channel service. Each event represents a single state transition
(e.g. delivered, opened, clicked) for a specific Communication.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CampaignEvent(Base):
    """
    A delivery event for a single communication.

    These are created when the channel service posts to the /receipts
    endpoint. They form an immutable audit trail of the message lifecycle.

    Attributes:
        id: Auto-incrementing primary key.
        communication_id: FK to the parent communication record.
        event_type: The type of event — "delivered", "failed",
                    "opened", "read", "clicked".
        timestamp: When the event occurred (as reported by the channel service).
    """

    __tablename__ = "campaign_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    communication_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("communications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    communication: Mapped["Communication"] = relationship(  # noqa: F821
        "Communication", back_populates="events"
    )

    def __repr__(self) -> str:
        return (
            f"<CampaignEvent(id={self.id}, comm={self.communication_id}, "
            f"type='{self.event_type}')>"
        )
