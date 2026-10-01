"""add campaign automation fields

Revision ID: 59372f6ffb9f
Revises: 83bbe12af05d
Create Date: 2026-09-17 08:14:16.390882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59372f6ffb9f'
down_revision: Union[str, Sequence[str], None] = '83bbe12af05d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --------------------------------------------------
    # Campaign automation fields
    # --------------------------------------------------

    op.add_column(
        "campaigns",
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "next_follow_up_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "follow_up_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "max_follow_ups",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "last_response_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "response_category",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "campaigns",
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    # --------------------------------------------------
    # Lead lifecycle
    # --------------------------------------------------

    op.add_column(
        "leads",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("leads", "status")

    op.drop_column("campaigns", "failure_reason")
    op.drop_column("campaigns", "completed_at")
    op.drop_column("campaigns", "response_category")
    op.drop_column("campaigns", "last_response_at")
    op.drop_column("campaigns", "max_follow_ups")
    op.drop_column("campaigns", "follow_up_count")
    op.drop_column("campaigns", "next_follow_up_at")
    op.drop_column("campaigns", "sent_at")
    op.drop_column("campaigns", "scheduled_at")
