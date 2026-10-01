import pandas as pd
import streamlit as st

from services.college_service import CollegeService
from components.common import init_page
import html
from services.api_client import post


init_page("Colleges")

st.title("Colleges")
st.caption(
    "Monitor college intelligence, lead qualification, and campaign operations."
)


# =========================================================
# Load real data
# =========================================================

try:
    with st.spinner("Loading colleges..."):
        response = CollegeService.get_overview()

    results = response.get("results", [])

except Exception as exc:
    st.error(f"Failed to load colleges: {exc}")
    st.stop()


# =========================================================
# Summary metrics
# =========================================================

total_colleges = len(results)

qualified = 0
needs_review = 0
high_priority = 0
operations = 0

for item in results:

    lead = item.get("lead") or {}

    qualification = (
        lead.get("qualification") or ""
    ).lower()

    priority = (
        lead.get("priority") or ""
    ).lower()

    operation_status = item.get(
        "operation_status",
        "No Operation",
    )

    if qualification == "qualified":
        qualified += 1

    if qualification == "needs_review":
        needs_review += 1

    if priority == "high":
        high_priority += 1

    if operation_status != "No Operation":
        operations += 1


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Colleges", total_colleges)

with col2:
    st.metric("Qualified", qualified)

with col3:
    st.metric("High Priority", high_priority)

with col4:
    st.metric("With Operations", operations)


st.divider()

# ------------------------------------------- 
# Two clickable buttons
# -------------------------------------------
st.markdown("### Lead Review")

review_col1, review_col2 = st.columns(2)

with review_col1:

    if st.button(
        "Needs Review Colleges",
        use_container_width=True,
        type="primary",
    ):
        st.session_state["college_review_mode"] = "needs_review"


with review_col2:

    if st.button(
        "Low Priority Colleges",
        use_container_width=True,
    ):
        st.session_state["college_review_mode"] = "low_priority"

st.divider()

# =========================================================
# Lead Review Panel(needs_review & low_priority)
# =========================================================

review_mode = st.session_state.get(
    "college_review_mode"
)


if review_mode == "needs_review":

    needs_review_colleges = [
        college
        for college in results
        if str(
            (college.get("lead") or {}).get(
                "qualification",
                ""
            )
        ).lower() == "needs_review"
    ]

    st.markdown(
        f"### Needs Review Colleges "
        f"({len(needs_review_colleges)})"
    )

    st.caption(
        "These leads require a human decision before "
        "campaign generation."
    )

    if not needs_review_colleges:

        st.success(
            "There are no colleges currently waiting "
            "for lead review."
        )

    else:

        for college in needs_review_colleges:

            lead = college.get("lead") or {}
            college_info = college.get("college") or {}

            college_id = college_info.get("id")

            college_name = (
                college_info.get("name")
                or "Unknown College"
            )

            city = college_info.get("city") or "—"
            state = college_info.get("state") or "—"

            lead_score = lead.get(
                "lead_score",
                "—",
            )

            priority = lead.get(
                "priority",
                "—",
            )

            contact_role = lead.get(
                "contact_role",
                "—",
            )

            reason = lead.get(
                "reason",
                "No qualification reason available.",
            )

            with st.container(border=True):

                st.markdown(
                    f"**{college_name}**"
                )

                st.caption(
                    f"{city}, {state}"
                )

                info1, info2, info3, info4 = st.columns(4)

                with info1:
                    st.caption("Lead Score")
                    st.write(f"**{lead_score}**")

                with info2:
                    st.caption("Qualification")
                    st.write("**Needs Review**")

                with info3:
                    st.caption("Priority")
                    st.write(f"**{str(priority).title()}**")

                with info4:
                    st.caption("Contact Role")
                    st.write(f"**{contact_role}**")

                st.markdown(
                    "**Qualification Reason**"
                )

                st.write(reason)

                st.markdown("---")

                approve_col, reject_col, close_col = (
                    st.columns(3)
                )

                # -----------------------------------------
                # Approve
                # -----------------------------------------

                with approve_col:

                    if st.button(
                        "Approve Lead",
                        key=f"approve_lead_{college_id}",
                        type="primary",
                        use_container_width=True,
                    ):

                        try:

                            response = post(
                                f"/colleges/{college_id}/lead/approve",
                                {},
                            )

                            st.success(
                                "Lead approved and campaign "
                                "draft created."
                            )

                            st.session_state[
                                "college_review_mode"
                            ] = None

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Unable to approve lead."
                            )

                            st.caption(str(exc))

                # -----------------------------------------
                # Reject
                # -----------------------------------------

                with reject_col:

                    if st.button(
                        "Reject Lead",
                        key=f"reject_lead_{college_id}",
                        use_container_width=True,
                    ):

                        try:

                            response = post(
                                f"/colleges/{college_id}/lead/reject",
                                {},
                            )

                            st.success(
                                "Lead rejected and removed "
                                "from the campaign workflow."
                            )

                            st.session_state[
                                "college_review_mode"
                            ] = None

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Unable to reject lead."
                            )

                            st.caption(str(exc))

                # -----------------------------------------
                # Close
                # -----------------------------------------

                with close_col:

                    if st.button(
                        "Close Review",
                        key=f"close_review_{college_id}",
                        use_container_width=True,
                    ):
                        st.session_state["college_review_mode"] = None
                        st.rerun()


