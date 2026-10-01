from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.agents.human_review_agent import HumanReviewAgent
from backend.agents.state import AgentState
from backend.database.connection import engine
from backend.models import Campaign, CampaignStatusHistory


class CampaignReviewService:
    """
    Handles human approval/rejection of persisted campaigns.

    This service does NOT send campaigns.

    Workflow:

        draft
          ↓
      human review
        ↙     ↘
    approved  rejected

    Approval only changes campaign status.
    Outreach is handled separately by the
    Outreach Orchestrator.
    """

    def __init__(self):
        self.human_review_agent = HumanReviewAgent()

    # ==================================================
    # Get campaign
    # ==================================================

    def get_campaign(
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
    # Approve campaign
    # ==================================================

    def approve_campaign(
        self,
        campaign_id: int,
        approved_by: str,
        reason: str = "",
    ) -> Campaign:

        if not approved_by or not approved_by.strip():
            raise ValueError(
                "approved_by is required"
            )

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
            # Only draft campaigns can be approved
            # ----------------------------------

            if campaign.status != "draft":
                raise ValueError(
                    "Only draft campaigns can be approved. "
                    f"Campaign {campaign_id} has status "
                    f"'{campaign.status}'."
                )

            # ----------------------------------
            # Create AgentState for human review
            # ----------------------------------

            state = AgentState()

            state.approval_status = "pending"
            state.approval_required = (
                campaign.required_approval
            )

            state.qualified_leads = [
                {
                    "college_id": campaign.college_id,
                    "college_name": (
                        f"College {campaign.college_id}"
                    ),
                }
            ]

            # ----------------------------------
            # Apply human approval
            # ----------------------------------

            state = self.human_review_agent.approve(
                state=state,
                approved_by=approved_by.strip(),
                reason=reason,
            )

            # ----------------------------------
            # Persist approval
            # ----------------------------------

            now = datetime.now(timezone.utc)

            campaign.status = "approved"
            campaign.approved_at = now

            history = CampaignStatusHistory(
                campaign_id=campaign.id,
                status="approved",
                changed_at=now,
                changed_by=approved_by.strip(),
                reason=reason.strip() or None,
            )

            session.add(history)

            session.commit()
            session.refresh(campaign)

            return campaign
        
    # ==================================================
    # Approve All Campaigns At Once
    # ==================================================
    def approve_all_pending_campaigns(
        self,
        approved_by: str,
        reason: str,
    ) -> dict:
        """
        Approve all campaigns currently waiting for human approval.

        Only campaigns with:
            status = draft
            required_approval = True

        are approved.
        """

        if not approved_by or not approved_by.strip():
            raise ValueError("approved_by is required")

        with Session(engine) as session:

            campaigns = session.scalars(
                select(Campaign).where(
                    Campaign.status == "draft",
                    Campaign.required_approval.is_(True),
                )
            ).all()

            if not campaigns:
                return {
                    "approved_count": 0,
                    "campaign_ids": [],
                    "message": "No campaigns pending approval.",
                }

            approved_campaign_ids = []

            for campaign in campaigns:

                # ----------------------------------
                # Create AgentState for human review
                # ----------------------------------

                state = AgentState()

                state.approval_status = "pending"
                state.approval_required = (
                    campaign.required_approval
                )

                state.qualified_leads = [
                    {
                        "college_id": campaign.college_id,
                        "college_name": (
                            f"College {campaign.college_id}"
                        ),
                    }
                ]

                # ----------------------------------
                # Apply human approval
                # ----------------------------------

                state = self.human_review_agent.approve(
                    state=state,
                    approved_by=approved_by.strip(),
                    reason=reason,
                )

                # ----------------------------------
                # Persist approval
                # ----------------------------------

                now = datetime.now(timezone.utc)

                campaign.status = "approved"
                campaign.approved_at = now

                history = CampaignStatusHistory(
                    campaign_id=campaign.id,
                    status="approved",
                    changed_at=now,
                    changed_by=approved_by.strip(),
                    reason=reason.strip() or None,
                )

                session.add(history)

                approved_campaign_ids.append(campaign.id)

            # ----------------------------------
            # Commit all approvals together
            # ----------------------------------

            session.commit()

            return {
                "approved_count": len(approved_campaign_ids),
                "campaign_ids": approved_campaign_ids,
                "message": (
                    f"{len(approved_campaign_ids)} "
                    "campaigns approved successfully."
                ),
            }

    # ==================================================
    # Reject campaign
    # ==================================================

    def reject_campaign(
        self,
        campaign_id: int,
        rejected_by: str,
        reason: str = "",
    ) -> Campaign:

        if not rejected_by or not rejected_by.strip():
            raise ValueError(
                "rejected_by is required"
            )

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
            # Only draft campaigns can be rejected
            # ----------------------------------

            if campaign.status != "draft":
                raise ValueError(
                    "Only draft campaigns can be rejected. "
                    f"Campaign {campaign_id} has status "
                    f"'{campaign.status}'."
                )

            # ----------------------------------
            # Create AgentState for human review
            # ----------------------------------

            state = AgentState()

            state.approval_status = "pending"
            state.approval_required = (
                campaign.required_approval
            )

            state.qualified_leads = [
                {
                    "college_id": campaign.college_id,
                    "college_name": (
                        f"College {campaign.college_id}"
                    ),
                }
            ]

            # ----------------------------------
            # Apply human rejection
            # ----------------------------------

            state = self.human_review_agent.reject(
                state=state,
                rejected_by=rejected_by.strip(),
                reason=reason,
            )

            # ----------------------------------
            # Persist rejection
            # ----------------------------------

            now = datetime.now(timezone.utc)

            # Keep "rejected" for now because your
            # existing API/UI already uses this state.
            campaign.status = "rejected"
            campaign.approved_at = None

            history = CampaignStatusHistory(
                campaign_id=campaign.id,
                status="rejected",
                changed_at=now,
                changed_by=rejected_by.strip(),
                reason=reason.strip() or None,
            )

            session.add(history)

            session.commit()
            session.refresh(campaign)

            return campaign