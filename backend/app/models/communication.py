"""
Communication ORM model.

Each Communication is a single message sent to one customer as part
of a campaign. Its status is updated asynchronously by delivery
receipts from the channel service.
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


class Communication(Base):
    """
    An individual message delivery record within a campaign.

    Attributes:
        id: Auto-incrementing primary key.
        campaign_id: FK to the parent campaign.
        customer_id: FK to the recipient customer.
        channel: Delivery channel used (mirrors campaign channel).
        message: The personalised message content sent to this customer.
        status: Current delivery state — progresses through:
                sent → delivered → opened → read → clicked  (happy path)
                sent → failed  (error path)
        created_at: When the communication was dispatched.
    """

    __tablename__ = "communications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "sent", "delivered", "failed", "opened", "read", "clicked",
            name="communication_status",
            create_constraint=True,
        ),
        nullable=False,
        default="sent",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    campaign: Mapped["Campaign"] = relationship(  # noqa: F821
        "Campaign", back_populates="communications"
    )
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="communications"
    )
    events: Mapped[list["CampaignEvent"]] = relationship(  # noqa: F821
        "CampaignEvent", back_populates="communication", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Communication(id={self.id}, campaign={self.campaign_id}, "
            f"customer={self.customer_id}, status='{self.status}')>"
        )
