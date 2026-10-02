class CampaignApprovalService:
    """
    Handles campaign tier and approval decisions
    based on the lead score.

    Rules:
        Lead Score >= 80
            -> Tier 1
            -> Auto Approval

        Lead Score < 80
            -> Tier 2
            -> Human Approval
    """

    AUTO_APPROVAL_SCORE = 80

    @classmethod
    def evaluate(cls, lead_score):
        """
        Evaluate the campaign based on lead score.

        Returns:
            Dictionary containing:
            - lead_score
            - tier
            - approval_type
            - required_human_approval
            - approval_status
            - campaign_status
            - reason
        """

        # -----------------------------------------------------
        # Convert lead score safely to integer
        # -----------------------------------------------------

        try:
            score = int(lead_score)
        except (TypeError, ValueError):
            score = 0

        # -----------------------------------------------------
        # Keep score within 0-100
        # -----------------------------------------------------

        score = max(0, min(score, 100))

        # -----------------------------------------------------
        # TIER 1
        # Lead Score >= 80
        # Auto Approval
        # -----------------------------------------------------

        if score >= cls.AUTO_APPROVAL_SCORE:

            return {
                "lead_score": score,
                "tier": "Tier 1",
                "approval_type": "auto",
                "required_human_approval": False,
                "approval_status": "approved",
                "campaign_status": "Approved",
                "reason": "Lead score is 80 or above."
            }

        # -----------------------------------------------------
        # TIER 2
        # Lead Score < 80
        # Human Approval
        # -----------------------------------------------------

        return {
            "lead_score": score,
            "tier": "Tier 2",
            "approval_type": "human",
            "required_human_approval": True,
            "approval_status": "pending",
            "campaign_status": "Draft",
            "reason": "Lead score is below 80 and requires human approval."
        }