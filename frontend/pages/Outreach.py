import streamlit as st
from datetime import datetime, date, time

from services.outreach_service import OutreachService


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Outreach | AAMP",
    page_icon="📨",
    layout="wide",
)


# =========================================================
# HEADER
# =========================================================

st.title("📨 Outreach Management")

st.caption(
    "Manage outreach messages, college responses, "
    "follow-ups and demo meetings."
)


# =========================================================
# LOAD OUTREACH DATA
# =========================================================

try:

    outreach_list = OutreachService.get_all()

    if isinstance(outreach_list, dict):

        outreach_list = outreach_list.get(
            "outreach",
            outreach_list.get("data", [])
        )

    if outreach_list is None:

        outreach_list = []

except Exception as e:

    st.error(
        f"Failed to load outreach: {str(e)}"
    )

    st.stop()


# =========================================================
# SUMMARY COUNTS
# =========================================================

total = len(outreach_list)

queued = sum(
    1
    for item in outreach_list
    if str(item.get("status", "")).lower() == "queued"
)

sent = sum(
    1
    for item in outreach_list
    if str(item.get("status", "")).lower() == "sent"
)

follow_up = sum(
    1
    for item in outreach_list
    if str(item.get("status", "")).lower()
    == "follow_up_due"
)

replied = sum(
    1
    for item in outreach_list
    if str(item.get("status", "")).lower()
    in ["responded", "replied"]
)

opted_out = sum(
    1
    for item in outreach_list
    if str(item.get("status", "")).lower()
    == "opted_out"
)

completed = sum(
    1
    for item in outreach_list
    if str(item.get("status", "")).lower()
    == "completed"
)


# =========================================================
# SUMMARY CARDS
# =========================================================

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:

    st.metric(
        "Total",
        total
    )

with col2:

    st.metric(
        "Queued",
        queued
    )

with col3:

    st.metric(
        "Sent",
        sent
    )

with col4:

    st.metric(
        "Follow-up",
        follow_up
    )

with col5:

    st.metric(
        "Replied",
        replied
    )

with col6:

    st.metric(
        "Opted Out",
        opted_out
    )


st.divider()


# =========================================================
# SEARCH + FILTER
# =========================================================

st.subheader("🔎 Outreach")

filter_col1, filter_col2 = st.columns([2, 1])


with filter_col1:

    search = st.text_input(
        "Search",
        placeholder=(
            "Search by college, recipient or subject..."
        )
    )


with filter_col2:

    status_filter = st.selectbox(
        "Status",
        [
            "All",
            "queued",
            "sent",
            "follow_up_due",
            "responded",
            "opted_out",
            "completed",
            "failed",
        ],
    )


# =========================================================
# FILTER DATA
# =========================================================

filtered_outreach = []

for item in outreach_list:

    college_name = str(
        item.get("college_name", "")
    ).lower()

    recipient = str(
        item.get("recipient", "")
    ).lower()

    subject = str(
        item.get("subject", "")
    ).lower()

    status = str(
        item.get("status", "")
    ).lower()

    search_text = (
        f"{college_name} "
        f"{recipient} "
        f"{subject}"
    )

    if search:

        if search.lower() not in search_text:

            continue

    if status_filter != "All":

        if status != status_filter.lower():

            continue

    filtered_outreach.append(item)


# =========================================================
# NO DATA
# =========================================================

if not filtered_outreach:

    st.info(
        "No outreach records found."
    )

    if st.button(
        "🔄 Refresh"
    ):

        st.rerun()

    st.stop()


# =========================================================
# OUTREACH CARDS
# =========================================================

