import streamlit as st
from datetime import datetime
import requests

from services.campaign_service import CampaignService
from services.college_service import CollegeService
from components.common import init_page

BASE_URL = "http://127.0.0.1:8000/api/v1"
# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_campaign_type(value):
    if not value:
        return "Campaign"

    return str(value).replace("_", " ").title()


def format_channel(value):
    if not value:
        return "N/A"

    return str(value).replace("_", " ").title()


def get_campaign_actions(campaign_status):
    status = str(campaign_status or "").lower()

    actions = {
        "draft": (
            "Campaign created",
            "Review and approve campaign",
        ),
        "approved": (
            "Campaign approved",
            "Send campaign",
        ),
        "sent": (
            "Initial outreach sent",
            "Follow-up 1 if no response",
        ),
        "follow_up_1": (
            "Follow-up 1 sent",
            "Follow-up 2 if no response",
        ),
        "follow_up_2": (
            "Follow-up 2 sent",
            "Complete campaign if no response",
        ),
        "replied": (
            "Response received",
            "Review response",
        ),
        "completed": (
            "Campaign completed",
            "No further action",
        ),
        "closed": (
            "Campaign closed",
            "No further action",
        ),
        "rejected": (
            "Campaign rejected",
            "Create or edit campaign",
        ),
        "failed": (
            "Campaign failed",
            "Review campaign",
        ),
        "opted_out": (
            "College opted out",
            "No further outreach",
        ),
    }

    return actions.get(
        status,
        (
            "Campaign status updated",
            "Review campaign",
        ),
    )


def get_display_status(campaign):
    status = str(
        campaign.get("status", "")
    ).lower()

    if (
        status == "draft"
        and campaign.get("required_approval") is True
    ):
        return "Approval Pending"

    status_labels = {
        "follow_up_1": "Follow-up 1",
        "follow_up_2": "Follow-up 2",
        "proposal": "Proposal",
        "opt_out": "Completed",
        "opted_out": "Completed",
    }

    return status_labels.get(
        status,
        status.title(),
    )


def get_status_class(display_status):
    status = str(
        display_status or ""
    ).lower()

    status_classes = {
        "approval pending": "status-pending",
        "approved": "status-approved",
        "sent": "status-sent",
        "follow-up 1": "status-followup",
        "follow-up 2": "status-followup",
        "replied": "status-replied",
        "proposal": "status-proposal",
        "completed": "status-completed",
        "closed": "status-closed",
        "rejected": "status-rejected",
        "failed": "status-failed",
        "opted out": "status-opted-out",
    }

    return status_classes.get(
        status,
        "status-default",
    )


init_page("Campaigns")


# =========================================================
# COLLEGE STATUS STYLING
# =========================================================

