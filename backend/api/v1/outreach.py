from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.database.models import Outreach
from backend.agents.outreach_orchestrator_agent import (
    OutreachOrchestratorAgent,
)


router = APIRouter()


# =========================================================
# Response Request Model
# =========================================================

class OutreachResponseRequest(BaseModel):
    response_text: str


# =========================================================
# Get all outreach messages
# =========================================================

@router.get("/outreach")
def get_outreach(
    db: Session = Depends(get_db),
):

    outreach_records = (
        db.query(Outreach)
        .order_by(Outreach.created_at.desc())
        .all()
    )

    return [
        {
            "id": outreach.id,
            "campaign_id": outreach.campaign_id,
            "college_id": outreach.college_id,
            "channel": outreach.channel,
            "recipient": outreach.recipient,
            "subject": outreach.subject,
            "message": outreach.message,
            "status": outreach.status,
            "scheduled_at": outreach.scheduled_at,
            "sent_at": outreach.sent_at,
            "response_received_at": (
                outreach.response_received_at
            ),
            "follow_up_count": (
                outreach.follow_up_count
            ),
            "last_error": outreach.last_error,
            "created_at": outreach.created_at,
        }
        for outreach in outreach_records
    ]


# =========================================================
# Get one outreach record
# =========================================================

@router.get("/outreach/{outreach_id}")
def get_outreach_by_id(
    outreach_id: int,
    db: Session = Depends(get_db),
):

    outreach = (
        db.query(Outreach)
        .filter(
            Outreach.id == outreach_id
        )
        .first()
    )

    if outreach is None:

        raise HTTPException(
            status_code=404,
            detail="Outreach record not found",
        )

    return {
        "id": outreach.id,
        "campaign_id": outreach.campaign_id,
        "college_id": outreach.college_id,
        "channel": outreach.channel,
        "recipient": outreach.recipient,
        "subject": outreach.subject,
        "message": outreach.message,
        "status": outreach.status,
        "scheduled_at": outreach.scheduled_at,
        "sent_at": outreach.sent_at,
        "response_received_at": (
            outreach.response_received_at
        ),
        "follow_up_count": (
            outreach.follow_up_count
        ),
        "last_error": outreach.last_error,
        "created_at": outreach.created_at,
    }


# =========================================================
# Check follow-up status and update database
# =========================================================

@router.get("/outreach/{outreach_id}/follow-up")
def check_follow_up(
    outreach_id: int,
    db: Session = Depends(get_db),
):

    outreach = (
        db.query(Outreach)
        .filter(
            Outreach.id == outreach_id
        )
        .first()
    )

    if outreach is None:

        raise HTTPException(
            status_code=404,
            detail="Outreach record not found",
        )

    # -----------------------------------------------------
    # If follow-up is already due, do not recalculate it
    # -----------------------------------------------------

    if outreach.status == "follow_up_due":

        if outreach.follow_up_count == 1:
            next_action = "send_follow_up_1"
        else:
            next_action = "send_follow_up_2"

        return {
            "outreach_id": outreach.id,
            "campaign_id": outreach.campaign_id,
            "college_id": outreach.college_id,
            "previous_status": outreach.status,
            "previous_follow_up_count": (
                outreach.follow_up_count
            ),
            "current_status": outreach.status,
            "follow_up_count": (
                outreach.follow_up_count
            ),
            "follow_up": {
                "status": "follow_up_due",
                "next_action": next_action,
                "follow_up_count": (
                    outreach.follow_up_count
                ),
            },
            "message": (
                "Follow-up is already due. "
                "Waiting for follow-up action."
            ),
        }

    # -----------------------------------------------------
    # Save current values
    # -----------------------------------------------------

    previous_status = outreach.status

    previous_follow_up_count = (
        outreach.follow_up_count
    )

    # -----------------------------------------------------
    # Run Outreach Orchestrator follow-up logic
    # -----------------------------------------------------

    orchestrator = OutreachOrchestratorAgent()

    follow_up_result = (
        orchestrator.calculate_follow_up(
            sent_at=outreach.sent_at,
            follow_up_count=(
                outreach.follow_up_count
            ),
            response_received=(
                outreach.response_received_at
                is not None
            ),
            opted_out=(
                outreach.status == "opted_out"
            ),
            max_follow_ups=2,
        )
    )

    # -----------------------------------------------------
    # Update database
    # -----------------------------------------------------

    new_status = follow_up_result.get(
        "status"
    )

    new_follow_up_count = (
        follow_up_result.get(
            "follow_up_count"
        )
    )

    if new_status:
        outreach.status = new_status

    if new_follow_up_count is not None:
        outreach.follow_up_count = (
            new_follow_up_count
        )

    # -----------------------------------------------------
    # Save changes
    # -----------------------------------------------------

    try:

        db.commit()
        db.refresh(outreach)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Follow-up was calculated but "
                f"database update failed: {str(exc)}"
            ),
        )

    # -----------------------------------------------------
    # Return result
    # -----------------------------------------------------

    return {
        "outreach_id": outreach.id,
        "campaign_id": outreach.campaign_id,
        "college_id": outreach.college_id,
        "previous_status": previous_status,
        "previous_follow_up_count": (
            previous_follow_up_count
        ),
        "current_status": outreach.status,
        "follow_up_count": (
            outreach.follow_up_count
        ),
        "follow_up": follow_up_result,
        "message": (
            "Follow-up status calculated "
            "and database updated successfully."
        ),
    }


# =========================================================
# Send follow-up
# =========================================================

