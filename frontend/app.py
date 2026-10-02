import streamlit as st
from components.sidebar import create_sidebar


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AAMP",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# LIGHT THEME
# --------------------------------------------------

st.markdown(
    """
    <style>

    /* Hide Streamlit default navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Main background */
    .stApp {
        background-color: #f8fafc;
    }

    /* Main content */
    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    /* Headings */
    h1, h2, h3 {
        color: #334155 !important;
    }

    /* Normal text */
    p {
        color: #64748b;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px;
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
    }

    div[data-testid="stMetricValue"] {
        color: #334155 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #dbe3ec;
        background-color: #ffffff;
        color: #475569;
    }

    .stButton > button:hover {
        border-color: #b8c7d9;
        background-color: #f8fafc;
    }

    /* Horizontal line */
    hr {
        border-color: #e5e7eb;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

create_sidebar()


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.title("🤖 Agentic AI Marketing Platform")

st.caption(
    "Intelligent campaign management powered by AI agents"
)

st.divider()


# --------------------------------------------------
# WELCOME
# --------------------------------------------------

st.header("Welcome to AAMP 👋")

st.write(
    "Discover colleges, qualify leads, create personalized campaigns, "
    "manage human approvals and track outreach activities using "
    "AI-powered agents."
)

st.divider()


# --------------------------------------------------
# PLATFORM OVERVIEW
# --------------------------------------------------

st.header("📊 Platform Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🏫 Colleges",
        value="10",
        help="Colleges discovered by AAMP"
    )

with col2:
    st.metric(
        label="📢 Campaigns",
        value="23",
        help="Campaigns created by AAMP"
    )

with col3:
    st.metric(
        label="✉️ Outreach",
        value="16",
        help="Outreach records"
    )

with col4:
    st.metric(
        label="🤖 AI Agents",
        value="11",
        help="Registered AI agents"
    )


st.divider()


# --------------------------------------------------
# CAMPAIGN WORKFLOW
# --------------------------------------------------

st.header("🔄 Campaign Workflow")

st.info(
    """
    **College Discovery**  
    ↓  
    **Lead Qualification**  
    ↓  
    **Campaign Strategy**  
    ↓  
    **Personalized Message**  
    ↓  
    **Human Approval**  
    ↓  
    **Outreach**  
    ↓  
    **Follow-up**  
    ↓  
    **Response**  
    ↓  
    **Human Handoff**
    """
)


# --------------------------------------------------
# ABOUT AAMP
# --------------------------------------------------

st.header("💡 About AAMP")

st.write(
    "AAMP is an Agentic AI Marketing Platform designed to automate "
    "college discovery, lead qualification, campaign creation and "
    "outreach management while keeping human approval in the loop."
)


st.divider()

st.caption("AAMP • Agentic AI Marketing Platform • Version 1.0")