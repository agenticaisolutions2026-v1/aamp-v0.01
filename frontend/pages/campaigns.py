import streamlit as st
import pandas as pd

# ------------------------------------------------
# Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="Campaigns",
    page_icon="📢",
    layout="wide"
)

# ------------------------------------------------
# Page Title
# ------------------------------------------------
st.title("📢 Campaigns")
st.write("Create and Manage Outreach Campaigns")

# ------------------------------------------------
# Summary Cards
# ------------------------------------------------
st.subheader("📈 Campaign Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background-color:#E8F5E9;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>📢 Active Campaigns</h4>
        <h2 style="color:#2E7D32;">12</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background-color:#E3F2FD;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>📧 Emails Sent</h4>
        <h2 style="color:#1565C0;">250</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background-color:#F3E5F5;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>✅ Approved</h4>
        <h2 style="color:#6A1B9A;">9</h2>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ------------------------------------------------
# Campaign Form
# ------------------------------------------------
st.subheader("📝 Create Campaign")

campaign_name = st.text_input("Campaign Name")

course = st.selectbox(
    "Target Department",
    [
        "AI & ML",
        "Computer Science",
        "ECE",
        "Data Science"
    ]
)

campaign_type = st.selectbox(
    "Campaign Type",
    [
        "Workshop",
        "Internship",
        "Course Promotion",
        "Placement Drive"
    ]
)

description = st.text_area("Campaign Description")

col1, col2, col3 = st.columns(3)

with col1:
    st.button("🤖 Generate Proposal")

with col2:
    st.button("✅ Approve")

with col3:
    st.button("📧 Send Email")

st.divider()

# ------------------------------------------------
# Campaign Status Table
# ------------------------------------------------
st.subheader("📋 Campaign Status")

df = pd.DataFrame({
    "Campaign": [
        "AI Workshop",
        "Placement Drive",
        "Internship Program"
    ],
    "Department": [
        "AI & ML",
        "Computer Science",
        "ECE"
    ],
    "Status": [
        "Proposal Generated",
        "Approved",
        "Email Sent"
    ],
    "Approval": [
        "Pending",
        "Approved",
        "Approved"
    ]
})

st.dataframe(df, use_container_width=True)

st.success("✅ Campaign data loaded successfully.")