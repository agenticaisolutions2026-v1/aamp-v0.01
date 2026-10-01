from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import Campaign, CampaignStatusHistory
from backend.services.email_service import EmailService


class OutreachOrchestratorAgent:
    """
    Coordinates approved campaign outreach.

    Current workflow:

        APPROVED
            ↓
        QUEUED
            ↓
        EmailService
            ↓
          SENT

    Responsibilities:
        - Find approved campaigns
        - Queue a campaign for outreach
        - Call the existing EmailService
        - Return the outreach result

    This agent does NOT:
        - Generate campaign content
        - Approve campaigns
        - Analyze responses
        - Schedule follow-ups
        - Create another email-sending mechanism
    """

    def __init__(self):
        self.email_service = EmailService()

    # ==================================================
    # Get campaign
    # ==================================================

    def _get_campaign(
        self,
        campaign_id: int,
    ) -> Campaign:

        with Session(engine) as session:

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign not found: {campaign_id}"
                )

            return campaign

    # ==================================================
    # Add status history
    # ==================================================

    @staticmethod
    def _add_status_history(
        session: Session,
        campaign: Campaign,
        status: str,
        reason: str,
    ) -> None:

        history = CampaignStatusHistory(
            campaign_id=campaign.id,
            status=status,
            changed_at=datetime.now(timezone.utc),
            changed_by="outreach_orchestrator",
            reason=reason,
        )

        session.add(history)

    # ==================================================
    # Queue campaign
    # ==================================================

    def queue_campaign(
        self,
        campaign_id: int,
    ) -> Campaign:

        with Session(engine) as session:

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign not found: {campaign_id}"
                )

            # ----------------------------------
            # Safety check
            # ----------------------------------

            if campaign.status != "approved":
                raise ValueError(
                    "Only approved campaigns can be queued. "
                    f"Campaign {campaign_id} has status "
                    f"'{campaign.status}'."
                )

            # ----------------------------------
            # Queue campaign
            # ----------------------------------

            campaign.status = "queued"

            self._add_status_history(
                session=session,
                campaign=campaign,
                status="queued",
                reason=(
                    "Campaign queued for automatic outreach."
                ),
            )

            session.commit()
            session.refresh(campaign)

            return campaign

    # ==================================================
    # Send campaign
    # ==================================================

    def send_campaign(
        self,
        campaign_id: int,
    ) -> dict:
        """
        Send a queued campaign.

        The campaign is already in QUEUED status.
        The existing EmailService accepts queued campaigns
        and changes the status to SENT after successful
        SMTP delivery.
        """

        with Session(engine) as session:

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign not found: {campaign_id}"
                )

            # ----------------------------------
            # Only queued campaigns can be sent
            # ----------------------------------

            if campaign.status != "queued":
                raise ValueError(
                    "Only queued campaigns can be sent. "
                    f"Campaign {campaign_id} has status "
                    f"'{campaign.status}'."
                )

            # ----------------------------------
            # Email channel
            # ----------------------------------

            if campaign.channel != "email":
                raise ValueError(
                    "Only email campaigns are supported "
                    "by the current outreach orchestrator."
                )

        # ----------------------------------
        # Reuse existing SMTP EmailService
        # ----------------------------------

        try:

            result = self.email_service.send_campaign_email(
                campaign_id
            )

            return {
                "campaign_id": campaign_id,
                "status": result.get(
                    "status",
                    "sent",
                ),
                "sent": result.get(
                    "sent",
                    False,
                ),
                "recipient": result.get(
                    "recipient",
                ),
                "sent_at": result.get(
                    "sent_at",
                ),
                "next_follow_up_at": result.get(
                    "next_follow_up_at",
                ),
                "follow_up_count": result.get(
                    "follow_up_count",
                    0,
                ),
            }

        except Exception as exc:

            # EmailService already persists FAILED.
            return {
                "campaign_id": campaign_id,
                "status": "failed",
                "sent": False,
                "error": str(exc),
            }

    # ==================================================
    # Process one campaign
    # ==================================================

    def process_campaign(
        self,
        campaign_id: int,
    ) -> dict:
        """
        Process one approved campaign.

        Workflow:

            APPROVED
                ↓
            QUEUED
                ↓
              SENT
        """

        campaign = self._get_campaign(
            campaign_id
        )

        # ----------------------------------
        # Campaign must be approved
        # ----------------------------------

        if campaign.status != "approved":
            return {
                "campaign_id": campaign_id,
                "status": campaign.status,
                "action": "skip",
                "reason": (
                    "Campaign is not approved "
                    "for automatic outreach."
                ),
            }

        # ----------------------------------
        # Queue
        # ----------------------------------

        self.queue_campaign(
            campaign_id
        )

        # ----------------------------------
        # Send
        # ----------------------------------

        result = self.send_campaign(
            campaign_id
        )

        return {
            "campaign_id": campaign_id,
            "action": "outreach_processed",
            **result,
        }

    # ==================================================
    # Process all approved campaigns
    # ==================================================

    def process_approved_campaigns(self) -> list[dict]:
        """
        Find all approved email campaigns and process them.

        This method is intended to be called later by a
        scheduler/background worker.
        """

        with Session(engine) as session:

            campaigns = session.scalars(
                select(Campaign)
                .where(
                    Campaign.status == "approved",
                    Campaign.channel == "email",
                )
                .order_by(
                    Campaign.created_at.asc()
                )
            ).all()

            campaign_ids = [
                campaign.id
                for campaign in campaigns
            ]

        results = []

        for campaign_id in campaign_ids:

            result = self.process_campaign(
                campaign_id
            )

            results.append(result)

        return results