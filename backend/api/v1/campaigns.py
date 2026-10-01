from fastapi import APIRouter, HTTPException, Request


from backend.services.campaign_service import CampaignService

from pydantic import BaseModel
from backend.services.campaign_review_service import CampaignReviewService
from backend.services.email_service import EmailService
from sqlalchemy.orm import Session
from backend.database.connection import engine
from backend.models import Campaign, College
from backend.agents.outreach_orchestrator_agent import (
    OutreachOrchestratorAgent,
)
from backend.agents.response_analysis_agent import ResponseAnalysisAgent
from backend.agents.state import AgentState
from backend.services.follow_up_service import FollowUpService
from datetime import datetime
from fastapi import File, UploadFile
from backend.models.campaign_call import CampaignCall
from backend.services.follow_up_date_service import FollowUpDateService
from backend.services.contact_discovery_service import (
    ContactDiscoveryService,
)

router = APIRouter()

campaign_service = CampaignService()
campaign_review_service = CampaignReviewService()
email_service = EmailService()
outreach_orchestrator = OutreachOrchestratorAgent()
response_analysis_agent = ResponseAnalysisAgent()
follow_up_service = FollowUpService()
contact_discovery_service = ContactDiscoveryService()

class CampaignApproveRequest(BaseModel):
    approved_by: str
    reason: str = ""


class CampaignRejectRequest(BaseModel):
    rejected_by: str
    reason: str = ""

class CampaignUpdateRequest(BaseModel):
    subject: str | None = None
    message: str | None = None
    channel: str | None = None
    priority: str | None = None

class CampaignCreateRequest(BaseModel):
    college_id: int
    campaign_type: str
    message_type: str
    channel: str
    subject: str | None = None
    message: str
    priority: str

class CampaignRecreateRequest(BaseModel):
    campaign_id: int

class CampaignInboundMessageRequest(BaseModel):
    sender_email: str
    recipient_email: str | None = None
    subject: str | None = None
    message: str

class MeetingConfirmationRequest(BaseModel):
    recipient_email: str
    subject: str
    message: str

class MeetingCreateRequest(BaseModel):
    response_action_id: int | None = None
    meeting_date: datetime
    duration_minutes: int = 30
    mode: str
    meeting_link: str | None = None


class MeetingRescheduleRequest(BaseModel):
    meeting_date: datetime
    duration_minutes: int = 30
    mode: str
    meeting_link: str | None = None


class CallCreateRequest(BaseModel):
    call_date: datetime
    duration_minutes: int = 30
    notes: str | None = None
    previous_call_id: int | None = None


class CallRescheduleRequest(BaseModel):

    call_date: datetime

    duration_minutes: int = 30

    notes: str | None = None


class ContactUpdateRequest(BaseModel):
    role: str
    email: str
    phone: str | None = None


@router.post("/campaigns")
def create_campaign(request: CampaignCreateRequest):
    try:
        campaign = campaign_service.create_campaign(
            campaign_data=request.model_dump()
        )

        return {
            "id": campaign.id,
            "college_id": campaign.college_id,
            "campaign_type": campaign.campaign_type,
            "message_type": campaign.message_type,
            "channel": campaign.channel,
            "subject": campaign.subject,
            "message": campaign.message,
            "priority": campaign.priority,
            "status": campaign.status,
            "required_approval": campaign.required_approval,
            "approved_at": campaign.approved_at,
            "created_at": campaign.created_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/campaigns")
def get_campaigns():
    try:
        campaigns = campaign_service.get_all_campaigns()

        return [
            {
                "id": campaign.id,
                "college_id": campaign.college_id,
                "campaign_type": campaign.campaign_type,
                "message_type": campaign.message_type,
                "channel": campaign.channel,
                "subject": campaign.subject,
                "message": campaign.message,
                "priority": campaign.priority,
                "status": campaign.status,
                "required_approval": campaign.required_approval,
                "approved_at": campaign.approved_at,
                "created_at": campaign.created_at,
            }
            for campaign in campaigns
        ]

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get("/campaigns/scheduler/status")
def get_scheduler_status(request: Request):
    scheduler = request.app.state.campaign_scheduler

    return {
        "status": "running" if scheduler.scheduler.running else "stopped",
        "scheduler": scheduler.get_status(),
    }

@router.get("/campaigns/status/{status}")
def get_campaigns_by_status(status: str):
    try:
        campaigns = campaign_service.get_campaigns_by_status(status)

        return [
            {
                "id": campaign.id,
                "college_id": campaign.college_id,
                "campaign_type": campaign.campaign_type,
                "message_type": campaign.message_type,
                "channel": campaign.channel,
                "subject": campaign.subject,
                "priority": campaign.priority,
                "status": campaign.status,
                "required_approval": campaign.required_approval,
                "approved_at": campaign.approved_at,
                "created_at": campaign.created_at,
            }
            for campaign in campaigns
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get("/campaigns/college/{college_id}")
def get_campaigns_by_college(
    college_id: int,
):
    try:

        campaigns = campaign_service.get_campaigns_by_college(
            college_id
        )

        return [
            {
                "id": campaign.id,
                "college_id": campaign.college_id,
                "campaign_type": campaign.campaign_type,
                "message_type": campaign.message_type,
                "channel": campaign.channel,
                "subject": campaign.subject,
                "message": campaign.message,
                "priority": campaign.priority,
                "status": campaign.status,
                "required_approval": campaign.required_approval,
                "approved_at": campaign.approved_at,
                "created_at": campaign.created_at,
            }
            for campaign in campaigns
        ]

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
    
@router.post("/campaigns/{campaign_id}/approve")
def approve_campaign(
    campaign_id: int,
    request: CampaignApproveRequest,
):
    try:
        # ----------------------------------
        # Human approval
        # ----------------------------------

        campaign = campaign_review_service.approve_campaign(
            campaign_id=campaign_id,
            approved_by=request.approved_by,
            reason=request.reason,
        )

        # ----------------------------------
        # Automatic outreach
        # ----------------------------------
        #
        # Currently EmailService is the only
        # implemented outreach channel.
        #
        # Other channels remain APPROVED until
        # their sending service is implemented.
        # ----------------------------------

        outreach_result = None

        if campaign.channel == "email":
            outreach_result = (
                outreach_orchestrator.process_campaign(
                    campaign.id
                )
            )

            # Re-read campaign because the
            # outreach process may have changed
            # its status.
            campaign = campaign_service.get_campaign(
                campaign.id
            )

        return {
            "id": campaign.id,
            "college_id": campaign.college_id,
            "campaign_type": campaign.campaign_type,
            "message_type": campaign.message_type,
            "channel": campaign.channel,
            "subject": campaign.subject,
            "priority": campaign.priority,
            "status": campaign.status,
            "required_approval": campaign.required_approval,
            "approved_at": campaign.approved_at,
            "created_at": campaign.created_at,
            "outreach": outreach_result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.post("/campaigns/bulk-approve")
def bulk_approve_campaigns():
    try:

        result = campaign_review_service.approve_all_pending_campaigns(
            approved_by="Naresh",
            reason="Bulk approved from Streamlit.",
        )

        return {
            "status": "success",
            **result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

# =========================================================
# Process All Approved Campaigns
# =========================================================

@router.post("/campaigns/bulk-approved-process")
def bulk_approved_process():
    try:
        results = outreach_orchestrator.process_approved_campaigns()

        sent_count = sum(
            1
            for result in results
            if result.get("status") == "sent"
        )

        failed_count = sum(
            1
            for result in results
            if result.get("status") == "failed"
        )

        return {
            "status": "success",
            "processed": len(results),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "results": results,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    try:
        campaign = campaign_service.get_campaign(campaign_id)

        return {
            "id": campaign.id,
            "college_id": campaign.college_id,
            "campaign_type": campaign.campaign_type,
            "message_type": campaign.message_type,
            "channel": campaign.channel,
            "subject": campaign.subject,
            "message": campaign.message,
            "priority": campaign.priority,
            "status": campaign.status,
            "required_approval": campaign.required_approval,
            "approved_at": campaign.approved_at,
            "created_at": campaign.created_at,
            "scheduled_at": campaign.scheduled_at,
            "sent_at": campaign.sent_at,
            "next_follow_up_at": campaign.next_follow_up_at,
            "follow_up_count": campaign.follow_up_count,
            "max_follow_ups": campaign.max_follow_ups,
            "last_response_at": campaign.last_response_at,
            "response_category": campaign.response_category,
            "contact_updated": campaign.contact_updated,
            "completed_at": campaign.completed_at,
            "failure_reason": campaign.failure_reason,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@router.get("/campaigns/{campaign_id}/history")
def get_campaign_history(campaign_id: int):
    try:
        history = campaign_service.get_campaign_history(
            campaign_id=campaign_id
        )

        return [
            {
                "id": item.id,
                "campaign_id": item.campaign_id,
                "status": item.status,
                "changed_at": item.changed_at,
                "changed_by": item.changed_by,
                "reason": item.reason,
            }
            for item in history
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@router.get("/campaigns/{campaign_id}/messages")
def get_campaign_messages(campaign_id: int):
    try:
        messages = campaign_service.get_campaign_messages(
            campaign_id=campaign_id
        )

        return [
            {
                "id": item.id,
                "campaign_id": item.campaign_id,
                "college_id": item.college_id,
                "direction": item.direction,
                "sender_email": item.sender_email,
                "recipient_email": item.recipient_email,
                "subject": item.subject,
                "message": item.message,
                "status": item.status,
                "sent_at": item.sent_at,
                "received_at": item.received_at,
                "created_at": item.created_at,
            }
            for item in messages
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post("/campaigns/{campaign_id}/reject")
def reject_campaign(
    campaign_id: int,
    request: CampaignRejectRequest,
):
    try:
        campaign = campaign_review_service.reject_campaign(
            campaign_id=campaign_id,
            rejected_by=request.rejected_by,
            reason=request.reason,
        )

        return {
            "id": campaign.id,
            "college_id": campaign.college_id,
            "campaign_type": campaign.campaign_type,
            "message_type": campaign.message_type,
            "channel": campaign.channel,
            "subject": campaign.subject,
            "priority": campaign.priority,
            "status": campaign.status,
            "required_approval": campaign.required_approval,
            "approved_at": campaign.approved_at,
            "created_at": campaign.created_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.patch("/campaigns/{campaign_id}/draft")
def update_campaign(
    campaign_id: int,
    request: CampaignUpdateRequest,
):
    try:
        campaign = campaign_service.update_campaign(
            campaign_id=campaign_id,
            subject=request.subject,
            message=request.message,
            channel=request.channel,
            priority=request.priority,
        )

        return {
            "id": campaign.id,
            "college_id": campaign.college_id,
            "campaign_type": campaign.campaign_type,
            "message_type": campaign.message_type,
            "channel": campaign.channel,
            "subject": campaign.subject,
            "message": campaign.message,
            "priority": campaign.priority,
            "status": campaign.status,
            "required_approval": campaign.required_approval,
            "approved_at": campaign.approved_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/campaigns/{campaign_id}/close")
def close_campaign(campaign_id: int):
    try:
        campaign = campaign_service.close_campaign(
            campaign_id
        )

        return {
            "id": campaign.id,
            "college_id": campaign.college_id,
            "campaign_type": campaign.campaign_type,
            "message_type": campaign.message_type,
            "channel": campaign.channel,
            "subject": campaign.subject,
            "priority": campaign.priority,
            "status": campaign.status,
            "required_approval": campaign.required_approval,
            "approved_at": campaign.approved_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    
@router.post("/campaigns/{campaign_id}/send")
def send_campaign(campaign_id: int):
    try:
        result = email_service.send_campaign_email(
            campaign_id=campaign_id
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.post(
    "/campaigns/{campaign_id}/send-confirmation"
)
def send_meeting_confirmation(
    campaign_id: int,
    request: MeetingConfirmationRequest,
):
    try:

        result = email_service.send_meeting_confirmation(
            campaign_id=campaign_id,
            recipient_email=request.recipient_email,
            subject=request.subject,
            message=request.message,
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
    
# ============================================================
# SEND INFORMATION PACKAGE [NEEDS INFORMATION]
# ============================================================

@router.post(
    "/campaigns/{campaign_id}/send-information"
)
def send_information_package(
    campaign_id: int,
):
    try:

        result = email_service.send_information_package(
            campaign_id=campaign_id,
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

# ==================================================
# Meeting lifecycle
# ==================================================

@router.post("/campaigns/{campaign_id}/meetings")
def schedule_meeting(
    campaign_id: int,
    request: MeetingCreateRequest,
):
    try:
        meeting = campaign_service.schedule_meeting(
            campaign_id=campaign_id,
            response_action_id=request.response_action_id,
            meeting_date=request.meeting_date,
            duration_minutes=request.duration_minutes,
            mode=request.mode,
            meeting_link=request.meeting_link,
        )

        return {
            "id": meeting.id,
            "campaign_id": meeting.campaign_id,
            "response_action_id": meeting.response_action_id,
            "meeting_date": meeting.meeting_date,
            "duration_minutes": meeting.duration_minutes,
            "mode": meeting.mode,
            "meeting_link": meeting.meeting_link,
            "status": meeting.status,
            "scheduled_at": meeting.scheduled_at,
            "cancelled_at": meeting.cancelled_at,
            "completed_at": meeting.completed_at,
            "created_at": meeting.created_at,
            "updated_at": meeting.updated_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/campaigns/{campaign_id}/meetings/current")
def get_current_meeting(
    campaign_id: int,
):
    try:
        meeting = campaign_service.get_current_meeting(
            campaign_id=campaign_id,
        )

        if meeting is None:
            return {
                "meeting": None,
            }

        return {
            "meeting": {
                "id": meeting.id,
                "campaign_id": meeting.campaign_id,
                "response_action_id": meeting.response_action_id,
                "meeting_date": meeting.meeting_date,
                "duration_minutes": meeting.duration_minutes,
                "mode": meeting.mode,
                "meeting_link": meeting.meeting_link,
                "status": meeting.status,
                "scheduled_at": meeting.scheduled_at,
                "cancelled_at": meeting.cancelled_at,
                "completed_at": meeting.completed_at,
                "created_at": meeting.created_at,
                "updated_at": meeting.updated_at,
            }
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.patch(
    "/campaigns/{campaign_id}/meetings/{meeting_id}/reschedule"
)
def reschedule_meeting(
    campaign_id: int,
    meeting_id: int,
    request: MeetingRescheduleRequest,
):
    try:
        meeting = campaign_service.reschedule_meeting(
            campaign_id=campaign_id,
            meeting_id=meeting_id,
            meeting_date=request.meeting_date,
            duration_minutes=request.duration_minutes,
            mode=request.mode,
            meeting_link=request.meeting_link,
        )

        return {
            "id": meeting.id,
            "campaign_id": meeting.campaign_id,
            "response_action_id": meeting.response_action_id,
            "meeting_date": meeting.meeting_date,
            "duration_minutes": meeting.duration_minutes,
            "mode": meeting.mode,
            "meeting_link": meeting.meeting_link,
            "status": meeting.status,
            "scheduled_at": meeting.scheduled_at,
            "cancelled_at": meeting.cancelled_at,
            "completed_at": meeting.completed_at,
            "created_at": meeting.created_at,
            "updated_at": meeting.updated_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/campaigns/{campaign_id}/meetings/{meeting_id}/cancel"
)
def cancel_meeting(
    campaign_id: int,
    meeting_id: int,
):
    try:
        meeting = campaign_service.cancel_meeting(
            campaign_id=campaign_id,
            meeting_id=meeting_id,
        )

        return {
            "id": meeting.id,
            "campaign_id": meeting.campaign_id,
            "response_action_id": meeting.response_action_id,
            "meeting_date": meeting.meeting_date,
            "duration_minutes": meeting.duration_minutes,
            "mode": meeting.mode,
            "meeting_link": meeting.meeting_link,
            "status": meeting.status,
            "scheduled_at": meeting.scheduled_at,
            "cancelled_at": meeting.cancelled_at,
            "completed_at": meeting.completed_at,
            "created_at": meeting.created_at,
            "updated_at": meeting.updated_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

# ============================================================
# DELETE MISSED / CANCELLED MEETING
# ============================================================

@router.delete(
    "/campaigns/{campaign_id}/meetings/{meeting_id}"
)
def delete_meeting(
    campaign_id: int,
    meeting_id: int,
):
    try:

        campaign_service.delete_meeting(
            campaign_id=campaign_id,
            meeting_id=meeting_id,
        )

        return {
            "message": "Meeting deleted successfully.",
            "campaign_id": campaign_id,
            "meeting_id": meeting_id,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
# ==================================================
# CALL lifecycle
# ==================================================

@router.post("/campaigns/{campaign_id}/calls")
def schedule_call(
    campaign_id: int,
    request: CallCreateRequest,
):

    try:

        response_action = (
            campaign_service.get_pending_response_action(
                campaign_id=campaign_id,
                response_category="REQUEST_CALL",
            )
        )

        if response_action is None:
            raise ValueError(
                "No pending REQUEST_CALL response action found "
                f"for campaign {campaign_id}."
            )

        call = campaign_service.schedule_call(
            campaign_id=campaign_id,
            response_action_id=response_action.id,
            call_date=request.call_date,
            duration_minutes=request.duration_minutes,
            notes=request.notes,
        )

        return {
            "campaign_id": campaign_id,
            "call": {
                "id": call.id,
                "call_date": call.call_date,
                "duration_minutes": call.duration_minutes,
                "status": call.status,
                "notes": call.notes,
                "scheduled_at": call.scheduled_at,
            },
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get("/campaigns/{campaign_id}/calls/current")
def get_current_call(campaign_id: int):

    try:

        call = campaign_service.get_current_call(
            campaign_id=campaign_id
        )

        pending_action = (
            campaign_service.get_pending_response_action(
                campaign_id=campaign_id,
                response_category="REQUEST_CALL",
            )
        )

        response = {
            "campaign_id": campaign_id,
            "pending_request_call": (
                pending_action is not None
            ),
            "response_action": None,
            "call": None,
        }

        # -----------------------------------------------
        # Pending REQUEST_CALL
        # -----------------------------------------------

        if pending_action is not None:

            response["response_action"] = {
                "id": pending_action.id,
                "response_category": (
                    pending_action.response_category
                ),
                "action_type": pending_action.action_type,
                "action_status": pending_action.action_status,
                "created_at": pending_action.created_at,
                "completed_at": pending_action.completed_at,
            }

        # -----------------------------------------------
        # Current / latest call
        # -----------------------------------------------

        if call is not None:

            response["call"] = {
                "id": call.id,
                "call_date": call.call_date,
                "duration_minutes": call.duration_minutes,
                "status": call.status,
                "notes": call.notes,
                "scheduled_at": call.scheduled_at,
                "cancelled_at": call.cancelled_at,
                "completed_at": call.completed_at,
            }

        return response

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.post("/campaigns/{campaign_id}/calls/schedule-new")
def schedule_new_call(
    campaign_id: int,
    request: CallCreateRequest,
):
    try:
        call = campaign_service.schedule_new_call(
            campaign_id=campaign_id,
            previous_call_id=request.previous_call_id,
            call_date=request.call_date,
            duration_minutes=request.duration_minutes,
            notes=request.notes,
        )

        return {
            "campaign_id": campaign_id,
            "previous_call_id": request.previous_call_id,
            "call": {
                "id": call.id,
                "call_date": call.call_date,
                "duration_minutes": call.duration_minutes,
                "status": call.status,
                "notes": call.notes,
                "scheduled_at": call.scheduled_at,
                "cancelled_at": call.cancelled_at,
                "completed_at": call.completed_at,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post("/campaigns/{campaign_id}/calls/{call_id}/reschedule")
def reschedule_call(
    campaign_id: int,
    call_id: int,
    request: CallRescheduleRequest,
):
    try:
        call = campaign_service.reschedule_call(
            campaign_id=campaign_id,
            call_id=call_id,
            call_date=request.call_date,
            duration_minutes=request.duration_minutes,
            notes=request.notes,
        )

        return {
            "campaign_id": campaign_id,
            "call": {
                "id": call.id,
                "call_date": call.call_date,
                "duration_minutes": call.duration_minutes,
                "status": call.status,
                "notes": call.notes,
                "scheduled_at": call.scheduled_at,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post("/campaigns/{campaign_id}/calls/{call_id}/cancel")
def cancel_call(
    campaign_id: int,
    call_id: int,
):
    try:
        call = campaign_service.cancel_call(
            campaign_id=campaign_id,
            call_id=call_id,
        )

        return {
            "campaign_id": campaign_id,
            "call": {
                "id": call.id,
                "call_date": call.call_date,
                "duration_minutes": call.duration_minutes,
                "status": call.status,
                "notes": call.notes,
                "cancelled_at": call.cancelled_at,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    
@router.post("/campaigns/follow-ups/process")
def process_due_followups():

    try:
        results = follow_up_service.process_due_followups()

        return {
            "status": "success",
            "processed": len(results),
            "results": results,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.post("/campaigns/{campaign_id}/messages/inbound")
def add_inbound_message(
    campaign_id: int,
    request: CampaignInboundMessageRequest,
):
    try:
        # --------------------------------------------------
        # 1. Save incoming message
        # --------------------------------------------------

        conversation = campaign_service.add_inbound_message(
            campaign_id=campaign_id,
            sender_email=request.sender_email,
            recipient_email=request.recipient_email,
            subject=request.subject,
            message=request.message,
        )

        # --------------------------------------------------
        # 2. Response Analysis
        # --------------------------------------------------

        state = AgentState()

        state.incoming_response = request.message

        print("DEBUG INBOUND MESSAGE:", request.message)

        state = response_analysis_agent.execute(state)

        print(
            "DEBUG RESPONSE CATEGORY:",
            state.response_category
        )

        print(
            "DEBUG NEXT ACTION:",
            state.next_action
        )


        if state.status == "failed":
            raise ValueError(
                f"Response analysis failed: {state.error}"
            )

        response_category = state.response_category
        next_action = state.next_action
        follow_up_hint = getattr(
            state,
            "follow_up_hint",
            "none",
        )

        # --------------------------------------------------
        # Calculate automatic follow-up date
        # Only ASK_LATER and OUT_OF_OFFICE use this.
        # --------------------------------------------------

        next_follow_up_at = None

        if response_category in {
            "ASK_LATER",
            "OUT_OF_OFFICE",
        }:
            next_follow_up_at = (
                FollowUpDateService.calculate_follow_up_at(
                    follow_up_hint=follow_up_hint,
                )
            )

            print(
                "DEBUG FOLLOW-UP HINT:",
                follow_up_hint,
            )

            print(
                "DEBUG NEXT FOLLOW-UP AT:",
                next_follow_up_at,
            )

        # --------------------------------------------------
        # 3. Persist response analysis
        # --------------------------------------------------

        if response_category == "NOT_INTERESTED":

            campaign = campaign_service.update_response_analysis(
                campaign_id=campaign_id,
                response_category=response_category,
                next_action="CLOSE_CAMPAIGN",
                next_follow_up_at=None,
            )

            campaign = campaign_service.close_campaign(
                campaign_id=campaign_id,
                reason="Automatically completed because the college is not interested.",
            )

        else:

            campaign = campaign_service.update_response_analysis(
                campaign_id=campaign_id,
                response_category=response_category,
                next_action=next_action,
                next_follow_up_at=next_follow_up_at,
            )

        # --------------------------------------------------
        # 4. Return inbound message + analysis
        # --------------------------------------------------

        return {
            "id": conversation.id,
            "campaign_id": conversation.campaign_id,
            "college_id": conversation.college_id,
            "direction": conversation.direction,
            "sender_email": conversation.sender_email,
            "recipient_email": conversation.recipient_email,
            "subject": conversation.subject,
            "message": conversation.message,
            "status": conversation.status,
            "received_at": conversation.received_at,
            "created_at": conversation.created_at,

            "response_analysis": {
                "response_category": response_category,
                "next_action": next_action,
                "follow_up_hint": follow_up_hint,
            },

            "campaign": {
                "status": campaign.status,
                "response_category": campaign.response_category,
                "last_response_at": campaign.last_response_at,
                "next_follow_up_at": campaign.next_follow_up_at,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: int):
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)

        if campaign is None:
            raise HTTPException(
                status_code=404,
                detail="Campaign not found",
            )

        session.delete(campaign)
        session.commit()

        return {
            "message": "Campaign deleted successfully",
            "campaign_id": campaign_id,
        }

@router.post("/campaigns/recreate")
def recreate_campaign(request: CampaignRecreateRequest):

    with Session(engine) as session:

        old_campaign = session.get(Campaign, request.campaign_id)

        if old_campaign is None:
            raise HTTPException(
                status_code=404,
                detail="Campaign not found",
            )

        if old_campaign.status not in {
            "closed",
            "completed",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only completed campaigns can be recreated."
                ),
            )

        college_id = old_campaign.college_id

        new_campaign_data = {
            "college_id": college_id,
            "campaign_type": old_campaign.campaign_type,
            "message_type": old_campaign.message_type,
            "channel": old_campaign.channel,
            "subject": old_campaign.subject,
            "message": old_campaign.message,
            "priority": old_campaign.priority,
        }

    try:
        campaign = CampaignService().create_campaign(
            new_campaign_data
        )

        return {
            "message": "New campaign draft created successfully.",
            "old_campaign_id": old_campaign.id,
            "new_campaign_id": campaign.id,
            "status": campaign.status,
            "college_id": college_id,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

# ==================================================
# sending the proposal API
# ==================================================
@router.post(
    "/campaigns/{campaign_id}/send-proposal"
)
async def send_proposal(
    campaign_id: int,
    proposal_file: UploadFile = File(...),
):

    try:

        file_bytes = await proposal_file.read()

        if not file_bytes:
            raise ValueError(
                "Proposal file is empty."
            )

        result = email_service.send_proposal_email(
            campaign_id=campaign_id,
            attachment_bytes=file_bytes,
            attachment_filename=proposal_file.filename,
            attachment_content_type=(
                proposal_file.content_type
                or "application/pdf"
            ),
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get(
    "/campaigns/{campaign_id}/response-actions/latest/{response_category}"
)
def get_latest_response_action(
    campaign_id: int,
    response_category: str,
):
    try:

        action = campaign_service.get_latest_response_action(
            campaign_id=campaign_id,
            response_category=response_category,
        )

        if action is None:
            return {
                "campaign_id": campaign_id,
                "response_action": None,
            }

        return {
            "campaign_id": campaign_id,
            "response_action": {
                "id": action.id,
                "response_category": action.response_category,
                "action_type": action.action_type,
                "action_status": action.action_status,
                "created_at": action.created_at,
                "completed_at": action.completed_at,
            },
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/campaigns/{campaign_id}/calls/{call_id}/confirmation"
)
def send_call_confirmation(
    campaign_id: int,
    call_id: int,
):
    try:
        result = campaign_service.send_call_confirmation(
            campaign_id=campaign_id,
            call_id=call_id,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get(
    "/campaigns/{campaign_id}/calls/{call_id}/confirmation-status"
)
def get_call_confirmation_status(
    campaign_id: int,
    call_id: int,
):
    try:
        call = campaign_service.get_call(
            campaign_id=campaign_id,
            call_id=call_id,
        )

        confirmation_sent = (
            call.confirmation_sent_at is not None
        )

        return {
            "campaign_id": campaign_id,
            "call_id": call_id,
            "confirmation_sent": confirmation_sent,
            "confirmation_sent_at": call.confirmation_sent_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/campaigns/{campaign_id}/find-contact"
)
def find_contact_for_campaign(
    campaign_id: int,
):
    try:

        # ----------------------------------
        # Get campaign
        # ----------------------------------

        campaign = campaign_service.get_campaign(
            campaign_id
        )

        # ----------------------------------
        # Get college
        # ----------------------------------

        with Session(engine) as session:

            college = session.get(
                College,
                campaign.college_id,
            )

            if college is None:
                raise ValueError(
                    f"College not found: {campaign.college_id}"
                )

        # ----------------------------------
        # Get latest inbound message
        # ----------------------------------

        messages = campaign_service.get_campaign_messages(
            campaign_id
        )

        inbound_messages = [
            message
            for message in messages
            if message.direction == "inbound"
        ]

        if not inbound_messages:
            raise ValueError(
                "No inbound response found for this campaign."
            )

        latest_inbound = inbound_messages[-1]

        # ----------------------------------
        # Extract requested role
        # ----------------------------------

        requested_role = (
            contact_discovery_service.extract_requested_role(
                latest_inbound.message
            )
        )

        if not requested_role:
            return {
                "status": "not_found",
                "campaign_id": campaign_id,
                "college_id": campaign.college_id,
                "requested_role": None,
                "contact": None,
                "message": (
                    "The requested contact role "
                    "could not be identified."
                ),
            }

        # ----------------------------------
        # Existing contact
        # ----------------------------------

        existing_contact = {
            "role": (
                college.contact_role.get("value")
                if isinstance(
                    college.contact_role,
                    dict,
                )
                else None
            ),
            "email": (
                college.official_email.get("value")
                if isinstance(
                    college.official_email,
                    dict,
                )
                else None
            ),
            "phone": (
                college.official_phone.get("value")
                if isinstance(
                    college.official_phone,
                    dict,
                )
                else None
            ),
        }

        # ----------------------------------
        # Official domain
        # ----------------------------------

        official_domain = college.website

        # ----------------------------------
        # Find new contact
        # ----------------------------------

        result = contact_discovery_service.find_new_contact(
            college_name=college.name,
            state=college.state,
            official_domain=official_domain,
            requested_role=requested_role,
            existing_contact=existing_contact,
        )

        return {
            "campaign_id": campaign_id,
            "college_id": college.id,
            "college_name": college.name,
            "requested_role": requested_role,
            "current_contact": existing_contact,
            "result": result,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post(
    "/campaigns/{campaign_id}/update-contact"
)
def update_campaign_contact(
    campaign_id: int,
    request: ContactUpdateRequest,
):
    try:

        college = campaign_service.update_college_contact(
            campaign_id=campaign_id,
            role=request.role,
            email=request.email,
            phone=request.phone,
        )

        return {
            "status": "success",
            "message": "College contact updated successfully.",
            "campaign_id": campaign_id,
            "college_id": college.id,
            "contact": {
                "role": (
                    college.contact_role.get("value")
                    if isinstance(
                        college.contact_role,
                        dict,
                    )
                    else None
                ),
                "email": (
                    college.official_email.get("value")
                    if isinstance(
                        college.official_email,
                        dict,
                    )
                    else None
                ),
                "phone": (
                    college.official_phone.get("value")
                    if isinstance(
                        college.official_phone,
                        dict,
                    )
                    else None
                ),
            },
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/campaigns/{campaign_id}/create-new-contact-campaign")
def create_new_contact_campaign(campaign_id: int):

    try:

        # ----------------------------------
        # Get the previous campaign
        # ----------------------------------

        old_campaign = campaign_service.get_campaign(campaign_id)

        if old_campaign is None:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}",
            )

        # ----------------------------------
        # Validate contact update
        # ----------------------------------

        if not old_campaign.contact_updated:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The contact has not been updated yet. "
                    "Update the contact before creating a new campaign."
                ),
            )

        # ----------------------------------
        # Only WRONG_CONTACT campaigns
        # ----------------------------------

        if old_campaign.response_category != "WRONG_CONTACT":
            raise HTTPException(
                status_code=400,
                detail=(
                    "A new contact campaign can only be created "
                    "from a WRONG_CONTACT campaign."
                ),
            )

        # ----------------------------------
        # Create new campaign
        # ----------------------------------

        campaign_data = {
            "college_id": old_campaign.college_id,
            "campaign_type": old_campaign.campaign_type,
            "message_type": "initial_outreach",
            "channel": old_campaign.channel,
            "subject": old_campaign.subject,
            "message": old_campaign.message,
            "priority": old_campaign.priority,
        }

        new_campaign = campaign_service.create_campaign(
            campaign_data
        )

        return {
            "status": "success",
            "message": "New campaign created successfully.",
            "previous_campaign_id": old_campaign.id,
            "new_campaign_id": new_campaign.id,
            "college_id": new_campaign.college_id,
            "campaign": {
                "id": new_campaign.id,
                "status": new_campaign.status,
                "campaign_type": new_campaign.campaign_type,
                "message_type": new_campaign.message_type,
                "channel": new_campaign.channel,
                "subject": new_campaign.subject,
                "priority": new_campaign.priority,
            },
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )





