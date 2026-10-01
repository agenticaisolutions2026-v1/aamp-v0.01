from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    college_id: Mapped[int] = mapped_column(
        ForeignKey("colleges.id"),
        nullable=False,
    )

    campaign_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    subject: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
    )

    required_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    follow_up_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    max_follow_ups: Mapped[int] = mapped_column(
        nullable=False,
        default=2,
    )

    last_response_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    response_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    contact_updated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    college = relationship(
        "College",
        back_populates="campaigns",
    )

    status_history = relationship(
        "CampaignStatusHistory",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="CampaignStatusHistory.changed_at",
    )

    conversation_messages = relationship(
        "ConversationMessage",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )

    response_actions = relationship(
        "CampaignResponseAction",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="CampaignResponseAction.created_at",
    )

    meetings = relationship(
        "CampaignMeeting",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="CampaignMeeting.meeting_date",
    )

    calls = relationship(
        "CampaignCall",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="CampaignCall.call_date",
    )