elif review_mode == "low_priority":

    low_priority_colleges = [
        college
        for college in results
        if str(
            (college.get("lead") or {}).get(
                "qualification",
                ""
            )
        ).lower() == "low_priority"
    ]

    st.markdown(
        f"### Low Priority Colleges "
        f"({len(low_priority_colleges)})"
    )

    st.caption(
        "These leads are stopped and do not enter "
        "automatic campaign generation."
    )

    if not low_priority_colleges:

        st.info(
            "There are no low-priority colleges."
        )

    else:

        for college in low_priority_colleges:

            lead = college.get("lead") or {}
            college_info = college.get("college") or {}

            college_name = (
                college_info.get("name")
                or "Unknown College"
            )

            city = college_info.get("city") or "—"
            state = college_info.get("state") or "—"

            with st.container(border=True):

                st.markdown(
                    f"**{college_name}**"
                )

                st.caption(
                    f"{city}, {state}"
                )

                info1, info2, info3 = st.columns(3)

                with info1:
                    st.caption("Lead Score")
                    st.write(
                        f"**{lead.get('lead_score', '—')}**"
                    )

                with info2:
                    st.caption("Qualification")
                    st.write("**Low Priority**")

                with info3:
                    st.caption("Priority")
                    st.write(
                        f"**{str(lead.get('priority', '—')).title()}**"
                    )

                if lead.get("reason"):

                    st.markdown(
                        "**Qualification Reason**"
                    )

                    st.write(
                        lead.get("reason")
                    )

        if st.button(
            "Close Review",
            key="close_low_priority",
        ):

            st.session_state[
                "college_review_mode"
            ] = None

            st.rerun()


# =========================================================
# Filters
# =========================================================

st.subheader("College Operations")

filter_col1, filter_col2 = st.columns([2,3])

with filter_col1:
    state_options = [
        "Select State",
        "Andhra Pradesh",
        "Telangana",
        "Tamil Nadu",
        "Karnataka",
        "Kerala",
        "Maharashtra",
        "Odisha",
        "West Bengal",
        "Delhi",
        "Gujarat",
        "Rajasthan",
        "Madhya Pradesh",
        "Uttar Pradesh",
        "Bihar",
        "Jharkhand",
        "Chhattisgarh",
        "Punjab",
        "Haryana",
    ]

    selected_state = st.selectbox(
        "State",
        state_options,
    )

with filter_col2:
    search_college = st.text_input(
        "Search college...",
        placeholder="Enter college name",
    )


filter_col3, filter_col4,  filter_col5, filter_col6 = st.columns(
    [1.5, 1.5, 1.5, 1.5]
)

with filter_col3:
    qualification_filter = st.selectbox(
        "Qualification",
        ["All", "Qualified", "Needs Review", "Disqualified"],
    )

with filter_col4:
    priority_filter = st.selectbox(
        "Lead Priority",
        ["All", "High", "Medium", "Low"],
    )
with filter_col5:
    operation_filter = st.selectbox(
        "Operation",
        [
            "All",
            "No operation",
            "draft",
            "approved",
            "rejected",
            "sent",
            "replied",
            "closed",
        ],
    )
with filter_col6:
    campaign_status_filter = st.selectbox(
        "Campaign Status",
        [
            "All",
            "Draft",
            "Approved",
            "Rejected",
            "Sent",
            "Replied",
            "Closed",
            "Opted_Out",
            "Completed"
        ],
    )


# =========================================================
# Apply filters
# =========================================================

filtered_results = []

for item in results:

    college = item.get("college") or {}
    lead = item.get("lead") or {}

    name = college.get("name") or ""
    state = college.get("state") or ""

    qualification = (
        lead.get("qualification") or ""
    )

    lead_priority = (
        lead.get("priority") or ""
    )

    operation_status = item.get(
        "operation_status",
        "No Operation",
    )

    campaign_status = item.get(
        "campaign_status",
        "",
    )

    # State
    if selected_state != "Select State":

        if state.lower() != selected_state.lower():
            continue

    # Search
    if search_college and search_college.lower() not in name.lower():
        continue

    # Qualification
    if qualification_filter != "All":

        expected = qualification_filter.lower().replace(
            " ",
            "_",
        )

        if qualification.lower() != expected:
            continue

    # Lead priority
    if priority_filter != "All":

        if lead_priority.lower() != priority_filter.lower():
            continue

    # Operation status
    if operation_filter != "All":

        if operation_status.lower() != operation_filter.lower():
            continue

    # Campaign status
    if campaign_status_filter != "All":

        if (campaign_status or "").lower() != campaign_status_filter.lower():
            continue

    filtered_results.append(item)


st.caption(
    f"Showing {len(filtered_results)} of {total_colleges} colleges"
)


# =========================================================
# Build table
# =========================================================

table_data = []

for item in filtered_results:

    college = item.get("college") or {}
    lead = item.get("lead") or {}
    campaign = item.get("campaign") or {}

    city = college.get("city") or "—"
    state = college.get("state") or "—"

    location = (
        f"{city}, {state}"
        if city != "—" and state != "—"
        else city if city != "—"
        else state
    )

    qualification = lead.get(
        "qualification"
    )

    lead_score = lead.get(
        "lead_score"
    )

    lead_priority = lead.get(
        "priority"
    )

    campaign_priority = campaign.get(
        "priority"
    )

    campaign_status = campaign.get(
        "status"
    )

    operation_status = item.get(
        "operation_status",
        "No Operation",
    )

    table_data.append(
        {
            "S.No.": len(table_data) + 1,
            "College": college.get(
                "name",
                "Unknown College",
            ),
            "Location": location,
            "Qualification": (
                qualification.replace("_", " ").title()
                if qualification
                else "—"
            ),
            "Lead Score": (
                lead_score
                if lead_score is not None
                else "—"
            ),
            "Lead Priority": (
                lead_priority.title()
                if lead_priority
                else "—"
            ),
            "Campaign Priority": (
                campaign_priority.title()
                if campaign_priority
                else "—"
            ),
            "Operation Status": operation_status,
            "Campaign Status": (
                campaign_status.title()
                if campaign_status
                else "—"
            ),
        }
    )


# =========================================================
# Display table
# =========================================================

if not table_data:

    st.info(
        "No colleges match the selected filters."
    )

else:

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "S.No.": st.column_config.NumberColumn(
                "S.No.",
                width="small",
            ),
            "College": st.column_config.TextColumn(
                "College",
                width="large",
            ),
            "Location": st.column_config.TextColumn(
                "Location",
                width="medium",
            ),
            "Qualification": st.column_config.TextColumn(
                "Qualification",
                width="medium",
            ),
            "Lead Score": st.column_config.NumberColumn(
                "Lead Score",
                format="%.0f",
            ),
            "Lead Priority": st.column_config.TextColumn(
                "Lead Priority",
            ),
            "Campaign Priority": st.column_config.TextColumn(
                "Campaign Priority",
            ),
            "Operation Status": st.column_config.TextColumn(
                "Operation Status",
            ),
            "Campaign Status": st.column_config.TextColumn(
                "Campaign Status",
            ),
        },
    )