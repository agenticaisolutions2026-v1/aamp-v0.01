import streamlit as st
from services.health_service import HealthService

def create_sidebar():
    with st.sidebar:
        st.title("AAMP")
        st.page_link("app.py", label="🏠 Home")
        st.markdown("---")

        #st.write("### Welcome")
        #st.write("👤 Admin")

        #st.markdown("---")

        #st.write("### Quick Links")
        st.page_link("pages/Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/Organizations.py", label="🏢 Organizations")
        st.page_link("pages/Campaigns.py", label="📢 Campaigns")
        st.page_link("pages/Agents.py", label="👥 Agents")
        st.page_link("pages/Analytics.py", label="👥 Analytics")
        st.page_link("pages/Settings.py", label="⚙️ Settings")

        st.write("System Status")
        health = HealthService.get_status()
        if health.get("status") == "healthy":
            st.success("🟢 Backend: Connected")
        else:
            st.error("🔴 Backend: Disconnected")
        st.markdown("---")
        st.caption("Version 1.0")