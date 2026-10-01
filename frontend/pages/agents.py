import streamlit as st
from services.agent_service import AgentService
from components.common import init_page
import pandas as pd
from datetime import datetime

init_page("Agents")
st.title("Agents")
st.write("Agents Management")
try:
    with st.spinner("Loading agents..."):
        agents = AgentService.get_all()
        if not agents:
            st.warning("No agents found.")
        else:
            st.success(f"Loaded {len(agents)} agents successfully.")
            agent_rows = []

            for agent in agents:

                start_time = agent.get("start_time")
                end_time = agent.get("end_time")

                if start_time:
                    start_time = datetime.fromisoformat(
                        str(start_time).replace("Z", "+00:00")
                    ).strftime("%d %b %Y %H:%M:%S")

                if end_time:
                    end_time = datetime.fromisoformat(
                        str(end_time).replace("Z", "+00:00")
                    ).strftime("%d %b %Y %H:%M:%S")

                agent_rows.append({
                    "Agent": agent.get("name", "—"),
                    "Status": agent.get("status", "—"),
                    "Start Time": start_time or "—",
                    "End Time": end_time or "—",
                    "Duration": agent.get("duration", "—"),
                })
            st.markdown("""
                <style>
                .date-label {
                    font-weight: 600;
                    color: var(--text-color) !important;
                }
                </style>
                """, unsafe_allow_html=True)

            st.markdown(
                f'<div class="date-label">Date: {datetime.now().strftime("%d %b %Y")}</div>',
                unsafe_allow_html=True
            )
            df = pd.DataFrame(agent_rows)

            def style_agent_row(row):
                status = row["Status"]

                if status == "Completed":
                    return ["background-color: #183B2A; color: #E8F5E9"] * len(row)

                elif status == "Running":
                    return ["background-color: #17344D; color: #E3F2FD"] * len(row)

                elif status == "Waiting":
                    return ["background-color: #4A3B16; color: #FFF8E1"] * len(row)

                else:
                    return ["background-color: #1C1F26; color: #D1D5DB"] * len(row)


            styled_df = df.style.apply(style_agent_row, axis=1)

            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
            )
             
except Exception as e:
    st.error(f"❌ Failed to load agents: {e}")

# -------------------------------------------------------
# Naresh - Newly added section for executing agents
# -------------------------------------------------------
st.subheader("Run Agent Workflow")

user_query = st.text_input(
    "Enter your query",
    placeholder="Example: Find AI/ML colleges in Andhra Pradesh"
)

if st.button("Execute Agent"):
    if not user_query:
        st.warning("Please enter a query.")
    else:
        try:
            with st.spinner("Executing agent..."):
                result = AgentService.execute({
                    "user_query": user_query
                })

            st.success("Agent executed successfully.")

            st.write("**Selected Agent:**", result["selected_agent"])
            st.write("**Status:**", result["status"].title())

            workflow_result = result.get("result") or {}

            if isinstance(workflow_result, dict):

                st.subheader("Workflow Result")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Colleges Processed",
                        workflow_result.get("count", 0),
                    )

                college_results = workflow_result.get("results", [])
                requested_query = workflow_result.get("query", "").lower()

                created_count = sum(
                    1
                    for item in college_results
                    if item.get("action") == "campaign_created"
                )

                skipped_count = sum(
                    1
                    for item in college_results
                    if item.get("action") == "skip"
                )

                review_count = sum(
                    1
                    for item in college_results
                    if item.get("action") in [
                        "human_review",
                        "human_decision",
                    ]
                )

                with col2:
                    st.metric("Campaigns Created", created_count)

                with col3:
                    st.metric("Skipped", skipped_count)

                with col4:
                    st.metric("Human Review", review_count)

                if not college_results:
                    st.info(
                        workflow_result.get(
                            "message",
                            "No information available in the AAMP database for this query.",
                        )
                    )
                else:
                    st.subheader("College Results")

                    for item in college_results:

                        college = item.get("college") or {}
                        lead = item.get("lead") or {}
                        campaign = item.get("campaign") or {}

                        college_name = college.get(
                            "name",
                            "Unknown College",
                        )

                        lead_score = lead.get("lead_score")
                        priority = lead.get("priority")

                        website = college.get("website")
                        email_data = college.get("official_email") or {}
                        phone_data = college.get("official_phone") or {}
                        whatsapp_data = college.get("whatsapp") or {}
                        linkedin_data = college.get("linkedin") or {}
                        contact_form_data = college.get("contact_form") or {}

                        email = email_data.get("value")
                        phone = phone_data.get("value")
                        whatsapp = whatsapp_data.get("value")
                        linkedin = linkedin_data.get("value")
                        contact_form = contact_form_data.get("value")

                        campaign_status = campaign.get(
                            "status",
                            "No Campaign",
                        )

                        st.write(
                            f"• **{college_name}** — "
                            f"Campaign: **{campaign_status}**"
                        )

                        if lead_score is not None:
                            st.caption(
                                f"Lead Score: {lead_score} | "
                                f"Priority: {priority or '—'}"
                            )

                        if "website" in requested_query:
                            if website:
                                st.write(f"Website: {website}")
                            else:
                                st.write("⚠️ Website: No information available")

                        if "email" in requested_query:
                            if email:
                                st.write(f"Email: {email}")
                            else:
                                st.write("⚠️ Email: No information available")

                        if "phone" in requested_query:
                            if phone:
                                st.write(f"Phone: {phone}")
                            else:
                                st.write("⚠️ Phone: No information available")

                        if "whatsapp" in requested_query:
                            if whatsapp:
                                st.write(f"WhatsApp: {whatsapp}")
                            else:
                                st.write("⚠️ WhatsApp: No information available")

                        if "linkedin" in requested_query:
                            if linkedin:
                                st.write(f"LinkedIn: {linkedin}")
                            else:
                                st.write("⚠️ LinkedIn: No information available")

                        if "contact form" in requested_query:
                            if contact_form:
                                st.write("Contact Form: Available")
                            else:
                                st.write("⚠️ Contact Form: No information available")

            else:
                st.write(workflow_result)

            if result.get("error"):
                st.error(
                    f"Workflow Error: {result['error']}"
                )

        except Exception as e:
            st.error(f"❌ Agent execution failed: {e}")