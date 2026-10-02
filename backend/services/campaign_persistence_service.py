from sqlalchemy.orm import Session

from backend.database.models import Campaign


class CampaignPersistenceService:

    @staticmethod
    def save_campaign(
        db: Session,
        campaign_data: dict,
    ):

        campaign = Campaign(
            college_id=campaign_data.get(
                "college_id"
            ),

            college_name=campaign_data.get(
                "college_name",
                "",
            ),

            campaign_type=campaign_data.get(
                "campaign_type",
                "institutional_training",
            ),

            channel=campaign_data.get(
                "recommended_channel",
                "manual_review",
            ),

            contact_role=campaign_data.get(
                "contact_role"
            ),

            subject=campaign_data.get(
                "subject"
            ),

            message=campaign_data.get(
                "message",
                "",
            ),

            objective=campaign_data.get(
                "objective"
            ),

            lead_score=campaign_data.get(
                "lead_score"
            ),

            priority=campaign_data.get(
                "priority"
            ),

            # -----------------------------------------
            # NEW: Campaign Tier
            # -----------------------------------------

            tier=campaign_data.get(
                "tier"
            ),

            qualification=campaign_data.get(
                "qualification"
            ),

            # -----------------------------------------
            # Approval
            # -----------------------------------------

            required_human_approval=campaign_data.get(
                "required_human_approval",
                True,
            ),

            status=campaign_data.get(
                "status",
                "Draft",
            ),

            # -----------------------------------------
            # NEW: Approval timestamp
            # -----------------------------------------

            approved_at=campaign_data.get(
                "approved_at"
            ),
        )

        # ---------------------------------------------
        # Save campaign
        # ---------------------------------------------

        db.add(campaign)

        db.commit()

        db.refresh(campaign)

        return campaign

    # =================================================
    # Get all campaigns
    # =================================================

    @staticmethod
    def get_all(
        db: Session,
    ):

        return (
            db.query(Campaign)
            .all()
        )