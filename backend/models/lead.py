from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Lead(Base):
    __tablename__ = "leads"

    # --------------------------------------------------
    # Primary key
    # --------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # --------------------------------------------------
    # College relationship
    # --------------------------------------------------

    college_id: Mapped[int] = mapped_column(
        ForeignKey("colleges.id"),
        nullable=False,
    )

    # --------------------------------------------------
    # Lead information
    # --------------------------------------------------

    contact_role: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    qualification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
    )

    lead_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------
    # Timestamps
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Relationships
    # --------------------------------------------------

    college = relationship(
        "College",
        back_populates="leads",
    )