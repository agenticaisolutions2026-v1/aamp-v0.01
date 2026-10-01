from datetime import datetime,timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey(
            "workflow_runs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "campaigns.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    agent_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    workflow = relationship(
        "WorkflowRun",
        back_populates="agent_runs",
    )