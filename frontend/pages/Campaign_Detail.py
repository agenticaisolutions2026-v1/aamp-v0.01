import streamlit as st
import requests
import textwrap
import base64

from services.campaign_service import CampaignService
from services.college_service import CollegeService
from components.common import init_page
from datetime import datetime
from zoneinfo import ZoneInfo



BASE_URL = "http://127.0.0.1:8000/api/v1"


init_page("Campaign Detail")


# =========================================================
# GET SELECTED CAMPAIGN
# =========================================================

campaign_id = st.session_state.get(
    "selected_campaign_id"
)


# =========================================================
# SAFETY CHECK
# =========================================================

if not campaign_id:

    st.warning(
        "No campaign selected."
    )

    if st.button("← Back to Campaigns"):

        st.switch_page(
            "Pages/Campaigns.py"
        )

    st.stop()


# =========================================================
# LOAD CAMPAIGN
# =========================================================

try:

    campaign = CampaignService.get_by_id(
        campaign_id
    )

except Exception as exc:

    st.error(
        f"Failed to load campaign: {exc}"
    )
    st.stop()


if not campaign:

    st.error(
        f"Campaign #{campaign_id} was not found."
    )
    st.stop()

# =========================================================
# LOAD COLLEGE
# =========================================================

try:

    college = CollegeService.get_by_id(
        campaign["college_id"]
    )

except Exception as exc:

    st.error(
        f"Failed to load college: {exc}"
    )
    st.stop()


if not college:

    st.error(
        f"College #{campaign['college_id']} was not found."
    )
    st.stop()

# ============================================================
# LOAD CONVERSATION
# ============================================================

try:

    messages = CampaignService.get_messages(
        campaign_id
    )

except Exception:

    messages = []


# ============================================================
# CHECK WHETHER PROPOSAL WAS ALREADY SENT
# ============================================================

proposal_sent = any(
    str(item.get("direction", "")).lower() == "outbound"
    and (
        "Please find attached the requested proposal"
        in str(item.get("message", ""))
    )
    for item in messages
)


# =========================================================
# PAGE HEADER
# =========================================================

if st.button("← Back to Campaigns"):

    st.switch_page(
        "Pages/Campaigns.py"
    )


st.title(
    f"Campaign #{campaign_id}"
)


st.caption(
    "Campaign details and automation status."
)


# ============================================================
# STEP-1:AUTO CAMPAIGN FLOW
# ============================================================

st.markdown("### 🤖 Auto Campaign Flow")

status = str(campaign.get("status", "")).lower()
response_category = str(
    campaign.get("response_category", "")
).upper()
follow_up_count = campaign.get("follow_up_count", 0) or 0

is_opt_out_completed = (
    response_category == "OPT_OUT"
    and status == "completed"
)

email_sent = status in [
    "sent",
    "delivered",
    "replied",
    "follow_up_due",
    "proposal",
    "action_required",
    "completed",
    "closed",
    "opted_out",
]

followup_1_done = follow_up_count >= 1
followup_2_done = follow_up_count >= 2

campaign_completed = status in {
    "completed",
    "closed",
}


# ------------------------------------------------------------
# Campaign state
# ------------------------------------------------------------

response_received = bool(
    campaign.get("last_response_at")
)

is_opted_out = status == "opted_out"

is_response_flow = (
    response_received
    or status in [
        "replied",
        "proposal",
        "action_required",
    ]
)

is_approval_pending = status in [
    "draft",
    "rejected",
]

is_waiting_for_response = (
    email_sent
    and not is_response_flow
    and not is_opted_out
)


# ------------------------------------------------------------
# Current stage
# ------------------------------------------------------------

if is_opted_out:

    current_stage = "Campaign Opted Out"

elif is_response_flow:

    if campaign_completed:

        current_stage = "Campaign Completed"

    else:

        current_stage = "Human Action Required"

elif is_approval_pending:

    current_stage = "Human Approval"

elif followup_2_done:

    current_stage = "Final Response Check"

elif followup_1_done:

    current_stage = "Follow-up #2"

elif email_sent:

    current_stage = "Waiting for College Response"

elif status in [
    "approved",
    "queued",
]:

    current_stage = "Email Sending"

else:

    current_stage = "Human Approval"


# ------------------------------------------------------------
# Campaign steps
# ------------------------------------------------------------

if is_opted_out:

    # ----------------------------------------
    # PATH 4: OPTED OUT
    # ----------------------------------------

    steps = [
        "Qualified Lead",
        "Campaign Strategy",
        "Personalization",
        "Human Approval",
        "Email Sent",
        "Response Received",
        "Response Classified",
        "Campaign Opted Out",
    ]

elif is_response_flow:

    # ----------------------------------------
    # PATH 3: RESPONSE RECEIVED
    # ----------------------------------------

    steps = [
        "Qualified Lead",
        "Campaign Strategy",
        "Personalization",
        "Human Approval",
        "Email Sent",
        "Response Received",
        "Response Classified",
        "Human Action Required",
        "Campaign Completed",
    ]

else:

    # ----------------------------------------
    # PATH 1 + 2:
    # APPROVAL / NO RESPONSE / FOLLOW-UPS
    # ----------------------------------------

    steps = [
        "Qualified Lead",
        "Campaign Strategy",
        "Personalization",
        "Human Approval",
        "Email Sent",
        "Waiting for College Response",
        "Follow-up #1",
        "Follow-up #2",
        "Final Response Check",
        "Campaign Completed",
    ]


# ------------------------------------------------------------
# Completed steps
# ------------------------------------------------------------

completed_steps = {

    "Qualified Lead": True,

    "Campaign Strategy": True,

    "Personalization": True,

    "Human Approval": (
        email_sent
        or is_response_flow
        or is_opted_out
    ),

    "Email Sent": email_sent,

    # ----------------------------------------
    # NO-RESPONSE FLOW
    # ----------------------------------------

    "Waiting for College Response": (
        email_sent
        and not is_response_flow
        and not is_opted_out
    ),

    "Follow-up #1": (
        followup_1_done
        and not is_response_flow
        and not is_opted_out
    ),

    "Follow-up #2": (
        followup_2_done
        and not is_response_flow
        and not is_opted_out
    ),

    "Final Response Check": (
        campaign_completed
        and not is_response_flow
        and not is_opted_out
    ),

    # ----------------------------------------
    # RESPONSE FLOW
    # ----------------------------------------

    "Response Received": (
        is_response_flow
        or is_opted_out
    ),

    "Response Classified": (
        (
            is_response_flow
            or is_opted_out
        )
        and bool(
            campaign.get("response_category")
        )
    ),

    "Human Action Required": (
        is_response_flow
        and not is_opted_out
        and not campaign_completed
    ),

    "Campaign Completed": (
        campaign_completed
        and not is_opted_out
    ),

    # ----------------------------------------
    # OPT-OUT FLOW
    # ----------------------------------------

    "Campaign Opted Out": is_opted_out,
}

# ============================================================
# FLOW BOX
# ============================================================

with st.container(border=True):

    for index, step in enumerate(steps):

        completed = completed_steps.get(step, False)
        current = step == current_stage

        # ----------------------------------------------------
        # COMPLETED STEP
        # ----------------------------------------------------

        if completed and not current:

            st.markdown(
                f"**:green[✓]**  {step}"
            )

        # ----------------------------------------------------
        # CURRENT STEP
        # ----------------------------------------------------

        elif current:

            if step == "Campaign Opted Out":

                st.markdown(
                    f"**:red[🛑 {step}]**"
                )

            else:

                st.markdown(
                    f"**:blue[🔵 {step}]**"
                )

            if step == "Waiting for College Response":

                next_time = campaign.get(
                    "next_follow_up_at"
                )

                if next_time:
                    next_time_display = str(next_time)[:16]
                else:
                    next_time_display = "Scheduled automatically"

                with st.container(border=True):

                    st.markdown(
                        "**NEXT AUTOMATIC ACTION**"
                    )

                    st.markdown(
                        "**Follow-up #1**"
                    )

                    st.markdown(
                        f"**{next_time_display}**"
                    )

            elif step == "Follow-up #1":

                next_time = campaign.get("next_follow_up_at")

                with st.container(border=True):

                    st.markdown("**NEXT AUTOMATIC ACTION**")
                    st.markdown("**Follow-up #2**")

                    if next_time:
                        st.markdown(f"**{str(next_time)[:16]}**")
                    else:
                        st.markdown("**Not scheduled**")

            elif step == "Follow-up #2":

                next_time = campaign.get("next_follow_up_at")

                if next_time:
                    next_time_display = str(next_time)[:16]
                else:
                    next_time_display = "Not scheduled"

                with st.container(border=True):

                    st.markdown(
                        "**NEXT AUTOMATIC ACTION**"
                    )

                    st.markdown(
                        "**Final Response Check**"
                    )

                    st.markdown(
                        f"**{next_time_display}**"
                    )

            elif step == "Final Response Check":

                with st.container(border=True):

                    st.markdown(
                        "**NEXT AUTOMATIC ACTION**"
                    )

                    st.markdown(
                        "**Complete campaign if no response**"
                    )

            elif step == "Campaign Completed":

                st.success(
                    "No action required"
                )

        # ----------------------------------------------------
        # FUTURE STEP
        # ----------------------------------------------------

        else:

            st.markdown(
                f"○  {step}"
            )

        # ----------------------------------------------------
        # VERTICAL CONNECTOR
        # ----------------------------------------------------

        if index < len(steps) - 1:

            st.markdown(
                """
                <div style="
                    width: 2px;
                    height: 12px;
                    background-color: #6b7280;
                    margin-left: 8px;
                    margin-top: -2px;
                    margin-bottom: -2px;
                "></div>
                """,
                unsafe_allow_html=True,
            )

