from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class CampaignCall(Base):
    __tablename__ = "campaign_calls"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )

    response_action_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_response_actions.id", ondelete="SET NULL"),
        nullable=True,
    )

    call_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SCHEDULED",
    )

    notes: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    confirmation_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    campaign = relationship(
        "Campaign",
        back_populates="calls",
    )

    response_action = relationship(
        "CampaignResponseAction",
        back_populates="call",
    )