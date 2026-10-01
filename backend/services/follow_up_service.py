from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models.campaign import Campaign
from backend.services.email_service import EmailService


class FollowUpService:
    """
    Service responsible for campaign follow-up automation.

    Flow:

        Initial outreach
             ↓
        Day 3 → Follow-up #1
             ↓
        Day 7 → Follow-up #2
             ↓
        No response → Completed

    If a response is received at any point,
    follow-up automation stops.
    """

    def __init__(self):
        self.email_service = EmailService()

    def is_response_driven_campaign(self, campaign) -> bool:
        """
        Return True when the campaign is waiting to send
        the one automatic follow-up triggered by a recipient
        response.
        """

        return campaign.response_category in {
            "ASK_LATER",
            "OUT_OF_OFFICE",
        }

    # --------------------------------------------------
    # 1. Get campaigns whose follow-up is due
    # --------------------------------------------------

    def get_due_followups(self):

        now = datetime.now(timezone.utc)

        with Session(engine) as session:

            campaigns = session.scalars(
                select(Campaign).where(
                    Campaign.channel == "email",
                    Campaign.next_follow_up_at.is_not(None),
                    Campaign.next_follow_up_at <= now,
                    Campaign.status.in_(
                        [
                            "sent",
                            "delivered",
                            "follow_up_due",
                            "replied",
                        ]
                    ),
                )
            ).all()

            # ----------------------------------------------
            # Only allow "replied" campaigns when the
            # response intentionally scheduled a follow-up.
            # ----------------------------------------------

            due_campaigns = []

            for campaign in campaigns:

                if campaign.status == "replied":

                    if campaign.response_category not in {
                        "ASK_LATER",
                        "OUT_OF_OFFICE",
                    }:
                        continue

                due_campaigns.append(campaign)

            return due_campaigns

    # --------------------------------------------------
    # 2. Check whether response already exists
    # --------------------------------------------------

    def has_response(self, campaign_id: int) -> bool:

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

            return campaign.last_response_at is not None

    # --------------------------------------------------
    # 3. Send one follow-up
    # --------------------------------------------------

    def send_followup(self, campaign_id: int):

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

            # ------------------------------------------
            # Current time
            # ------------------------------------------

            now = datetime.now(timezone.utc)

            is_response_driven = (
                campaign.response_category
                in {
                    "ASK_LATER",
                    "OUT_OF_OFFICE",
                }
                and campaign.follow_up_count == 0
            )

            is_response_window_expired = (
                campaign.response_category
                in {
                    "ASK_LATER",
                    "OUT_OF_OFFICE",
                }
                and campaign.follow_up_count >= 1
            )

            if is_response_window_expired:
                campaign.status = "completed"
                campaign.completed_at = now
                campaign.next_follow_up_at = None

                session.commit()

                return {
                    "campaign_id": campaign_id,
                    "status": "completed",
                    "reason": (
                        "No response within 3 days after "
                        "the response-driven follow-up."
                    ),
                    "completed_at": campaign.completed_at,
                }

            # ------------------------------------------
            # Safety check: email only
            # ------------------------------------------

            if campaign.channel != "email":
                return {
                    "campaign_id": campaign_id,
                    "status": "skipped",
                    "reason": "Campaign is not an email campaign.",
                }

            # ------------------------------------------
            # Safety check: response received
            # ------------------------------------------

            if (
                campaign.last_response_at is not None
                and campaign.response_category
                not in {
                    "ASK_LATER",
                    "OUT_OF_OFFICE",
                }
            ):
                return {
                    "campaign_id": campaign_id,
                    "status": "skipped",
                    "reason": "Response already received.",
                }

            # ------------------------------------------
            # Final response check
            # ------------------------------------------

            if (
                not is_response_driven
                and campaign.follow_up_count
                >= campaign.max_follow_ups
            ):

                campaign.status = "completed"
                campaign.completed_at = now
                campaign.next_follow_up_at = None

                session.commit()

                return {
                    "campaign_id": campaign_id,
                    "status": "completed",
                    "reason": (
                        "No response after maximum follow-ups."
                    ),
                    "completed_at":
                        campaign.completed_at,
                }

            # ------------------------------------------
            # Safety check: scheduled time
            # ------------------------------------------

            if campaign.next_follow_up_at is None:
                return {
                    "campaign_id": campaign_id,
                    "status": "skipped",
                    "reason": "No follow-up is scheduled.",
                }

            next_follow_up = (
                campaign.next_follow_up_at
            )

            if next_follow_up.tzinfo is None:
                next_follow_up = (
                    next_follow_up.replace(
                        tzinfo=timezone.utc
                    )
                )

            if next_follow_up > now:
                return {
                    "campaign_id": campaign_id,
                    "status": "skipped",
                    "reason": "Follow-up is not due yet.",
                    "next_follow_up_at":
                        campaign.next_follow_up_at,
                }

            # ------------------------------------------
            # Response-driven follow-up
            # ------------------------------------------

            if is_response_driven:
                campaign.status = "follow_up_due"
                session.commit()

                sent_campaign = (
                    self.email_service.send_campaign_email(
                        campaign_id,
                        is_response_driven=True,
                    )
                )

                return {
                    "campaign_id": campaign_id,
                    "status": "sent",
                    "type": "response_driven_follow_up",
                    "follow_up_count": (
                        sent_campaign.get("follow_up_count")
                    ),
                    "next_follow_up_at": (
                        sent_campaign.get("next_follow_up_at")
                    ),
                }

            # ------------------------------------------
            # Mark campaign as follow-up due
            # ------------------------------------------

            campaign.status = "follow_up_due"

            session.commit()


        # ----------------------------------------------
        # Send outside the session
        # ----------------------------------------------

        sent_campaign = (
            self.email_service.send_campaign_email(
                campaign_id
            )
        )

        return {
            "campaign_id": campaign_id,
            "status": "sent",
            "follow_up_count":
                sent_campaign.get("follow_up_count"),
            "next_follow_up_at":
                sent_campaign.get("next_follow_up_at"),
        }

    # --------------------------------------------------
    # 4. Process all due follow-ups
    # --------------------------------------------------

    def process_due_followups(self):

        campaigns = self.get_due_followups()

        results = []

        for campaign in campaigns:

            try:

                result = self.send_followup(
                    campaign.id
                )

                results.append(result)

            except Exception as exc:

                results.append(
                    {
                        "campaign_id": campaign.id,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        return results