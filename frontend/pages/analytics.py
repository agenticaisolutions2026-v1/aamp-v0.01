import streamlit as st
import pandas as pd

# ------------------------------------------------
# Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="Analytics",
    page_icon="📊",
    layout="wide"
)

# ------------------------------------------------
# Page Title
# ------------------------------------------------
st.title("📊 Analytics Dashboard")
st.write("Track Campaign Performance and Insights")

# ------------------------------------------------
# Summary Cards
# ------------------------------------------------
st.subheader("📈 Performance Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
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

with col2:
    st.markdown("""
    <div style="
        background-color:#E8F5E9;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>📬 Replies</h4>
        <h2 style="color:#2E7D32;">85</h2>
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
        <h4>📅 Meetings</h4>
        <h2 style="color:#F57F17;">20</h2>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="
        background-color:#F3E5F5;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🎯 Success Rate</h4>
        <h2 style="color:#6A1B9A;">34%</h2>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ------------------------------------------------
# Bar Chart
# ------------------------------------------------
st.subheader("📊 Campaign Performance")

performance = pd.DataFrame({
    "Campaign": [
        "AI Workshop",
        "Placement",
        "Internship",
        "Course Promotion"
    ],
    "Emails Sent": [
        100,
        80,
        50,
        20
    ]
})

st.bar_chart(performance.set_index("Campaign"))

st.divider()

# ------------------------------------------------
# Line Chart
# ------------------------------------------------
st.subheader("📈 Weekly Response Trend")

weekly = pd.DataFrame({
    "Week": [
        "Week 1",
        "Week 2",
        "Week 3",
        "Week 4"
    ],
    "Replies": [
        20,
        35,
        50,
        65
    ]
})

st.line_chart(weekly.set_index("Week"))

st.divider()

# ------------------------------------------------
# Response Table
# ------------------------------------------------
st.subheader("📋 Response Analysis")

response = pd.DataFrame({
    "Status": [
        "Positive",
        "Pending",
        "No Response"
    ],
    "Count": [
        50,
        25,
        10
    ]
})

st.dataframe(response, use_container_width=True)

st.success("Analytics updated successfully.")