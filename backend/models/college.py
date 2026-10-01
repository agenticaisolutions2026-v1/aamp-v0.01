from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class College(Base):
    __tablename__ = "colleges"

    # --------------------------------------------------
    # Basic information
    # --------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    official_email: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    official_phone: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    relevance_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="discovered",
    )

    # --------------------------------------------------
    # Academic information
    # --------------------------------------------------

    departments: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    programs: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------------------------------------
    # AI relevance
    # --------------------------------------------------

    ai_ml_related: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    generative_ai_related: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    agentic_ai_related: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------------------------------------
    # Official contact information
    # --------------------------------------------------

    contact_role: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    contact_form: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    whatsapp: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    linkedin: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------------------------------------
    # Institutional information
    # --------------------------------------------------

    placement_page: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    contact_page: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    innovation: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    entrepreneurship: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    clubs_events: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    training: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    workshop_training_opportunity: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    placement_available: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------------------------------------
    # Verification / provenance
    # --------------------------------------------------

    sources: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    missing_fields: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    errors: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------------------------------------
    # Relationships
    # --------------------------------------------------

    leads = relationship(
        "Lead",
        back_populates="college",
        cascade="all, delete-orphan",
    )

    campaigns = relationship(
        "Campaign",
        back_populates="college",
        cascade="all, delete-orphan",
    )