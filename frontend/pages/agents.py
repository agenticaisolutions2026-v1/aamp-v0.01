import streamlit as st
import pandas as pd

# ------------------------------------------------
# Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="AI Agents",
    page_icon="🤖",
    layout="wide"
)

# ------------------------------------------------
# Page Title
# ------------------------------------------------
st.title("🤖 AI Agents")
st.write("Monitor and Manage AI Agents")

# ------------------------------------------------
# Summary Cards
# ------------------------------------------------
st.subheader("📈 AI Agent Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background-color:#E3F2FD;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🤖 Total Agents</h4>
        <h2 style="color:#1565C0;">8</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background-color:#E8F5E9;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🟢 Active Agents</h4>
        <h2 style="color:#2E7D32;">7</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background-color:#FFF8E1;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🟡 Idle Agents</h4>
        <h2 style="color:#F57F17;">1</h2>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ------------------------------------------------
# AI Agent Status
# ------------------------------------------------
st.subheader("📋 Agent Status")

agents = pd.DataFrame({
    "Agent Name": [
        "Supervisor Agent",
        "Research Agent",
        "Website Agent",
        "Analysis Agent",
        "Proposal Agent",
        "Campaign Agent",
        "Response Tracking Agent",
        "Analytics Agent"
    ],
    "Status": [
        "🟢 Active",
        "🟢 Active",
        "🟢 Active",
        "🟢 Active",
        "🟢 Active",
        "🟢 Active",
        "🟡 Idle",
        "🟢 Active"
    ],
    "Current Task": [
        "Managing Workflow",
        "Finding Colleges",
        "Analyzing Websites",
        "Identifying Departments",
        "Generating Proposal",
        "Sending Emails",
        "Waiting for Response",
        "Generating Reports"
    ]
})

st.dataframe(agents, use_container_width=True)

st.divider()

# ------------------------------------------------
# System Health
# ------------------------------------------------
st.subheader("💚 System Health")

st.progress(90)

st.success("Overall AI Agent Health: 90%")

st.info("All critical AI agents are running successfully.")