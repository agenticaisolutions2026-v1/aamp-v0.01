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
        st.page_link("Pages/Dashboard.py", label="📊 Dashboard")
        st.page_link("Pages/Organizations.py", label="🏢 Organizations")
        st.page_link("Pages/Colleges.py", label="🎓 Colleges")
        st.page_link("Pages/Campaigns.py", label="📢 Campaigns")
        st.page_link("Pages/Agents.py", label="👥 Agents")
        st.page_link("Pages/Analytics.py", label="👥 Analytics")
        st.page_link("Pages/Settings.py", label="⚙️ Settings")

        st.write("System Status")
        health = HealthService.get_status()
        if health.get("status") == "healthy":
            st.success("🟢 Backend: Connected")
        else:
            st.error("🔴 Backend: Disconnected")
        st.markdown("---")
        st.caption("Version 1.0")