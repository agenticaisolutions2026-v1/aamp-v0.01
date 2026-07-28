import streamlit as st

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

st.title("🏠 Dashboard")
st.write("Welcome to the Agentic AI Marketing Platform (AAMP).")

# Summary Cards
col1, col2, col3, col4 = st.columns(4)

st.subheader("📊 Today's Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="
        background-color:#E3F2FD;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🏫 Organizations</h4>
        <h2 style="color:#1565C0;">250</h2>
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
        <h4>📢 Campaigns</h4>
        <h2 style="color:#2E7D32;">12</h2>
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
        <h4>🤖 AI Agents</h4>
        <h2 style="color:#6A1B9A;">8</h2>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="
        background-color:#FFF8E1;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>📅 Meetings</h4>
        <h2 style="color:#F57F17;">15</h2>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Workflow
st.subheader("🚀 Campaign Workflow")

workflow = [
    "1️⃣ Select State",
    "2️⃣ Find Colleges",
    "3️⃣ Analyze Official Website",
    "4️⃣ Identify AI / ML / CS / ECE Departments",
    "5️⃣ Generate Personalized Proposal",
    "6️⃣ Human Approval",
    "7️⃣ Send Outreach",
    "8️⃣ Track Responses",
    "9️⃣ Schedule Meeting",
    "🔟 Analytics Dashboard"
]

for step in workflow:
    st.success(step)

st.divider()

st.subheader("📝 Recent Activities")

st.write("✅ Campaign Created")
st.write("✅ Proposal Generated")
st.write("✅ Meeting Scheduled")