@router.post("/outreach/{outreach_id}/send-follow-up")
def send_follow_up(
    outreach_id: int,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # Find outreach record
    # -----------------------------------------------------

    outreach = (
        db.query(Outreach)
        .filter(
            Outreach.id == outreach_id
        )
        .first()
    )

    if outreach is None:

        raise HTTPException(
            status_code=404,
            detail="Outreach record not found",
        )

    # -----------------------------------------------------
    # Follow-up must be due
    # -----------------------------------------------------

    if outreach.status != "follow_up_due":

        raise HTTPException(
            status_code=400,
            detail=(
                "Follow-up is not currently due. "
                f"Current status: {outreach.status}"
            ),
        )

    # -----------------------------------------------------
    # Check follow-up number
    # -----------------------------------------------------

    follow_up_count = (
        outreach.follow_up_count
    )

    if follow_up_count not in (1, 2):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid follow-up count. "
                "Expected 1 or 2."
            ),
        )

    # -----------------------------------------------------
    # IMPORTANT
    #
    # This is only a simulated send.
    # No real email, WhatsApp, LinkedIn,
    # or external API is called.
    # -----------------------------------------------------

    outreach.sent_at = datetime.utcnow()

    # -----------------------------------------------------
    # Follow-up 1
    # -----------------------------------------------------

    if follow_up_count == 1:

        outreach.status = "sent"

        next_action = "wait_for_response"

        message = (
            "Follow-up 1 marked as sent "
            "successfully. No real message was sent."
        )

    # -----------------------------------------------------
    # Follow-up 2
    # -----------------------------------------------------

    else:

        outreach.status = "completed"

        next_action = "stop_outreach"

        message = (
            "Follow-up 2 marked as completed. "
            "No further outreach will be performed."
        )

    # -----------------------------------------------------
    # Save changes
    # -----------------------------------------------------

    try:

        db.commit()
        db.refresh(outreach)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Follow-up state was not saved: "
                f"{str(exc)}"
            ),
        )

    # -----------------------------------------------------
    # Return result
    # -----------------------------------------------------

    return {
        "outreach_id": outreach.id,
        "campaign_id": outreach.campaign_id,
        "college_id": outreach.college_id,
        "status": outreach.status,
        "follow_up_count": (
            outreach.follow_up_count
        ),
        "sent_at": outreach.sent_at,
        "next_action": next_action,
        "message": message,
        "real_message_sent": False,
    }


# =========================================================
# Process outreach response
# =========================================================

@router.post("/outreach/{outreach_id}/response")
def process_outreach_response(
    outreach_id: int,
    request: OutreachResponseRequest,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # Find outreach record
    # -----------------------------------------------------

    outreach = (
        db.query(Outreach)
        .filter(
            Outreach.id == outreach_id
        )
        .first()
    )

    if outreach is None:

        raise HTTPException(
            status_code=404,
            detail="Outreach record not found",
        )

    # -----------------------------------------------------
    # Validate response
    # -----------------------------------------------------

    if not request.response_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Response text cannot be empty",
        )

    # -----------------------------------------------------
    # Convert database record to dictionary
    # -----------------------------------------------------

    outreach_data = {
        "id": outreach.id,
        "campaign_id": outreach.campaign_id,
        "college_id": outreach.college_id,
        "channel": outreach.channel,
        "recipient": outreach.recipient,
        "subject": outreach.subject,
        "message": outreach.message,
        "status": outreach.status,
        "scheduled_at": outreach.scheduled_at,
        "sent_at": outreach.sent_at,
        "response_received_at": (
            outreach.response_received_at
        ),
        "follow_up_count": (
            outreach.follow_up_count
        ),
        "last_error": outreach.last_error,
    }

    # -----------------------------------------------------
    # Process response
    # -----------------------------------------------------

    orchestrator = OutreachOrchestratorAgent()

    try:

        result = orchestrator.process_response(
            response_text=request.response_text,
            outreach=outreach_data,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Response processing failed: "
                f"{str(exc)}"
            ),
        )

    # -----------------------------------------------------
    # Get updated outreach data
    # -----------------------------------------------------

    updated_outreach = result.get(
        "outreach",
        {},
    )

    response_result = result.get(
        "response",
        {},
    )

    # -----------------------------------------------------
    # Update database record
    # -----------------------------------------------------

    if "status" in updated_outreach:

        outreach.status = (
            updated_outreach["status"]
        )

    if "response_received_at" in updated_outreach:

        outreach.response_received_at = (
            updated_outreach[
                "response_received_at"
            ]
        )

    if "follow_up_count" in updated_outreach:

        outreach.follow_up_count = (
            updated_outreach[
                "follow_up_count"
            ]
        )

    # -----------------------------------------------------
    # Save changes
    # -----------------------------------------------------

    try:

        db.commit()
        db.refresh(outreach)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Response was classified but "
                f"database update failed: {str(exc)}"
            ),
        )

    # -----------------------------------------------------
    # Return structured result
    # -----------------------------------------------------

    return {
        "outreach_id": outreach.id,
        "campaign_id": outreach.campaign_id,
        "college_id": outreach.college_id,

        "response": {
            "response_text": (
                request.response_text
            ),
            "response_category": (
                response_result.get(
                    "response_category"
                )
            ),
            "next_action": (
                response_result.get(
                    "next_action"
                )
            ),

            # -------------------------------------------------
            # New:
            # Prepared reply for interested responses
            # -------------------------------------------------

            "reply": (
                response_result.get(
                    "reply"
                )
            ),
        },

        "outreach": {
            "status": outreach.status,
            "follow_up_count": (
                outreach.follow_up_count
            ),
            "response_received_at": (
                outreach.response_received_at
            ),
        },

        "message": (
            "Response classified and "
            "outreach status updated successfully."
        ),
    }