from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.database.models import Campaign, College
from backend.agents.state import AgentState
from backend.agents.outreach_orchestrator_agent import (
    OutreachOrchestratorAgent,
)
from backend.services.outreach_persistence_service import (
    OutreachPersistenceService,
)


router = APIRouter()

outreach_orchestrator = OutreachOrchestratorAgent()


# =========================================================
# Get all campaigns
# =========================================================

@router.get("/campaigns")
def get_campaigns(
    db: Session = Depends(get_db),
):

    campaigns = (
        db.query(Campaign)
        .order_by(Campaign.created_at.desc())
        .all()
    )

    campaign_list = []

    for campaign in campaigns:

        # -------------------------------------------------
        # Determine approval information
        # -------------------------------------------------

        if campaign.tier == "Tier 1":

            approval_type = "auto"

            approval_status = "approved"

        elif campaign.tier == "Tier 2":

            approval_type = "human"

            if campaign.status == "Approved":

                approval_status = "approved"

            elif campaign.status == "Rejected":

                approval_status = "rejected"

            else:

                approval_status = "pending"

        else:

            if campaign.required_human_approval:

                approval_type = "human"

            else:

                approval_type = "auto"

            if campaign.status == "Approved":

                approval_status = "approved"

            elif campaign.status == "Rejected":

                approval_status = "rejected"

            else:

                approval_status = "pending"

        # -------------------------------------------------
        # Build campaign response
        # -------------------------------------------------

        campaign_list.append(
            {
                "id": campaign.id,

                "college_id": campaign.college_id,

                "college_name": campaign.college_name,

                "campaign_type": campaign.campaign_type,

                "channel": campaign.channel,

                "contact_role": campaign.contact_role,

                "subject": campaign.subject,

                "message": campaign.message,

                "objective": campaign.objective,

                "lead_score": campaign.lead_score,

                "priority": campaign.priority,

                "tier": campaign.tier,

                "qualification": campaign.qualification,

                "required_human_approval": (
                    campaign.required_human_approval
                ),

                "approval_type": approval_type,

                "approval_status": approval_status,

                "status": campaign.status,

                "approved_at": campaign.approved_at,

                "created_at": campaign.created_at,

                "updated_at": campaign.updated_at,
            }
        )

    return campaign_list


# =========================================================
# Approve campaign and create outreach queue
# =========================================================

@router.post("/campaigns/{campaign_id}/approve")
def approve_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):

    campaign = (
        db.query(Campaign)
        .filter(
            Campaign.id == campaign_id
        )
        .first()
    )

    if campaign is None:

        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    if campaign.status == "Rejected":

        raise HTTPException(
            status_code=400,
            detail="Rejected campaign cannot be approved",
        )

    if campaign.status == "Sent":

        raise HTTPException(
            status_code=400,
            detail="Campaign has already been sent",
        )

    if campaign.status == "Approved":

        raise HTTPException(
            status_code=400,
            detail="Campaign has already been approved",
        )

    # -----------------------------------------------------
    # Get college information
    # -----------------------------------------------------

    college = None

    if campaign.college_id:

        college = (
            db.query(College)
            .filter(
                College.id == campaign.college_id
            )
            .first()
        )

    # -----------------------------------------------------
    # Human approval
    # -----------------------------------------------------

    campaign.status = "Approved"

    campaign.approved_at = datetime.utcnow()

    # -----------------------------------------------------
    # Build approved campaign input
    # for Outreach Orchestrator
    # -----------------------------------------------------

    campaign_data = {
        "campaign_id": campaign.id,

        "college_id": campaign.college_id,

        "college_name": campaign.college_name,

        "priority": campaign.priority,

        "channel": campaign.channel,

        "subject": campaign.subject,

        "message": campaign.message,

        "required_human_approval": (
            campaign.required_human_approval
        ),

        "approval_status": "approved",

        "recipient": (
            college.email
            if college
            else None
        ),
    }

    # -----------------------------------------------------
    # Create AgentState
    # -----------------------------------------------------

    state = AgentState()

    state.result = {
        "campaign": campaign_data
    }

    # -----------------------------------------------------
    # Run Outreach Orchestrator
    # -----------------------------------------------------

    try:

        result_state = outreach_orchestrator.execute(
            state
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Campaign was not queued because "
                f"the Outreach Orchestrator failed: {str(exc)}"
            ),
        )

    # -----------------------------------------------------
    # Check orchestrator result
    # -----------------------------------------------------

    if result_state.status != "success":

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=(
                result_state.result
                or {
                    "status": "blocked",
                    "reason": result_state.error
                    or "Outreach queue creation failed",
                }
            ),
        )

    outreach_data = result_state.result.get(
        "outreach"
    )

    if not outreach_data:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Outreach Orchestrator completed "
                "but no outreach queue was created."
            ),
        )

    # -----------------------------------------------------
    # Save outreach queue in database
    # -----------------------------------------------------

    try:

        outreach_record = (
            OutreachPersistenceService.save_outreach(
                db,
                outreach_data,
            )
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Campaign was approved but outreach "
                f"could not be saved: {str(exc)}"
            ),
        )

    # -----------------------------------------------------
    # Refresh campaign
    # -----------------------------------------------------

    db.refresh(campaign)

    # -----------------------------------------------------
    # Return structured output
    # -----------------------------------------------------

    return {
        "campaign": {
            "id": campaign.id,

            "college_id": campaign.college_id,

            "college_name": campaign.college_name,

            "lead_score": campaign.lead_score,

            "tier": campaign.tier,

            "priority": campaign.priority,

            "required_human_approval": (
                campaign.required_human_approval
            ),

            "approval_type": (
                "human"
                if campaign.required_human_approval
                else "auto"
            ),

            "approval_status": "approved",

            "status": campaign.status,

            "approved_at": campaign.approved_at,
        },

        "outreach": {
            "id": outreach_record.id,

            "campaign_id": (
                outreach_record.campaign_id
            ),

            "college_id": (
                outreach_record.college_id
            ),

            "channel": (
                outreach_record.channel
            ),

            "recipient": (
                outreach_record.recipient
            ),

            "subject": (
                outreach_record.subject
            ),

            "status": (
                outreach_record.status
            ),

            "follow_up_count": (
                outreach_record.follow_up_count
            ),
        },

        "next_action": outreach_data.get(
            "next_action"
        ),

        "message": (
            "Campaign approved successfully "
            "and outreach queued."
        ),
    }


# =========================================================
# Reject campaign
# =========================================================

@router.post("/campaigns/{campaign_id}/reject")
def reject_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):

    campaign = (
        db.query(Campaign)
        .filter(
            Campaign.id == campaign_id
        )
        .first()
    )

    if campaign is None:

        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    if campaign.status == "Sent":

        raise HTTPException(
            status_code=400,
            detail="Sent campaign cannot be rejected",
        )

    campaign.status = "Rejected"

    db.commit()

    db.refresh(campaign)

    return {
        "id": campaign.id,

        "college_name": campaign.college_name,

        "tier": campaign.tier,

        "approval_status": "rejected",

        "status": campaign.status,

        "message": "Campaign rejected successfully",
    }