st.markdown(
    """
    <style>

    /* Reserve space on the right for the status */
    div[data-testid="stExpander"] summary {
        position: relative;
        padding-right: 190px !important;
    }

    /* Default status */
    div[data-testid="stExpander"]:has(.status-default) summary::after {
        color: #94a3b8;
        content: "● Status";
    }

    /* Approval Pending */
    div[data-testid="stExpander"]:has(.status-pending) summary::after {
        color: #f59e0b;
        content: "● Approval Pending";
    }

    /* Approved */
    div[data-testid="stExpander"]:has(.status-approved) summary::after {
        color: #22c55e;
        content: "● Approved";
    }

    /* Sent */
    div[data-testid="stExpander"]:has(.status-sent) summary::after {
        color: #3b82f6;
        content: "● Sent";
    }

    /* Proposal */
    div[data-testid="stExpander"]:has(.status-proposal) summary::after {
        color: #a855f7;
        content: "● Proposal";
    }

    /* Follow-ups */
    div[data-testid="stExpander"]:has(.status-followup) summary::after {
        color: #eab308;
        content: "● Follow-up";
    }

    /* Replied */
    div[data-testid="stExpander"]:has(.status-replied) summary::after {
        color: #22c55e;
        content: "● Replied";
    }

    /* Completed */
    div[data-testid="stExpander"]:has(.status-completed) summary::after {
        color: #94a3b8;
        content: "● Completed";
    }

    /* Closed */
    div[data-testid="stExpander"]:has(.status-closed) summary::after {
        color: #94a3b8;
        content: "● Closed";
    }

    /* Rejected */
    div[data-testid="stExpander"]:has(.status-rejected) summary::after {
        color: #ef4444;
        content: "● Rejected";
    }

    /* Failed */
    div[data-testid="stExpander"]:has(.status-failed) summary::after {
        color: #ef4444;
        content: "● Failed";
    }

    /* Opted Out */
    div[data-testid="stExpander"]:has(.status-opted-out) summary::after {
        color: #ef4444;
        content: "● Opted Out";
    }

    /* Right-side status */
    div[data-testid="stExpander"] summary::after {
        position: absolute;
        right: 25px;
        top: 50%;
        transform: translateY(-50%);

        font-size: 14px;
        font-weight: 600;

        white-space: nowrap;

        animation: statusPulse 1.8s ease-in-out infinite;
    }

    /* Running dot effect */
    @keyframes statusPulse {
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


# =========================================================
# PAGE HEADER
# =========================================================

st.title("Campaigns")
st.caption("Manage campaign review and outreach.")

# =========================================================
# CREATE CAMPAIGN
# =========================================================

create_col1, create_col2 = st.columns([6, 1.5])

with create_col2:

    create_campaign_clicked = st.button(
        "＋ Create Campaign",
        type="primary",
        use_container_width=True,
    )


if create_campaign_clicked:
    st.session_state["show_create_campaign"] = True


if st.session_state.get(
    "show_create_campaign",
    False,
):

    st.divider()

    st.markdown("### Create Campaign")
    st.caption(
        "Create a draft campaign. It must be approved before sending."
    )

    # -----------------------------------------------------
    # Load colleges
    # -----------------------------------------------------

    try:

        college_response = CollegeService.search()
        college_results = college_response.get("results", [])

        state_options = {}

        for item in college_results:

            college = item.get("college", {})

            college_id = college.get("id")
            college_name = college.get("name")
            college_state = college.get("state")

            if college_id is not None and college_name and college_state:
                state_options.setdefault(college_state, {})
                state_options[college_state][
                    f"{college_name} (ID: {college_id})"
                ] = college_id

    except Exception as exc:

        st.error(
            f"Failed to load colleges: {exc}"
        )
        state_options = {}


    if not state_options:

        st.warning(
            "No colleges are available. "
            "Create or discover a college first."
        )

    else:

        with st.form("create_campaign_form"):

            selected_state = st.selectbox(
                "State",
                sorted(state_options.keys()),
            )

            college_options = state_options[selected_state]

            selected_college_label = st.selectbox(
                "College",
                list(college_options.keys()),
            )


            campaign_type = st.selectbox(
                "Campaign Type",
                [
                    "institutional_training",
                    "course_promotion",
                    "partnership",
                    "event_invitation",
                    "general_outreach",
                ],
            )

            message_type = st.selectbox(
                "Message Type",
                [
                    "initial_outreach",
                    "follow_up",
                    "proposal",
                    "event_invitation",
                ],
            )

            channel = st.selectbox(
                "Channel",
                [
                    "email",
                    "whatsapp",
                    "contact_form",
                    "linkedin",
                    "phone",
                ],
            )

            priority = st.selectbox(
                "Priority",
                [
                    "high",
                    "medium",
                    "low",
                ],
                index=1,
            )

            subject = st.text_input(
                "Subject",
                placeholder="Enter campaign subject",
            )

            message = st.text_area(
                "Message",
                placeholder="Enter campaign message",
                height=180,
            )

            form_col1, form_col2 = st.columns(2)

            with form_col1:

                create_draft = st.form_submit_button(
                    "Create Draft",
                    type="primary",
                    use_container_width=True,
                )

            with form_col2:

                cancel_create = st.form_submit_button(
                    "Cancel",
                    use_container_width=True,
                )


            if cancel_create:

                st.session_state[
                    "show_create_campaign"
                ] = False

                st.rerun()


            if create_draft:

                if not subject.strip():
                    st.error(
                        "Subject is required."
                    )

                elif not message.strip():
                    st.error(
                        "Message is required."
                    )

                else:

                    try:

                        selected_college_id = college_options[
                            selected_college_label
                        ]

                        CampaignService.create(
                            {
                                "college_id": selected_college_id,
                                "campaign_type": campaign_type,
                                "message_type": message_type,
                                "channel": channel,
                                "subject": subject.strip(),
                                "message": message.strip(),
                                "priority": priority,
                            }
                        )

                        st.success(
                            "Campaign draft created successfully."
                        )

                        st.session_state[
                            "show_create_campaign"
                        ] = False

                        st.rerun()

                    except Exception as exc:

                        st.error(
                            f"Failed to create campaign: {exc}"
                        )

    st.divider()


# =========================================================
# STATUS CONFIGURATION
# =========================================================

status_options = {
    "All": None,
    "Approval Pending": "draft",
    "Approved": "approved",
    "Rejected": "rejected",
    "Sent": "sent",
    "Follow-up 1": "follow_up_1",
    "Follow-up 2": "follow_up_2",
    "Replied": "replied",
    "Completed": "completed",
    "Closed": "closed",
    "Failed": "failed",
    "Opted Out": "opted_out",
}


# =========================================================
# LOAD CAMPAIGNS + COLLEGES
# =========================================================

selected_status = st.selectbox(
    "Campaign Status",
    list(status_options.keys()),
)

status = status_options[selected_status]


try:

    with st.spinner("Loading campaigns..."):

        if status:
            campaigns = CampaignService.get_by_status(status)
        else:
            campaigns = CampaignService.get_all()

        if campaigns is None:
            campaigns = []

        # ---------------------------------------------
        # Load college names
        # ---------------------------------------------
        college_response = CollegeService.search()
        college_results = college_response.get("results", [])

        college_names = {}

        for item in college_results:

            college = item.get("college", {})

            college_id = college.get("id")
            college_name = college.get("name")

            if college_id is not None:
                college_names[college_id] = college_name

        # ---------------------------------------------
        # Group campaigns by college
        # ---------------------------------------------
        colleges = {}

        for campaign in campaigns:

            college_id = campaign.get("college_id")

            if college_id not in colleges:
                colleges[college_id] = []

            colleges[college_id].append(campaign)


except Exception as exc:

    st.error(f"Failed to load campaigns: {exc}")
    st.stop()


# =========================================================
# STATUS SUMMARY
# =========================================================

# We calculate summary from all campaigns so that the
# overview remains meaningful even when a filter is selected.

try:

    all_campaigns = CampaignService.get_all()

    if all_campaigns is None:
        all_campaigns = []

except Exception:
    all_campaigns = campaigns


status_counts = {
    "draft": 0,
    "approved": 0,
    "rejected": 0,
    "sent": 0,
    "replied": 0,
    "closed": 0,
}


for campaign in all_campaigns:

    campaign_status = str(
        campaign.get("status", "")
    ).lower()

    if campaign_status in status_counts:
        status_counts[campaign_status] += 1


# =========================================================
# CAMPAIGN OVERVIEW
# =========================================================

st.markdown("### Campaign Overview")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        "Total",
        len(all_campaigns),
    )

with col2:
    st.metric(
        "Pending",
        status_counts["draft"],
    )

with col3:
    st.metric(
        "Approved",
        status_counts["approved"],
    )

with col4:
    st.metric(
        "Sent",
        status_counts["sent"],
    )

with col5:
    st.metric(
        "Replied",
        status_counts["replied"],
    )

with col6:
    st.metric(
        "Closed",
        status_counts["closed"],
    )

# =========================================================
# READY TO CREATE CAMPAIGN DRAFTS
# =========================================================

try:

    college_response = CollegeService.get_overview()

    overview_results = college_response.get(
        "results",
        [],
    )

except Exception as exc:

    st.error(
        f"Failed to load college overview: {exc}"
    )

    overview_results = []


ready_to_create = 0

for item in overview_results:

    lead = item.get("lead") or {}
    campaign = item.get("campaign")

    qualification = (
        lead.get("qualification") or ""
    ).lower()

    if qualification == "qualified" and campaign is None:
        ready_to_create += 1


st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:

    st.markdown("### Campaign Drafts")

    st.caption(
        f"Qualified leads ready for campaign creation: {ready_to_create}"
    )

with col2:

    create_draft_button = st.button(
        "🎯 Create Draft",
        disabled=(ready_to_create == 0),
        use_container_width=True,
    )


# =========================================================
# FILTER RESULT
# =========================================================

st.divider()

if not campaigns:

    st.info(
        f"No campaigns found for {selected_status.lower()}."
    )
    st.stop()

# =========================================================
# CAMPAIGN COLLEGES
# =========================================================

st.markdown("### Campaign Colleges")
st.caption(
    f"{len(colleges)} "
    f"{'college' if len(colleges) == 1 else 'colleges'} "
    f"with campaigns"
)


# =========================================================
# BULK APPROVAL
# =========================================================

pending_approval_count = sum(
    1
    for campaign in campaigns
    if str(campaign.get("status", "")).lower() == "draft"
    and campaign.get("required_approval") is True
)

bulk_col1, bulk_col2 = st.columns([1, 4])

with bulk_col1:

    if st.button(
        "✅ Approve All",
        type="primary",
        use_container_width=True,
        disabled=(pending_approval_count == 0),
    ):

        try:

            response = requests.post(
                f"{BASE_URL}/campaigns/bulk-approve",
                timeout=120,
            )

            response.raise_for_status()

            result = response.json()

            approved_count = result.get(
                "approved_count",
                0,
            )

            if approved_count > 0:

                st.success(
                    f"✅ {approved_count} campaigns approved successfully."
                )

            else:

                st.info(
                    "No campaigns pending approval."
                )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Bulk approval failed: {exc}"
            )

with bulk_col2:

    if pending_approval_count > 0:

        st.caption(
            f"{pending_approval_count} campaigns pending approval"
        )

    else:

        st.caption(
            "No campaigns pending approval"
        )

# =========================================================
# BULK OUTREACH
# =========================================================

approved_count = sum(
    1
    for campaign in campaigns
    if str(campaign.get("status", "")).lower() == "approved"
)

bulk_send_col1, bulk_send_col2 = st.columns([1, 4])

with bulk_send_col1:
    if st.button(
        "🚀 Send All Approved",
        type="primary",
        use_container_width=True,
        disabled=(approved_count == 0),
    ):
        st.session_state["confirm_bulk_send"] = True

with bulk_send_col2:
    if approved_count > 0:
        st.caption(
            f"{approved_count} approved campaigns ready to send"
        )
    else:
        st.caption("No approved campaigns ready to send.")

if st.session_state.get("confirm_bulk_send", False):

    st.warning(
        f"⚠️ This will send real emails to "
        f"{approved_count} approved college campaigns."
    )

    confirm_col1, confirm_col2 = st.columns(2)

    with confirm_col1:
        if st.button(
            "🚀 Confirm & Send All",
            type="primary",
            use_container_width=True,
        ):
            try:
                response = requests.post(
                    f"{BASE_URL}/campaigns/bulk-approved-process",
                    timeout=600,
                )

                response.raise_for_status()

                result = response.json()

                sent_count = result.get("sent_count", 0)
                failed_count = result.get("failed_count", 0)

                st.session_state["confirm_bulk_send"] = False

                if failed_count == 0:
                    st.success(
                        f"✅ {sent_count} campaigns sent successfully."
                    )
                else:
                    st.warning(
                        f"⚠️ {sent_count} sent, "
                        f"{failed_count} failed."
                    )

                st.rerun()

            except Exception as exc:
                st.error(
                    f"Bulk outreach failed: {exc}"
                )

    with confirm_col2:
        if st.button(
            "Cancel",
            use_container_width=True,
        ):
            st.session_state["confirm_bulk_send"] = False
            st.rerun()


# =========================================================
# COLLEGE LIST
# =========================================================

for college_id, college_campaigns in colleges.items():

    # -----------------------------------------------------
    # Resolve college name
    # -----------------------------------------------------

    college_name = (
        college_names.get(college_id)
        or f"College ID: {college_id}"
    )

    # -----------------------------------------------------
    # Determine current campaign
    # -----------------------------------------------------

    current_campaign = max(
        college_campaigns,
        key=lambda item: str(
            item.get("created_at") or ""
        ),
    )

    current_display_status = get_display_status(
        current_campaign
    )

    status_class = get_status_class(
        current_display_status
    )


    with st.expander(
        f"🏛️ {college_name}"
    ):

        # Hidden marker used by CSS to place
        # the dynamic status in the expander header.
        st.markdown(
            f'<span class="{status_class}"></span>',
            unsafe_allow_html=True,
        )

        st.caption(
            f"College ID: {college_id}"
        )


        # =================================================
        # CAMPAIGN HISTORY
        # =================================================

        for campaign in college_campaigns:

            campaign_id = campaign.get("id")

            campaign_status = str(
                campaign.get("status", "")
            ).lower()

            campaign_type = campaign.get(
                "campaign_type",
                "Campaign",
            )

            message_type = campaign.get(
                "message_type",
                "N/A",
            )

            channel = campaign.get(
                "channel",
                "N/A",
            )

            priority = campaign.get(
                "priority",
                "N/A",
            )

            subject = campaign.get(
                "subject"
            ) or "No subject"

            message = campaign.get(
                "message",
                "",
            )

            created_at = campaign.get(
                "created_at"
            )

            # -------------------------------------------------
            # Campaign display information
            # -------------------------------------------------

            campaign_title = format_campaign_type(
                campaign_type
            )

            last_action, next_action = get_campaign_actions(
                campaign_status
            )


            # -------------------------------------------------
            # Format created date
            # -------------------------------------------------

            if created_at:

                try:

                    if isinstance(created_at, str):

                        created_datetime = (
                            datetime.fromisoformat(
                                created_at
                            )
                        )

                    else:

                        created_datetime = created_at

                    created_date = (
                        created_datetime.strftime(
                            "%b %d, %Y · %I:%M %p"
                        )
                    )

                except (ValueError, TypeError):

                    created_date = str(
                        created_at
                    )

            else:

                created_date = "N/A"


            # -------------------------------------------------
            # Display status
            # -------------------------------------------------

            display_status = (
                "Approval Pending"
                if (
                    campaign_status == "draft"
                    and campaign.get(
                        "required_approval"
                    ) is True
                )
                else campaign_status.title()
            )


            # =================================================
            # CAMPAIGN CARD
            # =================================================

            with st.container(border=True):

                # -------------------------------------------------
                # Campaign Header
                # -------------------------------------------------

                header_col1, header_col2, header_col3 = st.columns(
                    [5, 2, 1.5]
                )

                with header_col1:

                    st.markdown(
                        f"**Campaign #{campaign_id}**"
                    )

                    st.caption(
                        f"{created_date}"
                    )

                with header_col2:

                    st.markdown(
                        f"**● {display_status}**"
                    )

                with header_col3:

                    st.markdown(
                        """
                        <style>
                        div[data-testid="stButton"] > button[kind="secondary"] {
                            background-color: #22c55e;
                            color: white;
                            border: 1px solid #22c55e;
                        }

                        div[data-testid="stButton"] > button[kind="secondary"]:hover {
                            background-color: #16a34a;
                            color: white;
                            border-color: #16a34a;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        "View →",
                        key=f"view_campaign_{campaign_id}",
                        use_container_width=True
                    ):
                        st.session_state[
                            "selected_campaign_id"
                        ] = campaign_id

                        st.switch_page(
                            "Pages/Campaign_Detail.py"
                        )

                # -------------------------------------------------
                # Campaign Title
                # -------------------------------------------------

                st.markdown(
                    f"**{campaign_title}**"
                )

                # -------------------------------------------------
                # Last Action / Next Action
                # -------------------------------------------------

                action_col1, action_col2 = st.columns(2)

                with action_col1:

                    st.caption("Last action")

                    st.write(
                        last_action
                    )

                with action_col2:

                    st.caption("Next action")

                    st.write(
                        next_action
                    )

                # -------------------------------------------------
                # Campaign Information
                # -------------------------------------------------

                st.divider()

                info_col1, info_col2 = st.columns(2)

                with info_col1:

                    st.caption("Channel")

                    st.write(
                        format_channel(channel)
                    )

                with info_col2:

                    st.caption("Priority")

                    st.write(
                        str(priority).title()
                    )


                # ---------------------------------------------
                # Main details
                # ---------------------------------------------

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.caption("Campaign Type")
                    st.write(campaign_type)

                with col2:

                    st.caption("Message Type")
                    st.write(message_type)

                with col3:

                    st.caption("Channel")
                    st.write(channel)

                with col4:

                    st.caption("Priority")
                    st.write(priority)


                # -------------------------------------------------
                # DRAFT
                # -------------------------------------------------

                if campaign_status == "draft":

                    action_col1, action_col2, action_col3 = (
                        st.columns(3)
                    )


                    # ---------------------------------------------
                    # Approve
                    # ---------------------------------------------

                    with action_col1:

                        if st.button(
                            "✅ Approve Campaign",
                            key=f"approve_{campaign_id}",
                            type="primary",
                            use_container_width=True,
                        ):

                            try:

                                CampaignService.approve(
                                    campaign_id=campaign_id,
                                    approved_by="Naresh",
                                    reason=(
                                        "Approved from "
                                        "Streamlit."
                                    ),
                                )

                                st.success(
                                    f"Campaign #{campaign_id} approved."
                                )

                                st.rerun()

                            except Exception as exc:

                                st.error(
                                    f"Approval failed: {exc}"
                                )


                    # ---------------------------------------------
                    # Reject
                    # ---------------------------------------------

                    with action_col2:

                        if st.button(
                            "❌ Reject Campaign",
                            key=f"reject_{campaign_id}",
                            use_container_width=True,
                        ):

                            try:

                                CampaignService.reject(
                                    campaign_id=campaign_id,
                                    rejected_by="Naresh",
                                    reason=(
                                        "Rejected from "
                                        "Streamlit."
                                    ),
                                )

                                st.warning(
                                    f"Campaign #{campaign_id} rejected."
                                )

                                st.rerun()

                            except Exception as exc:

                                st.error(
                                    f"Rejection failed: {exc}"
                                )


                    # ---------------------------------------------
                    # Edit
                    # ---------------------------------------------

                    with action_col3:

                        if st.button(
                            "✏️ Edit Campaign",
                            key=f"edit_{campaign_id}",
                            use_container_width=True,
                        ):

                            st.session_state[
                                f"editing_{campaign_id}"
                            ] = True


                    # ---------------------------------------------
                    # Edit form
                    # ---------------------------------------------

                    if st.session_state.get(
                        f"editing_{campaign_id}",
                        False,
                    ):

                        st.markdown("#### Edit Campaign")

                        with st.form(
                            key=f"edit_form_{campaign_id}"
                        ):

                            edit_col1, edit_col2 = (
                                st.columns(2)
                            )

                            with edit_col1:

                                edit_campaign_type = (
                                    st.text_input(
                                        "Campaign Type",
                                        value=str(
                                            campaign_type
                                        ),
                                    )
                                )

                                edit_message_type = (
                                    st.text_input(
                                        "Message Type",
                                        value=str(
                                            message_type
                                        ),
                                    )
                                )

                                edit_subject = (
                                    st.text_input(
                                        "Subject",
                                        value=str(
                                            subject
                                        ),
                                    )
                                )

                            with edit_col2:

                                edit_channel = (
                                    st.selectbox(
                                        "Channel",
                                        [
                                            "email",
                                            "whatsapp",
                                            "contact_form",
                                            "linkedin",
                                            "phone",
                                            "no_channel",
                                        ],
                                        index=(
                                            [
                                                "email",
                                                "whatsapp",
                                                "contact_form",
                                                "linkedin",
                                                "phone",
                                                "no_channel",
                                            ].index(
                                                channel
                                            )
                                            if channel
                                            in [
                                                "email",
                                                "whatsapp",
                                                "contact_form",
                                                "linkedin",
                                                "phone",
                                                "no_channel",
                                            ]
                                            else 0
                                        ),
                                    )
                                )

                                edit_priority = (
                                    st.selectbox(
                                        "Priority",
                                        [
                                            "high",
                                            "medium",
                                            "low",
                                        ],
                                        index=(
                                            [
                                                "high",
                                                "medium",
                                                "low",
                                            ].index(
                                                priority
                                            )
                                            if priority
                                            in [
                                                "high",
                                                "medium",
                                                "low",
                                            ]
                                            else 1
                                        ),
                                    )
                                )

                            edit_message = st.text_area(
                                "Message",
                                value=str(message),
                                height=180,
                            )


                            save_col1, save_col2 = (
                                st.columns(2)
                            )


                            with save_col1:

                                save_changes = (
                                    st.form_submit_button(
                                        "Save Changes",
                                        type="primary",
                                        use_container_width=True,
                                    )
                                )


                            with save_col2:

                                cancel_edit = (
                                    st.form_submit_button(
                                        "Cancel",
                                        use_container_width=True,
                                    )
                                )


                            if save_changes:

                                try:

                                    CampaignService.update(
                                        campaign_id,
                                        {
                                            "campaign_type": (
                                                edit_campaign_type
                                            ),
                                            "message_type": (
                                                edit_message_type
                                            ),
                                            "channel": (
                                                edit_channel
                                            ),
                                            "subject": (
                                                edit_subject
                                            ),
                                            "message": (
                                                edit_message
                                            ),
                                            "priority": (
                                                edit_priority
                                            ),
                                        },
                                    )

                                    st.success(
                                        "Campaign updated."
                                    )

                                    st.session_state[
                                        f"editing_{campaign_id}"
                                    ] = False

                                    st.rerun()

                                except Exception as exc:

                                    st.error(
                                        f"Update failed: {exc}"
                                    )


                            if cancel_edit:

                                st.session_state[
                                    f"editing_{campaign_id}"
                                ] = False

                                st.rerun()


                # =================================================
                # APPROVED
                # =================================================

                elif campaign_status == "approved":

                    action_col1, action_col2 = (
                        st.columns(2)
                    )


                    # ---------------------------------------------
                    # Send
                    # ---------------------------------------------

                    with action_col1:

                        if st.button(
                            "Send Campaign",
                            key=f"send_{campaign_id}",
                            type="primary",
                            use_container_width=True,
                        ):

                            try:

                                CampaignService.send(
                                    campaign_id
                                )

                                st.success(
                                    f"Campaign #{campaign_id} sent."
                                )

                                st.rerun()

                            except Exception as exc:

                                st.error(
                                    f"Send failed: {exc}"
                                )


                    # ---------------------------------------------
                    # Close
                    # ---------------------------------------------

                    with action_col2:

                        if st.button(
                            "Close Campaign",
                            key=f"close_{campaign_id}",
                            use_container_width=True,
                        ):
                            st.session_state[
                                f"confirm_close_{campaign_id}"
                            ] = True


                    if st.session_state.get(
                        f"confirm_close_{campaign_id}",
                        False,
                    ):

                        st.warning(
                            "Closing this campaign will mark it as completed. "
                            "Are you sure?"
                        )

                        confirm_col1, confirm_col2 = st.columns(2)

                        with confirm_col1:

                            if st.button(
                                "Cancel",
                                key=f"cancel_close_{campaign_id}",
                                use_container_width=True,
                            ):
                                st.session_state[
                                    f"confirm_close_{campaign_id}"
                                ] = False

                                st.rerun()

                        with confirm_col2:

                            if st.button(
                                "Confirm Close",
                                key=f"confirm_close_action_{campaign_id}",
                                type="primary",
                                use_container_width=True,
                            ):

                                try:

                                    CampaignService.close(
                                        campaign_id
                                    )

                                    st.success(
                                        f"Campaign #{campaign_id} closed."
                                    )

                                    st.session_state[
                                        f"confirm_close_{campaign_id}"
                                    ] = False

                                    st.rerun()

                                except Exception as exc:

                                    st.error(
                                        f"Close failed: {exc}"
                                    )

                # =================================================
                # SENT / REPLIED / CLOSED
                # =================================================

                elif campaign_status in {
                    "sent",
                    "replied",
                    "closed"
                }:

                    # -------------------------------------------------
                    # Actions
                    # -------------------------------------------------

                    if campaign_status in {
                        "sent",
                        "replied",
                    }:

                        st.divider()

                        action_col1, action_col2 = st.columns(2)

                        with action_col1:

                            if st.button(
                                "Close Campaign",
                                key=f"close_sent_replied_{campaign_id}",
                                use_container_width=True,
                            ):
                                st.session_state[
                                    f"confirm_close_{campaign_id}"
                                ] = True

                        with action_col2:

                            if campaign_status == "replied":

                                st.button(
                                    "Reply",
                                    key=f"reply_{campaign_id}",
                                    use_container_width=True,
                                    disabled=True,
                                    help=(
                                        "AI-assisted reply workflow "
                                        "will be added later."
                                    ),
                                )

                        # -------------------------------------------------
                        # Close Confirmation
                        # -------------------------------------------------

                        if st.session_state.get(
                            f"confirm_close_{campaign_id}",
                            False,
                        ):

                            st.warning(
                                "Closing this campaign will mark it as "
                                "completed. Are you sure?"
                            )

                            confirm_col1, confirm_col2 = st.columns(2)

                            with confirm_col1:

                                if st.button(
                                    "Cancel",
                                    key=f"cancel_close_sent_replied_{campaign_id}",
                                    use_container_width=True,
                                ):

                                    st.session_state[
                                        f"confirm_close_{campaign_id}"
                                    ] = False

                                    st.rerun()

                            with confirm_col2:

                                if st.button(
                                    "Confirm Close",
                                    key=f"confirm_close_action_sent_replied_{campaign_id}",
                                    type="primary",
                                    use_container_width=True,
                                ):

                                    try:

                                        CampaignService.close(
                                            campaign_id
                                        )

                                        st.success(
                                            f"Campaign #{campaign_id} closed."
                                        )

                                        st.session_state[
                                            f"confirm_close_{campaign_id}"
                                        ] = False

                                        st.rerun()

                                    except Exception as exc:

                                        st.error(
                                            f"Close failed: {exc}"
                                        )

                # -------------------------------------------------
                # Closed Campaign Actions
                # -------------------------------------------------

                if campaign_status == "closed":

                    st.divider()

                    closed_col1, closed_col2 = st.columns(2)

                    with closed_col1:

                        if st.button(
                            "🔄 Create New Campaign",
                            key=f"recreate_campaign_{campaign_id}",
                            use_container_width=True,
                        ):
                            st.session_state[
                                f"confirm_recreate_{campaign_id}"
                            ] = True

                            st.rerun()

                    with closed_col2:

                        if st.button(
                            "🗑 Delete Campaign",
                            key=f"delete_campaign_{campaign_id}",
                            use_container_width=True,
                        ):
                            st.session_state[
                                f"confirm_delete_{campaign_id}"
                            ] = True

                            st.rerun()

                    if st.session_state.get(
                        f"confirm_delete_{campaign_id}",
                        False,
                    ):

                        st.warning(
                            f"Delete Campaign #{campaign_id}? "
                            "This action cannot be undone."
                        )

                        delete_col1, delete_col2 = st.columns(2)

                        with delete_col1:

                            if st.button(
                                "No, Keep Campaign",
                                key=f"cancel_delete_{campaign_id}",
                                use_container_width=True,
                            ):
                                st.session_state[
                                    f"confirm_delete_{campaign_id}"
                                ] = False

                                st.rerun()

                        with delete_col2:

                            if st.button(
                                "Yes, Delete Campaign",
                                key=f"confirm_delete_action_{campaign_id}",
                                type="primary",
                                use_container_width=True,
                            ):

                                try:

                                    CampaignService.delete(
                                        campaign_id
                                    )

                                    st.success(
                                        f"Campaign #{campaign_id} deleted."
                                    )

                                    st.session_state[
                                        f"confirm_delete_{campaign_id}"
                                    ] = False

                                    st.rerun()

                                except Exception as exc:

                                    st.error(
                                        f"Delete failed: {exc}"
                                    )


                    if st.session_state.get(
                        f"confirm_recreate_{campaign_id}",
                        False,
                    ):

                        st.warning(
                            "Create a new campaign for this college?"
                        )

                        confirm_col1, confirm_col2 = st.columns(2)

                        with confirm_col1:

                            if st.button(
                                "No",
                                key=f"cancel_recreate_{campaign_id}",
                                use_container_width=True,
                            ):
                                st.session_state[
                                    f"confirm_recreate_{campaign_id}"
                                ] = False

                                st.rerun()

                        with confirm_col2:

                            if st.button(
                                "Yes, Create Draft",
                                key=f"confirm_recreate_action_{campaign_id}",
                                type="primary",
                                use_container_width=True,
                            ):
                                # Actual agent-based new draft creation
                                # will be connected in the next step.

                                try:

                                    result = CampaignService.recreate(
                                        campaign_id
                                    )

                                    st.session_state[
                                        f"confirm_recreate_{campaign_id}"
                                    ] = False

                                    st.success(
                                        f"New draft Campaign #{result['new_campaign_id']} "
                                        f"created successfully."
                                    )

                                    st.rerun()

                                except Exception as exc:

                                    st.error(
                                        f"Failed to create new draft: {exc}"
                                    )


                # =================================================
                # REJECTED / CLOSED
                # =================================================

                else:

                    st.caption(
                        "No actions available for this campaign status."
                    )