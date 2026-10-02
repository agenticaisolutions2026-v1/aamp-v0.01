from datetime import datetime
from typing import Any, Dict, Optional

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


class OutreachOrchestratorAgent(BaseAgent):
    """
    Outreach Orchestrator Agent

    Responsibilities:
    - Accept an approved campaign
    - Check human approval
    - Block unapproved campaigns
    - Create an internal outreach queue
    - Prepare outreach records for database persistence
    - Manage outreach statuses
    - Calculate follow-up state
    - Classify incoming responses
    - Handle opt-out requests
    - Trigger human handoff when required
    - Prepare automatic replies for interested responses
    - Recommend channel actions
    - Never perform automatic bulk messaging
    """

    name = "outreach_orchestrator"

    def execute(self, state: AgentState) -> AgentState:
        """
        Main entry point for the Outreach Orchestrator Agent.
        """

        try:
            campaign = self._get_campaign(state)

            if not campaign:
                state.status = "failed"
                state.error = "No campaign data provided."
                state.result = {
                    "status": "failed",
                    "reason": "No campaign data provided.",
                }
                return state

            # ---------------------------------------------------------
            # 1. Check human approval
            # ---------------------------------------------------------

            approval_result = self._check_approval(campaign)

            if not approval_result["approved"]:
                state.status = "blocked"

                state.result = {
                    "status": "blocked",
                    "reason": "human approval required",
                    "campaign_id": campaign.get("campaign_id"),
                    "college_id": campaign.get("college_id"),
                    "next_action": "Wait for approval",
                    "required_human_approval": True,
                }

                return state

            # ---------------------------------------------------------
            # 2. Create outreach queue
            # ---------------------------------------------------------

            outreach_job = self._create_outreach_queue(campaign)

            # ---------------------------------------------------------
            # 3. Determine initial outreach state
            # ---------------------------------------------------------

            outreach_status = self._determine_initial_status(
                campaign
            )

            outreach_job["status"] = outreach_status
            outreach_job["next_action"] = "send"

            # ---------------------------------------------------------
            # 4. Build structured result
            # ---------------------------------------------------------

            state.status = "success"

            state.result = {
                "status": "queued",
                "campaign": campaign,
                "outreach": outreach_job,
                "approval": approval_result,
                "follow_up": {
                    "follow_up_count": 0,
                    "max_follow_ups": 2,
                    "schedule": {
                        "follow_up_1": "Day 3",
                        "follow_up_2": "Day 7",
                    },
                },
                "channel_action": self._get_channel_action(
                    campaign.get("channel")
                ),
            }

            return state

        except Exception as exc:
            state.status = "failed"
            state.error = str(exc)

            state.result = {
                "status": "failed",
                "reason": str(exc),
            }

            return state

    # ================================================================
    # CAMPAIGN INPUT
    # ================================================================

    def _get_campaign(
        self,
        state: AgentState,
    ) -> Optional[Dict[str, Any]]:
        """
        Get campaign information from AgentState.

        Supports:
            state.result["campaign"]
            state.result
        """

        if not getattr(state, "result", None):
            return None

        result = state.result

        if isinstance(result, dict):

            campaign = result.get("campaign")

            if isinstance(campaign, dict):
                return campaign

            # Allow the result itself to be the campaign
            if (
                "campaign_id" in result
                or "college_id" in result
                or "college_name" in result
            ):
                return result

        return None

    # ================================================================
    # APPROVAL CHECK
    # ================================================================

    def _check_approval(
        self,
        campaign: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Check whether a campaign has human approval.

        Approved:
            approval_status = approved

        Unapproved:
            draft / pending_approval / missing approval
        """

        approval_status = str(
            campaign.get(
                "approval_status",
                campaign.get("status", ""),
            )
        ).strip().lower()

        required_human_approval = campaign.get(
            "required_human_approval",
            campaign.get(
                "requires_human_approval",
                True,
            ),
        )

        # Explicit approval
        if approval_status == "approved":
            return {
                "approved": True,
                "approval_status": "approved",
                "required_human_approval": (
                    required_human_approval
                ),
            }

        # Approval not required
        if required_human_approval is False:
            return {
                "approved": True,
                "approval_status": (
                    approval_status or "approved"
                ),
                "required_human_approval": False,
            }

        # Everything else is blocked
        return {
            "approved": False,
            "approval_status": (
                approval_status or "pending_approval"
            ),
            "required_human_approval": True,
        }

    # ================================================================
    # OUTREACH QUEUE
    # ================================================================

    def _create_outreach_queue(
        self,
        campaign: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create an internal outreach job.

        This prepares the record for database persistence.

        IMPORTANT:
        This method does NOT send an email, WhatsApp message,
        LinkedIn message, or any other bulk outreach.
        """

        campaign_id = campaign.get("campaign_id")
        college_id = campaign.get("college_id")
        channel = campaign.get("channel")

        recipient = campaign.get(
            "recipient",
            campaign.get(
                "official_email",
                campaign.get("email"),
            ),
        )

        return {
            # Database fields
            "campaign_id": campaign_id,
            "college_id": college_id,
            "channel": channel,
            "recipient": recipient,
            "subject": campaign.get("subject"),
            "message": campaign.get("message", ""),
            "status": "queued",
            "scheduled_at": None,
            "sent_at": None,
            "response_received_at": None,
            "follow_up_count": 0,
            "last_error": None,
            "created_at": datetime.utcnow(),

            # Workflow fields
            "college_name": campaign.get("college_name"),
            "next_action": "send",
            "required_human_approval": campaign.get(
                "required_human_approval",
                True,
            ),
        }

    # ================================================================
    # INITIAL STATUS
    # ================================================================

    def _determine_initial_status(
        self,
        campaign: Dict[str, Any],
    ) -> str:
        """
        Determine the initial outreach status.
        """

        channel = str(
            campaign.get("channel", "")
        ).strip().lower()

        if not channel:
            return "failed"

        supported_channels = {
            "email",
            "whatsapp",
            "linkedin",
            "website_contact_form",
            "phone",
            "manual_review",
        }

        if channel not in supported_channels:
            return "failed"

        return "queued"

    # ================================================================
    # CHANNEL INTERFACE
    # ================================================================

    def _get_channel_action(
        self,
        channel: Optional[str],
    ) -> Dict[str, Any]:
        """
        Return the action that should be performed for a channel.

        No credentials are stored here.
        No automatic bulk messaging is performed.
        """

        channel_value = str(
            channel or ""
        ).strip().lower()

        channel_actions = {

            "email": {
                "channel": "email",
                "action": "send_email",
                "credentials_required": True,
                "automatic_bulk_send": False,
            },

            "whatsapp": {
                "channel": "whatsapp",
                "action": "approved_whatsapp_workflow",
                "credentials_required": True,
                "automatic_bulk_send": False,
            },

            "linkedin": {
                "channel": "linkedin",
                "action": "institutional_linkedin_follow_up",
                "credentials_required": True,
                "automatic_bulk_send": False,
            },

            "website_contact_form": {
                "channel": "website_contact_form",
                "action": "submit_contact_form",
                "credentials_required": False,
                "automatic_bulk_send": False,
            },

            "phone": {
                "channel": "phone",
                "action": "phone_follow_up",
                "credentials_required": False,
                "automatic_bulk_send": False,
            },

            "manual_review": {
                "channel": "manual_review",
                "action": "human_review",
                "credentials_required": False,
                "automatic_bulk_send": False,
            },
        }

        return channel_actions.get(
            channel_value,
            {
                "channel": channel_value,
                "action": "manual_review",
                "credentials_required": False,
                "automatic_bulk_send": False,
            },
        )

    # ================================================================
    # FOLLOW-UP STATE MACHINE
    # ================================================================

    def calculate_follow_up(
        self,
        sent_at: Optional[datetime],
        follow_up_count: int = 0,
        response_received: bool = False,
        opted_out: bool = False,
        max_follow_ups: int = 2,
    ) -> Dict[str, Any]:
        """
        Follow-up logic:

        Day 0 -> Initial outreach
        Day 3 -> Follow-up 1
        Day 7 -> Follow-up 2
        After maximum follow-ups -> Completed

        No follow-up is allowed after a response or opt-out.
        """

        if opted_out:
            return {
                "status": "opted_out",
                "next_action": "stop_all_outreach",
                "follow_up_count": follow_up_count,
            }

        if response_received:
            return {
                "status": "responded",
                "next_action": "human_handoff",
                "follow_up_count": follow_up_count,
            }

        if sent_at is None:
            return {
                "status": "queued",
                "next_action": "send",
                "follow_up_count": follow_up_count,
            }

        if follow_up_count >= max_follow_ups:
            return {
                "status": "completed",
                "next_action": "stop_outreach",
                "follow_up_count": follow_up_count,
            }

        if not isinstance(sent_at, datetime):
            return {
                "status": "failed",
                "next_action": "invalid_sent_at",
                "follow_up_count": follow_up_count,
            }

        now = datetime.utcnow()
        days_since_sent = (now - sent_at).days

        # Day 3
        if (
            follow_up_count == 0
            and days_since_sent >= 3
        ):
            return {
                "status": "follow_up_due",
                "next_action": "send_follow_up_1",
                "follow_up_count": 1,
                "days_since_sent": days_since_sent,
            }

        # Day 7
        if (
            follow_up_count == 1
            and days_since_sent >= 7
        ):
            return {
                "status": "follow_up_due",
                "next_action": "send_follow_up_2",
                "follow_up_count": 2,
                "days_since_sent": days_since_sent,
            }

        return {
            "status": "sent",
            "next_action": "wait_for_response",
            "follow_up_count": follow_up_count,
            "days_since_sent": days_since_sent,
        }

    # ================================================================
    # RESPONSE CLASSIFICATION
    # ================================================================

    def classify_response(
        self,
        response_text: str,
    ) -> Dict[str, Any]:
        """
        Classify an incoming college response.

        Categories:
        - interested
        - not_interested
        - needs_information
        - request_callback
        - wrong_contact
        - opt_out
        - unknown
        """

        if not response_text:
            return {
                "response_category": "unknown",
                "next_action": "human_review",
            }

        text = response_text.strip().lower()

        # ------------------------------------------------------------
        # OPT OUT
        # ------------------------------------------------------------

        opt_out_keywords = [
            "do not contact",
            "don't contact",
            "dont contact",
            "stop contacting",
            "stop contact",
            "remove me",
            "unsubscribe",
            "opt out",
            "opt-out",
            "no more emails",
            "no further emails",
        ]

        if any(
            keyword in text
            for keyword in opt_out_keywords
        ):
            return {
                "response_category": "opt_out",
                "next_action": "stop_all_outreach",
            }

        # ------------------------------------------------------------
        # INTERESTED
        # ------------------------------------------------------------

        interested_keywords = [
            "interested",
            "sounds good",
            "we are interested",
            "let us discuss",
            "yes",
            "proceed",
            "would like to discuss",
            "interested in workshop",
            "interested in training",
        ]

        if any(
            keyword in text
            for keyword in interested_keywords
        ):
            return {
                "response_category": "interested",
                "next_action": "prepare_thank_you_and_demo",
            }

        # ------------------------------------------------------------
        # NEEDS INFORMATION
        # ------------------------------------------------------------

        information_keywords = [
            "course details",
            "course information",
            "pricing",
            "price",
            "fees",
            "brochure",
            "syllabus",
            "details",
            "proposal",
            "curriculum",
            "duration",
            "training details",
        ]

        if any(
            keyword in text
            for keyword in information_keywords
        ):
            return {
                "response_category": "needs_information",
                "next_action": "human_review",
            }

        # ------------------------------------------------------------
        # CALLBACK
        # ------------------------------------------------------------

        callback_keywords = [
            "call me",
            "call us",
            "callback",
            "call back",
            "contact me",
            "contact us",
            "schedule a call",
            "meeting",
            "discuss over phone",
        ]

        if any(
            keyword in text
            for keyword in callback_keywords
        ):
            return {
                "response_category": "request_callback",
                "next_action": "human_handoff",
            }

        # ------------------------------------------------------------
        # WRONG CONTACT
        # ------------------------------------------------------------

        wrong_contact_keywords = [
            "wrong person",
            "wrong contact",
            "not the right person",
            "not responsible",
            "contact someone else",
            "please contact",
            "not handling this",
        ]

        if any(
            keyword in text
            for keyword in wrong_contact_keywords
        ):
            return {
                "response_category": "wrong_contact",
                "next_action": "human_review",
            }

        # ------------------------------------------------------------
        # NOT INTERESTED
        # ------------------------------------------------------------

        not_interested_keywords = [
            "not interested",
            "no interest",
            "cannot proceed",
            "not required",
            "no requirement",
            "not looking for",
            "maybe later",
        ]

        if any(
            keyword in text
            for keyword in not_interested_keywords
        ):
            return {
                "response_category": "not_interested",
                "next_action": "close_or_review",
            }

        # ------------------------------------------------------------
        # UNKNOWN
        # ------------------------------------------------------------

        return {
            "response_category": "unknown",
            "next_action": "human_review",
        }

    # ================================================================
    # INTERESTED RESPONSE
    # ================================================================

    def prepare_interested_reply(
        self,
        outreach: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a professional thank-you and demo invitation
        for an interested college response.

        IMPORTANT:
        This only prepares the reply.
        It does NOT send any real message.
        """

        outreach = outreach or {}

        college_name = (
            outreach.get("college_name")
            or "the college"
        )

        reply_subject = (
            "Thank You for Your Interest - "
            "AI Training Program"
        )

        reply_message = (
            f"Dear Sir/Madam,\n\n"
            f"Thank you for your interest in our AI training "
            f"program. We are pleased to know that "
            f"{college_name} is interested in exploring "
            f"this opportunity.\n\n"
            "We would be happy to arrange a short demo to "
            "discuss the program, training format, topics "
            "covered, and possible collaboration options.\n\n"
            "Please let us know a convenient date and time "
            "for the demo, or select a suitable slot from "
            "the available options.\n\n"
            "We look forward to connecting with you.\n\n"
            "Regards,\n"
            "AI & Quantum Training Team"
        )

        return {
            "reply_type": "interested_thank_you",
            "channel": outreach.get("channel"),
            "recipient": outreach.get("recipient"),
            "subject": reply_subject,
            "message": reply_message,
            "status": "prepared",
            "real_message_sent": False,
            "next_action": "schedule_demo",
        }

    # ================================================================
    # PROCESS RESPONSE
    # ================================================================

    def process_response(
        self,
        response_text: str,
        outreach: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process an incoming response and update the outreach state.
        """

        classification = self.classify_response(
            response_text
        )

        outreach = outreach or {}

        category = classification[
            "response_category"
        ]

        # ------------------------------------------------------------
        # OPT OUT
        # ------------------------------------------------------------

        if category == "opt_out":

            outreach["status"] = "opted_out"

            outreach["next_action"] = (
                "stop_all_outreach"
            )

        # ------------------------------------------------------------
        # INTERESTED
        # ------------------------------------------------------------

        elif category == "interested":

            outreach["status"] = "responded"

            interested_reply = (
                self.prepare_interested_reply(
                    outreach
                )
            )

            outreach["next_action"] = (
                "schedule_demo"
            )

            classification["reply"] = (
                interested_reply
            )

        # ------------------------------------------------------------
        # CALLBACK
        # ------------------------------------------------------------

        elif category == "request_callback":

            outreach["status"] = "responded"

            outreach["next_action"] = (
                "human_handoff"
            )

        # ------------------------------------------------------------
        # NEEDS INFORMATION
        # ------------------------------------------------------------

        elif category == "needs_information":

            outreach["status"] = "responded"

            outreach["next_action"] = (
                "human_review"
            )

        # ------------------------------------------------------------
        # NOT INTERESTED
        # ------------------------------------------------------------

        elif category == "not_interested":

            outreach["status"] = "completed"

            outreach["next_action"] = (
                "stop_outreach"
            )

        # ------------------------------------------------------------
        # WRONG CONTACT
        # ------------------------------------------------------------

        elif category == "wrong_contact":

            outreach["status"] = "responded"

            outreach["next_action"] = (
                "human_review"
            )

        # ------------------------------------------------------------
        # UNKNOWN
        # ------------------------------------------------------------

        else:

            outreach["status"] = "responded"

            outreach["next_action"] = (
                "human_review"
            )

        # ------------------------------------------------------------
        # Response timestamp
        # ------------------------------------------------------------

        outreach[
            "response_received_at"
        ] = datetime.utcnow()

        return {
            "outreach": outreach,
            "response": classification,
        }

    # ================================================================
    # HUMAN HANDOFF
    # ================================================================

    def create_human_handoff(
        self,
        campaign: Dict[str, Any],
        response_category: str,
        response_text: str = "",
    ) -> Dict[str, Any]:
        """
        Create a structured human handoff.
        """

        return {
            "status": "human_handoff",
            "campaign_id": campaign.get(
                "campaign_id"
            ),
            "college_id": campaign.get(
                "college_id"
            ),
            "college_name": campaign.get(
                "college_name"
            ),
            "contact_role": campaign.get(
                "contact_role"
            ),
            "response_category": response_category,
            "response_text": response_text,
            "next_action": "human_review",
            "created_at": datetime.utcnow(),
        }

    # ================================================================
    # OPT-OUT HANDLING
    # ================================================================

    def handle_opt_out(
        self,
        campaign: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Stop all future outreach for an opted-out
        college/contact.
        """

        return {
            "campaign_id": campaign.get(
                "campaign_id"
            ),
            "college_id": campaign.get(
                "college_id"
            ),
            "status": "opted_out",
            "next_action": "stop_all_outreach",
            "follow_up_count": 0,
            "outreach_allowed": False,
            "updated_at": datetime.utcnow(),
        }