# ============================================================
# STEP-2: OUTREACH SCHEDULE
# ============================================================
st.markdown(
    """
    <style>

    .status-sent {
        color: #22c55e;
        font-weight: 600;
    }

    .status-received {
        color: #3b82f6;
        font-weight: 600;
    }

    .status-not-required {
        color: #94a3b8;
        font-weight: 600;
    }

    .status-pending {
        color: #f59e0b;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 📤Outreach Schedule")

sent_at = campaign.get("sent_at")
next_follow_up_at = campaign.get("next_follow_up_at")
follow_up_count = campaign.get("follow_up_count", 0) or 0
last_response_at = campaign.get("last_response_at")
failure_reason = campaign.get("failure_reason")

response_received = (
    bool(last_response_at)
    or status in [
        "replied",
        "proposal",
        "action_required",
        "closed",
    ]
)

campaign_closed = status in {
    "completed",
    "closed",
}


with st.container(border=True):

    # --------------------------------------------------------
    # Initial Email
    # --------------------------------------------------------

    if status == "failed":
        st.markdown(
            "❌ **Initial Email** · "
            '<span style="color:#ef4444; font-weight:600;">Failed</span>',
            unsafe_allow_html=True,
        )

        if failure_reason:
            # Strip leading indentation to prevent Streamlit from rendering HTML as a code block
            st.markdown(
                f"""
    <div style="margin: 6px 0 14px 28px; padding: 10px 14px; border-left: 3px solid #ef4444; background: rgba(239, 68, 68, 0.08); border-radius: 6px;">
        <div style="font-weight: 600; margin-bottom: 4px; color: #1e293b;">Failure Reason</div>
        <div style="font-size: 14px; color: #64748b;">{failure_reason}</div>
    </div>
    """,
                unsafe_allow_html=True,
            )

    else:
        if sent_at:
            # Inline styling replaces class="status-sent" to guarantee styling without external CSS
            st.markdown(
                f"✅ **Initial Email** · "
                f"{str(sent_at)[:16]} · "
                f'<span style="color:#10b981; font-weight:600; background:rgba(16, 185, 129, 0.1); padding:2px 8px; border-radius:4px;">Sent</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("⬜ **Initial Email** · Pending")

    # ========================================================
    # FAILED OUTREACH BRANCH
    # ========================================================

    if status == "failed":

        # ----------------------------------------------------
        # Outreach Failed
        # ----------------------------------------------------

        st.markdown(
            "🛑 **Outreach Stopped** · "
            '<span style="color:#ef4444;font-weight:600;">'
            "Initial email failed"
            "</span>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # Follow-up #1
        # ----------------------------------------------------

        st.markdown(
            "— **Follow-up #1** · "
            '<span style="color:#94a3b8;font-weight:600;">'
            "Not scheduled — initial email failed"
            "</span>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # Follow-up #2
        # ----------------------------------------------------

        st.markdown(
            "— **Follow-up #2** · "
            '<span style="color:#94a3b8;font-weight:600;">'
            "Not scheduled — initial email failed"
            "</span>",
            unsafe_allow_html=True,
        )

    # ========================================================
    # OPT-OUT BRANCH
    # ========================================================

    elif status == "opted_out":

        # ----------------------------------------------------
        # College Response
        # ----------------------------------------------------

        if last_response_at:

            st.markdown(
                f"🟦 **College Response** · "
                f"{str(last_response_at)[:16]} · "
                '<span class="status-received">Received</span>',
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                "🟦 **College Response** · "
                '<span class="status-received">'
                "Received"
                "</span>",
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # Follow-up #1
        # ----------------------------------------------------

        st.markdown(
            "— **Follow-up #1** · "
            '<span class="status-not-required">'
            "Not required — opt out"
            "</span>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # Follow-up #2
        # ----------------------------------------------------

        st.markdown(
            "— **Follow-up #2** · "
            '<span class="status-not-required">'
            "Not required — opt out"
            "</span>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # Outreach Stopped
        # ----------------------------------------------------

        st.markdown(
            "🛑 **Outreach Stopped** · "
            '<span style="color:#ef4444;font-weight:600;">'
            "Opted out"
            "</span>",
            unsafe_allow_html=True,
        )


    # ========================================================
    # RESPONSE BRANCH
    # ========================================================

    elif response_received:

        # ----------------------------------------------------
        # College Response
        # ----------------------------------------------------

        if last_response_at:

            st.markdown(
                f"🟦 **College Response** · "
                f"{str(last_response_at)[:16]} · "
                f'<span class="status-received">Received</span>',
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                "🟦 **College Response** · "
                '<span class="status-received">'
                "Received"
                "</span>",
                unsafe_allow_html=True,
            )


        # ----------------------------------------------------
        # Follow-ups skipped
        # ----------------------------------------------------

        st.markdown(
            "— **Follow-up #1** · "
            '<span class="status-not-required">'
            "Not required — response received"
            "</span>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "— **Follow-up #2** · "
            '<span class="status-not-required">'
            "Not required — response received"
            "</span>",
            unsafe_allow_html=True,
        )


        # ----------------------------------------------------
        # Final Response Check
        # ----------------------------------------------------

        if campaign_closed:

            st.markdown(
                "✅ **Final Response Check**  ·  "
                "**Completed**"
            )

        else:

            st.markdown(
                "⬜ **Final Response Check** · "
                '<span class="status-pending">'
                "Pending campaign closure"
                "</span>",
                unsafe_allow_html=True,
            )




    # ========================================================
    # NO RESPONSE BRANCH
    # ========================================================

    else:

        # ----------------------------------------------------
        # Follow-up #1
        # ----------------------------------------------------

        if follow_up_count >= 1:

            st.markdown(
                "✅ **Follow-up #1**  ·  **Sent**"
            )

        elif next_follow_up_at:

            st.markdown(
                f"⬜ **Follow-up #1**  ·  "
                f"{str(next_follow_up_at)[:16]}  ·  **Pending**"
            )

        else:

            st.markdown(
                "⬜ **Follow-up #1**  ·  Scheduled"
            )


        # ----------------------------------------------------
        # Follow-up #2
        # ----------------------------------------------------

        if follow_up_count >= 2:

            st.markdown(
                "✅ **Follow-up #2**  ·  **Sent**"
            )

        elif follow_up_count >= 1:

            st.markdown(
                "⬜ **Follow-up #2**  ·  Scheduled"
            )

        else:

            st.markdown(
                "⬜ **Follow-up #2**  ·  Waiting for Follow-up #1"
            )


        # ----------------------------------------------------
        # Final Response Check
        # ----------------------------------------------------

        if campaign_closed:

            st.markdown(
                "✅ **Final Response Check**  ·  **Completed**"
            )

        else:

            st.markdown(
                "⬜ **Final Response Check**  ·  Scheduled"
            )

# ============================================================
# STEP-3: CONVERSATION
# ============================================================

st.markdown("### 💬 Conversation")

messages = CampaignService.get_messages(campaign_id)

if not messages:

    with st.container(border=True):
        st.caption("No conversation yet.")

else:

    # --------------------------------------------------------
    # Separate messages by direction
    # --------------------------------------------------------

    sent_messages = []
    inbox_messages = []

    for msg in messages:

        direction = str(
            msg.get("direction", "")
        ).lower()

        if direction == "inbound":
            inbox_messages.append(msg)
        else:
            sent_messages.append(msg)


    # ========================================================
    # SENT MESSAGES
    # ========================================================

    with st.expander(
        f"📤 Sent Messages ({len(sent_messages)})",
        expanded=False,
    ):

        if not sent_messages:

            st.caption("No sent messages.")

        else:

            for index, msg in enumerate(sent_messages):

                sender_email = (
                    msg.get("sender_email")
                    or msg.get("from_email")
                    or msg.get("from")
                    or ""
                )

                recipient_email = (
                    msg.get("recipient_email")
                    or msg.get("to_email")
                    or msg.get("to")
                    or ""
                )

                subject = (
                    msg.get("subject")
                    or campaign.get("subject")
                    or ""
                )

                message_text = (
                    msg.get("message")
                    or msg.get("body")
                    or msg.get("content")
                    or ""
                )

                created_at = (
                    msg.get("created_at")
                    or msg.get("sent_at")
                    or msg.get("received_at")
                    or ""
                )

                st.markdown(
                    f"✉️ **You** · {str(created_at)[:16]}"
                )

                st.markdown(
                    f"**From:** {sender_email}"
                )

                st.markdown(
                    f"**To:** {recipient_email}"
                )

                st.markdown(
                    f"**Subject:** {subject}"
                )

           

                st.markdown(
                    f"""
                    <div style="
                        background: rgba(59,130,246,0.08);
                        border: 1px solid rgba(59,130,246,0.20);
                        border-radius: 8px;
                        padding: 12px 14px;
                        margin-top: 8px;
                        margin-bottom: 14px;
                        color: inherit;
                        font-size: 14px;
                        line-height: 1.6;
                    ">
                        {message_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if index < len(sent_messages) - 1:
                    st.markdown("---")


    # ========================================================
    # INBOX
    # ========================================================

    with st.expander(
        f"📥 Inbox ({len(inbox_messages)})",
        expanded=False,
    ):

        if not inbox_messages:

            st.caption("No incoming messages.")

        else:

            for index, msg in enumerate(inbox_messages):

                sender_email = (
                    msg.get("sender_email")
                    or msg.get("from_email")
                    or msg.get("from")
                    or ""
                )

                recipient_email = (
                    msg.get("recipient_email")
                    or msg.get("to_email")
                    or msg.get("to")
                    or ""
                )

                subject = (
                    msg.get("subject")
                    or campaign.get("subject")
                    or ""
                )

                message_text = (
                    msg.get("message")
                    or msg.get("body")
                    or msg.get("content")
                    or ""
                )

                created_at = (
                    msg.get("created_at")
                    or msg.get("sent_at")
                    or msg.get("received_at")
                    or ""
                )

                st.markdown(
                    f"🏫 **College** · {str(created_at)[:16]}"
                )

                st.markdown(
                    f"**From:** {sender_email}"
                )

                st.markdown(
                    f"**To:** {recipient_email}"
                )

                st.markdown(
                    f"**Subject:** {subject}"
                )

               

                st.markdown(
                    f"""
                    <div style="
                        background: rgba(34,197,94,0.08);
                        border: 1px solid rgba(34,197,94,0.20);
                        border-radius: 8px;
                        padding: 12px 14px;
                        margin-top: 8px;
                        margin-bottom: 14px;
                        color: inherit;
                        font-size: 14px;
                        line-height: 1.6;
                    ">
                        {message_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if index < len(inbox_messages) - 1:
                    st.markdown("---")

# ============================================================
# STEP-4: RESPONSE ANALYSIS
# ============================================================

st.markdown("### 📩 Response Analysis")

response_category = campaign.get("response_category")


# ------------------------------------------------------------
# Response interpretation
# ------------------------------------------------------------

response_interpretations = {
    "REQUEST_PROPOSAL":
        "The college has requested a proposal for the proposed training or workshop opportunity.",
    "REQUEST_MEETING":
        "The college is interested in discussing the opportunity through a meeting.",
    "REQUEST_CALL":
        "The college has requested a call to discuss the opportunity further.",
    "NEEDS_INFORMATION":
        "The college is asking for additional information before deciding on the opportunity.",
    "INTERESTED":
        "The college has expressed interest in the proposed opportunity.",
    "ASK_LATER":
        "The college has asked to be contacted at a later time.",
    "NOT_INTERESTED":
        "The college has indicated that it is not interested in the current opportunity.",
    "WRONG_CONTACT":
        "The response indicates that the recipient may not be the appropriate contact.",
    "OUT_OF_OFFICE":
        "The contact is currently unavailable or out of office.",
    "UNCLEAR":
        "The response could not be confidently interpreted and requires human review.",
    "OPT_OUT":
        "The college has asked to stop further outreach.",
}


# ------------------------------------------------------------
# Campaign impact
# ------------------------------------------------------------

response_impacts = {
    "REQUEST_PROPOSAL":
        "Automated follow-ups are paused while the proposal request is reviewed.",
    "REQUEST_MEETING":
        "Automated follow-ups are paused while the meeting request is reviewed.",
    "REQUEST_CALL":
        "Automated follow-ups are paused while the call request is reviewed.",
    "NEEDS_INFORMATION":
        "Automated follow-ups are paused. Human review is needed to decide what information should be sent.",
    "INTERESTED":
        "Automated follow-ups are paused while the interested response is reviewed.",
    "ASK_LATER":
        "Further outreach should wait until the requested follow-up period.",
    "NOT_INTERESTED":
        "No further automated outreach should be sent unless the campaign is reopened.",
    "WRONG_CONTACT":
        "Further outreach should stop until the correct contact is identified.",
    "OUT_OF_OFFICE":
        "Further action should wait until the contact becomes available.",
    "UNCLEAR":
        "Human review is required before deciding the next campaign action.",
    "OPT_OUT":
        "All further automated outreach should stop.",
}

with st.container(border=True):

    # ========================================================
    # RESPONSE RECEIVED
    # ========================================================

    if last_response_at:

        st.markdown(
            """
            <div style="
                font-size: 15px;
                font-weight: 700;
                margin-bottom: 18px;
            ">
                🤖 AI Response Analysis
            </div>
            """,
            unsafe_allow_html=True,
        )

        if response_category:

            category = str(
                response_category
            ).upper()

            interpretation = response_interpretations.get(
                category,
                "The response has been classified by the AI response analysis system."
            )

            impact = response_impacts.get(
                category,
                "Human review is required before deciding the next campaign action."
            )

            # ------------------------------------------------
            # RESPONSE TYPE
            # ------------------------------------------------

            st.markdown(
                """
                <div style="
                    color: #94a3b8;
                    font-size: 12px;
                    font-weight: 600;
                    margin-bottom: 6px;
                ">
                    RESPONSE TYPE
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div style="
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 6px;
                    background: rgba(59,130,246,0.12);
                    border: 1px solid rgba(59,130,246,0.25);
                    color: #60a5fa;
                    font-size: 13px;
                    font-weight: 700;
                    margin-bottom: 18px;
                ">
                    ● {category}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ------------------------------------------------
            # WHAT THIS MEANS
            # ------------------------------------------------

            st.markdown(
                """
                <div style="
                    color: #cbd5e1;
                    font-size: 13px;
                    font-weight: 700;
                    margin-bottom: 5px;
                ">
                    💡 What this means
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div style="
                    color: #94a3b8;
                    font-size: 13px;
                    line-height: 1.6;
                    margin-bottom: 18px;
                ">
                    {interpretation}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ------------------------------------------------
            # CAMPAIGN IMPACT
            # ------------------------------------------------

            st.markdown(
                """
                <div style="
                    color: #f59e0b;
                    font-size: 13px;
                    font-weight: 700;
                    margin-bottom: 5px;
                ">
                    ⚠️ Campaign Impact
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div style="
                    color: #94a3b8;
                    font-size: 13px;
                    line-height: 1.6;
                ">
                    {impact}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                <div style="
                    color: #cbd5e1;
                    font-size: 13px;
                    font-weight: 600;
                ">
                    📨 Response received
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                "AI response analysis is pending. "
                "The response will be classified before "
                "the next campaign action is determined."
            )

    # ========================================================
    # NO RESPONSE
    # ========================================================

    else:

        st.markdown(
            """
            <div style="
                font-size: 15px;
                font-weight: 700;
                margin-bottom: 8px;
            ">
                ⏳ Waiting for college response
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "AI response analysis will appear when a response "
            "is received."
        )


# ============================================================
# STEP-5: ACTION REQUIRED
# ============================================================

st.markdown("### ⚡ Action Required")

response_category = campaign.get("response_category")

with st.container(border=True):

    if not last_response_at:

        st.markdown(
            """
            <div style="
                font-size: 15px;
                font-weight: 700;
                margin-bottom: 6px;
            ">
                ⏳ No action required yet
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Action options will appear after a college response "
            "is received and analyzed."
        )

    elif not response_category:

        st.markdown(
            """
            <div style="
                font-size: 15px;
                font-weight: 700;
                margin-bottom: 6px;
            ">
                🔍 Response analysis pending
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "The response must be classified before the next "
            "campaign action can be selected."
        )

    else:

        category = str(
            response_category
        ).upper()

        st.markdown(
            """
            <div style="
                font-size: 15px;
                font-weight: 700;
                margin-bottom: 6px;
            ">
                🤖 Recommended Next Actions
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="
                color: #94a3b8;
                font-size: 12px;
                margin-bottom: 18px;
            ">
                Based on response type:
                <span style="
                    color: #60a5fa;
                    font-weight: 700;
                ">
                    {category}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ====================================================
        # REQUEST PROPOSAL
        # ====================================================


        if category == "REQUEST_PROPOSAL":

            # ====================================================
            # PROPOSAL ALREADY SENT
            # ====================================================

            if proposal_sent:

                st.success("Proposal sent successfully.")

                st.markdown(
                    textwrap.dedent("""
                        <div style="margin-top: 10px; padding: 14px 16px; border-radius: 8px; background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.35);">
                            <div style="color: #4ade80; font-size: 14px; font-weight: 700;">📄 Status: Proposal Delivered</div>
                            <div style="color: #94a3b8; font-size: 12px; margin-top: 6px;">The requested proposal has already been sent.</div>
                        </div>
                    """),
                    unsafe_allow_html=True,
                )

            # ====================================================
            # PROPOSAL NOT SENT
            # ====================================================

            else:

                st.info(
                    "The college has requested a proposal. "
                    "Attach the appropriate proposal file and send it."
                )

                # existing Review & Send Proposal workflow

            if st.button(
                "📄 Review & Send Proposal",
                key=f"review_send_proposal_{campaign_id}",
                use_container_width=True,
            ):
                st.session_state["selected_campaign_action"] = "send_proposal"
                st.session_state["show_proposal_workflow"] = True

            # ------------------------------------------------
            # PROPOSAL WORKFLOW
            # ------------------------------------------------

            if st.session_state.get("show_proposal_workflow", False):

                st.markdown("#### 📄 Proposal")

                st.caption(
                    "Select an existing proposal file to attach to this response."
                )

                proposal_file = st.file_uploader(
                    "Choose proposal file",
                    type=["pdf", "doc", "docx"],
                    key=f"proposal_file_{campaign_id}",
                )

                if proposal_file:

                    st.success(
                        f"Attached: {proposal_file.name}"
                    )

                    # Check top-level sending state
                    is_proposal_sent = st.session_state.get(f"proposal_sent_{campaign_id}", False)

                    if is_proposal_sent:
                        # ====================================================
                        # FINAL STEP: SUCCESS / DELIVERED STATE
                        # ====================================================
                        st.success("✅ Proposal sent successfully.")

                        st.markdown(
                            textwrap.dedent(f"""
                                <div style="padding: 14px 16px; border: 1px solid rgba(34,197,94,0.3); border-radius: 8px; background: rgba(34,197,94,0.08); margin-top: 10px;">
                                    <div style="font-size: 14px; font-weight: 700; color: #4ade80;">
                                        📨 Status: Proposal Delivered
                                    </div>
                                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                                        Attached file: {proposal_file.name} ({proposal_file.size / 1024:.1f} KB)
                                    </div>
                                </div>
                            """),
                            unsafe_allow_html=True,
                        )

                    else:
                        # ====================================================
                        # REVIEW & SEND FLOW
                        # ====================================================
                        st.markdown("#### 🔍 Review Proposal")

                        st.markdown(
                            textwrap.dedent(f"""
                                <div style="padding: 14px 16px; border: 1px solid #334155; border-radius: 8px; margin-top: 8px; margin-bottom: 14px;">
                                    <div style="font-size: 12px; color: #94a3b8; margin-bottom: 5px;">Attached proposal</div>
                                    <div style="font-size: 14px; font-weight: 600;">📎 {proposal_file.name}</div>
                                    <div style="font-size: 12px; color: #94a3b8; margin-top: 5px;">{proposal_file.size / 1024:.1f} KB</div>
                                </div>
                            """),
                            unsafe_allow_html=True,
                        )

                        if st.button(
                            "🔍 Preview Proposal PDF",
                            key=f"review_proposal_{campaign_id}",
                            use_container_width=True,
                        ):
                            st.session_state[f"proposal_reviewed_{campaign_id}"] = True

                        if st.session_state.get(f"proposal_reviewed_{campaign_id}", False):
                            st.success("Proposal reviewed and ready to send.")

                            # Embed PDF preview iframe
                            base64_pdf = base64.b64encode(proposal_file.getvalue()).decode("utf-8")
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)

                            if st.button(
                                "✉️ Send Proposal",
                                key=f"send_proposal_{campaign_id}",
                                use_container_width=True,
                            ):
                                try:
                                    files = {
                                        "proposal_file": (
                                            proposal_file.name,
                                            proposal_file.getvalue(),
                                            proposal_file.type or "application/pdf",
                                        )
                                    }

                                    with st.spinner("Sending proposal..."):
                                        response = requests.post(
                                            f"{BASE_URL}/campaigns/{campaign_id}/send-proposal",
                                            files=files,
                                            timeout=30,
                                        )

                                    if response.status_code == 200:
                                        st.session_state[f"proposal_sent_{campaign_id}"] = True
                                        st.session_state["proposal_ready_to_send"] = False
                                        st.rerun()

                                    else:
                                        try:
                                            error_detail = response.json().get("detail", "Failed to send proposal.")
                                        except Exception:
                                            error_detail = "Failed to send proposal."

                                        st.error(f"Unable to send proposal: {error_detail}")

                                except requests.exceptions.RequestException as exc:
                                    st.error(f"Could not connect to the backend: {exc}")
        # ====================================================
        # REQUEST MEETING
        # ====================================================

        elif category == "REQUEST_MEETING":

            st.info(
                "The college has requested a meeting."
            )

            # ------------------------------------------------
            # Meeting state — DB is the source of truth
            # ------------------------------------------------

            meeting_form_open = st.session_state.get(
                f"meeting_form_open_{campaign_id}",
                False,
            )

            meeting_details = None
            meeting_status = ""

            try:

                meeting_response = requests.get(
                    f"{BASE_URL}/campaigns/{campaign_id}/meetings/current",
                    timeout=15,
                )

                if meeting_response.status_code == 200:

                    meeting_data = meeting_response.json()

                    meeting_details = meeting_data.get("meeting")

                    if meeting_details and not meeting_form_open:

                        meeting_status = meeting_details.get(
                            "status",
                            "",
                        ).upper()

            except requests.RequestException:

                meeting_details = None

            # ====================================================
            # MEETING ALREADY SCHEDULED
            # ====================================================

            if meeting_details:

                if meeting_status == "SCHEDULED":
                    st.success("Meeting Scheduled")

                elif meeting_status == "MISSED":
                    st.error("Meeting Missed")

                elif meeting_status == "COMPLETED":
                    st.success("Meeting Completed")

                elif meeting_status == "CANCELLED":
                    st.warning("Meeting Cancelled")

                # ------------------------------------------------
                # Meeting date/time from DB
                # ------------------------------------------------

                meeting_datetime = datetime.fromisoformat(
                    meeting_details["meeting_date"]
                )

                meeting_date_display = meeting_datetime.strftime("%d %b %Y")
                meeting_time_display = meeting_datetime.strftime("%I:%M %p")

                st.markdown(
                    f"📅 **{meeting_date_display}** · "
                    f"🕐 **{meeting_time_display}**"
                )

                st.markdown(
                    f"⏱️ **{meeting_details['duration_minutes']} minutes** · "
                    f"🌐 **{meeting_details['mode'].title()}**"
                )

                # ------------------------------------------------
                # Meeting link
                # ------------------------------------------------

                if (
                    meeting_status == "SCHEDULED"
                    and meeting_details["mode"].lower() == "online"
                ):
                    meeting_link = meeting_details.get("meeting_link")
                    if meeting_link:
                        st.markdown(
                            f"🔗 **Meeting Link:** [Join Meeting]({meeting_link})"
                        )

                # ====================================================
                # ACTIVE MEETING ACTIONS
                # ====================================================

                if meeting_status == "SCHEDULED":

                    # ====================================================
                    # CONFIRMATION STATUS
                    # ====================================================

                    confirmation_sent = st.session_state.get(
                        f"confirmation_sent_{campaign_id}",
                        False,
                    )

                    # ====================================================
                    # CONFIRMATION ALREADY SENT
                    # ====================================================

                    if confirmation_sent:

                        st.markdown(
                            """
                            <div style="
                                margin-top: 14px;
                                padding: 10px 14px;
                                border-radius: 7px;
                                background: rgba(34,197,94,0.08);
                                border: 1px solid rgba(34,197,94,0.25);
                                font-size: 13px;
                                font-weight: 600;
                            ">
                                📨 Confirmation Sent
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            """
                            <div style="
                                margin-top: 14px;
                                margin-bottom: 8px;
                                font-size: 13px;
                                font-weight: 700;
                            ">
                                Next Action
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # ====================================================
                        # CHECK MEETING TIME
                        # ====================================================

                        meeting_datetime = datetime.fromisoformat(
                            meeting_details["meeting_date"]
                        )

                        current_datetime = datetime.now(
                            meeting_datetime.tzinfo
                        )

                        # ====================================================
                        # MEETING TIME NOT REACHED
                        # ====================================================

                        if current_datetime < meeting_datetime:

                            st.info(
                                f"⏳ Meeting scheduled for "
                                f"{meeting_datetime.strftime('%d %b %Y')} · "
                                f"{meeting_datetime.strftime('%I:%M %p')}"
                            )

                            # ====================================================
                            # UPCOMING MEETING ACTIONS
                            # ====================================================

                            action_col1, action_col2 = st.columns(2)

                            with action_col1:

                                if st.button(
                                    "↻ Reschedule Meeting",
                                    key=f"reschedule_upcoming_{campaign_id}",
                                    use_container_width=True,
                                ):

                                    st.session_state[
                                        f"reschedule_meeting_open_{campaign_id}"
                                    ] = True

                                    st.rerun()

                            with action_col2:

                                if st.button(
                                    "✕ Cancel Meeting",
                                    key=f"cancel_upcoming_{campaign_id}",
                                    use_container_width=True,
                                ):

                                    st.session_state[
                                        f"cancel_meeting_confirm_{campaign_id}"
                                    ] = True

                                    st.rerun()

                            # ====================================================
                            # CANCEL MEETING CONFIRMATION
                            # ====================================================

                            if st.session_state.get(
                                f"cancel_meeting_confirm_{campaign_id}",
                                False,
                            ):

                                st.warning(
                                    "Are you sure you want to cancel this meeting?"
                                )

                                cancel_col1, cancel_col2 = st.columns(2)

                                with cancel_col1:

                                    if st.button(
                                        "Keep Meeting",
                                        key=f"keep_meeting_{campaign_id}",
                                        use_container_width=True,
                                    ):

                                        st.session_state[
                                            f"cancel_meeting_confirm_{campaign_id}"
                                        ] = False

                                        st.rerun()

                                with cancel_col2:

                                    if st.button(
                                        "✕ Yes, Cancel Meeting",
                                        key=f"confirm_cancel_meeting_{campaign_id}",
                                        use_container_width=True,
                                    ):

                                        try:

                                            response = requests.post(
                                                f"{BASE_URL}/campaigns/{campaign_id}/meetings/"
                                                f"{meeting_details['id']}/cancel",
                                                timeout=30,
                                            )

                                            if response.status_code == 200:

                                                st.session_state[
                                                    f"cancel_meeting_confirm_{campaign_id}"
                                                ] = False

                                                st.success(
                                                    "Meeting cancelled successfully."
                                                )

                                                st.rerun()

                                            else:

                                                try:
                                                    error_detail = response.json().get(
                                                        "detail",
                                                        "Failed to cancel meeting.",
                                                    )
                                                except Exception:
                                                    error_detail = (
                                                        "Failed to cancel meeting."
                                                    )

                                                st.error(
                                                    f"Unable to cancel meeting: {error_detail}"
                                                )

                                        except requests.exceptions.RequestException as exc:

                                            st.error(
                                                f"Could not connect to the backend: {exc}"
                                            )

                        # ====================================================
                        # MEETING TIME REACHED / PASSED
                        # ====================================================

                        else:

                            st.info(
                                f"🔵 Meeting time reached — "
                                f"{meeting_datetime.strftime('%d %b %Y')} · "
                                f"{meeting_datetime.strftime('%I:%M %p')}"
                            )

                            meeting_col1, meeting_col2, meeting_col3 = st.columns(3)

                            with meeting_col1:

                                meeting_completed = st.button(
                                    "✓ Mark Completed",
                                    key=f"meeting_completed_{campaign_id}",
                                    use_container_width=True,
                                )

                            with meeting_col2:

                                meeting_cancelled = st.button(
                                    "✕ Cancelled",
                                    key=f"meeting_cancelled_{campaign_id}",
                                    use_container_width=True,
                                )

                            with meeting_col3:

                                if st.button(
                                    "↻ Reschedule Meeting",
                                    key=f"reschedule_meeting_{campaign_id}",
                                    use_container_width=True,
                                ):
                                    st.session_state[
                                        f"meeting_form_open_{campaign_id}"
                                    ] = True

                                    st.rerun()

                    # ====================================================
                    # CONFIRMATION NOT YET SENT
                    # ====================================================

                    else:

                        st.markdown(
                            """
                            <div style="
                                margin-top: 14px;
                                margin-bottom: 8px;
                                font-size: 13px;
                                font-weight: 700;
                            ">
                                Next Action
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if st.button(
                            "✉️ Send Confirmation",
                            key=f"scheduled_send_confirmation_{campaign_id}",
                            use_container_width=True,
                        ):
                            st.session_state[
                                f"confirmation_form_open_{campaign_id}"
                            ] = True

                            st.rerun()

                    # ====================================================
                    # SEND CONFIRMATION FORM
                    # ====================================================
                    cancel_confirmation = False
                    send_confirmation = False
                    
                    if st.session_state.get(
                        f"confirmation_form_open_{campaign_id}",
                        False,
                    ):

                        st.markdown(
                            "#### ✉️ Meeting Confirmation"
                        )

                        with st.form(
                            key=f"confirmation_form_{campaign_id}"
                        ):

                            recipient_email = st.text_input(
                                "Recipient Email",
                                placeholder="placement@college.edu",
                            )

                            confirmation_subject = st.text_input(
                                "Subject",
                                value="Meeting Confirmation – AI Training & Workshop",
                            )

                            confirmation_message = st.text_area(
                                "Message",
                                value=(
                                    "Dear Sir/Madam,\n\n"
                                    "Thank you for your response. "
                                    "We are pleased to confirm the meeting "
                                    "to discuss the AI training and workshop opportunities.\n\n"
                                    f"Meeting Date: {meeting_datetime.strftime('%d %b %Y')}\n"
                                    f"Meeting Time: {meeting_datetime.strftime('%I:%M %p')}\n"
                                    f"Duration: {meeting_details['duration_minutes']} minutes\n"
                                    f"Mode: {meeting_details['mode'].title()}\n"
                                    + (
                                        f"Meeting Link: {meeting_details['meeting_link']}\n"
                                        if meeting_details.get("mode", "").lower() == "online"
                                        and meeting_details.get("meeting_link")
                                        else ""
                                    )
                                    + "\n"
                                    "We look forward to the discussion.\n\n"
                                    "Best regards,\n"
                                    "AAMP Team"
                                ),
                                height=220,
                            )

                            confirmation_col1, confirmation_col2 = st.columns(2)

                            with confirmation_col1:

                                cancel_confirmation = st.form_submit_button(
                                    "Cancel",
                                    use_container_width=True,
                                )

                            with confirmation_col2:

                                send_confirmation = st.form_submit_button(
                                    "📤 Send Confirmation",
                                    use_container_width=True,
                                )

                    # ------------------------------------------------
                    # Cancel
                    # ------------------------------------------------

                    if cancel_confirmation:

                        st.session_state[
                            f"confirmation_form_open_{campaign_id}"
                        ] = False

                        st.rerun()

                    # ------------------------------------------------
                    # Send
                    # ------------------------------------------------

                    if send_confirmation:

                        # ====================================================
                        # VALIDATION
                        # ====================================================

                        if not recipient_email.strip():

                            st.error("Recipient email is required.")

                        elif not confirmation_subject.strip():

                            st.error("Subject is required.")

                        elif not confirmation_message.strip():

                            st.error("Message is required.")

                        else:

                            # ====================================================
                            # SEND THROUGH FASTAPI
                            # ====================================================

                            try:

                                payload = {
                                    "recipient_email": recipient_email.strip(),
                                    "subject": confirmation_subject.strip(),
                                    "message": confirmation_message.strip(),
                                }

                                response = requests.post(
                                    f"{BASE_URL}/campaigns/{campaign_id}/send-confirmation",
                                    json=payload,
                                    timeout=30,
                                )

                                # --------------------------------------------
                                # Successful email
                                # --------------------------------------------

                                if response.status_code == 200:

                                    result = response.json()

                                    st.session_state[
                                        "selected_campaign_action"
                                    ] = "send_confirmation"

                                    st.session_state[
                                        f"confirmation_sent_{campaign_id}"
                                    ] = True

                                    st.session_state[
                                        f"confirmation_form_open_{campaign_id}"
                                    ] = False

                                    st.success(
                                        "Meeting confirmation sent successfully."
                                    )

                                    st.rerun()

                                # --------------------------------------------
                                # FastAPI validation/business error
                                # --------------------------------------------

                                else:

                                    try:
                                        error_detail = response.json().get(
                                            "detail",
                                            "Failed to send meeting confirmation."
                                        )
                                    except Exception:
                                        error_detail = (
                                            "Failed to send meeting confirmation."
                                        )

                                    st.error(
                                        f"Unable to send confirmation: {error_detail}"
                                    )

                            except requests.exceptions.RequestException as exc:

                                st.error(
                                    f"Could not connect to the backend: {exc}"
                                )

            # ============================================================
            # MISSED / CANCELLED MEETING
            # ============================================================

            if (
                meeting_status in ["MISSED", "CANCELLED"]
                and not meeting_form_open
            ):

                if meeting_status == "MISSED":
                    st.info(
                        "The scheduled meeting time has passed "
                        "without the meeting being completed."
                    )

                elif meeting_status == "CANCELLED":
                    st.info(
                        "The scheduled meeting was cancelled."
                    )

                action_col1, action_col2 = st.columns(2)

                # --------------------------------------------------------
                # RESCHEDULE
                # --------------------------------------------------------
                with action_col1:

                    if st.button(
                        "↻ Reschedule Meeting",
                        key=f"reschedule_missed_cancelled_{campaign_id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"meeting_form_open_{campaign_id}"
                        ] = True

                        st.rerun()

                # --------------------------------------------------------
                # DELETE
                # --------------------------------------------------------
                with action_col2:

                    if st.button(
                        "🗑 Delete Meeting",
                        key=f"delete_missed_cancelled_{campaign_id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"delete_meeting_confirm_{campaign_id}"
                        ] = True

                        st.rerun()

            # ============================================================
            # DELETE MEETING CONFIRMATION
            # ============================================================

            if st.session_state.get(
                f"delete_meeting_confirm_{campaign_id}",
                False,
            ):

                st.warning(
                    "Are you sure you want to delete this meeting?"
                )

                delete_col1, delete_col2 = st.columns(2)

                with delete_col1:

                    if st.button(
                        "Keep Meeting",
                        key=f"keep_deleted_meeting_{campaign_id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"delete_meeting_confirm_{campaign_id}"
                        ] = False

                        st.rerun()

                with delete_col2:

                    if st.button(
                        "🗑 Yes, Delete",
                        key=f"confirm_delete_meeting_{campaign_id}",
                        use_container_width=True,
                    ):
                        try:

                            response = requests.delete(
                                f"{BASE_URL}/campaigns/{campaign_id}/meetings/"
                                f"{meeting_details['id']}",
                                timeout=30,
                            )

                            if response.status_code == 200:

                                st.session_state[
                                    f"delete_meeting_confirm_{campaign_id}"
                                ] = False

                                st.success(
                                    "Meeting deleted successfully."
                                )

                                st.rerun()

                            else:

                                try:
                                    error_detail = response.json().get(
                                        "detail",
                                        "Failed to delete meeting.",
                                    )
                                except Exception:
                                    error_detail = (
                                        "Failed to delete meeting."
                                    )

                                st.error(
                                    f"Unable to delete meeting: {error_detail}"
                                )

                        except requests.exceptions.RequestException as exc:

                            st.error(
                                f"Could not connect to the backend: {exc}"
                            )


            # ====================================================
            # SCHEDULE MEETING FORM
            # ====================================================

            elif meeting_form_open:

                st.markdown(
                    """
                    <div style="
                        margin-top: 16px;
                        margin-bottom: 10px;
                        font-size: 15px;
                        font-weight: 700;
                    ">
                        📅 Schedule Meeting
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form(
                    key=f"meeting_form_{campaign_id}"
                ):

                    # --------------------------------------------
                    # Meeting Date
                    # --------------------------------------------

                    meeting_date = st.date_input(
                        "Meeting Date",
                        key=f"meeting_date_{campaign_id}",
                    )

                    # --------------------------------------------
                    # Meeting Time
                    # --------------------------------------------

                    meeting_time = st.time_input(
                        "Meeting Time",
                        key=f"meeting_time_{campaign_id}",
                    )

                    # --------------------------------------------
                    # Duration
                    # --------------------------------------------

                    duration = st.number_input(
                        "Duration (minutes)",
                        min_value=5,
                        max_value=240,
                        value=30,
                        step=5,
                        key=f"meeting_duration_{campaign_id}",
                    )

                    # --------------------------------------------
                    # Meeting Mode
                    # --------------------------------------------

                    meeting_mode = st.selectbox(
                        "Mode",
                        ["Online", "In-person"],
                        key=f"meeting_mode_{campaign_id}",
                    )

                    # --------------------------------------------
                    # Meeting Link
                    # --------------------------------------------

                    meeting_link = ""

                    if meeting_mode == "Online":

                        meeting_link = st.text_input(
                            "Meeting Link",
                            placeholder="https://meet.google.com/...",
                            key=f"meeting_link_{campaign_id}",
                        )

                    # --------------------------------------------
                    # Form buttons
                    # --------------------------------------------

                    form_col1, form_col2 = st.columns(2)

                    with form_col1:

                        cancel = st.form_submit_button(
                            "Cancel",
                            use_container_width=True,
                        )

                    with form_col2:

                        schedule = st.form_submit_button(
                            "📅 Schedule Meeting",
                            use_container_width=True,
                        )

                # ====================================================
                # CANCEL
                # ====================================================

                if cancel:

                    st.session_state[
                        f"meeting_form_open_{campaign_id}"
                    ] = False

                    st.rerun()

                # ====================================================
                # SCHEDULE
                # ====================================================

                if schedule:

                    # --------------------------------------------
                    # Online meeting requires a link
                    # --------------------------------------------

                    if meeting_mode == "Online" and not meeting_link.strip():

                        st.error(
                            "Meeting link is required for an online meeting."
                        )

                    else:

                        # --------------------------------------------
                        # Combine date + time
                        # --------------------------------------------

                        meeting_datetime = datetime.combine(
                            meeting_date,
                            meeting_time,
                        ).replace(tzinfo=ZoneInfo("Asia/Kolkata"))

                        # --------------------------------------------
                        # Schedule through FastAPI
                        # --------------------------------------------

                        try:

                            payload = {
                                "meeting_date": meeting_datetime.isoformat(),
                                "duration_minutes": int(duration),
                                "mode": meeting_mode.lower(),
                                "meeting_link": (
                                    meeting_link.strip()
                                    if meeting_mode == "Online"
                                    else None
                                ),
                            }

                            response = requests.post(
                                f"{BASE_URL}/campaigns/{campaign_id}/meetings",
                                json=payload,
                                timeout=30,
                            )

                            # ----------------------------------------
                            # Successfully scheduled
                            # ----------------------------------------

                            if response.status_code == 200:

                                st.session_state[
                                    f"meeting_form_open_{campaign_id}"
                                ] = False

                                st.session_state[
                                    "selected_campaign_action"
                                ] = "meeting_scheduled"

                                st.success(
                                    "Meeting scheduled successfully."
                                )

                                st.rerun()

                            # ----------------------------------------
                            # Backend validation/business error
                            # ----------------------------------------

                            else:

                                try:
                                    error_detail = response.json().get(
                                        "detail",
                                        "Failed to schedule meeting.",
                                    )
                                except Exception:
                                    error_detail = (
                                        "Failed to schedule meeting."
                                    )

                                st.error(
                                    f"Unable to schedule meeting: {error_detail}"
                                )

                        except requests.exceptions.RequestException as exc:

                            st.error(
                                f"Could not connect to the backend: {exc}"
                            )

            # ====================================================
            # NO MEETING SCHEDULED
            # ====================================================

            elif not meeting_details:

                if st.button(
                    "📅 Schedule Meeting",
                    key=f"schedule_meeting_{campaign_id}",
                    use_container_width=True,
                ):
                    st.session_state[
                        f"meeting_form_open_{campaign_id}"
                    ] = True

                    st.rerun()


        # ====================================================
        # REQUEST CALL
        # ====================================================

        elif category == "REQUEST_CALL":

            st.info(
                "The college has requested a call."
            )

            # -----------------------------------------------
            # Get current call from backend
            # -----------------------------------------------

            try:
                response = requests.get(
                    f"{BASE_URL}/campaigns/{campaign_id}/calls/current",
                    timeout=10,
                )

                response.raise_for_status()

                response_data = response.json()

                call_data = response_data.get("call")

                pending_request_call = response_data.get(
                    "pending_request_call",
                    False,
                )

            except requests.RequestException as exc:

                st.error(
                    f"Unable to load call details: {exc}"
                )

                call_data = None
                pending_request_call = False

            # -----------------------------------------------
            # New REQUEST_CALL / No call scheduled
            # -----------------------------------------------

            if pending_request_call or call_data is None:

                if st.button(
                    "📞 Schedule Call",
                    key=f"schedule_call_{campaign_id}",
                    use_container_width=True,
                ):
                    st.session_state[
                        f"call_form_open_{campaign_id}"
                    ] = True

                    st.rerun()

                # -------------------------------------------
                # Call scheduling form
                # -------------------------------------------

                if st.session_state.get(
                    f"call_form_open_{campaign_id}",
                    False,
                ):

                    st.markdown(
                        "### 📞 Schedule Call"
                    )

                    # -----------------------------------------------
                    # College Contact Details
                    # -----------------------------------------------

                    contact_role = (
                        college.get("contact_role", {}).get("value")
                        if isinstance(college.get("contact_role"), dict)
                        else None
                    )

                    official_phone = (
                        college.get("official_phone", {}).get("value")
                        if isinstance(college.get("official_phone"), dict)
                        else None
                    )

                    official_email = (
                        college.get("official_email", {}).get("value")
                        if isinstance(college.get("official_email"), dict)
                        else None
                    )

                    st.markdown(
                        """
                    <div style="
                        border: 1px solid rgba(128,128,128,0.25);
                        border-radius: 10px;
                        padding: 14px 16px;
                        margin: 16px 0;
                    ">

                    <div style="
                        font-size: 15px;
                        font-weight: 600;
                        margin-bottom: 10px;
                    ">
                    👤 College Contact
                    </div>

                    <div style="line-height: 1.8;">
                    <b>Role:</b> CONTACT_ROLE<br>
                    <b>Phone:</b> OFFICIAL_PHONE<br>
                    <b>Email:</b> OFFICIAL_EMAIL
                    </div>

                    </div>
                    """.replace(
                            "CONTACT_ROLE",
                            contact_role or "Not available",
                        ).replace(
                            "OFFICIAL_PHONE",
                            official_phone or "Not available",
                        ).replace(
                            "OFFICIAL_EMAIL",
                            official_email or "Not available",
                        ),
                        unsafe_allow_html=True,
                    )

                    # -----------------------------------------------
                    # Call Details
                    # -----------------------------------------------

                    st.markdown("#### 📅 Call Details")

                    call_date = st.date_input(
                        "Date",
                        key=f"call_date_{campaign_id}",
                    )

                    call_time = st.time_input(
                        "Time",
                        key=f"call_time_{campaign_id}",
                    )

                    duration = st.number_input(
                        "Duration (minutes)",
                        min_value=5,
                        max_value=180,
                        value=30,
                        step=5,
                        key=f"call_duration_{campaign_id}",
                    )

                    notes = st.text_area(
                        "Notes",
                        placeholder="Optional notes about the call",
                        key=f"call_notes_{campaign_id}",
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "📞 Confirm Schedule",
                            key=f"confirm_schedule_call_{campaign_id}",
                            use_container_width=True,
                        ):

                            call_datetime = datetime.combine(
                                call_date,
                                call_time,
                            ).replace(
                                tzinfo=ZoneInfo("Asia/Kolkata")
                            )

                            payload = {
                                "call_date": call_datetime.isoformat(),
                                "duration_minutes": int(duration),
                                "notes": notes.strip() or None,
                            }

                            try:
                                response = requests.post(
                                    f"{BASE_URL}/campaigns/{campaign_id}/calls",
                                    json=payload,
                                    timeout=10,
                                )

                                response.raise_for_status()

                                st.session_state[
                                    f"call_form_open_{campaign_id}"
                                ] = False

                                st.success(
                                    "✓ Call scheduled successfully."
                                )

                                st.rerun()

                            except requests.RequestException as exc:

                                try:
                                    detail = response.json().get(
                                        "detail",
                                        str(exc),
                                    )
                                except Exception:
                                    detail = str(exc)

                                st.error(
                                    f"Unable to schedule call: {detail}"
                                )

                    with col2:
                        if st.button(
                            "Cancel",
                            key=f"cancel_schedule_call_{campaign_id}",
                            use_container_width=True,
                        ):
                            st.session_state[
                                f"call_form_open_{campaign_id}"
                            ] = False

                            st.rerun()

            # -----------------------------------------------
            # Call already scheduled / existing call
            # -----------------------------------------------

            else:

                call_status = str(
                    call_data.get("status", "")
                ).upper()

                if call_status == "SCHEDULED":

                    call_datetime = datetime.fromisoformat(
                        call_data["call_date"]
                    )

                    st.success(
                        "✓ Call Scheduled"
                    )

                    # -----------------------------------------------
                    # College Contact Details
                    # -----------------------------------------------

                    contact_role = (
                        college.get("contact_role", {}).get("value")
                        if isinstance(college.get("contact_role"), dict)
                        else None
                    )

                    official_phone = (
                        college.get("official_phone", {}).get("value")
                        if isinstance(college.get("official_phone"), dict)
                        else None
                    )

                    official_email = (
                        college.get("official_email", {}).get("value")
                        if isinstance(college.get("official_email"), dict)
                        else None
                    )

                    st.markdown(
                        """
                <div style="
                    border: 1px solid rgba(128,128,128,0.25);
                    border-radius: 10px;
                    padding: 14px 16px;
                    margin: 16px 0;
                ">

                <div style="
                    font-size: 15px;
                    font-weight: 600;
                    margin-bottom: 10px;
                ">
                👤 College Contact
                </div>

                <div style="line-height: 1.8;">
                <b>Role:</b> CONTACT_ROLE<br>
                <b>Phone:</b> OFFICIAL_PHONE<br>
                <b>Email:</b> OFFICIAL_EMAIL
                </div>

                </div>
                """.replace(
                            "CONTACT_ROLE",
                            contact_role or "Not available",
                        ).replace(
                            "OFFICIAL_PHONE",
                            official_phone or "Not available",
                        ).replace(
                            "OFFICIAL_EMAIL",
                            official_email or "Not available",
                        ),
                        unsafe_allow_html=True,
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(
                            f"📅 **{call_datetime.strftime('%d %b %Y')}**"
                        )

                    with col2:
                        st.write(
                            f"🕐 **{call_datetime.strftime('%I:%M %p')}**"
                        )

                    with col3:
                        st.write(
                            f"⏱ **{call_data.get('duration_minutes', 30)} min**"
                        )

                    if call_data.get("notes"):
                        st.caption(
                            f"Notes: {call_data['notes']}"
                        )

                    st.info(
                        "The call is scheduled. "
                        "Send a confirmation to the college."
                    )

                    # -------------------------------------------
                    # Check whether confirmation was already sent
                    # -------------------------------------------

                    try:
                        confirmation_response = requests.get(
                            f"{BASE_URL}/campaigns/"
                            f"{campaign_id}/calls/"
                            f"{call_data['id']}/confirmation-status",
                            timeout=10,
                        )

                        confirmation_response.raise_for_status()

                        confirmation_sent = (
                            confirmation_response.json().get(
                                "confirmation_sent",
                                False,
                            )
                        )

                    except requests.RequestException as exc:
                        confirmation_sent = False
                        st.warning(
                            f"Unable to check confirmation status: {exc}"
                        )

                    # -------------------------------------------
                    # Confirmation action
                    # -------------------------------------------

                    if confirmation_sent:

                        st.success("✓ Confirmation Sent")

                    else:

                        if st.button(
                            "✉️ Send Confirmation",
                            key=f"send_confirmation_call_{campaign_id}",
                            use_container_width=True,
                        ):

                            try:
                                response = requests.post(
                                    f"{BASE_URL}/campaigns/"
                                    f"{campaign_id}/calls/"
                                    f"{call_data['id']}/confirmation",
                                    timeout=30,
                                )

                                response.raise_for_status()

                                st.success(
                                    "✓ Call confirmation sent successfully."
                                )

                                st.rerun()

                            except requests.RequestException as exc:

                                try:
                                    detail = response.json().get(
                                        "detail",
                                        str(exc),
                                    )
                                except Exception:
                                    detail = str(exc)

                                st.error(
                                    f"Unable to send confirmation: {detail}"
                                )

                    if st.button(
                        "❌ Cancel Call",
                        key=f"cancel_call_{campaign_id}_{call_data['id']}",
                        use_container_width=True,
                    ):
                        try:
                            response = requests.post(
                                f"{BASE_URL}/campaigns/"
                                f"{campaign_id}/calls/{call_data['id']}/cancel",
                                timeout=10,
                            )
                            response.raise_for_status()

                            st.success("✓ Call cancelled successfully.")
                            st.rerun()

                        except requests.RequestException as exc:
                            try:
                                error_detail = response.json().get("detail", str(exc))
                            except Exception:
                                error_detail = str(exc)

                            st.error(f"Unable to cancel call: {error_detail}")


                elif call_status == "CANCELLED":

                    st.warning(
                        "The previously scheduled call was cancelled."
                    )

                    if st.button(
                        "📞 Schedule New Call",
                        key=f"schedule_new_call_{campaign_id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"call_form_open_{campaign_id}"
                        ] = True

                    # -----------------------------------------------
                    # Show scheduling form
                    # -----------------------------------------------

                    if st.session_state.get(
                        f"call_form_open_{campaign_id}",
                        False,
                    ):

                        st.markdown("### 📞 Schedule New Call")

                        # -----------------------------------------------
                        # College Contact Details
                        # -----------------------------------------------

                        contact_role = (
                            college.get("contact_role", {}).get("value")
                            if isinstance(college.get("contact_role"), dict)
                            else None
                        )

                        official_phone = (
                            college.get("official_phone", {}).get("value")
                            if isinstance(college.get("official_phone"), dict)
                            else None
                        )

                        official_email = (
                            college.get("official_email", {}).get("value")
                            if isinstance(college.get("official_email"), dict)
                            else None
                        )

                        st.markdown(
                            """
                        <div style="
                            border: 1px solid rgba(128,128,128,0.25);
                            border-radius: 10px;
                            padding: 14px 16px;
                            margin: 16px 0;
                        ">

                        <div style="font-size: 15px; font-weight: 600; margin-bottom: 10px;">
                        👤 College Contact
                        </div>

                        <div style="line-height: 1.8;">
                        <b>Role:</b> CONTACT_ROLE<br>
                        <b>Phone:</b> OFFICIAL_PHONE<br>
                        <b>Email:</b> OFFICIAL_EMAIL
                        </div>

                        </div>
                        """.replace(
                                "CONTACT_ROLE",
                                contact_role or "Not available",
                            ).replace(
                                "OFFICIAL_PHONE",
                                official_phone or "Not available",
                            ).replace(
                                "OFFICIAL_EMAIL",
                                official_email or "Not available",
                            ),
                            unsafe_allow_html=True,
                        )

                        # -----------------------------------------------
                        # Call Details
                        # -----------------------------------------------

                        st.markdown("#### 📅 Call Details")

                        call_date = st.date_input(
                            "Date",
                            key=f"new_call_date_{campaign_id}",
                        )

                        call_time = st.time_input(
                            "Time",
                            key=f"new_call_time_{campaign_id}",
                        )

                        duration = st.number_input(
                            "Duration (minutes)",
                            min_value=5,
                            max_value=180,
                            value=30,
                            step=5,
                            key=f"new_call_duration_{campaign_id}",
                        )

                        notes = st.text_area(
                            "Notes",
                            placeholder="Optional notes about the call",
                            key=f"new_call_notes_{campaign_id}",
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            if st.button(
                                "📞 Confirm Schedule",
                                key=f"confirm_new_call_{campaign_id}",
                                use_container_width=True,
                            ):
                                call_datetime = datetime.combine(
                                    call_date,
                                    call_time,
                                ).replace(
                                    tzinfo=ZoneInfo("Asia/Kolkata")
                                )

                                payload = {
                                    "previous_call_id": call_data["id"],
                                    "call_date": call_datetime.isoformat(),
                                    "duration_minutes": int(duration),
                                    "notes": notes.strip() or None,
                                }

                                try:
                                    response = requests.post(
                                        f"{BASE_URL}/campaigns/"
                                        f"{campaign_id}/calls/schedule-new",
                                        json=payload,
                                        timeout=10,
                                    )

                                    response.raise_for_status()

                                    st.session_state[
                                        f"call_form_open_{campaign_id}"
                                    ] = False

                                    st.success(
                                        "✓ New call scheduled successfully."
                                    )

                                    st.rerun()

                                except requests.RequestException as exc:

                                    try:
                                        detail = response.json().get(
                                            "detail",
                                            str(exc),
                                        )
                                    except Exception:
                                        detail = str(exc)

                                    st.error(
                                        f"Unable to schedule new call: {detail}"
                                    )

                        with col2:

                            if st.button(
                                "Cancel",
                                key=f"cancel_new_call_{campaign_id}",
                                use_container_width=True,
                            ):

                                st.session_state[
                                    f"call_form_open_{campaign_id}"
                                ] = False

                                st.rerun()

                   # MISSED → Schedule New Call
                elif call_status == "MISSED":
                    st.warning("The scheduled call was missed.")

                    if st.button(
                        "📞 Schedule New Call",
                        key=f"reschedule_missed_call_{campaign_id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"call_form_open_{campaign_id}"] = True
                        st.rerun()

                    if st.session_state.get(
                        f"call_form_open_{campaign_id}",
                        False,
                    ):
                        st.markdown("### 📞 Schedule New Call")

                        # ─────────────────────────────────────
                        # College Contact
                        # ─────────────────────────────────────

                        contact_role = (
                            college.get("contact_role", {}).get("value")
                            if isinstance(college.get("contact_role"), dict)
                            else None
                        )

                        official_phone = (
                            college.get("official_phone", {}).get("value")
                            if isinstance(college.get("official_phone"), dict)
                            else None
                        )

                        official_email = (
                            college.get("official_email", {}).get("value")
                            if isinstance(college.get("official_email"), dict)
                            else None
                        )

                        st.markdown(
                            """
                <div style="
                    border: 1px solid rgba(128,128,128,0.25);
                    border-radius: 10px;
                    padding: 14px 16px;
                    margin: 16px 0;
                ">

                <div style="
                    font-size: 15px;
                    font-weight: 600;
                    margin-bottom: 10px;
                ">
                👤 College Contact
                </div>

                <div style="line-height: 1.8;">
                <b>Role:</b> CONTACT_ROLE<br>
                <b>Phone:</b> OFFICIAL_PHONE<br>
                <b>Email:</b> OFFICIAL_EMAIL
                </div>

                </div>
                """.replace(
                                "CONTACT_ROLE",
                                contact_role or "Not available",
                            ).replace(
                                "OFFICIAL_PHONE",
                                official_phone or "Not available",
                            ).replace(
                                "OFFICIAL_EMAIL",
                                official_email or "Not available",
                            ),
                            unsafe_allow_html=True,
                        )

                        # ─────────────────────────────────────
                        # Call Details
                        # ─────────────────────────────────────

                        st.markdown("#### 📅 Call Details")

                        call_date = st.date_input(
                            "Date",
                            key=f"missed_call_date_{campaign_id}",
                        )

                        call_time = st.time_input(
                            "Time",
                            key=f"missed_call_time_{campaign_id}",
                        )

                        duration = st.number_input(
                            "Duration (minutes)",
                            min_value=5,
                            max_value=180,
                            value=30,
                            step=5,
                            key=f"missed_call_duration_{campaign_id}",
                        )

                        notes = st.text_area(
                            "Notes",
                            placeholder="Optional notes about the new call",
                            key=f"missed_call_notes_{campaign_id}",
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(
                                "📞 Confirm Schedule",
                                key=f"confirm_missed_call_{campaign_id}",
                                use_container_width=True,
                            ):
                                call_datetime = datetime.combine(
                                    call_date,
                                    call_time,
                                ).replace(
                                    tzinfo=ZoneInfo("Asia/Kolkata")
                                )

                                payload = {
                                    "previous_call_id": call_data["id"],
                                    "call_date": call_datetime.isoformat(),
                                    "duration_minutes": int(duration),
                                    "notes": notes.strip() or None,
                                }

                                try:
                                    response = requests.post(
                                        f"{BASE_URL}/campaigns/"
                                        f"{campaign_id}/calls/schedule-new",
                                        json=payload,
                                        timeout=10,
                                    )

                                    response.raise_for_status()

                                    st.session_state[
                                        f"call_form_open_{campaign_id}"
                                    ] = False

                                    st.success(
                                        "✓ New call scheduled successfully."
                                    )

                                    st.rerun()

                                except requests.RequestException as exc:
                                    try:
                                        detail = response.json().get(
                                            "detail",
                                            str(exc),
                                        )
                                    except Exception:
                                        detail = str(exc)

                                    st.error(
                                        f"Unable to schedule new call: {detail}"
                                    )

                        with col2:
                            if st.button(
                                "Cancel",
                                key=f"cancel_missed_call_{campaign_id}",
                                use_container_width=True,
                            ):
                                st.session_state[
                                    f"call_form_open_{campaign_id}"
                                ] = False

                                st.rerun()

        # ====================================================
        # MORE INFORMATION / NEEDS INFORMATION
        # ====================================================

        elif category == "NEEDS_INFORMATION":

            st.info(
                "The college has requested additional information. "
                "Send the standard information package for review."
            )

            # ------------------------------------------------
            # Check whether information package was already sent
            # ------------------------------------------------

            messages = CampaignService.get_messages(campaign_id)

            information_sent = False

            for message in messages:
                if (
                    str(message.get("direction", "")).lower() == "outbound"
                    and "standard information package" in
                    str(message.get("message", "")).lower()
                ):
                    information_sent = True
                    break

            # ------------------------------------------------
            # Information already sent
            # ------------------------------------------------

            if information_sent:

                st.success(
                    "Information package sent successfully."
                )

                st.markdown(
                    """
                <div style="
                    font-size: 14px;
                    line-height: 1.7;
                ">
                    ✓ Course / Training Information<br>
                    ✓ Brochure<br>
                    ✓ 1-Day Workshop Information<br>
                    ✓ 2-Day Workshop Information<br>
                    ✓ 3-Day Workshop Information
                </div>

                <div style="
                    margin-top: 10px;
                    font-size: 13px;
                    opacity: 0.75;
                ">
                    Waiting for the college's next response.
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # ------------------------------------------------
            # Information package not sent yet
            # ------------------------------------------------

            else:

                st.markdown(
                    """
                <div style="
                    font-size: 14px;
                    line-height: 1.7;
                ">
                    The following information will be sent together:
                    <br><br>
                    • Course / Training Information<br>
                    • Brochure<br>
                    • 1-Day Workshop Information<br>
                    • 2-Day Workshop Information<br>
                    • 3-Day Workshop Information
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # --------------------------------------------
                # Send Information
                # --------------------------------------------

                if st.button(
                    "✉️ Send Information",
                    key=f"send_information_{campaign_id}",
                    use_container_width=True,
                ):

                    try:

                        response = requests.post(
                            f"{BASE_URL}/campaigns/"
                            f"{campaign_id}/send-information",
                            timeout=30,
                        )

                        if response.status_code == 200:

                            st.session_state[
                                "selected_campaign_action"
                            ] = "send_information"

                            st.success(
                                "Information package sent successfully."
                            )

                            st.rerun()

                        else:

                            try:
                                error_detail = response.json().get(
                                    "detail",
                                    "Failed to send information package.",
                                )
                            except Exception:
                                error_detail = (
                                    "Failed to send information package."
                                )

                            st.error(
                                f"Unable to send information: "
                                f"{error_detail}"
                            )

                    except requests.exceptions.RequestException as exc:

                        st.error(
                            f"Could not connect to the backend: {exc}"
                        )


        # ====================================================
        # INTERESTED
        # ====================================================

        elif category == "INTERESTED":
            st.success("The college has expressed interest.")

            # Check whether information package was already sent
            information_sent = ...

            if not information_sent:

                if st.button(
                    "✉️ Send Information",
                    key=f"send_information_interest_{campaign_id}",
                    use_container_width=True,
                ):
                    try:
                        response = requests.post(
                            f"{BASE_URL}/campaigns/{campaign_id}/send-information",
                            timeout=120,
                        )
                        response.raise_for_status()

                        st.success("✓ Information package sent successfully.")
                        st.rerun()

                    except requests.RequestException as exc:
                        try:
                            error_detail = response.json().get("detail", str(exc))
                        except Exception:
                            error_detail = str(exc)

                        st.error(
                            f"Unable to send information: {error_detail}"
                        )

            else:

                st.success("✓ Information package sent successfully.")

                st.markdown("""
                ✓ Course / Training Information  
                ✓ Brochure   
                ✓ 1-Day Workshop Information  
                ✓ 2-Day Workshop Information  
                ✓ 3-Day Workshop Information  
                """)

                st.info("Waiting for the college's next response.")


        # ====================================================
        # ASK LATER
        # ====================================================

        elif category == "ASK_LATER":

            campaign_status = str(campaign.get("status", "")).lower()
            follow_up_count = int(campaign.get("follow_up_count") or 0)
            next_follow_up_at = campaign.get("next_follow_up_at")
            sent_at = campaign.get("sent_at")
            completed_at = campaign.get("completed_at")

            # ------------------------------------------------
            # CAMPAIGN COMPLETED
            # ------------------------------------------------

            if campaign_status == "completed":

                st.success("✓ Campaign Completed")

                if sent_at:
                    try:
                        sent_datetime = datetime.fromisoformat(str(sent_at))
                        sent_display = sent_datetime.strftime("%d %b %Y · %I:%M %p")

                        st.markdown(
                            textwrap.dedent(f"""
                                <div style="margin-top: 12px; padding: 14px 16px; border-radius: 8px; background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.30);">
                                    <div style="font-size: 14px; font-weight: 700;">📨 Automatic Follow-up Sent</div>
                                    <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">Sent: <b>{sent_display}</b></div>
                                </div>
                            """),
                            unsafe_allow_html=True,
                        )
                    except (ValueError, TypeError):
                        pass

                st.info(
                    "No response was received within 3 days after the automatic follow-up. "
                    "The campaign has been completed."
                )

                if completed_at:
                    try:
                        completed_datetime = datetime.fromisoformat(str(completed_at))
                        completed_display = completed_datetime.strftime("%d %b %Y · %I:%M %p")
                        st.caption(f"Completed: {completed_display}")
                    except (ValueError, TypeError):
                        pass

            # ------------------------------------------------
            # ONE AUTOMATIC FOLLOW-UP ALREADY SENT
            # ------------------------------------------------

            elif campaign_status == "sent" and follow_up_count >= 1:

                st.success("📨 Automatic Follow-up Sent")

                if sent_at:
                    try:
                        sent_datetime = datetime.fromisoformat(str(sent_at))
                        sent_display = sent_datetime.strftime("%d %b %Y · %I:%M %p")

                        st.markdown(
                            textwrap.dedent(f"""
                                <div style="margin-top: 10px; padding: 14px 16px; border-radius: 8px; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.30);">
                                    <div style="font-size: 14px; font-weight: 700;">📨 Follow-up sent successfully</div>
                                    <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">Sent: <b>{sent_display}</b></div>
                                </div>
                            """),
                            unsafe_allow_html=True,
                        )
                    except (ValueError, TypeError):
                        pass

                # --------------------------------------------
                # 3-DAY RESPONSE WINDOW
                # --------------------------------------------

                if next_follow_up_at:
                    try:
                        deadline_datetime = datetime.fromisoformat(str(next_follow_up_at))
                        deadline_display = deadline_datetime.strftime("%d %b %Y · %I:%M %p")

                        st.markdown(
                            textwrap.dedent(f"""
                                <div style="margin-top: 12px; padding: 14px 16px; border-radius: 8px; background: rgba(234,179,8,0.08); border: 1px solid rgba(234,179,8,0.30);">
                                    <div style="font-size: 14px; font-weight: 700;">⏳ Waiting for Response</div>
                                    <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">Response deadline: <b>{deadline_display}</b></div>
                                    <div style="margin-top: 6px; font-size: 12px; color: #94a3b8;">If no response is received by this deadline, the campaign will be completed.</div>
                                </div>
                            """),
                            unsafe_allow_html=True,
                        )
                    except (ValueError, TypeError):
                        pass

            # ------------------------------------------------
            # WAITING FOR THE ORIGINAL ASK-LATER DATE
            # ------------------------------------------------

            else:

                st.warning("The college has asked to be contacted later.")

                if next_follow_up_at:
                    try:
                        scheduled_datetime = datetime.fromisoformat(str(next_follow_up_at))
                        scheduled_display = scheduled_datetime.strftime("%d %b %Y · %I:%M %p")

                        st.markdown(
                            textwrap.dedent(f"""
                                <div style="margin-top: 12px; padding: 14px 16px; border-radius: 8px; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.30);">
                                    <div style="font-size: 14px; font-weight: 700;">⏰ Automatic Follow-up Scheduled</div>
                                    <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">Scheduled for: <b>{scheduled_display}</b></div>
                                    <div style="margin-top: 6px; font-size: 12px; color: #94a3b8;">The system will automatically send one follow-up at the scheduled time.</div>
                                </div>
                            """),
                            unsafe_allow_html=True,
                        )
                    except (ValueError, TypeError):
                        pass

                else:
                    st.info(
                        "The college has asked to be contacted later. "
                        "An automatic follow-up will be scheduled."
                    )

        # ====================================================
        # NOT INTERESTED
        # ====================================================

        elif category == "NOT_INTERESTED":

            campaign_status = str(
                campaign.get("status", "")
            ).lower()

            completed_at = campaign.get("completed_at")

            if campaign_status == "completed":

                st.success("✓ Campaign Closed")

                st.info(
                    "The college is not interested in the current "
                    "opportunity. No further automatic follow-ups "
                    "will be sent."
                )

                if completed_at:

                    try:
                        completed_datetime = datetime.fromisoformat(
                            str(completed_at)
                        )

                        completed_display = completed_datetime.strftime(
                            "%d %b %Y · %I:%M %p"
                        )

                        st.caption(
                            f"Closed: {completed_display}"
                        )

                    except (ValueError, TypeError):
                        pass

            else:

                st.warning(
                    "The college has indicated that it is not "
                    "interested in the current opportunity."
                )

                st.info(
                    "This campaign will be closed automatically."
                )
        # ====================================================
        # OPT_OUT
        # ====================================================
        elif category == "OPT_OUT":
            st.markdown(
                """
        <div style="
            padding: 12px 14px;
            border-radius: 8px;
            background: rgba(239,68,68,0.08);
            border: 1px solid rgba(239,68,68,0.25);
            margin-bottom: 10px;
        ">
            <div style="
                color: #f87171;
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 5px;
            ">
                🛑 Outreach Stopped
            </div>
            <div style="
                color: #94a3b8;
                font-size: 13px;
                line-height: 1.5;
            ">
                The college has opted out of further communication.
                No further automated outreach will be sent.
            </div>
        </div>
        """,
                unsafe_allow_html=True,
            )

        # ====================================================
        # WRONG CONTACT
        # ====================================================

        elif category == "WRONG_CONTACT":

            # Check if contact is updated either via session state OR backend campaign state
            contact_updated = st.session_state.get(
                f"contact_updated_{campaign_id}",
                False,
            ) or campaign.get("contact_updated", False)

            if contact_updated:

                st.success("✓ Contact updated successfully.")

                st.info("The new contact has been saved successfully.")

                selected_contact = st.session_state.get(
                    f"selected_contact_{campaign_id}"
                ) or {
                    "role": college.get("contact_role", {}).get("value") if isinstance(college.get("contact_role"), dict) else college.get("contact_role"),
                    "email": college.get("official_email", {}).get("value") if isinstance(college.get("official_email"), dict) else college.get("official_email"),
                    "phone": college.get("official_phone", {}).get("value") if isinstance(college.get("official_phone"), dict) else college.get("official_phone"),
                }

                if selected_contact:

                    updated_role = selected_contact.get("role") or "Not available"
                    updated_email = selected_contact.get("email") or "Not available"
                    updated_phone = selected_contact.get("phone") or "Not available"

                    st.markdown("### 👤 Updated Contact")

                    st.markdown(
                        textwrap.dedent(f"""
                            <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 10px; padding: 14px 16px; margin: 12px 0;">
                                <div style="font-size: 15px; font-weight: 600; margin-bottom: 10px;">New Contact</div>
                                <div style="line-height: 1.8;"><b>Role:</b> {updated_role}</div>
                                <div style="line-height: 1.8;"><b>Phone:</b> {updated_phone}</div>
                                <div style="line-height: 1.8;"><b>Email:</b> {updated_email}</div>
                            </div>
                        """),
                        unsafe_allow_html=True,
                    )

                    st.info(
                        "The previous campaign remains as historical WRONG_CONTACT. "
                        "A new campaign can now be created for this contact."
                    )

                    if st.button(
                        "📧 Create New Campaign",
                        key=f"create_new_contact_campaign_{campaign_id}",
                        use_container_width=True,
                    ):

                        try:

                            response = requests.post(
                                f"{BASE_URL}/campaigns/{campaign_id}/create-new-contact-campaign",
                                timeout=30,
                            )

                            if response.status_code == 200:

                                data = response.json()

                                new_campaign_id = data.get(
                                    "new_campaign_id"
                                )

                                st.success(
                                    f"✓ New campaign created successfully "
                                    f"(Campaign #{new_campaign_id})."
                                )

                                st.info(
                                    "The new campaign is now in DRAFT status "
                                    "and requires human approval before outreach."
                                )

                                st.session_state[
                                    f"new_contact_campaign_{campaign_id}"
                                ] = new_campaign_id

                            else:

                                error_detail = response.json().get(
                                    "detail",
                                    "Failed to create new campaign.",
                                )

                                st.error(
                                    f"Unable to create campaign: {error_detail}"
                                )

                        except Exception as exc:

                            st.error(
                                f"Error creating campaign: {exc}"
                            )

            else:

                # ====================================================
                # ORIGINAL WRONG CONTACT FLOW
                # ====================================================

                st.warning(
                    "The current contact is not the appropriate person for this outreach."
                )

                st.info(
                    "The college has indicated that another person should be contacted. "
                    "Please review the current contact and update it before continuing."
                )

                if st.button(
                    "🔍 Review Contact",
                    key=f"review_contact_{campaign_id}",
                    use_container_width=True,
                ):
                    st.session_state[
                        f"review_contact_open_{campaign_id}"
                    ] = True

                if st.session_state.get(
                    f"review_contact_open_{campaign_id}",
                    False,
                ):

                    contact_role = (
                        college.get("contact_role", {}).get("value")
                        if isinstance(college.get("contact_role"), dict)
                        else college.get("contact_role")
                    )

                    official_phone = (
                        college.get("official_phone", {}).get("value")
                        if isinstance(college.get("official_phone"), dict)
                        else college.get("official_phone")
                    )

                    official_email = (
                        college.get("official_email", {}).get("value")
                        if isinstance(college.get("official_email"), dict)
                        else college.get("official_email")
                    )

                    st.markdown("### 👤 Current Contact")

                    role_str = contact_role or "Not available"
                    phone_str = official_phone or "Not available"
                    email_str = official_email or "Not available"

                    st.markdown(
                        textwrap.dedent(f"""
                            <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 10px; padding: 14px 16px; margin: 12px 0;">
                                <div style="font-size: 15px; font-weight: 600; margin-bottom: 10px;">Current Contact</div>
                                <div style="line-height: 1.8;">
                                    <b>Role:</b> {role_str}<br>
                                    <b>Phone:</b> {phone_str}<br>
                                    <b>Email:</b> {email_str}
                                </div>
                            </div>
                        """),
                        unsafe_allow_html=True,
                    )

                    st.info(
                        "The college requested that you contact the appropriate person instead."
                    )

                    if st.button(
                        "👤 Find / Update Contact",
                        key=f"find_update_contact_{campaign_id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"find_update_contact_open_{campaign_id}"
                        ] = True

                # -----------------------------------------------
                # Find New Contact
                # -----------------------------------------------

                if st.session_state.get(
                    f"find_update_contact_open_{campaign_id}",
                    False,
                ):

                    if st.button(
                        "🔎 Find New Contact",
                        key=f"find_new_contact_{campaign_id}",
                        use_container_width=True,
                    ):

                        try:

                            response = requests.post(
                                f"{BASE_URL}/campaigns/{campaign_id}/find-contact",
                                timeout=120,
                            )

                            response.raise_for_status()

                            result = response.json()

                            st.session_state[
                                f"contact_discovery_result_{campaign_id}"
                            ] = result

                        except requests.RequestException as exc:

                            try:
                                error_detail = response.json().get(
                                    "detail",
                                    str(exc),
                                )
                            except Exception:
                                error_detail = str(exc)

                            st.error(
                                f"Unable to find a new contact: {error_detail}"
                            )

                    # -----------------------------------------------
                    # Discovery Result
                    # -----------------------------------------------

                    contact_result = st.session_state.get(
                        f"contact_discovery_result_{campaign_id}"
                    )

                    if contact_result:

                        result = contact_result.get(
                            "result",
                            {},
                        )

                        requested_role = contact_result.get(
                            "requested_role"
                        )

                        discovered_contact = result.get(
                            "contact"
                        )

                        st.markdown("### 🔎 Contact Discovery")

                        if requested_role:

                            st.caption(
                                f"Requested role: {requested_role}"
                            )

                        if result.get("status") == "found" and discovered_contact:

                            st.success(
                                "✓ A new contact was found."
                            )

                            discovered_role = discovered_contact.get(
                                "role"
                            ) or "Not available"

                            discovered_email = discovered_contact.get(
                                "email"
                            ) or "Not available"

                            discovered_phone = discovered_contact.get(
                                "phone"
                            ) or "Not available"

                            discovered_source = discovered_contact.get(
                                "source"
                            )

                            st.markdown(
                                textwrap.dedent(f"""
                                    <div style="border: 1px solid rgba(128,128,128,0.25); border-radius: 10px; padding: 14px 16px; margin: 12px 0;">
                                        <div style="font-size: 15px; font-weight: 600; margin-bottom: 10px;">New Contact Found</div>
                                        <div style="line-height: 1.8;">
                                            <b>Role:</b> {discovered_role}<br>
                                            <b>Phone:</b> {discovered_phone}<br>
                                            <b>Email:</b> {discovered_email}
                                        </div>
                                    </div>
                                """),
                                unsafe_allow_html=True,
                            )

                            if discovered_source:

                                st.caption(
                                    f"Source: {discovered_source}"
                                )

                            if st.button(
                                "✓ Use This Contact",
                                key=f"use_discovered_contact_{campaign_id}",
                                use_container_width=True,
                            ):

                                if not discovered_email or discovered_email == "Not available":
                                    st.error(
                                        "This contact cannot be used because no email address was found."
                                    )

                                else:
                                    update_payload = {
                                        "role": discovered_role,
                                        "email": discovered_email,
                                        "phone": discovered_phone,
                                    }

                                    try:
                                        response = requests.post(
                                            f"{BASE_URL}/campaigns/{campaign_id}/update-contact",
                                            json=update_payload,
                                            timeout=30,
                                        )

                                        if response.status_code == 200:

                                            data = response.json()

                                            # Save updated state permanently in session_state
                                            st.session_state[
                                                f"selected_contact_{campaign_id}"
                                            ] = data.get("contact") or update_payload

                                            st.session_state[
                                                f"contact_updated_{campaign_id}"
                                            ] = True

                                            st.rerun()

                                        else:

                                            error_detail = response.json().get(
                                                "detail",
                                                "Failed to update contact.",
                                            )

                                            st.error(
                                                f"Unable to update contact: {error_detail}"
                                            )

                                    except Exception as exc:

                                        st.error(
                                            f"Error updating contact: {exc}"
                                        )
        # ====================================================
        # OUT OF OFFICE
        # ====================================================

        elif category == "OUT_OF_OFFICE":

            campaign_status = str(campaign.get("status", "")).lower()
            follow_up_count = int(campaign.get("follow_up_count") or 0)
            next_follow_up_at = campaign.get("next_follow_up_at")
            sent_at = campaign.get("sent_at")
            completed_at = campaign.get("completed_at")

            # ------------------------------------------------
            # CAMPAIGN COMPLETED
            # ------------------------------------------------

            if campaign_status == "completed":

                st.success("✓ Campaign Completed")

                st.info(
                    "No response was received after the automatic "
                    "OUT_OF_OFFICE follow-up. The campaign has been completed."
                )

                if completed_at:
                    try:
                        completed_datetime = datetime.fromisoformat(
                            str(completed_at)
                        )
                        completed_display = completed_datetime.strftime(
                            "%d %b %Y · %I:%M %p"
                        )
                        st.caption(
                            f"Completed: {completed_display}"
                        )
                    except (ValueError, TypeError):
                        pass

            # ------------------------------------------------
            # AUTOMATIC FOLLOW-UP ALREADY SENT
            # ------------------------------------------------

            elif campaign_status == "sent" and follow_up_count >= 1:

                st.success("📨 Automatic Follow-up Sent")

                if sent_at:
                    try:
                        sent_datetime = datetime.fromisoformat(
                            str(sent_at)
                        )
                        sent_display = sent_datetime.strftime(
                            "%d %b %Y · %I:%M %p"
                        )

                        st.markdown(
                            textwrap.dedent(
                                f"""
                                <div style="margin-top: 10px; padding: 14px 16px; border-radius: 8px; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.30);">
                                    <div style="font-size: 14px; font-weight: 700;">📨 OUT_OF_OFFICE Follow-up Sent</div>
                                    <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">Sent: <b>{sent_display}</b></div>
                                </div>
                                """
                            ),
                            unsafe_allow_html=True,
                        )

                    except (ValueError, TypeError):
                        pass

                # --------------------------------------------
                # 3-DAY RESPONSE WINDOW
                # --------------------------------------------

                if next_follow_up_at:

                    try:
                        deadline_datetime = datetime.fromisoformat(
                            str(next_follow_up_at)
                        )
                        deadline_display = deadline_datetime.strftime(
                            "%d %b %Y · %I:%M %p"
                        )

                        st.markdown(
                            textwrap.dedent(
                                f"""
                                <div style="margin-top: 12px; padding: 14px 16px; border-radius: 8px; background: rgba(234,179,8,0.08); border: 1px solid rgba(234,179,8,0.30);">
                                    <div style="font-size: 14px; font-weight: 700;">⏳ Waiting for Response</div>
                                    <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">Response deadline: <b>{deadline_display}</b></div>
                                    <div style="margin-top: 6px; font-size: 12px; color: #94a3b8;">If no response is received by this deadline, the campaign will be completed automatically.</div>
                                </div>
                                """
                            ),
                            unsafe_allow_html=True,
                        )

                    except (ValueError, TypeError):
                        pass

            # ------------------------------------------------
            # WAITING FOR ORIGINAL OUT-OF-OFFICE DATE
            # ------------------------------------------------

            else:

                st.warning(
                    "The contact is currently unavailable."
                )

                if next_follow_up_at:

                    try:
                        scheduled_datetime = datetime.fromisoformat(
                            str(next_follow_up_at)
                        )
                        scheduled_display = scheduled_datetime.strftime(
                            "%d %b %Y · %I:%M %p"
                        )

                        st.markdown(
                            textwrap.dedent(
                                f"""
                                <div style="margin-top: 12px; padding: 14px 16px; border-radius: 8px; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.30);">
                                    <div style="font-size: 14px; font-weight: 700;">⏰ Automatic Follow-up Scheduled</div>
                                    <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">Scheduled for: <b>{scheduled_display}</b></div>
                                    <div style="margin-top: 6px; font-size: 12px; color: #94a3b8;">The system will automatically send a follow-up when the scheduled time is due.</div>
                                </div>
                                """
                            ),
                            unsafe_allow_html=True,
                        )

                    except (ValueError, TypeError):
                        pass

                else:

                    st.info(
                        "The contact is currently unavailable. "
                        "An automatic follow-up will be scheduled."
                    )


        # ====================================================
        # UNCLEAR
        # ====================================================

        elif category == "UNCLEAR":

            st.warning(
                "The response could not be confidently interpreted."
            )

            st.info(
                "Please review the college's response and decide how to proceed. "
                "No automatic follow-up is scheduled."
            )

            if st.button(
                "🔍 Review Response",
                key=f"review_response_{campaign_id}",
                use_container_width=True,
            ):
                st.session_state[
                    "selected_campaign_action"
                ] = "review_response"

                st.success(
                    "Response review verified."
                )

            if st.session_state.get("selected_campaign_action") == "review_response":

                if st.button(
                    "✉️ Send Information",
                    key=f"send_information_interest_{campaign_id}",
                    use_container_width=True,
                ):
                    try:
                        response = requests.post(
                            f"{BASE_URL}/campaigns/{campaign_id}/send-information",
                            timeout=120,
                        )
                        response.raise_for_status()

                        st.session_state[
                            f"information_sent_{campaign_id}"
                        ] = True

                        st.rerun()

                    except requests.RequestException as exc:
                        try:
                            error_detail = response.json().get(
                                "detail",
                                str(exc)
                            )
                        except Exception:
                            error_detail = str(exc)

                        st.error(
                            f"Unable to send information: {error_detail}"
                        )


            if st.session_state.get(
                f"information_sent_{campaign_id}",
                False,
            ):

                st.success(
                    "✓ Information package sent successfully."
                )

                st.markdown("""
            ✓ Course / Training Information  
            ✓ Brochure  
            ✓ 1-Day Workshop Information  
            ✓ 2-Day Workshop Information  
            ✓ 3-Day Workshop Information
            """)

                st.info(
                    "Waiting for the college's next response."
                )


# ============================================================
# STEP-6: CAMPAIGN TIMELINE
# ============================================================

st.markdown("### ⏳ Campaign Timeline")

history = CampaignService.get_history(campaign_id)


# ------------------------------------------------------------
# Helper: format real campaign timestamp
# ------------------------------------------------------------

def format_timeline_datetime(value):
    if not value:
        return None, None

    try:
        if isinstance(value, str):
            value = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(value)
        else:
            dt = value

        return (
            dt.strftime("%b %d"),
            dt.strftime("%I:%M %p"),
        )

    except Exception:
        return str(value), None


# ------------------------------------------------------------
# Build timeline events
# ------------------------------------------------------------

timeline_events = []


def add_timeline_event(
    timestamp,
    title,
    description=None,
    icon="✓",
    event_class="completed",
):
    if not timestamp:
        return

    date_text, time_text = format_timeline_datetime(timestamp)

    if not date_text:
        return

    timeline_events.append(
        {
            "timestamp": timestamp,
            "date": date_text,
            "time": time_text,
            "title": title,
            "description": description,
            "icon": icon,
            "class": event_class,
        }
    )


# ------------------------------------------------------------
# 1. Campaign Created
# ------------------------------------------------------------

add_timeline_event(
    campaign.get("created_at"),
    "Campaign created",
)


# ------------------------------------------------------------
# 2. Read actual campaign history
# ------------------------------------------------------------

history_events = []

for event in history or []:

    timestamp = (
        event.get("changed_at")
        or event.get("created_at")
        or event.get("timestamp")
    )

    event_type = str(
        event.get("event_type")
        or event.get("action")
        or event.get("status")
        or ""
    ).lower()

    description = (
        event.get("description")
        or event.get("message")
        or ""
    )

    history_events.append(
        {
            "timestamp": timestamp,
            "event_type": event_type,
            "description": description,
        }
    )


# ------------------------------------------------------------
# 3. Campaign Strategy
# ------------------------------------------------------------

for event in history_events:

    event_text = (
        event["event_type"]
        + " "
        + event["description"]
    ).lower()

    if "strategy" in event_text:
        add_timeline_event(
            event["timestamp"],
            "Campaign Strategy completed",
            event["description"] or None,
        )
        break


# ------------------------------------------------------------
# 4. Message Personalized
# ------------------------------------------------------------

for event in history_events:

    event_text = (
        event["event_type"]
        + " "
        + event["description"]
    ).lower()

    if (
        "personaliz" in event_text
        or "message generated" in event_text
        or "message created" in event_text
    ):
        add_timeline_event(
            event["timestamp"],
            "Message personalized",
            event["description"] or None,
        )
        break


# ------------------------------------------------------------
# 5. Human Approval
# ------------------------------------------------------------

for event in history_events:

    event_text = (
        event["event_type"]
        + " "
        + event["description"]
    ).lower()

    if (
        "approv" in event_text
        and "reject" not in event_text
    ):
        add_timeline_event(
            event["timestamp"],
            "Human approved",
            event["description"] or None,
        )
        break


# ------------------------------------------------------------
# 6. Email Sent
# ------------------------------------------------------------

add_timeline_event(
    campaign.get("sent_at"),
    "Email sent",
)


# ------------------------------------------------------------
# 7. College Response
# ------------------------------------------------------------

response_timestamp = campaign.get(
    "last_response_at"
)

if response_timestamp:

    add_timeline_event(
        response_timestamp,
        "Response received",
    )


# ------------------------------------------------------------
# 8. Response Classified
# ------------------------------------------------------------

response_category = campaign.get(
    "response_category"
)

if response_category and response_timestamp:

    add_timeline_event(
        response_timestamp,
        "Response classified",
        str(response_category).upper(),
    )


# ------------------------------------------------------------
# 9. Human Action Required
# ------------------------------------------------------------

if (
    response_category
    and response_timestamp
    and str(campaign.get("status", "")).lower()
    == "replied"
):

    add_timeline_event(
        response_timestamp,
        "Human action required",
        "Review the response and decide the next action.",
        icon="🔔",
        event_class="action-required",
    )


# ------------------------------------------------------------
# Sort by actual timestamp
# ------------------------------------------------------------

def timeline_sort_key(event):

    value = event.get("timestamp")

    if isinstance(value, datetime):
        return value

    try:
        if isinstance(value, str):
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
    except Exception:
        pass

    return datetime.min


timeline_events.sort(
    key=timeline_sort_key
)


# ------------------------------------------------------------
# Timeline CSS
# ------------------------------------------------------------

st.markdown(
    """
    <style>

    .campaign-timeline {
        margin-top: 10px;
        padding: 8px 0 5px 0;
    }

    .timeline-event {
        display: grid;
        grid-template-columns: 75px 32px 1fr;
        column-gap: 8px;
        margin-bottom: 18px;
        position: relative;
    }

    .timeline-date {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        padding-top: 2px;
    }

    .timeline-icon {
        font-size: 16px;
        font-weight: 600;
        position: relative;
        text-align: center;
    }

    .timeline-icon::after {
        content: "";
        position: absolute;
        top: 22px;
        left: 50%;
        width: 1px;
        height: 35px;
        background: #dbe3ea;
    }

    .timeline-event:last-child .timeline-icon::after {
        display: none;
    }

    .timeline-title {
        font-size: 14px;
        font-weight: 600;
        color: #1e293b;
        line-height: 1.4;
    }

    .timeline-time {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
    }

    .timeline-description {
        font-size: 12px;
        color: #64748b;
        margin-top: 3px;
    }

    .timeline-action .timeline-title {
        color: #d97706;
    }

    .timeline-action .timeline-icon {
        animation: timelinePulse 1.8s ease-in-out infinite;
    }

    @keyframes timelinePulse {
        0% {
            opacity: 0.55;
        }

        50% {
            opacity: 1;
        }

        100% {
            opacity: 0.55;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Render Timeline
# ------------------------------------------------------------

if not timeline_events:

    st.caption("No campaign activity recorded yet.")

else:

    for event in timeline_events:

        col1, col2, col3 = st.columns([1, 0.3, 4])

        with col1:
            st.caption(event["date"])

        with col2:
            st.write(event["icon"])

        with col3:
            st.markdown(
                f"**{event['title']}**"
            )

            if event.get("time"):
                st.caption(
                    event["time"]
                )

            if event.get("description"):
                st.caption(
                    event["description"]
                )