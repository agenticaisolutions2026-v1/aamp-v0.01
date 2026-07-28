import streamlit as st

st.set_page_config(
    page_title="AAMP",
    page_icon="🤖",
    layout="wide"
)

dashboard = st.Page("pages/dashboard.py", title="Dashboard", icon="🏠")
organizations = st.Page("pages/organizations.py", title="Organizations", icon="🏫")
campaigns = st.Page("pages/campaigns.py", title="Campaigns", icon="📢")
agents = st.Page("pages/agents.py", title="AI Agents", icon="🤖")
analytics = st.Page("pages/analytics.py", title="Analytics", icon="📊")
settings = st.Page("pages/settings.py", title="Settings", icon="⚙️")

pg = st.navigation(
    [
        dashboard,
        organizations,
        campaigns,
        agents,
        analytics,
        settings,
    ]
)

pg.run()