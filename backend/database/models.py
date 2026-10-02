from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


# ============================================================
# ORGANIZATION
# ============================================================

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )


# ============================================================
# COLLEGE
# ============================================================

class College(Base):
    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    departments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    programs: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    placement_page: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    contact_page: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


# ============================================================
# CAMPAIGN
# ============================================================

class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    college_id: Mapped[int | None] = mapped_column(
        ForeignKey("colleges.id"),
        nullable=True,
        index=True
    )

    college_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    campaign_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    contact_role: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    objective: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    lead_score: Mapped[int | None] = mapped_column(
        nullable=True
    )

    priority: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # --------------------------------------------------------
    # NEW: CAMPAIGN TIER
    # Tier 1 -> Lead Score >= 80 -> Auto Approval
    # Tier 2 -> Lead Score < 80 -> Human Approval
    # --------------------------------------------------------

    tier: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    qualification: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    required_human_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Draft"
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


# ============================================================
# OUTREACH
# ============================================================

class Outreach(Base):
    __tablename__ = "outreach_messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True
    )

    college_id: Mapped[int | None] = mapped_column(
        ForeignKey("colleges.id"),
        nullable=True,
        index=True
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    recipient: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued"
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    response_received_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    follow_up_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )