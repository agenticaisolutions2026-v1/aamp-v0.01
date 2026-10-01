from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import (
    Campaign,
    CampaignStatusHistory,
    ConversationMessage,
    College,
)
from backend.models.campaign_response_action import CampaignResponseAction
from backend.models.campaign_meeting import CampaignMeeting
from backend.models.campaign_call import CampaignCall

class CampaignService:
    """
    Persists and manages campaign records.

    Responsibilities:
        - Create campaign drafts
        - Read campaign records
        - Update editable drafts
        - Manage campaign status/history
        - Store inbound conversation messages

    This service does NOT:
        - Approve campaigns
        - Send campaigns
        - Schedule background jobs
    """

    # ==================================================
    # Campaign lifecycle
    # ==================================================

    CAMPAIGN_STATUSES = {
        "draft",
        "pending_approval",
        "approved",
        "queued",
        "sent",
        "delivered",
        "replied",
        "follow_up_due",
        "proposal",
        "completed",
        "failed",
        "opted_out",

        # Legacy statuses kept temporarily so that
        # existing API/UI behavior is not broken.
        "rejected",
        "closed",
    }

    # Campaigns in these states should prevent creation
    # of another active initial outreach campaign.
    ACTIVE_CAMPAIGN_STATUSES = {
        "draft",
        "pending_approval",
        "approved",
        "queued",
        "sent",
        "delivered",
        "replied",
        "follow_up_due",
        "proposal",
    }

    # ==================================================
    # Status history
    # ==================================================

    def _add_status_history(
        self,
        session: Session,
        campaign: Campaign,
        status: str,
        changed_by: str | None = None,
        reason: str | None = None,
    ) -> None:

        history = CampaignStatusHistory(
            campaign_id=campaign.id,
            status=status,
            changed_at=datetime.now(timezone.utc),
            changed_by=changed_by,
            reason=reason,
        )

        session.add(history)

    # ==================================================
    # Create campaign
    # ==================================================

    def create_campaign(self, campaign_data: dict) -> Campaign:
        """
        Create a new campaign in DRAFT status.

        Human approval is required before outreach.

        This method is used by:
            1. Automatic qualified-lead workflow
            2. Manual Create Campaign workflow
        """

        required_fields = [
            "college_id",
            "campaign_type",
            "message_type",
            "channel",
            "subject",
            "message",
            "priority",
        ]

        # ----------------------------------
        # Validate required fields
        # ----------------------------------

        for field in required_fields:
            if campaign_data.get(field) is None:
                raise ValueError(
                    f"Missing required campaign field: {field}"
                )

        college_id = campaign_data["college_id"]
        message_type = campaign_data["message_type"]

        with Session(engine) as session:

            # ----------------------------------
            # Prevent duplicate active initial outreach
            # ----------------------------------

            if message_type == "initial_outreach":

                existing_campaign = session.scalar(
                    select(Campaign).where(
                        Campaign.college_id == college_id,
                        Campaign.message_type == "initial_outreach",
                        Campaign.status.in_(
                            self.ACTIVE_CAMPAIGN_STATUSES
                        ),
                    )
                )

                if existing_campaign is not None:

                    if not existing_campaign.contact_updated:

                        raise ValueError(
                            "An active initial outreach campaign "
                            f"already exists for college_id "
                            f"{college_id} "
                            f"(campaign_id={existing_campaign.id}, "
                            f"status={existing_campaign.status})."
                        )

            # ----------------------------------
            # Create campaign
            # ----------------------------------

            campaign = Campaign(
                college_id=college_id,
                campaign_type=campaign_data["campaign_type"],
                message_type=message_type,
                channel=campaign_data["channel"],
                subject=campaign_data.get("subject"),
                message=campaign_data["message"],
                priority=campaign_data["priority"],

                # New campaigns always start here.
                status="draft",

                required_approval=True,
                approved_at=None,

                # Automation fields
                scheduled_at=None,
                sent_at=None,
                next_follow_up_at=None,
                follow_up_count=0,
                max_follow_ups=2,
                last_response_at=None,
                response_category=None,
                contact_updated=False,
                completed_at=None,
                failure_reason=None,

                created_at=datetime.now(timezone.utc),
            )

            session.add(campaign)
            session.flush()

            # ----------------------------------
            # Record initial status
            # ----------------------------------

            self._add_status_history(
                session=session,
                campaign=campaign,
                status="draft",
                reason="Campaign created.",
            )

            session.commit()
            session.refresh(campaign)

            return campaign

    # ==================================================
    # Get one campaign
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
    # Get all campaigns
    # ==================================================

    def get_all_campaigns(self) -> list[Campaign]:

        with Session(engine) as session:

            campaigns = session.scalars(
                select(Campaign).order_by(
                    Campaign.created_at.desc()
                )
            ).all()

            return list(campaigns)

    # ==================================================
    # Get campaigns by status
    # ==================================================

    def get_campaigns_by_status(
        self,
        status: str,
    ) -> list[Campaign]:

        status = status.strip().lower()

        if status not in self.CAMPAIGN_STATUSES:
            valid_statuses = ", ".join(
                sorted(self.CAMPAIGN_STATUSES)
            )

            raise ValueError(
                "Invalid campaign status. "
                f"Use one of: {valid_statuses}."
            )

        with Session(engine) as session:

            campaigns = session.scalars(
                select(Campaign)
                .where(
                    Campaign.status == status
                )
                .order_by(
                    Campaign.created_at.desc()
                )
            ).all()

            return list(campaigns)

    # ==================================================
    # Update campaign
    # ==================================================

    def update_campaign(
        self,
        campaign_id: int,
        subject: str | None = None,
        message: str | None = None,
        channel: str | None = None,
        priority: str | None = None,
    ) -> Campaign:

        with Session(engine) as session:

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign with id {campaign_id} not found."
                )

            # ----------------------------------
            # Only DRAFT campaigns can be edited
            # ----------------------------------

            if campaign.status != "draft":
                raise ValueError(
                    "Only draft campaigns can be edited."
                )

            # ----------------------------------
            # Subject
            # ----------------------------------

            if subject is not None:
                campaign.subject = subject.strip()

            # ----------------------------------
            # Message
            # ----------------------------------

            if message is not None:
                campaign.message = message.strip()

            # ----------------------------------
            # Channel
            # ----------------------------------

            if channel is not None:

                channel = channel.strip().lower()

                valid_channels = {
                    "email",
                    "whatsapp",
                    "contact_form",
                    "linkedin",
                    "phone",
                    "no_channel",
                }

                if channel not in valid_channels:
                    raise ValueError(
                        "Invalid channel."
                    )

                campaign.channel = channel

            # ----------------------------------
            # Priority
            # ----------------------------------

            if priority is not None:

                priority = priority.strip().lower()

                valid_priorities = {
                    "high",
                    "medium",
                    "low",
                }

                if priority not in valid_priorities:
                    raise ValueError(
                        "Invalid priority. "
                        "Use high, medium, or low."
                    )

                campaign.priority = priority

            session.commit()
            session.refresh(campaign)

            return campaign

    # ==================================================
    # Close campaign
    # ==================================================

    def close_campaign(
        self,
        campaign_id: int,
        reason: str = "Campaign manually completed.",
    ) -> Campaign:

        with Session(engine) as session:

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign with id {campaign_id} not found."
                )

            if campaign.status not in {
                "sent",
                "delivered",
                "replied",
                "proposal",
            }:
                raise ValueError(
                    "Only sent, delivered, replied, or "
                    "proposal campaigns can be closed."
                )

            now = datetime.now(timezone.utc)

            campaign.status = "completed"
            campaign.completed_at = now
            campaign.next_follow_up_at = None

            self._add_status_history(
                session=session,
                campaign=campaign,
                status="completed",
                reason=reason,
            )

            session.commit()
            session.refresh(campaign)

            return campaign

    # ==================================================
    # Add inbound message
    # ==================================================

    def add_inbound_message(
        self,
        campaign_id: int,
        sender_email: str,
        recipient_email: str | None,
        subject: str | None,
        message: str,
    ) -> ConversationMessage:

        if not sender_email or not sender_email.strip():
            raise ValueError(
                "sender_email is required."
            )

        if not message or not message.strip():
            raise ValueError(
                "message is required."
            )

        with Session(engine) as session:

            # ----------------------------------
            # Get campaign
            # ----------------------------------

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
            # Only outreach campaigns can receive
            # an inbound reply.
            # ----------------------------------

            allowed_reply_statuses = {
                "sent",
                "delivered",
                "follow_up_due",
                "replied"
            }

            if campaign.status not in allowed_reply_statuses:
                raise ValueError(
                    "Only sent, delivered, or follow-up-due "
                    "campaigns can receive an inbound reply. "
                    f"Campaign {campaign_id} has status "
                    f"'{campaign.status}'."
                )

            # ----------------------------------
            # Create inbound message
            # ----------------------------------

            now = datetime.now(timezone.utc)

            conversation = ConversationMessage(
                campaign_id=campaign.id,
                college_id=campaign.college_id,
                direction="inbound",
                sender_email=sender_email.strip(),
                recipient_email=(
                    recipient_email.strip()
                    if recipient_email
                    else None
                ),
                subject=(
                    subject.strip()
                    if subject
                    else None
                ),
                message=message.strip(),
                status="unread",
                received_at=now,
                created_at=now,
            )

            session.add(conversation)

            # ----------------------------------
            # Update campaign response state
            # ----------------------------------

            campaign.status = "replied"
            campaign.last_response_at = now

            # Response category is intentionally NOT
            # classified here.
            #
            # A future response-analysis component will
            # set:
            #
            # INTERESTED
            # NOT_INTERESTED
            # NEEDS_INFORMATION
            # REQUEST_CALLBACK
            # WRONG_CONTACT
            # OPT_OUT
            # UNKNOWN

            history = CampaignStatusHistory(
                campaign_id=campaign.id,
                status="replied",
                changed_at=now,
                changed_by=sender_email.strip(),
                reason="Inbound reply received.",
            )

            session.add(history)

            session.commit()
            session.refresh(conversation)

            return conversation

    # ==================================================
    # Update response analysis
    # ==================================================

    def update_response_analysis(
        self,
        campaign_id: int,
        response_category: str,
        next_action: str,
        next_follow_up_at: datetime | None = None,
    ) -> Campaign:

        with Session(engine) as session:

            # ----------------------------------
            # Get campaign
            # ----------------------------------

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
            # Validate response category
            # ----------------------------------

            valid_categories = {
                "REQUEST_PROPOSAL",
                "REQUEST_MEETING",
                "REQUEST_CALL",
                "NEEDS_INFORMATION",
                "INTERESTED",
                "ASK_LATER",
                "NOT_INTERESTED",
                "WRONG_CONTACT",
                "OUT_OF_OFFICE",
                "UNCLEAR",
                "OPT_OUT",
            }

            response_category = (
                response_category.strip().upper()
            )

            if response_category not in valid_categories:
                raise ValueError(
                    "Invalid response category: "
                    f"{response_category}"
                )

            # ----------------------------------
            # Save response analysis
            # ----------------------------------

            campaign.response_category = (
                response_category
            )

            # ----------------------------------
            # Response received means:
            # stop follow-up automation
            # ----------------------------------

            # ----------------------------------
            # Follow-up scheduling
            # ----------------------------------
            # ASK_LATER and OUT_OF_OFFICE may
            # schedule a new automatic follow-up.
            #
            # All other response categories clear
            # the previous follow-up schedule.
            # ----------------------------------

            if response_category in {
                "ASK_LATER",
                "OUT_OF_OFFICE",
            }:
                campaign.next_follow_up_at = (
                    next_follow_up_at
                )
            else:
                campaign.next_follow_up_at = None

            # ----------------------------------
            # Apply campaign lifecycle status
            # ----------------------------------

            if response_category == "OPT_OUT":

                campaign.status = "opted_out"

            else:

                campaign.status = "replied"

            # ----------------------------------
            # Record status history only if
            # response analysis changed the
            # campaign lifecycle status
            # ----------------------------------

            if campaign.status != "replied":

                self._add_status_history(
                    session=session,
                    campaign=campaign,
                    status=campaign.status,
                    changed_by="response_analysis_agent",
                    reason=(
                        f"Response classified as "
                        f"{response_category}; "
                        f"next action: {next_action}."
                    ),
                )

            # ----------------------------------
            # Create response action
            # ----------------------------------

            response_action = CampaignResponseAction(
                campaign_id=campaign.id,
                response_category=response_category,
                action_type=next_action,
                action_status="PENDING",
            )

            session.add(response_action)

            # ----------------------------------
            # Commit
            # ----------------------------------

            session.commit()
            session.refresh(campaign)

            return campaign
    # ==================================================
    # Get campaigns by college
    # ==================================================

    def get_campaigns_by_college(
        self,
        college_id: int,
    ) -> list[Campaign]:

        with Session(engine) as session:

            statement = (
                select(Campaign)
                .where(
                    Campaign.college_id == college_id
                )
                .order_by(
                    Campaign.created_at.desc()
                )
            )

            return session.execute(
                statement
            ).scalars().all()

    # ==================================================
    # Get campaign history
    # ==================================================

    def get_campaign_history(
        self,
        campaign_id: int,
    ) -> list[CampaignStatusHistory]:

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

            return list(
                session.scalars(
                    select(CampaignStatusHistory)
                    .where(
                        CampaignStatusHistory.campaign_id
                        == campaign_id
                    )
                    .order_by(
                        CampaignStatusHistory.changed_at
                    )
                )
            )

    # ==================================================
    # Get campaign messages
    # ==================================================

    def get_campaign_messages(
        self,
        campaign_id: int,
    ) -> list[ConversationMessage]:

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

            return list(
                session.scalars(
                    select(ConversationMessage)
                    .where(
                        ConversationMessage.campaign_id
                        == campaign_id
                    )
                    .order_by(
                        ConversationMessage.created_at
                    )
                )
            )

    # ==================================================
    # Meeting lifecycle
    # ==================================================

    def schedule_meeting(
        self,
        campaign_id: int,
        response_action_id: int | None,
        meeting_date: datetime,
        duration_minutes: int,
        mode: str,
        meeting_link: str | None = None,
    ) -> CampaignMeeting:

        if duration_minutes <= 0:
            raise ValueError("Meeting duration must be greater than 0 minutes.")
        
        now = datetime.now(timezone.utc)

        if meeting_date <= now:
            raise ValueError(
                "Meeting date and time must be in the future."
            )

        mode = mode.strip().lower()

        valid_modes = {
            "online",
            "in-person",
        }

        if mode not in valid_modes:
            raise ValueError(
                "Invalid meeting mode. Use online or in-person."
            )

        if mode == "online" and not meeting_link:
            raise ValueError(
                "Meeting link is required for online meetings."
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
            # Make sure there is no active meeting
            # ----------------------------------

            active_meeting = session.scalar(
                select(CampaignMeeting)
                .where(
                    CampaignMeeting.campaign_id == campaign_id,
                    CampaignMeeting.status == "SCHEDULED",
                )
                .order_by(
                    CampaignMeeting.meeting_date.desc()
                )
            )

            if active_meeting is not None:

                meeting_end = (
                    active_meeting.meeting_date
                    + timedelta(
                        minutes=active_meeting.duration_minutes
                    )
                )

                now = datetime.now(timezone.utc)

                # Existing meeting is still active.
                if now < meeting_end:
                    raise ValueError(
                        "An active meeting is already scheduled "
                        f"for campaign {campaign_id}."
                    )

                # Existing meeting has passed.
                active_meeting.status = "COMPLETED"
                active_meeting.completed_at = now

            # ----------------------------------
            # Create meeting
            # ----------------------------------

            now = datetime.now(timezone.utc)

            meeting = CampaignMeeting(
                campaign_id=campaign_id,
                response_action_id=response_action_id,
                meeting_date=meeting_date,
                duration_minutes=duration_minutes,
                mode=mode,
                meeting_link=meeting_link.strip()
                if meeting_link
                else None,
                status="SCHEDULED",
                scheduled_at=now,
                created_at=now,
                updated_at=now,
            )

            session.add(meeting)

            # ----------------------------------
            # Mark response action as completed
            # ----------------------------------

            if response_action_id is not None:

                response_action = session.scalar(
                    select(CampaignResponseAction).where(
                        CampaignResponseAction.id
                        == response_action_id
                    )
                )

                if response_action is not None:
                    response_action.action_status = "COMPLETED"
                    response_action.completed_at = now

            session.commit()
            session.refresh(meeting)

            return meeting

    # ==================================================
    # Get current meeting
    # ==================================================

    def get_current_meeting(
        self,
        campaign_id: int,
    ) -> CampaignMeeting | None:

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

            meeting = session.scalar(
                select(CampaignMeeting)
                .where(
                    CampaignMeeting.campaign_id == campaign_id,
                )
                .order_by(
                    CampaignMeeting.created_at.desc()
                )
            )

            if meeting is None:
                return None

            # ----------------------------------
            # Automatically recognize expired
            # meeting
            # ----------------------------------

            now = datetime.now(timezone.utc)

            meeting_end = (
                meeting.meeting_date
                + timedelta(
                    minutes=meeting.duration_minutes
                )
            )

            if now >= meeting_end:

                meeting.status = "MISSED"
                meeting.completed_at = None
                meeting.updated_at = now

                session.commit()
                session.refresh(meeting)

            return meeting

    # ==================================================
    # Reschedule meeting
    # ==================================================

    def reschedule_meeting(
        self,
        campaign_id: int,
        meeting_id: int,
        meeting_date: datetime,
        duration_minutes: int,
        mode: str,
        meeting_link: str | None = None,
    ) -> CampaignMeeting:

        if duration_minutes <= 0:
            raise ValueError(
                "Meeting duration must be greater than 0 minutes."
            )

        mode = mode.strip().lower()

        if mode not in {
            "online",
            "in-person",
        }:
            raise ValueError(
                "Invalid meeting mode. Use online or in-person."
            )

        if mode == "online" and not meeting_link:
            raise ValueError(
                "Meeting link is required for online meetings."
            )

        with Session(engine) as session:

            meeting = session.scalar(
                select(CampaignMeeting).where(
                    CampaignMeeting.id == meeting_id,
                    CampaignMeeting.campaign_id == campaign_id,
                )
            )

            if meeting is None:
                raise ValueError(
                    f"Meeting not found: {meeting_id}"
                )

            if meeting.status != "SCHEDULED":
                raise ValueError(
                    "Only scheduled meetings can be rescheduled."
                )

            now = datetime.now(timezone.utc)

            # ----------------------------------
            # Old meeting becomes cancelled
            # ----------------------------------

            meeting.status = "CANCELLED"
            meeting.cancelled_at = now
            meeting.updated_at = now

            # ----------------------------------
            # Create replacement meeting
            # ----------------------------------

            new_meeting = CampaignMeeting(
                campaign_id=campaign_id,
                response_action_id=meeting.response_action_id,
                meeting_date=meeting_date,
                duration_minutes=duration_minutes,
                mode=mode,
                meeting_link=meeting_link.strip()
                if meeting_link
                else None,
                status="SCHEDULED",
                scheduled_at=now,
                created_at=now,
                updated_at=now,
            )

            session.add(new_meeting)

            session.commit()
            session.refresh(new_meeting)

            return new_meeting

    # ==================================================
    # Cancel meeting
    # ==================================================

    def cancel_meeting(
        self,
        campaign_id: int,
        meeting_id: int,
    ) -> CampaignMeeting:

        with Session(engine) as session:

            meeting = session.scalar(
                select(CampaignMeeting).where(
                    CampaignMeeting.id == meeting_id,
                    CampaignMeeting.campaign_id == campaign_id,
                )
            )

            if meeting is None:
                raise ValueError(
                    f"Meeting not found: {meeting_id}"
                )

            if meeting.status != "SCHEDULED":
                raise ValueError(
                    "Only scheduled meetings can be cancelled."
                )

            now = datetime.now(timezone.utc)

            meeting.status = "CANCELLED"
            meeting.cancelled_at = now
            meeting.updated_at = now

            session.commit()
            session.refresh(meeting)

            return meeting

    # ==================================================
    # Delete meeting
    # ==================================================
    def delete_meeting(
        self,
        campaign_id: int,
        meeting_id: int,
    ) -> None:

        with Session(engine) as session:

            meeting = session.scalar(
                select(CampaignMeeting)
                .where(
                    CampaignMeeting.id == meeting_id,
                    CampaignMeeting.campaign_id == campaign_id,
                )
            )

            if meeting is None:
                raise ValueError(
                    f"Meeting not found: {meeting_id}"
                )

            if meeting.status not in ["MISSED", "CANCELLED"]:
                raise ValueError(
                    "Only MISSED or CANCELLED meetings can be deleted."
                )

            session.delete(meeting)
            session.commit()

    # ==================================================
    # Call lifecycle
    # ==================================================

    def schedule_call(
        self,
        campaign_id: int,
        response_action_id: int | None,
        call_date: datetime,
        duration_minutes: int,
        notes: str | None = None,
    ) -> CampaignCall:

        if duration_minutes <= 0:
            raise ValueError(
                "Call duration must be greater than 0 minutes."
            )

        now = datetime.now(timezone.utc)

        if call_date <= now:
            raise ValueError(
                "Call date and time must be in the future."
            )

        with Session(engine) as session:

            # ----------------------------------
            # Get campaign
            # ----------------------------------

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
            # Make sure there is no active call
            # ----------------------------------

            active_call = session.scalar(
                select(CampaignCall)
                .where(
                    CampaignCall.campaign_id == campaign_id,
                    CampaignCall.status == "SCHEDULED",
                )
                .order_by(
                    CampaignCall.call_date.desc()
                )
            )

            if active_call is not None:

                call_end = (
                    active_call.call_date
                    + timedelta(
                        minutes=active_call.duration_minutes
                    )
                )

                now = datetime.now(timezone.utc)

                # Existing call is still active.
                if now < call_end:
                    raise ValueError(
                        "An active call is already scheduled "
                        f"for campaign {campaign_id}."
                    )

                # Existing call has passed.
                active_call.status = "COMPLETED"
                active_call.completed_at = now

            # ----------------------------------
            # Create call
            # ----------------------------------

            now = datetime.now(timezone.utc)

            call = CampaignCall(
                campaign_id=campaign_id,
                response_action_id=response_action_id,
                call_date=call_date,
                duration_minutes=duration_minutes,
                status="SCHEDULED",
                notes=notes.strip() if notes else None,
                scheduled_at=now,
                created_at=now,
                updated_at=now,
            )

            session.add(call)

            # ----------------------------------
            # Mark response action as completed
            # ----------------------------------

            if response_action_id is not None:

                response_action = session.scalar(
                    select(CampaignResponseAction).where(
                        CampaignResponseAction.id
                        == response_action_id
                    )
                )

                if response_action is not None:
                    response_action.action_status = "COMPLETED"
                    response_action.completed_at = now

            session.commit()
            session.refresh(call)

            return call

    # ==================================================
    # Get current call
    # ==================================================

    def get_current_call(
        self,
        campaign_id: int,
    ) -> CampaignCall | None:

        with Session(engine) as session:

            # ----------------------------------
            # Get campaign
            # ----------------------------------

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
            # Get latest call
            # ----------------------------------

            call = session.scalar(
                select(CampaignCall)
                .where(
                    CampaignCall.campaign_id == campaign_id,
                )
                .order_by(
                    CampaignCall.created_at.desc()
                )
            )

            if call is None:
                return None

            # ----------------------------------
            # Automatically recognize expired call
            # ----------------------------------

            now = datetime.now(timezone.utc)

            call_end = (
                call.call_date
                + timedelta(
                    minutes=call.duration_minutes
                )
            )

            if (
                call.status == "SCHEDULED"
                and now >= call_end
            ):
                call.status = "MISSED"
                call.completed_at = None
                call.updated_at = now

                session.commit()
                session.refresh(call)

            return call
        
    # MISSED/CANCELLED
    def schedule_new_call(
        self,
        campaign_id: int,
        previous_call_id: int,
        call_date: datetime,
        duration_minutes: int = 30,
        notes: str | None = None,
    ):
        with Session(engine) as session:
            previous_call = session.scalar(
                select(CampaignCall).where(
                    CampaignCall.id == previous_call_id,
                    CampaignCall.campaign_id == campaign_id,
                )
            )

            if previous_call is None:
                raise ValueError(
                    f"Call {previous_call_id} not found "
                    f"for campaign {campaign_id}."
                )

            if previous_call.status not in {"MISSED", "CANCELLED"}:
                raise ValueError(
                    "A new call can only be scheduled after "
                    "a MISSED or CANCELLED call."
                )

            # Make sure the new call time is timezone-aware.
            if call_date.tzinfo is None:
                raise ValueError(
                    "Call date must include timezone information."
                )

            # The new call must be in the future.
            if call_date <= datetime.now(timezone.utc):
                raise ValueError(
                    "New call date must be in the future."
                )

            new_call = CampaignCall(
                campaign_id=campaign_id,
                response_action_id=previous_call.response_action_id,
                call_date=call_date,
                duration_minutes=duration_minutes,
                status="SCHEDULED",
                notes=notes,
            )

            session.add(new_call)
            session.commit()
            session.refresh(new_call)

            return new_call

    # ==================================================
    # Reschedule call
    # ==================================================

    def reschedule_call(
        self,
        campaign_id: int,
        call_id: int,
        call_date: datetime,
        duration_minutes: int,
        notes: str | None = None,
    ) -> CampaignCall:

        if duration_minutes <= 0:
            raise ValueError(
                "Call duration must be greater than 0 minutes."
            )

        now = datetime.now(timezone.utc)

        if call_date <= now:
            raise ValueError(
                "Call date and time must be in the future."
            )

        with Session(engine) as session:

            # ----------------------------------
            # Get existing call
            # ----------------------------------

            call = session.scalar(
                select(CampaignCall).where(
                    CampaignCall.id == call_id,
                    CampaignCall.campaign_id == campaign_id,
                )
            )

            if call is None:
                raise ValueError(
                    f"Call not found: {call_id}"
                )

            if call.status != "SCHEDULED":
                raise ValueError(
                    "Only scheduled calls can be rescheduled."
                )

            # ----------------------------------
            # Old call becomes cancelled
            # ----------------------------------

            call.status = "CANCELLED"
            call.cancelled_at = now
            call.updated_at = now

            # ----------------------------------
            # Create replacement call
            # ----------------------------------

            new_call = CampaignCall(
                campaign_id=campaign_id,
                response_action_id=call.response_action_id,
                call_date=call_date,
                duration_minutes=duration_minutes,
                status="SCHEDULED",
                notes=notes.strip() if notes else None,
                scheduled_at=now,
                created_at=now,
                updated_at=now,
            )

            session.add(new_call)

            session.commit()
            session.refresh(new_call)

            return new_call

    # ==================================================
    # Cancel call
    # ==================================================

    def cancel_call(
        self,
        campaign_id: int,
        call_id: int,
    ) -> CampaignCall:

        with Session(engine) as session:

            # ----------------------------------
            # Get call
            # ----------------------------------

            call = session.scalar(
                select(CampaignCall).where(
                    CampaignCall.id == call_id,
                    CampaignCall.campaign_id == campaign_id,
                )
            )

            if call is None:
                raise ValueError(
                    f"Call not found: {call_id}"
                )

            if call.status != "SCHEDULED":
                raise ValueError(
                    "Only scheduled calls can be cancelled."
                )

            # ----------------------------------
            # Cancel call
            # ----------------------------------

            now = datetime.now(timezone.utc)

            call.status = "CANCELLED"
            call.cancelled_at = now
            call.updated_at = now

            session.commit()
            session.refresh(call)

            return call
# =========================================================
# Response Action Helpers
# =========================================================

    # ==================================================
    # Get latest response action
    # ==================================================

    def get_latest_response_action(
        self,
        campaign_id: int,
        response_category: str | None = None,
    ) -> CampaignResponseAction | None:

        with Session(engine) as session:

            statement = (
                select(CampaignResponseAction)
                .where(
                    CampaignResponseAction.campaign_id == campaign_id
                )
            )

            if response_category is not None:
                statement = statement.where(
                    CampaignResponseAction.response_category
                    == response_category
                )

            return session.scalar(
                statement.order_by(
                    CampaignResponseAction.created_at.desc()
                )
            )

    def get_pending_response_action(
        self,
        campaign_id: int,
        response_category: str,
    ) -> CampaignResponseAction | None:

        with Session(engine) as session:

            return session.scalar(
                select(CampaignResponseAction)
                .where(
                    CampaignResponseAction.campaign_id == campaign_id,
                    CampaignResponseAction.response_category
                    == response_category,
                    CampaignResponseAction.action_status == "PENDING",
                )
                .order_by(
                    CampaignResponseAction.created_at.desc()
                )
            )

    def send_call_confirmation(
        self,
        campaign_id: int,
        call_id: int,
    ):
        import os
        import smtplib
        from email.message import EmailMessage

        with Session(engine) as session:

            # ----------------------------------
            # Get campaign
            # ----------------------------------

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign {campaign_id} not found."
                )

            # ----------------------------------
            # Get scheduled call
            # ----------------------------------

            call = session.scalar(
                select(CampaignCall).where(
                    CampaignCall.id == call_id,
                    CampaignCall.campaign_id == campaign_id,
                )
            )

            if call is None:
                raise ValueError(
                    f"Call {call_id} not found "
                    f"for campaign {campaign_id}."
                )

            if call.status != "SCHEDULED":
                raise ValueError(
                    "Confirmation can only be sent "
                    "for a scheduled call."
                )

            # ----------------------------------
            # Get latest inbound message
            # ----------------------------------

            inbound_message = session.scalar(
                select(ConversationMessage)
                .where(
                    ConversationMessage.campaign_id == campaign_id,
                    ConversationMessage.direction == "inbound",
                )
                .order_by(
                    ConversationMessage.created_at.desc()
                )
            )

            if inbound_message is None:
                raise ValueError(
                    "No inbound message found for this campaign."
                )

            recipient_email = inbound_message.sender_email

            # ----------------------------------
            # Test recipient
            # ----------------------------------

            email_test_mode = (
                os.getenv("EMAIL_TEST_MODE", "false")
                .lower()
                == "true"
            )

            email_test_recipient = os.getenv(
                "EMAIL_TEST_RECIPIENT"
            )

            if email_test_mode and email_test_recipient:
                recipient_email = email_test_recipient

            # ----------------------------------
            # SMTP configuration
            # ----------------------------------

            smtp_host = os.getenv("EMAIL_SMTP_HOST")
            smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
            smtp_username = os.getenv("EMAIL_SMTP_USERNAME")
            smtp_password = os.getenv("EMAIL_SMTP_PASSWORD")
            smtp_from_email = os.getenv("EMAIL_FROM_ADDRESS")
            smtp_from_name = os.getenv(
                "EMAIL_FROM_NAME",
                "AI & Quantum Training Team",
            )

            if not all(
                [
                    smtp_host,
                    smtp_username,
                    smtp_password,
                    smtp_from_email,
                ]
            ):
                raise ValueError(
                    "SMTP configuration is incomplete."
                )

            # ----------------------------------
            # Format call date/time
            # ----------------------------------

            call_datetime = call.call_date

            formatted_date = call_datetime.strftime(
                "%d %b %Y"
            )

            formatted_time = call_datetime.strftime(
                "%I:%M %p"
            )

            # ----------------------------------
            # Email content
            # ----------------------------------

            subject = (
                "Confirmation: Scheduled Call "
                "with AAMP"
            )

            message_body = f"""Dear Sir/Madam,

    Thank you for your response.

    This is to confirm our scheduled call regarding the AI training and workshop opportunity.

    Call Details:

    Date: {formatted_date}
    Time: {formatted_time}
    Duration: {call.duration_minutes} minutes

    We look forward to speaking with you and discussing the opportunity in more detail.

    Best regards,
    AAMP Team
    """

            # ----------------------------------
            # Build email
            # ----------------------------------

            email = EmailMessage()

            email["From"] = (
                f"{smtp_from_name} <{smtp_from_email}>"
            )
            email["To"] = recipient_email
            email["Subject"] = subject

            email.set_content(message_body)

            # ----------------------------------
            # Send email
            # ----------------------------------

            try:

                with smtplib.SMTP(
                    smtp_host,
                    smtp_port,
                    timeout=30,
                ) as server:

                    server.starttls()

                    server.login(
                        smtp_username,
                        smtp_password,
                    )

                    server.send_message(email)
                    # Email was successfully sent
                    call.confirmation_sent_at = datetime.now(timezone.utc)

            except Exception as exc:

                raise ValueError(
                    f"Failed to send call confirmation: {exc}"
                )

            # ----------------------------------
            # Store outbound conversation
            # ----------------------------------

            now = datetime.now(timezone.utc)

            conversation = ConversationMessage(
                campaign_id=campaign.id,
                college_id=campaign.college_id,
                direction="outbound",
                sender_email=smtp_from_email,
                recipient_email=recipient_email,
                subject=subject,
                message=message_body,
                status="sent",
                sent_at=now,
                created_at=now,
            )

            session.add(conversation)
            session.add(call)

            session.commit()

            return {
                "campaign_id": campaign_id,
                "call_id": call.id,
                "recipient": recipient_email,
                "subject": subject,
                "sent": True,
                "sent_at": now,
            }

    def get_call(
        self,
        campaign_id: int,
        call_id: int,
    ):
        with Session(engine) as session:
            call = session.scalar(
                select(CampaignCall).where(
                    CampaignCall.id == call_id,
                    CampaignCall.campaign_id == campaign_id,
                )
            )

            if call is None:
                raise ValueError(
                    f"Call {call_id} not found for campaign {campaign_id}."
                )

            return call

    def update_college_contact(
        self,
        campaign_id: int,
        role: str,
        email: str,
        phone: str | None = None,
    ) -> College:

        if not email or not email.strip():
            raise ValueError(
                "A valid email address is required."
            )

        if not role or not role.strip():
            raise ValueError(
                "Contact role is required."
            )

        with Session(engine) as session:

            # ----------------------------------
            # Get campaign
            # ----------------------------------

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

            if campaign.response_category != "WRONG_CONTACT":
                raise ValueError(
                    "Contact can only be updated for "
                    "a WRONG_CONTACT campaign."
                )

            # ----------------------------------
            # Get college
            # ----------------------------------

            college = session.scalar(
                select(College).where(
                    College.id == campaign.college_id
                )
            )

            if college is None:
                raise ValueError(
                    f"College not found: {campaign.college_id}"
                )

            # ----------------------------------
            # Replace active contact
            # ----------------------------------

            college.contact_role = {
                "value": role.strip()
            }

            college.official_email = {
                "value": email.strip().lower()
            }

            if phone and phone.strip():
                college.official_phone = {
                    "value": phone.strip()
                }
            else:
                college.official_phone = None

            campaign.contact_updated = True
            # ----------------------------------
            # Save
            # ----------------------------------

            session.commit()
            session.refresh(college)

            return college