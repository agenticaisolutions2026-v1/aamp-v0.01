import streamlit as st

from services.campaign_service import CampaignService
from components.common import init_page


init_page("Campaigns")

st.title("Campaigns")
st.write("Campaign Management")


try:

    # =========================================================
    # Load campaigns
    # =========================================================

    with st.spinner("Loading campaigns..."):

        campaigns = CampaignService.get_all()

    if not campaigns:

        st.warning("No campaigns found.")

    else:

        st.success(
            f"Loaded {len(campaigns)} campaigns successfully."
        )

        # =====================================================
        # Campaign Cards
        # =====================================================

        for campaign in campaigns:

            campaign_id = campaign.get("id")

            college_name = campaign.get(
                "college_name",
                "Unknown College",
            )

            status = campaign.get(
                "status",
                "Unknown",
            )

            priority = campaign.get(
                "priority",
                "Unknown",
            )

            channel = campaign.get(
                "channel",
                "Unknown",
            )

            subject = campaign.get(
                "subject",
                "",
            )

            message = campaign.get(
                "message",
                "",
            )

            contact_role = campaign.get(
                "contact_role",
                "",
            )

            lead_score = campaign.get(
                "lead_score",
                "",
            )

            tier = campaign.get(
                "tier",
                "",
            )

            required_human_approval = campaign.get(
                "required_human_approval",
                True,
            )

            approval_type = campaign.get(
                "approval_type",
                "",
            )

            approval_status = campaign.get(
                "approval_status",
                "",
            )

            # =================================================
            # Campaign Header
            # =================================================

            with st.expander(
                f"Campaign #{campaign_id} — "
                f"{college_name} — {status}"
            ):

                # =================================================
                # Campaign Information
                # =================================================

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.write("**Priority**")

                    st.write(
                        priority
                    )

                with col2:

                    st.write("**Channel**")

                    st.write(
                        channel
                    )

                with col3:

                    st.write("**Lead Score**")

                    st.write(
                        lead_score
                    )

                with col4:

                    st.write("**Tier**")

                    if tier == "Tier 1":

                        st.success(
                            "🟢 Tier 1"
                        )

                    elif tier == "Tier 2":

                        st.warning(
                            "🟡 Tier 2"
                        )

                    else:

                        st.write(
                            tier or "Not available"
                        )

                # =================================================
                # Approval Information
                # =================================================

                st.divider()

                approval_col1, approval_col2 = (
                    st.columns(2)
                )

                with approval_col1:

                    st.write(
                        "**Approval Type**"
                    )

                    if approval_type == "auto":

                        st.success(
                            "Automatic Approval"
                        )

                    elif approval_type == "human":

                        st.warning(
                            "Human Approval"
                        )

                    else:

                        if (
                            required_human_approval
                        ):

                            st.warning(
                                "Human Approval Required"
                            )

                        else:

                            st.success(
                                "Automatic Approval"
                            )

                with approval_col2:

                    st.write(
                        "**Approval Status**"
                    )

                    if approval_status == "approved":

                        st.success(
                            "✅ Approved"
                        )

                    elif approval_status == "pending":

                        st.warning(
                            "⏳ Pending Approval"
                        )

                    else:

                        st.write(
                            approval_status
                            or status
                        )

                # =================================================
                # Contact Role
                # =================================================

                st.write("**Contact Role**")

                st.write(
                    contact_role
                    or "Not specified"
                )

                # =================================================
                # Subject
                # =================================================

                st.write("**Subject**")

                st.write(
                    subject
                    or "No subject"
                )

                # =================================================
                # Message
                # =================================================

                st.write("**Message**")

                st.text_area(
                    "Campaign Message",
                    message,
                    height=220,
                    key=f"message_{campaign_id}",
                )

                # =================================================
                # Current Status
                # =================================================

                st.write(
                    f"**Current Status:** `{status}`"
                )

                # =================================================
                # Tier 2 — Human Approval
                # =================================================

                if (
                    status == "Draft"
                    and required_human_approval
                ):

                    st.warning(
                        "Human approval is required before "
                        "this campaign can enter the outreach queue."
                    )

                    approve_col, reject_col = (
                        st.columns(2)
                    )

                    # ---------------------------------------------
                    # Approve
                    # ---------------------------------------------

                    with approve_col:

                        if st.button(
                            "✅ Approve Campaign",
                            key=f"approve_{campaign_id}",
                            use_container_width=True,
                        ):

                            try:

                                with st.spinner(
                                    "Approving campaign..."
                                ):

                                    result = (
                                        CampaignService.approve(
                                            campaign_id
                                        )
                                    )

                                st.success(
                                    "Campaign approved and "
                                    "outreach queued successfully."
                                )

                                st.json(
                                    result
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    "Failed to approve "
                                    f"campaign: {e}"
                                )

                    # ---------------------------------------------
                    # Reject
                    # ---------------------------------------------

                    with reject_col:

                        if st.button(
                            "❌ Reject Campaign",
                            key=f"reject_{campaign_id}",
                            use_container_width=True,
                        ):

                            try:

                                with st.spinner(
                                    "Rejecting campaign..."
                                ):

                                    result = (
                                        CampaignService.reject(
                                            campaign_id
                                        )
                                    )

                                st.warning(
                                    "Campaign rejected successfully."
                                )

                                st.json(
                                    result
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    "Failed to reject "
                                    f"campaign: {e}"
                                )

                # =================================================
                # Tier 1 — Automatic Approval
                # =================================================

                elif (
                    status == "Approved"
                    and approval_type == "auto"
                ):

                    st.success(
                        "🟢 Tier 1 campaign automatically "
                        "approved."
                    )

                    st.info(
                        "📤 Outreach has been queued "
                        "for processing."
                    )

                # =================================================
                # Approved — Human or Existing
                # =================================================

                elif status == "Approved":

                    st.success(
                        "✅ Campaign approved. "
                        "Outreach has been queued."
                    )

                # =================================================
                # Rejected
                # =================================================

                elif status == "Rejected":

                    st.error(
                        "❌ Campaign rejected. "
                        "No outreach will be performed."
                    )

                # =================================================
                # Sent
                # =================================================

                elif status == "Sent":

                    st.info(
                        "📤 Campaign marked as sent."
                    )

                # =================================================
                # Other Status
                # =================================================

                else:

                    st.info(
                        f"Campaign status: {status}"
                    )

        # =========================================================
        # Campaign Overview
        # =========================================================

        st.divider()

        st.subheader(
            "Campaign Overview"
        )

        st.dataframe(
            campaigns,
            use_container_width=True,
            hide_index=True,
        )


except Exception as e:

    st.error(
        f"❌ Failed to load campaigns: {e}"
    )