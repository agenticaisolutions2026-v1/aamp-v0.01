import logging
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session


from backend.database.connection import engine
from backend.models import (
    Campaign,
    CampaignStatusHistory,
    College,
    ConversationMessage,
)
from zoneinfo import ZoneInfo
IST = ZoneInfo("Asia/Kolkata")

from pathlib import Path
import mimetypes

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================
# STANDARD INFORMATION PACKAGE
# ============================================================

INFORMATION_PACKAGE_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "information_package"
)

INFORMATION_PACKAGE_FILES = [
    "course_training",
    "brochure",
    "workshop_1_day",
    "workshop_2_day",
    "workshop_3_day",
]


class EmailService:
    """
    Sends approved campaign emails through SMTP.

    TEST MODE:
        Sends only to EMAIL_TEST_RECIPIENT.

    PRODUCTION MODE:
        Sends to the college's official email.

    Responsibilities:
        - Validate campaign before sending
        - Send email through SMTP
        - Mark campaign as SENT
        - Store sent_at
        - Schedule next follow-up
        - Store outbound conversation message
        - Mark failed campaigns as FAILED

    This service does NOT:
        - Approve campaigns
        - Decide whether a lead should be contacted
        - Analyze responses
        - Run scheduled follow-ups
    """

    def __init__(self):

        self.test_mode = (
            os.getenv(
                "EMAIL_TEST_MODE",
                "true",
            ).lower()
            == "true"
        )

        self.test_recipient = os.getenv(
            "EMAIL_TEST_RECIPIENT"
        )

        self.smtp_host = os.getenv(
            "EMAIL_SMTP_HOST",
            "smtp.gmail.com",
        )

        self.smtp_port = int(
            os.getenv(
                "EMAIL_SMTP_PORT",
                "587",
            )
        )

        self.smtp_username = os.getenv(
            "EMAIL_SMTP_USERNAME"
        )

        self.smtp_password = os.getenv(
            "EMAIL_SMTP_PASSWORD"
        )

        self.from_address = os.getenv(
            "EMAIL_FROM_ADDRESS",
            self.smtp_username,
        )

        self.from_name = os.getenv(
            "EMAIL_FROM_NAME",
            "AI & Quantum Training Team",
        )

    # ==================================================
    # Send campaign email
    # ==================================================

    def send_campaign_email(
        self,
        campaign_id: int,
        is_response_driven: bool = False,
    ) -> dict:
        """
        Send a campaign email.

        A campaign must be APPROVED before sending.

        On success:

            campaign.status = sent
            campaign.sent_at = now

        For the initial outreach:

            follow_up_count = 0
            next_follow_up_at = sent_at + 3 days

        For follow-ups:

            follow_up_count is incremented
            next_follow_up_at is scheduled for the
            next follow-up when applicable.
        """

        with Session(engine) as session:

            # --------------------------------------------------
            # 1. Get campaign
            # --------------------------------------------------

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign not found: {campaign_id}"
                )

            # --------------------------------------------------
            # 2. Safety checks
            # --------------------------------------------------

            allowed_statuses = {
                "approved",
                "queued",
                "follow_up_due",
            }

            if campaign.status not in allowed_statuses:
                raise ValueError(
                    "Only approved, queued, or follow_up_due "
                    "campaigns can be sent. "
                    f"Current status: {campaign.status}"
                )

            if campaign.channel != "email":
                raise ValueError(
                    "Campaign channel is not email."
                )

            # --------------------------------------------------
            # 3. Get college
            # --------------------------------------------------

            college = session.scalar(
                select(College).where(
                    College.id == campaign.college_id
                )
            )

            if college is None:
                raise ValueError(
                    f"College not found: "
                    f"{campaign.college_id}"
                )

            # --------------------------------------------------
            # 4. Determine recipient
            # --------------------------------------------------

            if self.test_mode:

                if not self.test_recipient:
                    raise ValueError(
                        "EMAIL_TEST_RECIPIENT "
                        "is not configured."
                    )

                recipient = self.test_recipient

            else:

                recipient = self._extract_email(
                    college.official_email
                )

                if not recipient:
                    raise ValueError(
                        "College does not have "
                        "a valid official email."
                    )

            # --------------------------------------------------
            # 5. Validate SMTP configuration
            # --------------------------------------------------

            if not self.smtp_username:
                raise ValueError(
                    "EMAIL_SMTP_USERNAME "
                    "is not configured."
                )

            if not self.smtp_password:
                raise ValueError(
                    "EMAIL_SMTP_PASSWORD "
                    "is not configured."
                )

            if not self.from_address:
                raise ValueError(
                    "EMAIL_FROM_ADDRESS "
                    "is not configured."
                )

            # --------------------------------------------------
            # 6. Build email
            # --------------------------------------------------

            email = EmailMessage()

            email["From"] = (
                f"{self.from_name} "
                f"<{self.from_address}>"
            )

            email["To"] = recipient

            email["Subject"] = (
                campaign.subject
                or "AI Training Opportunity"
            )

            email.set_content(
                campaign.message
            )

            # --------------------------------------------------
            # 7. Send through SMTP
            # --------------------------------------------------

            now = datetime.now(timezone.utc)

            try:

                with smtplib.SMTP(
                    self.smtp_host,
                    self.smtp_port,
                ) as smtp:

                    smtp.starttls()

                    smtp.login(
                        self.smtp_username,
                        self.smtp_password,
                    )

                    smtp.send_message(email)

            except Exception as exc:

                logger.exception(
                    "Failed to send campaign email: %s",
                    campaign_id,
                )

                # ------------------------------------------
                # Persist failure
                # ------------------------------------------

                campaign.status = "failed"
                campaign.failure_reason = str(exc)

                failure_history = (
                    CampaignStatusHistory(
                        campaign_id=campaign.id,
                        status="failed",
                        changed_at=now,
                        changed_by=self.from_address,
                        reason=str(exc),
                    )
                )

                session.add(
                    failure_history
                )

                session.commit()

                raise RuntimeError(
                    f"Email sending failed: {exc}"
                ) from exc

            # --------------------------------------------------
            # 8. Determine follow-up state
            # --------------------------------------------------

            is_initial_outreach = (
                campaign.message_type
                == "initial_outreach"
                and campaign.sent_at is None
                and campaign.follow_up_count == 0
            )

            is_special_response_follow_up = (
                is_response_driven
                and campaign.response_category
                in {
                    "ASK_LATER",
                    "OUT_OF_OFFICE",
                }
            )

            if is_special_response_follow_up:

                # ----------------------------------------------
                # Special response-driven follow-up
                #
                # This is the ONE automatic follow-up requested
                # by the recipient's previous response.
                #
                # It does NOT count as normal Follow-up #1/#2.
                # ----------------------------------------------
                campaign.follow_up_count += 1

                campaign.next_follow_up_at = (
                    now + timedelta(days=3)
                )

            elif is_initial_outreach:

                campaign.sent_at = now
                campaign.follow_up_count = 0

                # Day 3 follow-up at 9:30 AM.
                sent_at_ist = campaign.sent_at.astimezone(IST)

                follow_up_date = (
                    sent_at_ist.date()
                    + timedelta(days=3)
                )

                next_follow_up_ist = sent_at_ist.replace(
                    year=follow_up_date.year,
                    month=follow_up_date.month,
                    day=follow_up_date.day,
                    hour=9,
                    minute=30,
                    second=0,
                    microsecond=0,
                )

                campaign.next_follow_up_at = (
                    next_follow_up_ist.astimezone(timezone.utc)
                )

            else:

                campaign.follow_up_count += 1

                if (
                    campaign.follow_up_count
                    < campaign.max_follow_ups
                ):

                    # ------------------------------------------
                    # Follow-up #1
                    # Day 7 from the original initial send.
                    # ------------------------------------------

                    sent_at_ist = campaign.sent_at.astimezone(IST)

                    follow_up_date = (
                        sent_at_ist.date()
                        + timedelta(days=7)
                    )

                    next_follow_up_ist = sent_at_ist.replace(
                        year=follow_up_date.year,
                        month=follow_up_date.month,
                        day=follow_up_date.day,
                        hour=9,
                        minute=30,
                        second=0,
                        microsecond=0,
                    )

                    campaign.next_follow_up_at = (
                        next_follow_up_ist.astimezone(timezone.utc)
                    )

                else:

                    # ------------------------------------------
                    # Follow-up #2 has just been sent.
                    #
                    # Wait 2 days before the final
                    # response check.
                    # ------------------------------------------

                    now_ist = now.astimezone(IST)

                    final_check_date = (
                        now_ist.date()
                        + timedelta(days=2)
                    )

                    final_check_ist = now_ist.replace(
                        year=final_check_date.year,
                        month=final_check_date.month,
                        day=final_check_date.day,
                        hour=9,
                        minute=30,
                        second=0,
                        microsecond=0,
                    )

                    campaign.next_follow_up_at = (
                        final_check_ist.astimezone(timezone.utc)
                    )

            # --------------------------------------------------
            # 9. Mark campaign SENT
            # --------------------------------------------------

            campaign.status = "sent"

            history = CampaignStatusHistory(
                campaign_id=campaign.id,
                status="sent",
                changed_at=now,
                changed_by=self.from_address,
                reason=(
                    "Campaign email sent successfully."
                ),
            )

            session.add(history)

            # --------------------------------------------------
            # 10. Save outbound conversation message
            # --------------------------------------------------

            conversation = ConversationMessage(
                campaign_id=campaign.id,
                college_id=campaign.college_id,
                direction="outbound",
                sender_email=self.from_address,
                recipient_email=recipient,
                subject=campaign.subject,
                message=campaign.message,
                status="sent",
                sent_at=now,
                created_at=now,
            )

            session.add(conversation)

            # --------------------------------------------------
            # 11. Commit
            # --------------------------------------------------

            session.commit()
            session.refresh(campaign)

            # --------------------------------------------------
            # 12. Return result
            # --------------------------------------------------

            return {
                "campaign_id": campaign.id,
                "college_id": campaign.college_id,
                "college_name": college.name,
                "recipient": recipient,
                "from_address": self.from_address,
                "from_name": self.from_name,
                "subject": campaign.subject,
                "status": campaign.status,
                "test_mode": self.test_mode,
                "sent": True,
                "sent_at": campaign.sent_at,
                "next_follow_up_at": (
                    campaign.next_follow_up_at
                ),
                "follow_up_count": (
                    campaign.follow_up_count
                ),
            }

    # ==================================================
    # Send meeting confirmation email
    # ==================================================

    def send_meeting_confirmation(
        self,
        campaign_id: int,
        recipient_email: str,
        subject: str,
        message: str,
    ) -> dict:
        """
        Send a meeting confirmation email.

        This does NOT change the campaign status,
        follow-up count, or follow-up schedule.
        """

        if not recipient_email or not recipient_email.strip():
            raise ValueError(
                "Recipient email is required."
            )

        if not subject or not subject.strip():
            raise ValueError(
                "Email subject is required."
            )

        if not message or not message.strip():
            raise ValueError(
                "Email message is required."
            )

        if not self.smtp_username:
            raise ValueError(
                "EMAIL_SMTP_USERNAME is not configured."
            )

        if not self.smtp_password:
            raise ValueError(
                "EMAIL_SMTP_PASSWORD is not configured."
            )

        if not self.from_address:
            raise ValueError(
                "EMAIL_FROM_ADDRESS is not configured."
            )

        with Session(engine) as session:

            # --------------------------------------------------
            # Get campaign
            # --------------------------------------------------

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign not found: {campaign_id}"
                )

            # --------------------------------------------------
            # TEST MODE SAFETY
            # --------------------------------------------------

            actual_recipient = recipient_email.strip()

            if self.test_mode:

                if not self.test_recipient:
                    raise ValueError(
                        "EMAIL_TEST_RECIPIENT "
                        "is not configured."
                    )

                actual_recipient = self.test_recipient

            # --------------------------------------------------
            # Build email
            # --------------------------------------------------

            email = EmailMessage()

            email["From"] = (
                f"{self.from_name} "
                f"<{self.from_address}>"
            )

            email["To"] = actual_recipient
            email["Subject"] = subject.strip()

            email.set_content(
                message.strip()
            )

            now = datetime.now(timezone.utc)

            # --------------------------------------------------
            # Send through SMTP
            # --------------------------------------------------

            try:

                with smtplib.SMTP(
                    self.smtp_host,
                    self.smtp_port,
                ) as smtp:

                    smtp.starttls()

                    smtp.login(
                        self.smtp_username,
                        self.smtp_password,
                    )

                    smtp.send_message(email)

            except Exception as exc:

                logger.exception(
                    "Failed to send meeting confirmation "
                    "for campaign %s",
                    campaign_id,
                )

                raise RuntimeError(
                    f"Meeting confirmation email "
                    f"sending failed: {exc}"
                ) from exc

            # --------------------------------------------------
            # Save outbound conversation message
            # --------------------------------------------------

            conversation = ConversationMessage(
                campaign_id=campaign.id,
                college_id=campaign.college_id,
                direction="outbound",
                sender_email=self.from_address,
                recipient_email=actual_recipient,
                subject=subject.strip(),
                message=message.strip(),
                status="sent",
                sent_at=now,
                created_at=now,
            )

            session.add(conversation)

            session.commit()

            # --------------------------------------------------
            # Return result
            # --------------------------------------------------

            return {
                "campaign_id": campaign.id,
                "college_id": campaign.college_id,
                "recipient": actual_recipient,
                "from_address": self.from_address,
                "subject": subject.strip(),
                "sent": True,
                "sent_at": now,
                "test_mode": self.test_mode,
            }

    # ==================================================
    # Extract email
    # ==================================================

    @staticmethod
    def _extract_email(
        official_email,
    ) -> str | None:

        if not official_email:
            return None

        if isinstance(
            official_email,
            dict,
        ):
            return official_email.get(
                "value"
            )

        if isinstance(
            official_email,
            str,
        ):
            return official_email

        return 

    
    # ==================================================
    # sending the proposal
    # ==================================================
    def send_proposal_email(
        self,
        campaign_id: int,
        attachment_bytes: bytes,
        attachment_filename: str,
        attachment_content_type: str = "application/pdf",
    ) -> dict:

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

            if campaign.channel != "email":
                raise ValueError(
                    "Campaign channel is not email."
                )

            if campaign.status not in {
                "replied",
                "proposal",
                "action_required",
            }:
                raise ValueError(
                    "Proposal can only be sent for a campaign "
                    f"requiring a response. Current status: "
                    f"{campaign.status}"
                )

            # ---------------------------------------------
            # Find recipient from the existing conversation
            # ---------------------------------------------

            inbound_message = session.scalar(
                select(ConversationMessage)
                .where(
                    ConversationMessage.campaign_id == campaign_id,
                    ConversationMessage.direction == "inbound",
                )
                .order_by(
                    ConversationMessage.received_at.desc()
                )
            )

            if inbound_message is None:
                raise ValueError(
                    "No inbound response found for this campaign."
                )

            # ---------------------------------------------
            # Determine recipient
            # ---------------------------------------------

            if self.test_mode:

                if not self.test_recipient:
                    raise ValueError(
                        "EMAIL_TEST_RECIPIENT is not configured."
                    )

                recipient = self.test_recipient

            else:

                recipient = inbound_message.sender_email

                if not recipient:
                    raise ValueError(
                        "Could not determine the recipient email."
                    )

            # ---------------------------------------------
            # SMTP validation
            # ---------------------------------------------

            if not self.smtp_username:
                raise ValueError(
                    "EMAIL_SMTP_USERNAME is not configured."
                )

            if not self.smtp_password:
                raise ValueError(
                    "EMAIL_SMTP_PASSWORD is not configured."
                )

            if not self.from_address:
                raise ValueError(
                    "EMAIL_FROM_ADDRESS is not configured."
                )

            # ---------------------------------------------
            # Build proposal reply
            # ---------------------------------------------

            email = EmailMessage()

            email["From"] = (
                f"{self.from_name} "
                f"<{self.from_address}>"
            )

            email["To"] = recipient

            original_subject = (
                campaign.subject
                or "AI Training Opportunity"
            )

            email["Subject"] = (
                original_subject
                if original_subject.lower().startswith("re:")
                else f"Re: {original_subject}"
            )

            proposal_message = (
                "Dear Sir/Madam,\n\n"
                "Thank you for your response.\n\n"
                "Please find attached the requested proposal "
                "for your review.\n\n"
                "We look forward to discussing the opportunity "
                "with you.\n\n"
                "Best regards,\n"
                "AAMP Team"
            )

            email.set_content(proposal_message)
            
            conversation_message = (
                f"{proposal_message}\n\n"
                f"📎 Attachment: {attachment_filename}"
            )

            # ---------------------------------------------
            # Attach proposal
            # ---------------------------------------------

            maintype, subtype = (
                attachment_content_type.split("/", 1)
                if "/" in attachment_content_type
                else ("application", "pdf")
            )

            email.add_attachment(
                attachment_bytes,
                maintype=maintype,
                subtype=subtype,
                filename=attachment_filename,
            )

            now = datetime.now(timezone.utc)

            # ---------------------------------------------
            # Send email
            # ---------------------------------------------

            try:

                with smtplib.SMTP(
                    self.smtp_host,
                    self.smtp_port,
                ) as smtp:

                    smtp.starttls()

                    smtp.login(
                        self.smtp_username,
                        self.smtp_password,
                    )

                    smtp.send_message(email)

            except Exception as exc:

                logger.exception(
                    "Failed to send proposal email: %s",
                    campaign_id,
                )

                raise RuntimeError(
                    f"Proposal email sending failed: {exc}"
                ) from exc

            # ---------------------------------------------
            # Save outbound conversation message
            # ---------------------------------------------

            conversation = ConversationMessage(
                campaign_id=campaign.id,
                college_id=campaign.college_id,
                direction="outbound",
                sender_email=self.from_address,
                recipient_email=recipient,
                subject=email["Subject"],
                message=conversation_message,
                status="sent",
                sent_at=now,
                created_at=now,
            )

            session.add(conversation)

            # ---------------------------------------------
            # Keep campaign in replied state
            # ---------------------------------------------

            campaign.status = "replied"

            session.commit()

            return {
                "campaign_id": campaign.id,
                "recipient": recipient,
                "subject": email["Subject"],
                "attachment": attachment_filename,
                "sent": True,
                "sent_at": now,
                "status": campaign.status,
            }

    # ============================================================
    # Get information package files
    # ============================================================

    @staticmethod
    def _get_information_package_files() -> list[Path]:
        """
        Return the six standard information package files
        in the required order.
        """

        package_files = []

        for base_name in INFORMATION_PACKAGE_FILES:

            matches = list(
                INFORMATION_PACKAGE_DIR.glob(
                    f"{base_name}.*"
                )
            )

            if not matches:
                raise ValueError(
                    "Information package file not found: "
                    f"{base_name}.*"
                )

            if len(matches) > 1:
                raise ValueError(
                    "Multiple files found for information "
                    f"package item '{base_name}'. "
                    "Keep only one file."
                )

            package_files.append(matches[0])

        return package_files

    # ============================================================
    # Send standard information package
    # ============================================================

    def send_information_package(
        self,
        campaign_id: int,
    ) -> dict:
        """
        Send the standard AAMP information package.

        Attachments are always sent in this order:

            1. Course / Training Information
            2. Brochure
            3. 1-Day Workshop
            4. 2-Day Workshop
            5. 3-Day Workshop
        """

        with Session(engine) as session:

            # ----------------------------------------------------
            # 1. Get campaign
            # ----------------------------------------------------

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id
                )
            )

            if campaign is None:
                raise ValueError(
                    f"Campaign not found: {campaign_id}"
                )

            # ----------------------------------------------------
            # 2. Validate campaign
            # ----------------------------------------------------

            if campaign.channel != "email":
                raise ValueError(
                    "Campaign channel is not email."
                )

            if campaign.status not in {
                "replied",
                "proposal",
                "action_required",
            }:
                raise ValueError(
                    "Information package can only be sent "
                    "for a campaign requiring a response. "
                    f"Current status: {campaign.status}"
                )

            # ----------------------------------------------------
            # 3. Get latest inbound message
            # ----------------------------------------------------

            inbound_message = session.scalar(
                select(ConversationMessage)
                .where(
                    ConversationMessage.campaign_id == campaign_id,
                    ConversationMessage.direction == "inbound",
                )
                .order_by(
                    ConversationMessage.received_at.desc()
                )
            )

            if inbound_message is None:
                raise ValueError(
                    "No inbound college response found."
                )

            # ----------------------------------------------------
            # 4. Determine recipient
            # ----------------------------------------------------

            if self.test_mode:

                if not self.test_recipient:
                    raise ValueError(
                        "EMAIL_TEST_RECIPIENT "
                        "is not configured."
                    )

                recipient = self.test_recipient

            else:

                recipient = inbound_message.sender_email

                if not recipient:
                    raise ValueError(
                        "The inbound message does not contain "
                        "a valid sender email."
                    )

            # ----------------------------------------------------
            # 5. Validate SMTP configuration
            # ----------------------------------------------------

            if not self.smtp_username:
                raise ValueError(
                    "EMAIL_SMTP_USERNAME is not configured."
                )

            if not self.smtp_password:
                raise ValueError(
                    "EMAIL_SMTP_PASSWORD is not configured."
                )

            if not self.from_address:
                raise ValueError(
                    "EMAIL_FROM_ADDRESS is not configured."
                )

            # ----------------------------------------------------
            # 6. Find six information package files
            # ----------------------------------------------------

            package_files = (
                self._get_information_package_files()
            )

            # ----------------------------------------------------
            # 7. Build subject
            # ----------------------------------------------------

            original_subject = (
                campaign.subject
                or "AI Training & Workshop Information"
            )

            subject = (
                original_subject
                if original_subject.lower().startswith("re:")
                else f"Re: {original_subject}"
            )

            # ----------------------------------------------------
            # 8. Build email body
            # ----------------------------------------------------

            information_message = (
                "Dear Sir/Madam,\n\n"

                "Thank you for your response.\n\n"

                "As requested, please find attached our "
                "standard information package covering "
                "our AI training and workshop offerings.\n\n"

                "The attached information includes:\n\n"

                "1. Course / Training Information\n"
                "2. Brochure\n"
                "3. 1-Day Workshop Information\n"
                "4. 2-Day Workshop Information\n"
                "5. 3-Day Workshop Information\n\n"

                "Please review the information and let us know "
                "which program or workshop would be of interest "
                "to your institution.\n\n"

                "Based on your interest, we can provide the "
                "relevant proposal or arrange a discussion "
                "accordingly.\n\n"

                "We look forward to hearing from you.\n\n"

                "Best regards,\n"
                "AAMP Team"
            )

            # ----------------------------------------------------
            # 9. Create email
            # ----------------------------------------------------

            email = EmailMessage()

            email["From"] = (
                f"{self.from_name} "
                f"<{self.from_address}>"
            )

            email["To"] = recipient
            email["Subject"] = subject

            email.set_content(
                information_message
            )

            # ----------------------------------------------------
            # 10. Attach six files
            # ----------------------------------------------------

            attachment_names = []

            for file_path in package_files:

                mime_type, _ = mimetypes.guess_type(
                    file_path.name
                )

                if mime_type:
                    maintype, subtype = mime_type.split(
                        "/",
                        1,
                    )
                else:
                    maintype = "application"
                    subtype = "octet-stream"

                with file_path.open("rb") as file:

                    file_bytes = file.read()

                email.add_attachment(
                    file_bytes,
                    maintype=maintype,
                    subtype=subtype,
                    filename=file_path.name,
                )

                attachment_names.append(
                    file_path.name
                )

            # ----------------------------------------------------
            # 11. Send email
            # ----------------------------------------------------

            now = datetime.now(timezone.utc)

            try:

                with smtplib.SMTP(
                    self.smtp_host,
                    self.smtp_port,
                    timeout=120,
                ) as smtp:

                    print("INFO PACKAGE: SMTP CONNECTED")

                    smtp.starttls()
                    print("INFO PACKAGE: STARTTLS COMPLETE")

                    smtp.login(self.smtp_username, self.smtp_password)
                    print("INFO PACKAGE: SMTP LOGIN COMPLETE")

                    smtp.send_message(email)
                    print("INFO PACKAGE: SMTP SEND COMPLETE")

            except Exception as exc:

                logger.exception(
                    "Failed to send information package: %s",
                    campaign_id,
                )

                raise RuntimeError(
                    f"Information package sending failed: {exc}"
                ) from exc

            # ----------------------------------------------------
            # 12. Save outbound conversation
            # ----------------------------------------------------

            conversation_message = (
                f"{information_message}\n\n"
                "📎 Attachments:\n"
                + "\n".join(
                    f"- {name}"
                    for name in attachment_names
                )
            )

            conversation = ConversationMessage(
                campaign_id=campaign.id,
                college_id=campaign.college_id,
                direction="outbound",
                sender_email=self.from_address,
                recipient_email=recipient,
                subject=subject,
                message=conversation_message,
                status="sent",
                sent_at=now,
                created_at=now,
            )

            session.add(conversation)

            # ----------------------------------------------------
            # 13. Keep campaign active
            # ----------------------------------------------------

            campaign.status = "replied"

            # Important:
            # Do NOT schedule another automatic follow-up here.
            #
            # We are now waiting for the college to respond
            # to the information package.
            print("INFO PACKAGE: BEFORE COMMIT")

            session.commit()
            print("INFO PACKAGE: COMMIT COMPLETE")

            # ----------------------------------------------------
            # 14. Return result
            # ----------------------------------------------------

            return {
                "campaign_id": campaign.id,
                "recipient": recipient,
                "subject": subject,
                "attachments": attachment_names,
                "attachment_count": len(
                    attachment_names
                ),
                "sent": True,
                "sent_at": now,
                "status": campaign.status,
            }