for item in filtered_outreach:

    outreach_id = item.get("id")

    campaign_id = item.get(
        "campaign_id"
    )

    college_id = item.get(
        "college_id"
    )

    college_name = (
        item.get("college_name")
        or item.get("college")
        or f"College #{college_id}"
    )

    channel = item.get(
        "channel",
        "manual_review"
    )

    recipient = (
        item.get("recipient")
        or "Not available"
    )

    subject = (
        item.get("subject")
        or "No subject"
    )

    message = item.get(
        "message",
        ""
    )

    status = str(
        item.get(
            "status",
            "unknown"
        )
    )

    follow_up_count = item.get(
        "follow_up_count",
        0
    )

    response_received_at = item.get(
        "response_received_at"
    )

    status_lower = status.lower()


    # =====================================================
    # STATUS DISPLAY
    # =====================================================

    if status_lower == "queued":

        status_text = "🟡 Queued"

    elif status_lower == "sent":

        status_text = "🟢 Sent"

    elif status_lower == "follow_up_due":

        status_text = "🟠 Follow-up Due"

    elif status_lower in [
        "responded",
        "replied"
    ]:

        status_text = "🔵 Replied"

    elif status_lower == "opted_out":

        status_text = "🔴 Opted Out"

    elif status_lower == "completed":

        status_text = "✅ Completed"

    elif status_lower == "failed":

        status_text = "❌ Failed"

    else:

        status_text = (
            f"⚪ {status.title()}"
        )


    # =====================================================
    # CARD
    # =====================================================

    with st.container(border=True):

        top1, top2, top3 = st.columns(
            [4, 2, 2]
        )


        with top1:

            st.markdown(
                f"### 🏫 {college_name}"
            )


        with top2:

            st.markdown(
                f"**Status**  \n"
                f"{status_text}"
            )


        with top3:

            st.markdown(
                f"**Channel**  \n"
                f"{channel.title()}"
            )


        st.markdown("---")


        # =================================================
        # BASIC INFORMATION
        # =================================================

        info1, info2, info3 = st.columns(3)


        with info1:

            st.write(
                f"**Outreach ID:** {outreach_id}"
            )

            st.write(
                f"**Campaign ID:** {campaign_id}"
            )


        with info2:

            st.write(
                f"**Recipient:** {recipient}"
            )

            st.write(
                f"**Follow-ups:** {follow_up_count}"
            )


        with info3:

            st.write(
                f"**Subject:** {subject}"
            )

            if response_received_at:

                st.write(
                    f"**Response:** "
                    f"{response_received_at}"
                )


        # =================================================
        # SENT MESSAGE
        # =================================================

        with st.expander(
            "📤 View Sent Message"
        ):

            if message:

                st.text_area(
                    "Message",
                    value=message,
                    height=180,
                    disabled=True,
                    key=f"message_{outreach_id}",
                )

            else:

                st.info(
                    "No message available."
                )


        # =================================================
        # COLLEGE RESPONSE
        # =================================================

        if status_lower in [
            "responded",
            "replied",
            "opted_out"
        ]:

            st.markdown(
                "### 💬 College Response"
            )

            response_text = item.get(
                "response_text"
            )

            response_category = item.get(
                "response_category"
            )


            if response_text:

                st.info(
                    response_text
                )

            else:

                st.info(
                    "Response received. "
                    "Open the details to view the response."
                )


            if response_category:

                st.write(
                    f"**Response Type:** "
                    f"`{response_category}`"
                )


        # =================================================
        # ACTION BUTTONS
        # =================================================

        action1, action2, action3 = st.columns(3)


        # =================================================
        # VIEW DETAILS
        # =================================================

        with action1:

            if st.button(
                "🔍 View Details",
                key=f"details_{outreach_id}",
                use_container_width=True,
            ):

                try:

                    details = (
                        OutreachService.get_by_id(
                            outreach_id
                        )
                    )

                    st.session_state[
                        f"outreach_details_{outreach_id}"
                    ] = details

                except Exception as e:

                    st.error(
                        f"Unable to load details: {str(e)}"
                    )


        # =================================================
        # FOLLOW-UP
        # =================================================

        with action2:

            if status_lower == "follow_up_due":

                if st.button(
                    "📅 Check Follow-up",
                    key=f"followup_{outreach_id}",
                    use_container_width=True,
                ):

                    try:

                        result = (
                            OutreachService.check_follow_up(
                                outreach_id
                            )
                        )

                        st.success(
                            "Follow-up status checked."
                        )

                        st.json(
                            result
                        )

                    except Exception as e:

                        st.error(
                            f"Follow-up check failed: {str(e)}"
                        )


        # =================================================
        # SEND FOLLOW-UP
        # =================================================

        with action3:

            if status_lower == "follow_up_due":

                if st.button(
                    "📨 Send Follow-up",
                    key=f"sendfollowup_{outreach_id}",
                    use_container_width=True,
                ):

                    try:

                        result = (
                            OutreachService.send_follow_up(
                                outreach_id
                            )
                        )

                        st.success(
                            "Follow-up processed successfully."
                        )

                        st.json(
                            result
                        )

                    except Exception as e:

                        st.error(
                            f"Unable to send follow-up: {str(e)}"
                        )


        # =================================================
        # INTERESTED → DEMO MEETING
        # =================================================

        if status_lower in [
            "responded",
            "replied"
        ]:

            st.markdown("---")

            st.markdown(
                "### 🤝 Demo / Meeting"
            )

            st.caption(
                "If the college is interested, "
                "schedule a demo discussion."
            )


            meeting_col1, meeting_col2 = st.columns(2)


            with meeting_col1:

                meeting_date = st.date_input(
                    "📅 Meeting Date",
                    value=date.today(),
                    key=f"meeting_date_{outreach_id}",
                )


            with meeting_col2:

                meeting_time = st.time_input(
                    "⏰ Meeting Time",
                    value=time(11, 0),
                    key=f"meeting_time_{outreach_id}",
                )


            meeting_title = st.text_input(
                "Meeting Title",
                value=(
                    f"AI Training Demo - "
                    f"{college_name}"
                ),
                key=f"meeting_title_{outreach_id}",
            )


            meeting_notes = st.text_area(
                "Meeting Notes",
                placeholder=(
                    "Example: Discuss Generative AI / "
                    "Agentic AI demo, duration, "
                    "student audience..."
                ),
                key=f"meeting_notes_{outreach_id}",
            )


            # =================================================
            # SCHEDULE DEMO
            # =================================================

            if st.button(
                "📅 Schedule Demo Meeting",
                key=f"schedule_{outreach_id}",
                use_container_width=True,
            ):

                payload = {
                    "college_name": college_name,
                    "recipient": recipient,
                    "selected_date": meeting_date.isoformat(),
                    "selected_time": meeting_time.strftime(
                        "%I:%M %p"
                    ),
                }


                try:

                    with st.spinner(
                        "Scheduling demo..."
                    ):

                        result = (
                            OutreachService.schedule_demo(
                                payload
                            )
                        )


                    if result.get("status") == "scheduled":

                        st.session_state[
                            f"meeting_{outreach_id}"
                        ] = {

                            "title": meeting_title,

                            "college": college_name,

                            "date": result.get(
                                "demo_date"
                            ),

                            "time": result.get(
                                "demo_time"
                            ),

                            "datetime": result.get(
                                "scheduled_at"
                            ),

                            "notes": meeting_notes,

                            "status": "scheduled",

                            "confirmation_message": (
                                result.get(
                                    "confirmation_message"
                                )
                            ),

                            "real_message_sent": (
                                result.get(
                                    "real_message_sent",
                                    False,
                                )
                            ),
                        }


                        st.success(
                            "✅ Demo meeting scheduled successfully!"
                        )


                        if result.get(
                            "confirmation_message"
                        ):

                            st.info(
                                result[
                                    "confirmation_message"
                                ]
                            )


                    else:

                        st.error(
                            result.get(
                                "message",
                                "Demo scheduling failed.",
                            )
                        )


                except Exception as e:

                    st.error(
                        f"Unable to schedule demo: {str(e)}"
                    )


            # =================================================
            # SHOW SCHEDULED MEETING
            # =================================================

            meeting_key = (
                f"meeting_{outreach_id}"
            )


            if meeting_key in st.session_state:

                meeting = (
                    st.session_state[
                        meeting_key
                    ]
                )


                st.markdown(
                    "#### ✅ Scheduled Meeting"
                )


                st.write(
                    f"**Title:** "
                    f"{meeting['title']}"
                )


                st.write(
                    f"**College:** "
                    f"{meeting['college']}"
                )


                st.write(
                    f"**Date:** "
                    f"{meeting['date']}"
                )


                st.write(
                    f"**Time:** "
                    f"{meeting['time']}"
                )


                st.write(
                    f"**Status:** 🟢 "
                    f"{meeting['status'].title()}"
                )


                if meeting.get("notes"):

                    st.write(
                        f"**Notes:** "
                        f"{meeting['notes']}"
                    )


                if meeting.get(
                    "confirmation_message"
                ):

                    st.info(
                        meeting[
                            "confirmation_message"
                        ]
                    )


                if meeting.get(
                    "real_message_sent"
                ):

                    st.success(
                        "Confirmation message sent."
                    )

                else:

                    st.caption(
                        "Confirmation message prepared. "
                        "No real message was sent."
                    )


        # =================================================
        # DETAILS
        # =================================================

        details_key = (
            f"outreach_details_{outreach_id}"
        )


        if details_key in st.session_state:

            st.markdown(
                "#### 📋 Outreach Details"
            )


            details = (
                st.session_state[
                    details_key
                ]
            )


            if isinstance(
                details,
                dict
            ):

                d1, d2 = st.columns(2)


                with d1:

                    st.write(
                        f"**Status:** "
                        f"{details.get('status', 'N/A')}"
                    )


                    st.write(
                        f"**Recipient:** "
                        f"{details.get('recipient', 'N/A')}"
                    )


                    st.write(
                        f"**Channel:** "
                        f"{details.get('channel', 'N/A')}"
                    )


                with d2:

                    st.write(
                        f"**Follow-up Count:** "
                        f"{details.get('follow_up_count', 0)}"
                    )


                    st.write(
                        f"**Scheduled At:** "
                        f"{details.get('scheduled_at', 'N/A')}"
                    )


                    st.write(
                        f"**Sent At:** "
                        f"{details.get('sent_at', 'N/A')}"
                    )


            else:

                st.write(
                    details
                )


# =========================================================
# REFRESH
# =========================================================

st.divider()


if st.button(
    "🔄 Refresh Outreach"
):

    st.rerun()